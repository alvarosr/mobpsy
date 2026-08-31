#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import ipaddress
import json
import re
import sys
import subprocess
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

VERSION = "1.0.0"
CASES_DIR = Path.home() / "MobPsy" / "Casos"
ACTIVE_CASE_FILE = CASES_DIR / ".active_case.json"

TEXT_EXTENSIONS = {
    ".txt", ".log", ".csv", ".tsv", ".json", ".jsonl", ".xml", ".html", ".htm",
    ".md", ".yaml", ".yml", ".ini", ".conf", ".cfg", ".py", ".js", ".ps1", ".sh"
}
MAX_TEXT_BYTES = 25 * 1024 * 1024

EMAIL_RE = re.compile(r"(?<![\w.+-])([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,63})(?![\w.-])", re.I)
URL_RE = re.compile(r"\bhttps?://[^\s<>'\"{}\[\]|\\^`]+", re.I)
DOMAIN_RE = re.compile(r"(?<![@\w-])((?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,63})(?![\w-])", re.I)
IPV4_RE = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
IPV6_CANDIDATE_RE = re.compile(r"(?<![0-9A-Fa-f:])(?:[0-9A-Fa-f]{0,4}:){2,7}[0-9A-Fa-f]{0,4}(?![0-9A-Fa-f:])")
HASH_RE = re.compile(r"(?<![0-9A-Fa-f])([0-9A-Fa-f]{32}|[0-9A-Fa-f]{40}|[0-9A-Fa-f]{64})(?![0-9A-Fa-f])")
HANDLE_RE = re.compile(r"(?<![\w@])@([A-Za-z0-9_][A-Za-z0-9_.-]{1,31})(?![\w.-])")
PHONE_RE = re.compile(r"(?<!\w)(\+?\d[\d\s().-]{6,}\d)(?!\w)")

GENERATED_NAMES = {
    "correlation.json", "entities.csv", "relations.csv",
    "correlation.graphml", "correlation_graph.dot", "correlation_graph.svg", "correlation_report.md", "correlation_report.html"
}

def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def active_case_id() -> str | None:
    data = load_json(ACTIVE_CASE_FILE)
    for key in ("case_id", "id", "case"):
        value = data.get(key)
        if value:
            return str(value)
    return None

def iter_cases():
    if not CASES_DIR.is_dir():
        return
    for folder in sorted(CASES_DIR.iterdir()):
        if not folder.is_dir():
            continue
        manifest = folder / "case.json"
        if manifest.is_file():
            yield folder, load_json(manifest)

def find_case(case_id: str | None = None, case_path: str | None = None):
    if case_path:
        folder = Path(case_path).expanduser().resolve()
        manifest = folder / "case.json"
        if not manifest.is_file():
            raise RuntimeError(f"No existe case.json en {folder}.")
        return folder, load_json(manifest)

    wanted = case_id or active_case_id()
    if not wanted:
        raise RuntimeError(
            "No hay ningún caso activo. Selecciona uno con mobpsy-case "
            "o usa --case-id / --case-path."
        )

    for folder, data in iter_cases() or []:
        candidates = {
            str(data.get("case_id") or ""),
            str(data.get("id") or ""),
            folder.name,
        }
        if wanted in candidates:
            return folder, data
    raise RuntimeError(f"No se encuentra el caso '{wanted}'.")

def is_probably_text(path: Path) -> bool:
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return True
    try:
        sample = path.read_bytes()[:4096]
    except OSError:
        return False
    if b"\x00" in sample:
        return False
    if not sample:
        return True
    printable = sum((32 <= b <= 126) or b in (9,10,13) or b >= 128 for b in sample)
    return printable / len(sample) > 0.82

def read_text(path: Path) -> str | None:
    try:
        if path.stat().st_size > MAX_TEXT_BYTES or not is_probably_text(path):
            return None
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

def norm_domain(value: str) -> str:
    return value.strip().rstrip(".").lower()

def norm_email(value: str) -> str:
    return value.strip().lower()

