#!/usr/bin/env bash
set -Eeuo pipefail

USER_NAME="mobpsy"
USER_HOME="/home/${USER_NAME}"

if ! id "$USER_NAME" >/dev/null 2>&1; then
    echo "ERROR: el usuario mobpsy aun no existe." >&2
    exit 61
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update -y >/dev/null
apt-get install -y locales xdg-user-dirs xdg-user-dirs-gtk >/dev/null
locale-gen es_ES.UTF-8 >/dev/null 2>&1 || true
update-locale LANG=es_ES.UTF-8 LANGUAGE=es_ES:es || true
localectl set-locale LANG=es_ES.UTF-8 || true
localectl set-keymap es || true
localectl set-x11-keymap es || true

install -d -o "$USER_NAME" -g "$USER_NAME" "$USER_HOME/.config"
touch "$USER_HOME/.config/gnome-initial-setup-done"
chown "$USER_NAME:$USER_NAME" "$USER_HOME/.config/gnome-initial-setup-done"

# Desactiva asistentes de bienvenida/primer inicio.
for f in /etc/xdg/autostart/gnome-initial-setup*.desktop /etc/xdg/autostart/ubuntu-welcome*.desktop; do
    [ -e "$f" ] || continue
    if grep -q '^X-GNOME-Autostart-enabled=' "$f"; then
        sed -i 's/^X-GNOME-Autostart-enabled=.*/X-GNOME-Autostart-enabled=false/' "$f" || true
    else
        printf '\nX-GNOME-Autostart-enabled=false\n' >> "$f" || true
    fi
done

# Crea directamente los nombres espaÃƒÂ±oles y fija XDG para que no aparezca
# el dialogo preguntando si debe renombrar carpetas.
install -d -o "$USER_NAME" -g "$USER_NAME" \
  "$USER_HOME/Escritorio" "$USER_HOME/Descargas" "$USER_HOME/Plantillas" \
  "$USER_HOME/Público" "$USER_HOME/Documentos" "$USER_HOME/Música" \
  "$USER_HOME/Imágenes" "$USER_HOME/Vídeos"

cat > "$USER_HOME/.config/user-dirs.dirs" <<EOF
XDG_DESKTOP_DIR="$USER_HOME/Escritorio"
XDG_DOWNLOAD_DIR="$USER_HOME/Descargas"
XDG_TEMPLATES_DIR="$USER_HOME/Plantillas"
XDG_PUBLICSHARE_DIR="$USER_HOME/Público"
XDG_DOCUMENTS_DIR="$USER_HOME/Documentos"
XDG_MUSIC_DIR="$USER_HOME/Música"
XDG_PICTURES_DIR="$USER_HOME/Imágenes"
XDG_VIDEOS_DIR="$USER_HOME/Vídeos"
EOF
printf 'es_ES\n' > "$USER_HOME/.config/user-dirs.locale"
chown "$USER_NAME:$USER_NAME" "$USER_HOME/.config/user-dirs.dirs" "$USER_HOME/.config/user-dirs.locale"

# Solo elimina directorios ingleses si estan vacios. Nunca borra datos.
for old in Desktop Downloads Templates Public Documents Music Pictures Videos; do
    [ -d "$USER_HOME/$old" ] || continue
    rmdir "$USER_HOME/$old" >/dev/null 2>&1 || true
done

# Reduce avisos de actualizacion/upgrade durante el primer uso.
if [ -f /etc/update-manager/release-upgrades ]; then
    sed -i 's/^Prompt=.*/Prompt=never/' /etc/update-manager/release-upgrades || true
fi

install -d -o "$USER_NAME" -g "$USER_NAME" "$USER_HOME/.config/autostart"
cat > "$USER_HOME/.config/autostart/xdg-user-dirs-gtk-update.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=MobPsy XDG folders already configured
Exec=/bin/true
Hidden=true
X-GNOME-Autostart-enabled=false
EOF
chown "$USER_NAME:$USER_NAME" "$USER_HOME/.config/autostart/xdg-user-dirs-gtk-update.desktop"

echo "MOBPSY_FIRST_LOGIN_OK"

# MOBPSY_LEGACY_README_CLEANUP_V1
# Elimina documentación temporal/legacy que no debe aparecer en la edición final.
if [ -d "$USER_HOME/MobPsy" ]; then
    find "$USER_HOME/MobPsy" -maxdepth 2 -type f \
      \( -iname 'LEEME.txt' \
         -o -iname 'README.txt' \
         -o -iname 'README_OLD*' \
         -o -iname 'README-OLD*' \
         -o -iname 'INSTRUCCIONES_ANTIGUAS*' \
         -o -iname 'NOTAS_ANTIGUAS*' \) \
      -delete
fi
# FIN MOBPSY_LEGACY_README_CLEANUP_V1
