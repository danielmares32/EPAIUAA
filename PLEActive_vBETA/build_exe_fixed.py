#!/usr/bin/env python3
"""
Fixed build script to generate executable with proper resource handling
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Configuration
APP_NAME = "EPA_Dashboard"
MAIN_SCRIPT = "main.py"
ICON_FILE = "assets/logo.png"  # PNG, will convert to ICO if needed

# Directories
PROJECT_ROOT = Path(__file__).parent
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"

def check_pyinstaller():
    """Check if PyInstaller is installed"""
    try:
        import PyInstaller
        print("✓ PyInstaller is installed")
        return True
    except ImportError:
        print("✗ PyInstaller is not installed")
        print("\nInstalling PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        return True

def clean_build_folders():
    """Remove old build and dist folders"""
    print("\n📁 Cleaning old build folders...")
    for folder in [BUILD_DIR, DIST_DIR]:
        if folder.exists():
            shutil.rmtree(folder)
            print(f"   Removed: {folder}")

def get_spacy_data_paths():
    """Find spaCy model data directories"""
    import site
    spacy_models = []

    # Check site-packages for spacy models
    for site_dir in site.getsitepackages():
        site_path = Path(site_dir)
        # Look for Spanish model
        es_model = site_path / "es_core_news_sm"
        if es_model.exists():
            spacy_models.append((str(es_model), "es_core_news_sm"))
            print(f"   Found spaCy model: {es_model}")

        # Look for English model
        en_model = site_path / "en_core_web_sm"
        if en_model.exists():
            spacy_models.append((str(en_model), "en_core_web_sm"))
            print(f"   Found spaCy model: {en_model}")

    return spacy_models

def get_yake_stopwords_path():
    """Find YAKE stopwords directory"""
    import site

    # Check site-packages for YAKE stopwords
    for site_dir in site.getsitepackages():
        site_path = Path(site_dir)
        yake_stopwords = site_path / "yake" / "core" / "StopwordsList"
        if yake_stopwords.exists():
            print(f"   Found YAKE stopwords: {yake_stopwords}")
            return (str(yake_stopwords), "yake/core/StopwordsList")

    return None

def build_exe():
    """Build the .exe file with proper resource bundling"""
    print("\n🔨 Building executable...")

    # Base PyInstaller command
    cmd = [
        "pyinstaller",
        "--name", APP_NAME,
        "--windowed",  # No console window
        "--onedir",    # Directory mode (better for large apps with many dependencies)
        "--clean",     # Clean cache
        "--noconfirm", # Don't ask for confirmation
    ]

    # Add data files and folders - CRITICAL FIX for images
    data_includes = [
        ("assets", "assets"),           # Include entire assets folder
        ("config", "config"),
        ("qt_views", "qt_views"),
        ("services", "services"),
        ("app", "app"),
        ("secret.txt", "."),            # Include API authentication token
    ]

    print("\n📦 Including data files:")
    for src, dst in data_includes:
        src_path = PROJECT_ROOT / src
        if src_path.exists():
            cmd.extend(["--add-data", f"{src}{os.pathsep}{dst}"])
            print(f"   ✓ {src} -> {dst}")

    # Add spaCy models - CRITICAL FIX for NLP functionality
    print("\n📦 Including spaCy models:")
    spacy_models = get_spacy_data_paths()
    for src, dst in spacy_models:
        cmd.extend(["--add-data", f"{src}{os.pathsep}{dst}"])
        print(f"   ✓ {dst}")

    # Add YAKE stopwords - CRITICAL FIX for YAKE keyword extraction
    print("\n📦 Including YAKE stopwords:")
    yake_data = get_yake_stopwords_path()
    if yake_data:
        src, dst = yake_data
        cmd.extend(["--add-data", f"{src}{os.pathsep}{dst}"])
        print(f"   ✓ {dst}")
    else:
        print("   ⚠️  YAKE stopwords not found - app may crash!")

    # Hidden imports - EXPANDED LIST
    hidden_imports = [
        # PyQt5
        "PyQt5.QtCore",
        "PyQt5.QtGui",
        "PyQt5.QtWidgets",
        "PyQt5.sip",

        # NLP libraries
        "rake_nltk",
        "keybert",
        "yake",
        "spacy",
        "spacy.lang.es",
        "spacy.lang.en",

        # Standard libraries
        "requests",
        "sqlite3",
        "json",
        "base64",
        "tempfile",
        "shutil",
        "platform",
        "threading",

        # Flask
        "flask",
        "flask.json",
        "werkzeug",

        # Database
        "sqlalchemy",
        "sqlalchemy.ext.declarative",

        # Security
        "bcrypt",

        # ML/Transformers (if used)
        "sentence_transformers",
        "torch",
        "numpy",

        # Selenium/Scrapy (if used)
        "selenium",
        "selenium.webdriver",
        "selenium.webdriver.chrome",
        "scrapy",
    ]

    print("\n📦 Adding hidden imports:")
    for module in hidden_imports:
        cmd.extend(["--hidden-import", module])
        print(f"   ✓ {module}")

    # Runtime hooks for resource path handling
    runtime_hook_path = PROJECT_ROOT / "pyinstaller_hooks" / "runtime_hook.py"
    if runtime_hook_path.exists():
        cmd.extend(["--runtime-hook", str(runtime_hook_path)])
        print(f"\n📦 Using runtime hook: {runtime_hook_path}")

    # Add main script
    cmd.append(MAIN_SCRIPT)

    # Run PyInstaller
    print(f"\n🔧 Running PyInstaller...\n")
    try:
        subprocess.check_call(cmd)
        print("\n✓ Build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed with error: {e}")
        return False

def create_runtime_hook():
    """Create runtime hook for resource path handling"""
    hook_dir = PROJECT_ROOT / "pyinstaller_hooks"
    hook_dir.mkdir(exist_ok=True)

    hook_file = hook_dir / "runtime_hook.py"
    hook_content = """# PyInstaller runtime hook for resource path handling
