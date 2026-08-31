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
VERSION="$(/usr/bin/mediainfo --Version | head -n1)"

mkdir -p /etc/mobpsy
cat >/etc/mobpsy/mediainfo <<EOF
TOOL=mediainfo
METHOD=mediaarea-apt-repository
VERSION=${VERSION}
LAUNCHER=/usr/local/bin/mobpsy-mediainfo
EOF

echo "$VERSION"
