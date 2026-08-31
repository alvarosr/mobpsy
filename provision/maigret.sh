#!/usr/bin/env bash
set -Eeuo pipefail

export DEBIAN_FRONTEND=noninteractive

TOOL_ROOT="/opt/mobpsy/tools/maigret"
VENV="${TOOL_ROOT}/venv"

echo
echo "============================================================"
echo " MobPsy - Fase 5: Maigret"
echo "============================================================"
echo

echo "[1/5] Instalando dependencias base..."
apt-get update
apt-get install -y \
    python3 \
    python3-venv \
    python3-pip \
    ca-certificates \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev

echo "[2/5] Creando entorno virtual aislado..."
install -d -m 0755 "$TOOL_ROOT"
if [ ! -x "${VENV}/bin/python" ]; then
    python3 -m venv "$VENV"
fi

echo "[3/5] Instalando/actualizando Maigret desde PyPI..."
"${VENV}/bin/python" -m pip install --upgrade pip setuptools wheel
"${VENV}/bin/python" -m pip install --upgrade maigret

if [ ! -x "${VENV}/bin/maigret" ]; then
    echo "ERROR: Maigret se instaló pero no apareció el ejecutable maigret." >&2
    exit 60
fi

echo "[4/5] Creando lanzador estable para MobPsy..."
cat >/usr/local/bin/mobpsy-maigret <<EOF
#!/usr/bin/env bash
set -e
exec "${VENV}/bin/maigret" "\$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-maigret

echo "[5/5] Comprobando instalación..."
VERSION="$("${VENV}/bin/python" - <<'PY'
from importlib.metadata import version
print(version("maigret"))
PY
)"
echo "      Maigret ${VERSION}"

mkdir -p /etc/mobpsy
cat >/etc/mobpsy/maigret <<EOF
TOOL=maigret
METHOD=python-venv
PACKAGE=maigret
VERSION=${VERSION}
LAUNCHER=/usr/local/bin/mobpsy-maigret
EOF

echo
echo "Maigret preparado para MobPsy."
echo
