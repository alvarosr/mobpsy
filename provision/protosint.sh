#!/usr/bin/env bash
set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive

ROOT="/opt/mobpsy/tools/protosint"
SRC="$ROOT/src"
VENV="$ROOT/venv"
REPO="https://github.com/pixelbubble/ProtOSINT.git"

echo
echo "============================================================"
echo " MobPsy - Fase 10: ProtOSINT"
echo "============================================================"

apt-get update
apt-get install -y git python3 python3-venv python3-pip ca-certificates

install -d -m 0755 "$ROOT"

echo "[1/5] Sincronizando repositorio oficial..."
if [ ! -d "$SRC/.git" ]; then
    rm -rf "$SRC"
    git clone "$REPO" "$SRC"
else
    BRANCH="$(git -C "$SRC" remote show origin | sed -n '/HEAD branch/s/.*: //p')"
    [ -n "$BRANCH" ] || BRANCH="main"
    git -C "$SRC" fetch origin "$BRANCH"
    git -C "$SRC" reset --hard "origin/$BRANCH"
    git -C "$SRC" clean -fd
fi
COMMIT="$(git -C "$SRC" rev-parse HEAD)"

echo "[2/5] Creando entorno virtual..."
if [ ! -x "$VENV/bin/python" ]; then
    python3 -m venv "$VENV"
fi
"$VENV/bin/python" -m pip install --upgrade pip setuptools wheel
"$VENV/bin/python" -m pip install --upgrade -r "$SRC/requirements.txt"

echo "[3/5] Creando wrapper MobPsy sin credenciales/Selenium..."
cat >"$ROOT/mobpsy_protosint.py" <<PY
#!/usr/bin/env python3
import argparse
import sys

sys.path.insert(0, r"$SRC")
import protosint as p

def main():
    parser = argparse.ArgumentParser(description="MobPsy wrapper for ProtOSINT")
    parser.add_argument("email")
    args = parser.parse_args()

    email = args.email.strip().lower()
    p.SELENIUM_MODE = False

    print("ProtOSINT - modo API/key-server (sin Selenium)")
    print(f"Objetivo: {email}")
    print("-" * 60)

    try:
        status, source = p.verify_existence(email)
        print(f"Existencia ({source}): {status}")
    except Exception as exc:
        status = "unknown"
        print(f"Existencia: error ({exc})")

    try:
        present, created, key_type = p.keyserver_info(email)
        if present:
            created_txt = created.isoformat() if created else "desconocida"
            print(f"Key server: clave presente")
            print(f"Fecha de clave: {created_txt}")
            print(f"Tipo de clave: {key_type or 'desconocido'}")
            if status == "absent":
                print("Aviso: ProtOSINT indica que una clave puede ser DECOY si la cuenta no existe.")
        else:
            print("Key server: no se devolvió clave")
    except Exception as exc:
        print(f"Key server: error ({exc})")

    print()
    print("Nota: el proyecto considera Selenium con sesión Proton el método más fiable.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
PY
chmod 0755 "$ROOT/mobpsy_protosint.py"

echo "[4/5] Creando lanzador estable..."
cat >/usr/local/bin/mobpsy-protosint <<EOF
#!/usr/bin/env bash
set -e
exec "$VENV/bin/python" "$ROOT/mobpsy_protosint.py" "\$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-protosint

echo "[5/5] Verificando..."
/usr/local/bin/mobpsy-protosint -h >/dev/null

mkdir -p /etc/mobpsy
cat >/etc/mobpsy/protosint <<EOF
TOOL=protosint
METHOD=git-python-wrapper
REPOSITORY=${REPO}
COMMIT=${COMMIT}
MODE=api-keyserver-no-selenium
LAUNCHER=/usr/local/bin/mobpsy-protosint
EOF

echo "ProtOSINT preparado (${COMMIT})."
