# Dolphin as Default File Manager on Ubuntu/GNOME

Makes KDE Dolphin the system-wide file manager on Ubuntu with GNOME desktop.

Also includes a user-local right-click menu setup: copy paths and filenames,
open a terminal or VS Code, convert media, inspect metadata, and copy checksums.

## Install or restore the right-click menus

On Ubuntu 24.04, install the tools used by the actions:

```bash
sudo apt-get install dolphin konsole python3-pil ffmpeg mediainfo libimage-exiftool-perl zenity xclip wl-clipboard
python3 install-menus.py
```

Run the installer as your normal desktop user, not with sudo. Close and reopen
Dolphin afterward. VS Code must be installed separately for its action to work.

The menu installer only installs helpers and service menus in your home directory.
It does not change the default file manager, desktop favorites, portals, packages,
or server settings. Changed files are backed up below
`$HOME/.local/state/dolphin-gnome-setup/backups/` before replacement. Unchanged
files are not backed up again. Other custom menus are left alone.

### Included actions

- **Copy Path / Copy Filename:** one selected item per line.
- **Copy Parent Folder Path:** shared parent folders are listed once.
- **Copy Shell-Quoted Path(s):** a separately labeled, shell-ready command line.
- **Open Terminal Here / Open in VS Code:** work on files, folders, and folder background contexts.
- **Copy SHA256 Checksum:** one checksum per selected file.
- **Images:** convert to PNG or WebP, resize to 50%, show EXIF data.
- **Video/audio:** convert video to H.264 MP4, extract MP3, show media info.
- **Make Executable:** adds the owner's execute bit to selected scripts; never runs them.

Actions are configured at the top level, not inside custom submenus. Media and
script tools are limited to relevant MIME types; terminal and metadata actions
require a single item. Conversion outputs are created beside their originals,
using numbered names if necessary. Originals and existing output paths are not
overwritten. Animated/multi-page image conversion is rejected rather than
silently dropping frames. Long video conversions have start/end notifications,
but no progress or cancellation dialog.

### Optional existing integrations

- **Contabo Share:** the generic client helper is included, but its menus install
  only when a private configuration already exists at
  `$HOME/.config/contabo-share/config.json`. A compatible, separately provisioned
  restricted upload server, SSH key and trusted host key are required. The client
  supports up to five files and 500 MiB per file. Server provisioning, credentials,
  private configuration, and upload history are deliberately not included.
- **Google Drive:** menus install only when an existing
  `$HOME/.local/bin/gdrive-action` helper is present. That machine-specific helper,
  rclone credentials and private folder mappings are not included. These actions
  are useful only on folders supported by that existing helper.

Do not copy private configuration, SSH keys, history, or unrelated desktop files
into this repository. See `SECURITY.md` for the public-repository boundary.

### Verification

```bash
python3 -m unittest discover -s tests -v
bash -n setup.sh uninstall.sh bin/dolphin-copy-selection
```

Tests use temporary files and mocked clipboard commands, never real uploads.
They cover X11/Wayland selection, quoting, real image/video conversion, alpha and
CMYK inputs, output-name collisions, symlink replacement at publication, cleanup,
and installation/backup behavior. The local menu logic was tested on Ubuntu
24.04 with Dolphin 23.08.5. Live popup layout, background invocation, keyboard
navigation and cross-monitor fit have not all been verified.

## What it fixes

| Problem | Solution |
|---------|----------|
| Chrome "Show in folder" does nothing / opens Nautilus | Replaces DBus `FileManager1` service to point to Dolphin |
| File open/save dialogs show GTK picker | Installs `xdg-desktop-portal-kde`, routes `FileChooser` portal to KDE |
| `xdg-open ~/folder` opens wrong app | Sets `inode/directory` mime default to Dolphin |

## Make Dolphin the default (older desktop setup)

This is separate from the menu installer. Read the scripts before running them:
the original setup changes a system D-Bus service, portal configuration and
`/etc/environment`. It also replaces its own existing portal configuration.
It is not needed to update the right-click menus on an already configured desktop.

```bash
chmod +x setup.sh
./setup.sh
```

Then **quit and relaunch Chrome** (or log out/in for all apps).

## Uninstall

The original uninstall script below reverses the default-manager/portal setup;
it does not remove the new right-click helpers. For menu rollback, restore only
the files you need from the menu installer's timestamped backups. Do not delete
unrelated service-menu files or private integration configuration.

```bash
chmod +x uninstall.sh
./uninstall.sh
```

## How it works

### 1. DBus FileManager1 Service

Chrome calls `org.freedesktop.FileManager1.ShowItems()` over DBus when you click "Show in folder". By default Ubuntu points this to Nautilus.

**File:** `/usr/share/dbus-1/services/org.freedesktop.FileManager1.service`

### 2. XDG Desktop Portal

GTK apps delegate file dialogs to XDG Desktop Portal. The portal routes to a backend based on config. We route `FileChooser` to the KDE backend (Dolphin) while keeping everything else on GTK/GNOME.

**File:** `~/.config/xdg-desktop-portal/portals.conf`

### 3. GTK_USE_PORTAL=1

Tells GTK3 apps (like Chrome) to use the XDG portal for file dialogs instead of GTK's built-in file chooser.

**Files:**
- `~/.config/environment.d/kde-portal.conf` (systemd user session)
- `/etc/environment` (system-wide fallback)

### 4. MIME default

Sets `inode/directory` to open with `org.kde.dolphin.desktop` so `xdg-open` on any folder opens Dolphin.

**File:** `~/.config/mimeapps.list`

## Config files

```
configs/
├── org.freedesktop.FileManager1.service  → /usr/share/dbus-1/services/
├── portals.conf                          → ~/.config/xdg-desktop-portal/
├── kde-portal.conf                       → ~/.config/environment.d/
└── mimeapps-directory.list               → (reference, applied via xdg-mime)
```

## Tested on

- Ubuntu 24.04 (GNOME)
- Google Chrome 146
- KDE Dolphin (from apt)
