import sys
import os
import json
import requests
import base64
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QPushButton,
    QGridLayout,
    QDialog,
    QListWidget,
    QListWidgetItem,
    QCheckBox,
    QMessageBox,
    QAbstractItemView,
    QScrollArea,
    QSizePolicy,
    QLayout,
)
from PyQt5.QtCore import Qt, QSettings, QRect, QPoint, QSize
from PyQt5.QtGui import QImage, QPixmap
from .components.Sidebar import Sidebar
from .components.Header import Header
from qt_views.global_state import GlobalState


class FlowLayout(QLayout):
    """Layout tipo flujo para acomodar mosaicos horizontalmente con wrapping."""

    def __init__(self, parent=None, margin=0, spacing=16):
        super().__init__(parent)
        self._items = []
        self._spacing = spacing
        self.setContentsMargins(margin, margin, margin, margin)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._layout_items(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._layout_items(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            if item is not None:
                size = size.expandedTo(item.minimumSize())
        left, top, right, bottom = self.getContentsMargins()
        size += QSize(left + right, top + bottom)
        return size

    def spacing(self):
        return self._spacing

    def _layout_items(self, rect, test_only=False):
        if not self._items:
            return 0

        left, top, right, bottom = self.getContentsMargins()
        effective_rect = rect.adjusted(left, top, -right, -bottom)
        max_width = max(0, effective_rect.width())

        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0
        space_x = self._spacing
        space_y = self._spacing

        for item in self._items:
            if item is None:
                continue
            hint = item.sizeHint()
            item_width = hint.width()
            item_height = hint.height()

            if max_width > 0 and item_width > max_width:
                item_width = max_width

            if max_width > 0 and x > effective_rect.x() and (x + item_width) > (effective_rect.x() + max_width):
                x = effective_rect.x()
                y += line_height + space_y
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), QSize(item_width, item_height)))

            x += item_width + space_x
            line_height = max(line_height, item_height)

        total_height = (y + line_height) - rect.y() + top + bottom
        return total_height


class ProfileConfirmDialog(QDialog):
    """Diálogo moderno para confirmar el perfil seleccionado."""

    def __init__(self, profile_name, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setFixedSize(420, 260)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        container = QFrame(self)
        container.setGeometry(0, 0, 420, 260)
        container.setStyleSheet(
            """
            QFrame {
                background-color: #ffffff;
                border-radius: 16px;
                border: 1px solid #ece8f4;
            }
            """
        )

        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(18)

        header = QLabel("Confirmar perfil")
        header.setStyleSheet(
            "font-size: 20px; font-weight: 700; color: #5a155b;"
        )
        layout.addWidget(header)

        message = QLabel(
            f"Has seleccionado el perfil <b>{profile_name}</b>.\n¿Deseas continuar con este perfil?"
        )
        message.setWordWrap(True)
        message.setStyleSheet(
            "font-size: 15px; color: #2c3e50; line-height: 1.4;"
        )
        layout.addWidget(message)

        button_row = QHBoxLayout()
        button_row.addStretch()

        change_btn = QPushButton("Cambiar")
        change_btn.setCursor(Qt.PointingHandCursor)
        change_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #ffffff;
                color: #5a155b;
                border: 2px solid #5a155b;
                font-weight: 600;
                padding: 10px 24px;
                border-radius: 8px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #f8f4f9;
            }
            QPushButton:pressed {
                background-color: #ede7ef;
            }
            """
        )
        change_btn.clicked.connect(self.reject)

        confirm_btn = QPushButton("Confirmar")
        confirm_btn.setCursor(Qt.PointingHandCursor)
        confirm_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #5a155b;
                color: white;
                border: none;
                font-weight: 600;
                padding: 10px 24px;
                border-radius: 8px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #481244;
            }
            QPushButton:pressed {
                background-color: #3d0f37;
            }
            """
        )
        confirm_btn.clicked.connect(self.accept)

        button_row.addWidget(change_btn)
        button_row.addWidget(confirm_btn)
        layout.addLayout(button_row)

        # Centrar el diálogo respecto al padre
        if parent:
            parent_rect = parent.frameGeometry()
            dialog_rect = self.frameGeometry()
            dialog_rect.moveCenter(parent_rect.center())
            self.move(dialog_rect.topLeft())

