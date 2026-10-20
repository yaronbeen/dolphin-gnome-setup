#!/usr/bin/python3
"""Install user-local Dolphin menus, backing up changed files first."""

from datetime import datetime
from pathlib import Path
import os
import shutil
import subprocess


def install(root, home):
    binary = home / '.local/bin'
    menus = home / '.local/share/kio/servicemenus'
    if any(char in str(binary) for char in '"`$\\%\n\r'):
        raise ValueError('Home path contains characters unsupported by desktop Exec entries.')
    backup = home / '.local/state/dolphin-gnome-setup/backups' / datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    files = [(src, binary / src.name, src.read_bytes(), 0o755) for src in (root / 'bin').iterdir() if src.is_file()]
    for src in (root / 'servicemenus').glob('*.desktop'):
        if src.name == 'gdrive-actions.desktop' and not (binary / 'gdrive-action').is_file():
            continue
        if src.name.startswith('contabo-') and not (home / '.config/contabo-share/config.json').is_file():
            continue
        data = src.read_text().splitlines()
        for index, line in enumerate(data):
            if line.startswith('Exec=@BIN@/'):
                command, _, args = line[5:].partition(' ')
                data[index] = 'Exec="' + command.replace('@BIN@', str(binary)) + '"' + (' ' + args if args else '')
        files.append((src, menus / src.name, ('\n'.join(data) + '\n').encode(), 0o755))
    for _, target, data, mode in files:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink():
            raise ValueError(f'Refusing to replace a symlink: {target}')
        if target.exists() and target.read_bytes() != data:
            saved = backup / target.relative_to(home)
            saved.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            shutil.copy2(target, saved)
        temporary = target.with_name(target.name + f'.install-{os.getpid()}')
        try:
            with temporary.open('xb') as stream:
                stream.write(data)
            temporary.chmod(mode)
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    print(f'Installed {len(files)} helpers/menus. Changed-file backups: {backup}')


if __name__ == '__main__':
    install(Path(__file__).resolve().parent, Path.home())
    cache = shutil.which('kbuildsycoca6') or shutil.which('kbuildsycoca5')
    if cache:
        subprocess.run([cache, '--noincremental'], check=True)
    print('Close and reopen Dolphin to refresh menus. No desktop defaults, packages or server settings were changed.')
