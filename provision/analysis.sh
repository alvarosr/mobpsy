#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONUNBUFFERED=1

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

# 1) Validar el backend Python sin ejecutar una correlación real.
if ! timeout --foreground 20s /usr/bin/python3 -m py_compile "$ROOT/mobpsy_correlate.py"; then
    echo "ERROR: mobpsy_correlate.py no supera py_compile." >&2
    exit 241
fi

# 2) Validar el script lanzador como shell, sin depender de su ejecución.
if ! /bin/bash -n /usr/local/bin/mobpsy-correlate; then
    echo "ERROR: el lanzador /usr/local/bin/mobpsy-correlate contiene un error de sintaxis." >&2
    exit 242
fi

if [ ! -x /usr/local/bin/mobpsy-correlate ]; then
    echo "ERROR: el lanzador mobpsy-correlate no es ejecutable." >&2
    exit 243
fi

# 3) Probar el backend directamente. Esto valida argparse/imports y evita
# falsos negativos del wrapper durante el propio aprovisionamiento.
set +e
VERSION_OUTPUT="$(timeout --foreground 20s /usr/bin/python3 "$ROOT/mobpsy_correlate.py" --version 2>&1)"
RC=$?
set -e
if [ "$RC" -ne 0 ]; then
    if [ "$RC" -eq 124 ]; then
        echo "ERROR: la comprobación de versión de Correlator superó 20 segundos." >&2
    else
        echo "ERROR: el backend de Correlator no supera la comprobación de versión (código $RC)." >&2
        printf '%s\n' "$VERSION_OUTPUT" >&2
    fi
    exit 244
fi

echo "      Sintaxis: OK"
echo "      Lanzador: OK"
echo "      ${VERSION_OUTPUT:-MobPsy Correlator OK}"

echo "[5/6] Verificando integración con casos..."
install -d -o "$USER_NAME" -g "$USER_NAME" "$USER_HOME/MobPsy/Casos"

# status no analiza ningún expediente. Se ejecuta directamente con el backend
# para verificar la integración con ~/MobPsy/Casos sin depender del wrapper.
set +e
STATUS_OUTPUT="$(timeout --foreground 20s sudo -u "$USER_NAME" /usr/bin/python3 "$ROOT/mobpsy_correlate.py" status 2>&1)"
RC=$?
set -e
if [ "$RC" -ne 0 ]; then
    if [ "$RC" -eq 124 ]; then
        echo "ERROR: la comprobación de estado de Correlator superó 20 segundos." >&2
    else
        echo "ERROR: Correlator no pudo consultar su estado (código $RC)." >&2
        printf '%s\n' "$STATUS_OUTPUT" >&2
    fi
    exit 245
fi

echo "      Integración con casos: OK"

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
