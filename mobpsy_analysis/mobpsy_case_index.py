#!/usr/bin/env python3
from __future__ import annotations
import hashlib, html, json, re, subprocess, zipfile
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

TEXT_EXTENSIONS={".txt",".md",".log",".json",".csv",".tsv",".xml",".html",".htm",".yaml",".yml",".ini",".conf",".cfg",".py",".sh",".ps1",".bat"}
IMAGE_EXTENSIONS={".png",".jpg",".jpeg",".webp",".bmp",".tif",".tiff"}
SKIP_DIRS={"Informes",".mobpsy_ai"}
MAX_EXTRACT_CHARS=800000
CHUNK_SIZE=1800
CHUNK_OVERLAP=250

def sha256_file(path):
    h=hashlib.sha256()
    with path.open("rb") as fh:
        for b in iter(lambda:fh.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def clean_text(v):
    v=v.replace("\x00"," ")
    v=re.sub(r"\r\n?","\n",v)
    v=re.sub(r"[ \t]+\n","\n",v)
    v=re.sub(r"\n{4,}","\n\n\n",v)
    return v.strip()

def strip_xml(raw):
    try:
        root=ET.fromstring(raw); parts=[]
        for n in root.iter():
            if n.text and n.text.strip(): parts.append(n.text.strip())
        return clean_text("\n".join(parts))
    except Exception:
        s=raw.decode("utf-8",errors="replace")
        return clean_text(html.unescape(re.sub(r"<[^>]+>"," ",s)))

def cmd(args,timeout=45):
    try:
        cp=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,errors="replace",timeout=timeout,check=False)
        return clean_text(cp.stdout or "")
    except Exception: return ""

def extract(path):
    ext=path.suffix.lower()
    if ext in TEXT_EXTENSIONS:
        try:return clean_text(path.read_text(encoding="utf-8",errors="replace"))[:MAX_EXTRACT_CHARS],"texto"
        except Exception:return "","texto-error"
    if ext==".pdf":
        t=cmd(["pdftotext","-layout",str(path),"-"],60)
        if t:return t[:MAX_EXTRACT_CHARS],"pdftotext"
        try:
            import PyPDF2
            with path.open("rb") as f:
                t="\n".join((p.extract_text() or "") for p in PyPDF2.PdfReader(f).pages)
            return clean_text(t)[:MAX_EXTRACT_CHARS],"PyPDF2"
        except Exception:return "","pdf-sin-texto"
    if ext in {".docx",".pptx",".odt",".ods",".odp"}:
        try:
            with zipfile.ZipFile(path) as z:
                names=z.namelist()
                if ext==".docx": wanted=[n for n in names if n=="word/document.xml" or n.startswith("word/header") or n.startswith("word/footer")]
                elif ext==".pptx": wanted=sorted(n for n in names if n.startswith("ppt/slides/slide") and n.endswith(".xml"))
                else:wanted=["content.xml"] if "content.xml" in names else []
                return clean_text("\n\n".join(strip_xml(z.read(n)) for n in wanted))[:MAX_EXTRACT_CHARS],"office-xml"
        except Exception:return "","office-error"
    if ext==".xlsx":
        try:
            import openpyxl
            wb=openpyxl.load_workbook(path,read_only=True,data_only=True); rows=[]
            for ws in wb.worksheets:
                rows.append("HOJA: "+ws.title)
                for row in ws.iter_rows(values_only=True):
                    vals=["" if v is None else str(v) for v in row]
                    if any(v.strip() for v in vals): rows.append("\t".join(vals))
                    if sum(map(len,rows))>MAX_EXTRACT_CHARS: break
            return clean_text("\n".join(rows))[:MAX_EXTRACT_CHARS],"openpyxl"
        except Exception:return "","xlsx-error"
    if ext==".doc":
        t=cmd(["antiword",str(path)],45); return t[:MAX_EXTRACT_CHARS],("antiword" if t else "doc-sin-texto")
    if ext==".rtf":
        t=cmd(["unrtf","--text",str(path)],45); return t[:MAX_EXTRACT_CHARS],("unrtf" if t else "rtf-sin-texto")
    if ext in IMAGE_EXTENSIONS:
        for lang in ("spa+eng","eng"):
            t=cmd(["tesseract",str(path),"stdout","-l",lang,"--psm","6"],90)
            if t:return t[:MAX_EXTRACT_CHARS],"tesseract-"+lang
        return "","imagen-sin-ocr"
    t=cmd(["strings","-n","5",str(path)],30)
    return t[:100000],("strings" if t else "binario")

def make_chunks(text):
    if not text:return []
    out=[]; start=0
    while start<len(text):
        end=min(len(text),start+CHUNK_SIZE); c=text[start:end].strip()
        if c:out.append(c)
        if end>=len(text):break
        start=max(start+1,end-CHUNK_OVERLAP)
    return out

def tokenize(v): return re.findall(r"(?u)[a-záéíóúüñ0-9_.@:/+-]{2,}",str(v).casefold())

