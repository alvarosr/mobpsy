#!/usr/bin/env bash
set -Eeuo pipefail

# MOBPSY_AI_RESOURCES_V1
echo "[PRE] Preparando recursos para IA local..."
if [ -x /opt/mobpsy/analysis/ai_resources.sh ]; then
    /opt/mobpsy/analysis/ai_resources.sh
else
    SWAPFILE="/swapfile-mobpsy"
    if [ ! -f "$SWAPFILE" ]; then
        fallocate -l 8G "$SWAPFILE" 2>/dev/null || dd if=/dev/zero of="$SWAPFILE" bs=1M count=8192
        chmod 600 "$SWAPFILE"
        mkswap "$SWAPFILE" >/dev/null
    fi
    swapon "$SWAPFILE" 2>/dev/null || true
    grep -Fq "$SWAPFILE none swap sw 0 0" /etc/fstab || echo "$SWAPFILE none swap sw 0 0" >> /etc/fstab
fi
# FIN MOBPSY_AI_RESOURCES_V1

UPLOAD="/home/vagrant/mobpsy_analysis_upload"
ROOT="/opt/mobpsy/analysis"
echo
echo "============================================================"
echo " MobPsy 1.0.0 - IA OSINT local"
echo "============================================================"
for f in mobpsy_ai.py mobpsy_case_index.py mobpsy_report_engine.py ai_local_setup.sh osint_knowledge.md osint_system.txt; do
  test -f "$UPLOAD/$f" || { echo "ERROR: falta $f" >&2; exit 250; }
done
echo "[1/4] Instalando módulo..."
install -d -m 0755 "$ROOT"
install -m 0755 "$UPLOAD/mobpsy_ai.py" "$ROOT/mobpsy_ai.py"
install -m 0755 "$UPLOAD/mobpsy_case_index.py" "$ROOT/mobpsy_case_index.py"
install -m 0755 "$UPLOAD/mobpsy_report_engine.py" "$ROOT/mobpsy_report_engine.py"
install -m 0755 "$UPLOAD/ai_local_setup.sh" "$ROOT/ai_local_setup.sh"
install -m 0644 "$UPLOAD/osint_knowledge.md" "$ROOT/osint_knowledge.md"
install -m 0644 "$UPLOAD/osint_system.txt" "$ROOT/osint_system.txt"
cat >/usr/local/bin/mobpsy-ai <<EOF
#!/usr/bin/env bash
exec /usr/bin/python3 "$ROOT/mobpsy_ai.py" "\$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-ai
cat >/usr/local/bin/mobpsy-ai-setup <<EOF
#!/usr/bin/env bash
exec sudo "$ROOT/ai_local_setup.sh" "\$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-ai-setup
# MOBPSY_RAG_EXTRACTORS_V1
echo "[RAG] Instalando extractores de evidencias..."
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends poppler-utils tesseract-ocr tesseract-ocr-spa antiword unrtf binutils python3-openpyxl python3-pypdf2
# FIN MOBPSY_RAG_EXTRACTORS_V1

echo "[2/4] Preparando modelo..."
sudo "$ROOT/ai_local_setup.sh"
echo "[3/4] Validando..."
sudo -u mobpsy /usr/local/bin/mobpsy-ai status
echo "[4/4] Registrando..."
mkdir -p /etc/mobpsy
cat >/etc/mobpsy/ai <<'EOF'
MOBPSY_AI_VERSION=2.0.0
MOBPSY_AI_PROVIDER=ollama
MOBPSY_AI_MODEL=mobpsy-osint:latest
MOBPSY_AI_BASE_MODEL=qwen3:1.7b
EOF
rm -rf "$UPLOAD"
echo "IA OSINT local instalada."
