#!/usr/bin/env bash
set -u

fail=0

ok()   { printf "  [OK]   %s\n" "$1"; }
bad()  { printf "  [FALLO] %s\n" "$1"; fail=1; }
info() { printf "  [INFO] %s\n" "$1"; }

echo
echo "============================================================"
echo " MobPsy - Comprobación Fase 1"
echo "============================================================"

[ "$(systemctl get-default 2>/dev/null)" = "graphical.target" ] \
    && ok "Arranque gráfico (graphical.target)" \
    || bad "El sistema no arranca en graphical.target"

test -x /usr/sbin/gdm3 \
    && ok "GDM instalado" \
    || bad "GDM no encontrado"

id mobpsy >/dev/null 2>&1 \
    && ok "Usuario gráfico mobpsy" \
    || bad "Usuario mobpsy no existe"

snap list firefox >/dev/null 2>&1 \
    && ok "Firefox instalado" \
    || bad "Firefox no instalado"

snap list chromium >/dev/null 2>&1 \
    && ok "Chromium instalado" \
    || bad "Chromium no instalado"

TOR_START="/home/mobpsy/.local/share/mobpsy/tor-browser/start-tor-browser.desktop"
TOR_VERSION="/home/mobpsy/.local/share/mobpsy/tor-browser-version"

[ -x "$TOR_START" ] \
    && ok "Tor Browser instalado" \
    || bad "Tor Browser no instalado"

if [ -f "$TOR_VERSION" ]; then
    info "Tor Browser versión $(cat "$TOR_VERSION")"
fi


test -x /usr/local/bin/mobpsy \
    && ok "Lanzador MobPsy" \
    || bad "No existe /usr/local/bin/mobpsy"

test -f /usr/share/applications/mobpsy.desktop \
    && ok "Entrada de aplicación MobPsy" \
    || bad "Falta mobpsy.desktop"

if [ -x /opt/mobpsy/venv/bin/python ]; then
    if /opt/mobpsy/venv/bin/python -c 'import PySide6' >/dev/null 2>&1; then
        PYQT_VER="$(/opt/mobpsy/venv/bin/python -c 'import PySide6; print(PySide6.__version__)' 2>/dev/null)"
        ok "PySide6 importable (${PYQT_VER})"
    else
        bad "PySide6 no se puede importar"
    fi
else
    bad "Entorno virtual de MobPsy no encontrado"
fi

test -f /opt/mobpsy/app/main.py \
    && ok "Código de la GUI instalado" \
    || bad "Falta /opt/mobpsy/app/main.py"


test -x /usr/local/bin/mobpsy-sherlock \
    && ok "Sherlock: lanzador disponible" \
    || bad "Sherlock: falta /usr/local/bin/mobpsy-sherlock"

if test -x /usr/local/bin/mobpsy-sherlock; then
    if /usr/local/bin/mobpsy-sherlock --version >/dev/null 2>&1; then
        SHERLOCK_VERSION="$(/usr/local/bin/mobpsy-sherlock --version 2>&1 | head -n 1)"
        ok "Sherlock ejecutable (${SHERLOCK_VERSION})"
    else
        bad "Sherlock no responde a --version"
    fi
fi

test -x /usr/local/lib/mobpsy/display-resolution.sh \
    && ok "Resolución preferida 1600x900 configurada" \
    || bad "Falta configuración de resolución"


test -x /usr/local/bin/mobpsy-maigret \
    && ok "Maigret: lanzador disponible" \
    || bad "Maigret: falta /usr/local/bin/mobpsy-maigret"

if test -x /usr/local/bin/mobpsy-maigret; then
    if /opt/mobpsy/tools/maigret/venv/bin/python -c 'import maigret' >/dev/null 2>&1; then
        MAIGRET_VERSION="$(/opt/mobpsy/tools/maigret/venv/bin/python - <<'PY'
from importlib.metadata import version
print(version("maigret"))
PY
)"
        ok "Maigret importable (${MAIGRET_VERSION})"
    else
        bad "Maigret no se puede importar"
    fi
fi


test -x /usr/local/bin/mobpsy-holehe \
    && ok "Holehe: lanzador disponible" \
    || bad "Holehe: falta /usr/local/bin/mobpsy-holehe"

if test -x /opt/mobpsy/tools/holehe/venv/bin/python; then
    if /opt/mobpsy/tools/holehe/venv/bin/python -c \
        'import holehe, holehe.core, httpx, trio, requests' >/dev/null 2>&1; then
        HOLEHE_VERSION="$(/opt/mobpsy/tools/holehe/venv/bin/python - <<'PY'
