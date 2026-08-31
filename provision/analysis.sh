#!/usr/bin/env bash
set -Eeuo pipefail

UPLOAD="/home/vagrant/mobpsy_analysis_upload"
ROOT="/opt/mobpsy/analysis"
USER_NAME="mobpsy"
USER_HOME="/home/${USER_NAME}"

echo
echo "============================================================"
echo " MobPsy 1.0.0 - Correlator"
echo "============================================================"
echo

if [ ! -f "$UPLOAD/mobpsy_correlate.py" ]; then
    echo "ERROR: falta mobpsy_correlate.py en mobpsy_analysis." >&2
    echo "Ejecuta primero el provisioner mobpsy_analysis_files." >&2
    exit 240
fi

echo "[0/6] Instalando visores y utilidades de resultados..."
# MOBPSY_CORRELATION_VIEWERS_V1
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends   libreoffice-calc   graphviz   jq   xdg-utils

echo "[1/6] Instalando backend de correlación..."
install -d -m 0755 "$ROOT"
install -m 0755 "$UPLOAD/mobpsy_correlate.py" "$ROOT/mobpsy_correlate.py"

# Conservamos también los módulos de IA en el mismo árbol si están presentes.
# NO se ejecuta Ollama aquí: ai_local.sh lo configura en su fase independiente.
[ -f "$UPLOAD/mobpsy_ai.py" ] && install -m 0755 "$UPLOAD/mobpsy_ai.py" "$ROOT/mobpsy_ai.py"
[ -f "$UPLOAD/ai_local_setup.sh" ] && install -m 0755 "$UPLOAD/ai_local_setup.sh" "$ROOT/ai_local_setup.sh"

echo "[2/6] Creando comandos globales..."
cat >/usr/local/bin/mobpsy-correlate <<EOF
#!/usr/bin/env bash
set -e
exec /usr/bin/python3 "$ROOT/mobpsy_correlate.py" "\$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-correlate

cat >/usr/local/bin/mobpsy-correlator <<'EOF'
#!/usr/bin/env bash
set -e
exec /usr/local/bin/mobpsy-correlate "$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-correlator

echo "[3/6] Creando acceso gráfico..."
cat >/usr/share/applications/mobpsy-correlator.desktop <<'EOF'
[Desktop Entry]
Type=Application
Version=1.0
Name=MobPsy Correlator
GenericName=OSINT Correlation Engine
Comment=Correlaciona entidades del caso activo de MobPsy
Exec=gnome-terminal -- /usr/local/bin/mobpsy-correlate
Icon=mobpsy
Terminal=false
Categories=Utility;Security;
StartupNotify=true
EOF
chmod 0644 /usr/share/applications/mobpsy-correlator.desktop
update-desktop-database /usr/share/applications >/dev/null 2>&1 || true

echo "[4/6] Verificando sintaxis y lanzador..."
/usr/bin/python3 -m py_compile "$ROOT/mobpsy_correlate.py"
/usr/local/bin/mobpsy-correlate --help >/dev/null

echo "[5/6] Verificando integración con casos..."
install -d -o "$USER_NAME" -g "$USER_NAME" "$USER_HOME/MobPsy/Casos"
# status no exige que exista un caso activo: sirve para que el instalador pueda
# validar el backend incluso antes de que el usuario cree su primera investigación.
sudo -u "$USER_NAME" /usr/local/bin/mobpsy-correlate status >/dev/null

echo "[6/6] Registrando..."
mkdir -p /etc/mobpsy
cat >/etc/mobpsy/analysis <<EOF
MOBPSY_ANALYSIS_VERSION=1.0.0
MOBPSY_CORRELATOR=1
MOBPSY_CORRELATOR_COMMAND=/usr/local/bin/mobpsy-correlate
MOBPSY_CORRELATOR_ALIAS=/usr/local/bin/mobpsy-correlator
MOBPSY_CORRELATOR_OUTPUTS=correlation.json,entities.csv,relations.csv,correlation.graphml,correlation_graph.svg,correlation_report.md,correlation_report.html
EOF

# IMPORTANTE: no se borra $UPLOAD. La fase ai_local usa los mismos archivos
# más tarde durante la instalación.
echo
echo "MobPsy Correlator preparado correctamente."
echo "Comando: mobpsy-correlate"
