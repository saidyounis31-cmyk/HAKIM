from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import httpx

app = FastAPI(title="HAKIM API", version="2.1")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

EUROPEPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
SUPPORTED_LANGUAGES = {"ar", "he", "en", "fr", "de", "es"}

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "HAKIM"}

@app.get("/api/literature-search")
async def literature_search(query: str = Query(..., min_length=2), open_access: bool = False,
                            limit: int = Query(10, ge=5, le=20), lang: str = "en"):
    if lang not in SUPPORTED_LANGUAGES:
        raise HTTPException(400, "Unsupported language")
    expression = f"({query}) AND OPEN_ACCESS:Y" if open_access else query
    params = {"query": expression, "format": "json", "pageSize": limit, "sort": "CITED desc"}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(EUROPEPMC, params=params)
            response.raise_for_status()
            data = response.json()
    except Exception:
        raise HTTPException(502, "تعذر الاتصال بمؤشر Europe PMC حاليًا")

    records = []
    for item in data.get("resultList", {}).get("result", []):
        pmid = item.get("pmid")
        records.append({
            "title": item.get("title"), "authors": item.get("authorString"),
            "journal": item.get("journalTitle"), "year": item.get("pubYear"),
            "abstract": item.get("abstractText"), "doi": item.get("doi"),
            "pmid": pmid, "pmcid": item.get("pmcid"),
            "open_access": item.get("isOpenAccess") == "Y",
            "source_url": f"https://europepmc.org/article/MED/{pmid}" if pmid else None,
        })
    return {"query": query, "count": len(records), "language": lang, "records": records}

@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_PAGE

HTML_PAGE = r'''<!doctype html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HAKIM — البحث العلمي</title><style>
:root{--bg:#eef7f5;--card:#fff;--accent:#087f73;--text:#17312d}*{box-sizing:border-box}body{margin:0;font-family:Tahoma,Arial,sans-serif;background:var(--bg);color:var(--text)}header{background:var(--accent);color:white;padding:20px;text-align:center}main{max-width:980px;margin:auto;padding:24px}.controls{display:grid;grid-template-columns:1fr 120px 150px auto;gap:10px}input,select,button{padding:12px;border:1px solid #b9ccc8;border-radius:8px;font:inherit}button{background:var(--accent);color:white;cursor:pointer}.card{background:var(--card);border-radius:12px;padding:16px;margin-top:14px;box-shadow:0 3px 14px #1e4a4218}.meta{color:#5d7771;font-size:.9rem}.abstract{line-height:1.7}.notice{background:#fff7dc;border-right:4px solid #d59b00;padding:12px;margin-top:16px;border-radius:8px}a{color:#087f73}@media(max-width:760px){.controls{grid-template-columns:1fr}}
</style></head><body><header><h1>HAKIM حكيم</h1><p>البحث في الأدبيات العلمية المفتوحة</p></header><main>
<form id="search" class="controls"><input id="query" value="asthma randomized trial" required><select id="limit"><option>5</option><option selected>10</option><option>20</option></select><select id="lang"><option value="ar">العربية</option><option value="he">עברית</option><option value="en">English</option><option value="fr">Français</option><option value="de">Deutsch</option><option value="es">Español</option></select><button>بحث</button></form>
<label><input id="oa" type="checkbox"> الوصول المفتوح فقط</label><div class="notice">نموذج بحث وتعليم مهني؛ لا يقدم تشخيصًا أو وصفًا علاجيًا ولا يغني عن اختصاصي مرخص.</div><div id="status"></div><div id="results"></div></main>
<script>const form=document.querySelector('#search'),results=document.querySelector('#results'),statusEl=document.querySelector('#status');form.addEventListener('submit',async e=>{e.preventDefault();results.innerHTML='';statusEl.textContent='جارٍ البحث…';const p=new URLSearchParams({query:document.querySelector('#query').value,limit:document.querySelector('#limit').value,lang:document.querySelector('#lang').value,open_access:document.querySelector('#oa').checked});try{const r=await fetch('/api/literature-search?'+p),d=await r.json();if(!r.ok)throw Error(d.detail||'فشل البحث');statusEl.textContent=d.count+' نتيجة';results.innerHTML=d.records.map(x=>`<article class="card"><h2>${escapeHtml(x.title||'بدون عنوان')}</h2><div class="meta">${escapeHtml(x.authors||'')} · ${escapeHtml(x.journal||'')} · ${escapeHtml(x.year||'')} · ${x.open_access?'وصول مفتوح':''}</div><p class="abstract">${escapeHtml(x.abstract||'الملخص غير متوفر في السجل.')}</p>${x.source_url?`<a target="_blank" rel="noopener" href="${x.source_url}">عرض في Europe PMC</a>`:''}${x.doi?` · <a target="_blank" rel="noopener" href="https://doi.org/${encodeURIComponent(x.doi)}">DOI</a>`:''}</article>`).join('')}catch(err){statusEl.textContent='تعذر البحث: '+err.message}});function escapeHtml(s){const d=document.createElement('div');d.textContent=s||'';return d.innerHTML}</script></body></html>'''
