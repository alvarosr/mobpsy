#!/usr/bin/env bash
set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive

ROOT="/opt/mobpsy/tools/subfinder"
API="https://api.github.com/repos/projectdiscovery/subfinder/releases/latest"

echo
echo "============================================================"
echo " MobPsy - Fase 8: Subfinder"
echo "============================================================"

apt-get update
apt-get install -y ca-certificates curl jq unzip coreutils

install -d -m 0755 "$ROOT"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "[1/5] Consultando release oficial..."
JSON="$(curl --fail --silent --show-error --location \
    -H 'Accept: application/vnd.github+json' \
    -H 'User-Agent: MobPsy-Installer' \
    "$API")"

VERSION="$(printf '%s' "$JSON" | jq -r '.tag_name')"
ARCHIVE_NAME="$(printf '%s' "$JSON" | jq -r \
    '.assets[].name | select(test("linux_amd64\\.zip$"))' | head -n1)"
ARCHIVE_URL="$(printf '%s' "$JSON" | jq -r --arg n "$ARCHIVE_NAME" \
    '.assets[] | select(.name==$n) | .browser_download_url' | head -n1)"
CHECKSUM_NAME="$(printf '%s' "$JSON" | jq -r \
    '.assets[].name | select(test("checksums\\.txt$"))' | head -n1)"
CHECKSUM_URL="$(printf '%s' "$JSON" | jq -r --arg n "$CHECKSUM_NAME" \
    '.assets[] | select(.name==$n) | .browser_download_url' | head -n1)"

if [ -z "$ARCHIVE_NAME" ] || [ -z "$ARCHIVE_URL" ] || \
   [ -z "$CHECKSUM_NAME" ] || [ -z "$CHECKSUM_URL" ]; then
    echo "ERROR: no se encontraron assets Linux amd64/checksums." >&2
    exit 90
fi

echo "      Versión: $VERSION"

echo "[2/5] Descargando binario y checksums..."
curl --fail --show-error --location --retry 3 \
    -o "$TMP/$ARCHIVE_NAME" "$ARCHIVE_URL"
curl --fail --show-error --location --retry 3 \
    -o "$TMP/$CHECKSUM_NAME" "$CHECKSUM_URL"

echo "[3/5] Verificando SHA-256..."
EXPECTED="$(grep -E "[[:space:]]${ARCHIVE_NAME}$" "$TMP/$CHECKSUM_NAME" | awk '{print $1}' | head -n1)"
ACTUAL="$(sha256sum "$TMP/$ARCHIVE_NAME" | awk '{print $1}')"

if [ -z "$EXPECTED" ] || [ "$EXPECTED" != "$ACTUAL" ]; then
    echo "ERROR: checksum de Subfinder no válido." >&2
    exit 91
fi

echo "[4/5] Instalando..."
mkdir -p "$TMP/extract"
unzip -q "$TMP/$ARCHIVE_NAME" -d "$TMP/extract"
BIN="$(find "$TMP/extract" -type f -name subfinder -print -quit)"
if [ -z "$BIN" ]; then
    echo "ERROR: no se encontró el binario subfinder." >&2
    exit 92
fi

install -m 0755 "$BIN" "$ROOT/subfinder"

cat >/usr/local/bin/mobpsy-subfinder <<EOF
#!/usr/bin/env bash
set -e
exec "$ROOT/subfinder" "\$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-subfinder

echo "[5/5] Verificando..."
VERSION_OUT="$(/usr/local/bin/mobpsy-subfinder -version 2>&1 | head -n1 || true)"

mkdir -p /etc/mobpsy
cat >/etc/mobpsy/subfinder <<EOF
TOOL=subfinder
METHOD=github-release-binary
VERSION=${VERSION}
CHECKSUM=${ACTUAL}
LAUNCHER=/usr/local/bin/mobpsy-subfinder
EOF

echo "${VERSION_OUT:-Subfinder $VERSION}"