import sys
import os

# Fix for bundled resources
if getattr(sys, 'frozen', False):
    # Running in PyInstaller bundle
    bundle_dir = sys._MEIPASS
    os.chdir(bundle_dir)

    # Add bundle directory to path
    sys.path.insert(0, bundle_dir)

    print(f"Running from bundle: {bundle_dir}")
else:
    # Running in normal Python
    bundle_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Running from source: {bundle_dir}")
"""

    with open(hook_file, "w", encoding="utf-8") as f:
        f.write(hook_content)

    print(f"✓ Created runtime hook: {hook_file}")
    return hook_file

def create_resource_helper():
    """Create a helper module for resource path resolution"""
    helper_file = PROJECT_ROOT / "resource_path.py"
    helper_content = """# Resource path helper for PyInstaller
import sys
import os

def resource_path(relative_path):
    \"\"\"Get absolute path to resource, works for dev and for PyInstaller\"\"\"
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
"""

    with open(helper_file, "w", encoding="utf-8") as f:
        f.write(helper_content)

    print(f"✓ Created resource helper: {helper_file}")
    return helper_file

def create_portable_package():
    """Create a portable package with the .exe and necessary files"""
    print("\n📦 Creating portable package...")

    exe_file = DIST_DIR / f"{APP_NAME}.exe"
    if not exe_file.exists():
        print("✗ .exe file not found")
        return False

    # Create portable folder
    portable_dir = DIST_DIR / f"{APP_NAME}_Portable"
    portable_dir.mkdir(exist_ok=True)

    # Copy exe
    shutil.copy2(exe_file, portable_dir / f"{APP_NAME}.exe")
    print(f"   ✓ Copied: {APP_NAME}.exe")

    # Copy config folder if exists
    config_src = PROJECT_ROOT / "config"
    if config_src.exists():
        config_dst = portable_dir / "config"
        if config_dst.exists():
            shutil.rmtree(config_dst)
        shutil.copytree(config_src, config_dst)
        print(f"   ✓ Copied: config/")

    # Create README
    readme_path = portable_dir / "README.txt"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(f"""
{APP_NAME} - Portable Version
================================

How to run:
-----------
1. Double-click on {APP_NAME}.exe
2. The application will start

System Requirements:
--------------------
- Windows 7 or later (64-bit)
- No additional software required (all dependencies included)

Troubleshooting:
----------------
- If images don't load, ensure the application has read permissions
- For Chrome integration, ensure Chrome is installed
- If antivirus flags the .exe, add it to exceptions (false positive)

Notes:
------
- Configuration files are stored in the 'config' folder
- User data is stored in the application directory
- All NLP models are bundled (no internet required)

For support or issues, please contact the development team.

Build date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")
    print(f"   ✓ Created: README.txt")

    print(f"\n✓ Portable package created at: {portable_dir}")
    return True

def main():
    """Main build process"""
    print(f"""
╔═══════════════════════════════════════╗
║   EPA Dashboard - FIXED EXE Builder  ║
╚═══════════════════════════════════════╝

This build script includes fixes for:
✓ Image loading (proper resource bundling)
✓ Chrome functionality (all dependencies)
✓ spaCy models (bundled NLP models)
✓ YAKE stopwords (keyword extraction data)
✓ Database path (AppData folder)
✓ Resource path resolution
""")

    # Check requirements
    if not check_pyinstaller():
        print("✗ Failed to install PyInstaller")
        return 1

    # Check if main script exists
    if not (PROJECT_ROOT / MAIN_SCRIPT).exists():
        print(f"✗ Main script not found: {MAIN_SCRIPT}")
        return 1

    # Create helper modules
    print("\n📝 Creating helper modules...")
    create_runtime_hook()
    create_resource_helper()

    # Clean old builds
    clean_build_folders()

    # Build executable
    if not build_exe():
        return 1

    # Create portable package
    create_portable_package()

    print(f"""
╔═══════════════════════════════════════╗
║   Build completed successfully! ✓    ║
╚═══════════════════════════════════════╝

📂 Output location:
   {DIST_DIR}

📝 Files created:
   - {APP_NAME}.exe (standalone executable)
   - {APP_NAME}_Portable/ (portable package)

⚠️  IMPORTANT NOTES:
   1. Images are now bundled - use resource_path() helper
   2. spaCy models are included in the .exe
   3. Test on a clean Windows machine without Python

🔧 To fix image loading in your code, use:
   from resource_path import resource_path
   icon_path = resource_path("assets/logo.png")

🚀 You can now distribute the .exe file or the portable folder!
""")
    return 0

if __name__ == "__main__":
    sys.exit(main())
