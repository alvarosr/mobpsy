#!/usr/bin/env bash
set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive

REPO_DEB="https://mediaarea.net/repo/deb/repo-mediaarea_1.0-27_all.deb"

echo
echo "============================================================"
echo " MobPsy - Fase 7: MediaInfo"
echo "============================================================"

apt-get update
apt-get install -y ca-certificates wget

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "[1/3] Configurando repositorio oficial MediaArea..."
wget -q -O "$TMP/repo-mediaarea.deb" "$REPO_DEB"
dpkg -i "$TMP/repo-mediaarea.deb"
apt-get update

echo "[2/3] Instalando/actualizando MediaInfo..."
apt-get install -y mediainfo

cat >/usr/local/bin/mobpsy-mediainfo <<'EOF'
#!/usr/bin/env bash
set -e
exec /usr/bin/mediainfo "$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-mediainfo

echo "[3/3] Verificando..."

# No usar "mediainfo --Version | head -n1" con "set -o pipefail":
# head puede cerrar la tubería antes de que MediaInfo termine y provocar
# SIGPIPE, haciendo que el provisionador falle aunque MediaInfo esté bien.
if ! command -v /usr/bin/mediainfo >/dev/null 2>&1; then
    echo "ERROR: MediaInfo no está disponible tras la instalación." >&2
    exit 71
fi

if ! VERSION_OUTPUT="$(timeout --foreground 15s /usr/bin/mediainfo --Version 2>&1)"; then
    RC=$?
    if [ "$RC" -eq 124 ]; then
        echo "ERROR: MediaInfo no respondió en 15 segundos." >&2
    else
        echo "ERROR: MediaInfo no supera la comprobación de versión (código $RC)." >&2
        printf '%s\n' "$VERSION_OUTPUT" >&2
    fi
    exit 72
fi

# Obtener la primera línea sin crear una tubería que pueda disparar pipefail.
VERSION="${VERSION_OUTPUT%%$'\n'*}"
[ -n "$VERSION" ] || VERSION="MediaInfo instalado"

# Validar también el lanzador estable de MobPsy sin necesitar un archivo real.
if ! timeout --foreground 15s /usr/local/bin/mobpsy-mediainfo --Version >/dev/null 2>&1; then
    RC=$?
    if [ "$RC" -eq 124 ]; then
        echo "ERROR: el lanzador mobpsy-mediainfo no respondió en 15 segundos." >&2
    else
        echo "ERROR: el lanzador mobpsy-mediainfo falló (código $RC)." >&2
    fi
    exit 73
fi

mkdir -p /etc/mobpsy
cat >/etc/mobpsy/mediainfo <<EOF
TOOL=mediainfo
METHOD=mediaarea-apt-repository
VERSION=${VERSION}
LAUNCHER=/usr/local/bin/mobpsy-mediainfo
EOF

echo "      MediaInfo: OK"
echo "      $VERSION"