def norm_url(value: str) -> str:
    return value.strip().rstrip(".,;:!?)\"]}'")

def norm_phone(value: str) -> str | None:
    value = value.strip()
    plus = value.startswith("+")
    digits = re.sub(r"\D", "", value)
    if len(digits) < 7 or len(digits) > 15:
        return None
    return ("+" if plus else "") + digits

def valid_ip(value: str) -> str | None:
    try:
        return str(ipaddress.ip_address(value.strip()))
    except ValueError:
        return None

def entity_key(kind: str, value: str) -> str:
    return hashlib.sha256(f"{kind}\0{value}".encode("utf-8")).hexdigest()[:20]

def extract_entities(text: str):
    found: dict[tuple[str,str], set[str]] = defaultdict(set)

    urls = []
    for m in URL_RE.finditer(text):
        value = norm_url(m.group(0))
        if value:
            found[("url", value)].add(m.group(0))
            urls.append(value)

    for m in EMAIL_RE.finditer(text):
        value = norm_email(m.group(1))
        found[("email", value)].add(m.group(1))

    for m in IPV4_RE.finditer(text):
        value = valid_ip(m.group(0))
        if value:
            found[("ip", value)].add(m.group(0))

    for m in IPV6_CANDIDATE_RE.finditer(text):
        candidate = m.group(0)
        if ":" not in candidate:
            continue
        value = valid_ip(candidate)
        if value:
            found[("ip", value)].add(candidate)

    for m in HASH_RE.finditer(text):
        value = m.group(1).lower()
        kind = {32:"md5", 40:"sha1", 64:"sha256"}.get(len(value), "hash")
        found[("hash", value)].add(kind)

    for m in HANDLE_RE.finditer(text):
        handle = m.group(1)
        # Evita duplicar el usuario de un email como @handle.
        end = m.end()
        if end < len(text) and text[end:end+1] == ".":
            continue
        found[("username", handle.lower())].add("@" + handle)

    for m in PHONE_RE.finditer(text):
        value = norm_phone(m.group(1))
        if value:
            found[("phone", value)].add(m.group(1))

    # Dominios: excluye los que ya forman parte de emails/URLs, pero mantenerlos
    # como entidad independiente es útil para correlación. Se deduplican abajo.
    for m in DOMAIN_RE.finditer(text):
        value = norm_domain(m.group(1))
        if value:
            found[("domain", value)].add(m.group(1))

    # Añade explícitamente hostname de cada URL, incluso si regex de dominio no lo capturó.
    for url in urls:
        try:
            host = urlparse(url).hostname
        except Exception:
            host = None
        if host:
            ip = valid_ip(host)
            if ip:
                found[("ip", ip)].add(host)
            elif "." in host:
                found[("domain", norm_domain(host))].add(host)

    return found

def source_kind(path: Path, case_folder: Path) -> str:
    try:
        rel = path.relative_to(case_folder)
        first = rel.parts[0].lower() if rel.parts else ""
    except ValueError:
        first = ""
    if first.startswith("evid"):
        return "evidence"
    if first.startswith("export"):
        return "export"
    return "case_file"

def candidate_files(case_folder: Path):
    preferred = []
    for name in ("Evidencias","Exportaciones","Evidences","Exports"):
        p = case_folder / name
        if p.is_dir():
            preferred.append(p)
    if not preferred:
        preferred = [case_folder]

    seen = set()
    for root in preferred:
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            if path.name in GENERATED_NAMES:
                continue
            if "Analisis" in path.parts or "Analysis" in path.parts:
                continue
            rp = str(path.resolve())
            if rp in seen:
                continue
            seen.add(rp)
            yield path

def tool_for_source(path: Path, manifest: dict) -> str | None:
    # Intenta aprovechar el historial del manifiesto sin depender de una estructura concreta.
    name = path.name
    for key in ("executions", "runs", "history"):
        rows = manifest.get(key)
        if not isinstance(rows, list):
            continue
        for row in reversed(rows):
            if not isinstance(row, dict):
                continue
            haystack = " ".join(str(row.get(k) or "") for k in ("output","file","path","export","result"))
            if name and name in haystack:
                return str(row.get("tool") or row.get("name") or "") or None
    return None

