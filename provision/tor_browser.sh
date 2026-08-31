#!/usr/bin/env bash
set -Eeuo pipefail

export DEBIAN_FRONTEND=noninteractive
META_URL="https://aus1.torproject.org/torbrowser/update_3/release/download-linux-x86_64.json"
USER_NAME="mobpsy"
USER_HOME="/home/${USER_NAME}"
INSTALL_ROOT="${USER_HOME}/.local/share/mobpsy"
INSTALL_DIR="${INSTALL_ROOT}/tor-browser"
VERSION_FILE="${INSTALL_ROOT}/tor-browser-version"
APP_DIR="${USER_HOME}/.local/share/applications"

echo
echo "============================================================"
echo " MobPsy - Fase 2: Tor Browser"
echo "============================================================"
echo

echo "[1/7] Instalando dependencias..."
apt-get update
apt-get install -y ca-certificates curl jq xz-utils gnupg dirmngr

echo "[2/7] Consultando la versión estable oficial..."
META="$(curl --fail --silent --show-error --location "$META_URL")"
VERSION="$(printf '%s' "$META" | jq -r '.version')"
BINARY_URL="$(printf '%s' "$META" | jq -r '.binary')"
SIG_URL="$(printf '%s' "$META" | jq -r '.sig')"

for v in "$VERSION" "$BINARY_URL" "$SIG_URL"; do
    if [ -z "$v" ] || [ "$v" = "null" ]; then
        echo "ERROR: Tor Project no devolvió metadatos válidos." >&2
        exit 30
    fi
done

echo "      Versión disponible: $VERSION"

if [ -x "${INSTALL_DIR}/start-tor-browser.desktop" ]; then
    INSTALLED="desconocida"
    [ -f "$VERSION_FILE" ] && INSTALLED="$(cat "$VERSION_FILE")"
    echo "Tor Browser ya está instalado (versión registrada: ${INSTALLED})."
    echo "No se reemplazará automáticamente en esta fase."
    exit 0
fi

WORK="$(mktemp -d)"
GNUPGHOME_TMP="${WORK}/gnupg"
mkdir -m 700 "$GNUPGHOME_TMP"
trap 'rm -rf "$WORK"' EXIT

ARCHIVE="${WORK}/tor-browser.tar.xz"
SIGNATURE="${ARCHIVE}.asc"

echo "[3/7] Descargando Tor Browser desde Tor Project..."
curl --fail --show-error --location --retry 3 --output "$ARCHIVE" "$BINARY_URL"
curl --fail --show-error --location --retry 3 --output "$SIGNATURE" "$SIG_URL"

echo "[4/7] Obteniendo la clave oficial de Tor Browser Developers..."
gpg --batch --homedir "$GNUPGHOME_TMP" \
    --auto-key-locate nodefault,wkd \
    --locate-keys torbrowser@torproject.org

EXPECTED_FPR="EF6E286DDA85EA2A4BA7DE684E2C6E8793298290"
if ! gpg --batch --homedir "$GNUPGHOME_TMP" --with-colons --fingerprint \
    | grep -qi "$EXPECTED_FPR"; then
    echo "ERROR: El fingerprint de la clave no coincide con el oficial." >&2
    exit 31
fi

echo "[5/7] Verificando firma OpenPGP..."
gpg --batch --homedir "$GNUPGHOME_TMP" --verify "$SIGNATURE" "$ARCHIVE"

echo "[6/7] Instalando Tor Browser para mobpsy..."
mkdir -p "$INSTALL_ROOT" "$APP_DIR"
EXTRACT_DIR="${WORK}/extract"
mkdir -p "$EXTRACT_DIR"
tar -xf "$ARCHIVE" -C "$EXTRACT_DIR"
TOP_DIR="$(find "$EXTRACT_DIR" -mindepth 1 -maxdepth 1 -type d | head -n 1)"

if [ -z "$TOP_DIR" ] || [ ! -x "${TOP_DIR}/start-tor-browser.desktop" ]; then
    echo "ERROR: El archivo descargado no tiene la estructura esperada." >&2
    exit 32
fi

rm -rf "$INSTALL_DIR"
mv "$TOP_DIR" "$INSTALL_DIR"
printf '%s\n' "$VERSION" > "$VERSION_FILE"
chown -R "${USER_NAME}:${USER_NAME}" "$INSTALL_ROOT"

echo "[7/7] Registrando Tor Browser como aplicación de escritorio..."
runuser -u "$USER_NAME" -- bash -lc \
    "cd '$INSTALL_DIR' && ./start-tor-browser.desktop --register-app"

install -d -o "$USER_NAME" -g "$USER_NAME" "${USER_HOME}/.config/autostart"
mkdir -p /usr/local/lib/mobpsy
cat >/usr/local/lib/mobpsy/first-login-fase2.sh <<'EOF'
#!/usr/bin/env bash
set -u
MARKER="$HOME/.config/mobpsy/fase2-login.done"
mkdir -p "$HOME/.config/mobpsy"
[ -f "$MARKER" ] && exit 0
sleep 8
TOR_DESKTOP="$(find "$HOME/.local/share/applications" -maxdepth 1 -type f \
    \( -iname '*tor*browser*.desktop' -o -iname 'start-tor-browser.desktop' \) \
    -printf '%f\n' 2>/dev/null | head -n 1)"
if [ -n "$TOR_DESKTOP" ]; then
    gsettings set org.gnome.shell favorite-apps \
      "['firefox_firefox.desktop', 'chromium_chromium.desktop', '$TOR_DESKTOP', 'org.gnome.Nautilus.desktop', 'org.gnome.Terminal.desktop']" \
      2>/dev/null || true
fi
touch "$MARKER"
EOF
chmod 0755 /usr/local/lib/mobpsy/first-login-fase2.sh

cat >"${USER_HOME}/.config/autostart/mobpsy-first-login-fase2.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=MobPsy - configuración Tor Browser
Exec=/usr/local/lib/mobpsy/first-login-fase2.sh
Terminal=false
X-GNOME-Autostart-enabled=true
NoDisplay=true
EOF
chown -R "${USER_NAME}:${USER_NAME}" "${USER_HOME}/.config"

mkdir -p /etc/mobpsy
cat >/etc/mobpsy/release <<'EOF'
MOBPSY_PHASE=2
MOBPSY_RELEASE=browsers
EOF

echo
echo "============================================================"
echo " Tor Browser $VERSION instalado y verificado correctamente."
echo "============================================================"
echo
