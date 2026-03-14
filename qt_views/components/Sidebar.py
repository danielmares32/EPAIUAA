from PyQt5.QtWidgets import QFrame, QVBoxLayout, QListWidget, QListWidgetItem, QSizePolicy
from PyQt5.QtCore import Qt, QSize

class Sidebar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #5a155b; color: white; padding: 10px;")
        self.setMinimumWidth(220)  # Increased from 200 to prevent text cutoff
        self.setMaximumWidth(280)  # Allow some flexibility

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 15, 8, 15)  # Better margins for text visibility
        layout.setSpacing(10)

        # Menú lateral con Inicio + PLE (siempre habilitado)
        self.menu = QListWidget()
        self.menu.setStyleSheet("""
            QListWidget {
                background-color: #5a155b;
                color: white;
                font-size: 15px;
                font-weight: 500;
                border: none;
                padding: 8px;
                outline: none;
            }
            QListWidget::item {
                color: white;
                padding: 10px 15px;
                border: none;
                border-radius: 4px;
                margin: 2px 0px;
                min-height: 25px;
                background-color: transparent;
            }
            QListWidget::item[data-indent="1"] {
                padding-left: 30px;
                font-size: 13px;
            }
            QListWidget::item[data-parent="true"] {
                font-weight: bold;
            }
            QListWidget::item:selected {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                font-weight: bold;
            }
            QListWidget::item:hover {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
            }
            QListWidget::item:pressed {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        self.menu.setMinimumWidth(200)  # Ensure menu has enough width

        # Store PLE items for dynamic updates
        self.ple_items = []  # List of PLE parent items
        self.ple_subitems = {}  # Dict: ple_env_id -> list of submenu items
        self.ple_expanded = False
        self.ple_expanded_state = {}  # Track which PLEs are expanded
        self.ple_data = []

        item_inicio = QListWidgetItem("Inicio")
        item_inicio.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        item_inicio.setSizeHint(QSize(180, 40))  # Explicit size for visibility
        item_inicio.setData(Qt.UserRole, {"type": "main", "id": "inicio"})
        self.menu.addItem(item_inicio)

        self.item_ple = QListWidgetItem("▶ PLE")
        self.item_ple.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.item_ple.setSizeHint(QSize(180, 40))  # Explicit size for visibility
        self.item_ple.setData(Qt.UserRole, {"type": "parent", "id": "ple", "clickable": True})
        # PLE siempre habilitado
        self.menu.addItem(self.item_ple)

        # Ensure menu has proper minimum size
        self.menu.setMinimumSize(180, 90)

        # Optimize size policy for better layout management
        self.menu.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # Force visibility of menu and items
        self.menu.setVisible(True)
        self.menu.show()

        # Force geometry update
        self.menu.updateGeometry()

        # Conectar el cambio de selección
        self.menu.currentItemChanged.connect(self.on_item_changed)

        # Add menu to layout with stretch factor for proper distribution
        layout.addWidget(self.menu, 1)  # stretch factor 1
        layout.addStretch(0)  # minimal stretch at bottom

    def update_ple_submenu(self, ple_list, auto_expand=True):
        """Update the PLE submenu with the list of available PLEs."""
        print(f"[Sidebar] update_ple_submenu called with {len(ple_list) if ple_list else 0} PLEs")
        self.ple_data = ple_list

        # Remove existing PLE items and their subitems
        for item in self.ple_items:
            row = self.menu.row(item)
            if row >= 0:
                self.menu.takeItem(row)

        # Remove all subitems
        for subitems in self.ple_subitems.values():
            for subitem in subitems:
                row = self.menu.row(subitem)
                if row >= 0:
                    self.menu.takeItem(row)

        self.ple_items.clear()
        self.ple_subitems.clear()

        # Auto-expand on first load if requested
        if auto_expand and ple_list and not self.ple_expanded:
            self.ple_expanded = True
            self.item_ple.setText("▼ PLE")
            print("[Sidebar] Auto-expanding PLE submenu")

        # If expanded, add PLE items
        if self.ple_expanded and ple_list:
            ple_row = self.menu.row(self.item_ple)
            print(f"[Sidebar] Adding {len(ple_list)} PLE items at row {ple_row}")

            insert_position = ple_row + 1

            for idx, ple in enumerate(ple_list):
                if not isinstance(ple, dict):
                    continue

                ple_name = ple.get("name", "PLE sin nombre")
                env_id = ple.get("environmentID")

                # Create PLE parent item with expand arrow
                item = QListWidgetItem(f"  ▶ {ple_name}")
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                item.setSizeHint(QSize(180, 35))
                item.setData(Qt.UserRole, {
                    "type": "ple_parent",
                    "id": f"ple_{env_id}",
                    "ple_data": ple,
                    "env_id": env_id
                })

                # Insert PLE item
                self.menu.insertItem(insert_position, item)
                self.ple_items.append(item)
                insert_position += 1

                print(f"[Sidebar] Added PLE parent: {ple_name}")
        else:
            print(f"[Sidebar] Not adding items - expanded: {self.ple_expanded}, has data: {bool(ple_list)}")

    def toggle_ple_submenu(self):
        """Toggle the visibility of PLE submenu items."""
        self.ple_expanded = not self.ple_expanded

        if self.ple_expanded:
            self.item_ple.setText("▼ PLE")
            self.update_ple_submenu(self.ple_data)
        else:
            self.item_ple.setText("▶ PLE")
            # Remove PLE items and their subitems
            for item in self.ple_items:
                row = self.menu.row(item)
                if row >= 0:
                    self.menu.takeItem(row)

            # Remove all subitems
            for subitems in self.ple_subitems.values():
                for subitem in subitems:
                    row = self.menu.row(subitem)
                    if row >= 0:
                        self.menu.takeItem(row)

            self.ple_items.clear()
            self.ple_subitems.clear()
            self.ple_expanded_state.clear()

    def toggle_ple_item_submenu(self, ple_item, env_id, ple_data):
        """Toggle the visibility of submenu items for a specific PLE."""
        # Check if this PLE is already expanded
        is_expanded = self.ple_expanded_state.get(env_id, False)

        if is_expanded:
            # Collapse: remove subitems
            ple_item.setText(ple_item.text().replace("▼", "▶"))
            if env_id in self.ple_subitems:
                for subitem in self.ple_subitems[env_id]:
                    row = self.menu.row(subitem)
                    if row >= 0:
                        self.menu.takeItem(row)
                del self.ple_subitems[env_id]
            self.ple_expanded_state[env_id] = False
        else:
            # Expand: add subitems
            ple_item.setText(ple_item.text().replace("▶", "▼"))
            ple_row = self.menu.row(ple_item)

            # Define submenu options
            submenu_options = [
                ("Inicio", "inicio"),
                ("Preferencias", "preferencias"),
                ("Cambiar PLE", "cambiar_ple")
            ]

            subitems = []
            for idx, (label, section) in enumerate(submenu_options):
                subitem = QListWidgetItem(f"      • {label}")
                subitem.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                subitem.setSizeHint(QSize(180, 30))
                subitem.setData(Qt.UserRole, {
                    "type": "ple_section",
                    "section": section,
                    "ple_data": ple_data,
                    "env_id": env_id
                })

                # Insert after the PLE parent item
                self.menu.insertItem(ple_row + 1 + idx, subitem)
                subitems.append(subitem)

            self.ple_subitems[env_id] = subitems
            self.ple_expanded_state[env_id] = True
            print(f"[Sidebar] Added {len(subitems)} subitems for PLE {env_id}")

    def on_item_changed(self, current, previous):
        """Delegar al método padre `on_sidebar_menu(text)`."""
        if not current:
            return

        item_data = current.data(Qt.UserRole)
        if not item_data:
            return

        item_type = item_data.get("type")

        # Level 1: Main PLE parent clicked
        if item_type == "parent" and item_data.get("id") == "ple":
            # If already expanded, show PLE list instead of collapsing
            if self.ple_expanded:
                if hasattr(self.parent(), "on_sidebar_menu_ple_list"):
                    self.parent().on_sidebar_menu_ple_list()
            else:
                # If collapsed, expand to show PLEs
                self.toggle_ple_submenu()
            return

        # Level 2: Individual PLE clicked - toggle its submenu
        if item_type == "ple_parent":
            env_id = item_data.get("env_id")
            ple_data = item_data.get("ple_data")
            self.toggle_ple_item_submenu(current, env_id, ple_data)
            return

        # Level 3: PLE section clicked - open specific content
        if item_type == "ple_section":
            if hasattr(self.parent(), "on_sidebar_menu_ple_section"):
                section = item_data.get("section")
                ple_data = item_data.get("ple_data")
                self.parent().on_sidebar_menu_ple_section(ple_data, section)
            return

        # Handle main menu selections
        if hasattr(self.parent(), "on_sidebar_menu"):
            if item_type == "main":
                self.parent().on_sidebar_menu(current.text())

    def select_item(self, target: str) -> bool:
        """
        Selecciona programáticamente un elemento del sidebar y dispara el manejador
        correspondiente en la ventana contenedora.
        """
        if not target:
            return False

        normalized = target.strip().lower()

        # Caso especial para el nodo principal PLE
        if normalized == "ple":
            row = self.menu.row(self.item_ple)
            if row < 0:
                return False
            if self.menu.currentRow() != row:
                self.menu.setCurrentRow(row)
            else:
                self.on_item_changed(self.item_ple, None)

            if not self.ple_expanded:
                self.toggle_ple_submenu()

            parent = self.parent()
            if parent and hasattr(parent, "on_sidebar_menu_ple_list"):
                parent.on_sidebar_menu_ple_list()
            return True

        for idx in range(self.menu.count()):
            item = self.menu.item(idx)
            if not item:
                continue

            data = item.data(Qt.UserRole) or {}
            item_id = str(data.get("id", "")).lower()
            item_text = item.text()
            simplified = (
                item_text.replace("▶", "")
                .replace("▼", "")
                .replace("•", "")
                .strip()
                .lower()
            )

            if normalized in (item_id, simplified):
                if self.menu.currentRow() != idx:
                    self.menu.setCurrentRow(idx)
                else:
                    self.on_item_changed(item, None)
                return True

        return False
