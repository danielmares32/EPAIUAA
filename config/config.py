import os
import sys
from pathlib import Path
import base64
import logging

logger = logging.getLogger(__name__)

def get_data_dir():
    """Get the directory for storing app data (database, etc.)"""
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle - use user's home directory
        if sys.platform == 'darwin':  # macOS
            data_dir = Path.home() / 'Library' / 'Application Support' / 'EPA Dashboard'
        elif sys.platform == 'win32':  # Windows
            data_dir = Path(os.getenv('APPDATA')) / 'EPA Dashboard'
        else:  # Linux
            data_dir = Path.home() / '.epa_dashboard'
    else:
        # Running in development - use instance folder
        data_dir = Path(__file__).parent.parent / 'instance'

    # Create directory if it doesn't exist
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def resource_path(relative_path):
    """
    Get absolute path to resource - works for dev and PyInstaller bundle.

    Args:
        relative_path: Path relative to project root (e.g., "assets/logo.png")

    Returns:
        Absolute path as string
    """
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        base_path = Path(sys._MEIPASS)
    else:
        # Running in development
        base_path = Path(__file__).parent.parent

    return str(base_path / relative_path)

def get_api_token():
    """
    Retrieve API access token from environment or secure file.
    Priority: ENV_VAR > secret.txt (bundled or local) > None

    Security: Token should be provided via:
    1. Environment variable API_ACCESS_TOKEN (production/containers)
    2. secret.txt file (development or bundled in .app/.exe)
    """
    # First priority: Environment variable (for production/containers)
    token = os.getenv('API_ACCESS_TOKEN')
    if token:
        logger.debug("API token loaded from environment variable")
        return token

    # Second priority: secret.txt file
    # Check multiple locations for PyInstaller compatibility
    secret_locations = []

    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        bundle_dir = Path(sys._MEIPASS)
        secret_locations.append(bundle_dir / 'secret.txt')

    # Development location
    secret_locations.append(Path(__file__).parent.parent / 'secret.txt')

    for secret_file in secret_locations:
        if secret_file.exists():
            try:
                with open(secret_file, 'r', encoding='utf-8') as f:
                    token = f.read().strip()
                    if token:
                        logger.debug(f"API token loaded from {secret_file}")
                        return token
            except Exception as e:
                logger.error(f"Failed to read {secret_file}: {e}")

    logger.warning("No API access token found. API calls will fail authentication.")
    return None

def get_auth_headers():
    """
    Generate Authorization headers for API requests.
    Returns dict with Bearer token or empty dict if no token available.
    """
    token = get_api_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'epaisistema')

    # Use absolute path for database
    DB_PATH = get_data_dir() / 'epai.db'
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # API Configuration
    API_BASE_URL = os.getenv('API_BASE_URL', 'https://uninovadeplan-ws.javali.pt')
    API_TIMEOUT = int(os.getenv('API_TIMEOUT', '10'))

    # API Access Token (Bearer authentication)
    API_ACCESS_TOKEN = get_api_token()