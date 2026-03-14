# qt_views/ple/SyncSummaryWidget.py

import PLEView
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="ignore")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="ignore")
import os
import json
import sqlite3
import threading
import requests
from datetime import datetime, timedelta
from collections import defaultdict
from urllib.parse import urlparse
import re
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMainWindow,
    QMenu, QAction, QSizePolicy, QAbstractItemView, QApplication,
    QDialog, QLineEdit, QComboBox, QDialogButtonBox, QFormLayout,
    QMessageBox, QProgressBar, QTextEdit, QTabWidget, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QEvent, QPropertyAnimation, QRect, QThread
from PyQt5.QtGui import QFont, QPalette, QColor, QCursor

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EXPORT_DIR = PROJECT_ROOT / "ple"

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

#*********************************************************Modificado por Equipo UAA 18-08-2025

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
    print("Warning: NLP libraries not available. Basic functionality only.")

class ChromeHistoryExtractor:
    """Chrome history extraction functionality."""
    
    def get_chrome_history_path(self):
        """Get Chrome history database path based on OS."""
        if os.name == 'nt':  # Windows
            chrome_path = os.path.join(os.getenv('LOCALAPPDATA'), 'Google', 'Chrome', 'User Data', 'Default', 'History')
        elif os.name == 'posix':  # macOS/Linux
            if sys.platform == 'darwin':  # macOS
                chrome_path = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'Google', 'Chrome', 'Default', 'History')
            else:  # Linux
                chrome_path = os.path.join(os.path.expanduser('~'), '.config', 'google-chrome', 'Default', 'History')
        else:
            raise OSError("Unsupported operating system")
        
        if not os.path.exists(chrome_path):
            raise FileNotFoundError("Chrome history file not found")
        
        return chrome_path
    
    def convert_chrome_time(self, chrome_time):
        """Convert Chrome time to datetime."""
        epoch_start = datetime(1601, 1, 1)
        return epoch_start + timedelta(microseconds=chrome_time)
    
    def extract_history(self, limit=100):
        """Extract Chrome history data."""
        try:
            history_path = self.get_chrome_history_path()
            conn = sqlite3.connect(f"file:{history_path}?mode=ro", uri=True)
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
            
            history_data = []
            for row in results:
                visit_time = self.convert_chrome_time(row[3])
                duration_seconds = row[4] / 1_000_000 if row[4] > 0 else 5
                end_time = visit_time + timedelta(seconds=duration_seconds)
                
                history_data.append({
                    "id": row[0],
                    "url": row[1],
                    "title": row[2] or "Sin título",
                    "visit_time": visit_time.isoformat() + "Z",
                    "end_time": end_time.isoformat() + "Z",
                    "duration": duration_seconds
                })
            
            return history_data
        except Exception as e:
            raise Exception(f"Error extracting history: {str(e)}")

class KeywordExtractor:
    """Keyword extraction with fallbacks."""
    
    def __init__(self):
        self.kw_model = None
        self.nlp = None
        self.spanish_stopwords = set()
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize NLP models with fallbacks."""
        if not NLP_AVAILABLE:
            return
        
        try:
            nltk.download('stopwords', quiet=True)
            self.spanish_stopwords = set(stopwords.words('spanish'))
        except:
            self.spanish_stopwords = {'el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no'}
        
        try:
            self.kw_model = KeyBERT(model="paraphrase-multilingual-MiniLM-L12-v2")
        except:
            print("KeyBERT model not available")
        
        try:
            self.nlp = spacy.load("es_core_news_sm")
        except:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except:
                print("spaCy models not available")
    
    def extract_keywords_from_url(self, url, title=""):
        """Extract keywords from URL content."""
        if not self.kw_model:
            return self._basic_keyword_extraction(url, title)
        
        try:
            content = self._extract_page_content(url)
            if content.startswith("Error"):
                return ["Error: Could not extract content"]
            
            keywords = self.kw_model.extract_keywords(
                content,
                keyphrase_ngram_range=(1, 3),
                stop_words=list(self.spanish_stopwords),
                use_mmr=True,
                diversity=0.5,
                top_n=10
            )
            
            return [kw[0] for kw in keywords]
        except Exception as e:
            return [f"Error: {str(e)}"]
    
    def _extract_page_content(self, url):
        """Extract content from web page."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string.strip() if soup.title else "Sin título"
            
            paragraphs = soup.find_all('p', limit=3)
            content = " ".join([p.get_text(strip=True) for p in paragraphs])
            
            content = re.sub(r'\s+', ' ', content).strip()
            content = re.sub(r'[^\w\sáéíóúüñÁÉÍÓÚÜÑ]', '', content)
            
            combined_text = f"{title}. {content}"
            return combined_text if len(combined_text) > 50 else "Error: Insufficient content"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _basic_keyword_extraction(self, url, title=""):
        """Basic keyword extraction fallback."""
        domain = urlparse(url).netloc.replace('www.', '')
        keywords = [domain]
        
        if title:
            words = re.findall(r'\w+', title.lower())
            keywords.extend([w for w in words if len(w) > 3 and w not in self.spanish_stopwords][:5])
        
        return keywords

