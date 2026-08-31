#!/usr/bin/env bash
set -Eeuo pipefail

export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=a

echo
echo "============================================================"
echo " MobPsy - Actualización del sistema"
echo "============================================================"
echo

echo "[1/4] Actualizando repositorios APT..."
apt-get update

echo "[2/4] Aplicando actualizaciones de Ubuntu..."
apt-get -y upgrade

echo "[3/4] Actualizando paquetes Snap (Firefox, Chromium, etc.)..."
if command -v snap >/dev/null 2>&1; then
    snap refresh || true
fi

echo "[4/4] Limpiando dependencias que ya no son necesarias..."
apt-get -y autoremove
apt-get clean

echo
echo "Actualización finalizada."
echo