def correlate(case_folder: Path, manifest: dict):
    entities = {}
    relations = []
    files_scanned = 0
    files_text = 0

    for path in candidate_files(case_folder):
        files_scanned += 1
        text = read_text(path)
        if text is None:
            continue
        files_text += 1
        rel_path = str(path.relative_to(case_folder))
        skind = source_kind(path, case_folder)
        tool = tool_for_source(path, manifest)
        extracted = extract_entities(text)

        for (kind, value), raw_forms in extracted.items():
            eid = entity_key(kind, value)
            row = entities.setdefault(eid, {
                "id": eid,
                "type": kind,
                "value": value,
                "occurrences": 0,
                "sources": [],
            })
            row["occurrences"] += 1
            if rel_path not in row["sources"]:
                row["sources"].append(rel_path)
            relations.append({
                "entity_id": eid,
                "entity_type": kind,
                "entity_value": value,
                "source": rel_path,
                "source_kind": skind,
                "tool": tool or "",
            })

    # Una relación entidad-fuente no necesita repetirse varias veces.
    dedup = {}
    for r in relations:
        key = (r["entity_id"], r["source"])
        dedup[key] = r
    relations = sorted(dedup.values(), key=lambda x: (x["entity_type"], x["entity_value"], x["source"]))

    entity_rows = sorted(entities.values(), key=lambda x: (x["type"], x["value"]))
    for e in entity_rows:
        e["sources"].sort()
        e["source_count"] = len(e["sources"])
    return {
        "files_scanned": files_scanned,
        "text_files_scanned": files_text,
        "entities": entity_rows,
        "relations": relations,
    }

