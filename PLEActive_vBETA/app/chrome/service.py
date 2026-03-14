import os
import platform
import json
import base64
import sqlite3
import tempfile
import shutil
from datetime import datetime
from urllib.request import urlopen

from rake_nltk import Rake
from keybert import KeyBERT
import yake
import spacy

# ──────────────────────────────────────────────────────────────────────────────
# Inicialización global de extractores/modelos con fallbacks
try:
    spacy_nlp = spacy.load("es_core_news_sm")
except OSError:
    try:
        spacy_nlp = spacy.load("en_core_web_sm")
    except OSError:
        print("Warning: No spaCy models found. Installing basic English model...")
        try:
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)
            spacy_nlp = spacy.load("en_core_web_sm")
        except Exception:
            print("Warning: Could not install spaCy model. Using blank model.")
            spacy_nlp = spacy.blank("en")

try:
    rake_extractor = Rake(language="spanish", min_length=1, max_length=3)
except Exception:
    rake_extractor = Rake(language="english", min_length=1, max_length=3)

try:
    keybert_model = KeyBERT(model="paraphrase-multilingual-MiniLM-L12-v2")
except Exception:
    print("Warning: KeyBERT model not available. Using fallback.")
    keybert_model = None

try:
    yake_extractor = yake.KeywordExtractor(lan="es", n=2, top=5)
except Exception:
    yake_extractor = yake.KeywordExtractor(lan="en", n=2, top=5)
# ──────────────────────────────────────────────────────────────────────────────

def encode_image_to_base64(image_path):
    """Convierte una imagen a Base64 si el archivo existe en la ruta especificada."""
    if os.path.exists(image_path):
        try:
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode("utf-8")
        except Exception as e:
            print(f"Error al convertir la imagen {image_path} a Base64: {e}")
    return None

def fetch_avatar_from_url(url):
    """Descarga una imagen de perfil desde una URL y la convierte a Base64."""
    try:
        with urlopen(url) as response:
            return base64.b64encode(response.read()).decode("utf-8")
    except Exception as e:
        print(f"Error al descargar avatar desde {url}: {e}")
        return None