import holehe.core
print(getattr(holehe.core, "__version__", "desconocida"))
PY
)"
        ok "Holehe importable (${HOLEHE_VERSION})"
    else
        bad "Holehe o alguna dependencia no se puede importar"
    fi
else
    bad "Entorno virtual de Holehe no encontrado"
fi


test -x /usr/local/bin/mobpsy-phoneinfoga \
    && ok "PhoneInfoga: lanzador disponible" \
    || bad "PhoneInfoga no disponible"

if test -x /usr/local/bin/mobpsy-phoneinfoga; then
    PHONE_VERSION="$(/usr/local/bin/mobpsy-phoneinfoga version 2>&1 | head -n1 || true)"
    ok "PhoneInfoga ejecutable (${PHONE_VERSION})"
fi

test -x /usr/local/bin/mobpsy-exiftool \
    && ok "ExifTool: lanzador disponible" \
    || bad "ExifTool no disponible"

if test -x /usr/local/bin/mobpsy-exiftool; then
    ok "ExifTool versión $(/usr/local/bin/mobpsy-exiftool -ver)"
fi

test -x /usr/local/bin/mobpsy-mediainfo \
    && ok "MediaInfo: lanzador disponible" \
    || bad "MediaInfo no disponible"

if test -x /usr/local/bin/mobpsy-mediainfo; then
    ok "$(/usr/local/bin/mobpsy-mediainfo --Version | head -n1)"
fi


test -x /usr/local/bin/mobpsy-subfinder \
    && ok "Subfinder: lanzador disponible" \
    || bad "Subfinder no disponible"

if test -x /usr/local/bin/mobpsy-subfinder; then
    SUBFINDER_VERSION="$(/usr/local/bin/mobpsy-subfinder -version 2>&1 | head -n1 || true)"
    ok "Subfinder ejecutable (${SUBFINDER_VERSION})"
fi

test -x /usr/local/bin/mobpsy-dnsrecon \
    && ok "DNSRecon: lanzador disponible" \
    || bad "DNSRecon no disponible"

if test -x /opt/mobpsy/tools/dnsrecon/src/.venv/bin/python; then
    if /opt/mobpsy/tools/dnsrecon/src/.venv/bin/python -c 'import dnsrecon' >/dev/null 2>&1; then
        ok "DNSRecon importable con Python aislado"
    else
        bad "DNSRecon no se puede importar"
    fi
fi

test -x /usr/local/bin/mobpsy-whatweb \
    && ok "WhatWeb: lanzador disponible" \
    || bad "WhatWeb no disponible"

if test -x /usr/local/bin/mobpsy-whatweb; then
    WHATWEB_VERSION="$(/usr/local/bin/mobpsy-whatweb --version 2>&1 | head -n1 || true)"
    ok "WhatWeb ejecutable (${WHATWEB_VERSION})"
fi


test -x /usr/local/bin/mobpsy-wafw00f \
    && ok "WAFW00F: lanzador disponible" \
    || bad "WAFW00F no disponible"

if test -x /usr/local/bin/mobpsy-wafw00f; then
    WAF_VERSION="$(/usr/local/bin/mobpsy-wafw00f --version 2>&1 | head -n1 || true)"
    ok "WAFW00F ejecutable (${WAF_VERSION})"
fi

test -x /usr/local/bin/mobpsy-photon \
    && ok "Photon: lanzador disponible" \
    || bad "Photon no disponible"

if test -x /usr/local/bin/mobpsy-photon; then
    /usr/local/bin/mobpsy-photon -h >/dev/null 2>&1 \
        && ok "Photon ejecutable" \
        || bad "Photon no responde"
fi

test -x /usr/local/bin/mobpsy-theharvester \
    && ok "theHarvester: lanzador disponible" \
    || bad "theHarvester no disponible"

if test -x /usr/local/bin/mobpsy-theharvester; then
    if /usr/local/bin/mobpsy-theharvester -h >/dev/null 2>&1; then
        HARVESTER_PY="$(/opt/mobpsy/tools/theharvester/src/.venv/bin/python --version 2>&1)"
        ok "theHarvester ejecutable (${HARVESTER_PY})"
    else
        bad "theHarvester no responde"
    fi
fi


test -x /usr/local/bin/mobpsy-crosslinked \
    && ok "CrossLinked: lanzador disponible" \
    || bad "CrossLinked no disponible"

