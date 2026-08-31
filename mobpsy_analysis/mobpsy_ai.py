#!/usr/bin/env python3
from __future__ import annotations
import argparse, html, json, re, sys, urllib.error, urllib.request
from datetime import datetime
from pathlib import Path
from mobpsy_case_index import CaseIndex
from mobpsy_report_engine import build_report

CASES_DIR=Path.home()/"MobPsy"/"Casos"; ACTIVE_CASE_FILE=CASES_DIR/".active_case.json"
CONFIG_DIR=Path.home()/"MobPsy"/"Configuracion"; CONFIG_FILE=CONFIG_DIR/"ai.json"
INSTALL_DIR=Path("/opt/mobpsy/analysis"); KNOWLEDGE_FILE=INSTALL_DIR/"osint_knowledge.md"
DEFAULT={"provider":"ollama","endpoint":"http://127.0.0.1:11434","model":"mobpsy-osint:latest","timeout_seconds":300,"context_chars":10000}
REFS=[("Berkeley Protocol on Digital Open Source Investigations","OHCHR / UC Berkeley","https://www.ohchr.org/sites/default/files/2024-01/Berkeley-Protocol-Spanish_0.pdf"),("NIST SP 800-61 Rev. 3","NIST","https://csrc.nist.gov/pubs/sp/800/61/r3/final"),("Cybersecurity Advisories","CISA","https://www.cisa.gov/news-events/cybersecurity-advisories")]

def config():
    CONFIG_DIR.mkdir(parents=True,exist_ok=True)
    try:d=json.loads(CONFIG_FILE.read_text(encoding="utf-8")) if CONFIG_FILE.is_file() else {}
    except Exception:d={}
    r=dict(DEFAULT);r.update(d);r["model"]="mobpsy-osint:latest";r["context_chars"]=min(12000,max(8000,int(r.get("context_chars") or 10000)))
    CONFIG_FILE.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");return r
def active_case_id():
    try:return str(json.loads(ACTIVE_CASE_FILE.read_text(encoding="utf-8")).get("case_id") or "") or None
    except Exception:return None
def find_case(case_id=None):
    wanted=case_id or active_case_id()
    if not wanted:raise RuntimeError("No hay ningún caso activo.")
    for folder in CASES_DIR.iterdir() if CASES_DIR.is_dir() else []:
        m=folder/"case.json"
        if not m.is_file():continue
        try:d=json.loads(m.read_text(encoding="utf-8"))
        except Exception:continue
        if wanted in (str(d.get("case_id") or ""),str(d.get("id") or ""),folder.name):return folder,d
    raise RuntimeError(f"No se encuentra el caso {wanted}.")
def models(endpoint):
    req=urllib.request.Request(endpoint.rstrip("/")+"/api/tags",headers={"User-Agent":"MobPsy/1.0.0"})
    with urllib.request.urlopen(req,timeout=5) as r:d=json.loads(r.read().decode("utf-8",errors="replace"))
    return [str(x.get("name") or "") for x in d.get("models",[]) if x.get("name")]
def ai_status(cfg):
    try:installed=models(cfg["endpoint"])
    except Exception as e:return False,f"Ollama no está accesible: {e}."
    return (cfg["model"] in installed, f"IA OSINT lista. Modelo: {cfg['model']}." if cfg["model"] in installed else f"Falta el modelo {cfg['model']}.")
def knowledge():
    try:return KNOWLEDGE_FILE.read_text(encoding="utf-8")
    except Exception:return ""
def chat(cfg,system,user):
    payload={"model":cfg["model"],"messages":[{"role":"system","content":str(system)[:4500]},{"role":"user","content":str(user)[-14000:]}],"stream":False,"keep_alive":"10m","think":False,"options":{"temperature":0.1,"top_p":0.8,"num_ctx":4096,"num_predict":700,"repeat_penalty":1.08}}
    req=urllib.request.Request(cfg["endpoint"].rstrip("/")+"/api/chat",data=json.dumps(payload,ensure_ascii=False).encode("utf-8"),headers={"Content-Type":"application/json","User-Agent":"MobPsy/1.0.0"})
    try:
        with urllib.request.urlopen(req,timeout=int(cfg["timeout_seconds"])) as r:res=json.loads(r.read().decode("utf-8",errors="replace"))
    except urllib.error.HTTPError as e:
        body=e.read().decode("utf-8",errors="replace");raise RuntimeError(f"Ollama devolvió HTTP {e.code}: {body.strip() or e}") from e
    c=str(((res.get("message") or {}).get("content")) or "").strip()
    if not c:raise RuntimeError("Ollama respondió sin contenido.")
    return c
