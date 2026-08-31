#!/usr/bin/env bash
set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive

echo
echo "============================================================"
echo " MobPsy - Fase 7: ExifTool"
echo "============================================================"

apt-get update
apt-get install -y libimage-exiftool-perl

cat >/usr/local/bin/mobpsy-exiftool <<'EOF'
#!/usr/bin/env bash
set -e
exec /usr/bin/exiftool "$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-exiftool

VERSION="$(/usr/bin/exiftool -ver)"

mkdir -p /etc/mobpsy
cat >/etc/mobpsy/exiftool <<EOF
TOOL=exiftool
METHOD=apt
PACKAGE=libimage-exiftool-perl
VERSION=${VERSION}
LAUNCHER=/usr/local/bin/mobpsy-exiftool
EOF

echo "ExifTool ${VERSION} instalado."
