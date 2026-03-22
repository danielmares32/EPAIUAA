# Importación de librerías necesarias
import os   # Para manejar rutas de archivos y operaciones del sistema operativo
import sys  # For system path manipulation
import json # Para manejar rutas de archivos y operaciones del sistema operativo
import sqlite3  # Para interactuar con bases de datos SQLite
import scrapy   # type: ignore # Framework para la extracción de datos web
from scrapy.crawler import CrawlerProcess   # type: ignore # Para ejecutar spiders de Scrapy de manera programática
from datetime import datetime, timedelta    # Para manejar fechas y tiempos
import re   # Para manejar expresiones regulares
from collections import defaultdict # Para crear diccionarios con valores por defecto

# Import authentication configuration
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.config import get_auth_headers


###################################### Inicia Código de Librerías de Keybert y Spacy ######################################################## 
# Código añadido por Julio Enríquez 16-12-2024

import requests  # type: ignore # Para realizar solicitudes HTTP
from bs4 import BeautifulSoup  # type: ignore # Para analizar el HTML de una página web
from keybert import KeyBERT  # type: ignore # Para extraer palabras clave usando KeyBERT
import spacy  # type: ignore # Para validar y procesar texto avanzado
from nltk.corpus import stopwords, words, cess_esp  # type: ignore # Para manejar palabras comunes irrelevantes
import nltk  # type: ignore # Biblioteca para procesamiento de lenguaje natural
from pathlib import Path

import shutil
import tempfile
import platform
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EXPORT_DIR = str(PROJECT_ROOT / "chrome_exports" / "teacher")


GlobalKeywords = "something"

# Combinar stopwords en inglés y español
try:
    stop_words_en = set(stopwords.words('english'))
except Exception:
    stop_words_en = set()
try:
    stop_words_es = set(stopwords.words('spanish'))
except Exception:
    stop_words_es = set()
stop_words = stop_words_en.union(stop_words_es)

# Diccionarios de palabras válidas (convertidas a minúsculas para comparación)
try:
    english_words = set(word.lower() for word in words.words())  # Palabras en inglés
except Exception:
    english_words = set()
    print("Warning: NLTK 'words' corpus not found. Keyword validation will be limited.")

try:
    spanish_words = set(word.lower() for word in cess_esp.words())  # Palabras en español
except Exception:
    spanish_words = set()
    print("Warning: NLTK 'cess_esp' corpus not found. Keyword validation will be limited.")

# --- LISTA DE STOPWORDS EN ESPAÑOL (ampliable) ---
STOPWORDS = {
    'que', 'está', 'y', 'de', 'la', 'el', 'en', 'un', 'una', 'los', 'las', 'del',
    'al', 'por', 'con', 'para', 'es', 'son', 'como', 'se', 'su', 'lo', 'le',
    'me', 'te', 'nos', 'os', 'les', 'mi', 'tu', 'si', 'no', 'ni', 'o', 'pero',
    'porque', 'cuando', 'donde', 'cómo', 'cuál', 'qué', 'quien', 'cual', 'a',
    'ante', 'bajo', 'cabe', 'con', 'contra', 'desde', 'durante', 'en', 'entre',
    'hacia', 'hasta', 'mediante', 'para', 'según', 'sin', 'sobre', 'tras'
}




##################################### Termina Código de Librerías de Keybert y Spacy #########################################################

###################################### Inicia Código de Keybert y Spacy ###################################################################### 
# Código añadido por Equipo UAA 16-12-2024

# Descargar stopwords si no están disponibles
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    try:
        nltk.download('stopwords')
    except Exception:
        pass

try:
    spanish_stopwords = set(stopwords.words('spanish'))
except Exception:
    spanish_stopwords = set()

kw_model = None
nlp = None

def load_models():
    print("Entro a load_models")
    global kw_model, nlp
    if kw_model is None:
        kw_model = KeyBERT(model="paraphrase-multilingual-MiniLM-L12-v2")
    if nlp is None:
        try:
            nlp = spacy.load("es_core_news_sm")
        except Exception:
            nlp = spacy.blank("es")
            

##################################### Termina Código de Librerías de Keybert y Spacy #########################################################



