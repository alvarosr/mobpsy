#!/usr/bin/env bash
set -Eeuo pipefail

export DEBIAN_FRONTEND=noninteractive

TOOL_ROOT="/opt/mobpsy/tools/sherlock"
VENV="${TOOL_ROOT}/venv"

echo
echo "============================================================"
echo " MobPsy - Fase 4: Sherlock"
echo "============================================================"
echo

echo "[1/5] Instalando soporte Python aislado..."
apt-get update
apt-get install -y python3 python3-venv python3-pip ca-certificates

echo "[2/5] Creando entorno virtual de Sherlock..."
install -d -m 0755 "$TOOL_ROOT"
if [ ! -x "${VENV}/bin/python" ]; then
    python3 -m venv "$VENV"
fi

echo "[3/5] Instalando/actualizando Sherlock desde PyPI..."
"${VENV}/bin/python" -m pip install --upgrade pip setuptools wheel
"${VENV}/bin/python" -m pip install --upgrade sherlock-project

if [ ! -x "${VENV}/bin/sherlock" ]; then
    echo "ERROR: sherlock-project se instaló pero no apareció el ejecutable sherlock." >&2
    exit 50
fi

echo "[4/5] Creando lanzador estable para MobPsy..."
cat >/usr/local/bin/mobpsy-sherlock <<EOF
#!/usr/bin/env bash
set -e
exec "${VENV}/bin/sherlock" "\$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-sherlock

echo "[5/5] Comprobando la instalación..."
VERSION="$(/usr/local/bin/mobpsy-sherlock --version 2>&1 | head -n 1 || true)"
echo "      ${VERSION:-Sherlock instalado}"

mkdir -p /etc/mobpsy
cat >/etc/mobpsy/sherlock <<EOF
TOOL=sherlock
METHOD=python-venv
PACKAGE=sherlock-project
LAUNCHER=/usr/local/bin/mobpsy-sherlock
EOF

echo
echo "Sherlock preparado para la GUI de MobPsy."
echo
