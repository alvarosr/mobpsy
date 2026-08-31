#!/usr/bin/env bash
set -Eeuo pipefail
BASE_MODEL="${MOBPSY_AI_BASE_MODEL:-qwen3:1.7b}"
MODEL="${MOBPSY_AI_MODEL:-mobpsy-osint:latest}"
USER_NAME="${SUDO_USER:-mobpsy}"
[ "$USER_NAME" = "root" ] && USER_NAME="mobpsy"
id "$USER_NAME" >/dev/null 2>&1 || USER_NAME="mobpsy"
HOME_DIR="$(getent passwd "$USER_NAME" | cut -d: -f6)"
CONFIG_DIR="$HOME_DIR/MobPsy/Configuracion"
ROOT="/opt/mobpsy/analysis"
[ "${EUID:-$(id -u)}" -eq 0 ] || { echo "ERROR: se requieren privilegios." >&2; exit 1; }

echo "[1/6] Dependencias..."
apt-get update
apt-get install -y curl ca-certificates jq python3-markdown

echo "[PRE] Limitando recursos de Ollama..."
install -d -m 0755 /etc/systemd/system/ollama.service.d
cat >/etc/systemd/system/ollama.service.d/mobpsy-resources.conf <<'EOF'
[Service]
Environment="OLLAMA_NUM_PARALLEL=1"
Environment="OLLAMA_MAX_LOADED_MODELS=1"
Environment="OLLAMA_MAX_QUEUE=4"
EOF
systemctl daemon-reload

echo "[2/6] Ollama..."
if ! command -v ollama >/dev/null 2>&1; then curl -fsSL https://ollama.com/install.sh | sh; fi
systemctl enable ollama >/dev/null 2>&1 || true
systemctl restart ollama >/dev/null 2>&1 || systemctl start ollama >/dev/null 2>&1
for _ in $(seq 1 45); do curl -fsS --max-time 3 http://127.0.0.1:11434/api/tags >/dev/null 2>&1 && break; sleep 1; done
curl -fsS --max-time 5 http://127.0.0.1:11434/api/tags >/dev/null

echo "[3/6] Modelo base $BASE_MODEL..."
if ! ollama list 2>/dev/null | awk 'NR>1 {print $1}' | grep -Fxq "$BASE_MODEL"; then
  echo "Descargando $BASE_MODEL (modelo ligero para VM)..."
  ollama pull "$BASE_MODEL"
fi

echo "[4/6] Creando MobPsy OSINT..."
test -f "$ROOT/osint_system.txt"
MF="$(mktemp)"
cat >"$MF" <<EOF
FROM $BASE_MODEL
SYSTEM """
$(cat "$ROOT/osint_system.txt")
"""
PARAMETER temperature 0.15
PARAMETER top_p 0.85
PARAMETER num_ctx 4096
PARAMETER repeat_penalty 1.08
EOF
ollama create "$MODEL" -f "$MF"
rm -f "$MF"

echo "[5/6] Configurando..."
install -d -m 0755 -o "$USER_NAME" -g "$USER_NAME" "$CONFIG_DIR"
cat >"$CONFIG_DIR/ai.json" <<EOF
{"provider":"ollama","endpoint":"http://127.0.0.1:11434","model":"$MODEL","timeout_seconds":300,"context_chars":10000}
EOF
chown "$USER_NAME:$USER_NAME" "$CONFIG_DIR/ai.json"

echo "[6/6] Verificando..."
TMP_RESP="$(mktemp)"
HTTP_CODE="$(curl -sS --max-time 180 -o "$TMP_RESP" -w '%{http_code}' \
  http://127.0.0.1:11434/api/chat \
  -H 'Content-Type: application/json' \
  -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"Responde brevemente: prueba de funcionamiento\"}],\"stream\":false,\"think\":false,\"options\":{\"num_ctx\":4096,\"num_predict\":64}}")"
[ "$HTTP_CODE" = "200" ] || { cat "$TMP_RESP" >&2; rm -f "$TMP_RESP"; exit 52; }
jq -e '.message.content | type=="string" and length>0' "$TMP_RESP" >/dev/null
rm -f "$TMP_RESP"

# El modelo final ya referencia las capas que necesita. Quitamos tags que no se usan.
for OLD in gemma3:1b qwen3:4b-instruct; do
  if ollama list 2>/dev/null | awk 'NR>1 {print $1}' | grep -Fxq "$OLD"; then
    ollama rm "$OLD" >/dev/null 2>&1 || true
  fi
done
if [ "$BASE_MODEL" != "$MODEL" ]; then
  ollama rm "$BASE_MODEL" >/dev/null 2>&1 || true
fi
echo "[OK] MobPsy OSINT Analyst preparado: $MODEL"
