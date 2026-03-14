from PyQt5.QtWidgets import QFrame, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from qt_views.global_state import GlobalState
from config.config import resource_path
import base64

class Header(QFrame):
    def __init__(self, on_logout):
        super().__init__()

        self.setStyleSheet("background-color: #5a155b; padding: 15px;")
        self.setMinimumHeight(120)  #  Ensure enough height for all elements

        self.header_layout = QHBoxLayout()
        self.header_layout.setContentsMargins(10, 10, 10, 10)  # Better margins
        self.header_layout.setSpacing(15)  # Improved spacing

        # Logo
        logo_label = QLabel()
        logo_pixmap = QPixmap(resource_path("assets/epai_logo-web.png"))
        logo_label.setPixmap(logo_pixmap)
        logo_label.setFixedHeight(130)    #Antes 100
        logo_label.setFixedWidth(140)     #Antes 120
        logo_label.setAlignment(Qt.AlignVCenter)
        logo_label.setStyleSheet("margin-right: 15px;")
        logo_label.setScaledContents(True)

        # Espaciador - removed title for better space utilization
        self.header_layout.addWidget(logo_label)
        self.header_layout.addStretch()

        # Profile section container (image + name)
        from PyQt5.QtWidgets import QVBoxLayout, QWidget
        profile_container = QWidget()
        profile_layout = QVBoxLayout(profile_container)
        profile_layout.setContentsMargins(0, 0, 0, 0)
        profile_layout.setSpacing(5)
        profile_layout.setAlignment(Qt.AlignCenter)

        # Imagen de perfil (siempre visible)
        self.profile_label = QLabel()
        self.profile_label.setFixedSize(70, 70)
        self.profile_label.setStyleSheet("""
            QLabel {
                border-radius: 35px;
                background-color: white;
                border: 2px solid #f8f9fa;
            }
        """)
        self.profile_label.setAlignment(Qt.AlignCenter)
        self.profile_label.setScaledContents(True)
        profile_layout.addWidget(self.profile_label, alignment=Qt.AlignCenter)

        # Profile name label
        self.profile_name_label = QLabel()
        self.profile_name_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 13px;
                font-weight: 500;
                padding: 2px 5px;
            }
        """)
        self.profile_name_label.setAlignment(Qt.AlignCenter)
        self.profile_name_label.setWordWrap(False)
        profile_layout.addWidget(self.profile_name_label, alignment=Qt.AlignCenter)

        self.header_layout.addWidget(profile_container)

        # Cargar avatar inicial
        self.refresh_profile()

        # Botón cerrar sesión
        logout_button = QPushButton("Cerrar Sesión")
        logout_button.setStyleSheet("""
            QPushButton {
                background-color: #c0392b; color: white; font-weight: 500;
                padding: 12px 18px; border: none; border-radius: 6px;
                font-size: 14px; min-height: 20px; min-width: 120px;
            }
            QPushButton:hover { background-color: #a93226; }
            QPushButton:pressed { background-color: #922b21; }
        """)
        logout_button.clicked.connect(on_logout)

        self.header_layout.addWidget(logout_button)

        self.setLayout(self.header_layout)

    def refresh_profile(self):
        """Actualiza la imagen y nombre del perfil según GlobalState."""
        profile = GlobalState.selected_profile
        display_name = GlobalState.user_name or "Usuario"

        avatar_b64 = None
        if isinstance(profile, dict):
            avatar_b64 = profile.get("avatar")
            display_name = profile.get("display_name") or profile.get("name") or display_name

        if avatar_b64:
            try:
                image_data = base64.b64decode(avatar_b64)
                image = QImage.fromData(image_data)
                pixmap = QPixmap.fromImage(image)
                self.set_profile_image(pixmap)
            except Exception as e:
                print(f"Error loading Chrome avatar: {e}")
                self._set_default_user_icon(display_name)
        else:
            self._set_default_user_icon(display_name)

        self.profile_name_label.setText(display_name)

    def set_profile_image(self, image: QPixmap):
        """Mostrar la imagen del perfil en el header."""
        self.profile_label.setPixmap(image.scaled(70, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def _set_default_user_icon(self, name="Usuario"):
        """Set a default user icon using an emoji/text representation."""
        # Create a simple user icon using styled text
        self.profile_label.setText("👤")
        self.profile_label.setStyleSheet("""
            QLabel {
                border-radius: 35px;
                background-color: #e8e8e8;
                border: 2px solid #d0d0d0;
                font-size: 40px;
                color: #5a155b;
            }
        """)
        # Set default name
        self.profile_name_label.setText(name)
