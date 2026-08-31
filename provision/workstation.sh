#!/usr/bin/env bash
set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive

log() {
    echo
    echo "[$1] $2"
}

echo
echo "============================================================"
echo " MobPsy - Fase 1: preparando la workstation"
echo "============================================================"

log "1/7" "Actualizando índices de paquetes..."
apt-get update

log "2/7" "Instalando utilidades básicas..."
apt-get install -y \
    ca-certificates \
    curl \
    wget \
    git \
    jq \
    unzip \
    p7zip-full \
    xdg-utils \
    gnupg \
    software-properties-common \
    language-pack-es \
    language-pack-gnome-es

log "3/7" "Configurando idioma español y nombre del equipo..."
update-locale LANG=es_ES.UTF-8 LANGUAGE=es_ES:es
localectl set-locale LANG=es_ES.UTF-8 || true
localectl set-keymap es || true
localectl set-x11-keymap es || true
timedatectl set-timezone Europe/Madrid || true

cat >/etc/machine-info <<'EOF'
PRETTY_HOSTNAME=MobPsy Workstation
EOF

# Nombre descriptivo de la cuenta gráfica.
usermod -c "MobPsy Analyst" mobpsy || true

log "4/7" "Preparando estructura de trabajo del usuario..."
install -d -o mobpsy -g mobpsy \
    /home/mobpsy/MobPsy \
    /home/mobpsy/MobPsy/Casos \
    /home/mobpsy/MobPsy/Evidencias \
    /home/mobpsy/MobPsy/Exportaciones \
    /home/mobpsy/MobPsy/Temporal \
    /home/mobpsy/.config/mobpsy \
    /home/mobpsy/.config/autostart

cat >/home/mobpsy/MobPsy/LEEME.txt <<'EOF'
MobPsy Workstation

Esta carpeta será el espacio de trabajo local de MobPsy.

Casos/          investigaciones
Evidencias/     ficheros y evidencias guardadas
Exportaciones/  resultados e informes exportados
Temporal/       datos temporales

En esta fase todavía NO se ha instalado la aplicación MobPsy ni herramientas OSINT.
EOF
chown mobpsy:mobpsy /home/mobpsy/MobPsy/LEEME.txt

log "5/7" "Comprobando Firefox..."
# Ubuntu 22.04 distribuye Firefox como snap. ubuntu-desktop normalmente ya lo
# deja instalado, pero esta comprobación hace el provisionamiento repetible.
systemctl enable --now snapd.socket >/dev/null 2>&1 || true

# Esperar a que snapd termine de inicializarse en una instalación nueva.
for _ in $(seq 1 60); do
    if snap wait system seed.loaded >/dev/null 2>&1; then
        break
    fi
    sleep 2
done

if ! snap list firefox >/dev/null 2>&1; then
    snap install firefox
else
    echo "Firefox ya está instalado."
fi

log "6/7" "Instalando Chromium..."
if ! snap list chromium >/dev/null 2>&1; then
    snap install chromium
else
    echo "Chromium ya está instalado."
fi

log "7/7" "Preparando el dock de GNOME para el primer inicio..."
install -d /usr/local/lib/mobpsy

cat >/usr/local/lib/mobpsy/first-login.sh <<'EOF'
#!/usr/bin/env bash
set -u

MARKER="$HOME/.config/mobpsy/fase1-login.done"
mkdir -p "$HOME/.config/mobpsy"

[ -f "$MARKER" ] && exit 0

# Damos tiempo a GNOME Shell a terminar el inicio de sesión.
sleep 8

gsettings set org.gnome.desktop.interface clock-format '24h' 2>/dev/null || true
gsettings set org.gnome.shell favorite-apps \
"['firefox_firefox.desktop', 'chromium_chromium.desktop', 'org.gnome.Nautilus.desktop', 'org.gnome.Terminal.desktop']" \
2>/dev/null || true

touch "$MARKER"
EOF
chmod 0755 /usr/local/lib/mobpsy/first-login.sh

cat >/home/mobpsy/.config/autostart/mobpsy-first-login.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=MobPsy - configuración inicial
Comment=Aplica la configuración visual básica de MobPsy una sola vez
Exec=/usr/local/lib/mobpsy/first-login.sh
Terminal=false
X-GNOME-Autostart-enabled=true
NoDisplay=true
EOF
chown -R mobpsy:mobpsy /home/mobpsy/.config

mkdir -p /etc/mobpsy
cat >/etc/mobpsy/release <<'EOF'
MOBPSY_PHASE=1
MOBPSY_RELEASE=workstation
EOF

echo
echo "============================================================"
echo " Fase 1 aplicada correctamente."
echo " - Ubuntu Desktop: conservado"
echo " - Idioma/teclado: español"
echo " - Firefox: preparado"
echo " - Chromium: preparado"
echo " - Estructura ~/MobPsy: creada"
echo "============================================================"
echo
