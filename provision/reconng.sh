#!/usr/bin/env bash
set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive

ROOT="/opt/mobpsy/tools/recon-ng"
SRC="$ROOT/src"
VENV="$ROOT/venv"
REPO="https://github.com/lanmaster53/recon-ng.git"

echo
echo "============================================================"
echo " MobPsy - Fase 12: Recon-ng"
echo "============================================================"

apt-get update
apt-get install -y \
    git python3 python3-venv python3-pip \
    build-essential libxml2-dev libxslt1-dev zlib1g-dev \
    ca-certificates

install -d -m 0755 "$ROOT"

echo "[1/5] Sincronizando repositorio oficial..."
if [ ! -d "$SRC/.git" ]; then
    rm -rf "$SRC"
    git clone "$REPO" "$SRC"
else
    BRANCH="$(git -C "$SRC" remote show origin | sed -n '/HEAD branch/s/.*: //p')"
    [ -n "$BRANCH" ] || BRANCH="master"
    git -C "$SRC" fetch origin "$BRANCH"
    git -C "$SRC" reset --hard "origin/$BRANCH"
    git -C "$SRC" clean -fd
fi
COMMIT="$(git -C "$SRC" rev-parse HEAD)"

echo "[2/5] Creando entorno virtual..."
if [ ! -x "$VENV/bin/python" ]; then
    python3 -m venv "$VENV"
fi
"$VENV/bin/python" -m pip install --upgrade pip setuptools wheel

echo "[3/5] Instalando dependencias..."
"$VENV/bin/python" -m pip install --upgrade -r "$SRC/REQUIREMENTS"

echo "[4/5] Creando lanzador..."
cat >/usr/local/bin/mobpsy-recon-ng <<EOF
#!/usr/bin/env bash
set -e
cd "$SRC"
exec "$VENV/bin/python" "$SRC/recon-ng" "\$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-recon-ng
# MOBPSY_ALIAS_RECONNG_V1
ln -sf /usr/local/bin/mobpsy-recon-ng /usr/local/bin/mobpsy-reconng

echo "[5/5] Verificando..."
/usr/local/bin/mobpsy-recon-ng -h >/dev/null

VERSION="$(grep -E "__version__" "$SRC/VERSION" | head -n1 | sed -E "s/.*'([^']+)'.*/\1/" || true)"

mkdir -p /etc/mobpsy
cat >/etc/mobpsy/recon-ng <<EOF
TOOL=recon-ng
METHOD=git-python-venv
REPOSITORY=${REPO}
COMMIT=${COMMIT}
VERSION=${VERSION}
LAUNCHER=/usr/local/bin/mobpsy-recon-ng
EOF

echo "Recon-ng ${VERSION:-git} preparado."