if test -x /usr/local/bin/mobpsy-crosslinked; then
    /usr/local/bin/mobpsy-crosslinked -h >/dev/null 2>&1 \
        && ok "CrossLinked ejecutable" \
        || bad "CrossLinked no responde"
fi

test -x /usr/local/bin/mobpsy-protosint \
    && ok "ProtOSINT: lanzador disponible" \
    || bad "ProtOSINT no disponible"

if test -x /opt/mobpsy/tools/protosint/venv/bin/python; then
    /opt/mobpsy/tools/protosint/venv/bin/python -c \
        'import sys; sys.path.insert(0,"/opt/mobpsy/tools/protosint/src"); import protosint' \
        >/dev/null 2>&1 \
        && ok "ProtOSINT importable" \
        || bad "ProtOSINT no se puede importar"
fi

test -x /usr/local/bin/mobpsy-zehef \
    && ok "Zehef: lanzador disponible" \
    || bad "Zehef no disponible"

if test -x /usr/local/bin/mobpsy-zehef; then
    /usr/local/bin/mobpsy-zehef -h >/dev/null 2>&1 \
        && ok "Zehef ejecutable" \
        || bad "Zehef no responde"
fi


test -x /usr/local/bin/mobpsy-clatscope \
    && ok "ClatScope: lanzador disponible" \
    || bad "ClatScope no disponible"

test -x /usr/local/bin/mobpsy-social-analyzer \
    && ok "Social-Analyzer: lanzador disponible" \
    || bad "Social-Analyzer no disponible"

if test -x /usr/local/bin/mobpsy-social-analyzer; then
    /usr/local/bin/mobpsy-social-analyzer --help >/dev/null 2>&1 \
        && ok "Social-Analyzer ejecutable" \
        || bad "Social-Analyzer no responde"
fi

test -x /usr/local/bin/mobpsy-instaloader-profile \
    && ok "Instaloader: wrapper disponible" \
    || bad "Instaloader no disponible"

if test -x /usr/local/bin/mobpsy-instaloader-profile; then
    /usr/local/bin/mobpsy-instaloader-profile --help >/dev/null 2>&1 \
        && ok "Instaloader wrapper ejecutable" \
        || bad "Instaloader wrapper no responde"
fi


test -x /usr/local/bin/mobpsy-spiderfoot-ui \
    && ok "SpiderFoot: lanzador gráfico disponible" \
    || bad "SpiderFoot no disponible"

if test -x /opt/mobpsy/tools/spiderfoot/venv/bin/python; then
    /opt/mobpsy/tools/spiderfoot/venv/bin/python -c 'import cherrypy, requests, yaml' >/dev/null 2>&1 \
        && ok "SpiderFoot: dependencias importables" \
        || bad "SpiderFoot: dependencias dañadas"
fi

test -x /usr/local/bin/mobpsy-recon-ng \
    && ok "Recon-ng: lanzador disponible" \
    || bad "Recon-ng no disponible"

if test -x /usr/local/bin/mobpsy-recon-ng; then
    /usr/local/bin/mobpsy-recon-ng -h >/dev/null 2>&1 \
        && ok "Recon-ng ejecutable" \
        || bad "Recon-ng no responde"
fi

test -x /usr/local/bin/mobpsy-sn0int \
    && ok "sn0int: lanzador disponible" \
    || bad "sn0int no disponible"

if test -x /usr/local/bin/mobpsy-sn0int; then
    SN0INT_VERSION="$(/usr/local/bin/mobpsy-sn0int --version 2>&1 | head -n1 || true)"
    ok "sn0int ejecutable (${SN0INT_VERSION})"
fi




test -x /usr/local/bin/mobpsy \
    && ok "MobPsy GUI: lanzador disponible" \
    || bad "MobPsy GUI no disponible"


if test -f /etc/firefox/policies/policies.json; then
    python3 -m json.tool /etc/firefox/policies/policies.json >/dev/null 2>&1 \
        && ok "Firefox: política de marcadores válida" \
        || bad "Firefox: política de marcadores inválida"
else
    bad "Firefox: política de marcadores no encontrada"
fi

if test -f /etc/chromium/policies/managed/mobpsy-bookmarks.json; then
    python3 -m json.tool /etc/chromium/policies/managed/mobpsy-bookmarks.json >/dev/null 2>&1 \
        && ok "Chromium: política de marcadores válida" \
        || bad "Chromium: política de marcadores inválida"
else
    bad "Chromium: política de marcadores no encontrada"