def excerpt(text,pos,width=300):
    s=max(0,pos-width//2); e=min(len(text),pos+width//2)
    v=re.sub(r"\s+"," ",text[s:e].replace("\n"," ")).strip()
    return ("…" if s else "")+v+("…" if e<len(text) else "")

class CaseIndex:
    def __init__(self,case_dir,manifest):
        self.case_dir=Path(case_dir); self.manifest=manifest
        self.cache_path=self.case_dir/"Analisis"/".mobpsy_ai_index.json"; self.data=None
    def _skip(self,p):
        rel=p.relative_to(self.case_dir)
        if any(x in SKIP_DIRS for x in rel.parts[:-1]):return True
        return p.name.startswith("ia_pregunta_") or p.name.startswith("Informe_") or p.name==".mobpsy_ai_index.json"
    def files(self): return [p for p in sorted(self.case_dir.rglob("*"),key=lambda x:str(x).casefold()) if p.is_file() and not self._skip(p)]
    def sig(self,p):
        st=p.stat(); return {"size":st.st_size,"mtime_ns":st.st_mtime_ns}
    def build(self,force=False):
        if not force and self.cache_path.is_file():
            try:
                old=json.loads(self.cache_path.read_text(encoding="utf-8")); sigs=old.get("signatures") or {}; fs=self.files()
                if len(sigs)==len(fs) and all(sigs.get(str(p.relative_to(self.case_dir)))==self.sig(p) for p in fs):
                    self.data=old; return old
            except Exception:pass
        rows=[]; sigs={}
        for i,p in enumerate(self.files(),1):
            rel=str(p.relative_to(self.case_dir)); sigs[rel]=self.sig(p); text,method=extract(p)
            try:sha=sha256_file(p)
            except Exception:sha=""
            rows.append({"source_id":f"F{i:03d}","relative_path":rel,"name":p.name,"size_bytes":p.stat().st_size,"sha256":sha,"extractor":method,"text":text,"chunks":make_chunks(text)})
        payload={"schema":2,"case_id":self.manifest.get("case_id"),"title":self.manifest.get("title"),"signatures":sigs,"files":rows}
        self.cache_path.parent.mkdir(parents=True,exist_ok=True)
        self.cache_path.write_text(json.dumps(payload,ensure_ascii=False)+"\n",encoding="utf-8"); self.data=payload; return payload
    def stats(self):
        d=self.build(); return {"files":len(d["files"]),"with_text":sum(bool(x.get("text")) for x in d["files"]),"chars":sum(len(x.get("text") or "") for x in d["files"]),"extractors":dict(Counter(x.get("extractor") for x in d["files"]))}
    def exact_search(self,needle):
        d=self.build(); f=str(needle).casefold(); out=[]
        for row in d["files"]:
            text=row.get("text") or ""; low=text.casefold(); count=low.count(f); ph=f in row["relative_path"].casefold()
            if not count and not ph:continue
            ex=[]; pos=0
            for _ in range(min(count,8)):
                hit=low.find(f,pos)
                if hit<0:break
                ex.append(excerpt(text,hit)); pos=hit+max(1,len(f))
            out.append({"source_id":row["source_id"],"relative_path":row["relative_path"],"count":count,"path_hit":ph,"excerpts":ex})
        return out
    def retrieve(self,q,top_k=12,max_chars=10000):
        d=self.build(); qtokens=tokenize(q); qset=set(qtokens); scored=[]
        for row in d["files"]:
            for n,c in enumerate(row.get("chunks") or []):
                cs=set(tokenize(c)); overlap=len(qset&cs); score=overlap*3
                for t in qset:
                    if t in row["relative_path"].casefold():score+=2
                if score>0:scored.append((score,row,n,c))
        scored.sort(key=lambda x:(-x[0],x[1]["relative_path"],x[2]))
        blocks=[]; used=0; per=Counter()
        for score,row,n,c in scored:
            if len(blocks)>=top_k or used>=max_chars:break
            if per[row["source_id"]]>=3:continue
            b=f"[{row['source_id']}] {row['relative_path']} · fragmento {n+1}\n{c}"
            b=b[:max_chars-used]; blocks.append(b); used+=len(b); per[row["source_id"]]+=1
        return "\n\n".join(blocks)
    def catalog(self):
        d=self.build(); return [{"source_id":x["source_id"],"relative_path":x["relative_path"],"extractor":x["extractor"],"chars":len(x.get("text") or ""),"sha256":x.get("sha256") or ""} for x in d["files"]]
    def indicators(self,limit=60):
        d=self.build(); patterns={"email":re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",re.I),"url":re.compile(r"https?://[^\s<>'\"\]\)]+",re.I),"ipv4":re.compile(r"\b(?:25[0-5]|2[0-4]\d|1?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}\b"),"domain":re.compile(r"\b(?:[a-z0-9-]+\.)+[a-z]{2,}\b",re.I)}
        src={k:defaultdict(set) for k in patterns}; cnt={k:Counter() for k in patterns}
        for row in d["files"]:
            text=row.get("text") or ""
            for kind,rx in patterns.items():
                for m in rx.finditer(text):
                    v=m.group(0).rstrip(".,;:").casefold();cnt[kind][v]+=1;src[kind][v].add(row["source_id"])
        rows=[]
        for kind in patterns:
            for v,c in cnt[kind].items():rows.append({"type":kind,"value":v,"occurrences":c,"sources":sorted(src[kind][v]),"source_count":len(src[kind][v])})
        rows.sort(key=lambda x:(-x["source_count"],-x["occurrences"],x["type"],x["value"]))
        return rows[:limit]
    def dossier(self,max_chars=22000):
        d=self.build(); man={k:self.manifest.get(k) for k in ("case_id","title","subject","notes","status","created_at","updated_at")}
        parts=["[MANIFEST]\n"+json.dumps(man,ensure_ascii=False,indent=2),"[INDICADORES]\n"+json.dumps(self.indicators(),ensure_ascii=False,indent=2)]
        textual=[x for x in d["files"] if x.get("text")]; budget=max_chars-sum(map(len,parts))
        per=max(180,min(700,budget//max(1,len(textual))))
        for row in textual:
            parts.append(f"[{row['source_id']}] {row['relative_path']}\n{row['text'][:per]}")
        return "\n\n".join(parts)[:max_chars]
