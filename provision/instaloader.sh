#!/usr/bin/env bash
set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive

ROOT="/opt/mobpsy/tools/instaloader"
VENV="$ROOT/venv"

echo
echo "============================================================"
echo " MobPsy - Fase 11: Instaloader"
echo "============================================================"

apt-get update
apt-get install -y python3 python3-venv python3-pip ca-certificates

install -d -m 0755 "$ROOT"

echo "[1/5] Creando entorno virtual..."
if [ ! -x "$VENV/bin/python" ]; then
    python3 -m venv "$VENV"
fi

echo "[2/5] Instalando/actualizando Instaloader..."
"$VENV/bin/python" -m pip install --upgrade pip setuptools wheel
"$VENV/bin/python" -m pip install --upgrade instaloader

echo "[3/5] Creando wrapper de metadatos de perfil..."
cat >"$ROOT/profile_metadata.py" <<'PY'
#!/usr/bin/env python3
import argparse
import instaloader
from instaloader import Profile

def main():
    parser = argparse.ArgumentParser(description="MobPsy Instaloader profile metadata")
    parser.add_argument("username")
    args = parser.parse_args()

    loader = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        quiet=True,
    )

    try:
        profile = Profile.from_username(loader.context, args.username.strip())
    except Exception as exc:
        print(f"Error consultando Instagram: {exc}")
        return 1

    fields = [
        ("Username", profile.username),
        ("ID", profile.userid),
        ("Nombre", profile.full_name),
        ("BiografÃ­a", profile.biography),
        ("Seguidores", profile.followers),
        ("Seguidos", profile.followees),
        ("Publicaciones", profile.mediacount),
        ("Privado", profile.is_private),
        ("Verificado", profile.is_verified),
        ("URL externa", profile.external_url),
    ]

    for label, attr in [
        ("Cuenta negocio", "is_business_account"),
        ("CategorÃ­a negocio", "business_category_name"),
    ]:
        try:
            fields.append((label, getattr(profile, attr)))
        except Exception:
            pass

    print("Instaloader - metadatos de perfil")
    print("-" * 60)
    for label, value in fields:
        print(f"{label}: {'' if value is None else value}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
PY
chmod 0755 "$ROOT/profile_metadata.py"

echo "[4/5] Creando lanzador estable..."
cat >/usr/local/bin/mobpsy-instaloader-profile <<EOF
#!/usr/bin/env bash
set -e
exec "$VENV/bin/python" "$ROOT/profile_metadata.py" "\$@"
EOF
chmod 0755 /usr/local/bin/mobpsy-instaloader-profile
# MOBPSY_ALIAS_INSTALOADER_V1
ln -sf /usr/local/bin/mobpsy-instaloader-profile /usr/local/bin/mobpsy-instaloader

echo "[5/5] Verificando..."
/usr/local/bin/mobpsy-instaloader-profile --help >/dev/null

VERSION="$("$VENV/bin/python" - <<'PY'
from importlib.metadata import version
print(version("instaloader"))
PY
)"

mkdir -p /etc/mobpsy
cat >/etc/mobpsy/instaloader <<EOF
TOOL=instaloader
METHOD=python-venv-pypi-wrapper
PACKAGE=instaloader
VERSION=${VERSION}
MODE=profile-metadata-no-download
LAUNCHER=/usr/local/bin/mobpsy-instaloader-profile
EOF

echo "Instaloader ${VERSION} preparado."
