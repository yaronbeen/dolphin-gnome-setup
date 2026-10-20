#!/usr/bin/python3
"""Offline regression checks; no real uploads, clipboard changes, or user files."""

import configparser
import hashlib
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import shlex
from unittest.mock import patch

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / 'bin'
MENUS = ROOT / 'servicemenus'
loader = importlib.machinery.SourceFileLoader('file_actions', str(BIN / 'dolphin-file-action'))
spec = importlib.util.spec_from_loader(loader.name, loader)
actions = importlib.util.module_from_spec(spec)
loader.exec_module(actions)


class FileActionsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='dolphin-actions-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_clipboard_modes_and_x11_backend(self):
        for name in ['xclip', 'wl-copy']:
            tool = self.root / name
            tool.write_text('#!/bin/sh\n' + ('exit 77\n' if name == 'wl-copy' else '/bin/cat\n'))
            tool.chmod(0o700)
        files = [str(self.root / 'a "quoted" & name.txt'), str(self.root / '-second.txt')]
        env = dict(os.environ, PATH=f'{self.root}:/usr/bin:/bin', DISPLAY=':1')
        env.pop('WAYLAND_DISPLAY', None)
        for mode, expected in [('paths', '\n'.join(files) + '\n'),
                               ('names', 'a "quoted" & name.txt\n-second.txt\n'),
                               ('parents', str(self.root) + '\n')]:
            result = subprocess.run([str(BIN / 'dolphin-copy-selection'), mode, *files],
                                    env=env, capture_output=True, text=True, check=True)
            self.assertEqual(result.stdout, expected)
        result = subprocess.run([str(BIN / 'dolphin-copy-selection'), 'paths'], env=env)
        self.assertNotEqual(result.returncode, 0)

    def test_image_conversion_preserves_original_and_existing_output(self):
        source = self.root / 'image "quoted" & spaces.jpg'
        Image.new('RGB', (20, 10), 'red').save(source)
        before = source.read_bytes()
        existing = source.with_suffix('.png')
        existing.write_bytes(b'keep me')
        output = actions.convert_file(source, 'png')
        self.assertNotEqual(output, existing)
        self.assertEqual(existing.read_bytes(), b'keep me')
        self.assertEqual(source.read_bytes(), before)
        with Image.open(output) as image:
            self.assertEqual(image.size, (20, 10))
        with Image.open(actions.convert_file(source, 'half')) as image:
            self.assertEqual(image.size, (10, 5))
        with Image.open(actions.convert_file(source, 'webp')) as image:
            self.assertEqual(image.format, 'WEBP')

    def test_palette_transparency_and_cmyk(self):
        palette = self.root / 'palette.png'
        image = Image.new('P', (2, 2), 0)
        image.putpalette([255, 0, 0] + [0] * 765)
        image.save(palette, transparency=0)
        with Image.open(actions.convert_file(palette, 'webp')) as converted:
            self.assertEqual(converted.convert('RGBA').getpixel((0, 0))[3], 0)
        cmyk = self.root / 'print.jpg'
        Image.new('CMYK', (2, 2)).save(cmyk)
        before = cmyk.read_bytes()
        with Image.open(actions.convert_file(cmyk, 'png')) as converted:
            self.assertEqual(converted.mode, 'RGB')
        self.assertEqual(cmyk.read_bytes(), before)

    def test_private_source_produces_private_output(self):
        source = self.root / 'private.jpg'
        Image.new('RGB', (2, 2)).save(source)
        source.chmod(0o600)
        old_umask = os.umask(0o022)
        try:
            output = actions.convert_file(source, 'png')
        finally:
            os.umask(old_umask)
        self.assertEqual(output.stat().st_mode & 0o777, 0o600)

    def test_publish_collision_cannot_follow_symlink(self):
        source = self.root / 'source.jpg'
        Image.new('RGB', (2, 2)).save(source)
        victim = self.root / 'keep.txt'
        victim.write_text('unchanged')
        link = os.link
        inserted = []
        def raced_link(converted, target):
            if not inserted:
                target.symlink_to(victim)
                inserted.append(target)
            return link(converted, target)
        with patch.object(actions.os, 'link', side_effect=raced_link):
            output = actions.convert_file(source, 'png')
        self.assertEqual(victim.read_text(), 'unchanged')
        self.assertTrue(inserted[0].is_symlink())
        self.assertNotEqual(output, inserted[0])
        self.assertFalse(list(self.root.glob('.dolphin-convert-*')))

    def test_wayland_and_shell_copy(self):
        for name in ['xclip', 'wl-copy']:
            tool = self.root / name
            tool.write_text('#!/bin/sh\n' + ('exit 77\n' if name == 'xclip' else '/bin/cat\n'))
            tool.chmod(0o700)
        env = dict(os.environ, PATH=f'{self.root}:/usr/bin:/bin', WAYLAND_DISPLAY='wayland-test')
        files = ['a space', 'quote\'"', '$(nope)']
        result = subprocess.run([str(BIN / 'dolphin-copy-selection'), 'shell', *files],
                                env=env, capture_output=True, text=True, check=True)
        self.assertEqual(shlex.split(result.stdout), files)

    def test_animation_and_invalid_image_leave_no_partial_output(self):
        source = self.root / 'invalid.jpg'
        source.write_text('not an image')
        with self.assertRaises(OSError):
            actions.convert_file(source, 'png')
        self.assertFalse(source.with_suffix('.png').exists())
        animated = self.root / 'animated.webp'
        Image.new('RGB', (10, 10), 'red').save(animated, save_all=True,
            append_images=[Image.new('RGB', (10, 10), 'blue')], duration=100, loop=0)
        with self.assertRaisesRegex(ValueError, 'Animated'):
            actions.convert_file(animated, 'png')
        self.assertFalse(animated.with_suffix('.png').exists())

    def test_video_conversion_and_audio_extraction(self):
        source = self.root / 'video & "quote".mkv'
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-f', 'lavfi', '-i',
                        'color=c=blue:s=64x48:d=0.3', '-f', 'lavfi', '-i',
                        'sine=frequency=440:duration=0.3', '-shortest', str(source)], check=True)
        before = hashlib.sha256(source.read_bytes()).digest()
        for action, codec in [('mp4', 'h264'), ('mp3', 'mp3')]:
            output = actions.convert_file(source, action)
            result = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
                       'stream=codec_name', '-of', 'csv=p=0', str(output)], text=True)
            self.assertIn(codec, result)
        self.assertEqual(hashlib.sha256(source.read_bytes()).digest(), before)

    def test_failed_video_cleanup_and_folder_rejection(self):
        source = self.root / 'invalid.mp4'
        source.write_text('not video')
        with self.assertRaises(ValueError):
            actions.convert_file(source, 'mp3')
        self.assertFalse(source.with_suffix('.mp3').exists())
        with self.assertRaises(ValueError):
            actions.convert_file(self.root, 'png')

    def test_terminal_and_checksum_use_argument_arrays(self):
        source = self.root / 'quote " ; $(nope).py'
        source.write_bytes(b'hello')
        with patch.object(actions.subprocess, 'Popen') as popen:
            actions.run_action('terminal', [source])
            self.assertEqual(popen.call_args.args[0], ['konsole', '--workdir', str(self.root)])
        with patch.object(actions.subprocess, 'run') as run:
            actions.run_action('sha256', [source])
            self.assertEqual(run.call_args.args[0][-1], hashlib.sha256(b'hello').hexdigest())
        with self.assertRaises(ValueError):
            actions.run_action('terminal', [source, source])
        source.chmod(0o600)
        actions.run_action('executable', [source])
        self.assertEqual(source.stat().st_mode & 0o777, 0o700)

    def test_menu_configuration(self):
        action_ids = set()
        for menu in MENUS.glob('*.desktop'):
            config = configparser.ConfigParser(interpolation=None)
            config.read(menu)
            entry = config['Desktop Entry']
            self.assertEqual(entry['X-KDE-Protocol'], 'file', menu.name)
            self.assertEqual(entry['X-KDE-Priority'], 'TopLevel', menu.name)
            self.assertNotIn('X-KDE-Submenu', entry, menu.name)
            self.assertEqual(entry['Type'], 'Service', menu.name)
            for action in filter(None, entry['Actions'].split(';')):
                self.assertNotIn(action, action_ids)
                action_ids.add(action)
                command = config['Desktop Action ' + action]['Exec']
                self.assertNotIn('bash -c', command)
        self.assertTrue({'CopyPaths', 'CopyNames', 'CopyParents', 'ContaboUpload', 'ImagePNG',
                         'ImageWebP', 'ImageHalf', 'VideoMP4', 'VideoMP3', 'MediaInfo',
                         'ImageEXIF', 'MakeExecutable', 'OpenVSCode', 'TerminalHere',
                         'CopySHA256'}.issubset(action_ids))



if __name__ == '__main__':
    unittest.main(verbosity=2)
