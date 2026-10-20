import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('installer', ROOT / 'install-menus.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTest(unittest.TestCase):
    def test_install_backup_and_optional_integrations(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / 'home with spaces'
            binary = home / '.local/bin'
            binary.mkdir(parents=True)
            target = binary / 'dolphin-copy-selection'
            target.write_text('previous helper')
            installer.install(ROOT, home)
            menus = home / '.local/share/kio/servicemenus'
            self.assertNotIn('@BIN@', (menus / 'copy-selection.desktop').read_text())
            self.assertIn(f'Exec="{binary}/dolphin-copy-selection" paths %F', (menus / 'copy-selection.desktop').read_text())
            self.assertFalse((menus / 'contabo-share.desktop').exists())
            self.assertFalse((menus / 'gdrive-actions.desktop').exists())
            backups = list((home / '.local/state/dolphin-gnome-setup/backups').glob('*/.local/bin/dolphin-copy-selection'))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(), 'previous helper')
            installer.install(ROOT, home)
            self.assertEqual(len(list((home / '.local/state/dolphin-gnome-setup/backups').glob('*/.local/bin/dolphin-copy-selection'))), 1)
            (binary / 'gdrive-action').touch()
            config = home / '.config/contabo-share/config.json'
            config.parent.mkdir(parents=True)
            config.write_text('{}')
            installer.install(ROOT, home)
            self.assertTrue((menus / 'contabo-share.desktop').exists())
            self.assertTrue((menus / 'gdrive-actions.desktop').exists())

    def test_refuse_helper_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            target = home / '.local/bin/dolphin-copy-selection'
            target.parent.mkdir(parents=True)
            victim = home / 'victim'
            victim.write_text('keep')
            target.symlink_to(victim)
            with self.assertRaises(ValueError):
                installer.install(ROOT, home)
            self.assertEqual(victim.read_text(), 'keep')


if __name__ == '__main__':
    unittest.main()
