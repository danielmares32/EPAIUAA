from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QCheckBox, QPushButton, QVBoxLayout, QSpacerItem, QSizePolicy, QHBoxLayout, QDialog, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtWidgets import QMessageBox
from services.api_service import login
from PyQt5.QtCore import pyqtSignal
import requests
from config.config import resource_path

class ModernDialog(QDialog):
    """Modern styled dialog for better user experience"""
    
    def __init__(self, title, message, dialog_type="info", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(420, 280)
        
        # Remove window frame and add custom styling
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Main container
        main_container = QFrame(self)
        main_container.setGeometry(0, 0, 420, 280)
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
        
        # Icon based on dialog type
        icon_label = QLabel()
        if dialog_type == "success":
            icon_label.setText("✅")
            icon_color = "#27ae60"
        elif dialog_type == "error":
            icon_label.setText("❌")
            icon_color = "#e74c3c"
        elif dialog_type == "warning":
            icon_label.setText("⚠️")
            icon_color = "#f39c12"
        else:  # info
            icon_label.setText("ℹ️")
            icon_color = "#3498db"
            
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 32px;
                color: {icon_color};
                padding: 10px;
            }}
        """)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
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
                font-size: 14px;
                color: #34495e;
                line-height: 1.4;
                padding: 10px 0;
            }
        """)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_button = QPushButton("Aceptar")
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #5a155b;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #481244;
            }
            QPushButton:pressed {
                background-color: #3d0f38;
            }
        """)
        ok_button.clicked.connect(self.accept)
        
        button_layout.addWidget(ok_button)
        
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

class LoginWindow(QWidget):

    login_success = pyqtSignal()

    def __init__(self):
        super().__init__()

        # Configuración principal de la ventana
        self.setWindowTitle("Login Interface")
        self.setGeometry(200, 100, 800, 600)
        self.center_window()  

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(20)

        # Espacio superior vacío
        main_layout.addSpacerItem(QSpacerItem(20, 120, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Logo de la parte superior (imagen)
        self.logo_label = QLabel()
        self.logo_pixmap = QPixmap(resource_path("assets/logo.png"))
        self.logo_label.setPixmap(self.logo_pixmap)
        self.logo_label.setAlignment(Qt.AlignCenter)

        # Subtítulo
        self.subtitle_label = QLabel("PLE Active")
        self.subtitle_label.setStyleSheet("font-size: 18px; font-weight: 600; color: #5a155b; margin-bottom: 10px;")
        self.subtitle_label.setAccessibleName("subtitle")

        # Colocación del logo y subtítulo
        logo_layout = QVBoxLayout()
        logo_layout.addWidget(self.logo_label)
        logo_layout.addWidget(self.subtitle_label)
        logo_layout.setAlignment(self.logo_label, Qt.AlignCenter)
        logo_layout.setAlignment(self.subtitle_label, Qt.AlignCenter)

        # Formulario de inicio de sesión
        form_layout = QVBoxLayout()
        form_layout.setSpacing(12)

        # Campo de correo electrónico
        email_label = QLabel("Correo")
        email_label.setStyleSheet("font-size: 14px; font-weight: 500; color: #2c3e50; margin-bottom: 5px;")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("email@example.com")
        self.email_input.setStyleSheet("""
            QLineEdit {
                padding: 12px 15px; border: 2px solid #ecf0f1; border-radius: 6px;
                font-size: 14px; background-color: #ffffff;
                selection-background-color: #3498db;
            }
            QLineEdit:focus { border-color: #3498db; background-color: #fbfcfd; }
            QLineEdit:hover { border-color: #bdc3c7; }
        """)

        # Campo de contraseña
        password_label = QLabel("Contraseña")
        password_label.setStyleSheet("font-size: 14px; font-weight: 500; color: #2c3e50; margin-bottom: 5px;")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 12px 15px; border: 2px solid #ecf0f1; border-radius: 6px;
                font-size: 14px; background-color: #ffffff;
                selection-background-color: #3498db;
            }
            QLineEdit:focus { border-color: #3498db; background-color: #fbfcfd; }
            QLineEdit:hover { border-color: #bdc3c7; }
        """)

        # Checkbox de recordar
        self.remember_checkbox = QCheckBox("Recordarme")

        # Botón de acceso
        login_button = QPushButton("Acceder")
        login_button.setStyleSheet("""
            QPushButton {
                background-color: #5a155b; color: white; font-weight: bold; 
                padding: 12px 20px; border: none; border-radius: 6px;
                font-size: 14px; min-height: 20px;
            }
            QPushButton:hover { 
                background-color: #481244; 
            }
            QPushButton:pressed { 
                background-color: #3d0f38; 
            }
            QPushButton:disabled { 
                background-color: #bdc3c7; 
                color: #7f8c8d; 
            }
        """)
        login_button.clicked.connect(self.handle_login)

        # Texto de enlaces de recuperación y registro
        register_label = QLabel("¿Eres nuevo? <a href='https://uninovadeplan.dev11.javali.pt/user/register' style='color: #0078d7; text-decoration: none;'>Accede a EPA!</a>")
        forgot_label = QLabel("<u style='color: #0078d7;'>¿Olvidaste la contraseña?</u>")

        # Establecer estilo para los textos
        register_label.setOpenExternalLinks(True)  
        register_label.setAlignment(Qt.AlignCenter)
        register_label.setStyleSheet("margin-top: 20px; font-size: 14px;")
        forgot_label.setAlignment(Qt.AlignCenter)
        forgot_label.setStyleSheet("font-size: 14px;")

        # Agregar componentes al layout de formulario
        form_layout.addWidget(email_label)
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(self.remember_checkbox)
        form_layout.addWidget(login_button)
        form_layout.addWidget(register_label)
        form_layout.addWidget(forgot_label)

        # Centrar el formulario en el centro de la ventana
        form_widget = QWidget()
        form_widget.setLayout(form_layout)

        # Contenedor del formulario
        form_container = QVBoxLayout()
        form_container.addWidget(form_widget)
        form_container.setContentsMargins(160, 20, 160, 20)

        # Agregar el logo y formulario al layout principal
        main_layout.addLayout(logo_layout)
        main_layout.addLayout(form_container)

        # Espacio inferior vacío
        main_layout.addSpacerItem(QSpacerItem(20, 150, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.setLayout(main_layout)

    def center_window(self):
        qr = self.frameGeometry()
        cp = QApplication.desktop().screen().rect().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def open_dashboard(self):
        from qt_views.DashboardWindow import DashboardWindow  # Asegúrate de implementar DashboardWindow
        self.dashboard = DashboardWindow()
        self.dashboard.show()
        self.close()

    def handle_login(self):
        usuario = self.email_input.text().strip()
        contrasena = self.password_input.text().strip()

        if not usuario or not contrasena:
            dialog = ModernDialog("Campos Requeridos", "Por favor, ingresa todos los campos para continuar.", "warning", self)
            dialog.exec_()
            return

        try:
            respuesta = requests.post("http://127.0.0.1:5000/auth/login", data={
                "username": usuario,
                "password": contrasena
            })

            data = respuesta.json()
            print(data)

            if respuesta.status_code == 200 and data.get("status") == True:
                # Store user_id and user info in GlobalState
                from qt_views.global_state import GlobalState
                profile = data.get("profile", {})
                user_id = profile.get("uid")
                if user_id:
                    GlobalState.user_id = int(user_id)
                    print(f"[Login] Set GlobalState.user_id = {GlobalState.user_id}")

                # Store user name from login (not Chrome profile)
                user_name = profile.get("name") or profile.get("username") or profile.get("email") or "Usuario"
                GlobalState.user_name = user_name
                print(f"[Login] Set GlobalState.user_name = {GlobalState.user_name}")
                print(f"[Login] Profile data: {profile}")

                dialog = ModernDialog("¡Bienvenido!", "Inicio de sesión exitoso. Redirigiendo al panel principal...", "success", self)
                dialog.exec_()
                #self.login_success.emit()
                self.open_dashboard()

            else:
                error_msg = data.get("error", "Credenciales incorrectas. Por favor, verifica tu email y contraseña.")
                dialog = ModernDialog("Error de Autenticación", error_msg, "error", self)
                dialog.exec_()

        except requests.RequestException as e:
            error_msg = f"No se pudo conectar al servidor. Por favor, verifica tu conexión a internet.\n\nDetalle: {str(e)}"
            dialog = ModernDialog("Error de Conexión", error_msg, "error", self)
            dialog.exec_()