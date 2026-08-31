#!/usr/bin/env bash
set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive

ROOT="/opt/mobpsy/tools/dnsrecon"
SRC="$ROOT/src"
UV_ROOT="/opt/mobpsy/uv"
UV_API="https://api.github.com/repos/astral-sh/uv/releases/latest"
REPO="https://github.com/darkoperator/dnsrecon.git"

echo
echo "============================================================"
echo " MobPsy - Fase 8: DNSRecon"
echo "============================================================"

apt-get update
apt-get install -y ca-certificates curl jq git tar

install -d -m 0755 "$ROOT" "$UV_ROOT"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "[1/6] Instalando/actualizando uv..."
JSON="$(curl --fail --silent --show-error --location \
    -H 'Accept: application/vnd.github+json' \
    -H 'User-Agent: MobPsy-Installer' \
    "$UV_API")"

UV_URL="$(printf '%s' "$JSON" | jq -r \
    '.assets[] | select(.name=="uv-x86_64-unknown-linux-gnu.tar.gz") | .browser_download_url' | head -n1)"

if [ -z "$UV_URL" ] || [ "$UV_URL" = "null" ]; then
    echo "ERROR: no se encontró uv para Linux x86_64." >&2
    exit 100
fi

curl --fail --show-error --location --retry 3 \
    -o "$TMP/uv.tar.gz" "$UV_URL"
mkdir -p "$TMP/uv-extract"
tar -xzf "$TMP/uv.tar.gz" -C "$TMP/uv-extract"

UV_BIN="$(find "$TMP/uv-extract" -type f -name uv -print -quit)"
UVX_BIN="$(find "$TMP/uv-extract" -type f -name uvx -print -quit)"

if [ -z "$UV_BIN" ]; then
    echo "ERROR: no se encontró el binario uv." >&2
    exit 101
fi

install -m 0755 "$UV_BIN" "$UV_ROOT/uv"
if [ -n "$UVX_BIN" ]; then
    install -m 0755 "$UVX_BIN" "$UV_ROOT/uvx"
fi

echo "[2/6] Sincronizando repositorio oficial DNSRecon..."
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

echo "[3/6] Preparando Python 3.12 aislado con uv..."
export UV_PYTHON_INSTALL_DIR="$ROOT/python"
cd "$SRC"
"$UV_ROOT/uv" sync --python 3.12 --frozen

echo "[4/6] Comprobando ejecutable..."
if [ ! -x "$SRC/.venv/bin/dnsrecon" ]; then
    echo "ERROR: uv sync terminó sin crear dnsrecon." >&2
    exit 102
fi

echo "[5/6] Creando lanzador..."
cat >/usr/local/bin/mobpsy-dnsrecon <<EOF
#!/usr/bin/env bash
set -e
exec "$SRC/.venv/bin/dnsrecon" "\$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-dnsrecon

echo "[6/6] Registrando versión..."
VERSION="$("$SRC/.venv/bin/python" - <<'PY'
from importlib.metadata import version
try:
    print(version("dnsrecon"))
except Exception:
    print("git")
PY
)"

mkdir -p /etc/mobpsy
cat >/etc/mobpsy/dnsrecon <<EOF
TOOL=dnsrecon
METHOD=git-uv
REPOSITORY=${REPO}
COMMIT=${COMMIT}
VERSION=${VERSION}
PYTHON=3.12
LAUNCHER=/usr/local/bin/mobpsy-dnsrecon
EOF

echo "DNSRecon ${VERSION} (${COMMIT})"
