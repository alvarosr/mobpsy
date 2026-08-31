#!/usr/bin/env python3
from __future__ import annotations
import json, re
from collections import Counter, defaultdict
from pathlib import Path

EMAIL_RX=re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",re.I)
URL_RX=re.compile(r"https?://[^\s<>'\"\]\)]+",re.I)
IP_RX=re.compile(r"\b(?:25[0-5]|2[0-4]\d|1?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}\b")
DOMAIN_RX=re.compile(r"\b(?:[a-z0-9-]+\.)+[a-z]{2,}\b",re.I)

def md(v): return str(v or "").replace("|","\\|").replace("\n"," ").strip()

def classify_source(path):
    low=path.casefold().replace("\\","/")
    if low.startswith("evidencias/") or "/evidencias/" in low:return "Evidencia"
    if low.startswith("exportaciones/") or "/exportaciones/" in low:return "Exportación"
    if "correl" in low or low.startswith("analisis/"):return "Análisis / correlación"
    if low.endswith("case.json"):return "Manifiesto"
    return "Otro"

def tool_from_path(path):
    name=Path(path).stem.casefold()
    tools=["holehe","sherlock","maigret","phoneinfoga","social_analyzer","theharvester","subfinder","dnsrecon","whatweb","wafw00f","photon","crosslinked","protosint","zehef","clatscope","instaloader","spiderfoot","reconng","sn0int","exiftool","mediainfo"]
    for t in tools:
        if t in name:return t.replace("_"," ").title()
    return "Manual / no identificado"

def indicators(text):
    out=[]
    for kind,rx in (("Correo",EMAIL_RX),("URL",URL_RX),("IPv4",IP_RX),("Dominio",DOMAIN_RX)):
        for m in rx.finditer(text or ""):
            v=m.group(0).rstrip(".,;:)]}").casefold()
            if kind=="Dominio" and ("@" in v or v.startswith("http")):continue
            if any(x in v for x in ("localhost","127.0.0.1","github.com/alvarosr/mobpsy")):continue
            out.append((kind,v))
    return out

def meaningful_lines(text,limit=8):
    rows=[];seen=set()
    for raw in (text or "").splitlines():
        line=re.sub(r"\s+"," ",raw).strip(" \t-*#|")
        if len(line)<8 or len(line)>260:continue
        low=line.casefold()
        if low.startswith(("usage:","options:","traceback","file \"","warning:","error:","made by","requirement already satisfied")):continue
        if any(x in low for x in ("vagrant ssh","pip install","http://127.0.0.1","ollama")):continue
        interesting=bool(EMAIL_RX.search(line) or URL_RX.search(line) or IP_RX.search(line) or DOMAIN_RX.search(line) or any(w in low for w in ("found","encontr","exists","exist","username","profile","account","cuenta","domain","phone","location","metadata","true","false")))
        if not interesting:continue
        if low in seen:continue
        seen.add(low);rows.append(line)
        if len(rows)>=limit:break
    return rows

def consolidate(index,manifest):
    data=index.build();sources=[];srcmap=defaultdict(set);counts=Counter()
    for row in data.get("files",[]):
        sid=row["source_id"];path=row["relative_path"];text=row.get("text") or ""
        facts=meaningful_lines(text)
        sources.append({"id":sid,"path":path,"category":classify_source(path),"tool":tool_from_path(path),"extractor":row.get("extractor") or "","sha256":row.get("sha256") or "","facts":facts})
        for kind,val in indicators(text):
            srcmap[(kind,val)].add(sid);counts[(kind,val)]+=1
    inds=[{"kind":k,"value":v,"sources":sorted(srcmap[(k,v)]),"source_count":len(srcmap[(k,v)]),"occurrences":counts[(k,v)]} for (k,v) in srcmap]
    inds.sort(key=lambda x:(-x["source_count"],-x["occurrences"],x["kind"],x["value"]))
    chrono=[]
    for rec in manifest.get("evidence",[]) or []:
        chrono.append({"time":rec.get("added_at") or "","type":"Evidencia" if rec.get("kind")=="evidence" else "Exportación","tool":rec.get("tool") or "manual","item":rec.get("stored_name") or rec.get("stored_path") or ""})
    for rec in manifest.get("executions",[]) or []:
        chrono.append({"time":rec.get("timestamp") or "","type":"Ejecución","tool":rec.get("tool") or "","item":rec.get("target") or ""})
    chrono.sort(key=lambda x:x["time"])
    return {"case":{"id":manifest.get("case_id"),"title":manifest.get("title"),"subject":manifest.get("subject"),"status":manifest.get("status")},"sources":sources,"indicators":inds,"corroborated":[x for x in inds if x["source_count"]>=2],"isolated":[x for x in inds if x["source_count"]==1],"chronology":chrono}

