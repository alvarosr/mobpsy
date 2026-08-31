#!/usr/bin/env bash
set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive

ROOT="/opt/mobpsy/tools/wafw00f"
VENV="$ROOT/venv"

echo
echo "============================================================"
echo " MobPsy - Fase 9: WAFW00F"
echo "============================================================"

apt-get update
apt-get install -y python3 python3-venv python3-pip ca-certificates

install -d -m 0755 "$ROOT"

echo "[1/4] Creando entorno virtual aislado..."
if [ ! -x "$VENV/bin/python" ]; then
    python3 -m venv "$VENV"
fi

echo "[2/4] Instalando/actualizando WAFW00F..."
"$VENV/bin/python" -m pip install --upgrade pip setuptools wheel
"$VENV/bin/python" -m pip install --upgrade wafw00f

if [ ! -x "$VENV/bin/wafw00f" ]; then
    echo "ERROR: WAFW00F se instaló pero no apareció el ejecutable." >&2
    exit 120
fi

echo "[3/4] Creando lanzador estable..."
cat >/usr/local/bin/mobpsy-wafw00f <<EOF
#!/usr/bin/env bash
set -e
exec "$VENV/bin/wafw00f" "\$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-wafw00f

echo "[4/4] Verificando..."
VERSION="$(/usr/local/bin/mobpsy-wafw00f --version 2>&1 | head -n1)"

mkdir -p /etc/mobpsy
cat >/etc/mobpsy/wafw00f <<EOF
TOOL=wafw00f
METHOD=python-venv-pypi
PACKAGE=wafw00f
VERSION=${VERSION}
LAUNCHER=/usr/local/bin/mobpsy-wafw00f
EOF

echo "$VERSION"
