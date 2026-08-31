#!/usr/bin/env bash
set -Eeuo pipefail

export DEBIAN_FRONTEND=noninteractive

UPLOAD="/home/vagrant/mobpsy_cli_upload"
ROOT="/opt/mobpsy/terminal"
USER_NAME="mobpsy"
USER_HOME="/home/${USER_NAME}"

echo
echo "============================================================"
echo " MobPsy 1.0.0 - Terminal"
echo "============================================================"
echo

if [ ! -f "$UPLOAD/mobpsy_terminal.py" ] || [ ! -f "$UPLOAD/case_context.py" ]; then
    echo "ERROR: no se ha recibido mobpsy_terminal.py." >&2
    exit 170
fi

echo "[1/5] Instalando utilidades de terminal..."
apt-get update
apt-get install -y python3 less gnome-terminal desktop-file-utils

echo "[2/5] Instalando MobPsy Terminal..."
install -d -m 0755 "$ROOT"
install -m 0755 "$UPLOAD/mobpsy_terminal.py" "$ROOT/mobpsy_terminal.py"
install -m 0644 "$UPLOAD/case_context.py" "$ROOT/case_context.py"

echo "[3/5] Creando comandos globales..."
cat >/usr/local/bin/mobpsy-cli <<EOF
#!/usr/bin/env bash
set -e
exec /usr/bin/python3 "$ROOT/mobpsy_terminal.py" "\$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-cli

cat >/usr/local/bin/mobpsy-terminal <<'EOF'
#!/usr/bin/env bash
set -e
exec /usr/local/bin/mobpsy-cli "$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-terminal

echo "[4/5] Registrando como aplicación gráfica..."
cat >/usr/share/applications/mobpsy-terminal.desktop <<'EOF'
[Desktop Entry]
Type=Application
Version=1.0
Name=MobPsy Terminal
GenericName=OSINT Terminal Interface
Comment=Interfaz full-terminal de MobPsy para las herramientas OSINT instaladas
Exec=gnome-terminal --maximize -- /usr/local/bin/mobpsy-cli
Icon=utilities-terminal
Terminal=false
Categories=Utility;Security;
StartupNotify=true
EOF
chmod 0644 /usr/share/applications/mobpsy-terminal.desktop
update-desktop-database /usr/share/applications || true

# Acceso directo opcional en el escritorio del usuario.
DESKTOP_DIR="${USER_HOME}/Escritorio"
[ -d "$DESKTOP_DIR" ] || DESKTOP_DIR="${USER_HOME}/Desktop"
if [ -d "$DESKTOP_DIR" ]; then
    cp /usr/share/applications/mobpsy-terminal.desktop "$DESKTOP_DIR/MobPsy Terminal.desktop"
    chown "${USER_NAME}:${USER_NAME}" "$DESKTOP_DIR/MobPsy Terminal.desktop"
    chmod +x "$DESKTOP_DIR/MobPsy Terminal.desktop"
fi

echo "[5/5] Verificando..."
test -x /usr/local/bin/mobpsy-cli
/usr/bin/python3 -m py_compile "$ROOT/mobpsy_terminal.py"

mkdir -p /etc/mobpsy
cat >/etc/mobpsy/terminal <<'EOF'
MOBPSY_TERMINAL_VERSION=1.0.0
MOBPSY_TERMINAL_TOOLS=25
LAUNCHER=/usr/local/bin/mobpsy-cli
EOF

rm -rf "$UPLOAD"

echo
echo "============================================================"
echo " MobPsy Terminal moderno instalado correctamente."
echo " Comando: mobpsy-cli"
echo " Aplicación: MobPsy Terminal"
echo "============================================================"
echo