class HistoryProcessingThread(QThread):
    """Thread for processing Chrome history."""
    
    progress_updated = pyqtSignal(int)
    item_processed = pyqtSignal(dict)
    finished_processing = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, history_data):
        super().__init__()
        self.history_data = history_data
        self.keyword_extractor = KeywordExtractor()
    
    def run(self):
        """Process history data in background thread."""
        try:
            processed_items = []
            total_items = len(self.history_data)
            
            for i, item in enumerate(self.history_data):
                # Infer activity type
                activity_type = self._infer_activity_type(item['url'], item['title'])
                
                # Extract keywords
                keywords = self.keyword_extractor.extract_keywords_from_url(
                    item['url'], item['title']
                )
                
                # Infer domains
                domains = self._infer_domains(item['title'], keywords)
                
                processed_item = {
                    "type": "Sitio",
                    "content": item['url'],
                    "title": item['title'],
                    "status": "synced" if not any("Error" in k for k in keywords) else "error",
                    "last_used": self._format_time_ago(item['visit_time']),
                    "activity_type": activity_type,
                    "keywords": keywords,
                    "domains": domains,
                    "visit_time": item['visit_time'],
                    "end_time": item['end_time'],
                    "duration": item['duration']
                }
                
                processed_items.append(processed_item)
                self.item_processed.emit(processed_item)
                self.progress_updated.emit(int((i + 1) / total_items * 100))
            
            self.finished_processing.emit(processed_items)
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def _infer_activity_type(self, url, title):
        """Infer activity type from URL and title."""
        url_lower = url.lower()
        title_lower = title.lower()
        
        types = {
            "Video": ["youtube.com", "vimeo.com", "dailymotion.com", "twitch.tv"],
            "Article": ["medium.com", "researchgate.net", "jstor.org", "sciencedirect.com"],
            "Tool": ["docs.google.com", "drive.google.com", "github.com", "stackoverflow.com"],
            "Module": ["coursera.org", "edx.org", "udacity.com", "khanacademy.org"],
            "Book": ["goodreads.com", "books.google.com", "amazon.com/books"],
            "Collaboration": ["zoom.us", "teams.microsoft.com", "slack.com", "meet.google.com"]
        }
        
        for activity, keywords in types.items():
            if any(keyword in url_lower for keyword in keywords):
                return activity
        
        return "Other"
    
    def _infer_domains(self, title, keywords):
        """Infer academic domains."""
        fields = [
            "Computer Science", "Data Science", "Mathematics", "Physics", "Engineering",
            "Business", "Education", "Medicine", "Psychology", "Biology", "Chemistry"
        ]
        
        text = f"{title} {' '.join(keywords)}".lower()
        relevant_domains = [field for field in fields if field.lower() in text]
        
        return relevant_domains or ["General Knowledge"]
    
    def _format_time_ago(self, iso_time):
        """Format time as 'time ago' string."""
        try:
            visit_time = datetime.fromisoformat(iso_time.replace('Z', ''))
            now = datetime.now()
            diff = now - visit_time
            
            if diff.days > 0:
                return f"hace {diff.days} día{'s' if diff.days > 1 else ''}"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"hace {hours} hora{'s' if hours > 1 else ''}"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"hace {minutes} minuto{'s' if minutes > 1 else ''}"
            else:
                return "hace unos segundos"
        except:
            return "tiempo desconocido"