def get_chrome_profiles():
    """Obtiene información sobre los perfiles de Chrome disponibles en el sistema."""
    system = platform.system()
    if system == "Windows":
        base_path = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
    elif system == "Linux":
        base_path = os.path.expanduser("~/.config/google-chrome")
        if not os.path.exists(base_path):
            base_path = os.path.expanduser("~/.config/chromium")
    elif system == "Darwin":
        base_path = os.path.expanduser("~/Library/Application Support/Google/Chrome")
    else:
        return {"error": f"Sistema {system} no soportado"}

    if not os.path.isdir(base_path):
        return {"error": "No se encontró la carpeta de datos de Chrome"}

    profiles = []
    for profile in os.listdir(base_path):
        profile_path = os.path.join(base_path, profile)
        if not os.path.isdir(profile_path):
            continue

        # Filtrar solo perfiles estándar: "Default" y "Profile X"
        if profile != "Default" and not profile.startswith("Profile "):
            continue

        prefs_path = os.path.join(profile_path, "Preferences")
        web_data   = os.path.join(profile_path, "Web Data")
        name = profile  # Nombre base por defecto (nombre de la carpeta)
        display_name = None
        last_used = "Desconocido"
        avatar = None

        # Leer Preferences si existe para obtener nombre de perfil y last_used
        if os.path.exists(prefs_path):
            try:
                prefs = json.load(open(prefs_path, encoding="utf-8"))
                name = prefs.get("profile", {}).get("name", name)
                ts   = prefs.get("profile", {}).get("last_active_time")
                if ts:
                    # last_active_time viene en microsegundos (epoch), convertir a fecha legible
                    last_used_dt = datetime.utcfromtimestamp(int(ts)//1000000)
                    last_used = last_used_dt.strftime("%Y-%m-%d %H:%M:%S")
                # Obtener URL de avatar (imagen de perfil) si está disponible
                url = None
                account_info = prefs.get("account_info", [])
                if account_info and isinstance(account_info, list):
                    primary = account_info[0]
                    url = primary.get("picture_url")
                    display_name = (
                        primary.get("full_name")
                        or primary.get("given_name")
                        or primary.get("name")
                    )
                if url:
                    avatar = fetch_avatar_from_url(url)
            except Exception:
                pass

        # Si no hay avatar aún, intentar obtenerlo de Web Data (Chromium no almacena Preferences de la misma manera)
        if avatar is None and os.path.exists(web_data):
            try:
                conn = sqlite3.connect(web_data, timeout=5)
                cur = conn.cursor()
                cur.execute("SELECT avatar_url FROM profile_info LIMIT 1")
                row = cur.fetchone()
                conn.close()
                if row and row[0]:
                    avatar = fetch_avatar_from_url(row[0])
            except Exception:
                pass

        # Si aún no hay avatar, intentar cargar imagen local por defecto del perfil
        if avatar is None:
            avatar = encode_image_to_base64(os.path.join(profile_path, "Profile Picture.png"))

        profiles.append({
            "name": name,
            "display_name": display_name or name,
            "path": profile_path,
            "last_used": last_used,
            "avatar": avatar
        })

    return {"system": system, "profiles": profiles}

def profile_folder_from_selection(selected_profile: dict) -> str:
    """
    Dado el diccionario de un perfil devuelto por get_chrome_profiles(),
    retorna el nombre de la carpeta de dicho perfil (por ej. 'Default', 'Profile 1').
    Esto es útil si se necesita pasar solo el nombre de carpeta a otras funciones.
    """
    try:
        p = selected_profile.get("path")
        if p:
            return os.path.basename(p)
    except Exception:
        pass
    return "Default"

def extract_all_keywords(raw_text: str, top_n: int = 5) -> dict:
    """
    Extrae palabras clave de un texto usando múltiples enfoques: RAKE, KeyBERT, YAKE y spaCy.
    Retorna un diccionario con listas de keywords para cada método.
    """
    resultados = {}
    # RAKE
    try:
        rake_extractor.extract_keywords_from_text(raw_text)
        resultados["rake"] = rake_extractor.get_ranked_phrases()[:top_n]
    except Exception:
        resultados["rake"] = []
    # KeyBERT
    resultados["keybert"] = []
    if keybert_model:
        try:
            # Preprocesar texto para KeyBERT: lematizar y filtrar palabras poco útiles
            doc = spacy_nlp(raw_text)
            cleaned = " ".join(tok.lemma_.lower() for tok in doc if tok.is_alpha and not tok.is_stop)
            text_for_kb = cleaned if len(cleaned.split()) >= 50 else raw_text
            kws = keybert_model.extract_keywords(
                text_for_kb,
                keyphrase_ngram_range=(1, 2),
                stop_words="spanish",
                top_n=top_n,
                use_mmr=False
            )
            resultados["keybert"] = [kw for kw, _ in kws]
        except Exception:
            resultados["keybert"] = []
    # YAKE
    try:
        y = yake_extractor.extract_keywords(raw_text)
        resultados["yake"] = [kw for kw, _ in sorted(y, key=lambda x: x[1])[:top_n]]
    except Exception:
        resultados["yake"] = []
    # spaCy noun_chunks (frases nominales más frecuentes)
    try:
        doc = spacy_nlp(raw_text)
    except Exception:
        doc = spacy_nlp(raw_text) if spacy_nlp else []
    counts = {}
    for chunk in getattr(doc, "noun_chunks", []):
        t = chunk.text.lower().strip()
        if t:
            counts[t] = counts.get(t, 0) + 1
    resultados["spacy"] = sorted(counts, key=counts.get, reverse=True)[:top_n]
    return resultados

def get_recent_urls(profile_dir: str, limit: int = 10) -> list[dict]:
    """
    Lee hasta `limit` URLs recientes del historial de Chrome para el perfil indicado.
    `profile_dir` puede ser el **nombre de la carpeta** del perfil (p.ej. 'Default' o 'Profile 1')
    o una **ruta absoluta** al directorio del perfil.
    Retorna una lista de diccionarios con 'url' y 'title' de cada entrada.
    """
    # Determinar base de datos de historial según el sistema operativo
    system = platform.system()
    if profile_dir is None or profile_dir == "":
        profile_dir = "Default"
    # Si se proporciona una ruta absoluta de perfil, usarla directamente
    if os.path.isabs(profile_dir):
        base_dir = profile_dir
    else:
        if system == "Windows":
            base_dir = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
        elif system == "Darwin":
            base_dir = os.path.expanduser("~/Library/Application Support/Google/Chrome")
        else:  # Linux u otros (Chrome y Chromium)
            base_dir = os.path.expanduser("~/.config/google-chrome")
            if not os.path.isdir(base_dir):
                base_dir = os.path.expanduser("~/.config/chromium")
        base_dir = os.path.join(base_dir, profile_dir)
    history_file = os.path.join(base_dir, "History")
    if not os.path.isfile(history_file):
        # No se encontró el archivo de historial para ese perfil
        return []
    # Copiar el archivo de historial a una ubicación temporal para poder leerlo sin bloqueo
    profile_id = os.path.basename(base_dir) or "Default"
    tmp_history = os.path.join(tempfile.gettempdir(), f"History_{profile_id}.db")
    rows = []
    try:
        shutil.copy2(history_file, tmp_history)
        conn = sqlite3.connect(tmp_history, timeout=10)
        cur = conn.cursor()
        cur.execute(
            "SELECT DISTINCT url, title FROM urls ORDER BY last_visit_time DESC LIMIT ?",
            (limit,)
        )
        rows = cur.fetchall()
        conn.close()
    except Exception as e:
        # En caso de error, imprimir advertencia (podría añadirse logging)
        print(f"Advertencia: fallo al leer historial de Chrome - {e}")
        rows = []
    finally:
        try:
            if os.path.exists(tmp_history):
                os.remove(tmp_history)
        except Exception:
            pass
    # Devolver lista de diccionarios con URL y título
    return [{"url": u, "title": t} for u, t in rows]

def get_keywords_for_profile(profile_dir: str, limit: int = 10) -> list[dict]:
    """
    Para cada URL obtenida del perfil dado, extrae palabras clave de su título o URL.
    Retorna una lista de diccionarios con 'url' y 'keywords' (diccionario de listas por método).
    """
    entries = get_recent_urls(profile_dir, limit)
    result = []
    for e in entries:
        text = e.get("title") or e["url"]
        kws_dict = extract_all_keywords(text, top_n=5)
        result.append({
            "url": e["url"],
            "keywords": kws_dict
        })
    return result
