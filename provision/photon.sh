#!/usr/bin/env bash
set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive

ROOT="/opt/mobpsy/tools/photon"
SRC="$ROOT/src"
VENV="$ROOT/venv"
REPO="https://github.com/s0md3v/Photon.git"
OUTPUT="/home/mobpsy/MobPsy/Temporal/photon-last"

echo
echo "============================================================"
echo " MobPsy - Fase 9: Photon"
echo "============================================================"

apt-get update
apt-get install -y \
    git \
    python3 \
    python3-venv \
    python3-pip \
    ca-certificates

install -d -m 0755 "$ROOT"

echo "[1/5] Sincronizando repositorio oficial..."
if [ ! -d "$SRC/.git" ]; then
    rm -rf "$SRC"
    git clone "$REPO" "$SRC"
else
    DEFAULT_BRANCH="$(git -C "$SRC" remote show origin | sed -n '/HEAD branch/s/.*: //p')"
    [ -n "$DEFAULT_BRANCH" ] || DEFAULT_BRANCH="master"
    git -C "$SRC" fetch origin "$DEFAULT_BRANCH"
    git -C "$SRC" reset --hard "origin/$DEFAULT_BRANCH"
    git -C "$SRC" clean -fd
fi

COMMIT="$(git -C "$SRC" rev-parse HEAD)"

echo "[2/5] Creando entorno virtual..."
if [ ! -x "$VENV/bin/python" ]; then
    python3 -m venv "$VENV"
fi
"$VENV/bin/python" -m pip install --upgrade pip setuptools wheel

echo "[3/5] Instalando dependencias oficiales..."
"$VENV/bin/python" -m pip install --upgrade -r "$SRC/requirements.txt"

echo "[4/5] Creando lanzador estable..."
install -d -o mobpsy -g mobpsy "$OUTPUT"

cat >/usr/local/bin/mobpsy-photon <<EOF
#!/usr/bin/env bash
set -e
exec "$VENV/bin/python" "$SRC/photon.py" "\$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-photon

echo "[5/5] Verificando..."
/usr/local/bin/mobpsy-photon -h >/dev/null

mkdir -p /etc/mobpsy
cat >/etc/mobpsy/photon <<EOF
TOOL=photon
METHOD=git-python-venv
REPOSITORY=${REPO}
COMMIT=${COMMIT}
LAUNCHER=/usr/local/bin/mobpsy-photon
EOF

echo "Photon preparado (${COMMIT})."
