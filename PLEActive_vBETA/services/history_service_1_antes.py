# -*- coding: utf-8 -*-
# Dependencias básicas
import os, sys, sqlite3, time, threading, json, tempfile, shutil, platform
from datetime import datetime, timedelta
import json as _json
import requests
from bs4 import BeautifulSoup
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote


try:
    from keybert import KeyBERT
except Exception:
    KeyBERT = None
try:
    import spacy
except Exception:
    spacy = None
try:
    import nltk
    from nltk.corpus import stopwords as _stopwords
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        try:
            nltk.download('stopwords')
        except Exception:
            pass
    SP_STOPWORDS = set(_stopwords.words('spanish'))
except Exception:
    SP_STOPWORDS = set()

PROJECT_ROOT = Path(__file__).resolve().parent  # o .parent.parent si tu script está en /src/etc

TEMP_DIR = PROJECT_ROOT / "config" / "frecuenciaTemporal"
EXPORT_DIR = PROJECT_ROOT / "chrome_exports" / "teacher"

# Crear las carpetas si no existen
TEMP_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# Apunta los paths a las nuevas ubicaciones
STATE_PATH = str(TEMP_DIR / "chrome_rt_state.json")           # JSON temporal
OUTPUT_JSON_PATH = str(EXPORT_DIR / "chrome_history_rt.json")    # JSON final

# Configuración
PROFILE_DIR = None                 # Perfil de Chrome
POLL_INTERVAL_SECONDS = 3          # Frecuencia de consulta
BATCH_SIZE = 5                     # Enviar cada 5 visitas

BASE_URL = "https://uninovadeplan-ws.javali.pt"
SEND_RT_ENABLED = False # Cambiar a True para habilitar envío

HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
}
HTTP_TIMEOUT = 10

_KW_MODEL = None
_NLP = None

def _load_models():
    global _KW_MODEL, _NLP
    if _KW_MODEL is None and KeyBERT is not None:
        try:
            _KW_MODEL = KeyBERT(model="paraphrase-multilingual-MiniLM-L12-v2")
            print("[KW] KeyBERT cargado OK")
        except Exception as e:
            print(f"[KW] No se pudo cargar KeyBERT: {e}")
            _KW_MODEL = None
    if _NLP is None and spacy is not None:
        try:
            _NLP = spacy.load("es_core_news_sm")
            print("[NLP] spaCy es_core_news_sm cargado OK")
        except Exception as e:
            print(f"[NLP] spaCy no disponible, usando blank('es'): {e}")
            try:
                _NLP = spacy.blank("es")
            except Exception as e2:
                print(f"[NLP] No se pudo crear blank('es'): {e2}")
                _NLP = None

def _resolver_guardar_id_ple():
    """
    Busca qt_views/ple/guardarIDPLE.txt subiendo varios niveles o en el cwd.
    """
    candidatos = []
    base = Path(__file__).resolve().parent
    for _ in range(8):
        candidatos.append(base / "qt_views" / "ple" / "guardarIDPLE.txt")
        base = base.parent
    candidatos.append(Path(os.getcwd()) / "qt_views" / "ple" / "guardarIDPLE.txt")
    for c in candidatos:
        if c.is_file():
            return str(c)
    return None

def _resolver_perfil_usuario_json():
    """
    Busca app/auth/perfil_usuario.json subiendo varios niveles o en el cwd.
    """
    bases = []
    base = Path(__file__).resolve().parent
    for _ in range(6):
        bases.append(base / "app" / "auth" / "perfil_usuario.json")
        base = base.parent
    bases.append(Path(os.getcwd()) / "app" / "auth" / "perfil_usuario.json")
    for p in bases:
        if p.is_file():
            return str(p)
    return None

def _obtener_valor_json(archivo_json, clave):
    try:
        with open(archivo_json, 'r', encoding='utf-8') as f:
            return json.load(f).get(clave)
    except Exception as e:
        print(f"[UID] No se obtuvo {clave} de {archivo_json}: {e}")
        return None
    
def normalize_url(u: str) -> str:
    try:
        pu = urlparse(u)
        if pu.netloc.endswith(("google.com","google.es","google.com.mx","google.pt")) and pu.path == "/url":
            q = parse_qs(pu.query)
            for key in ("url","q","u"):
                if key in q and q[key]:
                    return unquote(q[key][0])
        bad_params = {"utm_source","utm_medium","utm_campaign","utm_term","utm_content","gclid","fbclid"}
        if pu.query:
            q = parse_qs(pu.query)
            clean = {k:v for k,v in q.items() if k not in bad_params}
            from urllib.parse import urlencode
            return pu._replace(query=urlencode(clean, doseq=True)).geturl()
        return u
    except Exception:
        return u
    
