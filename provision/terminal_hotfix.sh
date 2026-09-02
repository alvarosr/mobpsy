#!/usr/bin/env bash
set -Eeuo pipefail

CLI_SRC=/tmp/mobpsy_terminal_hotfix.py
GUI_SRC=/tmp/mobpsy_main_hotfix.py
CLI_DST=/opt/mobpsy/terminal/mobpsy_terminal.py
GUI_DST=/opt/mobpsy/app/main.py

for f in "$CLI_SRC" "$GUI_SRC"; do
  if [ ! -f "$f" ]; then
    echo "ERROR: falta $f" >&2
    exit 181
  fi
done

install -m 0755 "$CLI_SRC" "$CLI_DST"
install -m 0644 "$GUI_SRC" "$GUI_DST"

cat >/usr/local/bin/mobpsy-terminal <<'EOF2'
#!/usr/bin/env bash
# Contenedor persistente de MobPsy Terminal: evita que GNOME Terminal desaparezca
# si la TUI termina por un error o por un stdin alterado por una herramienta.
set +e
/usr/local/bin/mobpsy-cli "$@"
rc=$?
echo
echo "============================================================"
if [ "$rc" -eq 0 ]; then
  echo " MobPsy Terminal finalizado."
else
  echo " MobPsy Terminal terminó con código $rc."
fi
echo " Pulsa ENTER para cerrar esta ventana."
echo "============================================================"
if [ -r /dev/tty ]; then
  read -r _ </dev/tty || true
else
  read -r _ || true
fi
exit "$rc"
EOF2
chmod 0755 /usr/local/bin/mobpsy-terminal

cat >/usr/share/applications/mobpsy-terminal.desktop <<'EOF2'
[Desktop Entry]
Type=Application
Version=1.0
Name=MobPsy Terminal
GenericName=OSINT Terminal Interface
Comment=Interfaz full-terminal de MobPsy para las herramientas OSINT instaladas
Exec=gnome-terminal --maximize -- /usr/local/bin/mobpsy-terminal
Icon=utilities-terminal
Terminal=false
Categories=Utility;Security;
StartupNotify=true
EOF2
chmod 0644 /usr/share/applications/mobpsy-terminal.desktop
update-desktop-database /usr/share/applications >/dev/null 2>&1 || true

/usr/bin/python3 -m py_compile "$CLI_DST"
if [ -x /opt/mobpsy/venv/bin/python ]; then
  /opt/mobpsy/venv/bin/python -m py_compile "$GUI_DST"
else
  /usr/bin/python3 -m py_compile "$GUI_DST"
fi

rm -f "$CLI_SRC" "$GUI_SRC"
echo "MOBPSY_TERMINAL_HOTFIX_OK"
