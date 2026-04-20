# Dolphin as Default File Manager on Ubuntu/GNOME

Makes KDE Dolphin the system-wide file manager on Ubuntu with GNOME desktop.

## What it fixes

| Problem | Solution |
|---------|----------|
| Chrome "Show in folder" does nothing / opens Nautilus | Replaces DBus `FileManager1` service to point to Dolphin |
| File open/save dialogs show GTK picker | Installs `xdg-desktop-portal-kde`, routes `FileChooser` portal to KDE |
| `xdg-open ~/folder` opens wrong app | Sets `inode/directory` mime default to Dolphin |

## Install

```bash
chmod +x setup.sh
./setup.sh
```

Then **quit and relaunch Chrome** (or log out/in for all apps).

## Uninstall

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
