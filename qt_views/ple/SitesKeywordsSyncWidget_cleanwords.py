# qt_views/ple/SitesKeywordsSyncWidget.py
"""
import sys
sys.setdefaultencoding('utf-8')
"""
#import PLEView
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="ignore")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="ignore")
import json
import os
import sqlite3
import tempfile
import shutil
import requests
import re
import nltk 
from nltk.corpus import stopwords, words, cess_esp  # Requiere instalar nltk: pip install nltk
from datetime import datetime, timedelta
from collections import defaultdict
from urllib.parse import urlparse
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMainWindow,
    QMenu, QAction, QAbstractItemView, QApplication, QDialog, 
    QLineEdit, QComboBox, QDialogButtonBox, QFormLayout,
    QMessageBox, QCheckBox, QProgressBar, QFrame, QScrollArea,
    QTextEdit, QTabWidget
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QEvent, QThread, QObject
from PyQt5.QtGui import QFont, QPalette, QColor, QCursor
#from PLEView import *
"""
#from config import mi_variable_global
from PLEView import DEFAULT_PLE_USER_ID 
print(f"ID del usuario desde PLEview: '{DEFAULT_PLE_USER_ID}'")
"""

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EXPORT_DIR = PROJECT_ROOT / "ple"

#GlobalKeywords = ['maven', 'minutes', 'maven', 'maven in', '5 minutes', 'minutes –', '– maven', 'maven in 5', 'in 5 minutes', '5 minutes –']
GlobalKeywords = "something"

# Combinar stopwords en inglés y español
stop_words_en = set(stopwords.words('english'))
stop_words_es = set(stopwords.words('spanish'))
stop_words = stop_words_en.union(stop_words_es)

# Diccionarios de palabras válidas (convertidas a minúsculas para comparación)
english_words = set(word.lower() for word in words.words())  # Palabras en inglés
spanish_words = set(word.lower() for word in cess_esp.words())  # Palabras en español

# --- LISTA DE STOPWORDS EN ESPAÑOL (ampliable) ---
STOPWORDS = {
    'que', 'está', 'y', 'de', 'la', 'el', 'en', 'un', 'una', 'los', 'las', 'del',
    'al', 'por', 'con', 'para', 'es', 'son', 'como', 'se', 'su', 'lo', 'le',
    'me', 'te', 'nos', 'os', 'les', 'mi', 'tu', 'si', 'no', 'ni', 'o', 'pero',
    'porque', 'cuando', 'donde', 'cómo', 'cuál', 'qué', 'quien', 'cual', 'a',
    'ante', 'bajo', 'cabe', 'con', 'contra', 'desde', 'durante', 'en', 'entre',
    'hacia', 'hasta', 'mediante', 'para', 'según', 'sin', 'sobre', 'tras'
}

#print(PLEView.mi_variable_global) 

#**********************************************************Modificado por Equipo UAA 18-08-2025
def obtener_valor_json(archivo_json, clave):
  try:
    with open(archivo_json, 'r') as f:
      datos_json = json.load(f)
      return datos_json.get(clave) # Usa get() para evitar errores si la clave no existe
  except FileNotFoundError:
    print(f"Error: Archivo no encontrado: {archivo_json}")
    return None
  except json.JSONDecodeError:
    print(f"Error: Archivo JSON inválido: {archivo_json}")
    return None
  except Exception as e:
      print(f"Error inesperado: {e}")
      return None

directorio_actual = os.getcwd()
print(f"Directorio actual THIS FILE: {directorio_actual}")
cadenaDirPrincipal = directorio_actual
print(cadenaDirPrincipal)
"""
subcadena = "qt_views"
indice = cadenaDirPrincipal.index(subcadena)
realIndex = indice-1
print(f"La subcadena '{subcadena}' se encuentra en la posición {indice}.")
#cadena = "Python es genial"
subcadenaReal = cadenaDirPrincipal[:realIndex]  #
print(subcadenaReal)
"""
#  Ruta relativa a un archivo en un subdirectorio
ruta_relativa = "\\app\\auth\\perfil_usuario.json"
print(f"Ruta relativa: {ruta_relativa}")
finalLocation = cadenaDirPrincipal + ruta_relativa
print(f"final Location: {finalLocation}")
clave_a_extraer = 'uid'
valor = obtener_valor_json(finalLocation, clave_a_extraer)

if valor:
  print(f"El valor de '{clave_a_extraer}' es: {valor}")
else:
  print(f"No se pudo encontrar la clave '{clave_a_extraer}' en el archivo.")

userIDThisFile = valor
GOT_IT_ID = int(userIDThisFile)  
print(f"ID obtenido: {GOT_IT_ID}")
 
guardar_id_ple_path = DEFAULT_EXPORT_DIR / "guardarIDPLE.txt"
with open(guardar_id_ple_path, "r", encoding="utf-8") as archivo:
    for linea in archivo:
        # Divide la línea por el signo "=" y toma el segundo elemento (el valor)
        if "=" in linea:
            clave, valor = linea.strip().split("=")
            if clave == "pleseleccionado":
                variable_IDPLE = valor
                print(f"El ID del PLE seleccionado es: {variable_IDPLE}")
                idpleDinamico = int(variable_IDPLE) 


#*********************************************************    Modificado por Equipo UAA 18-08-2025



# NLP imports with fallbacks
try:
    from keybert import KeyBERT
    from bs4 import BeautifulSoup
    import spacy
    import nltk
    from nltk.corpus import stopwords
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False
    print("Warning: NLP libraries not available. Chrome extraction will use basic functionality only.")

class ChromeHistoryExtractor:
    """Extract Chrome history with cross-platform support."""
    
    def get_chrome_history_path(self):
        """Get Chrome history database path based on OS."""
        if os.name == 'nt':  # Windows
            chrome_path = os.path.join(os.getenv('LOCALAPPDATA'), 'Google', 'Chrome', 'User Data', 'Default', 'History')
        elif os.name == 'posix':  # macOS/Linux
            if sys.platform == 'darwin':  # macOS
                chrome_path = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'Google', 'Chrome', 'Default', 'History')
            else:  # Linux
                chrome_path = os.path.join(os.path.expanduser('~'), '.config', 'google-chrome', 'Default', 'History')
                if not os.path.exists(chrome_path):
                    chrome_path = os.path.join(os.path.expanduser('~'), '.config', 'chromium', 'Default', 'History')
        else:
            raise OSError("Unsupported operating system")
        
        if not os.path.exists(chrome_path):
            raise FileNotFoundError(f"Chrome history file not found at: {chrome_path}")
        
        return chrome_path
    
    def convert_chrome_time(self, chrome_time):
        """Convert Chrome time (microseconds since 1601-01-01) to datetime."""
        epoch_start = datetime(1601, 1, 1)
        return epoch_start + timedelta(microseconds=chrome_time)
    
    def extract_history(self, limit=100):
        """Extract Chrome history data with safety measures."""
        try:
            history_path = self.get_chrome_history_path()
            
            # Create temporary copy to avoid database lock issues
            temp_path = os.path.join(tempfile.gettempdir(), f"History_{os.getpid()}.db")
            shutil.copy2(history_path, temp_path)
            
            try:
                conn = sqlite3.connect(temp_path)
                cursor = conn.cursor()
                
                query = """
                SELECT urls.id, urls.url, urls.title, visits.visit_time, visits.visit_duration
                FROM urls
                JOIN visits ON urls.id = visits.url
                ORDER BY visits.visit_time DESC
                LIMIT ?
                """
                
                cursor.execute(query, (limit,))
                results = cursor.fetchall()
                conn.close()
                
                # Process results
                history_data = defaultdict(lambda: {
                    "urls": [], "titles": [], "visit_times": [], 
                    "end_times": [], "durations": []
                })
                
                for row in results:
                    visit_time = self.convert_chrome_time(row[3])
                    duration_seconds = row[4] / 1_000_000 if row[4] > 0 else 5
                    end_time = visit_time + timedelta(seconds=duration_seconds)
                    
                    history_data[row[0]]["urls"].append(row[1])
                    history_data[row[0]]["titles"].append(row[2] or "Sin título")
                    history_data[row[0]]["visit_times"].append(visit_time.isoformat() + "Z")
                    history_data[row[0]]["end_times"].append(end_time.isoformat() + "Z")
                    history_data[row[0]]["durations"].append(duration_seconds)
                
                # Convert to list format
                return [{"trackedDataID": tracked_id, **data} for tracked_id, data in history_data.items()]
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
        except Exception as e:
            raise Exception(f"Error extracting Chrome history: {str(e)}")

