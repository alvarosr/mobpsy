#!/usr/bin/env bash
set -Eeuo pipefail

USER_NAME="mobpsy"
USER_HOME="/home/${USER_NAME}"
UPLOAD="/home/vagrant/mobpsy_branding_assets_upload"
ICON_IN="$UPLOAD/mobpsy_logo.png"
WALL_IN="$UPLOAD/mobpsy_wallpaper.png"
ICON="/usr/share/pixmaps/mobpsy.png"
WALL="/usr/local/share/backgrounds/mobpsy-wallpaper.png"

[ -f "$ICON_IN" ] || { echo "Falta $ICON_IN" >&2; exit 71; }
[ -f "$WALL_IN" ] || { echo "Falta $WALL_IN" >&2; exit 72; }
id "$USER_NAME" >/dev/null 2>&1 || { echo "Falta usuario mobpsy" >&2; exit 73; }

install -d -m 0755 /usr/share/pixmaps /usr/share/icons/hicolor/512x512/apps /usr/local/share/backgrounds
install -m 0644 "$ICON_IN" "$ICON"
install -m 0644 "$ICON_IN" /usr/share/icons/hicolor/512x512/apps/mobpsy.png
install -m 0644 "$WALL_IN" "$WALL"

# Reemplaza tambien el asset interno si la GUI lo usa directamente.
if [ -d /opt/mobpsy/app/assets ]; then
    install -m 0644 "$ICON_IN" /opt/mobpsy/app/assets/mobpsy.png || true
    install -m 0644 "$ICON_IN" /opt/mobpsy/app/assets/mobpsy_icon.png || true
fi

# Icono de los lanzadores instalados.
for desktop in /usr/share/applications/mobpsy.desktop "$USER_HOME/.local/share/applications/mobpsy.desktop"; do
    [ -f "$desktop" ] || continue
    if grep -q '^Icon=' "$desktop"; then
        sed -i 's|^Icon=.*|Icon=mobpsy|' "$desktop"
    else
        printf '\nIcon=mobpsy\n' >> "$desktop"
    fi
done

URI="file://$WALL"
# dconf directo, persistente para el usuario aunque todavia no exista una sesion grafica activa.
install -d -o "$USER_NAME" -g "$USER_NAME" "$USER_HOME/.config/dconf"
sudo -u "$USER_NAME" dbus-run-session -- gsettings set org.gnome.desktop.background picture-uri "$URI" || true
sudo -u "$USER_NAME" dbus-run-session -- gsettings set org.gnome.desktop.background picture-uri-dark "$URI" || true
sudo -u "$USER_NAME" dbus-run-session -- gsettings set org.gnome.desktop.background picture-options 'zoom' || true
sudo -u "$USER_NAME" dbus-run-session -- gsettings set org.gnome.desktop.screensaver picture-uri "$URI" || true
sudo -u "$USER_NAME" dbus-run-session -- gsettings set org.gnome.desktop.screensaver picture-options 'zoom' || true

# Avatar/cuenta coherente con el logo (sin tocar credenciales).
install -d -m 0755 /var/lib/AccountsService/icons /var/lib/AccountsService/users
install -m 0644 "$ICON_IN" /var/lib/AccountsService/icons/mobpsy
if [ -f /var/lib/AccountsService/users/mobpsy ]; then
    if grep -q '^Icon=' /var/lib/AccountsService/users/mobpsy; then
        sed -i 's|^Icon=.*|Icon=/var/lib/AccountsService/icons/mobpsy|' /var/lib/AccountsService/users/mobpsy
    else
        printf '\nIcon=/var/lib/AccountsService/icons/mobpsy\n' >> /var/lib/AccountsService/users/mobpsy
    fi
fi

gtk-update-icon-cache -f /usr/share/icons/hicolor >/dev/null 2>&1 || true
update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
chown -R "$USER_NAME:$USER_NAME" "$USER_HOME/.config" || true

# MOBPSY_CANONICAL_LOGO_LOCK_V1
# El logo corporativo de MobPsy tiene una Ãºnica fuente. Cualquier fase posterior
# debe usar esta copia y nunca reintroducir un icono histÃ³rico.
CANONICAL_LOGO=""
for candidate in \
    /home/vagrant/mobpsy_app_upload/assets/mobpsy_logo.png \
    /home/vagrant/mobpsy_app_upload/mobpsy_app/assets/mobpsy_logo.png \
    /opt/mobpsy/app/assets/mobpsy_logo.png
do
    if [ -f "$candidate" ]; then
        CANONICAL_LOGO="$candidate"
        break
    fi
done

if [ -n "$CANONICAL_LOGO" ]; then
    install -d -m 0755 /usr/share/pixmaps /opt/mobpsy/branding

    copy_logo_if_needed() {
        local src="$1"
        local dst="$2"

        mkdir -p "$(dirname "$dst")"

        # Evita el fallo de GNU install cuando origen y destino son el mismo
        # archivo. Esto puede ocurrir cuando la única copia canónica disponible
        # ya es /opt/mobpsy/app/assets/mobpsy_logo.png.
        local src_real dst_real
        src_real="$(readlink -f "$src" 2>/dev/null || printf '%s' "$src")"
        dst_real="$(readlink -f "$dst" 2>/dev/null || printf '%s' "$dst")"

        if [ "$src_real" = "$dst_real" ]; then
            return 0
        fi

        install -m 0644 "$src" "$dst"
    }

    copy_logo_if_needed "$CANONICAL_LOGO" /usr/share/pixmaps/mobpsy.png
    copy_logo_if_needed "$CANONICAL_LOGO" /opt/mobpsy/branding/mobpsy_logo.png

    for target in \
        /opt/mobpsy/app/assets/mobpsy_logo.png \
        /opt/mobpsy/app/assets/mobpsy.png \
        /opt/mobpsy/app/resources/mobpsy_logo.png \
        /opt/mobpsy/app/icons/mobpsy.png
    do
        copy_logo_if_needed "$CANONICAL_LOGO" "$target"
    done
fi
# FIN MOBPSY_CANONICAL_LOGO_LOCK_V1

echo "MOBPSY_BRANDING_OK"
