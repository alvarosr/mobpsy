#!/usr/bin/env bash
set -Eeuo pipefail

export DEBIAN_FRONTEND=noninteractive

UPLOAD="/home/vagrant/mobpsy_bookmarks_upload"
CATALOG="${UPLOAD}/catalog.json"
ROOT="/opt/mobpsy/bookmarks"
USER_NAME="mobpsy"
USER_HOME="/home/${USER_NAME}"
OUTPUT_DIR="${USER_HOME}/MobPsy/Marcadores"
TOR_ROOT="${USER_HOME}/.local/share/mobpsy/tor-browser"

echo
echo "============================================================"
echo " MobPsy - Fase 16: marcadores de navegadores"
echo "============================================================"
echo

if [ ! -f "$CATALOG" ]; then
    echo "ERROR: no se ha recibido bookmarks/catalog.json." >&2
    echo "Ejecuta primero el provisioner mobpsy_bookmarks_files." >&2
    exit 180
fi

echo "[1/8] Instalando utilidades..."
apt-get update
apt-get install -y python3 jq ca-certificates

echo "[2/8] Validando catálogo..."
python3 -m json.tool "$CATALOG" >/dev/null

install -d -m 0755 "$ROOT"
install -m 0644 "$CATALOG" "$ROOT/catalog.json"

echo "[3/8] Generando políticas y páginas HTML..."
python3 - <<'PY'
from pathlib import Path
import html
import json

catalog_path = Path("/opt/mobpsy/bookmarks/catalog.json")
catalog = json.loads(catalog_path.read_text(encoding="utf-8"))

out = Path("/opt/mobpsy/bookmarks/generated")
out.mkdir(parents=True, exist_ok=True)

def managed(browser_key):
    data = catalog["browsers"][browser_key]
    result = [{"toplevel_name": data["title"]}]
    for category in data["categories"]:
        children = [
            {"name": item["name"], "url": item["url"]}
            for item in category["bookmarks"]
        ]
        result.append({"name": category["name"], "children": children})
    return result

