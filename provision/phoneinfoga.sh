#!/usr/bin/env bash
set -Eeuo pipefail

export DEBIAN_FRONTEND=noninteractive

ROOT="/opt/mobpsy/tools/phoneinfoga"
API="https://api.github.com/repos/sundowndev/phoneinfoga/releases/latest"

echo
echo "============================================================"
echo " MobPsy - Fase 7: PhoneInfoga"
echo "============================================================"

apt-get update
apt-get install -y ca-certificates curl jq tar coreutils

install -d -m 0755 "$ROOT"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "[1/5] Consultando la última release oficial..."
JSON="$(curl --fail --silent --show-error --location \
    -H 'Accept: application/vnd.github+json' \
    -H 'User-Agent: MobPsy-Installer' \
    "$API")"

VERSION="$(printf '%s' "$JSON" | jq -r '.tag_name')"
ARCHIVE_URL="$(printf '%s' "$JSON" | jq -r \
    '.assets[] | select(.name=="phoneinfoga_Linux_x86_64.tar.gz") | .browser_download_url' | head -n1)"
CHECKSUM_URL="$(printf '%s' "$JSON" | jq -r \
    '.assets[] | select(.name=="phoneinfoga_checksums.txt") | .browser_download_url' | head -n1)"

if [ -z "$VERSION" ] || [ "$VERSION" = "null" ] || \
   [ -z "$ARCHIVE_URL" ] || [ -z "$CHECKSUM_URL" ]; then
    echo "ERROR: no se pudieron localizar los assets Linux x86_64." >&2
    exit 80
fi

echo "      Versión: $VERSION"

echo "[2/5] Descargando binario y checksums..."
curl --fail --show-error --location --retry 3 \
    -o "$TMP/phoneinfoga.tar.gz" "$ARCHIVE_URL"
curl --fail --show-error --location --retry 3 \
    -o "$TMP/checksums.txt" "$CHECKSUM_URL"

echo "[3/5] Verificando SHA-256 publicado con la release..."
EXPECTED="$(grep -E 'phoneinfoga_Linux_x86_64\.tar\.gz$' "$TMP/checksums.txt" | awk '{print $1}' | head -n1)"
ACTUAL="$(sha256sum "$TMP/phoneinfoga.tar.gz" | awk '{print $1}')"

if [ -z "$EXPECTED" ] || [ "$EXPECTED" != "$ACTUAL" ]; then
    echo "ERROR: checksum de PhoneInfoga no válido." >&2
    exit 81
fi

echo "[4/5] Instalando binario..."
mkdir -p "$TMP/extract"
tar -xzf "$TMP/phoneinfoga.tar.gz" -C "$TMP/extract"
BIN="$(find "$TMP/extract" -type f -name phoneinfoga -print -quit)"

if [ -z "$BIN" ]; then
    echo "ERROR: no se encontró el binario phoneinfoga." >&2
    exit 82
fi

install -m 0755 "$BIN" "$ROOT/phoneinfoga"

cat >/usr/local/bin/mobpsy-phoneinfoga <<EOF
#!/usr/bin/env bash
set -e
exec "$ROOT/phoneinfoga" "\$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-phoneinfoga

echo "[5/5] Verificando..."
/usr/local/bin/mobpsy-phoneinfoga version

mkdir -p /etc/mobpsy
cat >/etc/mobpsy/phoneinfoga <<EOF
TOOL=phoneinfoga
METHOD=github-release-binary
VERSION=${VERSION}
CHECKSUM=${ACTUAL}
LAUNCHER=/usr/local/bin/mobpsy-phoneinfoga
EOF

echo "PhoneInfoga $VERSION instalado."
