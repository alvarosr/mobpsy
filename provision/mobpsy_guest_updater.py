#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile

VERSION_FILE = Path("/etc/mobpsy/version")
CONF_FILE = Path("/etc/mobpsy/update.conf")
DEFAULT_REPO = "alvarosr/mobpsy"
BACKUP_ROOT = Path("/var/backups/mobpsy")
INSTALL_ROOT = Path("/opt/mobpsy")

def current_version() -> str:
    try:
        return VERSION_FILE.read_text(encoding="utf-8").strip() or "1.0.0"
    except Exception:
        return "1.0.0"

def repository() -> str:
    env = os.environ.get("MOBPSY_UPDATE_REPOSITORY", "").strip()
    if env:
        return env
    try:
        for line in CONF_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("MOBPSY_UPDATE_REPOSITORY="):
                value = line.split("=", 1)[1].strip()
                if value:
                    return value
    except Exception:
        pass
    return DEFAULT_REPO

def version_tuple(value: str):
    nums = re.findall(r"\d+", value.lstrip("vV"))[:3]
    nums += ["0"] * (3 - len(nums))
    return tuple(int(x) for x in nums[:3])

def api_release(version: str):
    repo = repository()
    if version in ("", "latest"):
        url = f"https://api.github.com/repos/{repo}/releases/latest"
    else:
        tag = version if version.startswith("v") else f"v{version}"
        url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"MobPsy/{current_version()}",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))

def check(version: str = "latest"):
    installed = current_version()
    repo = repository()
    try:
        release = api_release(version)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return {
                "status": "prepublic",
                "installed": installed,
                "latest": None,
                "repository": repo,
                "message": "Todavía no existe una Release pública compatible de MobPsy.",
            }
        return {
            "status": "error",
            "installed": installed,
            "latest": None,
            "repository": repo,
            "message": f"GitHub respondió con HTTP {exc.code}.",
        }
    except Exception as exc:
        return {
            "status": "error",
            "installed": installed,
            "latest": None,
            "repository": repo,
            "message": f"No se pudo consultar GitHub: {exc}",
        }

    latest = str(release.get("tag_name") or "").lstrip("vV")
    assets = {str(a.get("name")): a for a in release.get("assets") or []}
    guest_name = f"MobPsy-guest-update-v{latest}.zip" if latest else ""
    sha_name = f"{guest_name}.sha256" if guest_name else ""
    compatible = bool(guest_name and guest_name in assets and sha_name in assets)
    available = bool(latest) and version_tuple(latest) > version_tuple(installed)

    if available and not compatible:
        status = "update_without_guest_package"
        message = f"MobPsy {latest} existe, pero la Release no incluye el paquete de actualización para OVA."
    elif available:
        status = "update_available"
        message = f"Nueva versión disponible: {latest}"
    else:
        status = "up_to_date"
        message = f"MobPsy {installed} está actualizado."

    return {
        "status": status,
        "installed": installed,
        "latest": latest or None,
        "repository": repo,
        "url": str(release.get("html_url") or f"https://github.com/{repo}/releases"),
        "message": message,
        "guest_asset": guest_name if compatible else None,
    }

def download(url: str, dest: Path):
    req = urllib.request.Request(url, headers={"User-Agent": f"MobPsy/{current_version()}"})
    with urllib.request.urlopen(req, timeout=60) as src, dest.open("wb") as dst:
        shutil.copyfileobj(src, dst)

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().lower()

def copy_tree(src: Path, dst: Path):
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

def create_backup() -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    target = BACKUP_ROOT / f"{stamp}_v{current_version()}"
    target.mkdir(parents=True, exist_ok=False)
    for name in ("app", "terminal", "analysis", "bookmarks", "branding"):
        src = INSTALL_ROOT / name
        if src.exists():
            shutil.copytree(src, target / name)
    if VERSION_FILE.exists():
        shutil.copy2(VERSION_FILE, target / "version")
    return target