class ProfileWindow(QWidget):
    def __init__(self, show_previous_prompt=True):
        super().__init__()

        self._should_prompt_previous_profile = show_previous_prompt

        self.settings = QSettings("EPAI", "EPAIApp")
        self.profiles_data = []
        self.profile_lookup = {}
        self.approved_paths = self._load_approved_paths()
        self.selected_path = self.settings.value("chrome_profile_path", type=str)
        self.selected_profile_data = None
        self.user_consented = False
        self._updating_approved_list = False

        self.setWindowTitle("Profiles - EPA!")
        self.setGeometry(200, 100, 1024, 768)
        self.resize(1024, 768)
        self.setMinimumSize(960, 640)
        self.center_window()

        # Layout principal de la ventana
        main_layout = QVBoxLayout(self)

        # Header (barra superior)
        self.header = Header(self.go_to_dashboard)

        # Sidebar (barra lateral)
        sidebar = Sidebar()

        # Contenido principal del perfil (envuelto en scroll)
        scroll_inner = QWidget()
        scroll_inner.setStyleSheet("background-color: #ffffff; padding: 20px;")

        # Contenedor principal del contenido
        main_content = QVBoxLayout(scroll_inner)
        main_content.setAlignment(Qt.AlignTop)  # Alinear al inicio
        main_content.setSpacing(15)

        # Elementos de consentimiento y estado
        self.consent_checkbox = QCheckBox("Estoy de acuerdo en usar los perfiles seleccionados")
        self.consent_checkbox.setStyleSheet(
            """
            QCheckBox {
                font-size: 15px;
                font-weight: 500;
                color: #2c3e50;
                padding: 8px 14px;
                border-radius: 20px;
                background-color: #f3e9f6;
            }
            QCheckBox::indicator {
                width: 22px;
                height: 22px;
                border-radius: 6px;
                border: 2px solid #5a155b;
                background-color: #ffffff;
            }
            QCheckBox::indicator:checked {
                background-color: #5a155b;
                border-color: #5a155b;
            }
            """
        )
        self.consent_checkbox.stateChanged.connect(self._on_consent_checkbox_changed)

        lists_frame = QFrame()
        lists_layout = QGridLayout()
        lists_frame.setLayout(lists_layout)
        lists_layout.setContentsMargins(0, 0, 0, 0)
        lists_layout.setHorizontalSpacing(12)
        lists_layout.setVerticalSpacing(8)

        self.active_list_widget = QListWidget()
        self.approved_list_widget = QListWidget()
        self.selected_list_widget = QListWidget()

        self.active_list_widget.setSelectionMode(QAbstractItemView.NoSelection)
        self.active_list_widget.setFocusPolicy(Qt.NoFocus)
        self.approved_list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.selected_list_widget.setSelectionMode(QAbstractItemView.NoSelection)
        self.selected_list_widget.setFocusPolicy(Qt.NoFocus)

        active_group = self._build_list_group("Perfiles activos", self.active_list_widget)
        approved_group = self._build_list_group("Perfiles aprobados", self.approved_list_widget)
        selected_group = self._build_list_group("Perfil seleccionado", self.selected_list_widget)

        active_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        approved_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        selected_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        lists_layout.addWidget(active_group, 0, 0)
        lists_layout.addWidget(approved_group, 0, 1)
        lists_layout.addWidget(selected_group, 0, 2)
        lists_layout.setColumnStretch(0, 1)
        lists_layout.setColumnStretch(1, 1)
        lists_layout.setColumnStretch(2, 1)

        self.approved_list_widget.itemChanged.connect(self._on_approved_item_changed)
        self.approved_list_widget.itemDoubleClicked.connect(self._on_approved_item_activated)

        self.apply_selection_button = QPushButton("Usar perfil seleccionado")
        self.apply_selection_button.setCursor(Qt.PointingHandCursor)
        self.apply_selection_button.setEnabled(False)
        self.apply_selection_button.setStyleSheet(
            """
            QPushButton {
                background-color: #5a155b;
                color: #ffffff;
                font-size: 15px;
                font-weight: 600;
                padding: 12px 30px;
                border-radius: 24px;
                border: none;
                min-width: 220px;
            }
            QPushButton:hover:!disabled {
                background-color: #481244;
            }
            QPushButton:pressed:!disabled {
                background-color: #3d0f38;
            }
            QPushButton:disabled {
                background-color: #cdb5d3;
                color: #f8f3fb;
            }
            """
        )
        self.apply_selection_button.clicked.connect(self._on_use_selected_clicked)

        # Barra superior del contenido (Título, Breadcrumb, y Botón)
        title_bar = QHBoxLayout()
        title_bar.setContentsMargins(0, 0, 0, 0)  # Sin márgenes
        title_bar.setSpacing(0)  # Sin espacio entre elementos

        # Botón "Atrás"
        back_button = QPushButton("←")
        back_button.setStyleSheet(
            """
            background-color: transparent; 
            color: black; 
            font-size: 16px; 
            font-weight: bold;
            border: none;
            margin-right: 10px;
        """
        )
        back_button.clicked.connect(self.go_to_dashboard)  # Acción para ir atrás

        # Contenedor del Título y Breadcrumb
        title_breadcrumb_container = QHBoxLayout()
        title_breadcrumb_container.setContentsMargins(0, 0, 0, 0)  # Sin márgenes
        title_breadcrumb_container.setSpacing(10)  # Espaciado entre título y breadcrumb

        # Título principal
        title_label = QLabel("Perfiles de Google Chrome activos:")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        title_label.setAccessibleName("title")
        title_label.setAlignment(Qt.AlignLeft)  # Alineado a la izquierda

        # Breadcrumb
        breadcrumb_label = QLabel("Inicio / Perfiles")
        breadcrumb_label.setStyleSheet("font-size: 14px; color: #5a155b; font-weight: 500;")
        breadcrumb_label.setAccessibleName("subtitle")
        breadcrumb_label.setAlignment(Qt.AlignRight)  # Alineado al extremo derecho

        # Agregar el título y breadcrumb al contenedor
        title_breadcrumb_container.addWidget(title_label, 1)  # Título ocupa el espacio restante
        title_breadcrumb_container.addWidget(breadcrumb_label, 0, Qt.AlignRight)

        # Agregar el botón y el contenedor de título/breadcrumb al título_bar
        title_bar.addWidget(back_button, 0, Qt.AlignLeft)
        title_bar.addLayout(title_breadcrumb_container, 1)  # Aseguramos que el contenido ocupe 100%

        # Contenedor de las tarjetas (flujo responsivo)
        self.cards_flow_layout = FlowLayout(margin=10, spacing=20)

        cards_container = QWidget()
        cards_container.setLayout(self.cards_flow_layout)

        cards_scroll = QScrollArea()
        cards_scroll.setWidget(cards_container)
        cards_scroll.setWidgetResizable(True)
        cards_scroll.setFrameShape(QFrame.NoFrame)
        cards_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        cards_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.cards_scroll = cards_scroll

        # Añadir el título y el grid al layout principal
        main_content.addLayout(title_bar)

        consent_layout = QHBoxLayout()
        consent_layout.addStretch()
        consent_layout.addWidget(self.consent_checkbox)
        consent_layout.addStretch()
        consent_layout.setContentsMargins(0, 10, 0, 10)
        consent_layout.setSpacing(0)
        main_content.addLayout(consent_layout)

        main_content.addWidget(lists_frame)
        button_bar = QHBoxLayout()
        button_bar.addStretch()
        button_bar.addWidget(self.apply_selection_button)
        button_bar.addStretch()
        button_bar.setContentsMargins(0, 10, 0, 10)
        button_bar.setSpacing(0)
        main_content.addLayout(button_bar)
        main_content.addWidget(self.cards_scroll, 1)

        content_scroll = QScrollArea()
        content_scroll.setWidget(scroll_inner)
        content_scroll.setWidgetResizable(True)
        content_scroll.setFrameShape(QFrame.NoFrame)
        content_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        content_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        content_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.content_scroll = content_scroll

        # Crear layout principal con sidebar y contenido
        content_layout = QHBoxLayout()
        content_layout.addWidget(sidebar)
        content_layout.addWidget(content_scroll)

        # Añadir header y layout de contenido al layout principal
        main_layout.addWidget(self.header)
        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)

        stored_consent = self.settings.value("chrome_profile_consent", type=str)
        if stored_consent == "yes":
            self.consent_checkbox.setChecked(True)
        else:
            self.consent_checkbox.setChecked(False)
            if stored_consent is None:
                self._prompt_initial_consent()

        # Agregar tarjetas basadas en el servicio
        self.load_profiles()

    def load_profiles(self):
        """Carga los perfiles desde el servicio y crea las tarjetas."""
        try:
            response = requests.get('http://127.0.0.1:5000/chrome/profiles')
            response.raise_for_status()  # Lanza un error si la respuesta no es 200
            data = response.json()  # Parsea la respuesta como JSON
            self.profiles_data = data.get("profiles", [])
            self.profile_lookup = {
                profile.get("path"): profile for profile in self.profiles_data if profile.get("path")
            }
            if self.approved_paths:
                available_paths = {path for path in self.profile_lookup.keys() if path}
                filtered = [path for path in self.approved_paths if path in available_paths]
                if filtered != self.approved_paths:
                    self.approved_paths = filtered
                    self._save_approved_paths()
            self._populate_active_list()
            self._populate_approved_list()
            if self.selected_path:
                self.selected_profile_data = self._profile_by_path(self.selected_path)
            self._update_selected_list()
            self._clear_cards()
            for profile in self.profiles_data:
                card = self.create_profile_card(profile)
                self.cards_flow_layout.addWidget(card)
            if self._should_prompt_previous_profile:
                self._show_previous_profile_prompt()
        except requests.RequestException as e:
            print(f'Error al cargar los perfiles: {e}')

    def create_profile_card(self, profile):
        """Crea una tarjeta para mostrar un perfil"""
        card_frame = QFrame()
        card_frame.setStyleSheet(
            """
            border: 1px solid #ccc; 
            background-color: #f7f7f7; 
            border-radius: 8px;
            """
        )
        card_frame.setFixedWidth(260)
        card_frame.setMinimumHeight(220)
        card_frame.setMaximumHeight(260)
        card_frame.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        card_layout = QVBoxLayout()
        card_layout.setAlignment(Qt.AlignTop)
        card_layout.setContentsMargins(12, 12, 12, 12)  # Better margins for text
        card_layout.setSpacing(12)  # Improved spacing

        # Imagen
        image_label = QLabel()
        image_label.setFixedSize(100, 100)
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setStyleSheet("border-radius: 50px; background-color: #e0e0e0;")
        image_label.setScaledContents(True)

        if profile["avatar"]:
            img_data = base64.b64decode(profile["avatar"])
            image = QImage.fromData(img_data)
            pixmap = QPixmap.fromImage(image)
            pixmap = pixmap.scaled(image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_label.setPixmap(pixmap)
        else:
            image_label.setText("Sin imagen")
            image_label.setStyleSheet("background-color: #ccc; color: #666; border-radius: 50px;")
            image_label.setAlignment(Qt.AlignCenter)

        # Contenedor centrado para la imagen
        image_container = QHBoxLayout()
        image_container.setAlignment(Qt.AlignCenter)
        image_container.addWidget(image_label)

        # Nombre
        display_name = profile.get("display_name") or profile.get("name") or "Perfil"
        display_name = str(display_name)
        title_label = QLabel(display_name)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50;")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)  # Allow text wrapping for long profile names
        title_label.setMinimumHeight(35)  # Ensure enough height for wrapped text

        # Botón
        access_button = QPushButton("Acceder")
        access_button.setStyleSheet("""
            QPushButton {
                background-color: #5a155b; color: white; font-weight: 500;
                padding: 8px 15px; border: none; border-radius: 6px;
                font-size: 13px; min-height: 18px;
            }
            QPushButton:hover { 
                background-color: #481244; 
            }
            QPushButton:pressed { 
                background-color: #3d0f38; 
            }
        """)

        # Conectar el botón a la función que maneja el acceso al perfil
        access_button.clicked.connect(lambda: self._on_access_button_clicked(profile))
        access_button.setCursor(Qt.PointingHandCursor)
        access_button.setToolTip("Acceder al perfil")

        # Agrega al layout
        card_layout.addLayout(image_container)
        card_layout.addWidget(title_label)
        card_layout.addWidget(access_button)
        card_layout.setAlignment(access_button, Qt.AlignCenter)

        card_frame.setLayout(card_layout)

        return card_frame

    def _clear_cards(self):
        if not hasattr(self, "cards_flow_layout"):
            return
        while self.cards_flow_layout.count():
            item = self.cards_flow_layout.takeAt(0)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()

    def _on_access_button_clicked(self, profile):
        self._confirm_and_open(profile)

    def _build_list_group(self, title, list_widget):
        container = QFrame()
        container.setStyleSheet(
            """
            QFrame {
                background-color: #faf8fc;
                border: 1px solid #ece8f4;
                border-radius: 10px;
            }
            """
        )
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        label = QLabel(title)
        label.setStyleSheet("font-size: 14px; font-weight: 600; color: #5a155b;")
        layout.addWidget(label)

        list_widget.setStyleSheet(
            """
            QListWidget {
                border: none;
                background-color: transparent;
            }
            QListWidget::item {
                padding: 6px 4px;
            }
            """
        )
        list_widget.setMinimumHeight(150)
        list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(list_widget)

        return container

    def _format_profile_label(self, profile):
        display_name = profile.get("display_name") or profile.get("name") or "Perfil"
        display_name = str(display_name)
        path = profile.get("path") or ""
        folder = os.path.basename(path) if path else ""
        if folder and folder.lower() not in display_name.lower():
            return f"{display_name} ({folder})"
        return display_name

    def _on_consent_checkbox_changed(self, state):
        self.user_consented = state == Qt.Checked
        self.apply_selection_button.setEnabled(self.user_consented)
        self.settings.setValue("chrome_profile_consent", "yes" if self.user_consented else "no")

    def _load_approved_paths(self):
        stored = self.settings.value("chrome_approved_profiles")
        if isinstance(stored, str):
            try:
                data = json.loads(stored)
                if isinstance(data, list):
                    return [str(data[0])] if data else []
            except json.JSONDecodeError:
                return [stored]
        if isinstance(stored, list):
            return [str(stored[0])] if stored else []
        return []

    def _save_approved_paths(self):
        self.approved_paths = self.approved_paths[:1]
        self.settings.setValue("chrome_approved_profiles", json.dumps(self.approved_paths))

    def _populate_active_list(self):
        self.active_list_widget.clear()
        for profile in self.profiles_data:
            item = QListWidgetItem(self._format_profile_label(profile))
            item.setData(Qt.UserRole, profile.get("path"))
            self.active_list_widget.addItem(item)

    def _populate_approved_list(self):
        self._updating_approved_list = True
        self.approved_list_widget.clear()
        target_path = self.selected_path or (self.approved_paths[0] if self.approved_paths else None)
        if not self.selected_path and target_path:
            self.selected_path = target_path
        for profile in self.profiles_data:
            item = QListWidgetItem(self._format_profile_label(profile))
            item.setFlags(
                item.flags()
                | Qt.ItemIsUserCheckable
                | Qt.ItemIsSelectable
                | Qt.ItemIsEnabled
            )
            path = profile.get("path")
            item.setData(Qt.UserRole, path)
            item.setCheckState(Qt.Checked if path and path == target_path else Qt.Unchecked)
            self.approved_list_widget.addItem(item)
        self._updating_approved_list = False
        if target_path:
            self._select_approved_item(target_path)
            self._update_selected_list()

    def _update_selected_list(self):
        self.selected_list_widget.clear()
        if not self.selected_path:
            return
        profile = self._profile_by_path(self.selected_path)
        if not profile:
            return
        item = QListWidgetItem(self._format_profile_label(profile))
        item.setFlags(Qt.ItemIsEnabled)
        self.selected_list_widget.addItem(item)
        self._select_approved_item(self.selected_path)

    def _select_approved_item(self, path):
        if not path:
            return
        for index in range(self.approved_list_widget.count()):
            item = self.approved_list_widget.item(index)
            if item.data(Qt.UserRole) == path:
                self.approved_list_widget.setCurrentItem(item)
                if item.checkState() != Qt.Checked:
                    self._updating_approved_list = True
                    item.setCheckState(Qt.Checked)
                    self._updating_approved_list = False
                break

    def _profile_by_path(self, path):
        if not path:
            return None
        return self.profile_lookup.get(path)

    def _remember_selected_profile(self, profile, *, update_ui=True):
        if not profile:
            return
        path = profile.get("path")
        if not path:
            return
        self.selected_profile_data = profile
        self.selected_path = path
        self.approved_paths = [path]
        self._save_approved_paths()
        display = profile.get("display_name") or profile.get("name")
        if display:
            self.settings.setValue("chrome_profile_display_name", display)
        self.settings.setValue("chrome_profile_path", path)
        if update_ui:
            self._populate_approved_list()

    def _on_approved_item_changed(self, item):
        if self._updating_approved_list or not item:
            return
        path = item.data(Qt.UserRole)
        if not path:
            return
        if item.checkState() == Qt.Checked:
            self._updating_approved_list = True
            for index in range(self.approved_list_widget.count()):
                other = self.approved_list_widget.item(index)
                if other is item:
                    continue
                if other.checkState() == Qt.Checked:
                    other.setCheckState(Qt.Unchecked)
            self._updating_approved_list = False
            profile = self._profile_by_path(path)
            if profile:
                self._remember_selected_profile(profile)
        else:
            if path in self.approved_paths:
                self.approved_paths = []
                self._save_approved_paths()
            if self.selected_path == path:
                self.selected_path = None
                self.selected_profile_data = None
                self.settings.remove("chrome_profile_path")
                self.settings.remove("chrome_profile_display_name")
                self.selected_list_widget.clear()
                GlobalState.selected_profile = None
                GlobalState.current_profile_dir = None

    def _on_approved_item_activated(self, item):
        if not item:
            return
        if item.checkState() != Qt.Checked:
            QMessageBox.information(
                self,
                "Perfil no aprobado",
                "Marca el perfil como aprobado antes de seleccionarlo."
            )
            return
        profile = self._profile_by_path(item.data(Qt.UserRole))
        if profile:
            self._remember_selected_profile(profile)

    def _on_use_selected_clicked(self):
        if not self.user_consented:
            QMessageBox.warning(
                self,
                "Consentimiento requerido",
                "Confirma que estás de acuerdo en usar los perfiles seleccionados."
            )
            return
        current_item = self.approved_list_widget.currentItem()
        profile = None
        if current_item:
            if current_item.checkState() != Qt.Checked:
                QMessageBox.information(
                    self,
                    "Seleccionar perfil",
                    "Aprueba el perfil marcando la casilla antes de continuar."
                )
                return
            profile = self._profile_by_path(current_item.data(Qt.UserRole))
        elif self.selected_path:
            profile = self._profile_by_path(self.selected_path)
        if not profile:
            QMessageBox.information(
                self,
                "Seleccionar perfil",
                "Selecciona un perfil aprobado para continuar."
            )
            return
        self._confirm_and_open(profile)

    def _prompt_initial_consent(self):
        message = QMessageBox(self)
        message.setWindowTitle("Uso de perfiles de Chrome")
        message.setText(
            "Antes de continuar, confirma si estás de acuerdo en usar tus perfiles de Google Chrome.\n"
            "También puedes aprobar perfiles específicos desde la lista."
        )
        agree_btn = message.addButton("Estoy de acuerdo", QMessageBox.AcceptRole)
        message.addButton("Seleccionar perfiles", QMessageBox.ActionRole)
        message.exec_()
        if message.clickedButton() == agree_btn:
            self.consent_checkbox.setChecked(True)
        else:
            self.consent_checkbox.setChecked(False)

    def _show_previous_profile_prompt(self):
        if not self.selected_path or not self.selected_profile_data:
            return
        profile = self.selected_profile_data
        display = profile.get("display_name") or profile.get("name") or os.path.basename(self.selected_path)
        box = QMessageBox(self)
        box.setWindowTitle("Perfil previo detectado")
        box.setText(
            f"Se detectó que anteriormente usaste el perfil \"{display}\".\n"
            "¿Deseas utilizarlo nuevamente o seleccionar un perfil distinto?"
        )
        use_prev_btn = box.addButton("Usar perfil previo", QMessageBox.AcceptRole)
        change_btn = box.addButton("Cambiar de perfil", QMessageBox.RejectRole)
        box.exec_()
        if box.clickedButton() == use_prev_btn:
            self._confirm_and_open(
                profile,
                require_confirmation=False,
                auto_consent=True
            )
        elif box.clickedButton() == change_btn:
            self._select_approved_item(self.selected_path)

    def _confirm_and_open(self, profile, require_confirmation=True, auto_consent=False):
        if not profile:
            QMessageBox.warning(self, "Perfil", "No se pudo identificar el perfil seleccionado.")
            return
        if auto_consent and not self.user_consented:
            if not self.consent_checkbox.isChecked():
                self.consent_checkbox.setChecked(True)
            self.user_consented = True
            self.apply_selection_button.setEnabled(True)
            self.settings.setValue("chrome_profile_consent", "yes")
        if not self.user_consented:
            QMessageBox.warning(
                self,
                "Consentimiento requerido",
                "Confirma que estás de acuerdo en usar los perfiles seleccionados."
            )
            return
        if require_confirmation:
            dialog = ProfileConfirmDialog(
                profile.get("display_name") or profile.get("name") or "Perfil",
                self,
            )
            if dialog.exec_() != QDialog.Accepted:
                return
        if auto_consent:
            self.hide()
        self._remember_selected_profile(profile, update_ui=not auto_consent)
        GlobalState.set_profile(profile)
        # Al pasar al dashboard solo mostramos la vista principal; el usuario abrirá PLE manualmente
        self._open_dashboard(show_ple=False)

    def _open_dashboard(self, show_ple=False):
        from PyQt5.QtWidgets import QApplication
        from qt_views.DashboardWindow import DashboardWindow

        app = QApplication.instance()
        existing_dashboard = None
        if app:
            for widget in app.topLevelWidgets():
                if isinstance(widget, DashboardWindow):
                    existing_dashboard = widget
                    break

        candidate = GlobalState.dashboard_window
        if candidate is not None and not isinstance(candidate, DashboardWindow):
            candidate = None

        target_dashboard = existing_dashboard or candidate or DashboardWindow()
        sidebar = getattr(target_dashboard, "sidebar", None)

        try:
            if show_ple:
                handled = sidebar.select_item("PLE") if sidebar else False
                if not handled and hasattr(target_dashboard, "show_ple_view"):
                    target_dashboard.show_ple_view()

            target_dashboard.show()
            target_dashboard.raise_()
            target_dashboard.activateWindow()
        except Exception:
            if not self.isVisible():
                self.show()
            raise
        else:
            self.dashboard_window = target_dashboard
            GlobalState.set_dashboard_window(target_dashboard)
            self.close()

    def center_window(self):
        qr = self.frameGeometry()
        cp = QApplication.desktop().screen().rect().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def go_to_dashboard(self):
        from qt_views.DashboardWindow import DashboardWindow

        self.dashboard_window = DashboardWindow()
        self.dashboard_window.show()
        self.close()


def main():
    app = QApplication(sys.argv)
    window = ProfileWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
