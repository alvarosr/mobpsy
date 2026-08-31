#!/usr/bin/env bash
set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive

ROOT="/opt/mobpsy/tools/crosslinked"
SRC="$ROOT/src"
VENV="$ROOT/venv"
REPO="https://github.com/m8sec/CrossLinked.git"
WORK="/home/mobpsy/MobPsy/Temporal/crosslinked-last"

echo
echo "============================================================"
echo " MobPsy - Fase 10: CrossLinked"
echo "============================================================"

apt-get update
apt-get install -y git python3 python3-venv python3-pip ca-certificates

install -d -m 0755 "$ROOT"
install -d -o mobpsy -g mobpsy "$WORK"

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

echo "[3/5] Instalando CrossLinked..."
"$VENV/bin/python" -m pip install --upgrade "$SRC"

if [ ! -x "$VENV/bin/crosslinked" ]; then
    echo "ERROR: no apareció el ejecutable crosslinked." >&2
    exit 140
fi

echo "[4/5] Creando lanzador estable..."
cat >/usr/local/bin/mobpsy-crosslinked <<EOF
#!/usr/bin/env bash
set -e
mkdir -p "$WORK"
cd "$WORK"
rm -f names.txt names.csv
exec "$VENV/bin/crosslinked" "\$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-crosslinked

echo "[5/5] Verificando..."
/usr/local/bin/mobpsy-crosslinked -h >/dev/null

mkdir -p /etc/mobpsy
cat >/etc/mobpsy/crosslinked <<EOF
TOOL=crosslinked
METHOD=git-python-venv
REPOSITORY=${REPO}
COMMIT=${COMMIT}
LAUNCHER=/usr/local/bin/mobpsy-crosslinked
EOF

echo "CrossLinked preparado (${COMMIT})."
