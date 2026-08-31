#!/usr/bin/env bash
set -Eeuo pipefail

TARGET_SWAP_GB="${MOBPSY_SWAP_GB:-8}"
MIN_FREE_GB="${MOBPSY_MIN_FREE_GB:-12}"

echo "============================================================"
echo " MobPsy - Preparación de recursos para IA local"
echo "============================================================"

echo "[1/5] Detectando disco raíz..."
ROOT_SRC="$(findmnt -n -o SOURCE /)"
ROOT_FS="$(findmnt -n -o FSTYPE /)"
ROOT_REAL="$(readlink -f "$ROOT_SRC")"
echo "Raíz: $ROOT_SRC ($ROOT_FS)"

grow_plain_partition() {
    local part="$1"
    local partn parent disk
    partn="$(lsblk -n -o PARTN "$part" 2>/dev/null | head -1 | xargs || true)"
    parent="$(lsblk -n -o PKNAME "$part" 2>/dev/null | head -1 | xargs || true)"
    [ -n "$partn" ] && [ -n "$parent" ] || return 0
    disk="/dev/$parent"
    echo "Ampliando partición raíz: $disk $partn"
    growpart "$disk" "$partn" || true
}

echo "[2/5] Ampliando partición/sistema de archivos si el disco virtual creció..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq cloud-guest-utils lvm2 >/dev/null

if [[ "$ROOT_SRC" == /dev/mapper/* || "$ROOT_REAL" == /dev/dm-* ]]; then
    PV="$(pvs --noheadings -o pv_name 2>/dev/null | awk 'NF {print $1; exit}')"
    if [ -n "${PV:-}" ]; then
        grow_plain_partition "$PV"
        pvresize "$PV" >/dev/null 2>&1 || true
        LV_PATH="$(lvs --noheadings -o lv_path 2>/dev/null | awk 'NF {print $1; exit}')"
        if [ -n "${LV_PATH:-}" ]; then
            lvextend -r -l +100%FREE "$LV_PATH" >/dev/null 2>&1 || true
        fi
    fi
else
    grow_plain_partition "$ROOT_REAL"
    case "$ROOT_FS" in
        ext2|ext3|ext4) resize2fs "$ROOT_REAL" >/dev/null 2>&1 || true ;;
        xfs) xfs_growfs / >/dev/null 2>&1 || true ;;
        btrfs) btrfs filesystem resize max / >/dev/null 2>&1 || true ;;
    esac
fi

echo "[3/5] Preparando swap de ${TARGET_SWAP_GB} GB..."
SWAPFILE="/swapfile-mobpsy"
TARGET_BYTES=$((TARGET_SWAP_GB * 1024 * 1024 * 1024))

if [ -f "$SWAPFILE" ]; then
    CURRENT_BYTES="$(stat -c %s "$SWAPFILE" 2>/dev/null || echo 0)"
    if [ "$CURRENT_BYTES" -lt "$TARGET_BYTES" ]; then
        swapoff "$SWAPFILE" 2>/dev/null || true
        rm -f "$SWAPFILE"
    fi
fi

if [ ! -f "$SWAPFILE" ]; then
    if ! fallocate -l "${TARGET_SWAP_GB}G" "$SWAPFILE" 2>/dev/null; then
        dd if=/dev/zero of="$SWAPFILE" bs=1M count=$((TARGET_SWAP_GB * 1024)) status=progress
    fi
    chmod 600 "$SWAPFILE"
    mkswap "$SWAPFILE" >/dev/null
fi

swapon "$SWAPFILE" 2>/dev/null || true
grep -Fq "$SWAPFILE none swap sw 0 0" /etc/fstab || echo "$SWAPFILE none swap sw 0 0" >> /etc/fstab

cat >/etc/sysctl.d/99-mobpsy-ai.conf <<'EOF'
vm.swappiness=20
vm.vfs_cache_pressure=80
EOF
sysctl --system >/dev/null 2>&1 || true

echo "[4/5] Comprobando memoria y espacio..."
MEM_MB="$(awk '/MemTotal/ {printf "%d", $2/1024}' /proc/meminfo)"
SWAP_MB="$(awk '/SwapTotal/ {printf "%d", $2/1024}' /proc/meminfo)"
ROOT_GB="$(df -BG / | awk 'NR==2 {gsub(/G/,"",$2); print $2}')"
FREE_GB="$(df -BG / | awk 'NR==2 {gsub(/G/,"",$4); print $4}')"

echo "RAM guest:     ${MEM_MB} MB"
echo "Swap total:    ${SWAP_MB} MB"
echo "Disco raíz:    ${ROOT_GB} GB"
echo "Espacio libre: ${FREE_GB} GB"

if [ "$FREE_GB" -lt "$MIN_FREE_GB" ]; then
    echo "ERROR: quedan menos de ${MIN_FREE_GB} GB libres." >&2
    exit 72
fi

echo "[5/5] Preparando directorios..."
install -d -m 0755 /opt/mobpsy/analysis
install -d -m 0755 /var/lib/ollama
if id ollama >/dev/null 2>&1; then
    chown -R ollama:ollama /var/lib/ollama
fi

echo
echo "[OK] Recursos preparados para IA local."
