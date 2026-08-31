#!/usr/bin/env bash
set -uo pipefail

USER_NAME="mobpsy"
USER_HOME="/home/mobpsy"
REPORT="/tmp/mobpsy_tool_audit.tsv"
DETAIL="/tmp/mobpsy_tool_audit.log"

: >"$REPORT"
: >"$DETAIL"

ok=0
warn=0
bad=0

run_as_user() {
  local seconds="$1"; shift
  timeout --signal=TERM "${seconds}s" \
    sudo -u "$USER_NAME" -H env \
      HOME="$USER_HOME" \
      LANG=C.UTF-8 LC_ALL=C.UTF-8 \
      PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin" \
      "$@"
}

classify() {
  local name="$1" command="$2" provisioner="$3" seconds="$4"; shift 4
  local tmp rc output

  tmp="$(mktemp)"
  echo "===== $name =====" >>"$DETAIL"
  echo "CMD: $*" >>"$DETAIL"

  set +e
  run_as_user "$seconds" "$@" >"$tmp" 2>&1
  rc=$?
  set -e

  output="$(cat "$tmp")"
  cat "$tmp" >>"$DETAIL"
  echo >>"$DETAIL"

  if [ "$rc" -eq 0 ]; then
    printf 'OK\t%s\t%s\t%s\t%s\n' "$name" "$command" "$provisioner" "respuesta correcta" >>"$REPORT"
    ok=$((ok+1))
  elif [ "$rc" -eq 124 ]; then
    # Muchos OSINT pueden esperar red/API. El binario arrancó, por lo que no
    # tratamos un timeout como instalación rota.
    printf 'WARN\t%s\t%s\t%s\t%s\n' "$name" "$command" "$provisioner" "timeout/red/API" >>"$REPORT"
    warn=$((warn+1))
  elif printf '%s' "$output" | grep -Eqi \
      'PermissionError|Permission denied|ModuleNotFoundError|ImportError|Traceback|No such file or directory|command not found|cannot open|not found:|SyntaxError'; then
    reason="$(printf '%s\n' "$output" | tail -n 3 | tr '\t\r\n' ' ' | cut -c1-240)"
    printf 'BROKEN\t%s\t%s\t%s\t%s\n' "$name" "$command" "$provisioner" "$reason" >>"$REPORT"
    bad=$((bad+1))
  else
    # Código != 0 por uso/argumentos/red no equivale necesariamente a que la
    # aplicación esté rota. Se registra como advertencia para no reinstalar a ciegas.
    reason="$(printf '%s\n' "$output" | tail -n 2 | tr '\t\r\n' ' ' | cut -c1-220)"
    printf 'WARN\t%s\t%s\t%s\t%s\n' "$name" "$command" "$provisioner" "salida no cero: $reason" >>"$REPORT"
    warn=$((warn+1))
  fi
  rm -f "$tmp"
}

set -e

echo "MobPsy - auditoría de 25 herramientas"
echo

# Pruebas de arranque/consulta. Para utilidades de red se usa example.com.
classify "Sherlock"        mobpsy-sherlock             sherlock        20 mobpsy-sherlock --version
classify "Maigret"         mobpsy-maigret              maigret         20 mobpsy-maigret --help
classify "CrossLinked"     mobpsy-crosslinked          crosslinked     20 mobpsy-crosslinked -h
classify "ClatScope"       mobpsy-clatscope            clatscope       20 mobpsy-clatscope --help

classify "Holehe"          mobpsy-holehe               holehe          20 mobpsy-holehe --help
classify "ProtOSINT"       mobpsy-protosint            protosint       20 mobpsy-protosint -h
classify "Zehef"           mobpsy-zehef                zehef           20 mobpsy-zehef -h

classify "PhoneInfoga"     mobpsy-phoneinfoga          phoneinfoga     20 mobpsy-phoneinfoga version

classify "Social-Analyzer" mobpsy-social-analyzer      social_analyzer 20 mobpsy-social-analyzer --help
classify "Instaloader"     mobpsy-instaloader          instaloader     20 mobpsy-instaloader --help

# Crear un archivo local para probar herramientas multimedia sin depender de Internet.
printf 'MobPsy test\n' >"$USER_HOME/.cache/mobpsy_test_file.txt"
classify "ExifTool"        mobpsy-exiftool             exiftool        15 mobpsy-exiftool "$USER_HOME/.cache/mobpsy_test_file.txt"
classify "MediaInfo"       mobpsy-mediainfo            mediainfo       15 mobpsy-mediainfo --Version

classify "Subfinder"       mobpsy-subfinder            subfinder       25 mobpsy-subfinder -version
classify "DNSRecon"        mobpsy-dnsrecon             dnsrecon        20 mobpsy-dnsrecon -h
classify "dig"             mobpsy-dig                  ip_dns_extra    20 mobpsy-dig +short example.com
classify "host"            mobpsy-host                 ip_dns_extra    20 mobpsy-host example.com

classify "Whois"           mobpsy-whois                ip_dns_extra    20 mobpsy-whois --help
classify "GeoIPLookup"     mobpsy-geoiplookup          ip_dns_extra    20 mobpsy-geoiplookup -h

classify "WhatWeb"         mobpsy-whatweb              whatweb         25 mobpsy-whatweb --version
classify "WAFW00F"         mobpsy-wafw00f              wafw00f         20 mobpsy-wafw00f --version
classify "Photon"          mobpsy-photon               photon          20 mobpsy-photon -h
classify "theHarvester"    mobpsy-theharvester         theharvester    20 mobpsy-theharvester -h

# SpiderFoot: no abrimos navegador. Verificamos el servidor y sus dependencias.
classify "SpiderFoot"      mobpsy-spiderfoot           spiderfoot      20 /bin/bash -lc 'test -x /usr/local/bin/mobpsy-spiderfoot-ui && test -x /usr/local/bin/mobpsy-spiderfoot-server && /opt/mobpsy/tools/spiderfoot/venv/bin/python -c "import cherrypy,requests,yaml"'
classify "Recon-ng"        mobpsy-reconng              reconng         20 mobpsy-reconng -h
classify "sn0int"          mobpsy-sn0int               sn0int          20 mobpsy-sn0int --version

echo
echo "Resultado: OK=$ok  WARN=$warn  BROKEN=$bad"
cat "$REPORT"

# Copia visible para el usuario.
install -d -o "$USER_NAME" -g "$USER_NAME" "$USER_HOME/MobPsy/Diagnostico"
cp "$REPORT" "$USER_HOME/MobPsy/Diagnostico/herramientas.tsv"
cp "$DETAIL" "$USER_HOME/MobPsy/Diagnostico/herramientas.log"
chown "$USER_NAME:$USER_NAME" \
  "$USER_HOME/MobPsy/Diagnostico/herramientas.tsv" \
  "$USER_HOME/MobPsy/Diagnostico/herramientas.log"

[ "$bad" -eq 0 ]
