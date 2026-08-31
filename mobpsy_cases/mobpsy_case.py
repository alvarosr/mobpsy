#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

CASES_DIR = Path.home() / "MobPsy" / "Casos"
EXPORT_DIR = Path.home() / "MobPsy" / "Exportaciones"
ACTIVE_CASE_FILE = CASES_DIR / ".active_case.json"


def safe_slug(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return value.strip("._-")[:70] or "caso"


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def case_dirs():
    CASES_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for folder in CASES_DIR.iterdir():
        if folder.is_dir() and (folder / "case.json").is_file():
            try:
                data = json.loads((folder / "case.json").read_text(encoding="utf-8"))
            except Exception:
                continue
            rows.append((data.get("created_at", ""), folder, data))
    return sorted(rows, key=lambda x: x[0], reverse=True)


def find_case(case_id: str | None):
    if not case_id:
        try:
            active = json.loads(ACTIVE_CASE_FILE.read_text(encoding="utf-8"))
            case_id = active.get("case_id")
        except Exception:
            case_id = None
    if not case_id:
        raise SystemExit("No hay caso activo. Usa: mobpsy-case active <CASE_ID>")
    for _, folder, data in case_dirs():
        if data.get("case_id") == case_id:
            return folder, data
    raise SystemExit(f"No se encuentra el caso: {case_id}")


def save_manifest(folder: Path, data: dict):
    data["updated_at"] = datetime.now().isoformat(timespec="seconds")
    (folder / "case.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def cmd_list(args):
    active = ""
    try:
        active = json.loads(ACTIVE_CASE_FILE.read_text(encoding="utf-8")).get("case_id", "")
    except Exception:
        pass

    rows = case_dirs()
    if not rows:
        print("No hay casos.")
        return 0

    for _, folder, data in rows:
        mark = "*" if data.get("case_id") == active else " "
        print(
            f"{mark} {data.get('case_id')}  "
            f"[{data.get('status', 'abierto')}]  "
            f"{data.get('title', folder.name)}"
        )
    return 0


def cmd_new(args):
    title = args.title or input("Título: ").strip()
    subject = args.subject or input("Objetivo: ").strip()
    notes = args.notes or input("Notas: ").strip()

    if not title:
        raise SystemExit("El título es obligatorio.")

    now = datetime.now()
    case_id = f"MOB-{now.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
    folder = CASES_DIR / f"{case_id}_{safe_slug(title)}"

    (folder / "Evidencias").mkdir(parents=True)
    (folder / "Exportaciones").mkdir()
    (folder / "Informes").mkdir()

    manifest = {
        "schema_version": 1,
        "case_id": case_id,
        "title": title,
        "subject": subject,
        "notes": notes,
        "status": "abierto",
        "created_at": now.isoformat(timespec="seconds"),
        "updated_at": now.isoformat(timespec="seconds"),
        "evidence": [],
        "executions": [],
    }
    save_manifest(folder, manifest)

    ACTIVE_CASE_FILE.write_text(
        json.dumps(
            {"case_id": case_id, "case_dir": str(folder), "updated_at": now.isoformat(timespec="seconds")},
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print(case_id)
    print(folder)
    return 0


def cmd_active(args):
    folder, data = find_case(args.case_id)
    ACTIVE_CASE_FILE.write_text(
        json.dumps(
            {
                "case_id": data["case_id"],
                "case_dir": str(folder),
                "updated_at": datetime.now().isoformat(timespec="seconds"),
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    print(f"Caso activo: {data['case_id']} · {data.get('title')}")
    return 0


def cmd_show(args):
    folder, data = find_case(args.case_id)
    print(f"ID:       {data.get('case_id')}")
    print(f"Título:   {data.get('title')}")
    print(f"Objetivo: {data.get('subject')}")
    print(f"Estado:   {data.get('status')}")
    print(f"Creado:   {data.get('created_at')}")
    print(f"Carpeta:  {folder}")
    print(f"Archivos: {len(data.get('evidence', []))}")
    print(f"Ejecuciones: {len(data.get('executions', []))}")
    print()
    if data.get("notes"):
        print("Notas:")
        print(data["notes"])
    return 0


def add_file(folder: Path, data: dict, source: Path, kind: str):
    if not source.is_file():
        raise SystemExit(f"No existe el archivo: {source}")

    dest_root = folder / ("Evidencias" if kind == "evidence" else "Exportaciones")
    dest_root.mkdir(exist_ok=True)

    try:
        same_folder = source.resolve().parent == dest_root.resolve()
    except Exception:
        same_folder = False

    destination = source if same_folder else dest_root / source.name
    if not same_folder:
        n = 1
        while destination.exists():
            destination = dest_root / f"{source.stem}_{n}{source.suffix}"
            n += 1

    original_path = str(source)
    if not same_folder:
        shutil.move(str(source), str(destination))

    sha = hash_file(destination)
    record = {
        "id": uuid.uuid4().hex,
        "kind": kind,
        "original_path": original_path,
        "stored_name": destination.name,
        "stored_path": str(destination.relative_to(folder)),
        "size_bytes": destination.stat().st_size,
        "sha256": sha,
        "added_at": datetime.now().isoformat(timespec="seconds"),
    }
    data.setdefault("evidence", []).append(record)
    save_manifest(folder, data)

    print(f"Movido al caso: {destination}")
    print(f"SHA-256: {sha}")


def cmd_add(args):
    folder, data = find_case(args.case_id)
    add_file(folder, data, Path(args.path).expanduser().resolve(), args.kind)
    return 0




def cmd_inactive(args):
    if not ACTIVE_CASE_FILE.exists():
        print("No hay ningún caso activo.")
        return 0
    try:
        active = json.loads(ACTIVE_CASE_FILE.read_text(encoding="utf-8"))
        old_id = active.get("case_id", "")
    except Exception:
        old_id = ""
    ACTIVE_CASE_FILE.unlink(missing_ok=True)
    print(f"Sin caso activo{': ' + old_id if old_id else ''}.")
    return 0


def _remove_record(folder: Path, data: dict, record: dict):
    stored_rel = str(record.get("stored_path", ""))
    if stored_rel:
        target = (folder / stored_rel).resolve()
        root = folder.resolve()
        if target.is_relative_to(root) and target.is_file():
            target.unlink()

    record_id = str(record.get("id", ""))
    data["evidence"] = [
        rec for rec in data.get("evidence", [])
        if str(rec.get("id", "")) != record_id
    ]
    for execution in data.get("executions", []):
        if stored_rel and execution.get("output_path") == stored_rel:
            execution["output_path"] = ""
            execution["output_removed_at"] = datetime.now().isoformat(timespec="seconds")
    save_manifest(folder, data)


def cmd_remove(args):
    folder, data = find_case(args.case_id)
    records = data.get("evidence", [])
    if not records:
        print("El caso no tiene evidencias ni exportaciones.")
        return 0

    record = None
    if getattr(args, "record_id", None):
        record = next((r for r in records if str(r.get("id")) == str(args.record_id)), None)
    elif getattr(args, "index", None):
        idx = int(args.index)
        if 1 <= idx <= len(records):
            record = records[idx - 1]

    if record is None:
        raise SystemExit("No se encuentra el elemento indicado.")

    _remove_record(folder, data, record)
    print(f"Eliminado: {record.get('stored_name', '?')}")
    return 0


def cmd_runs(args):
    folder, data = find_case(args.case_id)
    executions = data.get("executions", [])
    if not executions:
        print("No hay ejecuciones registradas.")
        return 0

    limit = args.limit
    selected = executions[-limit:] if limit else executions
    for execution in selected:
        command = " ".join(execution.get("command") or [])
        code = execution.get("exit_code")
        code_text = "" if code is None else f" exit={code}"
        print(
            f"{execution.get('timestamp', '?')}  "
            f"{execution.get('tool', '?')}  "
            f"[{execution.get('interface', '?')}] "
            f"{execution.get('status', '?')}{code_text}"
        )
        if command:
            print(f"  {command}")
        if execution.get("output_path"):
            print(f"  salida: {execution['output_path']}")
    return 0


def report(folder: Path, data: dict):
    lines = [
        f"# MobPsy · Informe de caso {data.get('case_id')}",
        "",
        f"**Título:** {data.get('title', '')}",
        f"**Objetivo:** {data.get('subject') or 'Sin especificar'}",
        f"**Estado:** {data.get('status', '')}",
        f"**Creado:** {data.get('created_at', '')}",
        "",
        "## Notas",
        "",
        data.get("notes") or "_Sin notas._",
        "",
        "## Evidencias y exportaciones",
        "",
    ]

    for idx, rec in enumerate(data.get("evidence", []), 1):
        kind = "Evidencia" if rec.get("kind") == "evidence" else "Exportación"
        lines += [
            f"### {idx}. {kind}: {rec.get('stored_name', '')}",
            f"- Herramienta: {rec.get('tool', 'manual')}",
            f"- Origen: {rec.get('source', 'manual')}",
            f"- Añadido: {rec.get('added_at', '')}",
            f"- Tamaño: {rec.get('size_bytes', 0)} bytes",
            f"- SHA-256: `{rec.get('sha256', '')}`",
            f"- Ruta: `{rec.get('stored_path', '')}`",
            "",
        ]

    lines += ["", "## Historial de ejecuciones", ""]
    executions = data.get("executions", [])
    if not executions:
        lines.append("_No hay ejecuciones registradas._")
    else:
        for idx, execution in enumerate(executions, 1):
            command = " ".join(execution.get("command") or [])
            lines += [
                f"### {idx}. {execution.get('tool', '?')}",
                f"- Fecha: {execution.get('timestamp', '')}",
                f"- Interfaz: {execution.get('interface', '')}",
                f"- Estado: {execution.get('status', '')}",
                f"- Código de salida: {execution.get('exit_code')}",
                f"- Comando: `{command}`" if command else "- Comando: no registrado",
                f"- Salida: `{execution.get('output_path', '')}`" if execution.get("output_path") else "- Salida: sin archivo asociado",
                "",
            ]

    target = folder / "Informes" / f"Informe_{data.get('case_id')}.md"
    target.parent.mkdir(exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")
    return target


def cmd_report(args):
    folder, data = find_case(args.case_id)
    ai_bin = shutil.which("mobpsy-ai")
    if ai_bin:
        completed = subprocess.run(
            [ai_bin, "report", str(data.get("case_id") or "")],
            text=True,
        )
        return completed.returncode

    print(report(folder, data))
    return 0


def cmd_open(args):
    folder, data = find_case(args.case_id)
    subprocess.Popen(["xdg-open", str(folder)])
    return 0


def interactive():
    while True:
        print()
        print("=" * 70)
        print("MobPsy · Casos y Evidencias")
        print("=" * 70)
        print("[1] Listar casos")
        print("[2] Crear caso")
        print("[3] Establecer caso activo")
        print("[4] Ver caso activo")
        print("[5] Añadir evidencia al caso activo")
        print("[6] Importar exportación al caso activo")
        print("[7] Generar informe del caso activo")
        print("[8] Abrir carpeta del caso activo")
        print("[9] Ver ejecuciones recientes")
        print("[10] Quitar caso activo")
        print("[11] Eliminar evidencia/exportación del caso activo")
        print("[0] Salir")
        choice = input("Opción: ").strip()

        try:
            if choice == "0":
                return 0
            if choice == "1":
                cmd_list(argparse.Namespace())
            elif choice == "2":
                cmd_new(argparse.Namespace(title=None, subject=None, notes=None))
            elif choice == "3":
                cid = input("CASE_ID: ").strip()
                cmd_active(argparse.Namespace(case_id=cid))
            elif choice == "4":
                cmd_show(argparse.Namespace(case_id=None))
            elif choice in ("5", "6"):
                path = input("Ruta del archivo: ").strip()
                kind = "evidence" if choice == "5" else "export"
                cmd_add(argparse.Namespace(case_id=None, path=path, kind=kind))
            elif choice == "7":
                cmd_report(argparse.Namespace(case_id=None))
            elif choice == "8":
                cmd_open(argparse.Namespace(case_id=None))
            elif choice == "9":
                cmd_runs(argparse.Namespace(case_id=None, limit=20))
            elif choice == "10":
                cmd_inactive(argparse.Namespace())
            elif choice == "11":
                folder, data = find_case(None)
                records = data.get("evidence", [])
                if not records:
                    print("El caso no tiene evidencias ni exportaciones.")
                    continue
                print()
                for idx, rec in enumerate(records, 1):
                    kind = "Evidencia" if rec.get("kind") == "evidence" else "Exportación"
                    print(f"[{idx}] {kind}: {rec.get('stored_name', '?')}")
                value = input("Número a eliminar (ENTER cancela): ").strip()
                if not value:
                    continue
                if not value.isdigit() or not (1 <= int(value) <= len(records)):
                    print("Selección no válida.")
                    continue
                rec = records[int(value) - 1]
                confirm = input(f"Eliminar {rec.get('stored_name', '?')} y su archivo? [s/N]: ").strip().lower()
                if confirm in ("s", "si", "sí", "y", "yes"):
                    _remove_record(folder, data, rec)
                    print("Eliminado.")
        except SystemExit as exc:
            print(exc)


def build_parser():
    parser = argparse.ArgumentParser(description="Gestor de Casos y Evidencias de MobPsy")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("list")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("new")
    p.add_argument("--title")
    p.add_argument("--subject")
    p.add_argument("--notes")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("active")
    p.add_argument("case_id")
    p.set_defaults(func=cmd_active)

    p = sub.add_parser("inactive", aliases=["clear-active"])
    p.set_defaults(func=cmd_inactive)

    p = sub.add_parser("remove")
    p.add_argument("--case-id")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--id", dest="record_id")
    group.add_argument("--index", type=int)
    p.set_defaults(func=cmd_remove)

    p = sub.add_parser("show")
    p.add_argument("case_id", nargs="?")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("add")
    p.add_argument("path")
    p.add_argument("--case-id")
    p.add_argument("--kind", choices=["evidence", "export"], default="evidence")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("runs")
    p.add_argument("case_id", nargs="?")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=cmd_runs)

    p = sub.add_parser("report")
    p.add_argument("case_id", nargs="?")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("open")
    p.add_argument("case_id", nargs="?")
    p.set_defaults(func=cmd_open)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        return interactive()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
