#!/usr/bin/env bash
set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive

KEY_URL="https://apt.vulns.sexy/kpcyrd.pgp"
KEY_ASC="/tmp/kpcyrd-sn0int-key.asc"
KEY_GPG_TMP="/tmp/apt-vulns-sexy.gpg.tmp"
KEY_GPG="/etc/apt/trusted.gpg.d/apt-vulns-sexy.gpg"
REPO_FILE="/etc/apt/sources.list.d/apt-vulns-sexy.list"

cleanup() {
    rm -f "$KEY_ASC" "$KEY_GPG_TMP"
}
trap cleanup EXIT

echo
echo "============================================================"
echo " MobPsy - Fase 12: sn0int (HOTFIX)"
echo "============================================================"
echo

echo "[1/7] Instalando herramientas necesarias..."
apt-get update
apt-get install -y curl sq ca-certificates

echo "[2/7] Descargando la clave del repositorio..."
rm -f "$KEY_ASC" "$KEY_GPG_TMP"

if ! curl \
    --fail \
    --show-error \
    --silent \
    --location \
    --retry 5 \
    --retry-delay 2 \
    --retry-all-errors \
    --connect-timeout 20 \
    --max-time 120 \
    --output "$KEY_ASC" \
    "$KEY_URL"; then
    echo
    echo "ERROR: no se pudo descargar la clave de sn0int desde:"
    echo "       $KEY_URL"
    exit 160
fi

if [ ! -s "$KEY_ASC" ]; then
    echo "ERROR: la clave descargada está vacía." >&2
    exit 161
fi

echo "      Clave descargada: $(wc -c < "$KEY_ASC") bytes"

echo "[3/7] Convirtiendo la clave OpenPGP al formato de APT..."
# El README oficial de sn0int usa exactamente la tubería:
# curl ... | sq dearmor | tee ...
# Aquí primero descargamos y validamos el fichero para evitar que `sq dearmor`
# reciba una entrada vacía y termine únicamente con "Error: EOF".
if ! sq dearmor < "$KEY_ASC" > "$KEY_GPG_TMP"; then
    echo
    echo "ERROR: sq no pudo convertir la clave descargada."
    echo "Primeras líneas recibidas (para diagnóstico):"
    echo "------------------------------------------------------------"
    head -n 5 "$KEY_ASC" || true
    echo "------------------------------------------------------------"
    exit 162
fi

if [ ! -s "$KEY_GPG_TMP" ]; then
    echo "ERROR: la clave desarmorizada quedó vacía." >&2
    exit 163
fi

install -m 0644 "$KEY_GPG_TMP" "$KEY_GPG"

echo "[4/7] Configurando el repositorio recomendado por sn0int..."
cat >"$REPO_FILE" <<'EOF'
deb http://apt.vulns.sexy stable main
EOF

echo "[5/7] Actualizando índices APT..."
if ! apt-get update; then
    echo
    echo "ERROR: APT no pudo actualizar el repositorio de sn0int."
    echo "Comprueba conectividad con apt.vulns.sexy."
    exit 164
fi

echo "[6/7] Instalando/actualizando sn0int..."
apt-get install -y sn0int

echo "[7/7] Verificando instalación..."
if ! command -v sn0int >/dev/null 2>&1; then
    echo "ERROR: APT terminó pero sn0int no está disponible." >&2
    exit 165
fi

cat >/usr/local/bin/mobpsy-sn0int <<'EOF'
#!/usr/bin/env bash
set -e
exec /usr/bin/sn0int "$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-sn0int

VERSION="$(/usr/local/bin/mobpsy-sn0int --version 2>&1 | head -n1 || true)"
/usr/local/bin/mobpsy-sn0int --help >/dev/null

mkdir -p /etc/mobpsy
cat >/etc/mobpsy/sn0int <<EOF
TOOL=sn0int
METHOD=signed-debian-repository
KEY_URL=${KEY_URL}
REPOSITORY=http://apt.vulns.sexy
VERSION=${VERSION}
LAUNCHER=/usr/local/bin/mobpsy-sn0int
EOF

echo
echo "${VERSION:-sn0int preparado correctamente}"
echo "sn0int instalado y verificado."
echo
