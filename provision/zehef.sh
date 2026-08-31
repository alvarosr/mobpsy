#!/usr/bin/env bash
set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive

ROOT="/opt/mobpsy/tools/zehef"
SRC="$ROOT/src"
VENV="$ROOT/venv"
REPO="https://github.com/N0rz3/Zehef.git"

echo
echo "============================================================"
echo " MobPsy - Fase 10: Zehef"
echo "============================================================"

apt-get update
apt-get install -y git python3 python3-venv python3-pip ca-certificates

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
"$VENV/bin/python" -m pip install --upgrade -r "$SRC/requirements.txt"

echo "[4/5] Creando lanzador estable..."
# Ejecutamos desde el propio repositorio porque Zehef tiene cÃ³digo que espera
# encontrar config.json relativo al directorio de trabajo.
cat >/usr/local/bin/mobpsy-zehef <<EOF
#!/usr/bin/env bash
set -e
cd "$SRC"
exec "$VENV/bin/python" "$SRC/zehef.py" "\$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-zehef

# MOBPSY_ZEHEF_CONFIG_PERMISSION_FIX_V1
# Zehef abre config.json con r+ durante el comprobador de versión.
# Debe poder escribirlo el usuario que ejecuta MobPsy.
if id mobpsy >/dev/null 2>&1 && [ -f "$SRC/config.json" ]; then
    chown mobpsy:mobpsy "$SRC/config.json"
    chmod 0664 "$SRC/config.json"
fi

echo "[5/5] Verificando..."
/usr/local/bin/mobpsy-zehef -h >/dev/null

mkdir -p /etc/mobpsy
cat >/etc/mobpsy/zehef <<EOF
TOOL=zehef
METHOD=git-python-venv
REPOSITORY=${REPO}
COMMIT=${COMMIT}
LAUNCHER=/usr/local/bin/mobpsy-zehef
EOF

echo "Zehef preparado (${COMMIT})."
