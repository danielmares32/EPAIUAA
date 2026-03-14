# qt_views/ple/PLEView.py

import sys
import os
import json
import requests
import sqlite3
import tempfile
import shutil
import platform
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QCheckBox,
    QPushButton, QScrollArea, QGridLayout, QMessageBox,
    QTabWidget, QTextEdit, QLineEdit, QListWidget, QButtonGroup
)
from PyQt5.QtCore import Qt
from qt_views.global_state import GlobalState

# Importadores de extracción de keywords
from rake_nltk import Rake
from keybert import KeyBERT
import yake
import spacy



API_BASE = "https://uninovadeplan-ws.javali.pt"
#DEFAULT_PLE_USER_ID = 295  # Usuario por defecto si no se recibe uno

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
DEFAULT_PLE_USER_ID = int(userIDThisFile)  
print(f"DEFAULT_PLE_USER_ID: {DEFAULT_PLE_USER_ID}")
 

#*********************************************************Modificado por Equipo UAA 18-08-2025

class PLEView(QWidget):
    """
    Vista PLE: mosaico de cursos y detalle en pestañas.
    """
    def __init__(self, parent=None, user_id=None, current_profile=None):
        super().__init__(parent)
        # Asignar user_id, si no se recibe usar valor por defecto
        self.user_id = user_id or DEFAULT_PLE_USER_ID
        self.current_profile = current_profile
        self.ple_data = []
        self.active_ple = None
        mi_variable_global = "Este es mi valor" 



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

        # Layout principal
        self.main_layout = QVBoxLayout(self)
        # Ajustar márgenes para alinear mejor al diseño
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # Título
        title = QLabel("PLE Active")
        title.setAlignment(Qt.AlignHCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #5a155b; margin-bottom: 15px;")
        title.setAccessibleName("title")
        self.main_layout.addWidget(title)

        # ScrollArea con mosaico de cursos
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        container = QWidget()
        # Usar directamente QGridLayout en el container
        self.grid = QGridLayout(container)
        self.grid.setSpacing(20)
        # Márgenes internos del grid
        self.grid.setContentsMargins(25, 25, 25, 25)
        container.setLayout(self.grid)
        self.scroll.setWidget(container)
        self.main_layout.addWidget(self.scroll, stretch=1)

        # Botón alternativo si no encuentra PLE
        self.no_ple_button = QPushButton("¿No encuentras tu PLE? Da clic aquí")
        self.no_ple_button.setStyleSheet("background-color:#555; color:white; padding:8px;")
        self.no_ple_button.clicked.connect(lambda:
            QMessageBox.information(self, "Crear PLE", "Aquí abrirías el enlace para crear un PLE")
        )
        self.main_layout.addWidget(self.no_ple_button, alignment=Qt.AlignCenter)

        # Carga inicial de cursos
        self.load_ples()

    def load_ples(self):
        """
        Carga la lista de PLEs y muestra mosaico.
        """
        # Limpiar grid actual
        for i in reversed(range(self.grid.count())):
            w = self.grid.itemAt(i).widget()
            if w:
                w.setParent(None)
        # Eliminar vistas de detalle previas
        if hasattr(self, 'tabs'):
            self.tabs.setParent(None)
            del self.tabs
        # Mostrar mosaico de nuevo
        self.scroll.show()
        self.no_ple_button.show()

        # Petición HTTP
        try:
            resp = requests.get(f"{API_BASE}/PLE/user/{self.user_id}", timeout=10)
            resp.raise_for_status()
            self.ple_data = resp.json()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los PLEs:\n{e}")
            return

        # Población del grid
        for idx, ple in enumerate(self.ple_data):
            frame = QFrame()
            color = ["#72B2E4", "#F589C5", "#7BE7E1", "#D6D6D6"][idx % 4]
            frame.setStyleSheet(f"background-color:{color}; padding:12px; border-radius:8px;")
            frame.setMinimumSize(420, 140)  # Increased for better text visibility
            frame.setMaximumSize(500, 180)  # Allow some flexibility

            v = QVBoxLayout(frame)
            v.setContentsMargins(10, 10, 10, 10)  # Better margins
            v.setSpacing(12)  # Improved spacing
            
            lbl = QLabel(f"<b>{ple['name']}</b>")
            lbl.setWordWrap(True)  # Allow text wrapping for long PLE names
            lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #2c3e50;")
            lbl.setMinimumHeight(40)  # Ensure enough height for wrapped text
            v.addWidget(lbl, alignment=Qt.AlignTop)

            btn = QPushButton("Acceder")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff; color: #5a155b; font-weight: 500;
                    padding: 10px 18px; border: 2px solid #5a155b; border-radius: 6px;
                    font-size: 14px; min-height: 22px; min-width: 100px;
                }
                QPushButton:hover { 
                    background-color: #f8f4f9; 
                    border-color: #481244;
                }
                QPushButton:pressed { 
                    background-color: #ede7ef; 
                }
            """)
            btn.clicked.connect(lambda _, p=ple: self.on_select_ple(p))
            v.addWidget(btn, alignment=Qt.AlignCenter)

            row, col = divmod(idx, 2)
            self.grid.addWidget(frame, row, col)

    def on_select_ple(self, ple):
        print("here is possible to get the environmentID")
        """
        Al seleccionar un curso, muestra vistas de detalle en pestañas.
        """
        self.active_ple = ple
        
        # Ensure we have valid PLE data
        if not ple or not isinstance(ple, dict):
            print("Warning: Invalid PLE data received")
            return
        
        # Ocultar mosaico
        self.scroll.hide()
        self.no_ple_button.hide()

        # Crear pestañas
        self.tabs = QTabWidget()
        # Fix tab text cutoff with minimum tab width and proper spacing
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
            }
            QTabBar::tab {
                min-width: 130px;  /* Increased minimum width for better text visibility */
                max-width: 200px;  /* Allow some flexibility */
                padding: 8px 12px; /* Better padding for text */
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
        self.tabs.setMinimumHeight(400)  # Ensure enough height for content
        self.main_layout.addWidget(self.tabs)

        # Tab Inicio
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
        idPLE = ple.get('environmentID','PLE without ID')
        print(f"ID from selected PLE:{idPLE}")
        #C:\000_PLE_Active\tracke4\qt_views\ple  C:\000_PLE_Active\EPAIUAAmain\qt_views\ple
        nombre_archivo = "C:\\000_PLE_Active\\EPAIUAAmain\\qt_views\\ple\\guardarIDPLE.txt"
        mi_variable = "pleseleccionado"+"="+str(idPLE)
        with open(nombre_archivo, 'w') as fichero:
            fichero.write(str(mi_variable))
        """
        nombre=Juan
        edad=30
        with open("datos.txt", "r") as archivo:
        for linea in archivo:
            # Divide la línea por el signo "=" y toma el segundo elemento (el valor)
            if "=" in linea:
                clave, valor = linea.strip().split("=")
                if clave == "nombre":
                    variable_nombre = valor
                    print(f"El nombre es: {variable_nombre}")        
        """        
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
        self.tabs.addTab(tab_inicio, "Inicio")

        # Tab Seguimiento
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
        self.mode_map = {0: "all", 1: "approved", 2: "none", 3: "logout"}

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
        self.tabs.addTab(tab_seg, "Seguimiento")

        #************************************************************************************************************** Inicia Código Pestaña Recomendaciones
        # Tab Recomendaciones
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
        #************************************************************************************************************************** Termina Código Pestaña Recomendaciones

        # Tab Cambiar PLE
        tab_camb = QWidget(); #lc = QVBoxLayout(tab_camb)
        self.tabs.addTab(tab_camb, "Cambiar PLE")
        #lc.setContentsMargins(15, 15, 15, 15)  # Better margins for readability
        #lc.setSpacing(15)  # Proper spacing between elements
        
        #change_label = QLabel("¿Deseas cambiar a otro PLE?")
        #change_label.setStyleSheet("font-size: 14px; color: #2c3e50; margin-bottom: 10px;")
        #change_label.setAlignment(Qt.AlignCenter)
        #lc.addWidget(change_label)
        
        #btn_camb = QPushButton("Cambiar de PLE")
        #btn_camb.setStyleSheet("""
        #    QPushButton {
        #        background-color: #e74c3c; color: white; font-weight: 500;
        #        padding: 12px 25px; border: none; border-radius: 6px;
        #        font-size: 14px; min-height: 20px; min-width: 150px;
        #    }
        #    QPushButton:hover { background-color: #c0392b; }
        #    QPushButton:pressed { background-color: #a93226; }
        #""")
        #btn_camb.clicked.connect(self.load_ples)
        #lc.addWidget(btn_camb, alignment=Qt.AlignCenter)
        #self.tabs.addTab(tab_camb, "Cambiar PLE")

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
    def on_tab_changed(self, index):
        """
        Manejador para el cambio de pestañas
        """
        # Obtenemos el texto de la pestaña que el usuario ha seleccionado
        tab_text = self.tabs.tabText(index)
        # Verificamos si la pestaña seleccionada es "Cambiar PLE"
        if tab_text == "Cambiar PLE":
            # Cargamos los PLE's
            self.load_ples()

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
        with open(fn, 'w', encoding='utf-8') as f:
            json.dump(data_json, f, ensure_ascii=False, indent=2)
        QMessageBox.information(self, "Éxito", f"Archivo {fn} generado.")

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
        if checked:
            try:
                # Import and open the full Sites and Keywords window
                from .SitesKeywordsSyncWidget import SitesKeywordsSyncWidget
                
                # Get the main window reference
                main_window = self.window()
                
                # Create and show the sites keywords sync window
                self.sites_keywords_window = SitesKeywordsSyncWidget(self, main_window=main_window)
                
                # Center the window on the main application
                if self.parent() and main_window:
                        main_rect = main_window.geometry()
                        window_rect = self.sites_keywords_window.geometry()
                        
                        # Calculate center position
                        x = main_rect.x() + (main_rect.width() - window_rect.width()) // 2
                        y = main_rect.y() + (main_rect.height() - window_rect.height()) // 2
                        
                        self.sites_keywords_window.move(max(0, x), max(0, y))
                
                # Show the window
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
        else:
            # Close the window if unchecked and it exists
            if hasattr(self, 'sites_keywords_window') and self.sites_keywords_window:
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
    
