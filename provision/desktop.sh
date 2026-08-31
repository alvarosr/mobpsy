#!/usr/bin/env bash
set -Eeuo pipefail

export DEBIAN_FRONTEND=noninteractive

echo
echo "============================================================"
echo " MobPsy Fase 0 - Instalando Ubuntu Desktop"
echo "============================================================"
echo

# 1) Paquetes actualizados de los repositorios de Ubuntu.
apt-get update

# 2) Escritorio Ubuntu completo.
# El metapaquete ubuntu-desktop incluye GNOME, GDM y X.Org.
apt-get install -y ubuntu-desktop

# 3) Usuario gráfico independiente del usuario interno de Vagrant.
if ! id mobpsy >/dev/null 2>&1; then
    useradd -m -s /bin/bash -G sudo mobpsy
fi

echo 'mobpsy:mobpsy' | chpasswd
cat >/etc/sudoers.d/90-mobpsy <<'EOF'
mobpsy ALL=(ALL) NOPASSWD:ALL
EOF
chmod 0440 /etc/sudoers.d/90-mobpsy

# 4) Configuración básica de escritorio.
timedatectl set-timezone Europe/Madrid || true
localectl set-keymap es || true
localectl set-x11-keymap es || true

# 5) GDM: sesión gráfica automática para la primera prueba.
# Forzamos Xorg para evitar añadir Wayland como variable en esta fase.
mkdir -p /etc/gdm3
python3 - <<'PY'
from pathlib import Path

p = Path("/etc/gdm3/custom.conf")
text = p.read_text() if p.exists() else "[daemon]\n"

if "[daemon]" not in text:
    text = "[daemon]\n" + text

lines = text.splitlines()
out = []
in_daemon = False
written = set()

wanted = {
    "AutomaticLoginEnable": "true",
    "AutomaticLogin": "mobpsy",
    "WaylandEnable": "false",
}

for line in lines:
    stripped = line.strip()
    if stripped.startswith("[") and stripped.endswith("]"):
        if in_daemon:
            for k, v in wanted.items():
                if k not in written:
                    out.append(f"{k}={v}")
            written.clear()
        in_daemon = stripped == "[daemon]"
        out.append(line)
        continue

    if in_daemon:
        key = stripped.lstrip("#").split("=", 1)[0].strip() if "=" in stripped.lstrip("#") else None
        if key in wanted:
            if key not in written:
                out.append(f"{key}={wanted[key]}")
                written.add(key)
            continue

    out.append(line)

if in_daemon:
    for k, v in wanted.items():
        if k not in written:
            out.append(f"{k}={v}")

p.write_text("\n".join(out) + "\n")
PY

# 6) El sistema debe arrancar en modo gráfico.
systemctl set-default graphical.target

# El paquete gdm3 crea display-manager.service. Lo comprobamos de forma explícita.
if ! test -x /usr/sbin/gdm3; then
    echo "ERROR: gdm3 no se ha instalado correctamente." >&2
    exit 20
fi

if ! dpkg-query -W -f='${Status}\n' ubuntu-desktop 2>/dev/null | grep -q "install ok installed"; then
    echo "ERROR: ubuntu-desktop no figura como instalado." >&2
    exit 21
fi

if [ "$(systemctl get-default)" != "graphical.target" ]; then
    echo "ERROR: el sistema no tiene graphical.target como objetivo por defecto." >&2
    exit 22
fi

echo
echo "============================================================"
echo " Ubuntu Desktop instalado correctamente."
echo " La VM se apagará y el instalador de Windows la abrirá"
echo " de nuevo en modo gráfico."
echo "============================================================"
echo
