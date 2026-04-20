#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIGS="$SCRIPT_DIR/configs"

echo "=== Dolphin as default file manager on Ubuntu/GNOME ==="
echo ""

# 1. Install required packages
echo "[1/6] Installing dolphin and xdg-desktop-portal-kde..."
sudo apt-get install -y dolphin xdg-desktop-portal-kde

# 2. Set Dolphin as default for directories via xdg-mime
echo "[2/6] Setting Dolphin as default directory handler..."
xdg-mime default org.kde.dolphin.desktop inode/directory
xdg-mime default org.kde.dolphin.desktop application/x-gnome-saved-search

# 3. Replace FileManager1 DBus service (Chrome's "Show in folder")
echo "[3/6] Configuring DBus FileManager1 service..."
DBUS_SERVICE="/usr/share/dbus-1/services/org.freedesktop.FileManager1.service"
if [ -f "$DBUS_SERVICE" ]; then
    sudo cp "$DBUS_SERVICE" "${DBUS_SERVICE}.bak"
    echo "  Backed up original to ${DBUS_SERVICE}.bak"
fi
sudo cp "$CONFIGS/org.freedesktop.FileManager1.service" "$DBUS_SERVICE"

# 4. Configure XDG portal to use KDE for file dialogs
echo "[4/6] Configuring XDG desktop portal for KDE file chooser..."
mkdir -p ~/.config/xdg-desktop-portal
cp "$CONFIGS/portals.conf" ~/.config/xdg-desktop-portal/portals.conf

# 5. Set GTK_USE_PORTAL=1 (makes GTK apps use portal for file dialogs)
echo "[5/6] Setting GTK_USE_PORTAL=1..."
mkdir -p ~/.config/environment.d
cp "$CONFIGS/kde-portal.conf" ~/.config/environment.d/kde-portal.conf

# Also add to /etc/environment for system-wide persistence
if ! grep -q "GTK_USE_PORTAL" /etc/environment 2>/dev/null; then
    echo 'GTK_USE_PORTAL=1' | sudo tee -a /etc/environment > /dev/null
fi

# 6. Activate in current session
echo "[6/6] Activating in current session..."
export GTK_USE_PORTAL=1
dbus-update-activation-environment GTK_USE_PORTAL=1 2>/dev/null || true
systemctl --user set-environment GTK_USE_PORTAL=1 2>/dev/null || true
systemctl --user restart xdg-desktop-portal 2>/dev/null || true

echo ""
echo "=== Done! ==="
echo ""
echo "Changes applied:"
echo "  - 'Show in folder' in Chrome/browsers → opens Dolphin"
echo "  - File open/save dialogs → KDE/Dolphin file picker"
echo "  - Dolphin is default directory handler"
echo ""
echo "NOTE: Fully quit and relaunch Chrome (or any running app) to see the new file dialogs."
echo "      A logout/login ensures everything is active system-wide."