def quick(data,q):
    x=" ".join(str(q).lower().split())
    if any(p in x for p in ("como se llama el caso","cómo se llama el caso","nombre del caso")):return f"El caso se llama «{data.get('title') or 'Sin título'}» [MANIFEST]."
    if any(p in x for p in ("id del caso","identificador del caso")):return f"El identificador es {data.get('case_id') or 'no consta'} [MANIFEST]."
    return None
def exact_target(q):
    for p in (r"(?:aparece|sale|figura|contiene)\s+exactamente\s+[«\"']?(.+?)[»\"']?\s*$",r"(?:busca|buscar)\s+exactamente\s+[«\"']?(.+?)[»\"']?\s*$",r"(?:todas las fuentes|todos los archivos).*?(?:aparece|contiene)\s+[«\"']?(.+?)[»\"']?\s*$"):
        m=re.search(p,str(q),re.I)
        if m:return m.group(1).strip().strip(" .,:;")
    return None
def exact_answer(idx,target):
    rows=idx.exact_search(target);s=idx.stats()
    if not rows:return f"He buscado literalmente «{target}» en los {s['files']} archivos del caso activo ({s['with_text']} con contenido extraíble) y no aparece de forma exacta."
    lines=[f"He buscado literalmente «{target}» en todos los archivos del caso activo.",f"Aparece en **{len(rows)} archivo(s)**.",""]
    for r in rows:
        lines.append(f"- [{r['source_id']}] `{r['relative_path']}` — {r['count']} coincidencia(s)")
        for e in r["excerpts"][:3]:lines.append("  - "+e)
    lines+=["","Resultado de búsqueda literal sobre el expediente; no es una inferencia del modelo."]
    return "\n".join(lines)
def qa_system():
    return """Eres MobPsy OSINT Analyst. Usa exclusivamente FUENTES RECUPERADAS del expediente. No inventes. No conviertas objetivos, comandos ni nombres de herramientas en hallazgos. Cita toda afirmación factual con [F###] o [MANIFEST]. Responde exactamente a la pregunta. Si falta evidencia, dilo. Distingue hecho, inferencia e hipótesis. Una coincidencia no prueba identidad ni atribución."""
def qa_prompt(q,ctx):return f"PREGUNTA:\n{q}\n\nFUENTES RECUPERADAS:\n{ctx}\n\nResponde de forma concreta, factual y citada."
def report_prompt(d):
    return f"""GUÍA METODOLÓGICA:\n{knowledge()[:3500]}\n\nDOSSIER DE TODOS LOS ARCHIVOS:\n{d}\n\nRedacta SOLO:\n## Resumen ejecutivo\n## Alcance y metodología\n## Hallazgos clave\n## Correlaciones y relaciones relevantes\n## Cronología\n## Evaluación analítica y confianza\n## Vacíos y limitaciones\n## Próximos pasos OSINT recomendados\n## Conclusiones\n\nCada hecho debe citar [F###] o [MANIFEST]. No inventes ni conviertas comandos/objetivos de herramientas en hechos. Prioriza corroboración real entre fuentes."""
def md(v):return str(v or "").replace("|","\\|")
def appendix(idx,data):
    cat=idx.catalog();inds=idx.indicators()
    lines=["## Cobertura documental","",f"Se indexaron **{len(cat)} archivos** antes del informe.","","| Fuente | Archivo | Extracción | Caracteres | SHA-256 |","|---|---|---|---:|---|"]
    for r in cat:lines.append(f"| {r['source_id']} | {md(r['relative_path'])} | {r['extractor']} | {r['chars']} | `{r['sha256']}` |")
    lines+=["","## Indicadores observados automáticamente","","| Tipo | Valor | Fuentes | Apariciones |","|---|---|---|---:|"]
    for i in inds:lines.append(f"| {i['type']} | `{md(i['value'])}` | {', '.join(i['sources'])} | {i['occurrences']} |")
    return "\n".join(lines)
def render(mdtext,title):
    try:
        import markdown;body=markdown.markdown(mdtext,extensions=["tables","fenced_code","sane_lists"])
    except Exception:body="<pre>"+html.escape(mdtext)+"</pre>"
    return f"<!doctype html><html lang='es'><meta charset='utf-8'><title>{html.escape(title)}</title><style>body{{font-family:system-ui;background:#f4f6f8}}main{{max-width:1100px;margin:28px auto;background:white;padding:44px}}table{{width:100%;border-collapse:collapse}}th,td{{border:1px solid #ccc;padding:8px;text-align:left}}h2{{margin-top:32px}}</style><main>{body}</main></html>"
