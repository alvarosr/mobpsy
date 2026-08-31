#!/usr/bin/env bash
set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive

ROOT="/opt/mobpsy/tools/social-analyzer"
VENV="$ROOT/venv"

echo
echo "============================================================"
echo " MobPsy - Fase 11: Social-Analyzer"
echo "============================================================"

apt-get update
apt-get install -y python3 python3-venv python3-pip ca-certificates

install -d -m 0755 "$ROOT"

echo "[1/4] Creando entorno virtual..."
if [ ! -x "$VENV/bin/python" ]; then
    python3 -m venv "$VENV"
fi

echo "[2/4] Instalando/actualizando Social-Analyzer..."
"$VENV/bin/python" -m pip install --upgrade pip setuptools wheel
"$VENV/bin/python" -m pip install --upgrade social-analyzer

echo "[3/4] Creando lanzador estable..."
if [ -x "$VENV/bin/social-analyzer" ]; then
    cat >/usr/local/bin/mobpsy-social-analyzer <<EOF
#!/usr/bin/env bash
set -e
exec "$VENV/bin/social-analyzer" "\$@"
EOF
else
    cat >/usr/local/bin/mobpsy-social-analyzer <<EOF
#!/usr/bin/env bash
set -e
exec "$VENV/bin/python" -m social-analyzer "\$@"
EOF
fi
chmod 0755 /usr/local/bin/mobpsy-social-analyzer

echo "[4/4] Verificando..."
/usr/local/bin/mobpsy-social-analyzer --help >/dev/null

VERSION="$("$VENV/bin/python" - <<'PY'
from importlib.metadata import version
print(version("social-analyzer"))
PY
)"

mkdir -p /etc/mobpsy
cat >/etc/mobpsy/social-analyzer <<EOF
TOOL=social-analyzer
METHOD=python-venv-pypi
PACKAGE=social-analyzer
VERSION=${VERSION}
LAUNCHER=/usr/local/bin/mobpsy-social-analyzer
EOF

echo "Social-Analyzer ${VERSION} preparado."
