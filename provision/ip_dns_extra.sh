#!/usr/bin/env bash
set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive

echo
echo "============================================================"
echo " MobPsy - Fase 15: IPs + DNS"
echo "============================================================"
echo

echo "[1/4] Instalando herramientas base..."
apt-get update
apt-get install -y whois dnsutils geoip-bin geoip-database

echo "[2/4] Creando lanzadores globales..."
cat >/usr/local/bin/mobpsy-whois <<'EOF'
#!/usr/bin/env bash
set -e
exec /usr/bin/whois "$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-whois

cat >/usr/local/bin/mobpsy-dig <<'EOF'
#!/usr/bin/env bash
set -e
exec /usr/bin/dig "$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-dig

cat >/usr/local/bin/mobpsy-host <<'EOF'
#!/usr/bin/env bash
set -e
exec /usr/bin/host "$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-host

cat >/usr/local/bin/mobpsy-geoiplookup <<'EOF'
#!/usr/bin/env bash
set -e
exec /usr/bin/geoiplookup "$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-geoiplookup

echo "[3/4] Registrando inventario..."
mkdir -p /etc/mobpsy
cat >/etc/mobpsy/ip_dns <<'EOF'
TOOLS=whois,dig,host,geoiplookup
PHASE=15
EOF

echo "[4/4] Verificando..."
command -v /usr/local/bin/mobpsy-whois >/dev/null
command -v /usr/local/bin/mobpsy-dig >/dev/null
command -v /usr/local/bin/mobpsy-host >/dev/null
command -v /usr/local/bin/mobpsy-geoiplookup >/dev/null

/usr/local/bin/mobpsy-whois --help >/dev/null 2>&1 || true
/usr/local/bin/mobpsy-dig -h >/dev/null 2>&1 || true
/usr/local/bin/mobpsy-host -h >/dev/null 2>&1 || true
/usr/local/bin/mobpsy-geoiplookup -h >/dev/null 2>&1 || true

echo
echo "Herramientas de IPs y DNS instaladas."
echo
