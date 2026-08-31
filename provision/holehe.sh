#!/usr/bin/env bash
set -Eeuo pipefail

export DEBIAN_FRONTEND=noninteractive

TOOL_ROOT="/opt/mobpsy/tools/holehe"
SRC_DIR="${TOOL_ROOT}/src"
VENV="${TOOL_ROOT}/venv"
REPO="https://github.com/megadose/holehe.git"

echo
echo "============================================================"
echo " MobPsy - Fase 6: Holehe"
echo "============================================================"
echo

echo "[1/6] Instalando dependencias base..."
apt-get update
apt-get install -y \
    git \
    ca-certificates \
    python3 \
    python3-venv \
    python3-pip \
    build-essential

echo "[2/6] Sincronizando el repositorio oficial de Holehe..."
install -d -m 0755 "$TOOL_ROOT"

if [ ! -d "${SRC_DIR}/.git" ]; then
    rm -rf "$SRC_DIR"
    git clone --depth 1 "$REPO" "$SRC_DIR"
else
    git -C "$SRC_DIR" fetch --depth 1 origin master
    git -C "$SRC_DIR" reset --hard origin/master
    git -C "$SRC_DIR" clean -fd
fi

COMMIT="$(git -C "$SRC_DIR" rev-parse HEAD)"

echo "[3/6] Creando entorno virtual aislado..."
if [ ! -x "${VENV}/bin/python" ]; then
    python3 -m venv "$VENV"
fi

"${VENV}/bin/python" -m pip install --upgrade pip setuptools wheel

echo "[4/6] Instalando Holehe y compatibilidad de dependencias..."
"${VENV}/bin/python" -m pip install --upgrade "$SRC_DIR"

# El setup.py oficial no declara algunas dependencias que determinadas
# revisiones/módulos han requerido. Las dejamos explícitas dentro del venv,
# sin contaminar el Python del sistema.
"${VENV}/bin/python" -m pip install --upgrade requests httpx trio

if [ ! -x "${VENV}/bin/holehe" ]; then
    echo "ERROR: Holehe se instaló pero no apareció el ejecutable." >&2
    exit 70
fi

echo "[5/6] Creando lanzador estable para MobPsy..."
cat >/usr/local/bin/mobpsy-holehe <<EOF
#!/usr/bin/env bash
set -e
export PYTHONUNBUFFERED=1
exec "${VENV}/bin/holehe" "\$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-holehe

echo "[6/6] Verificando importación y registrando versión..."
VERSION="$("${VENV}/bin/python" - <<'PY'
import holehe.core
print(getattr(holehe.core, "__version__", "desconocida"))
PY
)"

"${VENV}/bin/python" -c 'import holehe, holehe.core, httpx, trio, requests'

mkdir -p /etc/mobpsy
cat >/etc/mobpsy/holehe <<EOF
TOOL=holehe
METHOD=git-python-venv
REPOSITORY=${REPO}
COMMIT=${COMMIT}
VERSION=${VERSION}
LAUNCHER=/usr/local/bin/mobpsy-holehe
EOF

echo "      Holehe ${VERSION}"
echo "      Commit ${COMMIT}"
echo
echo "Holehe preparado para MobPsy."
echo
