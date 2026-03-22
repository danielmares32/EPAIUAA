# qt_views/ple/PLEView.py

import sys
import os
from typing import Optional, Union, Tuple
import json
import requests
import sqlite3
import tempfile
import shutil
import platform
import webbrowser
from datetime import datetime
from pathlib import Path
import importlib
import traceback
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QCheckBox,
    QPushButton, QScrollArea, QGridLayout, QMessageBox,
    QTabWidget, QTextEdit, QLineEdit, QListWidget, QButtonGroup, QGraphicsOpacityEffect
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, pyqtProperty, QThread, pyqtSignal
from qt_views.global_state import GlobalState

# Import authentication configuration
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.config import get_auth_headers

# Importadores de extracción de keywords
from rake_nltk import Rake
from keybert import KeyBERT
import yake
import spacy



API_BASE = "https://uninovadeplan-ws.javali.pt"
#DEFAULT_PLE_USER_ID = 295  # Usuario por defecto si no se recibe uno

def _qt_excepthook(type_, value, tb):
    traceback.print_exception(type_, value, tb)
    try:
        QMessageBox.critical(None, "Error",
            f"Ocurrió un error no controlado:\n{value}\n\nRevisa la consola para el traceback.")
    except Exception:
        pass

sys.excepthook = _qt_excepthook

def _get_app_data_dir():
    """Get the writable application data directory based on OS and bundle status"""
    if getattr(sys, 'frozen', False):
        # Running in a bundle - use Application Support directory
        if platform.system() == 'Darwin':  # macOS
            return Path.home() / "Library" / "Application Support" / "EPA_Dashboard"
        elif platform.system() == 'Windows':
            return Path(os.environ.get('APPDATA', Path.home())) / "EPA_Dashboard"
        else:  # Linux
            return Path.home() / ".config" / "EPA_Dashboard"
    else:
        # Running from source - use project directory
        return Path(__file__).resolve().parents[2]

def _resolver_guardar_id_ple():
        """
        Get path to guardarIDPLE.txt - uses Application Support when bundled
        """
        if getattr(sys, 'frozen', False):
            # Running in a bundle - use Application Support directory
            app_dir = _get_app_data_dir()
            fallback = app_dir / "qt_views" / "ple" / "guardarIDPLE.txt"
            fallback.parent.mkdir(parents=True, exist_ok=True)
            return str(fallback)
        else:
            # Running from source - try to find existing file first
            candidatos = []
            base = Path(__file__).resolve().parent
            for _ in range(8):
                candidatos.append(base / "qt_views" / "ple" / "guardarIDPLE.txt")
                base = base.parent
            candidatos.append(Path(os.getcwd()) / "qt_views" / "ple" / "guardarIDPLE.txt")
            for c in candidatos:
                if c.is_file():
                    return str(c)
            # fallback: crea en el cwd
            fallback = Path(os.getcwd()) / "qt_views" / "ple" / "guardarIDPLE.txt"
            fallback.parent.mkdir(parents=True, exist_ok=True)
            return str(fallback)
#**********************************************************Modificado por Equipo UAA 18-08-2025
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

# --- Prefs locales ahora POR USUARIO Y PLE ---
def _prefs_key(user_id:int, env_id:int) -> str:
    return f"{int(user_id)}:{int(env_id)}"

def _get_pref_for_user_env(user_id:int, env_id:int) -> Optional[dict]:
    prefs = _load_prefs()
    rec = prefs.get(_prefs_key(user_id, env_id))
    return rec if isinstance(rec, dict) else None

def _set_pref_for_user_env(user_id:int, env_id:int, mode:str, frequency:Optional[int]=0) -> None:
    prefs = _load_prefs()
    prefs[_prefs_key(user_id, env_id)] = {
        "mode": mode,
        "frequency": int(frequency or 0),
        "updatedAt": datetime.utcnow().isoformat() + "Z",
        "source": "local"
    }
    _save_prefs(prefs)

def _leer_ultimo_env_id() -> Optional[int]:
    """Lee 'pleseleccionado=<id>' de guardarIDPLE.txt, si existe."""
    try:
        path_txt = _resolver_guardar_id_ple()
        with open(path_txt, "r", encoding="utf-8") as f:
            for linea in f:
                if "=" in linea:
                    clave, valor = linea.strip().split("=", 1)
                    if clave == "pleseleccionado":
                        return int(valor)
    except Exception as e:
        print("[LastPLE] No se pudo leer el último environmentID:", e)
    return None

# --- Llamadas servidor (ajusta cabeceras según tu Swagger si usa auth) ---
SERVER_TIMEOUT = 12

def _auth_headers():
    # Use centralized authentication from config
    # This includes the Bearer token from secret.txt or environment variable
    h = get_auth_headers()
    h.update({"Accept": "application/json"})

    # Legacy fallback: check perfil_usuario.json for token (if needed)
    tok = _obtener_valor_json(_resolver_perfil_usuario_json(), "token")
    if tok and "Authorization" not in h:
        h["Authorization"] = f"Bearer {tok}"
    return h

def fetch_server_prefs(environment_id:int, user_id:int):
    url = f"{API_BASE}/preferences/{int(environment_id)}"
    r = requests.get(
        url,
        params={"userID": int(user_id)},
        headers=_auth_headers(),
        timeout=SERVER_TIMEOUT
    )
    print("[GET prefs] status:", r.status_code, "resp:", r.text[:500])
    if r.status_code == 404:
        return {"mode": "none", "frequency": 0, "_raw": {}}
    r.raise_for_status()
    data = r.json() or {}
    mode, freq = _flags_to_mode(data)
    return {"mode": mode, "frequency": freq, "_raw": data}

def ensure_server_prefs(environment_id: int, user_id: int) -> dict:
    """
    Si no existe registro en server (GET devuelve _raw == {}), lo crea con PUT (none,0).
    Devuelve siempre el estado resultante y sincroniza local.
    """
    rec = fetch_server_prefs(environment_id, user_id)  # no lanza 404; usa _raw == {}
    if rec.get("_raw", {}) == {}:
        # No hay row en server: sembrar
        rec = put_server_prefs(environment_id, user_id, mode="none", frequency=0)
    _set_pref_for_user_env(user_id, environment_id, rec["mode"], rec["frequency"])
    return rec

def put_server_prefs(environment_id:int, user_id:int, mode:str, frequency:Optional[int]=0):
    url = f"{API_BASE}/preferences/{int(environment_id)}"
    payload = _mode_to_flags(mode, frequency)
    try:
        print("[PUT prefs] url:", url,
              "params:", {"userID": int(user_id)},
              "payload:", payload)
        r = requests.put(
            url,
            params={"userID": int(user_id)},
            json=payload,
            headers={**_auth_headers(), "Content-Type":"application/json; charset=utf-8"},
            timeout=SERVER_TIMEOUT
        )
        print("[PUT prefs] status:", r.status_code, "resp:", r.text[:500])
    except Exception as e:
        print("[PUT prefs] error:", e)
        raise
    if r.status_code in (200, 204):
        try:
            data = r.json() or {}
        except ValueError:
            data = {}
        m, f = _flags_to_mode(data) if data else (mode, int(frequency or 0))
        return {"mode": m, "frequency": f, "_raw": data or payload}
    r.raise_for_status()
    return {"mode": mode, "frequency": int(frequency or 0), "_raw": {}}

def _prefs_path() -> Path:
    """Get the preferences path - uses Application Support on macOS for write access"""
    app_dir = _get_app_data_dir()
    base = app_dir / "config" / "preferenciasPorPLE"
    base.mkdir(parents=True, exist_ok=True)
    return base / "tracking_prefs.json"

def _load_prefs() -> dict:
    p = _prefs_path()
    try:
        if p.exists():
            with p.open("r", encoding="utf-8") as f:
                return json.load(f) or {}
    except Exception:
        pass
    return {}