class AddItemDialog(QDialog):
    """Simple dialog for adding new sync items."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar Elemento")
        self.setModal(True)
        self.setFixedSize(380, 180)
        
        layout = QFormLayout(self)
        
        # Type selection
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Sitio", "Palabra"])
        
        # Content input
        self.content_input = QLineEdit()
        self.content_input.setPlaceholderText("Ingrese URL o palabra clave...")
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal,
            self
        )
        
        ok_button = button_box.button(QDialogButtonBox.Ok)
        ok_button.setText("Agregar")
        cancel_button = button_box.button(QDialogButtonBox.Cancel)
        cancel_button.setText("Cancelar")
        
        layout.addRow("Tipo:", self.type_combo)
        layout.addRow("Contenido:", self.content_input)
        layout.addRow(button_box)
        
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
    def get_data(self):
        return {
            'type': self.type_combo.currentText(),
            'content': self.content_input.text().strip()
        }

class SyncSummaryWidget(QMainWindow):
    """Clean, modern sync summary widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_page = 1
        self.items_per_page = 10
        self.search_active = False
        self.search_text = ""
        
        # Configure window
        self.setWindowTitle("Resumen de Sincronización - EPAI")
        self.setMinimumSize(1000, 600)
        self.resize(1200, 800)
        
        # Data storage
        self.sample_data = []
        self.chrome_data = []
        self.history_extractor = ChromeHistoryExtractor()
        self.processing_thread = None
        
        # Initialize with sample data
        self._load_sample_data()
        
        self.setup_ui()
        self.apply_clean_styles()
        
    def _load_sample_data(self):
        """Load initial sample data."""
        self.sample_data = [
            {"type": "Sitio", "content": "python.org", "status": "synced", "last_used": "hace 2 minutos"},
            {"type": "Palabra", "content": "machine learning", "status": "synced", "last_used": "hace 5 minutos"},
            {"type": "Sitio", "content": "github.com", "status": "synced", "last_used": "hace 10 minutos"},
            {"type": "Palabra", "content": "artificial intelligence", "status": "error", "last_used": "hace 15 minutos"},
            {"type": "Sitio", "content": "stackoverflow.com", "status": "synced", "last_used": "hace 20 minutos"},
            {"type": "Palabra", "content": "deep learning", "status": "pending", "last_used": "hace 25 minutos"},
            {"type": "Sitio", "content": "epai.com", "status": "synced", "last_used": "hace 30 minutos"},
            {"type": "Palabra", "content": "neural networks", "status": "synced", "last_used": "hace 35 minutos"}
        ]
        
    def setup_ui(self):
        """Create clean UI layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        self.create_header(main_layout)
        
        # Summary
        self.create_summary(main_layout)
        
        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        main_layout.addWidget(self.progress_bar)
        
        # Create tabs for different views
        self.create_tabs(main_layout)
        
        # Install event filter for keyboard shortcuts
        self.installEventFilter(self)
        
    def create_header(self, parent_layout):
        """Create simple header."""
        header_frame = QWidget()
        header_frame.setObjectName("header")
        header_frame.setFixedHeight(60)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(24, 0, 24, 0)
        
        title_label = QLabel("EPAI - Resumen de Sincronización")
        title_label.setObjectName("title")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        parent_layout.addWidget(header_frame)
        
    def create_summary(self, parent_layout):
        """Create clean summary section."""
        summary_frame = QWidget()
        summary_frame.setObjectName("summary")
        
        summary_layout = QHBoxLayout(summary_frame)
        summary_layout.setContentsMargins(24, 16, 24, 16)
        summary_layout.setSpacing(16)
        
        # Metrics
        total_sites = sum(1 for item in self.sample_data if item['type'] == 'Sitio')
        total_keywords = sum(1 for item in self.sample_data if item['type'] == 'Palabra')
        
        metrics_label = QLabel(f"{total_sites} sitios • {total_keywords} palabras")
        metrics_label.setObjectName("metrics")
        
        # Buttons
        refresh_button = QPushButton("Actualizar")
        refresh_button.setObjectName("secondary")
        refresh_button.clicked.connect(self.on_refresh_clicked)
        
        chrome_button = QPushButton("📊 Extraer Chrome")
        chrome_button.setObjectName("primary")
        chrome_button.clicked.connect(self.on_extract_chrome_clicked)
        
        export_button = QPushButton("💾 Exportar JSON")
        export_button.setObjectName("secondary")
        export_button.clicked.connect(self.on_export_json_clicked)
        
        add_button = QPushButton("+ Agregar")
        add_button.setObjectName("primary")
        add_button.clicked.connect(self.on_add_clicked)
        
        summary_layout.addWidget(metrics_label)
        summary_layout.addStretch()
        summary_layout.addWidget(refresh_button)
        summary_layout.addWidget(chrome_button)
        summary_layout.addWidget(export_button)
        summary_layout.addWidget(add_button)
        
        parent_layout.addWidget(summary_frame)
        
    def create_tabs(self, parent_layout):
        """Create tabbed interface."""
        self.tab_widget = QTabWidget()
        
        # Main table tab
        table_tab = QWidget()
        table_layout = QVBoxLayout(table_tab)
        table_layout.setContentsMargins(0, 0, 0, 0)
        self.create_table(table_layout)
        
        # Details tab
        details_tab = QWidget()
        details_layout = QVBoxLayout(details_tab)
        self.create_details_view(details_layout)
        
        self.tab_widget.addTab(table_tab, "Resumen")
        self.tab_widget.addTab(details_tab, "Detalles")
        
        parent_layout.addWidget(self.tab_widget)
    
    def create_details_view(self, parent_layout):
        """Create detailed view for items."""
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setPlainText("Seleccione un elemento para ver detalles...")
        
        scroll_layout.addWidget(self.details_text)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        parent_layout.addWidget(scroll_area)
    
    def create_table(self, parent_layout):
        """Create clean table."""
        # Container for margins
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(24, 0, 24, 24)
        
        # Table
        self.table = QTableWidget()
        self.table.setObjectName("table")
        
        # Configure columns
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Contenido", "Tipo", "Estado", "Actividad", ""])
        
        # Basic styling
        self.table.setShowGrid(False)
        self.table.setFrameShape(QTableWidget.NoFrame)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        
        # Header
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.resizeSection(2, 80)
        header.resizeSection(4, 60)
        header.setFixedHeight(40)
        
        # Hide vertical header
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(48)
        
        # Events
        self.table.setMouseTracking(True)
        self.table.viewport().installEventFilter(self)
        self.table.cellClicked.connect(self.on_cell_clicked)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Populate
        self.populate_table()
        
        table_layout.addWidget(self.table, 1)
        parent_layout.addWidget(table_container, 1)
        
    def populate_table(self):
        """Populate table with data."""
        # Combine sample data and Chrome data
        all_data = self.sample_data + self.chrome_data
        self.table.setRowCount(len(all_data))
        
        for row, item in enumerate(all_data):
            # Content (truncate if too long)
            content = item['content']
            if len(content) > 60:
                content = content[:57] + "..."
            content_item = QTableWidgetItem(content)
            content_item.setFlags(content_item.flags() & ~Qt.ItemIsEditable)
            content_item.setToolTip(item['content'])  # Full content in tooltip
            self.table.setItem(row, 0, content_item)
            
            # Type
            type_item = QTableWidgetItem(item['type'])
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, type_item)
            
            # Status
            status_item = QTableWidgetItem("●")
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
            
            if item['status'] == 'synced':
                status_item.setForeground(QColor("#22c55e"))  # Green
            elif item['status'] == 'error':
                status_item.setForeground(QColor("#ef4444"))  # Red
            else:
                status_item.setForeground(QColor("#6b7280"))  # Gray
                
            self.table.setItem(row, 2, status_item)
            
            # Activity type (for Chrome data)
            activity_type = item.get('activity_type', 'N/A')
            activity_item = QTableWidgetItem(activity_type)
            activity_item.setFlags(activity_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 3, activity_item)
            
            # Actions (empty initially)
            actions_item = QTableWidgetItem("")
            actions_item.setFlags(actions_item.flags() & ~Qt.ItemIsEditable)
            actions_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, actions_item)
            
    def apply_clean_styles(self):
        """Apply clean, modern styling."""
        self.setStyleSheet("""
            /* Global */
            QMainWindow {
                background-color: #f9fafb;
            }
            
            QWidget {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                color: #111827;
            }
            
            /* Header */
            QWidget#header {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #6366f1, stop: 1 #8b5cf6);
            }
            
            QLabel#title {
                color: white;
                font-size: 18px;
                font-weight: 600;
            }
            
            /* Summary */
            QWidget#summary {
                background-color: white;
                border-bottom: 1px solid #e5e7eb;
            }
            
            QLabel#metrics {
                color: #6b7280;
                font-size: 14px;
                font-weight: 500;
            }
            
            /* Buttons */
            QPushButton#primary {
                background-color: #6366f1;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 14px;
            }
            
            QPushButton#primary:hover {
                background-color: #5145e5;
            }
            
            QPushButton#secondary {
                background-color: #f9fafb;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 14px;
            }
            
            QPushButton#secondary:hover {
                background-color: #f3f4f6;
            }
            
            /* Table */
            QTableWidget#table {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                outline: none;
            }
            
            QTableWidget#table::item {
                padding: 12px 8px;
                border: none;
                border-bottom: 1px solid #f3f4f6;
            }
            
            QTableWidget#table::item:selected {
                background-color: #eff6ff;
                color: #111827;
            }
            
            QTableWidget#table::item:hover {
                background-color: #f8fafc;
            }
            
            QHeaderView::section {
                background-color: #f9fafb;
                border: none;
                border-bottom: 1px solid #e5e7eb;
                padding: 12px 8px;
                font-weight: 600;
                color: #374151;
                font-size: 12px;
            }
            
            /* Scrollbar */
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                border: none;
            }
            
            QScrollBar::handle:vertical {
                background: #d1d5db;
                border-radius: 3px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #9ca3af;
            }
        """)
        
    def eventFilter(self, obj, event):
        """Handle events for search and row actions."""
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Slash and not self.search_active:
                self.show_search()
                return True
            elif event.key() == Qt.Key_Escape and self.search_active:
                self.hide_search()
                return True
                
        # Handle table hover for row actions
        if obj == self.table.viewport() and event.type() == QEvent.MouseMove:
            pos = event.pos()
            index = self.table.indexAt(pos)
            if index.isValid():
                self.show_row_actions(index.row())
            else:
                self.hide_all_row_actions()
                
        return super().eventFilter(obj, event)
        
    def show_row_actions(self, row):
        """Show actions for a specific row on hover."""
        self.hide_all_row_actions()
        actions_item = self.table.item(row, 4)
        if actions_item:
            actions_item.setText("⋯")
            actions_item.setForeground(QColor("#9ca3af"))
            
    def hide_all_row_actions(self):
        """Hide actions for all rows."""
        for row in range(self.table.rowCount()):
            actions_item = self.table.item(row, 4)
            if actions_item:
                actions_item.setText("")
                
    def show_search(self):
        """Show search functionality."""
        self.search_active = True
        # Implementation for search
        
    def hide_search(self):
        """Hide search functionality."""
        self.search_active = False
        
    def on_extract_chrome_clicked(self):
        """Extract Chrome history data."""
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("Extrayendo historial de Chrome...")
            
            # Extract raw history
            raw_history = self.history_extractor.extract_history(limit=50)
            
            if not raw_history:
                QMessageBox.warning(self, "Sin datos", "No se encontraron datos en el historial de Chrome.")
                self.progress_bar.setVisible(False)
                return
            
            # Process in background thread
            self.processing_thread = HistoryProcessingThread(raw_history)
            self.processing_thread.progress_updated.connect(self.progress_bar.setValue)
            self.processing_thread.item_processed.connect(self.on_item_processed)
            self.processing_thread.finished_processing.connect(self.on_processing_finished)
            self.processing_thread.error_occurred.connect(self.on_processing_error)
            
            self.progress_bar.setFormat("Procesando datos... %p%")
            self.processing_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error extrayendo historial: {str(e)}")
            self.progress_bar.setVisible(False)
    
    def on_item_processed(self, item):
        """Handle processed item."""
        # Add to chrome data if not already present
        if not any(existing['content'] == item['content'] for existing in self.chrome_data):
            self.chrome_data.append(item)
    
    def on_processing_finished(self, processed_items):
        """Handle processing completion."""
        self.progress_bar.setVisible(False)
        self.populate_table()
        
        QMessageBox.information(
            self, 
            "Extracción completada", 
            f"Se procesaron {len(processed_items)} elementos del historial de Chrome."
        )
    
    def on_processing_error(self, error_msg):
        """Handle processing error."""
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Error de procesamiento", f"Error: {error_msg}")
    
    def on_export_json_clicked(self):
        """Export data to JSON format."""
        try:
            # Combine all data
            all_data = self.sample_data + self.chrome_data
            
            if not all_data:
                QMessageBox.warning(self, "Sin datos", "No hay datos para exportar.")
                return
            
            # Prepare JSON structure
            json_data = {
                "userID": GOT_IT_ID,
                "associatedPLE": idpleDinamico,
                "trackedDataList": []
            }
            
            for item in all_data:
                json_item = {
                    "activityType": item.get('activity_type', 'Other'),
                    "associatedURL": item['content'] if item['type'] == 'Sitio' else None,
                    "associatedDomains": item.get('domains', ['General Knowledge']),
                    "associatedKeywords": item.get('keywords', [item['content']]),
                    "startTime": item.get('visit_time', datetime.now().isoformat() + "Z"),
                    "endTime": item.get('end_time', datetime.now().isoformat() + "Z"),
                    "feedback": {
                        "score": None,
                        "comments": None
                    }
                }
                json_data["trackedDataList"].append(json_item)
            
            # Save to file
            filename = f"epai_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
            
            QMessageBox.information(
                self, 
                "Exportación exitosa", 
                f"Datos exportados a {filename}\n\nElementos exportados: {len(json_data['trackedDataList'])}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error de exportación", f"Error: {str(e)}")
    
    def on_add_clicked(self):
        """Handle add button click."""
        dialog = AddItemDialog(self)
        
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            
            if not data['content']:
                QMessageBox.warning(self, "Error", "Por favor ingrese contenido.")
                return
            
            new_item = {
                "type": data['type'],
                "content": data['content'],
                "status": "synced",
                "last_used": "ahora"
            }
            
            self.sample_data.append(new_item)
            self.populate_table()
            
            QMessageBox.information(
                self, 
                "Éxito", 
                f"Se agregó: {data['content']}"
            )
        
    def on_refresh_clicked(self):
        """Handle refresh button click."""
        self.populate_table()
        
    def on_cell_clicked(self, row, col):
        """Handle cell click events."""
        if col == 4 and self.table.item(row, 4).text() == "⋯":
            self.show_actions_menu(row)
        else:
            # Show details for selected item
            self.show_item_details(row)
            
    def show_actions_menu(self, row):
        """Show actions menu for a specific row."""
        menu = QMenu(self)
        
        view_action = QAction("Ver detalles", self)
        view_action.triggered.connect(lambda: self.view_details(row))
        
        resync_action = QAction("Resincronizar", self)
        resync_action.triggered.connect(lambda: self.resync_item(row))
        
        delete_action = QAction("Eliminar", self)
        delete_action.triggered.connect(lambda: self.delete_item(row))
        
        menu.addAction(view_action)
        menu.addAction(resync_action)
        menu.addSeparator()
        menu.addAction(delete_action)
        
        menu.exec_(QCursor.pos())
        
    def show_context_menu(self, pos):
        """Show context menu on right-click."""
        item = self.table.itemAt(pos)
        if item:
            row = item.row()
            self.show_actions_menu(row)
            
    def show_item_details(self, row):
        """Show detailed information for selected item."""
        all_data = self.sample_data + self.chrome_data
        if row >= len(all_data):
            return
        
        item = all_data[row]
        details = f"Contenido: {item['content']}\n"
        details += f"Tipo: {item['type']}\n"
        details += f"Estado: {item['status']}\n"
        details += f"Última actividad: {item['last_used']}\n"
        
        if 'activity_type' in item:
            details += f"\nTipo de actividad: {item['activity_type']}\n"
        
        if 'title' in item:
            details += f"Título: {item['title']}\n"
        
        if 'keywords' in item and item['keywords']:
            details += f"\nPalabras clave:\n"
            for keyword in item['keywords'][:10]:  # Limit to 10 keywords
                details += f"  • {keyword}\n"
        
        if 'domains' in item and item['domains']:
            details += f"\nDominios académicos:\n"
            for domain in item['domains']:
                details += f"  • {domain}\n"
        
        if 'duration' in item:
            details += f"\nDuración de visita: {item['duration']:.1f} segundos\n"
        
        self.details_text.setPlainText(details)
        self.tab_widget.setCurrentIndex(1)  # Switch to details tab
    
    def view_details(self, row):
        """View details for an item."""
        self.show_item_details(row)
        
    def resync_item(self, row):
        """Resynchronize an item."""
        content = self.table.item(row, 0).text()
        print(f"Resynchronizing: {content}")
        
    def delete_item(self, row):
        """Delete an item."""
        content = self.table.item(row, 0).text()
        print(f"Deleting: {content}")
        self.table.removeRow(row)
        
    def resizeEvent(self, event):
        """Handle window resize."""
        super().resizeEvent(event)

def main():
    """Test the clean sync summary widget."""
    app = QApplication(sys.argv)
    widget = SyncSummaryWidget()
    widget.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()