# qt_views/dashboard.py

import sys
import os
import webbrowser
import requests

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFrame, QTextEdit, QStackedLayout, QScrollArea, QGridLayout,
    QDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap

from qt_views.components.Sidebar import Sidebar
from qt_views import login_interface
from qt_views.global_state import GlobalState
from services.history_service_4 import run_crawler
from multiprocessing import Process

API_BASE = "https://uninovadeplan-ws.javali.pt"

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

class PLEDetailDialog(QDialog):
    """Ventana modal para mostrar detalle de un PLE."""
    def __init__(self, ple_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(ple_data["name"])
        self.resize(800, 600)
        layout = QVBoxLayout(self)

        txt = QTextEdit()
        txt.setReadOnly(True)
        try:
            resp = requests.get(
                f"{API_BASE}/PLE/environment/{ple_data['environmentID']}",
                timeout=10
            )
            resp.raise_for_status()
            txt.setText(resp.text)
        except Exception as e:
            txt.setText(f"Error al cargar detalle:\n{e}")

        layout.addWidget(txt)


class DashboardWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dashboard - EPA!")
        self.setGeometry(200, 100, 1024, 768)
        self.setFixedSize(1024, 768)
        self.center_window()

        # ─── Layout principal ──────────────────────────────────────────────
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)

        # ─── Header ────────────────────────────────────────────────────────
        header = QFrame()
        header.setStyleSheet("background-color: #5a155b; padding: 15px;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(15,0,15,0)

        # Logo
        logo = QLabel()
        pix = QPixmap(os.path.join("assets","logo.png"))
        logo.setPixmap(pix.scaled(50,50, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        h_layout.addWidget(logo)

        # Título
        title = QLabel("EPA! - PLE Active")
        title.setStyleSheet(
            "color: white; font-size: 18px; font-weight: bold; margin-left: 10px;"
        )
        h_layout.addWidget(title)
        h_layout.addStretch()

        # Botón Cerrar Sesión
        btn_logout = QPushButton("Cerrar Sesión")
        btn_logout.setStyleSheet(
            "background-color: #c0392b; color: white;"
            " padding: 10px; border: none; border-radius: 5px;"
        )
        btn_logout.clicked.connect(self.go_to_login)
        h_layout.addWidget(btn_logout)

        # ─── Body ──────────────────────────────────────────────────────────
        body = QFrame()
        b_layout = QHBoxLayout(body)
        b_layout.setContentsMargins(0,0,0,0)
        b_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar(self)
        b_layout.addWidget(self.sidebar)

        # Stack de pantallas
        self.stack = QStackedLayout()
        self.stack.setContentsMargins(20,20,20,20)

        # --- Página Inicio ---
        self.page_inicio = QWidget()
        pi_l = QVBoxLayout(self.page_inicio)
        lbl = QLabel("Bienvenido al Dashboard de EPA!")
        lbl.setStyleSheet("font-size: 24px; font-weight: bold;")
        pi_l.addWidget(lbl, alignment=Qt.AlignTop)

        btn_nav = QPushButton("🔍 Analizar Navegación")
        btn_nav.setStyleSheet(
            "background-color: #ffffff; border: 2px solid #5a155b;"
            " color: #5a155b; font-weight: bold;"
            " padding: 15px; font-size: 18px;"
        )
        btn_nav.clicked.connect(self.on_analyze_navigation)
        pi_l.addWidget(btn_nav, alignment=Qt.AlignTop)

        self.stack.addWidget(self.page_inicio)

        # --- Página PLE ---
        self.page_ple = QWidget()
        ple_l = QVBoxLayout(self.page_ple)

        # ScrollArea para mosaicos
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        container = QWidget()
        self.grid = QGridLayout(container)
        self.grid.setSpacing(20)
        self.scroll.setWidget(container)
        ple_l.addWidget(self.scroll)

        # Enlace "¿No encuentras tu PLE?"
        btn_link = QPushButton("¿No encuentras tu PLE? Da clic aquí")
        btn_link.setStyleSheet(
            "background-color: #444; color: white;"
            " padding: 10px; border-radius: 5px;"
        )
        btn_link.clicked.connect(
            lambda: webbrowser.open("https://uninovadeplan.dev11.javali.pt/user/login")
        )
        ple_l.addWidget(btn_link, alignment=Qt.AlignCenter)

        self.stack.addWidget(self.page_ple)

        # Montaje final
        b_layout.addLayout(self.stack)
        main_layout.addWidget(header)
        main_layout.addWidget(body)
        self.setLayout(main_layout)

        # Selecciona “Inicio” por defecto y dispara la vista
        self.sidebar.menu.setCurrentRow(0)
        self.on_sidebar_menu("Inicio")

        # Habilita "PLE" si ya existe un perfil de Chrome guardado
        if GlobalState.current_profile_dir:
            self.sidebar.enable_ple()

    def on_sidebar_menu(self, text: str):
        """Maneja el cambio de página según lo que venga del Sidebar."""
        if text == "Inicio":
            self.stack.setCurrentWidget(self.page_inicio)

        elif text == "PLE":
            pd = GlobalState.current_profile_dir
            if not pd:
                # si no hay perfil, abrir ventana de selección
                from qt_views.ProfileWindow import ProfileWindow
                pw = ProfileWindow()
                pw.show()
                self.close()
                return

            # cargar mosaicos y mostrar
            self.load_ples()
            self.stack.setCurrentWidget(self.page_ple)

    def on_analyze_navigation(self):
        """Acción para 'Analizar Navegación' en Inicio."""
        pd = GlobalState.current_profile_dir
        if not pd:
            QMessageBox.warning(self, "Perfil", "Selecciona primero un perfil de Chrome.")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("Keywords extraídas")
        dlg.resize(600,400)
        txt = QTextEdit(dlg)
        txt.setReadOnly(True)
        try:
            r = requests.get(f"http://localhost:5000/chrome/keywords/{pd}", timeout=10)
            r.raise_for_status()
            txt.setText(r.text)
        except Exception as e:
            txt.setText(f"Error al obtener keywords:\n{e}")
        v = QVBoxLayout(dlg)
        v.addWidget(txt)
        dlg.exec_()

    def load_ples(self):
        """Carga el grid de mosaicos desde el backend."""
        # limpiar grid anterior
        for i in reversed(range(self.grid.count())):
            w = self.grid.itemAt(i).widget()
            if w:
                w.setParent(None)

        user_id = GlobalState.user_id
        try:
            r = requests.get(f"{API_BASE}/PLE/user/{user_id}", timeout=10)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            self.grid.addWidget(QLabel(f"Error cargando PLEs:\n{e}"), 0, 0)
            return

        # construir mosaicos
        for idx, item in enumerate(data):
            row, col = divmod(idx, 2)

            frm = QFrame()
            frm.setFixedSize(400,150)
            color = ["#72B2E4","#F589C5","#7BE7E1","#D6D6D6"][idx%4]
            frm.setStyleSheet(
                f"background-color: {color}; border:1px solid #444; border-radius:5px;"
            )
            vl = QVBoxLayout(frm)
            lbl = QLabel(item["name"])
            lbl.setWordWrap(True)
            lbl.setStyleSheet("font-weight:bold; font-size:14px;")
            vl.addWidget(lbl, alignment=Qt.AlignTop)

            btn = QPushButton("Acceder")
            btn.setFixedSize(QSize(100,30))
            btn.clicked.connect(lambda _, d=item: self.open_ple_window(d))
            vl.addWidget(btn, alignment=Qt.AlignHCenter|Qt.AlignBottom)

            self.grid.addWidget(frm, row, col)

    def open_ple_window(self, ple_data):
        dlg = PLEDetailDialog(ple_data, self)
        dlg.exec_()

    def go_to_login(self):
        """Vuelve a la ventana de login, pero antes ejecuta el crawler si el usuario lo armó para 'logout'."""
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

    def _finish_logout(self):
        # Aquí mantienes tu flujo original de ir al login
        self.login_window = login_interface.LoginWindow()
        self.login_window.show()
        self.close()

    def center_window(self):
        qr = self.frameGeometry()
        cp = QApplication.desktop().screen().rect().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


def main():
    app = QApplication(sys.argv)
    w = DashboardWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()