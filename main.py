# main.py

import sys
import multiprocessing

def main():
    # Must be called before anything else in a frozen (PyInstaller) app
    multiprocessing.freeze_support()

    if sys.platform == 'darwin':
        try:
            multiprocessing.set_start_method('spawn')
        except RuntimeError:
            pass

    import threading
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QIcon
    from app import create_app
    from qt_views.login_interface import LoginWindow
    from config.config import resource_path

    def run_flask(app):
        app.run(debug=False)

    app = create_app()

    # Lanzar Flask en un hilo
    flask_thread = threading.Thread(target=run_flask, args=(app,), daemon=True)
    flask_thread.start()

    # Iniciar la interfaz grafica
    qt_app = QApplication(sys.argv)
    qt_app.setWindowIcon(QIcon(resource_path("assets/logo.png")))

    # Global application stylesheet for consistency and modern look
    qt_app.setStyleSheet("""
        QWidget {
            font-family: system-ui, -apple-system, 'Helvetica Neue', Helvetica, Arial, sans-serif;
            background-color: #ffffff;
        }
        QFrame {
            border-radius: 8px;
            background-color: #ffffff;
        }
        QListWidget {
            border: none;
            border-radius: 6px;
            outline: none;
        }
        QListWidget::item:selected {
            background-color: rgba(90, 21, 91, 0.1);
            color: #5a155b;
            border-left: 3px solid #5a155b;
        }
        QListWidget::item:hover {
            background-color: rgba(90, 21, 91, 0.05);
        }
    """)

    login_window = LoginWindow()

    def on_login_success():
        login_window.open_dashboard()

    login_window.login_success.connect(on_login_success)

    login_window.show()
    sys.exit(qt_app.exec_())

if __name__ == "__main__":
    main()