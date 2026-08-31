#!/usr/bin/env bash
set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive

ROOT="/opt/mobpsy/tools/spiderfoot"
SRC="$ROOT/spiderfoot-4.0"
VENV="$ROOT/venv"
ARCHIVE_URL="https://github.com/smicallef/spiderfoot/archive/v4.0.tar.gz"

echo
echo "============================================================"
echo " MobPsy - Fase 12: SpiderFoot"
echo "============================================================"

apt-get update
apt-get install -y \
    python3 python3-venv python3-pip \
    build-essential libxml2-dev libxslt1-dev zlib1g-dev \
    libssl-dev libffi-dev ca-certificates curl netcat-openbsd

install -d -m 0755 "$ROOT"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "[1/6] Descargando release estable oficial v4.0..."
if [ ! -d "$SRC" ]; then
    curl --fail --show-error --location --retry 3 \
        -o "$TMP/spiderfoot.tar.gz" "$ARCHIVE_URL"
    tar -xzf "$TMP/spiderfoot.tar.gz" -C "$ROOT"
fi

echo "[2/6] Creando entorno virtual aislado..."
if [ ! -x "$VENV/bin/python" ]; then
    python3 -m venv "$VENV"
fi

echo "[3/6] Preparando dependencias compatibles..."
"$VENV/bin/python" -m pip install --upgrade "pip<25" "setuptools<70" wheel "Cython<3"
# SpiderFoot 4.0 fija PyYAML <6. La instalaciÃ³n sin build isolation evita
# problemas conocidos de construcciÃ³n con Cython moderno.
"$VENV/bin/python" -m pip install --no-build-isolation "PyYAML>=5.4.1,<6"
"$VENV/bin/python" -m pip install --upgrade -r "$SRC/requirements.txt"

echo "[4/6] Creando lanzador del servidor local..."
cat >/usr/local/bin/mobpsy-spiderfoot-server <<EOF
#!/usr/bin/env bash
set -e
cd "$SRC"
exec "$VENV/bin/python" "$SRC/sf.py" -l 127.0.0.1:5001
EOF
chmod 0755 /usr/local/bin/mobpsy-spiderfoot-server

echo "[5/6] Creando lanzador grÃ¡fico..."
cat >/usr/local/bin/mobpsy-spiderfoot-ui <<'EOF'
#!/usr/bin/env bash
set -e

URL="http://127.0.0.1:5001"

if ! nc -z 127.0.0.1 5001 >/dev/null 2>&1; then
    nohup /usr/local/bin/mobpsy-spiderfoot-server \
        >"$HOME/.cache/mobpsy-spiderfoot.log" 2>&1 &
fi

for _ in $(seq 1 30); do
    if nc -z 127.0.0.1 5001 >/dev/null 2>&1; then
        xdg-open "$URL" >/dev/null 2>&1 &
        exit 0
    fi
    sleep 1
done

echo "SpiderFoot no pudo iniciar en 127.0.0.1:5001."
echo "Log: $HOME/.cache/mobpsy-spiderfoot.log"
exit 1
EOF
chmod 0755 /usr/local/bin/mobpsy-spiderfoot-ui
# MOBPSY_ALIAS_SPIDERFOOT_V1
ln -sf /usr/local/bin/mobpsy-spiderfoot-ui /usr/local/bin/mobpsy-spiderfoot

echo "[6/6] Verificando importaciÃ³n..."
cd "$SRC"
"$VENV/bin/python" -c 'import cherrypy, requests, yaml'

mkdir -p /etc/mobpsy
cat >/etc/mobpsy/spiderfoot <<EOF
TOOL=spiderfoot
METHOD=stable-release-python-venv
VERSION=4.0
BIND=127.0.0.1:5001
LAUNCHER=/usr/local/bin/mobpsy-spiderfoot-ui
EOF

echo "SpiderFoot 4.0 preparado."
