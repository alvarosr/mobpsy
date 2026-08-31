#!/usr/bin/env bash
set -Eeuo pipefail

UPLOAD="/home/vagrant/mobpsy_cases_upload"
ROOT="/opt/mobpsy/cases"
USER_NAME="mobpsy"
USER_HOME="/home/${USER_NAME}"

echo
echo "============================================================"
echo " MobPsy 1.0.0 - Casos y evidencias"
echo "============================================================"
echo

if [ ! -f "$UPLOAD/mobpsy_case.py" ]; then
    echo "ERROR: no se ha recibido mobpsy_case.py." >&2
    exit 190
fi

echo "[1/5] Preparando estructura de casos..."
install -d -o "$USER_NAME" -g "$USER_NAME" "$USER_HOME/MobPsy/Casos"
install -d -o "$USER_NAME" -g "$USER_NAME" "$USER_HOME/MobPsy/Exportaciones"

echo "[2/5] Instalando gestor CLI..."
install -d -m 0755 "$ROOT"
install -m 0755 "$UPLOAD/mobpsy_case.py" "$ROOT/mobpsy_case.py"

cat >/usr/local/bin/mobpsy-case <<EOF
#!/usr/bin/env bash
set -e
exec /usr/bin/python3 "$ROOT/mobpsy_case.py" "\$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-case

echo "[3/5] Creando entrada del menú..."
cat >/usr/share/applications/mobpsy-cases.desktop <<'EOF'
[Desktop Entry]
Type=Application
Version=1.0
Name=MobPsy Casos
GenericName=OSINT Case Manager
Comment=Gestión de casos y evidencias de MobPsy
Exec=gnome-terminal -- /usr/local/bin/mobpsy-case
Icon=folder-documents
Terminal=false
Categories=Utility;Security;
StartupNotify=true
EOF
chmod 0644 /usr/share/applications/mobpsy-cases.desktop

echo "[4/5] Verificando..."
/usr/local/bin/mobpsy-case --help >/dev/null
test -d "$USER_HOME/MobPsy/Casos"

echo "[5/5] Registrando..."
mkdir -p /etc/mobpsy
cat >/etc/mobpsy/cases <<EOF
MOBPSY_CASES_VERSION=1.0.0
CASES_DIR=$USER_HOME/MobPsy/Casos
LAUNCHER=/usr/local/bin/mobpsy-case
EOF

rm -rf "$UPLOAD"

echo
echo "Gestor de casos preparado."


# MOBPSY_CASES_LEGACY_DOC_CLEANUP_V1
# Limpieza final de documentación legacy del área de casos.
if [ -d "/home/mobpsy/MobPsy" ]; then
    find "/home/mobpsy/MobPsy" -maxdepth 2 -type f \
      \( -iname 'LEEME.txt' \
         -o -iname 'README.txt' \
         -o -iname 'README_OLD*' \
         -o -iname 'README-OLD*' \
         -o -iname 'INSTRUCCIONES_ANTIGUAS*' \
         -o -iname 'NOTAS_ANTIGUAS*' \) \
      -delete
fi
# FIN MOBPSY_CASES_LEGACY_DOC_CLEANUP_V1
