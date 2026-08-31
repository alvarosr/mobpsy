#!/usr/bin/env bash
set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive

ROOT="/opt/mobpsy/tools/clatscope"
SRC="$ROOT/src"
VENV="$ROOT/venv"
REPO="https://github.com/Clats97/ClatScope.git"

echo
echo "============================================================"
echo " MobPsy - Fase 11: ClatScope"
echo "============================================================"

apt-get update
apt-get install -y \
    git python3 python3-venv python3-pip ca-certificates \
    libmagic1 build-essential

install -d -m 0755 "$ROOT"

echo "[1/5] Sincronizando repositorio oficial..."
if [ ! -d "$SRC/.git" ]; then
    rm -rf "$SRC"
    git clone "$REPO" "$SRC"
else
    BRANCH="$(git -C "$SRC" remote show origin | sed -n '/HEAD branch/s/.*: //p')"
    [ -n "$BRANCH" ] || BRANCH="main"
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
if [ -f "$SRC/requirements.txt" ]; then
    # El repositorio puede listar paquetes específicos de Windows.
    # Intentamos requirements y, si falla por python-magic-bin, instalamos
    # las dependencias declaradas por el README compatibles con Linux.
    if ! "$VENV/bin/python" -m pip install --upgrade -r "$SRC/requirements.txt"; then
        "$VENV/bin/python" -m pip install --upgrade \
            requests urllib3 pystyle tqdm phonenumbers dnspython \
            email_validator beautifulsoup4 lxml python-whois python-magic \
            Pillow PyPDF2 openpyxl python-docx python-pptx mutagen tinytag \
            argon2-cffi passlib
    fi
fi

echo "[4/5] Detectando script principal..."
MAIN="$(find "$SRC" -maxdepth 1 -type f -name 'ClatScope Info Tool*.py' -print -quit)"
if [ -z "$MAIN" ]; then
    echo "ERROR: no se encontró el script principal de ClatScope." >&2
    exit 150
fi

cat >/usr/local/bin/mobpsy-clatscope <<EOF
#!/usr/bin/env bash
set -e
cd "$SRC"
exec "$VENV/bin/python" "$MAIN" "\$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-clatscope

echo "[5/5] Registrando instalación..."
mkdir -p /etc/mobpsy
cat >/etc/mobpsy/clatscope <<EOF
TOOL=clatscope
METHOD=git-python-venv-interactive
REPOSITORY=${REPO}
COMMIT=${COMMIT}
LAUNCHER=/usr/local/bin/mobpsy-clatscope
EOF

echo "ClatScope preparado (${COMMIT})."
