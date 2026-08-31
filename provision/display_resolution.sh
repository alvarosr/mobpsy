#!/usr/bin/env bash
set -Eeuo pipefail

export DEBIAN_FRONTEND=noninteractive
USER_NAME="mobpsy"
USER_HOME="/home/${USER_NAME}"

echo
echo "============================================================"
echo " MobPsy - Configuración de pantalla"
echo "============================================================"
echo

echo "[1/3] Instalando utilidades X11..."
apt-get update
apt-get install -y x11-xserver-utils xcvt

echo "[2/3] Creando configuración de resolución preferida 1440x900..."
mkdir -p /usr/local/lib/mobpsy
install -d -o "$USER_NAME" -g "$USER_NAME" "${USER_HOME}/.config/autostart"

cat >/usr/local/lib/mobpsy/display-resolution.sh <<'EOF'
#!/usr/bin/env bash
set -u

# Esperar a que GNOME/Xorg haya terminado de iniciar.
sleep 5

command -v xrandr >/dev/null 2>&1 || exit 0

OUTPUT="$(xrandr --query | awk '/ connected/{print $1; exit}')"
[ -n "$OUTPUT" ] || exit 0

# Si 1440x900 ya está disponible, usarla directamente.
if xrandr --query | awk -v out="$OUTPUT" '
    $1 == out && $2 == "connected" {inside=1; next}
    inside && $1 !~ /^[0-9]/ {exit}
    inside && $1 == "1440x900" {found=1}
    END {exit found ? 0 : 1}
'; then
    xrandr --output "$OUTPUT" --mode 1440x900
    exit 0
fi

# Crear el modo si el driver lo permite.
MODELINE="$(cvt 1440 900 60 2>/dev/null | awk '/Modeline/{sub(/^Modeline /,""); print; exit}')"
if [ -n "$MODELINE" ]; then
    MODE_NAME="$(printf '%s\n' "$MODELINE" | awk '{gsub(/"/,"",$1); print $1}')"
    MODE_ARGS="$(printf '%s\n' "$MODELINE" | cut -d' ' -f2-)"

    # shellcheck disable=SC2086
    xrandr --newmode $MODELINE 2>/dev/null || true
    xrandr --addmode "$OUTPUT" "$MODE_NAME" 2>/dev/null || true
    if ! xrandr --output "$OUTPUT" --mode "$MODE_NAME" 2>/dev/null; then
        xrandr --output "$OUTPUT" --mode 1366x768 2>/dev/null || true
    fi
fi
EOF
chmod 0755 /usr/local/lib/mobpsy/display-resolution.sh

cat >"${USER_HOME}/.config/autostart/mobpsy-display-resolution.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=MobPsy - Resolución de pantalla
Comment=Establece 1440x900 como resolución preferida
Exec=/usr/local/lib/mobpsy/display-resolution.sh
Terminal=false
X-GNOME-Autostart-enabled=true
NoDisplay=true
EOF

chown -R "${USER_NAME}:${USER_NAME}" "${USER_HOME}/.config"

echo "[3/3] Configuración instalada."
echo "      Resolución preferida: 1440x900"
echo