class KeywordExtractor:
    """Advanced keyword extraction with NLP support."""
    
    def __init__(self):
        self.kw_model = None
        self.nlp = None
        self.spanish_stopwords = set()
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize NLP models with graceful fallbacks."""
        if not NLP_AVAILABLE:
            self.spanish_stopwords = {'el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le'}
            return
        
        try:
            # Download stopwords if needed
            nltk.download('stopwords', quiet=True)
            self.spanish_stopwords = set(stopwords.words('spanish'))
        except:
            self.spanish_stopwords = {'el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le'}
        
        try:
            self.kw_model = KeyBERT(model="paraphrase-multilingual-MiniLM-L12-v2")
        except Exception as e:
            print(f"KeyBERT not available: {e}")
        
        try:
            self.nlp = spacy.load("es_core_news_sm")
        except:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except Exception as e:
                print(f"spaCy models not available: {e}")
    
    def extract_page_content(self, url):
        """Extract and clean content from web page."""
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = soup.title.string.strip() if soup.title else "Sin título"
            
            # Extract more comprehensive content
            content_parts = []
            
            # Extract title
            if soup.title:
                content_parts.append(soup.title.get_text(strip=True))
            
            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                content_parts.append(meta_desc.get('content'))
            
            # Extract headings (h1-h3)
            for tag in ['h1', 'h2', 'h3']:
                headings = soup.find_all(tag, limit=3)
                for heading in headings:
                    content_parts.append(heading.get_text(strip=True))
            
            # Extract main content (first 5 paragraphs)
            paragraphs = soup.find_all('p', limit=5)
            for p in paragraphs:
                content_parts.append(p.get_text(strip=True))
            
            # Extract list items
            lists = soup.find_all(['ul', 'ol'], limit=2)
            for ul in lists:
                items = ul.find_all('li', limit=3)
                for li in items:
                    content_parts.append(li.get_text(strip=True))
            
            content = " ".join(content_parts)
            
            # Clean content
            content = re.sub(r'\s+', ' ', content).strip()
            content = re.sub(r'[^\w\sáéíóúüñÁÉÍÓÚÜÑ]', '', content)
            content = content.lower()
            
            combined_text = f"{title}. {content}"
            return combined_text if len(combined_text) > 50 else "Error: Contenido insuficiente"
            
        except Exception as e:
            return f"Error al extraer contenido: {str(e)}"
    
    def clean_and_validate_keywords(self, keywords):
        """Clean and validate extracted keywords."""
        if not self.nlp:
            # Basic validation without spaCy
            validated = []
            for kw in keywords:
                kw = re.sub(r'\s+', ' ', kw).strip().lower()
                words = kw.split()
                clean_words = [w for w in words if w not in self.spanish_stopwords and len(w) > 2]
                if clean_words:
                    validated.append(" ".join(clean_words))
            return validated[:20]  # Increased from 10 to 20 keywords
        
        # Advanced validation with spaCy
        validated_keywords = []
        for kw in keywords:
            # Clean the keyword
            kw = re.sub(r'([a-záéíóúüñ])([A-ZÁÉÍÓÚÜÑ])', r'\1 \2', kw)
            kw = re.sub(r'\s+', ' ', kw).strip().lower()
            
            # Process with spaCy
            doc = self.nlp(kw)
            tokens = [token.text for token in doc if token.is_alpha and token.text.lower() not in self.spanish_stopwords]
            
            if len(tokens) >= 1:
                validated_keywords.append(" ".join(tokens))
        
        # Filter meaningful keywords
        validated_keywords = [kw for kw in validated_keywords if len(kw.split()) > 1 or len(kw) > 4]
        return validated_keywords[:20]  # Increased from 10 to 20 keywords
    
    def extract_keywords_combined(self, url):
        """Extract keywords using multiple methods and combine results."""
        all_keywords = []
        
        # Method 1: Basic URL extraction
        basic_keywords = self._basic_keyword_extraction(url)
        all_keywords.extend(basic_keywords)
        
        # Method 2: Advanced KeyBERT extraction
        content = self.extract_page_content(url)
        if not content.startswith("Error") and self.kw_model:
            try:
                keybert_keywords = self.kw_model.extract_keywords(
                    content,
                    keyphrase_ngram_range=(1, 4),
                    stop_words=list(self.spanish_stopwords),
                    use_mmr=True,
                    diversity=0.3,
                    top_n=25
                )
                keybert_list = [kw[0] for kw in keybert_keywords]
                all_keywords.extend(keybert_list)
            except Exception as e:
                print(f"KeyBERT extraction failed: {e}")
        
        # Method 3: Additional URL analysis
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            
            # Extract query parameters as keywords
            if parsed.query:
                query_params = parsed.query.split('&')
                for param in query_params[:3]:  # Limit to 3 query params
                    if '=' in param:
                        key, value = param.split('=', 1)
                        if len(value) > 2:
                            all_keywords.append(value)
            
            # Extract fragment as keyword
            if parsed.fragment and len(parsed.fragment) > 2:
                all_keywords.append(parsed.fragment)
                
        except Exception as e:
            print(f"URL analysis failed: {e}")
        
        # Remove duplicates and validate
        unique_keywords = list(dict.fromkeys(all_keywords))  # Preserve order, remove duplicates
        validated_keywords = self.clean_and_validate_keywords(unique_keywords)
        
        # Score and rank keywords by relevance
        scored_keywords = self._score_keywords(validated_keywords, url, content)
        return scored_keywords
    
    def _basic_keyword_extraction(self, url):
        """Fallback keyword extraction from URL structure."""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.replace('www.', '')
            path_parts = [part for part in parsed_url.path.split('/') if part]
            
            keywords = [domain]
            
            # Extract meaningful parts from URL path
            for part in path_parts[:5]:  # Increased from 3 to 5 path parts
                clean_part = re.sub(r'[^\w\s-]', ' ', part)
                words = [w for w in clean_part.split() if len(w) > 2 and w not in self.spanish_stopwords]
                keywords.extend(words[:3])  # Increased from 2 to 3 words per path part
            
            return keywords[:15]  # Increased from 8 to 15 keywords
        except Exception:
            return ["website"]
    
    def _score_keywords(self, keywords, url, content):
        """Score and rank keywords by relevance."""
        if not keywords:
            return keywords
        
        scored_keywords = []
        content_lower = content.lower() if content else ""
        url_lower = url.lower()
        
        for keyword in keywords:
            score = 0
            keyword_lower = keyword.lower()
            
            # Score based on frequency in content
            if content_lower:
                score += content_lower.count(keyword_lower) * 2
            
            # Score based on position in URL
            if keyword_lower in url_lower:
                score += 5
                # Higher score if in domain
                if keyword_lower in url_lower.split('/')[2]:  # Domain part
                    score += 3
            
            # Score based on keyword length (prefer meaningful length)
            if 4 <= len(keyword) <= 20:
                score += 2
            elif len(keyword) > 20:
                score += 1
            
            # Score based on word count (prefer phrases)
            word_count = len(keyword.split())
            if word_count == 2:
                score += 3  # Bigrams are often most relevant
            elif word_count == 3:
                score += 2  # Trigrams are good
            elif word_count == 1:
                score += 1  # Single words are okay
            
            # Score based on character diversity (avoid repetitive keywords)
            unique_chars = len(set(keyword_lower))
            if unique_chars > len(keyword) * 0.5:  # Good character diversity
                score += 1
            
            scored_keywords.append((keyword, score))
        
        # Sort by score (descending) and return top keywords
        scored_keywords.sort(key=lambda x: x[1], reverse=True)
        return [kw for kw, score in scored_keywords[:25]]  # Return top 25 scored keywords

class SyncWorkerThread(QThread):
    """Background thread for API synchronization."""
    
    sync_success = pyqtSignal(str)  # batch_id
    sync_error = pyqtSignal(str)    # error_message
    
    def __init__(self, payload):
        super().__init__()
        self.payload = payload
    
    def run(self):
        """Perform the actual synchronization to remote API."""
        try:
            # Debug: Print the payload (first 3 items only for brevity)
            print("🔄 Synchronizing data to API...")
            print(f"📡 API URL: https://uninovadeplan-ws.javali.pt/tracked-data-batch")
            print(f"👤 User ID: {self.payload['userID']}")
            print(f"🎯 PLE ID: {self.payload['associatedPLE']}")
            print(f"📊 Total items: {len(self.payload['trackedDataList'])}")
            
            if self.payload['trackedDataList']:
                print("📋 Sample data (first item):")
                sample_item = self.payload['trackedDataList'][0]
                print(f"   Activity Type: {sample_item['activityType']}")
                print(f"   URL: {sample_item['associatedURL']}")
                print(f"   Domains: {sample_item['associatedDomains']}")
                print(f"   Keywords: {sample_item['associatedKeywords'][:3]}...")  # Show first 3 keywords
            
            # Make POST request
            api_url = "https://uninovadeplan-ws.javali.pt/tracked-data-batch"
            headers = {
                'accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            print("🌐 Sending POST request...")
            response = requests.post(api_url, json=self.payload, headers=headers, timeout=30)
            print(f"📨 Response status: {response.status_code}")
            
            if response.status_code == 200 or response.status_code == 201:
                # Success - try to get batch info from response
                try:
                    response_data = response.json()
                    batch_id = response_data.get('trackedBatchID', 'N/A')
                    print(f"✅ Success! Batch ID: {batch_id}")
                    self.sync_success.emit(str(batch_id))
                except:
                    print("✅ Success! (No batch ID received)")
                    self.sync_success.emit("N/A")
            else:
                # API error - provide detailed debugging information
                print(f"❌ API Error: {response.status_code}")
                print(f"📨 Response headers: {dict(response.headers)}")
                print(f"📄 Response text: {response.text}")

                # Try to parse JSON error response
                try:
                    error_data = response.json()
                    print(f"🔍 Parsed error data: {error_data}")
                    if isinstance(error_data, dict):
                        error_details = error_data.get('error', response.text)
                        validation_errors = error_data.get('validation_errors', None)
                        if validation_errors:
                            print(f"⚠️  Validation errors: {validation_errors}")
                        error_msg = f"Error del servidor ({response.status_code}): {error_details}"
                        if validation_errors:
                            error_msg += f"\nErrores de validación: {validation_errors}"
                    else:
                        error_msg = f"Error del servidor ({response.status_code}): {error_data}"
                except:
                    # If response is not JSON, use raw text
                    error_msg = f"Error del servidor ({response.status_code}): {response.text[:500]}"

                self.sync_error.emit(error_msg)
                
        except requests.exceptions.Timeout:
            self.sync_error.emit("Tiempo de espera agotado. Verifique su conexión.")
        except requests.exceptions.ConnectionError:
            self.sync_error.emit("Error de conexión. Verifique su conexión a internet.")
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            self.sync_error.emit(error_msg)

class ChromeProcessingThread(QThread):
    """Background thread for processing Chrome history data."""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    item_processed = pyqtSignal(dict)
    processing_finished = pyqtSignal(dict, dict)  # sites_data, keywords_data
    error_occurred = pyqtSignal(str)
    
    def __init__(self, history_data):
        super().__init__()
        self.history_data = history_data
        self.keyword_extractor = KeywordExtractor()
    
    def run(self):
        """Process Chrome history data in background."""
        try:
            sites_data = {}
            keywords_data = {}
            total_entries = len(self.history_data)
            
            self.status_updated.emit("Procesando historial de Chrome...")
            
            for i, entry in enumerate(self.history_data):
                if not entry.get('urls'):
                    continue
                
                url = entry['urls'][0]
                title = entry['titles'][0] if entry['titles'] else "Sin título"
                
                # Update progress
                progress = int((i + 1) / total_entries * 100)
                self.progress_updated.emit(progress)
                self.status_updated.emit(f"Procesando: {url[:50]}...")
                
                # Process URL as site
                if url not in sites_data:
                    sites_data[url] = {
                        'count': 0,
                        'last_used': None,
                        'type': 'site',
                        'title': title
                    }
                
                sites_data[url]['count'] += 1
                
                # Parse visit time
                try:
                    if entry['visit_times']:
                        visit_time = datetime.fromisoformat(entry['visit_times'][0].replace('Z', ''))
                        if sites_data[url]['last_used'] is None or visit_time > sites_data[url]['last_used']:
                            sites_data[url]['last_used'] = visit_time
                except:
                    if sites_data[url]['last_used'] is None:
                        sites_data[url]['last_used'] = datetime.now()
                
                # Extract keywords
                try:
                    extracted_keywords = self.keyword_extractor.extract_keywords_combined(url)
                    
                    for keyword in extracted_keywords:
                        if keyword and len(keyword.strip()) > 2:
                            if keyword not in keywords_data:
                                keywords_data[keyword] = {
                                    'count': 0,
                                    'last_used': None,
                                    'type': 'keyword'
                                }
                            
                            keywords_data[keyword]['count'] += 1
                            
                            try:
                                if entry['visit_times']:
                                    visit_time = datetime.fromisoformat(entry['visit_times'][0].replace('Z', ''))
                                    if keywords_data[keyword]['last_used'] is None or visit_time > keywords_data[keyword]['last_used']:
                                        keywords_data[keyword]['last_used'] = visit_time
                            except:
                                if keywords_data[keyword]['last_used'] is None:
                                    keywords_data[keyword]['last_used'] = datetime.now()
                
                except Exception as e:
                    print(f"Error extracting keywords for {url}: {e}")
                
                # Emit processed item for real-time updates
                self.item_processed.emit({
                    'url': url,
                    'title': title,
                    'keywords': extracted_keywords if 'extracted_keywords' in locals() else []
                })
            
            self.processing_finished.emit(sites_data, keywords_data)
            
        except Exception as e:
            self.error_occurred.emit(str(e))

class ModernConfirmDialog(QDialog):
    """Modern styled confirmation dialog."""
    
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(450, 300)
        
        # Remove window frame for custom styling
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Main container
        main_container = QFrame(self)
        main_container.setGeometry(0, 0, 450, 300)
        main_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        layout = QVBoxLayout(main_container)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(20)
        
        # Header with icon and title
        header_layout = QHBoxLayout()
        
        # Warning icon
        icon_label = QLabel("⚠️")
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 36px;
                color: #f59e0b;
                padding: 10px;
            }
        """)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px 0;
            }
        """)
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label, 1)
        header_layout.setAlignment(icon_label, Qt.AlignTop)
        
        # Message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("""
            QLabel {
                font-size: 15px;
                color: #34495e;
                line-height: 1.5;
                padding: 15px 0;
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_button = QPushButton("Cancelar")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
                min-width: 100px;
                margin-right: 10px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #495057;
            }
        """)
        cancel_button.clicked.connect(self.reject)
        
        delete_button = QPushButton("Eliminar")
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        delete_button.clicked.connect(self.accept)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(delete_button)
        
        # Add to main layout
        layout.addLayout(header_layout)
        layout.addWidget(message_label)
        layout.addStretch()
        layout.addLayout(button_layout)
        
        # Center the dialog
        self.center_on_parent()
    
    def center_on_parent(self):
        if self.parent():
            parent_rect = self.parent().geometry()
            dialog_rect = self.geometry()
            x = parent_rect.x() + (parent_rect.width() - dialog_rect.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - dialog_rect.height()) // 2
            self.move(max(0, x), max(0, y))
        else:
            # Center on screen
            qr = self.frameGeometry()
            cp = QApplication.desktop().screen().rect().center()
            qr.moveCenter(cp)
            self.move(qr.topLeft())


class FeedbackDialog(QDialog):
    """Dialog for capturing user feedback on URLs."""

    def __init__(self, url, current_feedback=None, parent=None):
        super().__init__(parent)
        self.url = url
        self.current_feedback = current_feedback or {}

        self.setWindowTitle("Retroalimentación de URL")
        self.setModal(True)
        self.setFixedSize(580, 680)  # Slightly taller to ensure star rating section is fully visible

        # Remove window frame for custom styling
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setup_ui()
        self.apply_feedback_styles()

        # Load current feedback if exists
        if self.current_feedback:
            self.load_current_feedback()

    def setup_ui(self):
        """Setup the dialog UI."""
        # Main container with border
        main_container = QFrame(self)
        main_container.setGeometry(15, 15, 550, 650)  # Slightly taller container for star section
        main_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e5e7eb;
                /* box-shadow not supported in PyQt5 */
            }
        """)

        layout = QVBoxLayout(main_container)
        layout.setContentsMargins(24, 24, 24, 24)  # Uniform 24px padding on all sides
        layout.setSpacing(18)  # Consistent 18px spacing between sections

        # Header section with balanced space
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Icon
        icon_label = QLabel("📝")
        icon_label.setStyleSheet("""
            font-size: 32px;
            padding: 8px;
            color: #5a155b;
        """)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFixedSize(50, 50)

        # Title and subtitle with improved hierarchy
        title_container = QVBoxLayout()
        title_container.setSpacing(4)

        title_label = QLabel("Retroalimentación de URL")
        title_label.setStyleSheet("""
            font-size: 20px;
            font-weight: 600;
            color: #1f2937;
            margin: 0;
            padding: 0;
        """)

        subtitle_label = QLabel("Evalúa la utilidad de la URL y agrega un comentario opcional")
        subtitle_label.setStyleSheet("""
            font-size: 14px;
            color: #9ca3af;
            margin: 0;
            padding: 2px 0;
            font-weight: 400;
        """)
        subtitle_label.setWordWrap(True)

        title_container.addWidget(title_label)
        title_container.addWidget(subtitle_label)

        header_layout.addWidget(icon_label)
        header_layout.addLayout(title_container, 1)
        header_layout.addStretch()

        # URL display section with consistent spacing
        url_container = QVBoxLayout()
        url_container.setSpacing(8)
        url_container.setContentsMargins(0, 0, 0, 0)

        url_label = QLabel("URL a evaluar:")
        url_label.setStyleSheet("""
            font-size: 14px;
            font-weight: 500;
            color: #374151;
            margin: 0;
            padding: 4px 0;
            min-height: 20px;
        """)

        # Truncate URL better for display
        display_url = self.url
        if len(display_url) > 70:
            display_url = display_url[:35] + "..." + display_url[-35:]

        url_display = QLabel(display_url)
        url_display.setWordWrap(True)
        url_display.setMinimumHeight(40)  # Balanced height for the smaller modal
        url_display.setStyleSheet("""
            font-size: 12px;
            color: #6b7280;
            background-color: #f3f4f6;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #d1d5db;
            font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
            min-height: 25px;
            font-style: italic;
        """)
        # Make URL display appear read-only
        url_display.setEnabled(True)  # Keep enabled for tooltip
        url_display.setStyleSheet(url_display.styleSheet() + """
            QLabel:disabled {
                color: #9ca3af;
                background-color: #f9fafb;
            }
        """)
        url_display.setToolTip(self.url)  # Show full URL on hover

        url_container.addWidget(url_label)
        url_container.addWidget(url_display)

        # Score section with extra spacing for stars
        score_container = QVBoxLayout()
        score_container.setSpacing(12)
        score_container.setContentsMargins(0, 8, 0, 8)  # Add vertical margins for the star section

        score_label = QLabel("Puntuación (1-5):")
        score_label.setStyleSheet("""
            font-size: 14px;
            font-weight: 500;
            color: #374151;
            margin: 0;
            padding: 4px 0;
            min-height: 20px;
        """)

        score_help = QLabel("Evalúa la utilidad de esta URL")
        score_help.setStyleSheet("""
            font-size: 12px;
            color: #9ca3af;
            margin: 0;
            padding: 2px 0 6px 0;
            min-height: 16px;
        """)

        score_input_layout = QHBoxLayout()
        score_input_layout.setSpacing(12)
        score_input_layout.setContentsMargins(0, 5, 0, 5)  # Add padding around star container

        # Create custom star rating widget instead of combo
        self.score_widget = self.create_star_rating_widget()
        self.current_rating = 0
        score_input_layout.addWidget(self.score_widget)
        score_input_layout.addStretch()

        score_container.addWidget(score_label)
        score_container.addWidget(score_help)
        score_container.addLayout(score_input_layout)

        # Comments section with consistent spacing
        comments_container = QVBoxLayout()
        comments_container.setSpacing(8)
        comments_container.setContentsMargins(0, 0, 0, 0)

        comments_label = QLabel("Comentarios:")
        comments_label.setStyleSheet("""
            font-size: 14px;
            font-weight: 500;
            color: #374151;
            margin: 0;
            padding: 4px 0;
            min-height: 20px;
        """)

        comments_help = QLabel("Comparte tu opinión sobre esta URL (opcional)")
        comments_help.setStyleSheet("""
            font-size: 12px;
            color: #9ca3af;
            margin: 0;
            padding: 2px 0 6px 0;
            min-height: 16px;
        """)

        self.comments_text = QTextEdit()
        self.comments_text.setPlaceholderText("Comparte por qué esta URL fue útil o no…")
        self.comments_text.setFixedHeight(80)  # Optimized height for the balanced modal
        self.comments_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #d1d5db;
                border-radius: 8px;
                background-color: white;
                font-size: 14px;
                padding: 12px;
                line-height: 1.4;
                color: #374151;
            }
            QTextEdit:focus {
                border-color: #5a155b;
                outline: none;
            }
            QTextEdit:hover {
                border-color: #9ca3af;
            }
        """)

        comments_container.addWidget(comments_label)
        comments_container.addWidget(comments_help)
        comments_container.addWidget(self.comments_text)

        # Button section with balanced spacing
        button_container = QHBoxLayout()
        button_container.setSpacing(16)
        button_container.setContentsMargins(0, 8, 0, 0)
        button_container.addStretch()

        # Cancel button (first - light gray)
        cancel_button = QPushButton("❌ Cancelar")
        cancel_button.setFixedHeight(42)  # Balanced button size
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6;
                color: #6b7280;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                padding: 0px 20px;
                font-size: 14px;
                font-weight: 500;
                min-width: 110px;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
                color: #374151;
                border-color: #9ca3af;
            }
            QPushButton:pressed {
                background-color: #d1d5db;
            }
        """)
        cancel_button.clicked.connect(self.reject)

        # Clear button (middle - dark gray)
        clear_button = QPushButton("🗑️ Limpiar")
        clear_button.setFixedHeight(42)  # Balanced button size
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0px 20px;
                font-size: 14px;
                font-weight: 600;
                min-width: 110px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
            QPushButton:pressed {
                background-color: #374151;
            }
        """)
        clear_button.clicked.connect(self.clear_feedback)

        # Save button (last - purple highlighted)
        save_button = QPushButton("💾 Guardar")
        save_button.setFixedHeight(42)  # Balanced button size
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #7c3aed;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0px 20px;
                font-size: 14px;
                font-weight: 600;
                min-width: 110px;
                /* Visual feedback via border change instead */
            }
            QPushButton:hover {
                background-color: #6d28d9;
                border-width: 2px;
                margin-top: -1px;
            }
            QPushButton:pressed {
                background-color: #5b21b6;
                margin-top: 0px;
                border-width: 1px;
            }
        """)
        save_button.clicked.connect(self.accept)

        button_container.addWidget(cancel_button)
        button_container.addWidget(clear_button)
        button_container.addWidget(save_button)

        # Add all sections to main layout with consistent spacing
        layout.addLayout(header_layout)
        layout.addSpacing(20)  # Consistent space after header

        layout.addLayout(url_container)
        layout.addSpacing(18)  # Consistent space between sections

        layout.addLayout(score_container)
        layout.addSpacing(22)  # Extra space after score section to prevent overlap

        layout.addLayout(comments_container)
        layout.addSpacing(24)  # Slightly more space before buttons

        layout.addStretch()  # Push buttons to bottom
        layout.addLayout(button_container)

        # Center the dialog
        self.center_on_parent()

    def create_star_rating_widget(self):
        """Create interactive star rating widget."""
        star_container = QWidget()
        star_container.setMinimumHeight(55)  # Ensure minimum height for star container
        star_layout = QHBoxLayout(star_container)
        star_layout.setSpacing(8)
        star_layout.setContentsMargins(0, 5, 0, 5)  # Add padding inside star container

        # Create star buttons
        self.star_buttons = []
        for i in range(5):
            star_btn = QPushButton("⭐")
            star_btn.setFixedSize(40, 40)  # Balanced size for the modal width
            star_btn.setObjectName(f"star_{i}")
            star_btn.clicked.connect(lambda checked, idx=i+1: self.set_rating(idx))

            # Initial style - empty star
            star_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: 2px solid #e5e7eb;
                    border-radius: 20px;
                    font-size: 20px;
                    color: #d1d5db;
                }
                QPushButton:hover {
                    background-color: #f3f4f6;
                    border-color: #9ca3af;
                    /* hover effect via padding instead */
                }
                QPushButton:pressed {
                    /* pressed effect via padding instead */
                }
            """)

            self.star_buttons.append(star_btn)
            star_layout.addWidget(star_btn)

        # Rating label
        self.rating_label = QLabel("Sin calificación")
        self.rating_label.setMinimumHeight(25)  # Ensure minimum height for label
        self.rating_label.setStyleSheet("""
            font-size: 14px;
            color: #6b7280;
            font-weight: 500;
            padding: 5px 10px;
            margin: 2px 0;
        """)

        star_layout.addWidget(self.rating_label)
        star_layout.addStretch()

        return star_container

    def set_rating(self, rating):
        """Set the star rating and update visual feedback."""
        self.current_rating = rating

        # Rating descriptions and colors
        descriptions = {
            0: ("Sin calificación", "#6b7280"),
            1: ("Muy mala", "#ef4444"),
            2: ("Mala", "#f97316"),
            3: ("Regular", "#eab308"),
            4: ("Buena", "#22c55e"),
            5: ("Excelente", "#10b981")
        }

        # Update star buttons
        for i, star_btn in enumerate(self.star_buttons):
            if i < rating:
                # Filled star
                color = descriptions[rating][1]
                star_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color};
                        border: 2px solid {color};
                        border-radius: 20px;
                        font-size: 20px;
                        color: white;
                        /* visual depth via border instead */
                    }}
                    QPushButton:hover {{
                        /* hover effect via padding instead */
                        border-width: 3px;
                    }}
                    QPushButton:pressed {{
                        /* pressed effect via padding instead */
                    }}
                """)
            else:
                # Empty star
                star_btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        border: 2px solid #e5e7eb;
                        border-radius: 20px;
                        font-size: 20px;
                        color: #d1d5db;
                    }
                    QPushButton:hover {
                        background-color: #f3f4f6;
                        border-color: #9ca3af;
                        /* hover effect via padding instead */
                    }
                    QPushButton:pressed {
                        /* pressed effect via padding instead */
                    }
                """)

        # Update rating label
        description, color = descriptions[rating]
        self.rating_label.setText(description)
        self.rating_label.setStyleSheet(f"""
            font-size: 14px;
            color: {color};
            font-weight: 600;
            padding: 0 10px;
        """)

    def create_section_separator(self):
        """Create a subtle section separator."""
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFixedHeight(1)  # Fixed height to prevent expansion
        separator.setStyleSheet("""
            QFrame {
                border: none;
                background-color: #e5e7eb;
                margin: 0px 25px;
            }
        """)
        return separator

    def apply_feedback_styles(self):
        """Apply additional styling."""
        pass  # Styles are applied inline above

    def load_current_feedback(self):
        """Load existing feedback into the form."""
        if 'score' in self.current_feedback and self.current_feedback['score'] is not None:
            # Set star rating
            score_value = int(self.current_feedback['score'])
            self.set_rating(score_value)

        if 'comments' in self.current_feedback and self.current_feedback['comments']:
            self.comments_text.setPlainText(self.current_feedback['comments'])

    def clear_feedback(self):
        """Clear all feedback fields."""
        self.set_rating(0)  # Clear star rating
        self.comments_text.clear()

    def get_feedback_data(self):
        """Get the feedback data from the form."""
        score = None
        if self.current_rating > 0:
            score = float(self.current_rating)

        comments = self.comments_text.toPlainText().strip()
        comments = comments if comments else None

        return {
            'score': score,
            'comments': comments
        }

    def center_on_parent(self):
        """Center dialog on parent window."""
        if self.parent():
            parent_rect = self.parent().geometry()
            dialog_rect = self.geometry()
            x = parent_rect.x() + (parent_rect.width() - dialog_rect.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - dialog_rect.height()) // 2
            self.move(max(0, x), max(0, y))
        else:
            # Center on screen
            qr = self.frameGeometry()
            cp = QApplication.desktop().screen().rect().center()
            qr.moveCenter(cp)
            self.move(qr.topLeft())


class SitesKeywordsSyncWidget(QMainWindow):
    """Widget for managing synchronized sites from Chrome history."""
    
    def __init__(self, parent=None, chrome_history_path=None, user_id=1, ple_id=20, env_id=None, main_window=None):
        super().__init__(parent)
        
        # Data storage
        self.sites_data = {}
        self.keywords_data = {}
        self.all_data = {}
        self.filtered_data = {}
        self.current_page = 1
        self.items_per_page = 10
        self.total_pages = 1

        # User feedback storage
        self.user_feedback = {}  # {url: {'score': float, 'comments': str}}
        
        # API configuration - ensure these are integers
        #self.user_id = int(user_id) if user_id else GOT_IT_ID
        #self.ple_id = int(ple_id) if ple_id else idpleDinamico
        self.user_id = int(GOT_IT_ID) 
        self.ple_id = int(idpleDinamico) 
        
        
        print(f"🔧 SitesKeywordsSyncWidget initialized with:")
        print(f"   User ID: {self.user_id} (type: {type(self.user_id)})")
        print(f"   PLE ID: {self.ple_id} (type: {type(self.ple_id)})")
        
        # Store reference to main window
        self.main_window = main_window
        
        # Chrome history file path and extractors
        self.chrome_history_path = chrome_history_path or "/Users/danielmares/Downloads/EPAI UAA PT3/Generación_JSON_URLS/chrome_history.json"
        self.chrome_extractor = ChromeHistoryExtractor()
        self.processing_thread = None
        self.sync_worker = None
        
        # Configure window
        self.setWindowTitle("Sitios Web - EPAI")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        self.setup_ui()
        self.apply_styles()
        # Don't load sample data on startup - wait for user to extract from Chrome
        # self.load_data()
        
        # Initialize with empty state
        self.apply_current_filters()

        # Hide main window when this widget is shown
        print(f"[SitesKeywordsSyncWidget] main_window received: {self.main_window}")
        print(f"[SitesKeywordsSyncWidget] Attempting to hide main window...")
        if self.main_window:
            print(f"[SitesKeywordsSyncWidget] Hiding main window: {self.main_window}")
            self.main_window.hide()
            print(f"[SitesKeywordsSyncWidget] Main window hidden successfully")
        else:
            print("[SitesKeywordsSyncWidget] WARNING: main_window is None, cannot hide")
    
    def closeEvent(self, event):
        """Handle close event to show main window again."""
        self._restore_main_window()
        event.accept()
    
    def _restore_main_window(self):
        """Restore the main window visibility."""
        if self.main_window:
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()
        
    def setup_ui(self):
        """Create the UI layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        main_layout.addWidget(self.create_header())
        
        # Control bar
        main_layout.addWidget(self.create_control_bar())
        
        # Table section
        main_layout.addWidget(self.create_table_section(), 1)
        
        # Pagination
        main_layout.addWidget(self.create_pagination_bar())
        
    def create_header(self):
        """Create header with title and breadcrumb."""
        header_widget = QWidget()
        header_widget.setObjectName("syncHeaderWidget")
        
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(24, 16, 24, 16)
        header_layout.setSpacing(8)
        
        # Breadcrumb
        breadcrumb = QLabel("Inicio / Perfiles / Sitios Web / Sincronizar")
        breadcrumb.setObjectName("breadcrumb")
        header_layout.addWidget(breadcrumb)
        
        # Title bar
        title_layout = QHBoxLayout()
        
        # Back button
        back_btn = QPushButton("← Volver")
        back_btn.setObjectName("backButton")
        back_btn.clicked.connect(self.go_back)
        
        # Title
        title = QLabel("Resumen de sitios web a sincronizar")
        title.setObjectName("screenTitle")
        
        title_layout.addWidget(back_btn)
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        header_layout.addLayout(title_layout)
        
        return header_widget
        
    def create_control_bar(self):
        """Create search and filter controls."""
        control_widget = QWidget()
        control_widget.setObjectName("controlBar")
        
        # Main vertical layout
        main_layout = QVBoxLayout(control_widget)
        main_layout.setContentsMargins(20, 12, 20, 12)
        main_layout.setSpacing(10)
        
        # First row - search, display count, and filters
        first_row = QHBoxLayout()
        first_row.setSpacing(12)
        
        # Second row - action buttons
        second_row = QHBoxLayout()
        second_row.setSpacing(8)
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar sitios web...")
        self.search_input.setObjectName("searchInput")
        self.search_input.setMinimumWidth(200)
        self.search_input.setMaximumWidth(300)
        self.search_input.textChanged.connect(self.filter_data)
        
        # Display count
        self.display_combo = QComboBox()
        self.display_combo.addItems(["10", "25", "50", "100"])
        self.display_combo.setMinimumWidth(60)
        self.display_combo.setMaximumWidth(80)
        self.display_combo.currentTextChanged.connect(self.update_display_count)
        
        
        # Sort button
        self.sort_btn = QPushButton("Ordenar ▼")
        self.sort_btn.setObjectName("sortButton")
        sort_menu = QMenu()
        sort_menu.addAction("Alfabéticamente", lambda: self.sort_data('alpha'))
        sort_menu.addAction("Más utilizadas", lambda: self.sort_data('usage'))
        sort_menu.addAction("Más recientes", lambda: self.sort_data('recent'))
        self.sort_btn.setMenu(sort_menu)
        
        # Chrome extraction button
        self.extract_btn = QPushButton("🌐 Chrome")
        self.extract_btn.setObjectName("extractButton")
        self.extract_btn.setToolTip("Extraer historial de Chrome")
        self.extract_btn.clicked.connect(self.extract_from_chrome)
        
        
        # Sync button
        self.sync_btn = QPushButton("🔄 Sincronizar")
        self.sync_btn.setObjectName("syncButton")
        self.sync_btn.setToolTip("Sincronizar todos los datos")
        self.sync_btn.clicked.connect(self.sync_all_data)
        
        # First row - search and filters
        first_row.addWidget(self.search_input)
        first_row.addWidget(self.display_combo)
        
        first_row.addStretch()
        
        # Second row - action buttons
        second_row.addWidget(self.sort_btn)
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setFrameShadow(QFrame.Sunken)
        second_row.addWidget(separator2)
        
        # Action buttons
        second_row.addWidget(self.extract_btn)
        second_row.addWidget(self.sync_btn)
        second_row.addStretch()
        
        # Add rows to main layout
        main_layout.addLayout(first_row)
        main_layout.addLayout(second_row)
        
        return control_widget
        
    def create_table_section(self):
        """Create the main data table."""
        # Container for margins
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(24, 0, 24, 24)
        
        # Progress bar for Chrome extraction (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        table_layout.addWidget(self.progress_bar)
        
        # Status label for extraction progress
        self.status_label = QLabel("")
        self.status_label.setVisible(False)
        self.status_label.setObjectName("statusLabel")
        table_layout.addWidget(self.status_label)
        
        # Table widget
        self.table = QTableWidget()
        self.table.setObjectName("syncTable")
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "URL", "Título", "Última vez usado", "Veces usado", "Feedback", "Acciones"
        ])
        
        # Column configuration
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)          # URL
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # Title
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # Last used
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # Usage count
        header.setSectionResizeMode(4, QHeaderView.Fixed)            # Feedback
        header.setSectionResizeMode(5, QHeaderView.Fixed)            # Actions
        header.resizeSection(4, 120)  # Feedback column
        header.resizeSection(5, 150)  # Actions column
        
        # Table properties
        self.table.setShowGrid(False)
        self.table.setFrameShape(QTableWidget.NoFrame)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(48)
        
        table_layout.addWidget(self.table, 1)
        return table_container
        
    def create_pagination_bar(self):
        """Create pagination controls."""
        pagination_widget = QWidget()
        pagination_widget.setObjectName("paginationBar")
        
        pagination_layout = QHBoxLayout(pagination_widget)
        pagination_layout.setContentsMargins(24, 16, 24, 16)
        pagination_layout.setSpacing(8)
        
        # Info label
        self.info_label = QLabel("0 elementos encontrados")
        self.info_label.setObjectName("infoLabel")
        
        # Pagination buttons
        self.first_btn = QPushButton("Inicio")
        self.first_btn.setObjectName("pageNavButton")
        self.prev_btn = QPushButton("←")
        self.prev_btn.setObjectName("pageNavButton")
        
        # Page numbers container
        self.page_buttons_layout = QHBoxLayout()
        self.page_buttons = []
        
        self.next_btn = QPushButton("→")
        self.next_btn.setObjectName("pageNavButton")
        self.last_btn = QPushButton("Última")
        self.last_btn.setObjectName("pageNavButton")
        
        # Connect navigation
        self.first_btn.clicked.connect(lambda: self.go_to_page(1))
        self.prev_btn.clicked.connect(self.go_to_previous_page)
        self.next_btn.clicked.connect(self.go_to_next_page)
        self.last_btn.clicked.connect(lambda: self.go_to_page(self.total_pages))
        
        # Add to layout
        pagination_layout.addWidget(self.info_label)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.first_btn)
        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addLayout(self.page_buttons_layout)
        pagination_layout.addWidget(self.next_btn)
        pagination_layout.addWidget(self.last_btn)
        pagination_layout.addStretch()
        
        return pagination_widget
        
    def load_data(self):
        """Load and process data from chrome_history.json."""
        try:
            if not os.path.exists(self.chrome_history_path):
                QMessageBox.warning(self, "Archivo no encontrado", 
                                  f"No se encontró el archivo: {self.chrome_history_path}")
                return
                
            with open(self.chrome_history_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.process_tracked_data(data.get('trackedDataList', []))
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar datos: {str(e)}")
            
    def process_tracked_data(self, tracked_list):
        """Aggregate sites and keywords from tracked data."""
        self.sites_data = {}
        self.keywords_data = {}
        
        for entry in tracked_list:
            # Process URL
            url = entry.get('associatedURL', '')
            if url:
                if url not in self.sites_data:
                    self.sites_data[url] = {
                        'count': 0,
                        'last_used': None,
                        'type': 'site'
                    }
                
                self.sites_data[url]['count'] += 1
                
                # Parse end time
                try:
                    end_time_str = entry.get('endTime', '')
                    if end_time_str:
                        end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                        
                        if (self.sites_data[url]['last_used'] is None or 
                            end_time > self.sites_data[url]['last_used']):
                            self.sites_data[url]['last_used'] = end_time
                except:
                    # Fallback to current time if parsing fails
                    if self.sites_data[url]['last_used'] is None:
                        self.sites_data[url]['last_used'] = datetime.now()
            
            # Process keywords
            keywords = entry.get('associatedKeywords', [])
            for keyword in keywords:
                if keyword and len(keyword.strip()) > 2:  # Filter out very short keywords
                    if keyword not in self.keywords_data:
                        self.keywords_data[keyword] = {
                            'count': 0,
                            'last_used': None,
                            'type': 'keyword'
                        }
                    
                    self.keywords_data[keyword]['count'] += 1
                    
                    try:
                        end_time_str = entry.get('endTime', '')
                        if end_time_str:
                            end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                            
                            if (self.keywords_data[keyword]['last_used'] is None or 
                                end_time > self.keywords_data[keyword]['last_used']):
                                self.keywords_data[keyword]['last_used'] = end_time
                    except:
                        if self.keywords_data[keyword]['last_used'] is None:
                            self.keywords_data[keyword]['last_used'] = datetime.now()
        
        # Combine and display
        self.all_data = {**self.sites_data, **self.keywords_data}
        self.filtered_data = self.all_data.copy()
        self.update_pagination()
        self.update_table()
        
    def filter_data(self):
        """Filter data based on search input."""
        # Apply current filters (which includes search filtering)
        self.apply_current_filters()
        
        
    def apply_current_filters(self):
        """Apply search filtering to the data - only show sites/URLs."""
        # Start with search-filtered data
        base_data = self.get_search_filtered_data()
        
        # Only show sites/URLs
        self.filtered_data = {
            name: data for name, data in base_data.items()
            if data['type'] == 'site'
        }
        
        self.current_page = 1
        self.update_pagination()
        self.update_table()
        
    def get_search_filtered_data(self):
        """Get data filtered by search text."""
        search_text = self.search_input.text().lower()
        
        if not search_text:
            return self.all_data.copy()
        else:
            return {
                name: data for name, data in self.all_data.items()
                if search_text in name.lower()
            }
        
    def sort_data(self, sort_type):
        """Sort data by different criteria."""
        if sort_type == 'alpha':
            self.filtered_data = dict(sorted(self.filtered_data.items()))
        elif sort_type == 'usage':
            self.filtered_data = dict(sorted(
                self.filtered_data.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            ))
        elif sort_type == 'recent':
            self.filtered_data = dict(sorted(
                self.filtered_data.items(),
                key=lambda x: x[1]['last_used'] or datetime.min,
                reverse=True
            ))
        
        self.update_table()
        
    def update_display_count(self, text):
        """Update items per page."""
        try:
            self.items_per_page = int(text)
        except ValueError:
            self.items_per_page = 10
        
        self.current_page = 1
        self.update_pagination()
        self.update_table()
        
    def update_pagination(self):
        """Update pagination controls."""
        total_items = len(self.filtered_data)
        self.total_pages = max(1, (total_items + self.items_per_page - 1) // self.items_per_page)
        
        # Update info label
        start_item = (self.current_page - 1) * self.items_per_page + 1
        end_item = min(self.current_page * self.items_per_page, total_items)
        
        if total_items > 0:
            self.info_label.setText(f"Mostrando {start_item}-{end_item} de {total_items} elementos")
        else:
            self.info_label.setText("0 elementos encontrados")
        
        # Update page buttons
        self.update_page_buttons()
        
        # Enable/disable navigation buttons
        self.first_btn.setEnabled(self.current_page > 1)
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < self.total_pages)
        self.last_btn.setEnabled(self.current_page < self.total_pages)
        
    def update_page_buttons(self):
        """Update page number buttons."""
        # Clear existing buttons
        for btn in self.page_buttons:
            btn.setParent(None)
        self.page_buttons.clear()
        
        # Create new buttons (show max 5 pages around current)
        start_page = max(1, self.current_page - 2)
        end_page = min(self.total_pages, start_page + 4)
        
        for page in range(start_page, end_page + 1):
            btn = QPushButton(str(page))
            btn.setObjectName("pageButton")
            btn.setCheckable(True)
            btn.setChecked(page == self.current_page)
            btn.clicked.connect(lambda checked, p=page: self.go_to_page(p))
            
            self.page_buttons.append(btn)
            self.page_buttons_layout.addWidget(btn)
            
    def go_to_page(self, page):
        """Navigate to specific page."""
        if 1 <= page <= self.total_pages:
            self.current_page = page
            self.update_pagination()
            self.update_table()
            
    def go_to_previous_page(self):
        """Go to previous page."""
        if self.current_page > 1:
            self.go_to_page(self.current_page - 1)
            
    def go_to_next_page(self):
        """Go to next page."""
        if self.current_page < self.total_pages:
            self.go_to_page(self.current_page + 1)
            
    def update_table(self):
        """Update table with current filtered data - only URLs."""
        self.table.setRowCount(0)
        
        # Get current page items - only show sites/URLs
        start_idx = (self.current_page - 1) * self.items_per_page
        end_idx = start_idx + self.items_per_page
        
        # Filter to only show sites (URLs)
        sites_only = {k: v for k, v in self.filtered_data.items() if v.get('type') == 'site'}
        items = list(sites_only.items())
        display_items = items[start_idx:end_idx]
        
        # Populate table
        for idx, (item_name, item_data) in enumerate(display_items):
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # URL (truncate if too long)
            url_text = item_name[:80] + "..." if len(item_name) > 80 else item_name
            url_item = QTableWidgetItem(url_text)
            url_item.setFlags(url_item.flags() & ~Qt.ItemIsEditable)
            url_item.setToolTip(item_name)  # Show full URL in tooltip
            self.table.setItem(row, 0, url_item)
            
            # Title
            title_item = QTableWidgetItem(item_data.get('title', 'N/A'))
            title_item.setFlags(title_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, title_item)
            
            # Last used
            if item_data['last_used']:
                last_used = item_data['last_used'].strftime("%d/%m/%Y %H:%M")
            else:
                last_used = "N/A"
            last_used_item = QTableWidgetItem(last_used)
            last_used_item.setFlags(last_used_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 2, last_used_item)
            
            # Usage count
            count_item = QTableWidgetItem(str(item_data['count']))
            count_item.setFlags(count_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 3, count_item)

            # Feedback column
            feedback_widget = self.create_feedback_widget(item_name)
            self.table.setCellWidget(row, 4, feedback_widget)

            # Actions column
            actions_widget = self.create_actions_widget(item_name)
            self.table.setCellWidget(row, 5, actions_widget)
            
        
    def delete_item(self, item_name):
        """Delete an item from the data."""
        # Truncate long item names for display
        display_name = item_name[:50] + "..." if len(item_name) > 50 else item_name
        
        dialog = ModernConfirmDialog(
            "Confirmar eliminación",
            f"¿Está seguro de que desea eliminar el siguiente elemento?\n\n{display_name}\n\nEsta acción no se puede deshacer.",
            self
        )
        
        if dialog.exec_() == QDialog.Accepted:
            # Remove from appropriate dictionary
            if item_name in self.sites_data:
                del self.sites_data[item_name]
            if item_name in self.keywords_data:
                del self.keywords_data[item_name]
            
            # Update display
            self.all_data = {**self.sites_data, **self.keywords_data}
            self.apply_current_filters()
            
    def extract_from_chrome(self):
        """Extract data directly from Chrome browser history."""
        try:
            # Show progress indicators
            self.progress_bar.setVisible(True)
            self.status_label.setVisible(True)
            self.progress_bar.setValue(0)
            self.status_label.setText("Conectando a Chrome...")
            
            # Disable extraction button
            self.extract_btn.setEnabled(False)
            
            # Extract raw history data
            raw_history = self.chrome_extractor.extract_history(limit=100)
            
            if not raw_history:
                QMessageBox.warning(self, "Sin datos", "No se encontraron datos en el historial de Chrome.")
                self._hide_progress_indicators()
                return
            
            # Process data in background thread
            self.processing_thread = ChromeProcessingThread(raw_history)
            self.processing_thread.progress_updated.connect(self.progress_bar.setValue)
            self.processing_thread.status_updated.connect(self.status_label.setText)
            self.processing_thread.item_processed.connect(self.on_item_processed)
            self.processing_thread.processing_finished.connect(self.on_chrome_processing_finished)
            self.processing_thread.error_occurred.connect(self.on_processing_error)
            
            self.processing_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error accediendo a Chrome: {str(e)}")
            self._hide_progress_indicators()
    
    def on_item_processed(self, item_data):
        """Handle real-time item processing updates."""
        # Could show real-time updates in status if needed
        pass
    
    def on_chrome_processing_finished(self, sites_data, keywords_data):
        """Handle completion of Chrome data processing."""
        # Merge with existing data
        self.sites_data.update(sites_data)
        self.keywords_data.update(keywords_data)
        
        # Update display
        self.all_data = {**self.sites_data, **self.keywords_data}
        self.apply_current_filters()
        
        # Hide progress indicators
        self._hide_progress_indicators()
        
        # Show success message
        total_items = len(sites_data) + len(keywords_data)
        QMessageBox.information(
            self, 
            "Extracción completada", 
            f"Se extrajeron {len(sites_data)} sitios del historial de Chrome."
        )
    
    def on_processing_error(self, error_msg):
        """Handle processing errors."""
        self._hide_progress_indicators()
        QMessageBox.critical(self, "Error de procesamiento", f"Error: {error_msg}")
    
    def _hide_progress_indicators(self):
        """Hide progress bar and status label."""
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)
        self.extract_btn.setEnabled(True)
    

    def sync_all_data(self):
        """Synchronize all data to remote server."""
        # Prepare data for API
        all_data = {**self.sites_data, **self.keywords_data}
        
        if not all_data:
            QMessageBox.warning(self, "Sin datos", "No hay datos para sincronizar.")
            return
        
        # Build tracked data list according to API specification
        tracked_data_list = []
        
        for item_name, item_data in all_data.items():
            # Skip items that are keywords without valid URLs or example URLs
            if item_data['type'] == 'keyword':
                continue  # Skip keywords - only process actual URLs

            # Validate URL to exclude example.com and invalid URLs
            if not self._is_valid_url_for_sync(item_name):
                continue  # Skip invalid or example URLs

            # Determine activity type
            activity_type = self._get_activity_type_for_sync(item_name, item_data)

            # Extract domains from URL or use keywords
            domains = self._extract_domains(item_name, item_data)

            # Extract keywords
            keywords = self._extract_keywords_for_sync(item_name, item_data)
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
            #lista = ['maven', 'minutes', 'maven', 'maven', 'in', 'minutes', 'minutes', 'maven', 'maven', 'in', 'in', 'minutes', 'minutes']
            lista_sin_repetidos = list(dict.fromkeys(palabras_limpias))
            print("Lista limpia hasta el momento")
            print(lista_sin_repetidos)
            
            # --- FILTRAR STOPWORDS ---
            lista_final = [palabra for palabra in lista_sin_repetidos if palabra not in STOPWORDS]

            print("\nLista FINAL sin stopwords:")
            print(lista_final)
            
            """
            resultados_limpios = []
            for i, conjunto in enumerate(lista_final):
                limpio = limpiar_conjunto(conjunto)
                resultados_limpios.append(limpio)
            """
            
            
            """
            for palabra in palabras_limpias:
                palabras_semifinal.extend(self.es_palabra_valida(palabra)) 
            """    
                
            """    
                if palabra.lower() not in stop_words and self.es_palabra_valida(palabra):
                    return palabra
            # Si no hay palabras válidas no-stopwords, devolver None
            return None
            """
                        
            #print("Resultado final hasta el momento (palabras_semifinal)")
            #print(palabras_semifinal)
                        
            # Validate extracted data
            if not self._validate_keywords_for_api(keywords):
                print(f"⚠️  Invalid keywords for {item_name}: {keywords}")
                keywords = ["Web Content"]  # Fallback keywords

            if not self._validate_domains_for_api(domains):
                print(f"⚠️  Invalid domains for {item_name}: {domains}")
                domains = ["General"]  # Fallback domain

            # Set times (use last_used or current time)
            start_time = item_data.get('last_used', datetime.now())
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', ''))
            elif start_time is None:
                start_time = datetime.now()

            end_time = start_time + timedelta(minutes=5)  # Assume 5-minute sessions

            # Get feedback data
            feedback_data = self._get_user_feedback(item_name)
            
            # Ensure feedback is always an object (never None)
            if feedback_data is None:
                feedback_data = {
                    "score": None,
                    "comments": None
                }
            
            tracked_item = {
                "activityType": activity_type,
                "associatedURL": item_name,  # Only use real URLs, never example.com
                "associatedDomains": domains,
                "associatedKeywords": lista_final, # Antes keywords
                "startTime": start_time.isoformat() + "Z",
                "endTime": end_time.isoformat() + "Z",
                "feedback": feedback_data
            }
            
            # Validate the tracked item before adding to list
            if self._validate_tracked_item(tracked_item):
                tracked_data_list.append(tracked_item)
            else:
                print(f"⚠️  Skipping invalid tracked item: {item_name}")
               
        # Check if we have any valid data to send
        if not tracked_data_list:
            QMessageBox.warning(self, "Sin datos válidos", "No se encontraron datos válidos para sincronizar.")
            return
        
        # Prepare final payload
        payload = {
            "userID": self.user_id,
            "associatedPLE": self.ple_id,
            "trackedDataList": tracked_data_list
        }

        # Validate payload structure before sending
        print("🔍 Validating final payload...")
        print(f"   User ID: {payload['userID']} (type: {type(payload['userID'])})")
        print(f"   PLE ID: {payload['associatedPLE']} (type: {type(payload['associatedPLE'])})")
        print(f"   Tracked Data List count: {len(payload['trackedDataList'])}")
        
        # Debug first few items in detail
        if payload['trackedDataList']:
            print("🔍 Detailed validation of first 3 items:")
            for i, item in enumerate(payload['trackedDataList'][:3]):
                print(f"   Item {i+1}:")
                print(f"     Activity Type: {item.get('activityType')} (type: {type(item.get('activityType'))})")
                print(f"     URL: {item.get('associatedURL')} (type: {type(item.get('associatedURL'))})")
                print(f"     Domains: {item.get('associatedDomains')} (type: {type(item.get('associatedDomains'))})")
                print(f"     Keywords: {item.get('associatedKeywords')} (type: {type(item.get('associatedKeywords'))})")
                print(f"     Start Time: {item.get('startTime')} (type: {type(item.get('startTime'))})")
                print(f"     End Time: {item.get('endTime')} (type: {type(item.get('endTime'))})")
                print(f"     Feedback: {item.get('feedback')} (type: {type(item.get('feedback'))})")

        # Validate required fields
        if not payload['userID'] or not str(payload['userID']).strip():
            QMessageBox.warning(self, "Error de validación", "ID de usuario no válido")
            self.hide_sync_overlay()
            return

        if not payload['associatedPLE'] or not str(payload['associatedPLE']).strip():
            QMessageBox.warning(self, "Error de validación", "ID de PLE no válido")
            self.hide_sync_overlay()
            return

        if not payload['trackedDataList']:
            QMessageBox.warning(self, "Error de validación", "No hay datos válidos para sincronizar")
            self.hide_sync_overlay()
            return

        # Test JSON serialization to catch any data issues
        try:
            import json
            test_json = json.dumps(payload, ensure_ascii=False, indent=2)
            print("✅ Payload JSON serialization successful")
        except Exception as e:
            print(f"❌ JSON serialization failed: {e}")
            QMessageBox.critical(self, "Error de datos", f"Los datos no se pueden serializar: {str(e)}")
            self.hide_sync_overlay()
            return

        # Show sync overlay
        self.show_sync_overlay()
        
        # Create and start sync worker thread
        self.sync_worker = SyncWorkerThread(payload)
        self.sync_worker.sync_success.connect(self.on_sync_success)
        self.sync_worker.sync_error.connect(self.on_sync_error)
        self.sync_worker.start()
        print(f"🚀 Sync worker started with payload containing {len(tracked_data_list)} items")
     
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
    """
    # Función para verificar si una palabra es válida en inglés o español
    def es_palabra_valida(self,palabra):
        return palabra.lower() in english_words or palabra.lower() in spanish_words        
    """
    
    def _get_activity_type_for_sync(self, item_name, item_data):
        """Get activity type for sync API."""
        if item_data['type'] == 'keyword':
            return "article"  # Default for keywords
        
        # URL-based detection
        url_lower = item_name.lower()
        if any(vid in url_lower for vid in ['youtube.com', 'vimeo.com', 'dailymotion.com']):
            return "video"
        elif any(pod in url_lower for pod in ['spotify.com', 'soundcloud.com', 'podcast']):
            return "podcast"
        elif any(art in url_lower for art in ['medium.com', 'wikipedia.org', 'blog', 'article']):
            return "article"
        else:
            return "article"  # Default
    
    def _extract_domains(self, item_name, item_data):
        """Extract relevant domains for the item."""
        if item_data['type'] == 'keyword':
            # For keywords, infer domain from the keyword itself
            keyword = item_name.lower()
            if any(tech in keyword for tech in ['python', 'javascript', 'programming', 'code', 'java', 'maven', 'oracle', 'apache']):
                return ["Technology", "Programming"]
            elif any(ai in keyword for ai in ['ai', 'machine learning', 'neural', 'deep learning', 'federated learning']):
                return ["AI", "Data Science"]
            elif any(clim in keyword for clim in ['climate', 'change', 'planet', 'save', 'global']):
                return ["Environment"]
            elif any(edu in keyword for edu in ['education', 'learning', 'course', 'tutorial']):
                return ["Education"]
            else:
                return ["General Knowledge"]
        else:
            # For URLs, extract domain and categorize
            try:
                from urllib.parse import urlparse
                parsed = urlparse(item_name)
                domain = parsed.netloc.replace('www.', '')
                
                # Categorize by domain
                if 'youtube.com' in domain or 'video' in domain:
                    return ["Technology", "Video Content"]
                elif 'wikipedia.org' in domain:
                    return ["Education", "Reference"]
                elif 'github.com' in domain:
                    return ["Technology", "Programming"]
                elif 'oracle.com' in domain:
                    return ["Database", "Software"]
                elif 'apache.org' in domain:
                    return ["Servidor", "Mutiplataforma"]                    
                elif any(news in domain for news in ['news', 'bbc', 'cnn', 'reuters']):
                    return ["News", "Current Events"]
                else:
                    return ["Web Content", "General"]
            except:
                return ["Web Content"]
    
    def _extract_keywords_for_sync(self, item_name, item_data):
        """Extract keywords for sync API."""
        if item_data['type'] == 'keyword':
            return [item_name]
        else:
            # For URLs, extract keywords from title or URL
            title = item_data.get('title', '')
            if title and title != 'Sin título':
                # Enhanced keyword extraction from title
                words = title.lower().split()
                keywords = [word.strip('.,!?;:') for word in words if len(word) > 2]  # Reduced from 3 to 2
                
                # Add bigrams and trigrams from title
                for i in range(len(words) - 1):
                    bigram = f"{words[i]} {words[i+1]}"
                    if len(bigram) > 5:  # Meaningful bigrams
                        keywords.append(bigram)
                
                for i in range(len(words) - 2):
                    trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
                    if len(trigram) > 8:  # Meaningful trigrams
                        keywords.append(trigram)
                
                return keywords[:10]  # Increased from 5 to 10 keywords
            else:
                # Enhanced extraction from URL path
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(item_name)
                    path_parts = [part for part in parsed.path.split('/') if part and len(part) > 1]  # Reduced from 2 to 1
                    
                    # Extract domain keywords too
                    domain_parts = parsed.netloc.replace('www.', '').split('.')
                    keywords = domain_parts[:2]  # Add domain parts
                    
                    # Add path parts
                    keywords.extend(path_parts[:5])  # Increased from 3 to 5
                    
                    # Add subdomain if present
                    if '.' in parsed.netloc and not parsed.netloc.startswith('www.'):
                        subdomain = parsed.netloc.split('.')[0]
                        if len(subdomain) > 2:
                            keywords.append(subdomain)
                    
                    return keywords[:8]  # Increased from 3 to 8 keywords
                except:
                    return ["Web Content"]

    def _is_valid_url_for_sync(self, url):
        """Validate URL to exclude example.com and other invalid URLs."""
        if not url or not isinstance(url, str):
            return False

        url_lower = url.lower()

        # Exclude example domains and invalid URLs
        invalid_patterns = [
            'example.com',
            'example.org',
            'example.net',
            'localhost',
            '127.0.0.1',
            'test.com',
            'sample.com',
            'demo.com'
        ]

        # Check if URL contains any invalid pattern
        for pattern in invalid_patterns:
            if pattern in url_lower:
                print(f"🚫 Skipping invalid URL: {url} (contains {pattern})")
                return False

        # Must start with http:// or https://
        if not (url_lower.startswith('http://') or url_lower.startswith('https://')):
            print(f"🚫 Skipping invalid URL format: {url}")
            return False

        # Additional validation - must have valid domain structure
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            if not parsed.netloc or len(parsed.netloc) < 4:
                print(f"🚫 Skipping URL with invalid domain: {url}")
                return False
        except:
            print(f"🚫 Skipping URL that failed parsing: {url}")
            return False

        return True

    def _validate_keywords(self, keywords):
        """Validate and clean keywords list."""
        if not keywords:
            return []

        clean_keywords = []
        for keyword in keywords:
            if keyword and isinstance(keyword, str):
                clean_kw = keyword.strip()
                if len(clean_kw) > 0 and len(clean_kw) <= 100:  # Reasonable length limit
                    clean_keywords.append(clean_kw)

        # Ensure we don't send too many keywords
        return clean_keywords[:10]

    def _validate_domains(self, domains):
        """Validate and clean domains list."""
        if not domains:
            return ["General"]  # Default domain if none provided

        clean_domains = []
        for domain in domains:
            if domain and isinstance(domain, str):
                clean_domain = domain.strip()
                if len(clean_domain) > 0 and len(clean_domain) <= 50:
                    clean_domains.append(clean_domain)

        # Ensure we have at least one domain and not too many
        if not clean_domains:
            clean_domains = ["General"]

        return clean_domains[:5]

    def _get_user_feedback(self, url):
        """Get user feedback for a URL, returns None if no feedback provided."""
        if url in self.user_feedback:
            feedback = self.user_feedback[url]
            # Ensure feedback has valid values
            score = feedback.get('score')
            comments = feedback.get('comments')
            
            # Only return feedback if we have meaningful data
            if score is not None or (comments and comments.strip()):
                return {
                    "score": float(score) if score is not None else None,
                    "comments": comments.strip() if comments else None
                }
        return None

    def _validate_keywords_for_api(self, keywords):
        """Validate keywords list for API compatibility."""
        if not isinstance(keywords, list):
            return False

        # Check if all keywords are strings and not empty
        for keyword in keywords:
            if not isinstance(keyword, str) or not keyword.strip():
                return False
            # Check for reasonable length
            if len(keyword) > 100:  # Arbitrary max length
                return False

        # Check reasonable number of keywords
        if len(keywords) > 20:  # Limit to 20 keywords max
            return False

        return True

    def _validate_domains_for_api(self, domains):
        """Validate domains list for API compatibility - updated for category domains."""
        if not isinstance(domains, list):
            return False

        # Check if all domains are strings and not empty
        for domain in domains:
            if not isinstance(domain, str) or not domain.strip():
                return False
            # Updated validation - domains can be categories like "General", "Technology", etc.
            # or actual domain names like "example.com"
            if len(domain) < 1 or len(domain) > 255:
                return False

        return True

    def _validate_tracked_item(self, item):
        """Validate a tracked data item against API requirements."""
        try:
            # Check required fields
            if not item.get("activityType") or not isinstance(item["activityType"], str):
                print(f"   ❌ Invalid activityType: {item.get('activityType')}")
                return False
            
            if not item.get("associatedURL") or not isinstance(item["associatedURL"], str):
                print(f"   ❌ Invalid associatedURL: {item.get('associatedURL')}")
                return False
            
            if not item.get("associatedDomains") or not isinstance(item["associatedDomains"], list):
                print(f"   ❌ Invalid associatedDomains: {item.get('associatedDomains')}")
                return False
            
            if not item.get("associatedKeywords") or not isinstance(item["associatedKeywords"], list):
                print(f"   ❌ Invalid associatedKeywords: {item.get('associatedKeywords')}")
                return False
            
            if not item.get("startTime") or not isinstance(item["startTime"], str):
                print(f"   ❌ Invalid startTime: {item.get('startTime')}")
                return False
            
            if not item.get("endTime") or not isinstance(item["endTime"], str):
                print(f"   ❌ Invalid endTime: {item.get('endTime')}")
                return False
            
            # Check feedback structure
            feedback = item.get("feedback")
            if feedback is not None:
                if not isinstance(feedback, dict):
                    print(f"   ❌ Invalid feedback type: {type(feedback)}")
                    return False
                
                # Check feedback fields if present
                if "score" in feedback and feedback["score"] is not None:
                    if not isinstance(feedback["score"], (int, float)):
                        print(f"   ❌ Invalid feedback score type: {type(feedback['score'])}")
                        return False
                
                if "comments" in feedback and feedback["comments"] is not None:
                    if not isinstance(feedback["comments"], str):
                        print(f"   ❌ Invalid feedback comments type: {type(feedback['comments'])}")
                        return False
            
            return True
            
        except Exception as e:
            print(f"   ❌ Validation error: {e}")
            return False

    def create_feedback_widget(self, url):
        """Create feedback display/edit widget for table."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Feedback button
        feedback_btn = QPushButton("📝")
        feedback_btn.setObjectName("feedbackButton")
        feedback_btn.setToolTip("Agregar retroalimentación")
        feedback_btn.setMaximumSize(30, 30)
        feedback_btn.clicked.connect(lambda: self.open_feedback_dialog(url))

        # Status indicator
        status_label = QLabel()
        if url in self.user_feedback:
            status_label.setText("✅")
            status_label.setToolTip(f"Score: {self.user_feedback[url].get('score', 'N/A')}")
        else:
            status_label.setText("⚪")
            status_label.setToolTip("Sin retroalimentación")
        status_label.setMaximumSize(20, 20)

        layout.addWidget(feedback_btn)
        layout.addWidget(status_label)
        layout.addStretch()

        return container

    def create_actions_widget(self, url):
        """Create actions widget for table."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Delete button
        delete_btn = QPushButton("Eliminar")
        delete_btn.setObjectName("deleteButton")
        delete_btn.clicked.connect(lambda: self.delete_item(url))

        layout.addWidget(delete_btn)
        layout.addStretch()

        return container

    def open_feedback_dialog(self, url):
        """Open feedback dialog for a specific URL."""
        dialog = FeedbackDialog(url, self.user_feedback.get(url, {}), self)
        if dialog.exec_() == QDialog.Accepted:
            feedback_data = dialog.get_feedback_data()
            if feedback_data['score'] is not None or feedback_data['comments']:
                self.user_feedback[url] = feedback_data
            elif url in self.user_feedback:
                # Remove feedback if both fields are empty
                del self.user_feedback[url]

            # Refresh table to update feedback indicators
            self.update_table()

    def on_sync_success(self, batch_id):
        """Handle successful synchronization (called from worker thread via signal)."""
        if hasattr(self, 'sync_overlay') and self.sync_overlay.isVisible():
            self.sync_complete(batch_id)
    
    def on_sync_error(self, error_message):
        """Handle synchronization error (called from worker thread via signal)."""
        if hasattr(self, 'sync_overlay') and self.sync_overlay.isVisible():
            self.sync_overlay.hide()
        
        # Show error dialog
        QMessageBox.critical(
            self, 
            "Error de Sincronización", 
            f"No se pudieron sincronizar los datos:\n\n{error_message}"
        )
        
    def show_sync_overlay(self):
        """Show synchronization progress overlay."""
        # Create overlay
        self.sync_overlay = QWidget(self)
        self.sync_overlay.setObjectName("syncOverlay")
        self.sync_overlay.resize(self.size())
        self.sync_overlay.move(0, 0)
        
        # Center content
        content = QWidget(self.sync_overlay)
        content.setObjectName("syncContent")
        content.setFixedSize(300, 150)
        
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(16)
        
        # Progress bar
        progress = QProgressBar()
        progress.setRange(0, 0)  # Indeterminate
        
        # Status label
        status_label = QLabel("Sincronizando datos...")
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setObjectName("syncStatusLabel")
        
        content_layout.addWidget(status_label)
        content_layout.addWidget(progress)
        
        # Center the content
        content.move(
            (self.width() - content.width()) // 2,
            (self.height() - content.height()) // 2
        )
        
        self.sync_overlay.show()
    
    def hide_sync_overlay(self):
        """Hide the synchronization progress overlay."""
        if hasattr(self, 'sync_overlay') and self.sync_overlay.isVisible():
            self.sync_overlay.hide()
        
    def sync_complete(self, batch_id=None):
        """Handle sync completion."""
        # Update overlay to show success
        content = self.sync_overlay.findChild(QWidget, "syncContent")
        layout = content.layout()
        
        # Clear current widgets
        while layout.count():
            layout.takeAt(0).widget().deleteLater()
        
        # Success message
        success_icon = QLabel("✅")
        success_icon.setStyleSheet("font-size: 48px; color: #4CAF50;") #Antes 48px;
        success_icon.setAlignment(Qt.AlignCenter)
        #label1 = Label(root, text="Etiqueta con tamaño específico", width=20, height=2)
        
        success_label = QLabel("¡Sincronización Exitosa!")
        success_label.setAlignment(Qt.AlignCenter)
        success_label.setObjectName("syncSuccessLabel")
        
        # Show count of synchronized items
        total_items = len(self.sites_data) + len(self.keywords_data)
        count_label = QLabel(f"Se sincronizaron {total_items} elementos con el servidor")
        count_label.setAlignment(Qt.AlignCenter)
        count_label.setStyleSheet("font-size: 7px; color: #6b7280; margin-top: 8px;") #antes font-size: 14px
        
        # Show batch ID if available
        if batch_id:
            batch_label = QLabel(f"ID de lote: {batch_id}")
            batch_label.setAlignment(Qt.AlignCenter)
            batch_label.setStyleSheet("font-size: 7px; color: #9ca3af; margin-top: 4px; font-family: monospace;")  #antes font-size: 12px
        
        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("syncOkButton")
        ok_btn.clicked.connect(lambda: self.sync_overlay.hide())
        
        layout.addWidget(success_icon)
        layout.addWidget(success_label)
        layout.addWidget(count_label)
        if batch_id:
            layout.addWidget(batch_label)
        layout.addWidget(ok_btn)
        
        # Auto-hide after 5 seconds (increased to read batch ID)
        QTimer.singleShot(5000, self.sync_overlay.hide)
        
    def go_back(self):
        """Handle back button click."""
        self._restore_main_window()
        self.close()
        
    def resizeEvent(self, event):
        """Handle window resize."""
        super().resizeEvent(event)
        
        # Update overlay size if it exists
        if hasattr(self, 'sync_overlay') and self.sync_overlay.isVisible():
            self.sync_overlay.resize(self.size())
            content = self.sync_overlay.findChild(QWidget, "syncContent")
            if content:
                content.move(
                    (self.width() - content.width()) // 2,
                    (self.height() - content.height()) // 2
                )

    def apply_styles(self):
        """Apply styling to match EPAI design."""
        self.setStyleSheet("""
            /* Global - Specific to this widget */
            SitesKeywordsSyncWidget {
                background-color: #f9fafb;
            }
            
            SitesKeywordsSyncWidget QWidget {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                color: #111827;
            }
            
            /* Header - More specific selectors */
            SitesKeywordsSyncWidget QWidget#syncHeaderWidget {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #5a155b, stop: 1 #8b5cf6);
                border-bottom: 1px solid #e5e7eb;
                margin: 0px;
                padding: 0px;
            }
            
            SitesKeywordsSyncWidget QLabel#breadcrumb {
                color: rgba(255, 255, 255, 0.8);
                font-size: 12px;
                font-weight: 400;
                background: transparent;
                border: none;
                margin: 0px;
                padding: 4px 0px;
            }
            
            SitesKeywordsSyncWidget QLabel#screenTitle {
                color: white;
                font-size: 20px;
                font-weight: 600;
                background: transparent;
                border: none;
                margin: 4px 0px;
                padding: 0px;
            }
            
            SitesKeywordsSyncWidget QPushButton#backButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 14px;
                margin: 0px;
            }
            
            SitesKeywordsSyncWidget QPushButton#backButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
            
            /* Control Bar */
            SitesKeywordsSyncWidget QWidget#controlBar {
                background-color: white;
                border-bottom: 1px solid #e5e7eb;
                margin: 0px;
                padding: 0px;
            }
            
            SitesKeywordsSyncWidget QLineEdit#searchInput {
                padding: 8px 12px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                background-color: white;
                font-size: 14px;
                min-width: 250px;
                margin: 0px;
            }
            
            SitesKeywordsSyncWidget QLineEdit#searchInput:focus {
                border-color: #5a155b;
                outline: none;
            }
            
            /* Quantity Selector (Display Combo) */
            SitesKeywordsSyncWidget QComboBox {
                background-color: white;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                color: #374151;
                min-width: 180px;
                margin: 0px;
            }
            
            SitesKeywordsSyncWidget QComboBox:hover {
                border-color: #9ca3af;
                background-color: #f9fafb;
            }
            
            SitesKeywordsSyncWidget QComboBox:focus {
                border-color: #5a155b;
                outline: none;
            }
            
            SitesKeywordsSyncWidget QComboBox::drop-down {
                border: none;
                width: 20px;
                margin-right: 4px;
            }
            
            SitesKeywordsSyncWidget QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #6b7280;
                width: 0px;
                height: 0px;
            }
            
            SitesKeywordsSyncWidget QComboBox::down-arrow:hover {
                border-top-color: #5a155b;
            }
            
            SitesKeywordsSyncWidget QComboBox QAbstractItemView {
                background-color: white;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                outline: none;
                selection-background-color: rgba(90, 21, 91, 0.1);
                selection-color: #5a155b;
                padding: 4px;
            }
            
            SitesKeywordsSyncWidget QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                border: none;
                min-height: 20px;
            }
            
            SitesKeywordsSyncWidget QComboBox QAbstractItemView::item:hover {
                background-color: rgba(90, 21, 91, 0.05);
                color: #5a155b;
            }
            
            SitesKeywordsSyncWidget QComboBox QAbstractItemView::item:selected {
                background-color: rgba(90, 21, 91, 0.1);
                color: #5a155b;
            }
            
            SitesKeywordsSyncWidget QCheckBox {
                font-size: 14px;
                padding: 4px;
            }
            
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            
            QCheckBox::indicator:unchecked {
                border: 1px solid #d1d5db;
                border-radius: 3px;
                background-color: white;
            }
            
            QCheckBox::indicator:checked {
                border: 1px solid #5a155b;
                background-color: #5a155b;
                border-radius: 3px;
            }
            
            /* Buttons */
            
            QPushButton#extractButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 12px;
                font-weight: 600;
                font-size: 13px;
                margin: 0 2px;
                min-width: 85px;
                border: 2px solid transparent;
            }
            
            QPushButton#extractButton:hover {
                background-color: #2563eb;
                border: 2px solid #1d4ed8;
            }
            
            QPushButton#extractButton:pressed {
                background-color: #1d4ed8;
                border: 2px solid #1e40af;
            }
            
            QPushButton#extractButton:disabled {
                background-color: #9ca3af;
                color: #6b7280;
                border: 2px solid #e5e7eb;
            }
            
            
            QPushButton#syncButton {
                background-color: #5a155b;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 12px;
                font-weight: 600;
                font-size: 13px;
                margin: 0 2px;
                min-width: 100px;
                border: 2px solid transparent;
            }
            
            QPushButton#syncButton:hover {
                background-color: #481244;
                border: 2px solid #3d0f38;
            }
            
            QPushButton#syncButton:pressed {
                background-color: #3d0f38;
                border: 2px solid #2d0a2b;
            }
            
            QPushButton#sortButton {
                background-color: #f9fafb;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 14px;
            }
            
            QPushButton#sortButton:hover {
                background-color: #f3f4f6;
            }
            
            QPushButton#deleteButton {
                color: #ef4444;
                border: 1px solid #ef4444;
                border-radius: 4px;
                padding: 4px 12px;
                background-color: transparent;
                font-size: 12px;
            }
            
            QPushButton#deleteButton:hover {
                background-color: #ef4444;
                color: white;
            }

            QPushButton#feedbackButton {
                background-color: #f59e0b;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
                font-weight: 600;
                min-width: 30px;
                max-width: 30px;
                min-height: 30px;
                max-height: 30px;
            }

            QPushButton#feedbackButton:hover {
                background-color: #d97706;
            }

            QPushButton#feedbackButton:pressed {
                background-color: #b45309;
            }

            /* Table */
            SitesKeywordsSyncWidget QTableWidget#syncTable {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                outline: none;
                gridline-color: transparent;
                margin: 0px;
            }
            
            SitesKeywordsSyncWidget QTableWidget#syncTable::item {
                padding: 12px 8px;
                border: none;
                border-bottom: 1px solid #f3f4f6;
            }
            
            SitesKeywordsSyncWidget QTableWidget#syncTable::item:selected {
                background-color: #eff6ff;
                color: #111827;
            }
            
            SitesKeywordsSyncWidget QTableWidget#syncTable::item:hover {
                background-color: #f8fafc;
            }
            
            SitesKeywordsSyncWidget QHeaderView::section {
                background-color: #f9fafb;
                border: none;
                border-bottom: 1px solid #e5e7eb;
                padding: 12px 8px;
                font-weight: 600;
                color: #374151;
                font-size: 12px;
            }
            
            /* Progress and Status */
            SitesKeywordsSyncWidget QProgressBar {
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                background-color: #f3f4f6;
                text-align: center;
                font-size: 13px;
                font-weight: 500;
                color: #374151;
                height: 24px;
                margin: 8px 0px;
            }
            
            SitesKeywordsSyncWidget QProgressBar::chunk {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #3b82f6, stop: 1 #1d4ed8);
                border-radius: 6px;
                margin: 2px;
            }
            
            SitesKeywordsSyncWidget QLabel#statusLabel {
                color: #6b7280;
                font-size: 14px;
                font-style: italic;
                padding: 4px 8px;
                background: transparent;
                border: none;
                margin: 0px;
            }
            
            /* Pagination */
            SitesKeywordsSyncWidget QWidget#paginationBar {
                background-color: white;
                border-top: 1px solid #e5e7eb;
                margin: 0px;
            }
            
            SitesKeywordsSyncWidget QLabel#infoLabel {
                color: #6b7280;
                font-size: 14px;
                font-weight: 500;
                background: transparent;
                border: none;
                margin: 0px;
            }
            
            SitesKeywordsSyncWidget QPushButton#pageNavButton {
                background-color: #f9fafb;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: 500;
                font-size: 14px;
                min-width: 32px;
                margin: 0px;
            }
            
            SitesKeywordsSyncWidget QPushButton#pageNavButton:hover {
                background-color: #f3f4f6;
            }
            
            SitesKeywordsSyncWidget QPushButton#pageNavButton:disabled {
                background-color: #f9fafb;
                color: #9ca3af;
                border-color: #e5e7eb;
            }
            
            SitesKeywordsSyncWidget QPushButton#pageButton {
                background-color: #f9fafb;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 6px;
                font-weight: 500;
                font-size: 14px;
                min-width: 32px;
                min-height: 32px;
                margin: 0px;
            }
            
            SitesKeywordsSyncWidget QPushButton#pageButton:hover {
                background-color: #f3f4f6;
            }
            
            SitesKeywordsSyncWidget QPushButton#pageButton:checked {
                background-color: #5a155b;
                color: white;
                border-color: #5a155b;
            }
            
            /* Sync Overlay */
            QWidget#syncOverlay {
                background-color: rgba(0, 0, 0, 0.5);
            }
            
            QWidget#syncContent {
                background-color: white;
                border-radius: 8px;
                padding: 30px;
            }
            
            QLabel#syncStatusLabel {
                font-size: 16px;
                font-weight: 600;
                color: #374151;
            }
            
            QLabel#syncSuccessLabel {
                font-size: 16px;
                font-weight: 600;
                color: #059669;
            }
            
            QPushButton#syncOkButton {
                background-color: #5a155b;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-weight: 600;
                font-size: 14px;
            }
            
            QPushButton#syncOkButton:hover {
                background-color: #481244;
            }
        """)

def main():
    """Test the Sites and Keywords sync widget."""
    app = QApplication(sys.argv)
    widget = SitesKeywordsSyncWidget()
    widget.show()       
    sys.exit(app.exec_())   

if __name__ == "__main__":
    main()