def install_package(package: Path, expected_version: str):
    with tempfile.TemporaryDirectory(prefix="mobpsy_guest_update_extract_") as td:
        extract = Path(td)
        with zipfile.ZipFile(package, "r") as zf:
            zf.extractall(extract)

        meta_path = extract / "UPDATE.json"
        if not meta_path.is_file():
            raise RuntimeError("El paquete no contiene UPDATE.json.")
        meta = json.loads(meta_path.read_text(encoding="utf-8-sig"))
        if meta.get("product") != "MobPsy" or meta.get("type") != "guest-update":
            raise RuntimeError("El paquete no es una actualización guest válida de MobPsy.")
        package_version = str(meta.get("version") or "")
        if package_version != expected_version:
            raise RuntimeError(f"La versión del paquete ({package_version}) no coincide con {expected_version}.")

        backup = create_backup()
        print(f"[BACKUP] {backup}")

        mapping = {
            "app": INSTALL_ROOT / "app",
            "terminal": INSTALL_ROOT / "terminal",
            "analysis": INSTALL_ROOT / "analysis",
            "bookmarks": INSTALL_ROOT / "bookmarks",
        }
        for name, dst in mapping.items():
            src = extract / name
            if src.is_dir():
                copy_tree(src, dst)

        # Branding: solo logo corporativo. No se pisa el wallpaper del usuario.
        logo = extract / "assets" / "mobpsy_logo.png"
        if logo.is_file():
            (INSTALL_ROOT / "branding").mkdir(parents=True, exist_ok=True)
            shutil.copy2(logo, INSTALL_ROOT / "branding" / "mobpsy_logo.png")
            Path("/usr/share/pixmaps").mkdir(parents=True, exist_ok=True)
            shutil.copy2(logo, "/usr/share/pixmaps/mobpsy.png")
            app_assets = INSTALL_ROOT / "app" / "assets"
            app_assets.mkdir(parents=True, exist_ok=True)
            shutil.copy2(logo, app_assets / "mobpsy_logo.png")
            shutil.copy2(logo, app_assets / "mobpsy.png")

        # Dependencias de la GUI, si cambian.
        req = INSTALL_ROOT / "app" / "requirements.txt"
        pip = INSTALL_ROOT / "venv" / "bin" / "pip"
        if req.is_file() and pip.is_file():
            subprocess.run([str(pip), "install", "-r", str(req)], check=True)

        # Lanzadores estables.
        Path("/usr/local/bin/mobpsy").write_text(
            '#!/usr/bin/env bash\nset -e\nexec /opt/mobpsy/venv/bin/python /opt/mobpsy/app/main.py "$@"\n',
            encoding="utf-8",
        )
        Path("/usr/local/bin/mobpsy-cli").write_text(
            '#!/usr/bin/env bash\nset -e\nexec /usr/bin/python3 /opt/mobpsy/terminal/mobpsy_terminal.py "$@"\n',
            encoding="utf-8",
        )
        Path("/usr/local/bin/mobpsy-terminal").write_text(
            '#!/usr/bin/env bash\nset -e\nexec /usr/local/bin/mobpsy-cli "$@"\n',
            encoding="utf-8",
        )
        Path("/usr/local/bin/mobpsy-correlate").write_text(
            '#!/usr/bin/env bash\nset -e\nexec /usr/bin/python3 /opt/mobpsy/analysis/mobpsy_correlate.py "$@"\n',
            encoding="utf-8",
        )
        Path("/usr/local/bin/mobpsy-correlator").write_text(
            '#!/usr/bin/env bash\nset -e\nexec /usr/local/bin/mobpsy-correlate "$@"\n',
            encoding="utf-8",
        )
        for p in (
            "/usr/local/bin/mobpsy",
            "/usr/local/bin/mobpsy-cli",
            "/usr/local/bin/mobpsy-terminal",
            "/usr/local/bin/mobpsy-correlate",
            "/usr/local/bin/mobpsy-correlator",
        ):
            os.chmod(p, 0o755)

        # Verificaciones mínimas antes de marcar la versión como instalada.
        subprocess.run(
            [str(INSTALL_ROOT / "venv" / "bin" / "python"), "-m", "py_compile", str(INSTALL_ROOT / "app" / "main.py")],
            check=True,
        )
        if (INSTALL_ROOT / "analysis" / "mobpsy_correlate.py").is_file():
            subprocess.run(["/usr/local/bin/mobpsy-correlate", "--help"], check=True, stdout=subprocess.DEVNULL)

        VERSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        VERSION_FILE.write_text(expected_version + "\n", encoding="utf-8")
        subprocess.run(["update-desktop-database", "/usr/share/applications"], check=False)
        return backup