for browser in ("firefox", "chromium", "tor"):
    items = managed(browser)
    (out / f"{browser}-managed-bookmarks.json").write_text(
        json.dumps(items, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

# Firefox / Tor use Mozilla enterprise policies.
for browser in ("firefox", "tor"):
    policies = {
        "policies": {
            "ManagedBookmarks": managed(browser),
            "DisplayBookmarksToolbar": "always",
        }
    }
    (out / f"{browser}-policies.json").write_text(
        json.dumps(policies, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

# Chromium uses Linux JSON policies.
chromium_policy = {
    "BookmarkBarEnabled": True,
    "EditBookmarksEnabled": True,
    "ManagedBookmarks": managed("chromium"),
}
(out / "chromium-policy.json").write_text(
    json.dumps(chromium_policy, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

def page(browser):
    info = catalog["browsers"][browser]
    blocks = []
    for cat in info["categories"]:
        lis = "\n".join(
            f'<li><a href="{html.escape(x["url"], quote=True)}">{html.escape(x["name"])}</a></li>'
            for x in cat["bookmarks"]
        )
        blocks.append(
            f"<section><h2>{html.escape(cat['name'])}</h2><ul>{lis}</ul></section>"
        )

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(info["title"])}</title>
<style>
body {{
  background:#0b0f14; color:#d8dee9; font-family:system-ui,sans-serif;
  max-width:1100px; margin:0 auto; padding:32px;
}}
h1 {{ color:#f0f6fc; }}
h2 {{ color:#58a6ff; margin-top:0; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:16px; }}
section {{ background:#111820; border:1px solid #263241; border-radius:12px; padding:18px; }}
a {{ color:#79c0ff; text-decoration:none; }}
a:hover {{ text-decoration:underline; }}
li {{ margin:8px 0; }}
.small {{ color:#8b949e; }}
</style>
</head>
<body>
<h1>{html.escape(info["title"])}</h1>
<p class="small">Copia local del catálogo de marcadores MobPsy.</p>
<div class="grid">{''.join(blocks)}</div>
</body>
</html>"""

for browser in ("firefox", "chromium", "tor"):
    (out / f"{browser}.html").write_text(page(browser), encoding="utf-8")

# Índice general.
index = """<!doctype html>
<html lang="es">
<head><meta charset="utf-8"><title>MobPsy · Marcadores</title>
<style>
body {background:#0b0f14;color:#d8dee9;font-family:system-ui,sans-serif;max-width:900px;margin:auto;padding:40px}
a{display:block;background:#111820;color:#79c0ff;border:1px solid #263241;border-radius:12px;padding:18px;margin:14px 0;text-decoration:none;font-size:1.1rem}
</style></head>
<body><h1>MobPsy · Marcadores OSINT</h1>
<a href="Firefox.html">Firefox · Investigación</a>
<a href="Chromium.html">Chromium · Técnico</a>
<a href="Tor.html">Tor Browser · Privacidad</a>
</body></html>"""
(out / "index.html").write_text(index, encoding="utf-8")
PY

echo "[4/8] Instalando política de Firefox..."
install -d -m 0755 /etc/firefox/policies
install -m 0644 "$ROOT/generated/firefox-policies.json" \
    /etc/firefox/policies/policies.json

# Compatibilidad adicional con el empaquetado Snap de Ubuntu.
install -d -m 0755 /var/snap/firefox/common/policies
install -m 0644 "$ROOT/generated/firefox-policies.json" \
    /var/snap/firefox/common/policies/policies.json

echo "[5/8] Instalando política de Chromium..."
# Chromium upstream.
install -d -m 0755 /etc/chromium/policies/managed
install -m 0644 "$ROOT/generated/chromium-policy.json" \
    /etc/chromium/policies/managed/mobpsy-bookmarks.json

# Ruta utilizada históricamente por el paquete Ubuntu.
install -d -m 0755 /etc/chromium-browser/policies/managed
install -m 0644 "$ROOT/generated/chromium-policy.json" \
    /etc/chromium-browser/policies/managed/mobpsy-bookmarks.json

# Copia adicional para el snap de Chromium.
install -d -m 0755 /var/snap/chromium/common/policies/managed
install -m 0644 "$ROOT/generated/chromium-policy.json" \
    /var/snap/chromium/common/policies/managed/mobpsy-bookmarks.json

echo "[6/8] Instalando política de Tor Browser..."
if [ -d "$TOR_ROOT/Browser" ]; then
    install -d -m 0755 "$TOR_ROOT/Browser/distribution"
    install -m 0644 "$ROOT/generated/tor-policies.json" \
        "$TOR_ROOT/Browser/distribution/policies.json"
    chown -R "${USER_NAME}:${USER_NAME}" "$TOR_ROOT/Browser/distribution"
else
    echo "AVISO: no se ha encontrado Tor Browser en $TOR_ROOT/Browser."
    echo "       Se conservará el HTML local y podrá reprovisionarse más tarde."
fi

echo "[7/8] Instalando copia local y acceso desde Ubuntu..."
install -d -o "$USER_NAME" -g "$USER_NAME" "$OUTPUT_DIR"

cp "$ROOT/generated/firefox.html" "$OUTPUT_DIR/Firefox.html"
cp "$ROOT/generated/chromium.html" "$OUTPUT_DIR/Chromium.html"
cp "$ROOT/generated/tor.html" "$OUTPUT_DIR/Tor.html"
cp "$ROOT/generated/index.html" "$OUTPUT_DIR/index.html"
cp "$ROOT/catalog.json" "$OUTPUT_DIR/catalog.json"

chown -R "${USER_NAME}:${USER_NAME}" "$OUTPUT_DIR"

cat >/usr/share/applications/mobpsy-bookmarks.desktop <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=MobPsy Marcadores
GenericName=OSINT Bookmarks
Comment=Catálogo local de marcadores OSINT de MobPsy
Exec=xdg-open ${OUTPUT_DIR}/index.html
Icon=emblem-web
Terminal=false
Categories=Utility;Security;
StartupNotify=true
EOF
chmod 0644 /usr/share/applications/mobpsy-bookmarks.desktop

echo "[8/8] Validando instalación..."
python3 -m json.tool /etc/firefox/policies/policies.json >/dev/null
python3 -m json.tool /etc/chromium/policies/managed/mobpsy-bookmarks.json >/dev/null

if [ -f "$TOR_ROOT/Browser/distribution/policies.json" ]; then
    python3 -m json.tool "$TOR_ROOT/Browser/distribution/policies.json" >/dev/null
fi

test -f "$OUTPUT_DIR/index.html"

mkdir -p /etc/mobpsy
cat >/etc/mobpsy/bookmarks <<EOF
MOBPSY_BOOKMARKS_VERSION=$(jq -r '.version' "$ROOT/catalog.json")
FIREFOX_POLICY=/etc/firefox/policies/policies.json
CHROMIUM_POLICY=/etc/chromium/policies/managed/mobpsy-bookmarks.json
TOR_POLICY=${TOR_ROOT}/Browser/distribution/policies.json
CATALOG=${ROOT}/catalog.json
EOF

rm -rf "$UPLOAD"

echo
echo "============================================================"
echo " Marcadores MobPsy instalados."
echo " - Firefox:  investigación"
echo " - Chromium: técnico"
echo " - Tor:      privacidad"
echo "============================================================"
echo


# MOBPSY_BROWSER_EXTENSIONS_FASE20_V4
# Se ejecuta automaticamente al instalar/regenerar marcadores.
set -Eeuo pipefail

echo "============================================================"
echo " MobPsy - Extensiones de navegador OSINT / ciberseguridad"
echo "============================================================"

CHROMIUM_POLICY_DIR="/etc/chromium/policies/managed"
CHROME_POLICY_DIR="/etc/opt/chrome/policies/managed"
mkdir -p "$CHROMIUM_POLICY_DIR" "$CHROME_POLICY_DIR"
cat >/tmp/mobpsy_chromium_extensions.json <<'JSON'
{
  "ExtensionInstallForcelist": [
    "gppongmhjkpfnbhagpmjfkannfbllamg;https://clients2.google.com/service/update2/crx",
    "jjalcfnidlmpjhdfepjhjbhnhkbgleap;https://clients2.google.com/service/update2/crx",
    "ddkjiahejlhfcafbddmgiahcphecmpfh;https://clients2.google.com/service/update2/crx",
    "gcknhkkoolaabfmlnjonogaaifnjlfnp;https://clients2.google.com/service/update2/crx"
  ]
}
JSON
install -m 0644 /tmp/mobpsy_chromium_extensions.json "$CHROMIUM_POLICY_DIR/mobpsy-extensions.json"
install -m 0644 /tmp/mobpsy_chromium_extensions.json "$CHROME_POLICY_DIR/mobpsy-extensions.json"

cat >/tmp/mobpsy_firefox_policies.json <<'JSON'
{
  "policies": {
    "Extensions": {
      "Install": [
        "https://addons.mozilla.org/firefox/downloads/latest/wappalyzer/latest.xpi",
        "https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi",
        "https://addons.mozilla.org/firefox/downloads/latest/foxyproxy-standard/latest.xpi"
      ]
    }
  }
}
JSON
mkdir -p /etc/firefox/policies /usr/lib/firefox/distribution /usr/lib/firefox-esr/distribution
install -m 0644 /tmp/mobpsy_firefox_policies.json /etc/firefox/policies/policies.json
install -m 0644 /tmp/mobpsy_firefox_policies.json /usr/lib/firefox/distribution/policies.json
if [ -d /usr/lib/firefox-esr ]; then install -m 0644 /tmp/mobpsy_firefox_policies.json /usr/lib/firefox-esr/distribution/policies.json; fi
mkdir -p /opt/mobpsy/config
cat >/opt/mobpsy/config/browser-extensions.txt <<'TXT'
MobPsy - Extensiones gestionadas
Chromium/Chrome: Wappalyzer, Shodan, uBlock Origin Lite, FoxyProxy
Firefox: Wappalyzer, uBlock Origin, FoxyProxy Standard
TXT
chmod 0644 /opt/mobpsy/config/browser-extensions.txt
echo "Extensiones configuradas. Cierra y vuelve a abrir los navegadores."



# MOBPSY_BROWSER_EXTENSIONS_INLINE_V2
# Extensiones base. Se repite aquÃ­ de forma idempotente para que una instalaciÃ³n
# limpia las tenga aunque no se invoque un provisionador adicional.
echo "[MobPsy] Configurando extensiones de navegador..."
for d in /etc/chromium/policies/managed /etc/opt/chrome/policies/managed; do
  mkdir -p "$d"
  cat >"$d/mobpsy-extensions.json" <<'MOBPSY_CHROME_EXT'
{
  "ExtensionInstallForcelist": [
    "gppongmhjkpfnbhagpmjfkannfbllamg;https://clients2.google.com/service/update2/crx",
    "jjalcfnidlmpjhdfepjhjbhnhkbgleap;https://clients2.google.com/service/update2/crx",
    "ddkjiahejlhfcafbddmgiahcphecmpfh;https://clients2.google.com/service/update2/crx",
    "gcknhkkoolaabfmlnjonogaaifnjlfnp;https://clients2.google.com/service/update2/crx"
  ]
}
MOBPSY_CHROME_EXT
  chmod 0644 "$d/mobpsy-extensions.json"
done

for d in /etc/firefox/policies /usr/lib/firefox/distribution /usr/lib/firefox-esr/distribution; do
  mkdir -p "$d"
  cat >"$d/policies.json" <<'MOBPSY_FF_EXT'
{
  "policies": {
    "Extensions": {
      "Install": [
        "https://addons.mozilla.org/firefox/downloads/latest/wappalyzer/latest.xpi",
        "https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi",
        "https://addons.mozilla.org/firefox/downloads/latest/foxyproxy-standard/latest.xpi"
      ]
    }
  }
}
MOBPSY_FF_EXT
  chmod 0644 "$d/policies.json"
done