def report(cfg,folder,data):
    idx=CaseIndex(folder,data)
    idx.build()

    def analytical_narrative(prompt):
        return chat(
            cfg,
            qa_system() + "\nRedacta un informe profesional, sin repetir datos y sin inventar.",
            prompt,
        )

    body, consolidated = build_report(idx, data, analytical_narrative)
    now=datetime.now()
    header=(
        f"# MobPsy · Informe de análisis OSINT — {data.get('case_id')}\n\n"
        f"**Caso:** {data.get('title') or 'Sin título'}\n"
        f"**Objetivo:** {data.get('subject') or 'No especificado'}\n"
        f"**Estado:** {data.get('status') or 'No especificado'}\n"
        f"**Fecha del informe:** {now.isoformat(timespec='seconds')}\n"
        f"**Archivos analizados:** {len(consolidated['sources'])}\n\n"
    )
    full=header+body+"\n"
    d=folder/"Informes"; d.mkdir(exist_ok=True)
    base=f"Informe_Profesional_{data.get('case_id')}_{now.strftime('%Y%m%d_%H%M%S')}"
    mp=d/(base+".md"); hp=d/(base+".html")
    lm=d/f"Informe_{data.get('case_id')}.md"; lh=d/f"Informe_{data.get('case_id')}.html"
    mp.write_text(full,encoding="utf-8"); lm.write_text(full,encoding="utf-8")
    h=render(full,str(data.get("case_id")))
    hp.write_text(h,encoding="utf-8"); lh.write_text(h,encoding="utf-8")
    return mp,hp

def save(folder,q,a):
    d=folder/"Analisis";d.mkdir(exist_ok=True);p=d/f"ia_pregunta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md";p.write_text(f"# Pregunta\n\n**Pregunta:** {q}\n\n{a}\n",encoding="utf-8");return p
def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest="cmd");sub.add_parser("status");ix=sub.add_parser("index");ix.add_argument("case_id",nargs="?");ix.add_argument("--force",action="store_true");se=sub.add_parser("search");se.add_argument("text");se.add_argument("--case-id");a=sub.add_parser("ask");a.add_argument("question",nargs="?");a.add_argument("--case-id");r=sub.add_parser("report");r.add_argument("case_id",nargs="?");args=p.parse_args();cfg=config()
    try:
        if args.cmd=="status":
            ok,msg=ai_status(cfg);print(msg)
            try:
                f,d=find_case();s=CaseIndex(f,d).stats();print(f"Caso: {s['files']} archivos · {s['with_text']} con contenido · {s['chars']} caracteres extraídos.")
            except Exception:pass
            return 0 if ok else 1
        if args.cmd=="index":
            f,d=find_case(args.case_id);idx=CaseIndex(f,d);idx.build(force=args.force);print(json.dumps(idx.stats(),ensure_ascii=False,indent=2));return 0
        if args.cmd=="search":
            f,d=find_case(args.case_id);print(exact_answer(CaseIndex(f,d),args.text));return 0
        if args.cmd=="ask":
            ok,msg=ai_status(cfg)
            if not ok:raise RuntimeError(msg)
            f,d=find_case(args.case_id);q=(args.question or "").strip()
            if not q:raise RuntimeError("Escribe una pregunta.")
            ans=quick(d,q)
            if not ans:
                idx=CaseIndex(f,d);idx.build();target=exact_target(q)
                if target:ans=exact_answer(idx,target)
                else:
                    ctx=idx.retrieve(q,12,int(cfg["context_chars"]))
                    ans=chat(cfg,qa_system(),qa_prompt(q,ctx)) if ctx else "No he encontrado contenido suficiente del expediente relacionado con esa pregunta."
            print(ans);print(f"\nRespuesta guardada en: {save(f,q,ans)}",file=sys.stderr);return 0
        if args.cmd=="report":
            ok,msg=ai_status(cfg)
            if not ok:raise RuntimeError(msg)
            f,d=find_case(args.case_id);m,h=report(cfg,f,d);print(f"INFORME_MD={m}");print(f"INFORME_HTML={h}");return 0
        p.print_help();return 0
    except Exception as e:
        print(f"ERROR: {e}",file=sys.stderr);return 2
if __name__=="__main__":raise SystemExit(main())
