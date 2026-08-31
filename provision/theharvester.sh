#!/usr/bin/env bash
set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive

ROOT="/opt/mobpsy/tools/theharvester"
SRC="$ROOT/src"
UV_ROOT="/opt/mobpsy/uv"
UV_API="https://api.github.com/repos/astral-sh/uv/releases/latest"
REPO="https://github.com/laramies/theHarvester.git"

echo
echo "============================================================"
echo " MobPsy - Fase 9: theHarvester"
echo "============================================================"

apt-get update
apt-get install -y ca-certificates curl jq git tar

install -d -m 0755 "$ROOT" "$UV_ROOT"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "[1/6] Comprobando uv..."
if [ ! -x "$UV_ROOT/uv" ]; then
    JSON="$(curl --fail --silent --show-error --location \
        -H 'Accept: application/vnd.github+json' \
        -H 'User-Agent: MobPsy-Installer' \
        "$UV_API")"

    UV_URL="$(printf '%s' "$JSON" | jq -r \
        '.assets[] | select(.name=="uv-x86_64-unknown-linux-gnu.tar.gz") | .browser_download_url' | head -n1)"

    if [ -z "$UV_URL" ] || [ "$UV_URL" = "null" ]; then
        echo "ERROR: no se encontró uv para Linux x86_64." >&2
        exit 130
    fi

    curl --fail --show-error --location --retry 3 \
        -o "$TMP/uv.tar.gz" "$UV_URL"
    mkdir -p "$TMP/uv-extract"
    tar -xzf "$TMP/uv.tar.gz" -C "$TMP/uv-extract"

    UV_BIN="$(find "$TMP/uv-extract" -type f -name uv -print -quit)"
    [ -n "$UV_BIN" ] || { echo "ERROR: no se encontró uv." >&2; exit 131; }
    install -m 0755 "$UV_BIN" "$UV_ROOT/uv"
fi

echo "[2/6] Sincronizando repositorio oficial..."
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

DEFAULT_BRANCH="$(git -C "$SRC" remote show origin | sed -n '/HEAD branch/s/.*: //p')"
[ -n "$DEFAULT_BRANCH" ] || DEFAULT_BRANCH="master"
git -C "$SRC" fetch origin "$DEFAULT_BRANCH"
git -C "$SRC" reset --hard "origin/$DEFAULT_BRANCH"
COMMIT="$(git -C "$SRC" rev-parse HEAD)"

echo "[3/6] Preparando Python 3.14 aislado..."
export UV_PYTHON_INSTALL_DIR="$ROOT/python"
cd "$SRC"
"$UV_ROOT/uv" sync --frozen

echo "[4/6] Comprobando ejecutable..."
if [ ! -x "$SRC/.venv/bin/theHarvester" ]; then
    echo "ERROR: uv sync no creó theHarvester." >&2
    exit 132
fi

echo "[5/6] Creando lanzador estable..."
cat >/usr/local/bin/mobpsy-theharvester <<EOF
#!/usr/bin/env bash
set -e
cd "$SRC"
exec "$SRC/.venv/bin/theHarvester" "\$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-theharvester

echo "[6/6] Verificando..."
/usr/local/bin/mobpsy-theharvester -h >/dev/null

PYTHON_VERSION="$("$SRC/.venv/bin/python" --version 2>&1)"
mkdir -p /etc/mobpsy
cat >/etc/mobpsy/theharvester <<EOF
TOOL=theHarvester
METHOD=git-uv
REPOSITORY=${REPO}
COMMIT=${COMMIT}
PYTHON=${PYTHON_VERSION}
LAUNCHER=/usr/local/bin/mobpsy-theharvester
EOF

echo "theHarvester preparado (${COMMIT}, ${PYTHON_VERSION})."