def _fallback_keywords_from_title_and_path(url, soup):
    title = ""
    if soup and soup.title and soup.title.string:
        title = soup.title.string.strip()
    # tokens del path
    path_tokens = []
    try:
        from urllib.parse import urlparse
        p = urlparse(url).path
        path_tokens = [t for t in re.split(r"[/\-_]+", p) if t and t.isalpha() and len(t) > 3]
    except Exception:
        pass
    candidates = []
    if title:
        candidates.extend(re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{4,}", title))
    candidates.extend(path_tokens)
    cleaned = _clean_and_validate_keywords(candidates)
    return cleaned[:8]

# Lee userID una sola vez al cargar el módulo
_perfil = _resolver_perfil_usuario_json()
uid_val = _obtener_valor_json(_perfil, "uid") if _perfil else None
try:
    DEFAULT_PLE_USER_ID = int(uid_val) if uid_val is not None else 0
except Exception:
    DEFAULT_PLE_USER_ID = 0
print(f"[UID] DEFAULT_PLE_USER_ID: {DEFAULT_PLE_USER_ID}")

def _leer_id_ple_dinamico():
    """
    Lee pleseleccionado=<id> de guardarIDPLE.txt.
    Retorna 0 si no se encuentra.
    """
    try:
        path = _resolver_guardar_id_ple()
        if not path:
            return 0
        with open(path, "r", encoding="utf-8") as fh:
            for linea in fh:
                if "=" in linea:
                    k, v = linea.strip().split("=", 1)
                    if k.strip() == "pleseleccionado":
                        return int(v.strip())
    except Exception as e:
        print(f"[PLE] No se pudo leer guardarIDPLE.txt: {e}")
    return 0

# Rutas de Chrome
def resolve_chrome_history_path(profile_dir=None):
    sysname = platform.system()
    if sysname == 'Windows':
        base = os.path.join(os.getenv('LOCALAPPDATA'), 'Google', 'Chrome', 'User Data')
    elif sysname == 'Darwin':
        base = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'Google', 'Chrome')
    else:
        base = os.path.join(os.path.expanduser('~'), '.config', 'google-chrome')
    requested = (profile_dir or 'Default') or 'Default'
    alias_map = {"Persona 1": "Profile 1", "Persona 2": "Profile 2", "Person 1": "Profile 1", "Person 2": "Profile 2"}
    requested = alias_map.get(requested, requested)
    candidates = [requested]
    if requested.lower().startswith("persona "):
        try:
            n = requested.split()[-1]
            candidates.append(f"Profile {int(n)}")
        except Exception:
            pass
    if requested != "Default":
        candidates.append("Default")
    try:
        for d in sorted(os.listdir(base)):
            if d.startswith("Profile ") and d not in candidates:
                candidates.append(d)
    except FileNotFoundError:
        raise FileNotFoundError(f"No existe la carpeta base de Chrome: {base}")
    for folder in candidates:
        hist_path = os.path.join(base, folder, 'History')
        if os.path.isfile(hist_path):
            return hist_path
    raise FileNotFoundError("No se encontró el archivo 'History'.")

# Copia temporal segura
def copy_history_to_temp(src_history_path):
    tmp_dir = tempfile.mkdtemp(prefix="chrome_hist_rt_")
    tmp_history = os.path.join(tmp_dir, "History.sqlite")
    shutil.copy2(src_history_path, tmp_history)
    return tmp_dir, tmp_history

