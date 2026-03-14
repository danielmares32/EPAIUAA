# qt_views/DashboardWindow.py
import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QLabel, QPushButton, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from .components.Sidebar import Sidebar
from .components.Header import Header
from qt_views.ProfileWindow import ProfileWindow
from qt_views.global_state import GlobalState
from qt_views.ple.PLEView import PLEView
from services.history_service_4 import run_crawler
from multiprocessing import Process

class HistoryWorker(QThread):
    done = pyqtSignal()
    fail = pyqtSignal(str)

    def __init__(self, profile_dir=None, output_dir=None):
        super().__init__()
        self.profile_dir = profile_dir
        self.output_dir = output_dir

    def run(self):
        try:
            from services.history_service_4 import run_crawler
            run_crawler(profile_dir=self.profile_dir, output_dir=self.output_dir)
            self.done.emit()
        except Exception as e:
            self.fail.emit(str(e))

class DashboardWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Dashboard - EPA!")
        self.setGeometry(200, 100, 1024, 768)
        self.setFixedSize(1024, 768)
        self.center_window()

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header (barra superior)
        header = Header(self.go_to_login)

        # Sidebar (barra lateral)
        self.sidebar = Sidebar(self)

        # Contenido principal dinámico
        self.content_frame = QFrame()
        self.content_frame.setStyleSheet("background-color: #ffffff; padding: 30px;")
        self.content_frame.setMinimumWidth(600)  # Ensure enough width for content
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(25, 25, 25, 25)  # Better margins
        self.content_layout.setSpacing(25)  # Improved spacing

        # Establecer vista inicial de Dashboard
        self.setup_dashboard_content()

        # Crear layout con sidebar y contenido
        content_layout = QHBoxLayout()
        content_layout.addWidget(self.sidebar)
        content_layout.addWidget(self.content_frame)

        # Añadir header y contenido al layout principal
        main_layout.addWidget(header)
        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)

    def setup_dashboard_content(self):
        """
        Construye la vista de inicio del dashboard con el mensaje de bienvenida
        y el botón de "Analizar Navegación".
        """
        # Limpiar contenido previo
        self._clear_content_layout()

        # Título
        content_label = QLabel("Bienvenido al Dashboard de EPA!")
        content_label.setStyleSheet(
            "font-size: 28px; font-weight: bold; color: #2c3e50; margin-bottom: 20px;"
        )
        content_label.setAccessibleName("title")
        content_label.setWordWrap(True)  # Allow text wrapping
        content_label.setMinimumHeight(50)  # Ensure enough height
        content_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(content_label)

        # Botón de analizar navegación
        analyze_button = QPushButton("🔍 Analizar Navegación")
        analyze_button.setStyleSheet("""
            QPushButton {
                background-color: #ffffff; border: 2px solid #5a155b;
                color: #5a155b; font-weight: bold; padding: 18px 25px; 
                font-size: 18px; border-radius: 8px; min-height: 30px;
                min-width: 250px;  /* Ensure enough width for text */
            }
            QPushButton:hover { 
                background-color: #f8f4f9; 
                border-color: #481244;
            }
            QPushButton:pressed { 
                background-color: #ede7ef; 
                border-color: #3d0f38;
            }
        """)
        analyze_button.clicked.connect(self.open_profile_window)
        analyze_button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)  # Allow horizontal expansion
        self.content_layout.addWidget(analyze_button, alignment=Qt.AlignCenter)

    def on_sidebar_menu(self, selection_text):
        """
        Método invocado por Sidebar cuando cambia la selección.
        """
        if selection_text == "Inicio":
            self.setup_dashboard_content()
        elif selection_text == "PLE":
            self.show_ple_view()

    def show_ple_view(self):
        """
        Limpia el contenido actual y muestra la vista PLE dentro de la misma ventana.
        """
        # Limpiar contenido previo
        self._clear_content_layout()

        # Instanciar y mostrar PLEView (sin forzar selección de perfil)
        ple = PLEView(parent=self, user_id=GlobalState.selected_profile.get('id') if GlobalState.selected_profile else None, current_profile=GlobalState.selected_profile)
        self.content_layout.addWidget(ple)

    def _clear_content_layout(self):
        """
        Elimina todos los widgets de la vista de contenido.
        """
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

    def go_to_login(self):
        from qt_views.login_interface import LoginWindow

        if GlobalState.tracking_armed and GlobalState.tracking_mode == "logout":
            GlobalState.tracking_armed = False  # desarmar

            # >>> PASAR EL PERFIL SELECCIONADO <<<
            self._hist_worker = HistoryWorker(
                profile_dir=GlobalState.current_profile_dir,
                output_dir="chrome_exports"
            )

            self._hist_worker.done.connect(lambda: self._finish_logout(LoginWindow))
            self._hist_worker.fail.connect(lambda err: (print("Hist err:", err), self._finish_logout(LoginWindow)))
            self._hist_worker.start()
        else:
            self._finish_logout(LoginWindow)

    def _finish_logout(self, LoginWindow):
        self.login_window = LoginWindow()
        self.login_window.show()
        self.close()

    def open_profile_window(self):
        """
        Abre la ventana de selección de perfiles y cierra esta.
        """
        self.profile_window = ProfileWindow()
        self.profile_window.show()
        self.close()

    def center_window(self):
        qr = self.frameGeometry()
        cp = QApplication.desktop().screen().rect().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


def main():
    app = QApplication(sys.argv)
    window = DashboardWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
