#!/usr/bin/env bash
set -euo pipefail

echo "=== Reverting to default GNOME file manager ==="
echo ""

# 1. Restore original FileManager1 service
DBUS_SERVICE="/usr/share/dbus-1/services/org.freedesktop.FileManager1.service"
if [ -f "${DBUS_SERVICE}.bak" ]; then
    sudo cp "${DBUS_SERVICE}.bak" "$DBUS_SERVICE"
    echo "[1/4] Restored original DBus FileManager1 service"
else
    echo "[1/4] No backup found, writing Nautilus default..."
    sudo tee "$DBUS_SERVICE" > /dev/null << 'EOF'
[D-BUS Service]
Name=org.freedesktop.FileManager1
Exec=/usr/bin/nautilus --gapplication-service
EOF
fi

# 2. Remove portal config
echo "[2/4] Removing portal config..."
rm -f ~/.config/xdg-desktop-portal/portals.conf

# 3. Remove GTK_USE_PORTAL
echo "[3/4] Removing GTK_USE_PORTAL..."
rm -f ~/.config/environment.d/kde-portal.conf
sudo sed -i '/GTK_USE_PORTAL/d' /etc/environment 2>/dev/null || true

# 4. Reset default directory handler to Nautilus
echo "[4/4] Setting Nautilus as default directory handler..."
xdg-mime default org.gnome.Nautilus.desktop inode/directory

echo ""
echo "=== Reverted. Log out and back in for full effect. ==="
