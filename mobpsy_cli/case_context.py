#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


CASES_DIR = Path.home() / "MobPsy" / "Casos"
ACTIVE_CASE_FILE = CASES_DIR / ".active_case.json"


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json_write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


def _unique_destination(folder: Path, filename: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    destination = folder / filename
    counter = 1
    while destination.exists():
        source = Path(filename)
        destination = folder / f"{source.stem}_{counter}{source.suffix}"
        counter += 1
    return destination


def get_active_case() -> dict[str, Any] | None:
    """
    Return information for the currently active *open* case.

    Closed cases are deliberately ignored so a tool cannot continue adding
    results to an investigation that the analyst has already closed.
    """
    try:
        active = json.loads(ACTIVE_CASE_FILE.read_text(encoding="utf-8"))
        case_dir = Path(str(active["case_dir"])).expanduser()
        manifest_path = case_dir / "case.json"

        if not case_dir.is_dir() or not manifest_path.is_file():
            return None

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if str(manifest.get("case_id", "")) != str(active.get("case_id", "")):
            return None
        if manifest.get("status", "abierto") == "cerrado":
            return None

        manifest.setdefault("evidence", [])
        manifest.setdefault("executions", [])

        return {
            "case_id": manifest.get("case_id"),
            "case_dir": case_dir,
            "manifest_path": manifest_path,
            "manifest": manifest,
        }
    except Exception:
        return None


def active_case_label() -> str:
    active = get_active_case()
    if not active:
        return ""
    return str(active["case_id"])


def _append_execution(
    manifest: dict[str, Any],
    *,
    tool_name: str,
    interface: str,
    command: list[str] | None,
    target_value: str,
    exit_code: int | None,
    status: str,
    output_path: str = "",
) -> dict[str, Any]:
    record = {
        "id": uuid.uuid4().hex,
        "tool": tool_name,
        "interface": interface,
        "target": target_value,
        "command": command or [],
        "status": status,
        "exit_code": exit_code,
        "output_path": output_path,
        "timestamp": _now(),
    }
    manifest.setdefault("executions", []).append(record)
    return record


def register_execution(
    tool_name: str,
    *,
    command: list[str] | None = None,
    interface: str = "unknown",
    target_value: str = "",
    exit_code: int | None = None,
    status: str = "finished",
) -> dict[str, Any] | None:
    """
    Record a tool execution in the active case without copying an output file.
    Useful for interactive tools such as Recon-ng, sn0int or ClatScope.
    """
    active = get_active_case()
    if not active:
        return None

    manifest = active["manifest"]
    record = _append_execution(
        manifest,
        tool_name=tool_name,
        interface=interface,
        command=command,
        target_value=target_value,
        exit_code=exit_code,
        status=status,
    )
    manifest["updated_at"] = _now()
    _atomic_json_write(active["manifest_path"], manifest)

    return {
        "case_id": active["case_id"],
        "execution": record,
    }


def register_export(
    source_path: str | Path,
    *,
    tool_name: str,
    interface: str = "unknown",
    target_value: str = "",
    exit_code: int | None = None,
    command: list[str] | None = None,
) -> dict[str, Any] | None:
    """
    Copy a generated MobPsy output into the active case and register both:
      - an export/evidence record with SHA-256
      - an execution record for the tool run

    Returns None when no open active case exists.
    """
    active = get_active_case()
    if not active:
        return None

    source = Path(source_path).expanduser()
    if not source.is_file():
        return None

    case_dir: Path = active["case_dir"]
    manifest: dict[str, Any] = active["manifest"]

    destination = _unique_destination(case_dir / "Exportaciones", source.name)
    # Con caso activo, la exportación pasa a pertenecer al expediente.\n    # Se mueve para evitar copias duplicadas en Exportaciones.\n    shutil.move(str(source), str(destination))\n    sha256 = _sha256(destination)

    evidence_record = {
        "id": uuid.uuid4().hex,
        "kind": "export",
        "source": "automatic",
        "tool": tool_name,
        "interface": interface,
        "target": target_value,
        "exit_code": exit_code,
        "original_path": str(source),
        "stored_name": destination.name,
        "stored_path": str(destination.relative_to(case_dir)),
        "size_bytes": destination.stat().st_size,
        "sha256": sha256,
        "added_at": _now(),
    }
    manifest.setdefault("evidence", []).append(evidence_record)

    execution_record = _append_execution(
        manifest,
        tool_name=tool_name,
        interface=interface,
        command=command,
        target_value=target_value,
        exit_code=exit_code,
        status="finished",
        output_path=str(destination.relative_to(case_dir)),
    )

    manifest["updated_at"] = _now()
    _atomic_json_write(active["manifest_path"], manifest)

    return {
        "case_id": active["case_id"],
        "destination": str(destination),
        "sha256": sha256,
        "evidence": evidence_record,
        "execution": execution_record,
    }