def _save_prefs(prefs: dict) -> None:
    p = _prefs_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(prefs, f, ensure_ascii=False, indent=2)

def _mode_to_flags(mode: str, freq: Optional[int]) -> dict:
    freq = int(freq) if isinstance(freq, int) or (isinstance(freq, str) and str(freq).isdigit()) else 0
    flags = {
        "transmissionFrequency": freq,
        "trackAll": False,
        "trackApproved": False,
        "noTrack": False,
        "transmitAllEnd": False,
    }
    if mode == "all":
        flags["trackAll"] = True
    elif mode == "approved":
        flags["trackApproved"] = True
    elif mode == "logout":
        flags["transmitAllEnd"] = True
    else:  # "none"
        flags["noTrack"] = True
    return flags

def _flags_to_mode(d: dict) -> Tuple[str, int]:
    """Devuelve (mode, transmissionFrequency) desde respuesta del server."""
    if not isinstance(d, dict):
        return ("none", 0)
    freq = int(d.get("transmissionFrequency") or 0)
    if d.get("trackAll"):
        return ("all", freq)
    if d.get("trackApproved"):
        return ("approved", freq)
    if d.get("transmitAllEnd"):
        return ("logout", freq)
    if d.get("noTrack"):
        return ("none", freq)
    return ("none", freq)

def _obtener_valor_json(archivo_json, clave):
    try:
        with open(archivo_json, 'r', encoding='utf-8') as f:
            return json.load(f).get(clave)
    except Exception as e:
        print(f"[UID] No se obtuvo {clave} de {archivo_json}: {e}")
        return None

_perfil = _resolver_perfil_usuario_json()
uid_val = _obtener_valor_json(_perfil, "uid") if _perfil else None
try:
    DEFAULT_PLE_USER_ID = int(uid_val) if uid_val is not None else 0
except Exception:
    DEFAULT_PLE_USER_ID = 0
print(f"[UID] DEFAULT_PLE_USER_ID: {DEFAULT_PLE_USER_ID}")
 

#*********************************************************Modificado por Equipo UAA 18-08-2025

