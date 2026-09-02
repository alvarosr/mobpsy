#!/usr/bin/env bash
set -Eeuo pipefail

export DEBIAN_FRONTEND=noninteractive

UPLOAD_DIR="/home/vagrant/mobpsy_app_upload"
INSTALL_ROOT="/opt/mobpsy"
APP_DIR="${INSTALL_ROOT}/app"
VENV_DIR="${INSTALL_ROOT}/venv"
USER_NAME="mobpsy"
USER_HOME="/home/${USER_NAME}"

echo
echo "============================================================"
echo " MobPsy 1.0.0 - Interfaz grÃƒÆ’Ã‚Â¡fica"
echo "============================================================"
echo

REQUIRED_GUI_FILES=(
    main.py
    requirements.txt
    case_context.py
    mobpsy_runtime_pages.py
    mobpsy_functional_pages.py
    mobpsy_update_page.py
)

missing_gui_files=()
for f in "${REQUIRED_GUI_FILES[@]}"; do
    if [ ! -f "${UPLOAD_DIR}/${f}" ]; then
        missing_gui_files+=("${f}")
    fi
done

if [ "${#missing_gui_files[@]}" -ne 0 ]; then
    echo "ERROR: el paquete de la GUI recibido por Vagrant está incompleto." >&2
    printf 'Falta: %s\n' "${missing_gui_files[@]}" >&2
    echo "Comprueba que la carpeta mobpsy_app del repositorio contiene todos los módulos." >&2
    exit 40
fi

echo "[1/7] Instalando Python y soporte para entornos virtuales..."
apt-get update
apt-get install -y \
    python3 \
    python3-venv \
    python3-pip \
    libgl1 \
    libegl1 \
    libxkbcommon-x11-0 \
    libxcb-cursor0 \
    libxcb-xinerama0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-render-util0

echo "[2/7] Instalando el cÃƒÆ’Ã‚Â³digo de MobPsy en /opt/mobpsy..."
install -d -m 0755 "$APP_DIR"
rm -rf "${APP_DIR:?}/"*
cp -a "${UPLOAD_DIR}/." "$APP_DIR/"
chown -R root:root "$INSTALL_ROOT"

echo "[3/7] Creando entorno virtual aislado..."
if [ ! -x "${VENV_DIR}/bin/python" ]; then
    python3 -m venv "$VENV_DIR"
fi

"${VENV_DIR}/bin/python" -m pip install --upgrade pip setuptools wheel

echo "[4/7] Instalando PySide6 dentro del entorno virtual..."
"${VENV_DIR}/bin/python" -m pip install --upgrade -r "${APP_DIR}/requirements.txt"

echo "[5/8] Validando que Qt para Python puede importarse..."
"${VENV_DIR}/bin/python" - <<'PY'
import PySide6
print("PySide6:", PySide6.__version__)
PY

# MOBPSY_GUI_MODULE_VALIDATION_V2
# cp -a anterior debe copiar el paquete completo. Verificamos la instalación real
# antes de ejecutar el smoke test para detectar paquetes públicos incompletos.
for f in main.py case_context.py mobpsy_runtime_pages.py mobpsy_functional_pages.py mobpsy_update_page.py; do
    test -f "${APP_DIR}/${f}" || {
        echo "ERROR: falta ${APP_DIR}/${f} después de instalar la GUI." >&2
        exit 41
    }
done

echo "[6/8] Ejecutando smoke test completo de la GUI..."
QT_QPA_PLATFORM=offscreen "${VENV_DIR}/bin/python" - <<'PY'
import importlib.util
import sys

from PySide6.QtWidgets import QApplication