def narrative_prompt(cons):
    src=[]
    for s in cons["sources"]:
        if s["facts"]:
            src.append({"id":s["id"],"category":s["category"],"tool":s["tool"],"file":s["path"],"observations":s["facts"][:5]})
        if len(src)>=20:break
    payload={"case":cons["case"],"corroborated_findings":cons["corroborated"][:50],"single_source_findings":cons["isolated"][:50],"source_observations":src,"chronology":cons["chronology"][-40:]}
    rules = '''\n\nRedacta SOLO estas tres secciones:\n## Resumen ejecutivo\n## Análisis e interpretación\n## Conclusiones\n\nReglas:\n- no repitas datos;\n- cada hecho cita [F###];\n- usa la correlación como corroboración, no como otra copia;\n- distingue hecho/inferencia/hipótesis;\n- no conviertas comandos, targets u objetivos de herramientas en hallazgos;\n- no inventes nada;\n- explica qué significan conjuntamente las pruebas.\n'''
    return "DATOS CONSOLIDADOS:\n"+json.dumps(payload,ensure_ascii=False,indent=2)+rules

def fallback(cons):
    c=cons["case"];cor=cons["corroborated"]
    top="; ".join(f"`{x['value']}` ({', '.join(x['sources'])})" for x in cor[:5]) if cor else "No hay indicadores repetidos en dos o más fuentes."
    return f"## Resumen ejecutivo\n\nEl expediente **{c.get('title') or c.get('id') or 'sin título'}** contiene {len(cons['sources'])} archivos analizados. Objetivo: **{c.get('subject') or 'no especificado'}**.\n\nPrincipales elementos corroborados: {top}\n\n## Análisis e interpretación\n\nLa repetición de un dato en varias fuentes supone corroboración documental, pero no demuestra por sí sola identidad, propiedad o atribución. Los elementos presentes en una sola fuente se tratan como indicios no corroborados.\n\n## Conclusiones\n\nSolo deben considerarse defendibles los hechos observables en las fuentes y su nivel de corroboración. Cualquier atribución requiere evidencia independiente adicional."

def evidence_section(cons):
    lines=["## Fuentes y pruebas relevantes","","Cada evidencia/exportación se resume una sola vez a partir de su contenido real.",""]
    n=0
    for s in cons["sources"]:
        if not s["facts"]:continue
        n+=1;lines += [f"### [{s['id']}] {s['category']} · {s['tool']}",f"**Archivo:** `{s['path']}`",""]
        lines += [f"- {x}" for x in s["facts"][:8]];lines.append("")
    if not n:lines.append("_No se pudieron extraer observaciones textuales útiles._")
    return "\n".join(lines)

def findings_section(cons):
    lines=["## Hallazgos consolidados y correlación","","Cada dato aparece una sola vez. **Fuentes** muestra todos los archivos que lo respaldan.","","| Nivel | Tipo | Dato | Fuentes | Apariciones |","|---|---|---|---|---:|"]
    for x in cons["indicators"]:
        lvl="Corroborado" if x["source_count"]>=2 else "Una sola fuente"
        lines.append(f"| {lvl} | {x['kind']} | `{md(x['value'])}` | {', '.join(x['sources'])} | {x['occurrences']} |")
    if not cons["indicators"]:lines.append("| — | — | Sin indicadores normalizados | — | — |")
    return "\n".join(lines)

def methodology(cons):
    return f"## Alcance y metodología\n\nSe analizaron **{len(cons['sources'])} archivos** del caso activo. El proceso separa prueba observada, corroboración entre fuentes y análisis. Los datos repetidos se normalizan y aparecen una sola vez con todas las fuentes que los apoyan. Correlator se utiliza para reforzar relaciones ya observadas, no para duplicar resultados.\n"

def chronology(cons):
    lines=["## Cronología del expediente","","| Fecha | Tipo | Herramienta | Elemento |","|---|---|---|---|"]
    for r in cons["chronology"]:lines.append(f"| {md(r['time'])} | {md(r['type'])} | {md(r['tool'])} | {md(r['item'])} |")
    if not cons["chronology"]:lines.append("| — | — | — | Sin eventos registrados |")
    return "\n".join(lines)

def limitations(cons):
    return f"## Limitaciones\n\n- Un dato repetido implica corroboración documental, no atribución.\n- Hay **{len(cons['isolated'])} indicadores** presentes en una sola fuente.\n- La calidad del análisis depende de la calidad y alcance de las pruebas incorporadas.\n- La ausencia de resultados no demuestra inexistencia.\n"

def inventory(cons):
    lines=["## Inventario técnico","","| Fuente | Tipo | Herramienta | Archivo | SHA-256 |","|---|---|---|---|---|"]
    for s in cons["sources"]:lines.append(f"| {s['id']} | {s['category']} | {md(s['tool'])} | {md(s['path'])} | `{s['sha256']}` |")
    return "\n".join(lines)

def build_report(index,manifest,chat_func=None):
    cons=consolidate(index,manifest)
    try:
        narr=chat_func(narrative_prompt(cons)) if chat_func else fallback(cons)
        if not all(h in narr for h in ("## Resumen ejecutivo","## Análisis e interpretación","## Conclusiones")):narr=fallback(cons)
    except Exception:narr=fallback(cons)
    def sec(a,b=None):
        i=narr.find(a)
        if i<0:return ""
        j=narr.find(b,i+len(a)) if b else -1
        return narr[i:j].strip() if j>=0 else narr[i:].strip()
    parts=[sec("## Resumen ejecutivo","## Análisis e interpretación"),methodology(cons),evidence_section(cons),findings_section(cons),sec("## Análisis e interpretación","## Conclusiones"),chronology(cons),limitations(cons),sec("## Conclusiones"),inventory(cons)]
    return "\n\n".join(p for p in parts if p.strip()),cons
