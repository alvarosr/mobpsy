#!/usr/bin/env bash
set -Eeuo pipefail

echo
echo "============================================================"
echo " MobPsy - Extensiones OSINT / ciberseguridad"
echo "============================================================"

# Chromium / Google Chrome: políticas de instalación forzada.
for d in /etc/chromium/policies/managed /etc/opt/chrome/policies/managed; do
  mkdir -p "$d"
  cat >"$d/mobpsy-extensions.json" <<'JSON'
{
  "ExtensionInstallForcelist": [
    "gppongmhjkpfnbhagpmjfkannfbllamg;https://clients2.google.com/service/update2/crx",
    "jjalcfnidlmpjhdfepjhjbhnhkbgleap;https://clients2.google.com/service/update2/crx",
    "ddkjiahejlhfcafbddmgiahcphecmpfh;https://clients2.google.com/service/update2/crx",
    "gcknhkkoolaabfmlnjonogaaifnjlfnp;https://clients2.google.com/service/update2/crx"
  ]
}
JSON
  chmod 0644 "$d/mobpsy-extensions.json"
done

# Firefox (incluido Ubuntu Firefox snap): se escriben políticas en todas las
# ubicaciones soportadas que pueden leer las distintas instalaciones.
POLICY='{
  "policies": {
    "Extensions": {
      "Install": [
        "https://addons.mozilla.org/firefox/downloads/latest/wappalyzer/latest.xpi",
        "https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi",
        "https://addons.mozilla.org/firefox/downloads/latest/foxyproxy-standard/latest.xpi"
      ],
      "Locked": [
        "https://addons.mozilla.org/firefox/downloads/latest/wappalyzer/latest.xpi",
        "https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi",
        "https://addons.mozilla.org/firefox/downloads/latest/foxyproxy-standard/latest.xpi"
      ]
    }
  }
}'
for d in /etc/firefox/policies /usr/lib/firefox/distribution /usr/lib/firefox-esr/distribution; do
  mkdir -p "$d"
  printf '%s\n' "$POLICY" >"$d/policies.json"
  chmod 0644 "$d/policies.json"
done

mkdir -p /opt/mobpsy/config
cat >/opt/mobpsy/config/browser-extensions.txt <<'TXT'
Firefox:
- Wappalyzer
- uBlock Origin
- FoxyProxy Standard

Chromium / Chrome:
- Wappalyzer
- Shodan
- uBlock Origin Lite
- FoxyProxy
TXT
chmod 0644 /opt/mobpsy/config/browser-extensions.txt

echo "[OK] Políticas instaladas."
echo "Cierra completamente Firefox/Chromium/Chrome y vuelve a abrirlos."
