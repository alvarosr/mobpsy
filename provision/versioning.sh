#!/usr/bin/env bash
set -Eeuo pipefail

VERSION="1.0.0"
REPOSITORY="${MOBPSY_UPDATE_REPOSITORY:-alvarosr/mobpsy}"
USER_NAME="mobpsy"

echo
echo "============================================================"
echo " MobPsy - Actualizador interno para OVA"
echo "============================================================"
echo

install -d -m 0755 /etc/mobpsy /usr/local/lib/mobpsy /var/backups/mobpsy
printf '%s\n' "$VERSION" >/etc/mobpsy/version
printf 'MOBPSY_UPDATE_REPOSITORY=%s\n' "$REPOSITORY" >/etc/mobpsy/update.conf

if [ ! -f /tmp/mobpsy_guest_updater.py ]; then
    echo "ERROR: falta /tmp/mobpsy_guest_updater.py" >&2
    exit 251
fi

install -m 0755 /tmp/mobpsy_guest_updater.py /usr/local/lib/mobpsy/mobpsy_guest_updater.py

cat >/usr/local/bin/mobpsy-update-check <<'EOF'
#!/usr/bin/env bash
set -e
exec /usr/bin/python3 /usr/local/lib/mobpsy/mobpsy_guest_updater.py check "$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-update-check

cat >/usr/local/lib/mobpsy/mobpsy-update-root <<'EOF'
#!/usr/bin/env bash
set -e
case "${1:-}" in
  update)
    shift
    exec /usr/bin/python3 /usr/local/lib/mobpsy/mobpsy_guest_updater.py update "$@"
    ;;
  rollback)
    shift
    exec /usr/bin/python3 /usr/local/lib/mobpsy/mobpsy_guest_updater.py rollback "$@"
    ;;
  *)
    echo "Uso: mobpsy-update-root {update|rollback}" >&2
    exit 2
    ;;
esac
EOF
chmod 0755 /usr/local/lib/mobpsy/mobpsy-update-root

cat >/usr/local/bin/mobpsy-update <<'EOF'
#!/usr/bin/env bash
set -e
case "${1:-}" in
  --rollback|rollback)
    exec sudo -n /usr/local/lib/mobpsy/mobpsy-update-root rollback
    ;;
  --version)
    [ -n "${2:-}" ] || { echo "Falta versión." >&2; exit 2; }
    exec sudo -n /usr/local/lib/mobpsy/mobpsy-update-root update --version "$2"
    ;;
  ""|latest)
    exec sudo -n /usr/local/lib/mobpsy/mobpsy-update-root update --version latest
    ;;
  *)
    echo "Uso: mobpsy-update [latest|--version X.Y.Z|--rollback]" >&2
    exit 2
    ;;
esac
EOF
chmod 0755 /usr/local/bin/mobpsy-update

cat >/etc/sudoers.d/mobpsy-updater <<EOF
${USER_NAME} ALL=(root) NOPASSWD: /usr/local/lib/mobpsy/mobpsy-update-root
EOF
chmod 0440 /etc/sudoers.d/mobpsy-updater
visudo -cf /etc/sudoers.d/mobpsy-updater >/dev/null

rm -f /tmp/mobpsy_guest_updater.py

echo "[OK] Comandos instalados:"
echo "     mobpsy-update-check"
echo "     mobpsy-update"
echo
sudo -u "$USER_NAME" /usr/local/bin/mobpsy-update-check || true
