from PyQt5.QtWidgets import QFrame, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from qt_views.global_state import GlobalState
import base64

class Header(QFrame):
    def __init__(self, on_logout):
        super().__init__()

        self.setStyleSheet("background-color: #5a155b; padding: 15px;")
        self.setMinimumHeight(120)  # Ensure enough height for all elements

        self.header_layout = QHBoxLayout()
        self.header_layout.setContentsMargins(10, 10, 10, 10)  # Better margins
        self.header_layout.setSpacing(15)  # Improved spacing

        # Logo
        logo_label = QLabel()
        logo_pixmap = QPixmap("assets/logo_header.png")
        logo_label.setPixmap(logo_pixmap)
        logo_label.setFixedHeight(130)    #Antes 100
        logo_label.setFixedWidth(140)     #Antes 120
        logo_label.setAlignment(Qt.AlignVCenter)
        logo_label.setStyleSheet("margin-right: 15px;")
        logo_label.setScaledContents(True)


        # Título
        title_label = QLabel("EPA! - PLE Active")
        title_label.setStyleSheet("color: white; font-size: 20px; font-weight: bold; margin-left: 15px;")
        title_label.setWordWrap(True)  # Allow text wrapping if needed
        title_label.setMinimumWidth(200)  # Ensure enough width for title

        # Espaciador
        self.header_layout.addWidget(logo_label)
        self.header_layout.addWidget(title_label)
        self.header_layout.addStretch()

        # Imagen de perfil (inicialmente oculta o vacía)
        self.profile_label = QLabel()
        self.profile_label.setFixedSize(70, 70)
        # redondear la imagen del perfil
        self.profile_label.setStyleSheet("border-radius: 35px; background-color: white;")
        self.profile_label.setAlignment(Qt.AlignCenter)
        self.profile_label.setScaledContents(True)
        self.profile_label.hide()  # Oculto hasta que se seleccione perfil
        self.header_layout.addWidget(self.profile_label)

        profile = GlobalState.selected_profile
        if profile and profile["avatar"]:
            # Decodificar la imagen base64 y crear un QPixmap
            image_data = base64.b64decode(profile["avatar"])
            image = QImage.fromData(image_data)
            pixmap = QPixmap.fromImage(image)
            self.set_profile_image(pixmap)

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

    def set_profile_image(self, image: QPixmap):
        """Mostrar la imagen del perfil en el header."""
        self.profile_label.setPixmap(image.scaled(70, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.profile_label.show()
