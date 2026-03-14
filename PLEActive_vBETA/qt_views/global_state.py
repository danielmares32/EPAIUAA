# qt_views/global_state.py

import os
from pathlib import Path


class GlobalState:
    """
    Estado global de la app: guarda user_id, perfiles de Chrome y contexto del PLE.
    """

    user_id = None
    user_name = None  # Nombre del usuario autenticado (si aplica)
    selected_profile = None
    current_profile_dir = None   # Carpeta de Chrome (Default, Profile 1, etc.)
    selected_profile_path = None  # Ruta completa del perfil cuando está disponible
    active_ple = None
    approved_profiles = []
    dashboard_window = None

    # Estado de seguimiento (PLE)
    tracking_armed = False        # ¿Está armado para ejecutar?
    tracking_mode = ""            # "all" | "approved" | "none" | "logout"
    last_environment_id = None    # Último environmentID seleccionado en PLEView

    @classmethod
    def set_profile(cls, profile):
        """
        Guarda el perfil seleccionado (dict o str) y resuelve la carpeta de Chrome.
        """
        cls.selected_profile = profile
        cls.selected_profile_path = None
        cls.current_profile_dir = None

        path = None
        name_hint = None

        if isinstance(profile, dict):
            name_hint = profile.get("display_name") or profile.get("name")
            path = profile.get("path") or profile.get("profile_path") or profile.get("directory")
        elif isinstance(profile, str):
            path = profile.strip()

        if isinstance(path, str) and path.strip():
            cleaned = path.strip()
            cls.selected_profile_path = cleaned
            folder = Path(cleaned).name
            if not folder:
                folder = os.path.basename(cleaned.rstrip("\\/"))
            cls.current_profile_dir = folder or cleaned
        elif name_hint:
            cls.current_profile_dir = name_hint

        # Actualizar header del dashboard si está disponible
        window = cls.dashboard_window
        if window:
            header = getattr(window, "header", None)
            if header and hasattr(header, "refresh_profile"):
                header.refresh_profile()

    @classmethod
    def set_active_ple(cls, ple):
        """Guarda el PLE actualmente en uso."""
        cls.active_ple = ple

    @classmethod
    def clear_active_ple(cls):
        cls.active_ple = None

    @classmethod
    def register_approved_profile(cls, data):
        """Registra un perfil aprobado evitando duplicados simples."""
        if data and data not in cls.approved_profiles:
            cls.approved_profiles.append(data)

    @classmethod
    def get_approved_profiles(cls):
        return list(cls.approved_profiles)

    @classmethod
    def set_dashboard_window(cls, window):
        cls.dashboard_window = window
        if window:
            header = getattr(window, "header", None)
            if header and hasattr(header, "refresh_profile"):
                header.refresh_profile()