app_dir = "/opt/mobpsy/app"
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)
path = "/opt/mobpsy/app/main.py"
spec = importlib.util.spec_from_file_location("mobpsy_main_smoketest", path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

app = QApplication.instance() or QApplication([])
window = module.MobPsyWindow()

expected = {
    "home", "manual", "identity", "email", "phone", "social",
    "multimedia", "dns", "ips", "infra", "frameworks",
    "cases", "correlation", "tools", "settings",
}
missing = expected.difference(window.pages)
if missing:
    raise RuntimeError(f"PÃƒÆ’Ã‚Â¡ginas ausentes en MobPsy: {sorted(missing)}")

# Fuerza la navegaciÃƒÆ’Ã‚Â³n por todos los mÃƒÆ’Ã‚Â³dulos para detectar errores de construcciÃƒÆ’Ã‚Â³n.
for key in expected:
    window.show_section(key)

print("MobPsy GUI smoke test: OK")
print("PÃƒÆ’Ã‚Â¡ginas cargadas:", len(window.pages))
window.close()
app.quit()
PY

echo "[7/8] Creando lanzador y entrada del menÃƒÆ’Ã‚Âº..."
cat >/usr/local/bin/mobpsy <<'EOF'
#!/usr/bin/env bash
set -e
exec /opt/mobpsy/venv/bin/python /opt/mobpsy/app/main.py "$@"
EOF
chmod 0755 /usr/local/bin/mobpsy

cat >/usr/local/bin/mobpsy-gui-check <<'EOF'
#!/usr/bin/env bash
set -e
export QT_QPA_PLATFORM=offscreen
exec /opt/mobpsy/venv/bin/python - <<'PY'
import importlib.util
import sys
from PySide6.QtWidgets import QApplication

app_dir = "/opt/mobpsy/app"
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)
path = "/opt/mobpsy/app/main.py"
spec = importlib.util.spec_from_file_location("mobpsy_gui_check", path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

app = QApplication.instance() or QApplication([])
window = module.MobPsyWindow()

for section in module.SECTIONS:
    window.show_section(section.key)

print(f"MobPsy GUI {module.APP_VERSION}: OK")
print(f"MÃƒÆ’Ã‚Â³dulos cargados: {len(window.pages)}")
window.close()
app.quit()
PY
EOF
chmod 0755 /usr/local/bin/mobpsy-gui-check

cat >/usr/share/applications/mobpsy.desktop <<'EOF'
[Desktop Entry]
Type=Application
Version=1.0
Name=MobPsy
GenericName=OSINT Workstation
Comment=Entorno grÃƒÆ’Ã‚Â¡fico de investigaciÃƒÆ’Ã‚Â³n OSINT
Exec=/usr/local/bin/mobpsy
Icon=mobpsy
Terminal=false
Categories=Utility;Security;
StartupNotify=true
EOF
chmod 0644 /usr/share/applications/mobpsy.desktop

echo "[8/8] AÃƒÆ’Ã‚Â±adiendo MobPsy al dock en la siguiente sesiÃƒÆ’Ã‚Â³n..."
install -d -o "$USER_NAME" -g "$USER_NAME" "${USER_HOME}/.config/autostart"
mkdir -p /usr/local/lib/mobpsy

cat >/usr/local/lib/mobpsy/first-login-fase3.sh <<'EOF'
#!/usr/bin/env bash
set -u

MARKER="$HOME/.config/mobpsy/fase3-login.done"
mkdir -p "$HOME/.config/mobpsy"
[ -f "$MARKER" ] && exit 0

sleep 8

TOR_DESKTOP="$(find "$HOME/.local/share/applications" -maxdepth 1 -type f \
    \( -iname '*tor*browser*.desktop' -o -iname 'start-tor-browser.desktop' \) \
    -printf '%f\n' 2>/dev/null | head -n 1)"

FAVORITES="'mobpsy.desktop', 'firefox_firefox.desktop', 'chromium_chromium.desktop'"
if [ -n "$TOR_DESKTOP" ]; then
    FAVORITES="$FAVORITES, '$TOR_DESKTOP'"
fi
FAVORITES="$FAVORITES, 'org.gnome.Nautilus.desktop', 'org.gnome.Terminal.desktop'"

gsettings set org.gnome.shell favorite-apps "[$FAVORITES]" 2>/dev/null || true

touch "$MARKER"
EOF
chmod 0755 /usr/local/lib/mobpsy/first-login-fase3.sh

cat >"${USER_HOME}/.config/autostart/mobpsy-first-login-fase3.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=MobPsy - configuraciÃƒÆ’Ã‚Â³n inicial de la aplicaciÃƒÆ’Ã‚Â³n
Exec=/usr/local/lib/mobpsy/first-login-fase3.sh
Terminal=false
X-GNOME-Autostart-enabled=true
NoDisplay=true
EOF

chown -R "${USER_NAME}:${USER_NAME}" "${USER_HOME}/.config"

mkdir -p /etc/mobpsy
cat >/etc/mobpsy/release <<'EOF'
MOBPSY_RELEASE=1.0.0
MOBPSY_APP_VERSION=1.0.0
EOF

# El upload ya no es necesario y se elimina para que una futura reprovisiÃƒÆ’Ã‚Â³n
# vuelva a partir de un directorio limpio.
rm -rf "$UPLOAD_DIR"

echo
echo "============================================================"
echo " MobPsy GUI 1.0.0 instalada y validada correctamente."
echo " La aplicaciÃƒÆ’Ã‚Â³n aparecerÃƒÆ’Ã‚Â¡ como 'MobPsy' en Ubuntu."
echo "============================================================"
echo


# MOBPSY_CORRELATOR_AUTOINSTALL_V1
# El Correlator forma parte de la GUI base: asÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â­ una instalaciÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â³n limpia no
# depende de una fase final ni de que MOBPSY.ps1 sea modificado.
if [ -f /opt/mobpsy/app/integration/mobpsy_correlate.py ]; then
    echo "[MobPsy] Asegurando Correlator..."
    install -d -m 0755 /opt/mobpsy/analysis
    install -m 0755 /opt/mobpsy/app/integration/mobpsy_correlate.py /opt/mobpsy/analysis/mobpsy_correlate.py
    cat >/usr/local/bin/mobpsy-correlate <<'MOBPSY_CORR_LAUNCHER'
#!/usr/bin/env bash
set -e
exec /usr/bin/python3 /opt/mobpsy/analysis/mobpsy_correlate.py "$@"
MOBPSY_CORR_LAUNCHER
    chmod 0755 /usr/local/bin/mobpsy-correlate
    ln -sf /usr/local/bin/mobpsy-correlate /usr/local/bin/mobpsy-correlator
    cat >/usr/share/applications/mobpsy-correlator.desktop <<'MOBPSY_CORR_DESKTOP'
[Desktop Entry]
Type=Application
Version=1.0
Name=MobPsy Correlator
Comment=CorrelaciÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â³n de entidades del caso activo
Exec=gnome-terminal -- /usr/local/bin/mobpsy-correlate
Icon=mobpsy
Terminal=false
Categories=Utility;Security;
MOBPSY_CORR_DESKTOP
    chmod 0644 /usr/share/applications/mobpsy-correlator.desktop
    /usr/local/bin/mobpsy-correlate --help >/dev/null
fi

