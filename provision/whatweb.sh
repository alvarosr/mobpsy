#!/usr/bin/env bash
set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive

ROOT="/opt/mobpsy/tools/whatweb"
SRC="$ROOT/src"
REPO="https://github.com/urbanadventurer/WhatWeb.git"

echo
echo "============================================================"
echo " MobPsy - WhatWeb (HOTFIX)"
echo "============================================================"
echo

echo "[1/6] Instalando Ruby y dependencias del sistema..."
apt-get update
apt-get install -y \
    git \
    ruby \
    ruby-dev \
    build-essential \
    ca-certificates \
    libssl-dev \
    zlib1g-dev

install -d -m 0755 "$ROOT"

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
chmod +x "$SRC/whatweb"

echo "[3/6] Instalando las gems requeridas por WhatWeb..."
# WhatWeb comprueba explícitamente ipaddr, addressable y json al arrancar.
# getoptlong se instala también de forma explícita para no depender de si
# la versión de Ruby lo distribuye como librería/default gem.
gem install --no-document ipaddr addressable json getoptlong

echo "[4/6] Comprobando dependencias Ruby..."
ruby -e '
require "getoptlong"
require "ipaddr"
require "addressable"
require "json"
puts "Dependencias Ruby: OK"
'

echo "[5/6] Creando lanzador estable para MobPsy..."
cat >/usr/local/bin/mobpsy-whatweb <<EOF
#!/usr/bin/env bash
set -e
cd "$SRC"
exec "$SRC/whatweb" "\$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-whatweb

echo "[6/6] Verificando WhatWeb..."
VERIFY_LOG="$(mktemp)"
if ! /usr/local/bin/mobpsy-whatweb --version >"$VERIFY_LOG" 2>&1; then
    echo
    echo "ERROR: WhatWeb no pudo arrancar. Salida real:"
    echo "------------------------------------------------------------"
    cat "$VERIFY_LOG"
    echo "------------------------------------------------------------"
    rm -f "$VERIFY_LOG"
    exit 110
fi

VERSION_OUT="$(cat "$VERIFY_LOG" | head -n 1)"
rm -f "$VERIFY_LOG"

if [ -z "$VERSION_OUT" ]; then
    echo "ERROR: WhatWeb arrancó pero no devolvió información de versión." >&2
    exit 111
fi

mkdir -p /etc/mobpsy
cat >/etc/mobpsy/whatweb <<EOF
TOOL=whatweb
METHOD=git-ruby-gems
REPOSITORY=${REPO}
COMMIT=${COMMIT}
VERSION=${VERSION_OUT}
LAUNCHER=/usr/local/bin/mobpsy-whatweb
EOF

echo
echo "$VERSION_OUT"
echo "WhatWeb preparado correctamente."
echo