# Clase para extraer el historial de Google Chrome
class ChromeHistoryExtractor:
    """
    Extrae todos los registros del historial de la base de datos de Chrome.
        """
    def __init__(self, profile_dir=None):
        # p.ej. "Default", "Profile 1", "Persona 1"
        self.profile_dir = profile_dir

    def get_chrome_history_path(self):
        print("Entro a funcion get_chrome_history_path")
        sysname = platform.system()
        if sysname == 'Windows':
            base = os.path.join(os.getenv('LOCALAPPDATA'), 'Google', 'Chrome', 'User Data')
        elif sysname == 'Darwin':  # macOS
            base = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'Google', 'Chrome')
        else:  # Linux
            base = os.path.join(os.path.expanduser('~'), '.config', 'google-chrome')

        requested = (self.profile_dir or 'Default') or 'Default'

        # Mapear alias comunes (Chrome en español suele seguir usando "Profile N" como nombre de carpeta)
        alias_map = {
            "Persona 1": "Profile 1",
            "Persona 2": "Profile 2",
            "Person 1":  "Profile 1",
            "Person 2":  "Profile 2",
        }
        requested = alias_map.get(requested, requested)

        # Armar lista de candidatos en orden de preferencia
        candidates = []
        # 1) Lo que se pidió
        candidates.append(requested)
        # 2) Si pidieron "Persona N", probar "Profile N"
        if requested.lower().startswith("persona "):
            try:
                n = requested.split()[-1]
                candidates.append(f"Profile {int(n)}")
            except Exception:
                pass
        # 3) Default como fallback
        if requested != "Default":
            candidates.append("Default")
        # 4) Cualquier "Profile N" que exista
        try:
            for d in sorted(os.listdir(base)):
                if d.startswith("Profile ") and d not in candidates:
                    candidates.append(d)
        except FileNotFoundError:
            raise FileNotFoundError(f"No existe la carpeta base de Chrome: {base}")

        print(f"[history] base={base}")
        print(f"[history] candidatos de carpeta: {candidates}")

        # Probar cada candidato hasta encontrar el archivo History
        for folder in candidates:
            hist_path = os.path.join(base, folder, 'History')
            print(f"[history] probando: {hist_path}")
            if os.path.isfile(hist_path):
                print(f"[history] usando carpeta: {folder}")
                return hist_path

        # Diagnóstico adicional: listar cuáles tienen History
        print("[history] carpetas bajo base que SÍ tienen History:")
        try:
            for d in sorted(os.listdir(base)):
                hp = os.path.join(base, d, 'History')
                if os.path.isfile(hp):
                    print("   -", hp)
        except Exception as e:
            print("[history] no se pudo listar:", e)

        raise FileNotFoundError(
            f"No se encontró el archivo de historial de Google Chrome para ningún candidato en {base}. "
            f"Solicitado originalmente: {self.profile_dir!r} (traducido a {requested!r})."
        )

    def convert_chrome_time(self, chrome_time):
        print("Entro a convert_chrome_time")
        """
        Convierte el tiempo de Chrome (microsegundos desde 1601-01-01) a un formato de datetime estándar.
        """
        epoch_start = datetime(1601, 1, 1)
        return epoch_start + timedelta(microseconds=chrome_time)

    def extract_history(self, days_back=None, max_urls=None, shape="flat"):
        """
        Extrae historial de Chrome.
        - shape="flat": lista plana (url,title,visit_time,end_time,duration)  [tu formato]
        - shape="grouped": agrupado por trackedDataID con arrays               [formato equipo]
        days_back: si se da, filtra visitas recientes (UTC).
        max_urls:  límite para shape="flat" (no aplica a grouped).
        """
        print("Entro a extract_history")
        history_path = self.get_chrome_history_path()

        # Copia a un archivo temporal para evitar lock
        tmp_dir = tempfile.mkdtemp(prefix="chrome_hist_")
        try:
            tmp_history = os.path.join(tmp_dir, "History.sqlite")
            shutil.copy2(history_path, tmp_history)

            with sqlite3.connect(tmp_history) as conn:
                cursor = conn.cursor()

                if shape == "grouped":
                    
                    query = """
                    SELECT urls.id, urls.url, urls.title, visits.visit_time, visits.visit_duration
                    FROM urls
                    JOIN visits ON urls.id = visits.url
                    ORDER BY urls.id ASC;
                    """
                    cursor.execute(query)
                    results = cursor.fetchall()

                    # Construcción agrupada
                    history_data = defaultdict(lambda: {
                        "urls": [], "titles": [], "visit_times": [], "end_times": [], "durations": []
                    })
                    for row in results:
                        visit_dt = self.convert_chrome_time(row[3])  # visit_time
                        dur_s = (row[4] / 1_000_000) if (row[4] and row[4] > 0) else 5
                        end_dt = visit_dt + timedelta(seconds=dur_s)

                        history_data[row[0]]["urls"].append(row[1])   # url
                        history_data[row[0]]["titles"].append(row[2]) # title
                        history_data[row[0]]["visit_times"].append(visit_dt.isoformat() + "Z")
                        history_data[row[0]]["end_times"].append(end_dt.isoformat() + "Z")
                        history_data[row[0]]["durations"].append(dur_s)

                    return [{"trackedDataID": tid, **data} for tid, data in history_data.items()]

                else:
                    # Filtro temporal opcional
                    if days_back is not None and isinstance(days_back, (int, float)) and days_back > 0:
                        cutoff = datetime.utcnow() - timedelta(days=int(days_back))
                        chrome_epoch = datetime(1601, 1, 1)
                        cutoff_chrome_us = int((cutoff - chrome_epoch).total_seconds() * 1_000_000)
                        query = """
                        SELECT u.url,
                            u.title,
                            MAX(v.visit_time) as last_visit_time,
                            MAX(v.visit_duration) as last_visit_duration
                        FROM urls u
                        JOIN visits v ON u.id = v.url
                        WHERE v.visit_time >= ?
                        GROUP BY u.url, u.title
                        ORDER BY last_visit_time DESC
                        """ + ( " LIMIT ?;" if max_urls else ";" )
                        params = (cutoff_chrome_us,) if not max_urls else (cutoff_chrome_us, int(max_urls))
                        cursor.execute(query, params)
                    else:
                        # Sin filtro temporal
                        query = """
                        SELECT u.url,
                            u.title,
                            MAX(v.visit_time) as last_visit_time,
                            MAX(v.visit_duration) as last_visit_duration
                        FROM urls u
                        JOIN visits v ON u.id = v.url
                        GROUP BY u.url, u.title
                        ORDER BY last_visit_time DESC
                        """ + ( " LIMIT ?;" if max_urls else ";" )
                        params = (int(max_urls),) if max_urls else ()
                        cursor.execute(query, params)

                    rows = cursor.fetchall()

            # Construcción plana + dedup
            def _is_http(u): return u and (u.startswith("http://") or u.startswith("https://"))
            entries, seen = [], set()
            for url, title, visit_time, duration in rows:
                if not _is_http(url):
                    continue
                base_url = url.split("#", 1)[0]
                if base_url in seen:
                    continue
                seen.add(base_url)

                visit_dt = self.convert_chrome_time(visit_time)
                dur_s = (duration / 1_000_000) if (duration and duration > 0) else 5
                end_dt = visit_dt + timedelta(seconds=dur_s)

                entries.append({
                    "url": base_url,
                    "title": title or "",
                    "visit_time": visit_dt.isoformat() + "Z",
                    "end_time": end_dt.isoformat() + "Z",
                    "duration": float(dur_s),
                })
            return entries

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