def write_json(out_dir: Path, payload: dict):
    (out_dir / "correlation.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

def write_csvs(out_dir: Path, entities: list[dict], relations: list[dict]):
    with (out_dir / "entities.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id","type","value","occurrences","source_count","sources"])
        for e in entities:
            w.writerow([e["id"],e["type"],e["value"],e["occurrences"],e["source_count"],"; ".join(e["sources"])])
    with (out_dir / "relations.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["entity_id","entity_type","entity_value","source","source_kind","tool"])
        for r in relations:
            w.writerow([r["entity_id"],r["entity_type"],r["entity_value"],r["source"],r["source_kind"],r["tool"]])

def graphml_safe(value) -> str:
    return "" if value is None else str(value)

def write_graphml(out_dir: Path, entities: list[dict], relations: list[dict]):
    ns = "http://graphml.graphdrawing.org/xmlns"
    ET.register_namespace("", ns)
    root = ET.Element(f"{{{ns}}}graphml")
    keys = [
        ("d0","node","type"), ("d1","node","value"), ("d2","node","kind"),
        ("d3","edge","relation"), ("d4","node","path"), ("d5","node","tool"),
    ]
    for kid, target, name in keys:
        ET.SubElement(root, f"{{{ns}}}key", id=kid, **{"for":target, "attr.name":name, "attr.type":"string"})
    graph = ET.SubElement(root, f"{{{ns}}}graph", id="MobPsyCorrelation", edgedefault="undirected")

    for e in entities:
        node = ET.SubElement(graph, f"{{{ns}}}node", id="entity_" + e["id"])
        for kid, val in (("d0",e["type"]),("d1",e["value"]),("d2","entity")):
            ET.SubElement(node, f"{{{ns}}}data", key=kid).text = graphml_safe(val)

    source_ids = {}
    for r in relations:
        src = r["source"]
        sid = source_ids.setdefault(src, "source_" + hashlib.sha256(src.encode()).hexdigest()[:20])
    for src, sid in sorted(source_ids.items()):
        sample = next((r for r in relations if r["source"] == src), None) or {}
        node = ET.SubElement(graph, f"{{{ns}}}node", id=sid)
        for kid, val in (("d0","source"),("d1",Path(src).name),("d2",sample.get("source_kind","")),("d4",src),("d5",sample.get("tool",""))):
            ET.SubElement(node, f"{{{ns}}}data", key=kid).text = graphml_safe(val)

    for i, r in enumerate(relations, 1):
        edge = ET.SubElement(graph, f"{{{ns}}}edge", id=f"e{i}", source="entity_"+r["entity_id"], target=source_ids[r["source"]])
        ET.SubElement(edge, f"{{{ns}}}data", key="d3").text = "appears_in"

    tree = ET.ElementTree(root)
    tree.write(out_dir / "correlation.graphml", encoding="utf-8", xml_declaration=True)

def write_report(out_dir: Path, case_folder: Path, manifest: dict, result: dict):
    by_type = defaultdict(int)
    repeated = []
    for e in result["entities"]:
        by_type[e["type"]] += 1
        if e["source_count"] > 1:
            repeated.append(e)
    repeated.sort(key=lambda e: (-e["source_count"], e["type"], e["value"]))

    lines = [
        "# MobPsy Correlator",
        "",
        f"- **Generado:** {now_iso()}",
        f"- **Caso:** {manifest.get('case_id') or manifest.get('id') or case_folder.name}",
        f"- **Título:** {manifest.get('title') or 'Sin título'}",
        f"- **Archivos revisados:** {result['files_scanned']}",
        f"- **Archivos de texto analizados:** {result['text_files_scanned']}",
        f"- **Entidades únicas:** {len(result['entities'])}",
        f"- **Relaciones entidad-fuente:** {len(result['relations'])}",
        "",
        "## Entidades por tipo",
        "",
    ]
    if by_type:
        for kind, count in sorted(by_type.items()):
            lines.append(f"- **{kind}:** {count}")
    else:
        lines.append("- No se detectaron entidades.")

    lines += ["", "## Coincidencias entre fuentes", ""]
    if repeated:
        for e in repeated[:200]:
            lines.append(f"- `{e['value']}` ({e['type']}) aparece en **{e['source_count']}** fuentes: " + ", ".join(e["sources"]))
    else:
        lines.append("No se detectaron entidades presentes en más de una fuente.")

    lines += [
        "",
        "## Interpretación",
        "",
        "Una coincidencia indica que una misma entidad fue observada en varias fuentes o archivos. "
        "No constituye por sí sola una atribución ni confirma identidad, propiedad o relación causal.",
        "",
        "## Archivos generados",
        "",
        "- `correlation.json`",
        "- `entities.csv`",
        "- `relations.csv`",
        "- `correlation.graphml`",
        "- `correlation_report.md`",
        "",
    ]
    (out_dir / "correlation_report.md").write_text("\n".join(lines), encoding="utf-8")


def write_html_report(out_dir: Path, case_folder: Path, manifest: dict, result: dict):
    by_type = defaultdict(int)
    repeated = []
    for entity in result["entities"]:
        by_type[entity["type"]] += 1
        if entity["source_count"] > 1:
            repeated.append(entity)
    repeated.sort(key=lambda e: (-e["source_count"], -e["occurrences"], e["type"], e["value"]))

    case_id = manifest.get("case_id") or manifest.get("id") or case_folder.name
    title = manifest.get("title") or "Sin título"

    type_rows = "".join(
        f"<tr><td>{html.escape(str(kind))}</td><td>{count}</td></tr>"
        for kind, count in sorted(by_type.items())
    ) or '<tr><td colspan="2">No se detectaron entidades.</td></tr>'

    repeated_rows = "".join(
        "<tr>"
        f"<td>{html.escape(str(e['type']))}</td>"
        f"<td><code>{html.escape(str(e['value']))}</code></td>"
        f"<td>{e['source_count']}</td>"
        f"<td>{html.escape(', '.join(e['sources']))}</td>"
        "</tr>"
        for e in repeated[:300]
    ) or '<tr><td colspan="4">No se detectaron coincidencias entre fuentes.</td></tr>'

    document = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<title>MobPsy Correlator - {html.escape(str(case_id))}</title>
<style>
body{{font-family:system-ui,-apple-system,sans-serif;background:#0e141d;color:#e8edf5;margin:0;padding:28px}}
main{{max-width:1200px;margin:auto}} h1,h2{{color:#fff}}
.grid{{display:grid;grid-template-columns:repeat(4,minmax(140px,1fr));gap:12px;margin:18px 0}}
.card{{background:#151d29;border:1px solid #263142;border-radius:12px;padding:16px}}
.big{{font-size:28px;font-weight:800;color:#8a7cff}}
table{{width:100%;border-collapse:collapse;background:#111923;border-radius:10px;overflow:hidden}}
th,td{{padding:10px;border-bottom:1px solid #263142;text-align:left;vertical-align:top}}
th{{background:#182231}} code{{color:#d9d4ff}}
.note{{padding:14px;background:#151d29;border-left:4px solid #6d5dfc;border-radius:8px}}
a{{color:#a89eff}}
</style></head><body><main>
<h1>MobPsy Correlator</h1>
<p><strong>Caso:</strong> {html.escape(str(case_id))} · {html.escape(str(title))}</p>
<div class="grid">
<div class="card"><div class="big">{result['files_scanned']}</div>archivos revisados</div>
<div class="card"><div class="big">{len(result['entities'])}</div>entidades únicas</div>
<div class="card"><div class="big">{len(result['relations'])}</div>relaciones</div>
<div class="card"><div class="big">{len(repeated)}</div>coincidencias</div>
</div>
<h2>Entidades por tipo</h2>
<table><thead><tr><th>Tipo</th><th>Total</th></tr></thead><tbody>{type_rows}</tbody></table>
<h2>Coincidencias entre fuentes</h2>
<table><thead><tr><th>Tipo</th><th>Entidad</th><th>Fuentes</th><th>Localizaciones</th></tr></thead>
<tbody>{repeated_rows}</tbody></table>
<h2>Interpretación</h2>
<p class="note">Una coincidencia significa que la misma entidad aparece en varias fuentes. No constituye por sí sola una atribución, identidad confirmada ni relación causal.</p>
<h2>Archivos relacionados</h2>
<ul>
<li><a href="correlation_graph.svg">Grafo visual SVG</a></li>
<li><a href="entities.csv">Entidades CSV</a></li>
<li><a href="relations.csv">Relaciones CSV</a></li>
<li><a href="correlation.json">Datos JSON</a></li>
<li><a href="correlation.graphml">GraphML</a></li>
</ul></main></body></html>"""
    (out_dir / "correlation_report.html").write_text(document, encoding="utf-8")


def dot_escape(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\\n", " ")


def write_visual_graph(out_dir: Path, entities: list[dict], relations: list[dict]):
    selected = [e for e in entities if e.get("source_count", 0) > 1]
    selected.sort(key=lambda e: (-e.get("source_count", 0), -e.get("occurrences", 0), e["value"]))
    if not selected:
        selected = sorted(
            entities,
            key=lambda e: (-e.get("occurrences", 0), e["value"]),
        )[:40]
    else:
        selected = selected[:80]

    ids = {e["id"] for e in selected}
    selected_relations = [r for r in relations if r["entity_id"] in ids]
    sources = sorted({r["source"] for r in selected_relations})

    lines = [
        "graph MobPsyCorrelation {",
        '  graph [bgcolor="#0e141d", overlap=false, splines=true, pad=0.4];',
        '  node [fontname="DejaVu Sans", color="#6d5dfc", fontcolor="#f3f5fa"];',
        '  edge [color="#65738a", penwidth=1.2];',
    ]

    for entity in selected:
        label = f"{entity['type']}\\n{entity['value']}"
        lines.append(
            f'  "e_{entity["id"]}" [label="{dot_escape(label)}", '
            'shape=ellipse, style="filled", fillcolor="#332b70"];'
        )

    source_ids = {}
    for source in sources:
        sid = hashlib.sha256(source.encode("utf-8")).hexdigest()[:20]
        source_ids[source] = sid
        lines.append(
            f'  "s_{sid}" [label="{dot_escape(Path(source).name)}", '
            'shape=box, style="rounded,filled", fillcolor="#1b2735", color="#3c536e"];'
        )

    for relation in selected_relations:
        lines.append(
            f'  "e_{relation["entity_id"]}" -- "s_{source_ids[relation["source"]]}";'
        )

    lines.append("}")
    dot_path = out_dir / "correlation_graph.dot"
    svg_path = out_dir / "correlation_graph.svg"
    dot_path.write_text("\\n".join(lines) + "\\n", encoding="utf-8")

    try:
        subprocess.run(
            ["dot", "-Tsvg", str(dot_path), "-o", str(svg_path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )
    except Exception as exc:
        (out_dir / "graph_error.txt").write_text(str(exc) + "\\n", encoding="utf-8")

def run_case(case_folder: Path, manifest: dict, quiet: bool = False):
    result = correlate(case_folder, manifest)
    out_dir = case_folder / "Analisis"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "mobpsy-correlation-1",
        "generated_at": now_iso(),
        "case_id": manifest.get("case_id") or manifest.get("id") or case_folder.name,
        "case_path": str(case_folder),
        "files_scanned": result["files_scanned"],
        "text_files_scanned": result["text_files_scanned"],
        "entity_count": len(result["entities"]),
        "relation_count": len(result["relations"]),
        "entities": result["entities"],
        "relations": result["relations"],
    }
    write_json(out_dir, payload)
    write_csvs(out_dir, result["entities"], result["relations"])
    write_graphml(out_dir, result["entities"], result["relations"])
    write_visual_graph(out_dir, result["entities"], result["relations"])
    write_report(out_dir, case_folder, manifest, result)
    write_html_report(out_dir, case_folder, manifest, result)

    if not quiet:
        repeated = sum(1 for e in result["entities"] if e["source_count"] > 1)
        print("MobPsy Correlator")
        print(f"Caso: {payload['case_id']}")
        print(f"Archivos revisados: {result['files_scanned']}")
        print(f"Entidades únicas: {len(result['entities'])}")
        print(f"Relaciones: {len(result['relations'])}")
        print(f"Entidades repetidas entre fuentes: {repeated}")
        print(f"Resultados: {out_dir}")
    return payload

def status_cmd():
    active = active_case_id()
    count = sum(1 for _ in iter_cases() or [])
    print(f"MobPsy Correlator {VERSION}: OK")
    print(f"Casos disponibles: {count}")
    print(f"Caso activo: {active or 'ninguno'}")
    return 0

def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="mobpsy-correlate",
        description=(
            "Correlaciona entidades encontradas en Evidencias y Exportaciones "
            "del caso activo de MobPsy."
        ),
        epilog=(
            "Sin argumentos analiza el caso activo. "
            "Genera correlation.json, entities.csv, relations.csv, "
            "correlation.graphml y correlation_report.md en Analisis/."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    parser.add_argument("--case-id", "--case", dest="case_id", help="ID del caso que se analizará.")
    parser.add_argument("--case-path", help="Ruta directa a una carpeta de caso.")
    parser.add_argument("--quiet", action="store_true", help="Reduce la salida por terminal.")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("status", help="Comprueba el backend sin requerir un caso activo.")
    sub.add_parser("run", help="Ejecuta la correlación (equivale a no indicar subcomando).")

    args = parser.parse_args(argv)
    if args.command == "status":
        return status_cmd()

    try:
        folder, manifest = find_case(args.case_id, args.case_path)
        run_case(folder, manifest, quiet=args.quiet)
        return 0
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nOperación cancelada.", file=sys.stderr)
        return 130

if __name__ == "__main__":
    raise SystemExit(main())