class PLEView(QWidget):
    """
    Vista PLE: mosaico de cursos y detalle en pestañas.
    """

    def _ensure_grid(self):
        # Crea scroll+grid si hiciera falta (por si el orden cambiara en el futuro)
        if not hasattr(self, "scroll") or not hasattr(self, "grid") or self.grid is None:
            # Si ya había un scroll eliminado, lo reconstruimos e insertamos
            self.scroll = QScrollArea()
            self.scroll.setWidgetResizable(True)
            self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            container = QWidget()
            self.grid = QGridLayout(container)
            self.grid.setSpacing(2)
            self.grid.setContentsMargins(25, 25, 25, 25)
            container.setLayout(self.grid)
            self.scroll.setWidget(container)

            try:
                idx_btn = self.main_layout.indexOf(self.no_ple_button)
                if idx_btn != -1:
                    self.main_layout.insertWidget(idx_btn, self.scroll, stretch=1)
                else:
                    self.main_layout.addWidget(self.scroll, stretch=1)
            except Exception:
                self.main_layout.addWidget(self.scroll, stretch=1)

    def __init__(self, parent=None, user_id=None, current_profile=None):
        super().__init__(parent)
        # Asignar user_id, si no se recibe usar valor por defecto
        self._rt_watcher = None
        self.user_id = user_id or DEFAULT_PLE_USER_ID
        self.current_profile = current_profile
        self.ple_data = []
        self.active_ple = None
        mi_variable_global = "Este es mi valor"

        # Keyboard navigation state
        self.ple_cards = []  # Lista de tarjetas PLE
        self.selected_card_index = 0  # Índice de la tarjeta seleccionada

        # Habilitar foco por teclado
        self.setFocusPolicy(Qt.StrongFocus)

                # Layout principal
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for better space usage
        self.main_layout.setSpacing(0)  # Remove spacing for better control

        # *** Construye scroll + grid ANTES de llamar load_ples ***
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        container = QWidget()
        self.grid = QGridLayout(container)
        self.grid.setSpacing(2)
        self.grid.setContentsMargins(25, 25, 25, 25)
        container.setLayout(self.grid)
        self.scroll.setWidget(container)
        self.main_layout.addWidget(self.scroll, stretch=1)

        # Botón alternativo
        """
        qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2)
                    
        qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #764ba2, stop:1 #667eea)

        qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a3d8a, stop:1 #5568c8           
        

        QPushButton:hover {
                background: ;
            }
            QPushButton:pressed {
                background: );
            }        
        """
        self.no_ple_button = QPushButton("Crear nuevo PLE")
        self.no_ple_button.setStyleSheet("""
            QPushButton {
                background: #5a155b;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
            }            
        """)
        self.no_ple_button.setCursor(Qt.PointingHandCursor)
        self.no_ple_button.clicked.connect(lambda: webbrowser.open("https://frontend.epai.grisenergia.pt/dashboard/ples"))
        self.main_layout.addWidget(self.no_ple_button, alignment=Qt.AlignCenter)



        # Inicializar extractores de keywords con fallbacks
        try:
            self.spacy_nlp = spacy.load("es_core_news_sm")
        except:
            try:
                self.spacy_nlp = spacy.load("en_core_web_sm")
            except:
                print("Warning: Using blank spaCy model in PLEView")
                self.spacy_nlp = spacy.blank("en")
        
        try:
            self.rake_extractor = Rake(language="spanish", min_length=1, max_length=3)
        except:
            self.rake_extractor = Rake(language="english", min_length=1, max_length=3)
        
        try:
            self.keybert_model = KeyBERT(model="paraphrase-multilingual-MiniLM-L12-v2")
        except:
            print("Warning: KeyBERT not available in PLEView")
            self.keybert_model = None
        
        try:
            self.yake_extractor = yake.KeywordExtractor(lan="es", n=2, top=5)
        except:
            self.yake_extractor = yake.KeywordExtractor(lan="en", n=2, top=5)

        self.load_ples()

        

    def _start_realtime_tracker(self, profile_dir: str, batch_size: Optional[int] = None, poll_seconds: Optional[int] = None) -> bool:
        """
        Inicia el RealTimeHistoryWatcher en un hilo daemon.
        Ajusta el import al path real de tu archivo (ver bloques try/except).
        """
        try:
            # Opción A: si el archivo está en services/history_service_1.py
            mod = importlib.import_module("services.history_service_1")
        except Exception:
            try:
                # Opción B: si quedó al mismo nivel que PLEView (history_service_1.py)
                mod = importlib.import_module("history_service_1")
            except Exception as e:
                QMessageBox.critical(self, "Seguimiento", f"No pude importar el rastreador en tiempo real:\n{e}")
                return False

        RT = getattr(mod, "RealTimeHistoryWatcher", None)
        if RT is None:
            QMessageBox.critical(self, "Seguimiento", "El módulo importado no contiene RealTimeHistoryWatcher.")
            return False

        # Evitar duplicados: si ya hay uno, primero lo detenemos
        if self._rt_watcher:
            try:
                self._rt_watcher.stop()
            except Exception:
                pass
            self._rt_watcher = None

        kwargs = {}
        if isinstance(batch_size, int) and batch_size > 0:
            kwargs["batch_size"] = batch_size
        if isinstance(poll_seconds, int) and poll_seconds > 0:
            kwargs["poll_interval"] = poll_seconds

        try:
            self._rt_watcher = RT(profile_dir=profile_dir, **kwargs)
            self._rt_watcher.start()
            return True
        except Exception as e:
            QMessageBox.critical(self, "Seguimiento", f"No se pudo iniciar el rastreador:\n{e}")
            self._rt_watcher = None
            return False


    def _stop_realtime_tracker(self) -> None:
        rt = getattr(self, "_rt_watcher", None)
        if rt:
            try:
                rt.stop()
            except Exception:
                pass
        self._rt_watcher = None

    def open_sites_keywords(self, env_id: int):
        """Abrir el gestor de sitios y palabras clave (solo bajo demanda)."""
        try:
            from .SitesKeywordsSyncWidget import SitesKeywordsSyncWidget

            main_window = self.window()
            print(f"[PLEView] main_window retrieved: {main_window}")
            print(f"[PLEView] main_window type: {type(main_window)}")
            profile_hint = (
                getattr(GlobalState, "selected_profile_path", None)
                or (GlobalState.selected_profile.get("path") if isinstance(GlobalState.selected_profile, dict) else None)
                or getattr(GlobalState, "current_profile_dir", None)
            )
            try:
                # Si tu widget acepta env_id en el constructor
                self.sites_keywords_window = SitesKeywordsSyncWidget(
                    self,
                    user_id=GlobalState.user_id,
                    ple_id=env_id,
                    env_id=env_id,
                    main_window=main_window,
                    selected_profile=GlobalState.selected_profile,
                    profile_hint=profile_hint
                )
            except TypeError:
                # Compatibilidad: pasarlo luego
                self.sites_keywords_window = SitesKeywordsSyncWidget(
                    self,
                    selected_profile=GlobalState.selected_profile,
                    profile_hint=profile_hint
                )
                if hasattr(self.sites_keywords_window, "set_environment_id"):
                    self.sites_keywords_window.set_environment_id(env_id)
                else:
                    # Fallback: atributo público
                    self.sites_keywords_window.environment_id = env_id

            # Centrar
            if main_window:
                main_rect = main_window.geometry()
                window_rect = self.sites_keywords_window.geometry()
                x = main_rect.x() + (main_rect.width() - window_rect.width()) // 2
                y = main_rect.y() + (main_rect.height() - window_rect.height()) // 2
                self.sites_keywords_window.move(max(0, x), max(0, y))

            self.sites_keywords_window.show()
            self.sites_keywords_window.raise_()
            self.sites_keywords_window.activateWindow()
            print("✅ Ventana de gestión de sitios y palabras clave abierta")

        except ImportError as e:
            print(f"Error importing SitesKeywordsSyncWidget: {e}")
            QMessageBox.warning(self, "Error", "No se pudo cargar la gestión de sitios y palabras clave.")
        except Exception as e:
            print(f"Error opening sites keywords sync: {e}")
            QMessageBox.critical(self, "Error", f"Error al abrir la gestión: {str(e)}")

    def load_ples(self, auto_open: bool = True, show_mosaic: bool = True):

        self._ensure_grid()

        """
        Carga la lista de PLEs y muestra mosaico.
        """
        # 0) Limpiar UI actual (grid y tabs)
        for i in reversed(range(self.grid.count())):
            item = self.grid.itemAt(i)
            w = item.widget() if item else None
            if w:
                w.setParent(None)

        if hasattr(self, "tabs"):
            self.tabs.setParent(None)
            del self.tabs

        # 1) Cargar PLEs del servidor (una sola vez)
        try:
            resp = requests.get(
                f"{API_BASE}/PLE/user/{self.user_id}",
                headers=_auth_headers(),
                timeout=10
            )
            resp.raise_for_status()
            self.ple_data = resp.json() or []
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los PLEs:\n{e}")
            return

        # 2) Sembrar / asegurar preferencias para cada PLE cargado
        for p in self.ple_data:
            env = p.get("environmentID")
            try:
                if env is not None:
                    ensure_server_prefs(int(env), self.user_id)
            except Exception as e:
                print(f"[bootstrap prefs] env {env}: {e}")

        if auto_open and self.ple_data:
            last_env_id = _leer_ultimo_env_id()
            if last_env_id is not None:
                match = next((p for p in self.ple_data if str(p.get("environmentID")) == str(last_env_id)), None)
                if match:
                    # Abre directamente la vista del último PLE y evita dibujar el mosaico
                    self.on_select_ple(match)
                    return

        # 3) Renderizar mosaico solo si show_mosaic es True
        if not show_mosaic:
            # Hide mosaic elements when directly opening a PLE
            self.scroll.hide()
            self.no_ple_button.hide()
            return

        # 3) Renderizar mosaico
        self.scroll.show()
        self.no_ple_button.show()

        # Reset keyboard navigation
        self.ple_cards = []
        self.selected_card_index = 0

        # Población del grid
        cols = 1
        for idx, ple in enumerate(self.ple_data or []):
            if not isinstance(ple, dict):
                continue
            frm = QFrame()
            frm.setMinimumSize(280, 85)
            frm.setMaximumSize(500, 105)
            frm.setCursor(Qt.PointingHandCursor)

            # Store original state and index
            frm.setProperty("ple_data", ple)
            frm.setProperty("card_index", idx)

            frm.setStyleSheet("""
                QFrame {
                    background-color: #5a155b;
                    border: none;
                    border-radius: 6px;
                }
                QFrame:hover {
                    background-color: #6b1a6d;
                    border: 2px solid rgba(255, 255, 255, 0.6);
                }
            """)

            vl = QVBoxLayout(frm)
            vl.setContentsMargins(0, 0, 0, 0)
            vl.setSpacing(0)

            # PLE name
            lbl = QLabel(ple.get("name", "PLE sin nombre"))
            lbl.setWordWrap(True)
            lbl.setStyleSheet("""
                font-weight: 600;
                font-size: 14px;
                color: #ffffff;
                background: transparent;
                padding: 10px;
            """)
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            vl.addWidget(lbl)

            # Make the entire frame clickable
            frm.mousePressEvent = lambda event, p=ple: self.on_select_ple(p)

            # Add to cards list for keyboard navigation
            self.ple_cards.append(frm)

            row = idx // cols
            col = idx % cols
            self.grid.addWidget(frm, row, col)

        # Highlight first card by default if there are cards
        if self.ple_cards:
            self._highlight_selected_card()
    
    def imprimir_valor_entry(self):
        valor = self.entry_opcion1.text()
        print("Texto ingresado en opción 1:", valor)

    def _change_ple(self):
        self._stop_realtime_tracker()
        self.load_ples(auto_open=False)

    def on_select_ple(self, ple):
        """
        Al seleccionar un curso, muestra vistas de detalle en pestañas.
        Optimizado para cargar rápidamente.
        """
        # Detiene un seguimiento previo si lo hubiera
        self._stop_realtime_tracker()
        self.active_ple = ple
        self._approved_clicked = False

        # Ensure we have valid PLE data
        if not ple or not isinstance(ple, dict):
            print("Warning: Invalid PLE data received")
            return

        # 1) Validar primero
        env_id_raw = ple.get('environmentID', None)
        try:
            env_id = int(env_id_raw)
        except (TypeError, ValueError):
            env_id = None

        if env_id is None:
            QMessageBox.warning(self, "PLE sin ID válido",
                                f"El PLE seleccionado no trae un environmentID válido (recibido: {env_id_raw}).")
            self.scroll.show()
            self.no_ple_button.show()
            return

        # 2) Guardar ID localmente (sin bloquear UI)
        try:
            path_txt = _resolver_guardar_id_ple()
            with open(path_txt, "w", encoding="utf-8") as f:
                f.write(f"pleseleccionado={env_id}")
        except Exception as e:
            print("[save ple id] error:", e)

        # 3) Ocultar mosaico inmediatamente para respuesta rápida
        self.scroll.hide()
        self.no_ple_button.hide()

        # 4) Crear tabs con lazy loading
        if hasattr(self, "tabs") and self.tabs:
            self.tabs.setParent(None)
            self.tabs.deleteLater()

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
            }
            QTabBar::tab {
                min-width: 130px;
                max-width: 200px;
                padding: 8px 12px;
                margin: 2px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #f5f5f5;
                font-size: 13px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background-color: #5a155b;
                color: white;
                border-color: #5a155b;
            }
            QTabBar::tab:hover {
                background-color: #f8f4f9;
                border-color: #5a155b;
            }
        """)
        self.tabs.setMinimumHeight(400)
        self.main_layout.addWidget(self.tabs)

        # Track which tabs have been loaded
        self._loaded_tabs = set()

        # Create placeholder widgets for all tabs
        self.tab_inicio_widget = None
        self.tab_preferencias_widget = None
        self.tab_cambiar_widget = None

        # Add empty placeholders
        self.tabs.addTab(QWidget(), "Inicio")
        self.tabs.addTab(QWidget(), "Preferencias")
        self.tabs.addTab(QWidget(), "Cambiar PLE")

        # Connect tab change event for lazy loading
        self.tabs.currentChanged.connect(self._on_tab_changed)

        # Load first tab immediately
        self._load_tab_content(0)

        # Async: sync preferences in background
        QTimer.singleShot(100, lambda: self._async_sync_prefs(env_id))

    def _async_sync_prefs(self, env_id):
        """Sync preferences in background without blocking UI"""
        try:
            ensure_server_prefs(env_id, self.user_id)
        except Exception as e:
            print(f"[async prefs sync] error: {e}")

    def _on_tab_changed(self, index):
        """Load tab content when user switches to it (lazy loading)"""
        if index not in self._loaded_tabs:
            self._load_tab_content(index)

    def _load_tab_content(self, index):
        """Load specific tab content"""
        if index in self._loaded_tabs:
            return

        self._loaded_tabs.add(index)

        if index == 0:  # Inicio
            self._create_inicio_tab()
        elif index == 1:  # Preferencias
            self._create_preferencias_tab()
        elif index == 2:  # Cambiar PLE
            self._create_cambiar_ple_tab()

    def _create_inicio_tab(self):
        """Create Inicio tab content"""
        ple = self.active_ple
        if not ple:
            return

        tab_inicio = QWidget()
        # Enhanced tab container for better visibility
        tab_inicio.setMinimumSize(450, 350)
        tab_inicio.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
        """)
        
        li = QVBoxLayout(tab_inicio)
        li.setContentsMargins(20, 20, 20, 20)  # Generous margins for readability
        li.setSpacing(15)  # Clear spacing between elements
        
        # Enhanced title with better visibility
        title_text = ple.get('name', 'PLE Sin Nombre')
        #***************************************************************** Code added by UAA Team 21-08-2025

        env_id_raw = ple.get('environmentID', None)
        try:
            env_id = int(env_id_raw)
        except (TypeError, ValueError):
            QMessageBox.warning(self, "PLE sin ID válido",
                                f"El PLE seleccionado no trae un environmentID válido (recibido: {env_id_raw}).")
            env_id = None

        if env_id is None:
            return

        if env_id is not None:
            try:
                ensure_server_prefs(env_id, self.user_id)
                path_txt = _resolver_guardar_id_ple()
                with open(path_txt, "w", encoding="utf-8") as f:
                    f.write(f"pleseleccionado={env_id}")
            except Exception as e:
                print("[bootstrap prefs] on_select_ple:", e)
                QMessageBox.critical(self, "Error", f"No se pudo guardar el ID del PLE:\n{e}")
                return

        #***************************************************************** Code added by UAA Team 21-08-2025
        title_label = QLabel(f"<b>{title_text}</b>")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px; 
                font-weight: bold; 
                color: #2c3e50; 
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 6px;
                border: 1px solid #dee2e6;
                margin-bottom: 15px;
            }
        """)
        title_label.setWordWrap(True)  # Allow text wrapping for long names
        title_label.setMinimumHeight(50)  # Ensure adequate height
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        li.addWidget(title_label)
        
        for label, field_key in [
            ("Tipo:", 'typePLE'),
            ("Objetivo:", 'goal'),
            ("Dominios:", 'associatedDomains'),
            ("Palabras clave:", 'associatedKeywords'),
            ("ID Entorno:", 'environmentID')
        ]:
            # FIX: Handle empty/missing data properly
            field_value = ple.get(field_key, 'No disponible')
            
            # Convert lists to readable strings
            if isinstance(field_value, list):
                field_value = ', '.join(str(item) for item in field_value) if field_value else 'Ninguno'
            elif isinstance(field_value, dict):
                field_value = 'Configuración compleja' if field_value else 'No configurado'
            elif not field_value or str(field_value).strip() == '':
                field_value = 'No especificado'
            else:
                # Ensure it's a string and limit length for display
                field_value = str(field_value)
                if len(field_value) > 200:
                    field_value = field_value[:200] + '...'
            
            info_label = QLabel(f"<b>{label}</b> {field_value}")
            info_label.setWordWrap(True)  # Prevent text cutoff for long content
            info_label.setStyleSheet("""
                QLabel {
                    font-size: 14px; 
                    color: #2c3e50;
                    background-color: transparent;
                    padding: 8px;
                    border: none;
                    margin-bottom: 5px;
                }
            """)
            info_label.setMinimumHeight(30)  # Ensure enough height for text
            li.addWidget(info_label)

        # Replace placeholder with actual content
        self.tabs.removeTab(0)
        self.tabs.insertTab(0, tab_inicio, "Inicio")
        self.tab_inicio_widget = tab_inicio

    def _create_preferencias_tab(self):
        """Create Preferencias tab content"""
        ple = self.active_ple
        if not ple:
            return

        tab_seg = QWidget(); ls = QVBoxLayout(tab_seg)
        ls.setContentsMargins(15, 15, 15, 15)  # Better margins for readability
        ls.setSpacing(12)  # Proper spacing between elements
        
        freq_label = QLabel("Frecuencia de transmisión:")
        freq_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        ls.addWidget(freq_label)
        
        self.checkboxes = []
        opciones = [
            "Seguimiento de toda la actividad",
            "Seguimiento solo de la actividad aprobada", 
            "No realizar seguimiento de la actividad",
            "Transmitir todo lo nuevo (al final de la sesión)"
        ]
        
        self.track_group = QButtonGroup(self)
        self.track_group.setExclusive(True)
        # Mapas índice <-> modo
        self.mode_map = {0: "all", 1: "approved", 2: "none", 3: "logout"}

        # Cargar preferencia guardada para este PLE
        env_id_raw = ple.get("environmentID")
        try:
            env_id_int = int(env_id_raw)
        except (TypeError, ValueError):
            env_id_int = None

        saved = {"mode": "none", "frequency": 0}
        if env_id_int is not None:
            saved = _get_pref_for_user_env(self.user_id, env_id_int) or saved

        # 1) intenta traer del servidor
        try:
            if env_id_int is not None:
                srv = fetch_server_prefs(env_id_int, self.user_id)
                saved = {"mode": srv["mode"], "frequency": srv["frequency"]}
                _set_pref_for_user_env(self.user_id, env_id_int, saved["mode"], saved["frequency"])
        except Exception:
            pass

        self.checkboxes = []
        self.track_group.setExclusive(True)

        for i, op in enumerate(opciones):
            cb = QCheckBox(op)
            cb.setStyleSheet("font-size: 13px; padding: 5px; margin-bottom: 3px;")
            cb.setMinimumHeight(25)
            self.track_group.addButton(cb, i)
            self.checkboxes.append(cb)

            if i == 0:
                h_layout = QHBoxLayout()
                h_layout.addWidget(cb)
                h_layout.addSpacing(10)  # Add spacing between checkbox and input
                self.entry_opcion1 = QLineEdit()
                self.entry_opcion1.setPlaceholderText("Ingrese frecuencia...")
                self.entry_opcion1.setFixedWidth(150)
                self.entry_opcion1.setFixedHeight(30)
                self.entry_opcion1.setText(str(saved.get("frequency", 0)))
                cb.clicked.connect(self.imprimir_valor_entry)
                h_layout.addWidget(self.entry_opcion1)
                h_layout.addSpacing(10)  # Add spacing between input and label

                # Add label for unit
                unit_label = QLabel("enlaces visitados")
                unit_label.setStyleSheet("font-size: 13px; color: #6c757d;")
                h_layout.addWidget(unit_label)
                h_layout.addStretch()  # Push everything to the left

                container = QWidget()
                container.setLayout(h_layout)
                ls.addWidget(container)
            else:
                if i == 1:
                    cb.clicked.connect(self.on_second_checkbox_clicked)
                ls.addWidget(cb)

        index_from_mode = {"all": 0, "approved": 1, "none": 2, "logout": 3}
        index_to_check = index_from_mode.get(saved.get("mode", "none"), 2)
        btn_to_check = self.track_group.button(index_to_check)
        if btn_to_check:
            btn_to_check.setChecked(True)


        """
        for i, op in enumerate(opciones):
            cb = QCheckBox(op)
            cb.setStyleSheet("font-size: 13px; padding: 5px; margin-bottom: 3px;")
            cb.setMinimumHeight(25)  # Ensure enough height for text
            
            # Connect second checkbox to show sites and keywords widget
            if i == 1:  # "Seguimiento solo de la actividad aprobada"
                cb.clicked.connect(self.on_second_checkbox_clicked)
            
            self.track_group.addButton(cb, i)
            ls.addWidget(cb)
            self.checkboxes.append(cb)
        
        self.track_group.button(2).setChecked(True)
        """
        


        # Mapeo de índice -> modo
        # 0: "Seguimiento de toda la actividad"         -> "all"
        # 1: "Seguimiento solo de la actividad aprobada"-> "approved"
        # 2: "No realizar seguimiento de la actividad"  -> "none"
        # 3: "Transmitir todo lo nuevo (al final de la sesión)" -> "logout"
        
        btn_conf = QPushButton("Confirmar")
        btn_conf.setStyleSheet("""
            QPushButton {
                background-color: #5a155b; color: white; font-weight: 500;
                padding: 10px 20px; border: none; border-radius: 6px;
                font-size: 14px; min-height: 20px;
            }
            QPushButton:hover { background-color: #481244; }
            QPushButton:pressed { background-color: #3d0f37; }
        """)
        
        
        
        btn_conf.clicked.connect(self.confirmar_seguimiento)        
        ls.addWidget(btn_conf, alignment=Qt.AlignCenter)
        
        """
        # Create a QTextEdit widget
        text_editor = QTextEdit(self)
        text_editor.setPlaceholderText("Default 5...") # Optional placeholder
        
        ls.addWidget(text_editor,alignment=Qt.AlignCenter)
        """

        # Replace placeholder with actual content
        self.tabs.removeTab(1)
        self.tabs.insertTab(1, tab_seg, "Preferencias")
        self.tab_preferencias_widget = tab_seg

    def _create_cambiar_ple_tab(self):
        """Create Cambiar PLE tab content"""
        tab_camb = QWidget(); lc = QVBoxLayout(tab_camb)
        lc.setContentsMargins(15, 15, 15, 15)
        lc.setSpacing(15)

        change_label = QLabel("¿Deseas cambiar a otro PLE?")
        change_label.setStyleSheet("font-size: 14px; color: #2c3e50; margin-bottom: 10px;")
        change_label.setAlignment(Qt.AlignCenter)
        lc.addWidget(change_label)

        btn_camb = QPushButton("Cambiar de PLE")
        btn_camb.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c; color: white; font-weight: 500;
                padding: 12px 25px; border: none; border-radius: 6px;
                font-size: 14px; min-height: 20px; min-width: 150px;
            }
            QPushButton:hover { background-color: #c0392b; }
            QPushButton:pressed { background-color: #a93226; }
        """)
        btn_camb.clicked.connect(self._change_ple)
        lc.addWidget(btn_camb, alignment=Qt.AlignCenter)

        # Replace placeholder with actual content
        self.tabs.removeTab(2)
        self.tabs.insertTab(2, tab_camb, "Cambiar PLE")
        self.tab_cambiar_widget = tab_camb

        # Skip old commented code
        """tab_rec = QWidget(); lr = QVBoxLayout(tab_rec)
        lr.setContentsMargins(15, 15, 15, 15)  # Better margins for readability
        lr.setSpacing(12)  # Proper spacing between elements
        
        rec_label = QLabel("Publicar recomendación:")
        rec_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        lr.addWidget(rec_label)
        
        self.pub_input = QLineEdit()
        self.pub_input.setPlaceholderText("Escribe tu recomendación aquí...")
        self.pub_input.setStyleSheet(
            QLineEdit {
                padding: 10px; border: 2px solid #ecf0f1; border-radius: 6px;
                font-size: 13px; background-color: #ffffff;
                min-height: 20px;
            }
            QLineEdit:focus { border-color: #5a155b; }
            QLineEdit:hover { border-color: #bdc3c7; }
       )
        lr.addWidget(self.pub_input)
        
        self.pub_list = QListWidget()
        self.pub_list.setStyleSheet(
            QListWidget {
                border: 1px solid #ecf0f1; border-radius: 6px;
                background-color: #ffffff; font-size: 13px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px; border-bottom: 1px solid #f1f1f1;
                min-height: 20px;
            }
            QListWidget::item:selected {
                background-color: rgba(90, 21, 91, 0.1);
                color: #5a155b;
            }
       )
        lr.addWidget(self.pub_list)
        
        btn_pub = QPushButton("Publicar")
        btn_pub.setStyleSheet(
            QPushButton {
                background-color: #3498db; color: white; font-weight: 500;
                padding: 10px 20px; border: none; border-radius: 6px;
                font-size: 14px; min-height: 20px;
            }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:pressed { background-color: #21618c; }
        )
        btn_pub.clicked.connect(self.add_publicacion)
        lr.addWidget(btn_pub, alignment=Qt.AlignCenter)
        self.tabs.addTab(tab_rec, "Recomendaciones")"""

        # Inicia Código Tab Preferencias
        """entorno = ple.get('environmentID')
        if entorno:
            tab_pref = QWidget(); lp = QVBoxLayout(tab_pref)
            txt = QTextEdit(); txt.setReadOnly(True); lp.addWidget(txt)
            try:
                resp = requests.get(f"{API_BASE}/preferences/{entorno}"); resp.raise_for_status(); prefs = resp.json()
                txt.setPlainText(json.dumps(prefs, indent=2, ensure_ascii=False))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudieron obtener preferencias:\n{e}")
            self.tabs.addTab(tab_pref, "Preferencias")"""
        # Termina Código Tab Preferencias    
    
    """def on_tab_changed(self, index):
        
        #Manejador para el cambio de pestañas
        

        # Obtenemos el texto de la pestaña que el usuario ha seleccionado
        tab_text = self.tabs.tabText(index)

        # Verificamos si la pestaña seleccionada es "Cambiar PLE"
        if tab_text == "Cambiar PLE":
        
            # Cargamos los PLE's
            self.load_ples()"""

    def open_ple_section(self, ple, section):
        """
        Opens a specific section of a PLE directly without tabs.
        Args:
            ple: PLE data dictionary
            section: Section to open ('inicio', 'preferencias', 'cambiar_ple')
        """
        # Store active PLE
        self.active_ple = ple
        self._approved_clicked = False

        # Validate PLE data
        if not ple or not isinstance(ple, dict):
            print("Warning: Invalid PLE data received")
            return

        env_id_raw = ple.get('environmentID', None)
        try:
            env_id = int(env_id_raw)
        except (TypeError, ValueError):
            QMessageBox.warning(self, "PLE sin ID válido",
                                f"El PLE seleccionado no trae un environmentID válido.")
            return

        # Ensure preferences are bootstrapped
        try:
            ensure_server_prefs(env_id, self.user_id)
            path_txt = _resolver_guardar_id_ple()
            with open(path_txt, "w", encoding="utf-8") as f:
                f.write(f"pleseleccionado={env_id}")
        except Exception as e:
            print(f"[bootstrap prefs] open_ple_section: {e}")

        # Hide mosaic elements
        self.scroll.hide()
        self.no_ple_button.hide()

        # Remove any existing tabs
        if hasattr(self, "tabs"):
            self.tabs.setParent(None)
            del self.tabs

        # Create the specific section content directly
        if section == "inicio":
            self._create_inicio_section(ple, env_id)
        elif section == "preferencias":
            self._create_preferencias_section(ple, env_id)
        elif section == "cambiar_ple":
            self._create_cambiar_ple_section()

    def _create_inicio_section(self, ple, env_id):
        """Create the Inicio section content."""
        # Create a scroll area for the section
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        # Create a container widget for the section
        section_widget = QWidget()
        section_layout = QVBoxLayout(section_widget)
        section_layout.setContentsMargins(25, 20, 25, 20)  # Reduced margins
        section_layout.setSpacing(12)  # Reduced spacing

        # PLE name as header
        ple_name = ple.get('name', 'PLE')
        name_label = QLabel(ple_name)
        name_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #5a155b;
                padding: 12px 0px;
                border-bottom: 2px solid #5a155b;
                margin-bottom: 15px;
            }
        """)
        name_label.setWordWrap(True)
        section_layout.addWidget(name_label)

        # PLE information fields in a clean list
        info_fields = [
            ("Tipo", 'typePLE'),
            ("Objetivo", 'goal'),
            ("Dominios", 'associatedDomains'),
            ("Palabras clave", 'associatedKeywords'),
            ("ID Entorno", 'environmentID')
        ]

        for label, field_key in info_fields:
            field_value = ple.get(field_key, 'No disponible')

            if isinstance(field_value, list):
                field_value = ', '.join(str(item) for item in field_value) if field_value else 'Ninguno'
            elif isinstance(field_value, dict):
                field_value = 'Configuración compleja' if field_value else 'No configurado'
            elif not field_value or str(field_value).strip() == '':
                field_value = 'No especificado'
            else:
                field_value = str(field_value)
                if len(field_value) > 200:
                    field_value = field_value[:200] + '...'

            # Create field container
            field_container = QFrame()
            field_container.setStyleSheet("""
                QFrame {
                    background-color: #f8f9fa;
                    border-radius: 6px;
                    padding: 10px;
                    margin: 4px 0px;
                }
            """)
            field_layout = QVBoxLayout(field_container)
            field_layout.setContentsMargins(12, 10, 12, 10)
            field_layout.setSpacing(5)

            # Label
            label_widget = QLabel(f"<b>{label}</b>")
            label_widget.setStyleSheet("font-size: 13px; color: #6c757d;")
            field_layout.addWidget(label_widget)

            # Value
            value_widget = QLabel(field_value)
            value_widget.setWordWrap(True)
            value_widget.setStyleSheet("font-size: 14px; color: #2c3e50;")
            field_layout.addWidget(value_widget)

            section_layout.addWidget(field_container)

        # Add stretch at the bottom to push content to top
        section_layout.addStretch()

        # Set the widget to scroll area and add to main layout
        scroll_area.setWidget(section_widget)
        self.main_layout.addWidget(scroll_area)

    def _create_preferencias_section(self, ple, env_id):
        """Create the Preferencias section content."""
        # Create a scroll area for the section
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        section_widget = QWidget()
        section_layout = QVBoxLayout(section_widget)
        section_layout.setContentsMargins(2, 10, 2, 10)  # Ultra minimal horizontal margins
        section_layout.setSpacing(6)  # Very tight spacing

        # Title section
        title_label = QLabel("Configuración de Seguimiento")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #5a155b;
                padding: 8px 0px;
                border-bottom: 2px solid #5a155b;
                margin-bottom: 10px;
            }
        """)
        section_layout.addWidget(title_label)

        freq_label = QLabel("Selecciona tu preferencia:")
        freq_label.setStyleSheet("font-size: 12px; color: #6c757d; margin-bottom: 8px;")
        freq_label.setWordWrap(True)
        section_layout.addWidget(freq_label)

        # Create tracking options container with proper spacing
        self.checkboxes = []
        opciones = [
            "Seguimiento de toda la actividad",
            "Seguimiento solo de la actividad aprobada",
            "No realizar seguimiento de la actividad",
            "Transmitir todo lo nuevo (al final de la sesión)"
        ]

        self.track_group = QButtonGroup(self)
        self.track_group.setExclusive(True)
        self.mode_map = {0: "all", 1: "approved", 2: "none", 3: "logout"}

        # Load saved preferences
        saved = {"mode": "none", "frequency": 0}
        if env_id is not None:
            saved = _get_pref_for_user_env(self.user_id, env_id) or saved

        try:
            srv = fetch_server_prefs(env_id, self.user_id)
            saved = {"mode": srv["mode"], "frequency": srv["frequency"]}
            _set_pref_for_user_env(self.user_id, env_id, saved["mode"], saved["frequency"])
        except Exception:
            pass

        # Options container with background
        options_container = QFrame()
        options_container.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 6px;
                border: 1px solid #dee2e6;
                padding: 12px;
            }
        """)
        options_layout = QVBoxLayout(options_container)
        options_layout.setSpacing(6)  # Very tight spacing
        options_layout.setContentsMargins(5, 8, 5, 8)  # Ultra minimal margins

        for i, op in enumerate(opciones):
            # Create option container for proper alignment
            option_frame = QFrame()
            option_layout = QHBoxLayout(option_frame)
            option_layout.setContentsMargins(0, 0, 0, 0)
            option_layout.setSpacing(15)

            cb = QCheckBox(op)
            cb.setStyleSheet("""
                QCheckBox {
                    font-size: 14px;
                    color: #2c3e50;
                    padding: 8px;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    border-radius: 10px;
                    border: 2px solid #5a155b;
                }
                QCheckBox::indicator:checked {
                    background-color: #5a155b;
                    border: 2px solid #5a155b;
                }
                QCheckBox::indicator:unchecked {
                    background-color: white;
                }
            """)
            cb.setMinimumHeight(35)
            self.track_group.addButton(cb, i)
            self.checkboxes.append(cb)

            option_layout.addWidget(cb)

            if i == 0:
                # Add frequency input for first option
                self.entry_opcion1 = QLineEdit()
                self.entry_opcion1.setPlaceholderText("Ej: 5, 10, 15...")
                self.entry_opcion1.setFixedWidth(150)
                self.entry_opcion1.setFixedHeight(35)
                self.entry_opcion1.setText(str(saved.get("frequency", 0)))
                self.entry_opcion1.setStyleSheet("""
                    QLineEdit {
                        border: 2px solid #ced4da;
                        border-radius: 6px;
                        padding: 8px 12px;
                        font-size: 13px;
                        background-color: white;
                    }
                    QLineEdit:focus {
                        border-color: #5a155b;
                    }
                """)
                cb.clicked.connect(self.imprimir_valor_entry)
                option_layout.addWidget(self.entry_opcion1)

                # Add label for frequency
                freq_unit = QLabel("enlaces visitados")
                freq_unit.setStyleSheet("font-size: 13px; color: #6c757d;")
                option_layout.addWidget(freq_unit)
            else:
                if i == 1:
                    cb.clicked.connect(self.on_second_checkbox_clicked)

            option_layout.addStretch()
            options_layout.addWidget(option_frame)

        section_layout.addWidget(options_container)

        # Set saved selection
        index_from_mode = {"all": 0, "approved": 1, "none": 2, "logout": 3}
        index_to_check = index_from_mode.get(saved.get("mode", "none"), 2)
        btn_to_check = self.track_group.button(index_to_check)
        if btn_to_check:
            btn_to_check.setChecked(True)

        # Add spacing before button
        section_layout.addSpacing(20)

        # Confirm button
        btn_conf = QPushButton("Guardar Preferencias")
        btn_conf.setStyleSheet("""
            QPushButton {
                background-color: #5a155b; color: white; font-weight: 600;
                padding: 14px 28px; border: none; border-radius: 8px;
                font-size: 15px; min-height: 25px; min-width: 180px;
            }
            QPushButton:hover {
                background-color: #481244;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background-color: #3d0f37;
            }
        """)
        btn_conf.setCursor(Qt.PointingHandCursor)
        btn_conf.clicked.connect(self.confirmar_seguimiento)
        section_layout.addWidget(btn_conf, alignment=Qt.AlignCenter)

        # Add stretch at the bottom
        section_layout.addStretch()

        # Set the widget to scroll area and add to main layout
        scroll_area.setWidget(section_widget)
        self.main_layout.addWidget(scroll_area)

    def _create_cambiar_ple_section(self):
        """Create the Cambiar PLE section content - shows PLE list."""
        # Show the PLE list with auto-open Inicio enabled
        self._show_ple_list(auto_open_inicio=True)

    def _show_ple_list(self, auto_open_inicio=False):
        """Display the PLE mosaic/list for selection.

        Args:
            auto_open_inicio: If True, automatically opens Inicio section after selection
        """
        # Stop any tracking
        self._stop_realtime_tracker()

        # Hide any existing tabs
        if hasattr(self, "tabs"):
            self.tabs.setParent(None)
            del self.tabs

        # Clear the grid
        self._ensure_grid()
        for i in reversed(range(self.grid.count())):
            item = self.grid.itemAt(i)
            w = item.widget() if item else None
            if w:
                w.setParent(None)

        # Show the scroll area and button
        self.scroll.show()
        self.no_ple_button.show()

        # Render PLE mosaic
        if self.ple_data:
            # Reset keyboard navigation
            self.ple_cards = []
            self.selected_card_index = 0

            cols = 1

            for idx, ple in enumerate(self.ple_data):
                if not isinstance(ple, dict):
                    continue

                frm = QFrame()
                frm.setMinimumSize(280, 85)
                frm.setMaximumSize(500, 105)
                frm.setCursor(Qt.PointingHandCursor)

                # Store original state and data
                frm.setProperty("ple_data", ple)
                frm.setProperty("card_index", idx)

                frm.setStyleSheet("""
                    QFrame {
                        background-color: #5a155b;
                        border: none;
                        border-radius: 6px;
                    }
                    QFrame:hover {
                        background-color: #6b1a6d;
                        border: 2px solid rgba(255, 255, 255, 0.6);
                    }
                """)

                vl = QVBoxLayout(frm)
                vl.setContentsMargins(0, 0, 0, 0)
                vl.setSpacing(0)

                # PLE name
                lbl = QLabel(ple.get("name", "PLE sin nombre"))
                lbl.setWordWrap(True)
                lbl.setStyleSheet("""
                    font-weight: 600;
                    font-size: 14px;
                    color: #ffffff;
                    background: transparent;
                    padding: 10px;
                """)
                lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                vl.addWidget(lbl)

                # Make the entire frame clickable - connect to the appropriate handler
                if auto_open_inicio:
                    frm.mousePressEvent = lambda event, p=ple: self._select_and_open_inicio(p)
                else:
                    frm.mousePressEvent = lambda event, p=ple: self.on_select_ple(p)

                # Add to cards list for keyboard navigation
                self.ple_cards.append(frm)

                row = idx // cols
                col = idx % cols
                self.grid.addWidget(frm, row, col)

            # Highlight first card by default if there are cards
            if self.ple_cards:
                self._highlight_selected_card()

    def _select_and_open_inicio(self, ple):
        """
        Selects a PLE and automatically opens its Inicio section.
        Used when selecting from Cambiar PLE.
        """
        # Validate PLE data
        if not ple or not isinstance(ple, dict):
            print("Warning: Invalid PLE data received")
            return

        env_id_raw = ple.get('environmentID', None)
        try:
            env_id = int(env_id_raw)
        except (TypeError, ValueError):
            QMessageBox.warning(self, "PLE sin ID válido",
                                f"El PLE seleccionado no trae un environmentID válido.")
            return

        # Store active PLE
        self.active_ple = ple
        self._approved_clicked = False

        # Bootstrap preferences
        try:
            ensure_server_prefs(env_id, self.user_id)
            path_txt = _resolver_guardar_id_ple()
            with open(path_txt, "w", encoding="utf-8") as f:
                f.write(f"pleseleccionado={env_id}")
        except Exception as e:
            print(f"[bootstrap prefs] _select_and_open_inicio: {e}")

        # Hide mosaic
        self.scroll.hide()
        self.no_ple_button.hide()

        # Remove any existing tabs
        if hasattr(self, "tabs"):
            self.tabs.setParent(None)
            del self.tabs

        # Directly open Inicio section
        self._create_inicio_section(ple, env_id)

    def add_publicacion(self):
        texto = self.pub_input.text().strip()
        if texto:
            self.pub_list.addItem(texto)
            self.pub_input.clear()

    def confirmar_seguimiento(self):
        """
        Registra la preferencia de seguimiento y, si aplica, ejecuta/arma.
        """
        mode = self._selected_tracking_mode()

        print("[PLEView] checkedId:", self.track_group.checkedId(), "mode:", mode)

        # Guarda estado global
        GlobalState.tracking_mode = mode
        GlobalState.tracking_armed = (mode == "logout")

        env_id = self.active_ple.get("environmentID") if self.active_ple else None
        try:
            env_id_int = int(env_id)
        except (TypeError, ValueError):
            env_id_int = None

        frequency = 0
        if hasattr(self, "entry_opcion1"):
            txt = (self.entry_opcion1.text() or "").strip()
            try:
                frequency = max(0, int(txt))
            except ValueError:
                frequency = 0

        # guardar local primero
        if env_id_int is not None:
            try:
                srv = ensure_server_prefs(env_id_int, self.user_id)
                _set_pref_for_user_env(self.user_id, env_id_int, mode, frequency)
            except Exception as e:
                print("[bootstrap prefs] no fue posible sembrar pref en servidor:", e)
                QMessageBox.warning(self, "Aviso", f"No se pudo guardar la preferencia local:\n{e}")

            # subir a server (best-effort)
            try:
                resp = put_server_prefs(env_id_int, self.user_id, mode, frequency)
                _set_pref_for_user_env(self.user_id, env_id_int, resp["mode"], resp["frequency"])
                print("[VERIFY GET] solicitando estado en servidor…")
                ver = fetch_server_prefs(env_id_int, self.user_id)
                print("[VERIFY GET] mode:", ver["mode"], "freq:", ver["frequency"], "raw:", ver["_raw"])
            except Exception:
                QMessageBox.information(
                    self, "Preferencias",
                    "Preferencia guardada localmente.\nNo se pudo sincronizar con el servidor en este momento."
                )

        if mode == "all":
            prof = GlobalState.current_profile_dir
            if not prof:
                QMessageBox.warning(self, "Perfil", "No hay perfil de Chrome seleccionado.")
                return

            # Use the same sending path as option 3 (logout) via history_service_4
            from qt_views.DashboardWindow import HistoryWorker

            env_id_val = self.active_ple.get("environmentID") if self.active_ple else None
            if env_id_val is not None:
                os.environ["EPA_SELECTED_ENV_ID"] = str(env_id_val)

            self._hist_worker = HistoryWorker(
                profile_dir=prof,
                output_dir="chrome_exports/teacher"
            )
            self._hist_worker.done.connect(lambda: QMessageBox.information(
                self, "Seguimiento",
                f"Datos enviados correctamente al servidor.\nPerfil: {prof}"
            ))
            self._hist_worker.fail.connect(lambda err: QMessageBox.critical(
                self, "Error de envío",
                f"Error al enviar datos:\n{err}"
            ))
            self._hist_worker.start()
            QMessageBox.information(self, "Seguimiento",
                f"Enviando datos del historial de Chrome...\nPerfil: {prof}")
            return

        self._stop_realtime_tracker()

        if mode == "approved":
            if env_id_int is None:
                QMessageBox.warning(self, "PLE sin ID",
                                    "No se puede configurar sitios/palabras porque el PLE no trae un environmentID válido.")
                return

            reply = QMessageBox.question(
                self, "Sitios y palabras clave",
                "¿Quieres configurar los sitios y palabras clave aprobados ahora?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.open_sites_keywords(env_id_int)
            return

        if mode == "logout":
            QMessageBox.information(self, "Seguimiento",
                                    "Se realizará la transmisión al cerrar sesión.")
            return

        if mode == "none":
            QMessageBox.information(self, "Seguimiento", "No se realizará seguimiento.")
            return


        # Solo para modos que ejecutan ahora mismo (all / approved)
        prof = GlobalState.current_profile_dir
        if not prof:
            QMessageBox.warning(self, "Perfil", "No hay perfil de Chrome seleccionado.")
            return

        urls = self.get_recent_urls(prof, limit=10)
        if not urls:
            QMessageBox.information(self, "Sin historial", "No se encontraron URLs recientes.")
            return

        resultado = []
        for entry in urls:
            title_or_url = entry.get('title','') or entry.get('url','')
            kws = self.extract_all_keywords(title_or_url, top_n=5)
            resultado.append({'url': entry['url'], 'keywords': kws})

        data_json = {'chrome_profile': prof, 'ple': self.active_ple.get('name'), 'results': resultado}
        fn = f"keywords_{prof}.json"
        # Use app data directory for writable location
        app_dir = _get_app_data_dir()
        keywords_dir = app_dir / "keywords"
        keywords_dir.mkdir(parents=True, exist_ok=True)
        keywords_file = keywords_dir / fn
        with open(keywords_file, 'w', encoding='utf-8') as f:
            json.dump(data_json, f, ensure_ascii=False, indent=2)
        QMessageBox.information(self, "Éxito", f"Archivo generado en:\n{keywords_file}")

    def closeEvent(self, event):
        self._stop_realtime_tracker()
        super().closeEvent(event)

    def keyPressEvent(self, event):
        """Handle keyboard navigation"""
        from PyQt5.QtCore import Qt as QtCore

        # Only handle keyboard navigation when cards are visible
        if not self.ple_cards or not self.scroll.isVisible():
            super().keyPressEvent(event)
            return

        key = event.key()

        # Navigate down with Down Arrow or Tab
        if key in (QtCore.Key_Down, QtCore.Key_Tab):
            self.selected_card_index = (self.selected_card_index + 1) % len(self.ple_cards)
            self._highlight_selected_card()
            event.accept()

        # Navigate up with Up Arrow or Shift+Tab
        elif key == QtCore.Key_Up or (key == QtCore.Key_Tab and event.modifiers() & QtCore.ShiftModifier):
            self.selected_card_index = (self.selected_card_index - 1) % len(self.ple_cards)
            self._highlight_selected_card()
            event.accept()

        # Activate selected card with Enter or Space
        elif key in (QtCore.Key_Return, QtCore.Key_Enter, QtCore.Key_Space):
            if 0 <= self.selected_card_index < len(self.ple_cards):
                card = self.ple_cards[self.selected_card_index]
                ple_data = card.property("ple_data")
                if ple_data:
                    self.on_select_ple(ple_data)
            event.accept()

        else:
            super().keyPressEvent(event)

    def _highlight_selected_card(self):
        """Highlight the currently selected card for keyboard navigation"""
        for idx, card in enumerate(self.ple_cards):
            if idx == self.selected_card_index:
                # Selected state: white border
                card.setStyleSheet("""
                    QFrame {
                        background-color: #5a155b;
                        border: 2px solid #ffffff;
                        border-radius: 6px;
                    }
                    QFrame:hover {
                        background-color: #6b1a6d;
                        border: 2px solid rgba(255, 255, 255, 0.9);
                    }
                """)
                # Scroll to make sure the selected card is visible
                self.scroll.ensureWidgetVisible(card)
            else:
                # Normal state: no border
                card.setStyleSheet("""
                    QFrame {
                        background-color: #5a155b;
                        border: none;
                        border-radius: 6px;
                    }
                    QFrame:hover {
                        background-color: #6b1a6d;
                        border: 2px solid rgba(255, 255, 255, 0.6);
                    }
                """)

    def extract_all_keywords(self, raw_text, top_n=5):
        resultados = {}
        self.rake_extractor.extract_keywords_from_text(raw_text)
        resultados['rake'] = self.rake_extractor.get_ranked_phrases()[:top_n]
        doc = self.spacy_nlp(raw_text)
        cleaned = ' '.join(tok.lemma_.lower() for tok in doc if tok.is_alpha and not tok.is_stop)
        text_for_kb = cleaned if len(cleaned.split())>=50 else raw_text
        
        if self.keybert_model:
            try:
                kws_kb = self.keybert_model.extract_keywords(text_for_kb, keyphrase_ngram_range=(1,2), stop_words='spanish', top_n=top_n)
                resultados['keybert'] = [kw for kw,_ in kws_kb]
            except:
                resultados['keybert'] = []
        else:
            resultados['keybert'] = []
        try:
            yake_list = sorted(self.yake_extractor.extract_keywords(raw_text), key=lambda x: x[1])[:top_n]
            resultados['yake'] = [kw for kw,_ in yake_list]
        except:
            resultados['yake'] = []
        counts = {}
        for chunk in doc.noun_chunks:
            txt = chunk.text.lower().strip(); counts[txt] = counts.get(txt, 0)+1
        resultados['spacy'] = sorted(counts, key=counts.get, reverse=True)[:top_n]
        return resultados

    def get_recent_urls(self, profile_dir, limit=5):
        system = platform.system()
        if system=='Windows': base = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
        elif system=='Darwin': base = os.path.expanduser("~/Library/Application Support/Google/Chrome")
        else: base = os.path.expanduser("~/.config/google-chrome")
        history = os.path.join(base, profile_dir, 'History')
        if not os.path.isfile(history): return []
        tmp = os.path.join(tempfile.gettempdir(), f"History_{profile_dir}.db")
        shutil.copy2(history, tmp)
        conn = sqlite3.connect(tmp); cur = conn.cursor()
        cur.execute("SELECT DISTINCT url, title FROM urls ORDER BY last_visit_time DESC LIMIT ?", (limit,))
        rows = cur.fetchall(); conn.close(); os.remove(tmp)
        return [{'url': u, 'title': t} for u,t in rows]

    def on_second_checkbox_clicked(self, checked):
        """Handle click on second checkbox to open Sites and Keywords window."""
        self._approved_clicked = bool(checked)
        # Si la desmarcan y la ventana estaba abierta, la cerramos
        if (not checked) and hasattr(self, 'sites_keywords_window') and self.sites_keywords_window:
            self.sites_keywords_window.close()
    
    def _selected_tracking_mode(self) -> str:
        bid = self.track_group.checkedId()
        return self.mode_map.get(bid, "none")

    def show_sync_summary(self):
        """Show the synchronization summary in a separate window."""
        # Import the fast sync summary widget
        from .SyncSummaryWidget import SyncSummaryWidget
        
        # Create and show sync summary window
        self.sync_summary_window = SyncSummaryWidget(self)
        
        # Center the window on the main application
        if self.parent():
            # Get the main window geometry
            main_window = self.window()
            if main_window:
                main_rect = main_window.geometry()
                window_rect = self.sync_summary_window.geometry()
                
                # Calculate center position
                x = main_rect.x() + (main_rect.width() - window_rect.width()) // 2
                y = main_rect.y() + (main_rect.height() - window_rect.height()) // 2
                
                self.sync_summary_window.move(max(0, x), max(0, y))
        
        # Show the window
        self.sync_summary_window.show()
        self.sync_summary_window.raise_()
        self.sync_summary_window.activateWindow()
        
        print("✅ Ventana de sincronización abierta")
    