def extract_page_content(url):
    print("Entro a extract_page_content")
    """
    Extrae y limpia el contenido principal de una página web.
    """
    try:
        # Realizar una solicitud HTTP a la URL
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Verificar que no haya errores en la solicitud

        # Analizar el HTML con BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extraer el título de la página
        title = soup.title.string.strip() if soup.title else "Sin título"

        # Extraer los primeros 3 párrafos de contenido principal (menos texto para optimizar)
        paragraphs = soup.find_all('p', limit=3)
        content = " ".join([p.get_text(strip=True) for p in paragraphs])

        # Limpiar el texto eliminando caracteres especiales y reduciendo espacios
        content = re.sub(r'\s+', ' ', content).strip()
        content = re.sub(r'[^\w\sáéíóúüñÁÉÍÓÚÜÑ]', '', content)
        content = content.lower()  # Convertir todo el texto a minúsculas

        # Combinar título y contenido principal
        combined_text = f"{title}. {content}"
        return combined_text if len(combined_text) > 50 else "Error: Contenido insuficiente para procesar."
    except Exception as e:
        return f"Error al procesar la página: {e}"


def clean_and_validate_keywords(keywords):
    """
    Limpia y valida palabras clave eliminando combinaciones irrelevantes, stopwords
    y palabras concatenadas mal procesadas. Usa spaCy si está disponible;
    si no, hace fallback a regex.
    """
    # Asegura modelos cargados si están disponibles
    global nlp
    if nlp is None:
        try:
            load_models()
        except Exception:
            pass

    validated_keywords = []
    for kw in keywords or []:
        # Separar palabras pegadas y normalizar
        kw = re.sub(r'([a-záéíóúüñ])([A-ZÁÉÍÓÚÜÑ])', r'\1 \2', kw)
        kw = re.sub(r'\s+', ' ', kw).strip().lower()

        tokens = []
        if nlp:
            try:
                doc = nlp(kw)
                tokens = [t.text for t in doc if t.is_alpha and t.text.lower() not in spanish_stopwords]
            except Exception:
                # Fallback regex si falló spaCy
                tokens = [w for w in re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", kw) if w not in spanish_stopwords]
        else:
            # Fallback regex si no hay spaCy
            tokens = [w for w in re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", kw) if w not in spanish_stopwords]

        if tokens:
            norm = " ".join(tokens)
            # Evitar tokens triviales
            if len(norm.split()) > 1 or len(norm) > 4:
                validated_keywords.append(norm)

    # Deduplicar preservando orden
    seen, out = set(), []
    for t in validated_keywords:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def extract_keywords_combined(url):
    print("Entro a extract_keywords_combined")
    """
    Extrae palabras clave relevantes combinando KeyBERT y validaciones adicionales.
    """
    # Cargar modelos (si aún no se han cargado)
    load_models()

    # Obtener el contenido principal de la página
    content = extract_page_content(url)
    if content.startswith("Error"):
        return [content]

    # Generar palabras clave iniciales con KeyBERT
    keybert_keywords = kw_model.extract_keywords(
        content,
        keyphrase_ngram_range=(1, 3),  # Permitir palabras clave de 1 a 3 palabras
        stop_words=list(spanish_stopwords),
        use_mmr=True,  # Maximización de la Relevancia Marginal
        diversity=0.5,  # Reducir diversidad para evitar ruido
        top_n=15  # Limitar el resultado a un máximo de 15 palabras clave
    )
    keybert_keywords = [kw[0] for kw in keybert_keywords]

    # Limpiar y validar las palabras clave
    validated_keywords = clean_and_validate_keywords(keybert_keywords)

    # Filtrar duplicados
    return list(dict.fromkeys(validated_keywords))
def get_domains_from_metadata(response, max_topics=3):
        """
        Extrae dominios/temas directamente de metadatos (sin inferir):
        - <meta name="keywords">, <meta property="article:tag">, <meta property="article:section">
        - <meta name="category">, <meta name="subject">
        - JSON-LD: @type, about, keywords, articleSection, genre
        Retorna 1..max_topics elementos o ["General Knowledge"] si no hay señal.
        """
        import json, re

        def norm(s):
            s = re.sub(r'\s+', ' ', (s or '').strip())
            return s[:60]  # corta por seguridad

        topics = []

        # 1) META tags comunes
        meta_selectors = [
            '//meta[@name="keywords"]/@content',
            '//meta[@property="article:tag"]/@content',
            '//meta[@property="article:section"]/@content',
            '//meta[@name="category"]/@content',
            '//meta[@name="subject"]/@content'
        ]
        for sel in meta_selectors:
            for v in response.xpath(sel).getall():
                for piece in re.split(r',|;|\|', v):
                    piece = norm(piece)
                    if len(piece) > 2:
                        topics.append(piece)

        # 2) JSON-LD (application/ld+json)
        for ld in response.xpath('//script[@type="application/ld+json"]/text()').getall():
            try:
                data = json.loads(ld.strip())
                objs = data if isinstance(data, list) else [data]
                for obj in objs:
                    # @type
                    t = obj.get("@type")
                    if isinstance(t, list):
                        topics.extend([norm(x) for x in t if norm(x)])
                    elif t:
                        topics.append(norm(t))
                    # about (puede ser str o dict con name)
                    ab = obj.get("about")
                    if isinstance(ab, list):
                        for a in ab:
                            if isinstance(a, dict):
                                topics.append(norm(a.get("name", "")))
                            else:
                                topics.append(norm(str(a)))
                    elif isinstance(ab, dict):
                        topics.append(norm(ab.get("name", "")))
                    elif isinstance(ab, str):
                        topics.append(norm(ab))
                    # keywords / articleSection / genre
                    for key in ("keywords", "articleSection", "genre"):
                        val = obj.get(key)
                        if isinstance(val, list):
                            topics.extend([norm(x) for x in val if norm(x)])
                        elif isinstance(val, str):
                            for piece in re.split(r',|;|\|', val):
                                piece = norm(piece)
                                if len(piece) > 2:
                                    topics.append(piece)
            except Exception:
                pass

        # Limpieza: dedup conservando orden, quitar vacíos y triviales
        seen, clean = set(), []
        for t in topics:
            t = t.strip()
            if not t or len(t) < 3: 
                continue
            if t.lower() in ("news", "article", "blog", "website"):  # etiquetas genéricas
                continue
            if t not in seen:
                seen.add(t)
                clean.append(t)

        return (clean[:max_topics] or ["General Knowledge"])

# Clase Scrapy para analizar el historial web y enriquecerlo con datos adicionales
class ChromeHistorySpider(scrapy.Spider):
    name = 'chrome_history'

    def __init__(self, history_entries, profile_dir="Default"):
        self.history_entries = history_entries
        self.profile_dir = profile_dir

    def start_requests(self):
        print("Entro a start_requests")
        entries = getattr(self, "history_entries", None) or getattr(self, "history_data", None) or []
        for e in entries:
            if "url" in e:
                url = e["url"]
            elif "urls" in e and e["urls"]:
                url = e["urls"][0]
            else:
                continue
            yield scrapy.Request(
                url=url,
                callback=self.parse_history,
                cb_kwargs={"entry_meta": e},
                dont_filter=True
            )

    def infer_domains(self, title: str, description: str, extra: str):
        """
        Heurística simple si los metadatos no traen dominios/temas.
        """
        bag = f"{title or ''} {description or ''} {extra or ''}".lower()

        if any(w in bag for w in ["matemática", "álgebra", "cálculo", "geometría"]):
            return ["Mathematics"]
        if any(w in bag for w in ["biología", "química", "física", "ciencia"]):
            return ["Science"]
        if any(w in bag for w in ["programación", "software", "código", "python", "java", "javascript"]):
            return ["Computer Science"]

        # Por defecto
        return ["General Knowledge"]

    def _best_text_from_response(self, response, min_chars=400):
        
        article_html = response.xpath('//article//text()').getall()
        article_txt = " ".join([t.strip() for t in article_html if t.strip()])
        if len(article_txt) >= min_chars:
            return article_txt

        headers = response.xpath('//h1//text() | //h2//text()').getall()
        paras = response.xpath('//p//text()').getall()
        joined = " ".join([*headers[:5], *paras[:40]])
        txt = " ".join(t.strip() for t in joined.split())
        if len(txt) >= min_chars:
            return txt

        body_txt = " ".join(response.xpath('//body//text()').getall())
        body_txt = " ".join(body_txt.split())
        return body_txt[:12000]

    def _infer_from_metadata(self, response):
        # JSON-LD
        types = []
        for ld in response.xpath('//script[@type="application/ld+json"]/text()').getall():
            try:
                data = json.loads(ld.strip())
                if isinstance(data, dict) and "@type" in data:
                    t = data["@type"]
                    if isinstance(t, list):
                        types.extend([str(x) for x in t])
                    else:
                        types.append(str(t))
                elif isinstance(data, list):
                    for el in data:
                        t = el.get("@type")
                        if t:
                            types.append(str(t))
            except Exception:
                continue
        if types:
            # Mapea tipos comunes a nuestras categorías
            mapped = []
            for t in types:
                tl = t.lower()
                if "video" in tl:
                    mapped.append("Video")
                elif "article" in tl or "news" in tl or "blog" in tl:
                    mapped.append("Article")
                elif "softwaresourcecode" in tl or "code" in tl or "repository" in tl:
                    mapped.append("Code")
                elif "dataset" in tl:
                    mapped.append("Dataset")
                elif "educational" in tl or "course" in tl or "learning" in tl:
                    mapped.append("Module")
            if mapped:
                return mapped[0]

        # OpenGraph
        og_type = response.xpath(
            '//*[translate(@property,"OG:TYPE","og:type")="og:type"]/@content'
        ).get()
        if og_type:
            ot = og_type.lower()
            if "video" in ot:
                return "Video"
            if "article" in ot:
                return "Article"
            if "book" in ot:
                return "Book"

        return None

    def infer_activity_type(self, url, title, response=None):
        print("Entro a infer_activity_type")
        url = (url or "").lower()
        title = (title or "").lower()

        # 1) Metadatos de la página si tenemos response
        if response is not None:
            meta_guess = self._infer_from_metadata(response)
            if meta_guess:
                return meta_guess

        # 2) Patrones de dominio/ruta
        host = re.sub(r'^https?://', '', url).split('/')[0]
        path = url.split(host, 1)[-1] if host in url else url

        # Video
        if any(h in host for h in ["youtube.com", "youtu.be", "vimeo.com", "dailymotion.com", "twitch.tv"]):
            return "Video"

        # Code/Repo
        if "github.com" in host or "gitlab.com" in host or "bitbucket.org" in host:
            return "Code"

        # Artículo científico / Paper
        if any(h in host for h in ["arxiv.org", "doi.org", "jstor.org", "sciencedirect.com", "acm.org", "ieee.org", "springer.com", "nature.com"]):
            return "Article"

        # Wiki/Referencia
        if "wikipedia.org" in host:
            return "Reference"

        # Google Workspace / Herramientas
        if any(h in host for h in ["docs.google.com", "drive.google.com", "colab.research.google.com", "notion.so"]):
            # Sub-tipo por ruta
            if "/document" in path or "/presentation" in path or "/spreadsheets" in path:
                return "Doc"
            return "Tool"

        # Plataformas educativas / LMS
        if any(k in host for k in ["moodle", "canvas", "edx.org", "coursera.org", "udacity.com", "khanacademy.org", "classroom.google.com"]):
            return "Module"

        # Noticias / Medios
        if any(k in host for k in ["medium.com", "bbc.com", "nytimes.com", "theguardian.com", "elpais.com", "eluniversal.com.mx", "milenio.com"]):
            return "Article"

        # Social / Foros técnicos
        if any(k in host for k in ["stackoverflow.com", "stackexchange.com", "reddit.com", "x.com", "twitter.com", "fb.com", "facebook.com"]):
            return "Discussion"

        # Docs API / Referencia
        if any(k in host for k in ["docs.", "developer.", "developers."]) or "readthedocs" in host:
            return "Reference"

        # 3) Heurísticas de título
        if any(w in title for w in ["tutorial", "guía", "how to", "walkthrough", "curso"]):
            return "Module"
        if any(w in title for w in ["api", "reference", "docs", "manual"]):
            return "Reference"
        if any(w in title for w in ["paper", "estudio", "artículo", "journal"]):
            return "Article"

        return "Other"

    
    def extract_description(self, response):
        print("Entro a extract_description")
        """
        Extrae la descripción de la página a partir de meta etiquetas o contenido visible.
        """
        description = response.xpath(
            '//*[contains(@name, "description") or contains(@property, "og:description")]/@content'
        ).get()
        
        if not description:
            header_texts = response.xpath('//h1/text() | //h2/text()').getall()
            paragraph_texts = response.xpath('//p/text()').getall()
            description = ' '.join(header_texts[:2] + paragraph_texts[:2]).strip()

        if not description:
            # fallback al primer bloque 'article'
            article = response.xpath('//article//p//text()').getall()
            description = ' '.join(article[:4]).strip()

        return description[:300] if description else None

    def extract_additional_content(self, response):
        print("Entro a extract_additional_content")
        """
        Extrae contenido adicional de encabezados y párrafos de la página.
        """
        headers = response.xpath('//h1/text() | //h2/text()').getall()
        paragraphs = response.xpath('//p/text()').getall()
        additional_content = ' '.join([*headers[:10], *paragraphs[:100]])
        additional_content = " ".join(additional_content.split())
        return additional_content[:2000]  # Limitar la cantidad de contenido

    def extract_keywords(self, response):
        """
        Estrategia híbrida:
        1) Meta keywords / tags (case-insensitive y variantes): si hay sustancia, usar.
        2) Si no alcanza, generar con KeyBERT sobre el TEXTO del response (sin requests extra).
        3) Si el response no aporta suficiente texto, último recurso: extract_keywords_combined(response.url).
        """
        print("Entro a extract_keywords")

        # --- 1) Captura de meta-keywords y variantes ---
        # name=keywords (case-insensitive)
        meta_candidates = []
        meta_kw = response.xpath(
            '//*[translate(@name,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="keywords"]/@content'
        ).get()
        if meta_kw:
            meta_candidates.append(meta_kw)

        # Variantes comunes: news_keywords, article:tag, og:video:tag, etc.
        more_meta = response.xpath(
            '|'.join([
                '//meta[translate(@name,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="news_keywords"]/@content',
                '//meta[translate(@property,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="article:tag"]/@content',
                '//meta[translate(@property,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="og:video:tag"]/@content'
            ])
        ).getall()
        meta_candidates.extend(more_meta or [])

        # Normaliza y tokeniza listas de meta
        tokens = []
        for raw in meta_candidates:
            for piece in re.split(r',|;|\|', raw or ''):
                p = piece.strip()
                if p:
                    tokens.append(p)

        # Si hay suficiente "sustancia" en meta, úsala tras limpiar/validar
        if len(tokens) >= 3:
            validated = clean_and_validate_keywords(tokens)
            # Evita duplicados conservando orden
            seen, dedup = set(), []
            for t in validated:
                if t not in seen:
                    seen.add(t)
                    dedup.append(t)
            if dedup:
                return dedup[:15]

        # --- 2) KeyBERT sobre el texto ya descargado ---
        page_text = None
        try:
            page_text = self._best_text_from_response(response)
        except Exception:
            page_text = None

        if page_text and len(page_text) >= 120:
            title = (response.xpath('//title/text()').get() or "").strip() or "Sin título"
            content = f"{title}. {page_text}"
            load_models()
            try:
                keybert_keywords = kw_model.extract_keywords(
                    content,
                    keyphrase_ngram_range=(1, 3),
                    stop_words=list(spanish_stopwords),
                    use_mmr=True,
                    diversity=0.5,
                    top_n=20
                )
                keybert_keywords = [k[0] for k in keybert_keywords]
                validated = clean_and_validate_keywords(keybert_keywords)
                # dedup + corte
                out, seen = [], set()
                for k in validated:
                    if k not in seen:
                        seen.add(k)
                        out.append(k)
                if out:
                    return out[:15]
            except Exception as e:
                print(f"[KW] Error KeyBERT en response local: {e}")

        # --- 3) Último recurso: usa el pipeline externo (puede hacer requests) ---
        try:
            alternative_keywords = extract_keywords_combined(response.url)
            if alternative_keywords and not all("Error" in kw for kw in alternative_keywords):
                return alternative_keywords
        except Exception as e:
            print(f"[KW] Error en fallback extract_keywords_combined: {e}")

        # Sin suerte
        print(f"Error: No se pudieron generar palabras clave para {response.url}")
        return ["Error: Contenido insuficiente para procesar"]
            
    def parse_history(self, response, entry_meta=None):
        """
        Soporta ambos contratos:
        - Equipo: usa response.meta con arrays (urls[0], titles[0], visit_times[0], end_times[0])
        - Tu versión: usa cb_kwargs entry_meta = {"url", "title", "visit_time", "end_time"}
        """
        print("Entro a parse_history")

        # --- Normalización de metadatos según origen ---
        if entry_meta is None:
            # Contrato EQUIPO (meta con listas)
            meta = response.meta or {}
            try:
                url = meta["urls"][0]
            except Exception:
                url = meta.get("urls", [None])[0]
            title_from_hist = (meta.get("titles") or [""])[0] or ""
            start_time = (meta.get("visit_times") or [None])[0]
            end_time = None
            end_times = meta.get("end_times")
            if isinstance(end_times, list) and end_times:
                end_time = end_times[0]
            tracked_id = meta.get("trackedDataID")
        else:
            # Tu contrato (cb_kwargs)
            url = entry_meta.get("url")
            title_from_hist = entry_meta.get("title", "") or ""
            start_time = entry_meta.get("visit_time")
            end_time = entry_meta.get("end_time")
            tracked_id = entry_meta.get("trackedDataID")  # puede no existir

        # --- Inferencias y extracción consistente ---
        activity_type = self.infer_activity_type(url, title_from_hist, response=response)
        description = self.extract_description(response)
        additional_content = self.extract_additional_content(response)

        # Dominios: primero metadata del documento; si no aporta, fallback al método del equipo
        try:
            domains = get_domains_from_metadata(response)
        except NameError:
            domains = None
        if not domains or (len(domains) == 1 and domains[0] == "General Knowledge"):
            try:
                domains = self.infer_domains(title_from_hist, description, additional_content)
            except Exception:
                domains = ["General Knowledge"]

        keywords = self.extract_keywords(response)
        
        #************************************************************************************************************** NUEVO PROCESO DE LIMPIEZA DE KEYWORDS
        print("keywords after extraction process\n")
        print(keywords)
        GlobalKeywords = keywords            
        self._imprimir_GlobalKeywords(GlobalKeywords)
        
        string_representationGK = str(GlobalKeywords)            
        frase_limpia = self.limpiar_frase(string_representationGK)
        print("Vector de palabras claves despues de funcion frase_limpia")
        print(frase_limpia)
        
        # Dividir la frase en palabras
        palabras = frase_limpia.split()
                    
        # Limpiar cada palabra y expandir palabras combinadas
        palabras_limpias = []
        for palabra in palabras:
            palabras_limpias.extend(self.limpiar_palabra(palabra))

        print("palabras_limpias")
        print(palabras_limpias)
        
        # Filtrar stopwords y elegir la primera palabra válida no-stopword
        palabras_semifinal = []
        lista_sin_repetidos = list(dict.fromkeys(palabras_limpias))
        print("Lista limpia hasta el momento")
        print(lista_sin_repetidos)
        
        #**************************************************************************************************************** NUEVO PROCESO DE LIMPIEZA KEYWORDS
        
        # --- FILTRAR STOPWORDS ---
        lista_final = [palabra for palabra in lista_sin_repetidos if palabra not in STOPWORDS]

        print("\nLista FINAL sin stopwords:")
        print(lista_final)

        # Omitir si no hubo texto suficiente para obtener keywords
        if "Error: Contenido insuficiente para procesar" in keywords:
            print(f"Omitiendo registro para URL: {url} por contenido insuficiente.")
            return

        # --- Construcción uniforme del item ---
        history_item = {
            "activityType": activity_type,
            "associatedURL": url,
            "associatedDomains": domains,
            "associatedKeywords": lista_final, #Antes keywords
            "startTime": start_time,
            "endTime": end_time,
            "feedback": {"score": None, "comments": None},
        }
        # Si viene trackedDataID desde el contrato del equipo, inclúyelo
        if tracked_id is not None:
            history_item["trackedDataID"] = tracked_id

        yield history_item
    
    
    #******************************************************************************************** MEJORA PALABRAS CLAVE
    def _imprimir_GlobalKeywords(self,GlobalKeywords):
        print("GlobalKeywords de su propia funcion")
        print("Llamada a funcion directa")
        print(GlobalKeywords)

    def limpiar_frase(self,GlobalKeywords):
        # Eliminar caracteres no alfabéticos ni espacios, excepto acentos y ñ
        return re.sub(r'[^a-zA-ZáéíóúñÁÉÍÓÚÑ\s]', '', GlobalKeywords).strip()

    # Función para limpiar y separar palabras combinadas
    def limpiar_palabra(self,palabra):
        # Separar palabras combinadas, incluyendo caracteres acentuados y ñ
        # Patrón: letras (incluyendo acentos y ñ)
        palabras_separadas = re.findall(r'[a-zA-ZáéíóúñÁÉÍÓÚÑ]+', palabra)
        return palabras_separadas        
    
    #******************************************************************************************** MEJORA PALABRAS CLAVE   
        
def _resolver_guardar_id_ple():
    """
    Busca qt_views/ple/guardarIDPLE.txt de forma portable:
    1) Relativo a este archivo, subiendo varios niveles.
    2) Relativo al cwd.
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

def obtener_valor_json(archivo_json, clave):
    try:
        with open(archivo_json, 'r', encoding='utf-8') as f:
            return json.load(f).get(clave)
    except Exception as e:
        print(f"[UID] No se obtuvo {clave} de {archivo_json}: {e}")
        return None

_perfil = _resolver_perfil_usuario_json()
uid_val = obtener_valor_json(_perfil, "uid") if _perfil else None
try:
    DEFAULT_PLE_USER_ID = int(uid_val) if uid_val is not None else 0
except Exception:
    DEFAULT_PLE_USER_ID = 0
print(f"[UID] DEFAULT_PLE_USER_ID: {DEFAULT_PLE_USER_ID}")

#Pipeline para escribir los datos en un archivo  JSON
class JsonWriterPipeline:
    export_path = None
    override_user_id = None
    override_ple_id = None

    def open_spider(self, spider):
        print("Entro a open_spider")

        # Use overrides from run_crawler if provided, otherwise fall back to file-based values
        user_id = self.override_user_id
        if user_id is None:
            user_id = DEFAULT_PLE_USER_ID

        ple_id = self.override_ple_id
        if ple_id is None:
            ple_id = 0
            try:
                path = _resolver_guardar_id_ple()
                if path:
                    with open(path, "r", encoding="utf-8") as archivo:
                        for linea in archivo:
                            if "=" in linea:
                                clave, valor = linea.strip().split("=")
                                if clave.strip() == "pleseleccionado":
                                    ple_id = int(valor.strip())
                else:
                    print("[WARN] No se encontró guardarIDPLE.txt; usando 0.")
            except Exception as e:
                print(f"[WARN] No se pudo leer ID PLE dinámico: {e}. Usando 0.")

        print(f"[JsonWriterPipeline] userID={user_id}, associatedPLE={ple_id}")
        self.data = {
            "userID": user_id,
            "associatedPLE": ple_id,
            "trackedDataList": []
        }

    def close_spider(self, spider):
        print("Entro a close_spider")
        path = self.export_path or 'chrome_history.json'
        dirn = os.path.dirname(path)
        if dirn:
            os.makedirs(dirn, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as file:
            json.dump(self.data, file, ensure_ascii=False, indent=4)
        
    def process_item(self, item, spider):
        print("Entro a process_item")
        """
        Agrega cada elemento procesado al contenedor de datos.
        """
        self.data["trackedDataList"].append(item)
        return item

# Función principal para ejecutar el extractor y el spider
def run_crawler(profile_dir=None, output_dir=None, user_id=None, ple_id=None):
    print("Entro a run_crawler")
    export_dir = output_dir or DEFAULT_EXPORT_DIR
    os.makedirs(export_dir, exist_ok=True)
    print(f"[history_service_4] profile_dir => {profile_dir or 'Default'}")
    print(f"[history_service_4] user_id={user_id}, ple_id={ple_id}")

    # Pass IDs to the pipeline so they end up in the JSON payload
    if user_id is not None:
        JsonWriterPipeline.override_user_id = int(user_id)
    if ple_id is not None:
        JsonWriterPipeline.override_ple_id = int(ple_id)

    extractor = ChromeHistoryExtractor(profile_dir=profile_dir)
    history_entries = extractor.extract_history(days_back=90, max_urls=8000)
    if not history_entries:
        print("No se encontraron URLs en el rango solicitado.")
        return

    JsonWriterPipeline.export_path = os.path.join(export_dir, "chrome_history.json")
    print("Exportando JSON a:", JsonWriterPipeline.export_path)

    process = CrawlerProcess(settings={
        "ITEM_PIPELINES": { f"{__name__}.JsonWriterPipeline": 1 },
        "LOG_LEVEL": "INFO",
        # Crawling más estable y gentil
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "ROBOTSTXT_OBEY": True,         # Respeta robots.txt cuando exista
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 0.5,
        "AUTOTHROTTLE_MAX_DELAY": 8.0,
        "RETRY_TIMES": 2,
        "DOWNLOAD_TIMEOUT": 20,
        "CONCURRENT_REQUESTS": 16,
    })
    process.crawl(ChromeHistorySpider, history_entries=history_entries, profile_dir=profile_dir or "Default")
    process.start()
    #Después de generar el archivo JSON abre el archivo JSON y lo envía al servicio correspondiente
    #******************************** código para enviar el archivo JSON al servidor *************************************************
    BASE_URL = 'https://uninovadeplan-ws.javali.pt'
    json_path = Path(JsonWriterPipeline.export_path)
    with open(json_path, "r", encoding="utf-8") as j:
        monitoringData = json.load(j)

    # Add Bearer token authentication
    headers = get_auth_headers()
    headers.update({"Content-Type": "application/json"})

    response = requests.post(
        f"{BASE_URL}/tracked-data-batch",
        json=monitoringData,
        headers=headers,
        timeout=20
    )
    print(response.json())
    print("Llegó al final")
    #******************************** código para enviar el archivo JSON al servidor *************************************************

if __name__ == "__main__":
    run_crawler()