def update(version: str):
    if os.geteuid() != 0:
        raise RuntimeError("La instalación de actualizaciones necesita privilegios de administrador.")

    release = api_release(version)
    latest = str(release.get("tag_name") or "").lstrip("vV")
    if not latest:
        raise RuntimeError("La Release no contiene una versión válida.")

    assets = {str(a.get("name")): a for a in release.get("assets") or []}
    asset_name = f"MobPsy-guest-update-v{latest}.zip"
    sha_name = f"{asset_name}.sha256"
    if asset_name not in assets or sha_name not in assets:
        raise RuntimeError(f"La Release v{latest} no contiene {asset_name} y su SHA256.")

    with tempfile.TemporaryDirectory(prefix="mobpsy_guest_update_") as td:
        td = Path(td)
        package = td / asset_name
        hash_file = td / sha_name

        print(f"[1/5] Descargando MobPsy v{latest}...")
        download(str(assets[asset_name]["browser_download_url"]), package)
        download(str(assets[sha_name]["browser_download_url"]), hash_file)

        print("[2/5] Verificando SHA256...")
        expected = hash_file.read_text(encoding="utf-8", errors="replace").strip().split()[0].lower()
        actual = sha256(package)
        if expected != actual:
            raise RuntimeError("SHA256 incorrecto. La actualización se ha cancelado.")

        print("[3/5] Creando backup...")
        print("[4/5] Instalando actualización...")
        backup = install_package(package, latest)
        print("[5/5] Verificando...")
        print(f"[OK] MobPsy actualizado a v{latest}")
        print(f"[OK] Backup: {backup}")
        print("Cierra y vuelve a abrir MobPsy para cargar la nueva versión.")

def rollback():
    if os.geteuid() != 0:
        raise RuntimeError("Rollback necesita privilegios de administrador.")
    if not BACKUP_ROOT.is_dir():
        raise RuntimeError("No existen backups de actualizaciones.")
    backups = sorted([p for p in BACKUP_ROOT.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True)
    if not backups:
        raise RuntimeError("No existen backups de actualizaciones.")
    source = backups[0]
    for name in ("app", "terminal", "analysis", "bookmarks", "branding"):
        src = source / name
        if src.exists():
            copy_tree(src, INSTALL_ROOT / name)
    if (source / "version").is_file():
        VERSION_FILE.write_text((source / "version").read_text(encoding="utf-8").strip() + "\n", encoding="utf-8")
    print(f"[OK] Restaurado backup: {source}")
    print("Cierra y vuelve a abrir MobPsy.")

def main():
    parser = argparse.ArgumentParser(prog="mobpsy-guest-updater")
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check")
    p_check.add_argument("--json", action="store_true")
    p_check.add_argument("--version", default="latest")

    p_update = sub.add_parser("update")
    p_update.add_argument("--version", default="latest")

    sub.add_parser("rollback")
    args = parser.parse_args()

    if args.command == "check":
        data = check(args.version)
        if args.json:
            print(json.dumps(data, ensure_ascii=False))
        else:
            print(data["message"])
            print(f"Repositorio: https://github.com/{data['repository']}")
        return 1 if data["status"] == "error" else 0
    if args.command == "update":
        update(args.version)
        return 0
    if args.command == "rollback":
        rollback()
        return 0
    return 2

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        raise SystemExit(1)