fi

TOR_POLICY="/home/mobpsy/.local/share/mobpsy/tor-browser/Browser/distribution/policies.json"
if test -f "$TOR_POLICY"; then
    python3 -m json.tool "$TOR_POLICY" >/dev/null 2>&1 \
        && ok "Tor Browser: política de marcadores válida" \
        || bad "Tor Browser: política de marcadores inválida"
else
    bad "Tor Browser: política de marcadores no encontrada"
fi

test -f /home/mobpsy/MobPsy/Marcadores/index.html \
    && ok "Marcadores: portal local disponible" \
    || bad "Marcadores: portal local no disponible"

test -x /usr/local/bin/mobpsy-gui-check \
    && ok "MobPsy GUI: diagnóstico disponible" \
    || bad "MobPsy GUI: diagnóstico no disponible"

if test -x /usr/local/bin/mobpsy-gui-check; then
    if /usr/local/bin/mobpsy-gui-check >/tmp/mobpsy-gui-check.log 2>&1; then
        ok "MobPsy GUI: construcción y navegación OK"
    else
        bad "MobPsy GUI: smoke test fallido"
        cat /tmp/mobpsy-gui-check.log || true
    fi
fi

test -x /usr/local/bin/mobpsy-whois \
    && ok "Whois: lanzador disponible" \
    || bad "Whois no disponible"

test -x /usr/local/bin/mobpsy-dig \
    && ok "dig: lanzador disponible" \
    || bad "dig no disponible"

test -x /usr/local/bin/mobpsy-host \
    && ok "host: lanzador disponible" \
    || bad "host no disponible"

test -x /usr/local/bin/mobpsy-geoiplookup \
    && ok "GeoIPLookup: lanzador disponible" \
    || bad "GeoIPLookup no disponible"



if PYTHONPATH=/opt/mobpsy/app /opt/mobpsy/venv/bin/python -c \
    'import case_context; assert callable(case_context.register_export)' >/dev/null 2>&1; then
    ok "Caso activo: integración GUI disponible"
else
    bad "Caso activo: integración GUI no disponible"
fi

if PYTHONPATH=/opt/mobpsy/terminal /usr/bin/python3 -c \
    'import case_context; assert callable(case_context.register_export)' >/dev/null 2>&1; then
    ok "Caso activo: integración Terminal disponible"
else
    bad "Caso activo: integración Terminal no disponible"
fi

test -x /usr/local/bin/mobpsy-case \
    && ok "Casos: gestor CLI disponible" \
    || bad "Casos: gestor CLI no disponible"

test -d /home/mobpsy/MobPsy/Casos \
    && ok "Casos: directorio disponible" \
    || bad "Casos: directorio no disponible"

test -x /usr/local/bin/mobpsy-cli \
    && ok "MobPsy Terminal: lanzador disponible" \
    || bad "MobPsy Terminal no disponible"

test -f /opt/mobpsy/terminal/mobpsy_terminal.py \
    && ok "MobPsy Terminal: código instalado" \
    || bad "MobPsy Terminal: código no encontrado"

for d in Casos Evidencias Exportaciones Temporal; do
    [ -d "/home/mobpsy/MobPsy/$d" ] \
        && ok "Carpeta ~/MobPsy/$d" \
        || bad "Falta ~/MobPsy/$d"
done

if [ -f /etc/mobpsy/release ]; then
    info "$(tr '\n' ' ' </etc/mobpsy/release)"
else
    bad "No existe /etc/mobpsy/release"
fi

echo
if [ "$fail" -eq 0 ]; then
    echo "RESULTADO: Fase 1 correcta."
else
    echo "RESULTADO: Hay elementos que revisar."
fi
echo

exit "$fail"

echo
echo "IA local y versión"
if [ -x /usr/local/bin/mobpsy-ai ]; then
    if sudo -u mobpsy /usr/local/bin/mobpsy-ai status >/tmp/mobpsy-ai-status.txt 2>&1; then
        ok "IA local: $(cat /tmp/mobpsy-ai-status.txt)"
    else
        bad "IA local no operativa: $(cat /tmp/mobpsy-ai-status.txt)"
    fi
else
    bad "IA local: launcher ausente"
fi

if [ -x /usr/local/bin/mobpsy-update-check ] && [ "$(cat /etc/mobpsy/version 2>/dev/null || true)" = "1.0.0" ]; then
    ok "Versión MobPsy: 1.0.0"
else
    bad "Versionado de MobPsy no configurado correctamente"
fi