# Lecturas desde snapshot
def get_max_visit_id_on_snapshot(history_path):
    conn = sqlite3.connect(history_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT IFNULL(MAX(id), 0) FROM visits;")
        (max_id,) = cur.fetchone()
        return int(max_id or 0)
    finally:
        conn.close()

def fetch_new_visits_since(history_path, last_seen_id, limit):
    conn = sqlite3.connect(history_path)
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT v.id, u.url, u.title, v.visit_time, v.visit_duration
            FROM visits v
            JOIN urls u ON v.url = u.id
            WHERE v.id > ?
            ORDER BY v.id ASC
            LIMIT ?;
        """, (last_seen_id, limit))
        rows = cur.fetchall()
        epoch_start = datetime(1601, 1, 1)
        out = []
        for (vid, url, title, visit_time, visit_dur) in rows:
            start_dt = epoch_start + timedelta(microseconds=visit_time or 0)
            dur = (visit_dur / 1_000_000) if (visit_dur and visit_dur > 0) else 5
            end_dt = start_dt + timedelta(seconds=dur)
            out.append({
                "visit_id": int(vid),
                "url": url or "",
                "title": title or "",
                "startTime": start_dt.isoformat() + "Z",
                "endTime": end_dt.isoformat() + "Z",
                "durationSeconds": dur
            })
        return out
    finally:
        conn.close()

# Estado persistente (base interna)
def load_state(path=STATE_PATH):
    if not os.path.isfile(path):
        return {"last_seen_id": 0, "pending": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {"last_seen_id": int(data.get("last_seen_id", 0)), "pending": data.get("pending", [])}
    except Exception:
        return {"last_seen_id": 0, "pending": []}

def save_state(state, path=STATE_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def _requests_soup(url):
    try:
        r = requests.get(url, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT, allow_redirects=True)
        r.raise_for_status()
        ctype = r.headers.get("Content-Type", "").lower()
        if "text/html" not in ctype:
            print(f"[HTTP] no-html {url}: Content-Type={ctype}")
            return None
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print(f"[HTTP] fallo {url}: {e}")
        return None

def _best_text_from_soup(soup, min_chars=400):
    if soup is None:
        return ""
    def _join_text(nodes, limit=None):
        txt = " ".join([x.strip() for x in nodes if isinstance(x, str) and x.strip()])
        txt = " ".join(txt.split())
        return txt if limit is None else txt[:limit]

    # 1) <article>
    article = soup.select("article")
    if article:
        txt = _join_text(article[0].stripped_strings)
        if len(txt) >= min_chars:
            return txt

    # 2) encabezados + párrafos
    headers = [h.get_text(strip=True) for h in soup.select("h1, h2")[:5]]
    paras = [p.get_text(strip=True) for p in soup.select("p")[:40]]
    combo = " ".join([" ".join(headers), " ".join(paras)]).strip()
    if len(combo) >= min_chars:
        return combo

    # 3) fallback body
    body_txt = _join_text(soup.body.stripped_strings if soup.body else [], 12000)
    return body_txt

def _clean_and_validate_keywords(keywords):
    out = []
    for kw in keywords or []:
        kw = re.sub(r'([a-záéíóúüñ])([A-ZÁÉÍÓÚÜÑ])', r'\1 \2', kw)
        kw = re.sub(r'\s+', ' ', kw).strip().lower()
        tokens = []
        if _NLP:
            try:
                doc = _NLP(kw)
                tokens = [t.text for t in doc if t.is_alpha and t.text.lower() not in SP_STOPWORDS]
            except Exception:
                tokens = [w for w in re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", kw) if w.lower() not in SP_STOPWORDS]
        else:
            tokens = [w for w in re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", kw) if w.lower() not in SP_STOPWORDS]
        if tokens:
            norm = " ".join(tokens)
            if len(norm.split()) > 1 or len(norm) > 4:
                out.append(norm)
    # dedup preservando orden
    seen, dedup = set(), []
    for t in out:
        if t not in seen:
            seen.add(t)
            dedup.append(t)
    return dedup

def _meta_keywords_from_soup(soup):
    if soup is None:
        return []
    vals = []
    # name=keywords, news_keywords
    for sel in [
        'meta[name="keywords"]', 'meta[name="Keywords"]', 'meta[name="news_keywords"]'
    ]:
        for m in soup.select(sel):
            if m.get("content"):
                vals.append(m["content"])
    # property=article:tag, og:video:tag
    for sel in [
        'meta[property="article:tag"]', 'meta[property="og:video:tag"]'
    ]:
        for m in soup.select(sel):
            if m.get("content"):
                vals.append(m["content"])
    # split y limpiar
    toks = []
    for raw in vals:
        for p in re.split(r',|;|\|', raw or ""):
            p = (p or "").strip()
            if p:
                toks.append(p)
    return _clean_and_validate_keywords(toks)

def _jsonld_topics_from_soup(soup, max_topics=3):
    if soup is None:
        return []
    topics = []
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = _json.loads(script.get_text(strip=True))
            objs = data if isinstance(data, list) else [data]
            for obj in objs:
                if not isinstance(obj, dict):
                    continue
                # @type
                t = obj.get("@type")
                if isinstance(t, list):
                    topics.extend([str(x).strip() for x in t if str(x).strip()])
                elif t:
                    topics.append(str(t).strip())
                # about
                ab = obj.get("about")
                if isinstance(ab, list):
                    for a in ab:
                        if isinstance(a, dict):
                            v = str(a.get("name", "")).strip()
                            if v: topics.append(v)
                        else:
                            v = str(a).strip()
                            if v: topics.append(v)
                elif isinstance(ab, dict):
                    v = str(ab.get("name", "")).strip()
                    if v: topics.append(v)
                elif isinstance(ab, str):
                    v = ab.strip()
                    if v: topics.append(v)
                # keywords / articleSection / genre
                for key in ("keywords", "articleSection", "genre"):
                    val = obj.get(key)
                    if isinstance(val, list):
                        topics.extend([str(x).strip() for x in val if str(x).strip()])
                    elif isinstance(val, str):
                        for piece in re.split(r',|;|\|', val):
                            piece = piece.strip()
                            if piece:
                                topics.append(piece)
        except Exception:
            continue
    # limpieza/normalización
    bad = {"news", "article", "blog", "website"}
    seen, clean = set(), []
    for t in topics:
        t = re.sub(r'\s+', ' ', t).strip()
        if not t or len(t) < 3 or t.lower() in bad:
            continue
        if t not in seen:
            seen.add(t)
            clean.append(t)
    return clean[:max_topics]

def infer_activity_type(url, title, soup=None):
    """Heurístico con hints de OG/JSON-LD."""
    ul = (url or "").lower()
    tl = (title or "").lower()

    # JSON-LD / OG
    def _ld_types():
        ts = []
        if soup:
            for script in soup.select('script[type="application/ld+json"]'):
                try:
                    data = _json.loads(script.get_text(strip=True))
                    objs = data if isinstance(data, list) else [data]
                    for obj in objs:
                        t = obj.get("@type")
                        if isinstance(t, list):
                            ts.extend([str(x).lower() for x in t])
                        elif t:
                            ts.append(str(t).lower())
                except Exception:
                    continue
        return ts

    ld = _ld_types()
    if any("video" in t for t in ld):
        return "Video"
    if any(t in ld for t in ["article", "newsarticle", "blogposting"]):
        return "Article"
    if any(t in ld for t in ["softwaresourcecode", "code", "repository"]):
        return "Code"
    if any(t in ld for t in ["dataset"]):
        return "Dataset"
    if any(t in ld for t in ["course", "learningresource", "educationalorganization"]):
        return "Module"

    # OG type
    if soup:
        og = soup.select_one('meta[property="og:type"]')
        if og and og.get("content"):
            ogt = og["content"].lower()
            if "video" in ogt: return "Video"
            if "article" in ogt: return "Article"
            if "book" in ogt: return "Book"

    # dominio/ruta
    host = re.sub(r'^https?://', '', ul).split('/')[0]
    if any(h in host for h in ["youtube.com", "youtu.be", "vimeo.com", "dailymotion.com", "twitch.tv"]):
        return "Video"
    if any(h in host for h in ["github.com", "gitlab.com", "bitbucket.org"]):
        return "Code"
    if "wikipedia.org" in host:
        return "Reference"
    if any(h in host for h in ["docs.google.com", "drive.google.com", "colab.research.google.com", "notion.so"]):
        return "Tool"
    if any(k in host for k in ["edx.org","coursera.org","udacity.com","khanacademy.org","classroom.google.com","moodle","canvas"]):
        return "Module"
    if any(k in host for k in ["medium.com","bbc.com","nytimes.com","theguardian.com","elpais.com","eluniversal.com.mx","milenio.com"]):
        return "Article"
    if any(k in host for k in ["stackoverflow.com","stackexchange.com","reddit.com","x.com","twitter.com","facebook.com","fb.com"]):
        return "Discussion"
    if any(k in host for k in ["docs.", "developer.", "developers.", "readthedocs"]):
        return "Reference"

    # título
    if any(w in tl for w in ["tutorial","guía","how to","walkthrough","curso"]):
        return "Module"
    if any(w in tl for w in ["api","reference","docs","manual"]):
        return "Reference"
    if any(w in tl for w in ["paper","estudio","artículo","journal"]):
        return "Article"

    return "Other"

def extract_domains(soup, fallback_title="", fallback_desc=""):
    """Primero meta/JSON-LD; si no hay señal, usa heurística simple."""
    topics = _jsonld_topics_from_soup(soup, max_topics=3)
    if not topics:
        topics = _meta_keywords_from_soup(soup)
    if topics:
        return topics[:3]
    # heurística muy simple con título+desc
    bag = f"{fallback_title} {fallback_desc}".lower()
    if any(w in bag for w in ["matemática","álgebra","cálculo","geometría"]):
        return ["Mathematics"]
    if any(w in bag for w in ["biología","química","física","ciencia"]):
        return ["Science"]
    if any(w in bag for w in ["programación","software","código","python","java","javascript"]):
        return ["Computer Science"]
    return ["General Knowledge"]

def extract_keywords(url, soup):
    """meta → KeyBERT sobre texto → vacío si no se puede, con logs claros."""
    # 1) meta
    meta = _meta_keywords_from_soup(soup)
    if len(meta) >= 3:
        print(f"[KW][meta] {url} -> {len(meta)}")
        return meta[:15]

    # 2) KeyBERT sobre texto real
    if soup is None:
        print(f"[KW][skip] {url} -> sin HTML (soup=None)")
        # Fallback de último recurso aunque no haya HTML (sólo desde URL)
        fb = _fallback_keywords_from_title_and_path(url, soup)
        if fb:
            print(f"[KW][fallback] {url} -> {fb[:5]}")
            return fb
        return []

    _load_models()
    if _KW_MODEL is None:
        print(f"[KW][skip] {url} -> KeyBERT no disponible")
        fb = _fallback_keywords_from_title_and_path(url, soup)
        if fb:
            print(f"[KW][fallback] {url} -> {fb[:5]}")
            return fb
        return []

    text = _best_text_from_soup(soup, min_chars=120)
    if not text or len(text) < 120:
        print(f"[KW][no-text] {url} -> texto insuficiente ({0 if not text else len(text)} chars)")
        fb = _fallback_keywords_from_title_and_path(url, soup)
        if fb:
            print(f"[KW][fallback] {url} -> {fb[:5]}")
            return fb
        return []

    title = soup.title.string.strip() if (soup.title and soup.title.string) else ""

    try:
        content = f"{title}. {text}"
        kws = _KW_MODEL.extract_keywords(
            content,
            keyphrase_ngram_range=(1, 3),
            stop_words=list(SP_STOPWORDS),
            use_mmr=True,
            diversity=0.5,
            top_n=20
        )
        print(f"[KW][keybert] {url} -> {len(kws)} crudos")
        cleaned = _clean_and_validate_keywords([k[0] for k in kws])
        print(f"[KW][keybert-clean] {url} -> {len(cleaned)} limpios (preview: {cleaned[:5]})")
        if cleaned:
            return cleaned[:15]
        # Si KeyBERT devolvió vacío, último recurso:
        fb = _fallback_keywords_from_title_and_path(url, soup)
        if fb:
            print(f"[KW][fallback] {url} -> {fb[:5]}")
            return fb
        return []
    except Exception as e:
        print(f"[KW][error] {url} -> {e}")
        fb = _fallback_keywords_from_title_and_path(url, soup)
        if fb:
            print(f"[KW][fallback] {url} -> {fb[:5]}")
            return fb
        return []
    
def enrich_visit(item):
    """Devuelve el item con activityType, associatedDomains, associatedKeywords."""
    title = item.get("title", "") or ""
    url = normalize_url(item.get("url", ""))
    item["url"] = url  # para que se guarde el destino final
    soup = _requests_soup(url)

    # description sencillita para mejor dominio
    desc = ""
    if soup:
        meta_desc = soup.select_one('meta[name="description"], meta[property="og:description"]')
        if meta_desc and meta_desc.get("content"):
            desc = meta_desc["content"]

    try:
        activity = infer_activity_type(url, title, soup)
    except Exception:
        activity = "Other"

    try:
        domains = extract_domains(soup, fallback_title=title, fallback_desc=desc)
    except Exception:
        domains = ["General Knowledge"]

    try:
        keywords = extract_keywords(url, soup)
    except Exception:
        keywords = []

    print(f"[KW][final] {url} -> {len(keywords)} | {keywords[:5]}")

    item["activityType"] = activity
    item["associatedDomains"] = domains
    item["associatedKeywords"] = keywords
    return item
def _send_rt_batch_to_server(json_path: str):
    if not SEND_RT_ENABLED:
        return
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            monitoringData = json.load(f)
        resp = requests.post(f"{BASE_URL}/tracked-data-batch", json=monitoringData, timeout=20)
        resp.raise_for_status()
        print(f"[OK] Envío RT -> {BASE_URL}/tracked-data-batch (status {resp.status_code})")
    except Exception as e:
        print(f"[WARN] Falló envío RT: {e}")
# Escritura del lote JSON (sobrescribe)
def write_batch_json(batch_items, user_id=None, associated_ple=None, out_path=OUTPUT_JSON_PATH):
    
    if user_id is None:
        user_id = DEFAULT_PLE_USER_ID
    if associated_ple is None:
        associated_ple = _leer_id_ple_dinamico()
    
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    payload = {
        "userID": user_id,
        "associatedPLE": associated_ple,
        "trackedDataList": [
            {
                "activityType": item.get("activityType", "Other"),
                "associatedURL": item["url"],
                "associatedDomains": item.get("associatedDomains", ["General Knowledge"]),
                "associatedKeywords": item.get("associatedKeywords", []),
                "startTime": item["startTime"],
                "endTime": item["endTime"],
                "feedback": {"score": None, "comments": None}
            }
            for item in batch_items
        ]
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=4)

# Servicio de monitoreo
class RealTimeHistoryWatcher:
    def __init__(self, profile_dir=None, poll_interval=POLL_INTERVAL_SECONDS, batch_size=BATCH_SIZE):
        self.profile_dir = profile_dir
        self.poll_interval = poll_interval
        try:
            self.batch_size = int(batch_size) if int(batch_size) > 0 else BATCH_SIZE
        except Exception:
            self.batch_size = BATCH_SIZE
        self._stop = threading.Event()
        self._thread = None
        self._state = load_state()
        self._last_seen_id = self._state.get("last_seen_id", 0)

    def start(self):
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join()

    def _run_loop(self):
        try:
            history_src = resolve_chrome_history_path(self.profile_dir)
        except Exception as e:
            print(f"[ERROR] Ruta de History: {e}")
            return

        if not self._last_seen_id:
            try:
                tmp_dir, tmp_hist = copy_history_to_temp(history_src)
                try:
                    self._last_seen_id = get_max_visit_id_on_snapshot(tmp_hist)
                    self._state["last_seen_id"] = self._last_seen_id
                    save_state(self._state)
                finally:
                    shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception as e:
                print(f"[WARN] Init last_seen_id: {e}")
                self._last_seen_id = 0

        pending = list(self._state.get("pending", []))

        while not self._stop.is_set():
            try:
                tmp_dir, tmp_hist = copy_history_to_temp(history_src)
                try:
                    new_items = fetch_new_visits_since(tmp_hist, self._last_seen_id, max(self.batch_size, 50))
                    if new_items:
                        self._last_seen_id = max(self._last_seen_id, max(i["visit_id"] for i in new_items))
                        self._state["last_seen_id"] = self._last_seen_id
                        pending.extend(new_items)

                        if len(pending) >= self.batch_size:
                            batch = pending[:self.batch_size]
                            enriched = []
                            for it in batch:
                                try:
                                    enriched.append(enrich_visit(dict(it)))
                                except Exception:
                                    f=dict(it)
                                    f["activityType"] = "Other"
                                    f["associatedDomains"] = ["General Knowledge"]
                                    f["associatedKeywords"] = []
                                    enriched.append(f)
                            write_batch_json(enriched)
                            print(f"[OK] JSON con {len(enriched)} items -> {OUTPUT_JSON_PATH}")
                            _send_rt_batch_to_server(OUTPUT_JSON_PATH)
                            pending = pending[self.batch_size:]
                            self._state["pending"] = pending
                            save_state(self._state)
                        else:
                            self._state["pending"] = pending
                            save_state(self._state)
                finally:
                    shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception as e:
                print(f"[ERROR] Iteración: {e}")

            self._stop.wait(self.poll_interval)

        self._state["last_seen_id"] = self._last_seen_id
        self._state["pending"] = pending
        save_state(self._state)

if __name__ == "__main__":
    watcher = RealTimeHistoryWatcher(profile_dir=PROFILE_DIR, poll_interval=POLL_INTERVAL_SECONDS, batch_size=BATCH_SIZE)
    try:
        watcher.start()
        print("[INFO] Monitoreo iniciado. Ctrl+C para detener.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Deteniendo...")
        watcher.stop()
        print("[INFO] Finalizado.")
