#!/usr/bin/env python3
"""
macOS Application Builder for EPA Dashboard - FIXED VERSION
Creates a .app bundle and .dmg installer that actually works
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import plistlib
import site

# Configuration
APP_NAME = "EPA Dashboard"
APP_BUNDLE_NAME = "EPA_Dashboard.app"
APP_VERSION = "1.0.1"
APP_IDENTIFIER = "com.epai.dashboard"
MAIN_SCRIPT = "main.py"
ICON_FILE = "assets/logo.png"

# Directories
PROJECT_ROOT = Path(__file__).parent
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
DMG_DIR = PROJECT_ROOT / "dmg_temp"


def run_cmd(cmd, description=""):
    """Run command and return success status"""
    print(f"   Running: {' '.join(cmd[:3])}...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"   Error: {e.stderr}")
        return False, e.stderr


def check_requirements():
    """Check if required tools are installed"""
    print("\n[1/8] Checking requirements...")

    if sys.platform != "darwin":
        print("   ERROR: This script is for macOS only")
        return False

    # Check PyInstaller
    try:
        import PyInstaller
        print(f"   PyInstaller: {PyInstaller.__version__}")
    except ImportError:
        print("   Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Check spaCy models
    print("   Checking spaCy models...")
    import spacy
    for model in ["en_core_web_sm", "es_core_news_sm"]:
        if spacy.util.is_package(model):
            print(f"   {model}: OK")
        else:
            print(f"   Downloading {model}...")
            subprocess.check_call([sys.executable, "-m", "spacy", "download", model])

    return True


def clean_build():
    """Clean old build artifacts"""
    print("\n[2/8] Cleaning old builds...")
    for folder in [BUILD_DIR, DIST_DIR, DMG_DIR]:
        if folder.exists():
            shutil.rmtree(folder)
            print(f"   Removed: {folder.name}")


def create_icon():
    """Convert PNG to .icns"""
    print("\n[3/8] Creating application icon...")

    icon_png = PROJECT_ROOT / ICON_FILE
    if not icon_png.exists():
        print(f"   Warning: Icon not found at {icon_png}")
        return None

    iconset_dir = PROJECT_ROOT / "icon.iconset"
    iconset_dir.mkdir(exist_ok=True)

    sizes = [16, 32, 64, 128, 256, 512]
    try:
        for size in sizes:
            output = iconset_dir / f"icon_{size}x{size}.png"
            subprocess.run(
                ["sips", "-z", str(size), str(size), str(icon_png), "--out", str(output)],
                check=True, capture_output=True
            )
            if size <= 256:
                output_2x = iconset_dir / f"icon_{size}x{size}@2x.png"
                subprocess.run(
                    ["sips", "-z", str(size*2), str(size*2), str(icon_png), "--out", str(output_2x)],
                    check=True, capture_output=True
                )

        icns_file = PROJECT_ROOT / "icon.icns"
        subprocess.run(
            ["iconutil", "-c", "icns", str(iconset_dir), "-o", str(icns_file)],
            check=True, capture_output=True
        )
        shutil.rmtree(iconset_dir)
        print(f"   Created: icon.icns")
        return icns_file
    except Exception as e:
        print(f"   Error creating icon: {e}")
        if iconset_dir.exists():
            shutil.rmtree(iconset_dir)
        return None


def get_data_files():
    """Get all data files to include"""
    data_files = []

    # App directories
    dirs = ["assets", "config", "qt_views", "services", "app"]
    for d in dirs:
        path = PROJECT_ROOT / d
        if path.exists():
            data_files.append((str(path), d))

    # Secret file
    secret = PROJECT_ROOT / "secret.txt"
    if secret.exists():
        data_files.append((str(secret), "."))

    # spaCy models
    for site_dir in site.getsitepackages():
        site_path = Path(site_dir)
        for model in ["en_core_web_sm", "es_core_news_sm"]:
            model_path = site_path / model
            if model_path.exists():
                data_files.append((str(model_path), model))
                print(f"   Found spaCy model: {model}")

    # YAKE stopwords
    for site_dir in site.getsitepackages():
        site_path = Path(site_dir)
        yake_path = site_path / "yake" / "core" / "StopwordsList"
        if yake_path.exists():
            data_files.append((str(yake_path), "yake/core/StopwordsList"))
            print(f"   Found YAKE stopwords")
            break

    # NLTK data
    import nltk
    nltk_data = Path(nltk.data.path[0]) if nltk.data.path else None
    if nltk_data and nltk_data.exists():
        for subdir in ["corpora/stopwords", "tokenizers/punkt", "tokenizers/punkt_tab"]:
            data_path = nltk_data / subdir
            if data_path.exists():
                data_files.append((str(data_path), f"nltk_data/{subdir}"))
                print(f"   Found NLTK data: {subdir}")

    return data_files


def build_app():
    """Build the app using PyInstaller"""
    print("\n[4/8] Building application...")

    icns_file = create_icon()

    # Comprehensive hidden imports for all ML/NLP libraries
    hidden_imports = [
        # PyQt5
        "PyQt5", "PyQt5.QtCore", "PyQt5.QtGui", "PyQt5.QtWidgets", "PyQt5.sip",
        "PyQt5.QtNetwork", "PyQt5.QtPrintSupport",

        # Flask
        "flask", "flask.json", "flask.json.provider", "werkzeug", "werkzeug.routing",
        "werkzeug.utils", "jinja2", "markupsafe", "itsdangerous", "click",

        # SQLAlchemy
        "sqlalchemy", "sqlalchemy.ext.declarative", "sqlalchemy.orm",
        "sqlalchemy.engine", "sqlalchemy.pool",

        # NLP - spaCy
        "spacy", "spacy.lang", "spacy.lang.es", "spacy.lang.en",
        "spacy.tokenizer", "spacy.vocab", "spacy.pipeline",
        "thinc", "thinc.api", "thinc.layers", "thinc.model",
        "cymem", "cymem.cymem", "preshed", "preshed.maps", "murmurhash",
        "srsly", "srsly.msgpack", "srsly.json", "wasabi", "catalogue",
        "confection", "weasel",

        # NLP - NLTK
        "nltk", "nltk.tokenize", "nltk.corpus", "nltk.stem",

        # NLP - Keywords
        "yake", "rake_nltk", "keybert", "keybert.model",

        # ML - PyTorch
        "torch", "torch.nn", "torch.optim", "torch.utils", "torch.utils.data",
        "torch._C", "torch.cuda", "torch.backends",

        # ML - Transformers
        "transformers", "transformers.models", "transformers.tokenization_utils",
        "transformers.modeling_utils", "huggingface_hub", "safetensors",

        # ML - Sentence Transformers
        "sentence_transformers", "sentence_transformers.models",
        "sentence_transformers.util",

        # ML - sklearn
        "sklearn", "sklearn.feature_extraction", "sklearn.metrics",
        "sklearn.utils", "sklearn.preprocessing",

        # Core libs
        "numpy", "numpy.core", "numpy.linalg", "numpy.fft",
        "scipy", "scipy.sparse", "scipy.spatial",
        "pandas", "regex", "filelock", "packaging", "tqdm",

        # Selenium/Web
        "selenium", "selenium.webdriver", "selenium.webdriver.chrome",
        "selenium.webdriver.chrome.service", "selenium.webdriver.common",
        "webdriver_manager",

        # Scrapy
        "scrapy", "scrapy.spiders", "scrapy.http",

        # Security
        "bcrypt", "bcrypt._bcrypt",

        # HTTP
        "requests", "urllib3", "certifi", "charset_normalizer", "idna",

        # Standard library
        "sqlite3", "json", "base64", "tempfile", "shutil", "platform",
        "threading", "queue", "logging", "pathlib", "collections",
        "functools", "itertools", "typing", "dataclasses",

        # Misc
        "networkx", "PIL", "PIL.Image",
    ]

    print("\n   Including data files:")
    data_files = get_data_files()

    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "EPA_Dashboard",
        "--windowed",
        "--onedir",
        "--clean",
        "--noconfirm",
        "--osx-bundle-identifier", APP_IDENTIFIER,
    ]

    # Add icon
    if icns_file and icns_file.exists():
        cmd.extend(["--icon", str(icns_file)])

    # Add data files
    for src, dst in data_files:
        cmd.extend(["--add-data", f"{src}:{dst}"])

    # Add hidden imports
    for module in hidden_imports:
        cmd.extend(["--hidden-import", module])

    # Add collect-all for problematic packages
    for pkg in ["spacy", "thinc", "torch", "transformers", "sentence_transformers"]:
        cmd.extend(["--collect-all", pkg])

    # Architecture
    import platform
    if platform.machine() == "arm64":
        cmd.extend(["--target-arch", "arm64"])
        print("   Building for: Apple Silicon (arm64)")
    else:
        cmd.extend(["--target-arch", "x86_64"])
        print("   Building for: Intel (x86_64)")

    cmd.append(MAIN_SCRIPT)

    print("\n   Running PyInstaller (this may take several minutes)...")
    try:
        subprocess.check_call(cmd, cwd=str(PROJECT_ROOT))
        print("   Build completed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   Build failed: {e}")
        return False


def customize_plist():
    """Update Info.plist with proper values"""
    print("\n[5/8] Customizing Info.plist...")

    info_plist = DIST_DIR / APP_BUNDLE_NAME / "Contents" / "Info.plist"
    if not info_plist.exists():
        print(f"   Warning: Info.plist not found")
        return

    with open(info_plist, 'rb') as f:
        plist = plistlib.load(f)

    plist.update({
        'CFBundleDisplayName': APP_NAME,
        'CFBundleName': APP_NAME,
        'CFBundleVersion': APP_VERSION,
        'CFBundleShortVersionString': APP_VERSION,
        'CFBundleIdentifier': APP_IDENTIFIER,
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.15.0',  # Catalina for better compatibility
        'NSHumanReadableCopyright': '2025 EPAI Project',
        'NSRequiresAquaSystemAppearance': False,
        # Fix Gatekeeper issues
        'LSApplicationCategoryType': 'public.app-category.education',
        'NSAppleEventsUsageDescription': 'EPA Dashboard needs access to control other applications.',
    })

    with open(info_plist, 'wb') as f:
        plistlib.dump(plist, f)

    print("   Info.plist updated")


def sign_and_fix_security():
    """Sign the app and remove quarantine attributes"""
    print("\n[6/8] Fixing security issues...")

    app_path = DIST_DIR / APP_BUNDLE_NAME

    # Remove extended attributes (quarantine)
    print("   Removing quarantine attributes...")
    subprocess.run(["xattr", "-cr", str(app_path)], capture_output=True)

    # Check for signing identity
    result = subprocess.run(
        ["security", "find-identity", "-v", "-p", "codesigning"],
        capture_output=True, text=True
    )

    if "Developer ID Application" in result.stdout:
        # Extract signing identity
        import re
        match = re.search(r'"(Developer ID Application: [^"]+)"', result.stdout)
        if match:
            identity = match.group(1)
            print(f"   Found signing identity: {identity}")
            print("   Signing application...")

            # Sign the app
            sign_result = subprocess.run([
                "codesign", "--force", "--deep", "--sign", identity,
                "--options", "runtime",
                str(app_path)
            ], capture_output=True, text=True)

            if sign_result.returncode == 0:
                print("   App signed successfully!")
                return True
            else:
                print(f"   Signing failed: {sign_result.stderr}")
    else:
        print("   No Developer ID found - app will be unsigned")
        print("   Users will need to right-click > Open on first launch")

    # Ad-hoc signing (allows running locally without warnings)
    print("   Applying ad-hoc signature...")
    subprocess.run([
        "codesign", "--force", "--deep", "--sign", "-",
        str(app_path)
    ], capture_output=True)

    return False


def create_dmg():
    """Create DMG installer"""
    print("\n[7/8] Creating DMG installer...")

    app_path = DIST_DIR / APP_BUNDLE_NAME
    if not app_path.exists():
        print("   Error: App bundle not found")
        return False

    DMG_DIR.mkdir(exist_ok=True)

    # Copy app
    dmg_app = DMG_DIR / APP_BUNDLE_NAME
    if dmg_app.exists():
        shutil.rmtree(dmg_app)
    shutil.copytree(app_path, dmg_app, symlinks=True)

    # Create Applications symlink
    apps_link = DMG_DIR / "Applications"
    if apps_link.exists():
        apps_link.unlink()
    apps_link.symlink_to("/Applications")

    # Create README
    readme = DMG_DIR / "README.txt"
    readme.write_text(f"""{APP_NAME} v{APP_VERSION}
{'='*50}

INSTALLATION:
1. Drag {APP_BUNDLE_NAME} to the Applications folder
2. Open Applications and double-click {APP_NAME}

FIRST LAUNCH (Important!):
If macOS shows a security warning:
- Right-click (or Control-click) the app
- Select "Open" from the menu
- Click "Open" in the dialog

This only needs to be done once.

REQUIREMENTS:
- macOS 10.15 (Catalina) or later
- Chrome browser (for history sync features)

""")

    # Create DMG
    dmg_name = f"EPA_Dashboard_v{APP_VERSION}.dmg"
    dmg_path = DIST_DIR / dmg_name

    if dmg_path.exists():
        dmg_path.unlink()

    print(f"   Creating {dmg_name}...")
    result = subprocess.run([
        "hdiutil", "create",
        "-volname", APP_NAME,
        "-srcfolder", str(DMG_DIR),
        "-ov", "-format", "UDZO",
        str(dmg_path)
    ], capture_output=True, text=True)

    shutil.rmtree(DMG_DIR)

    if result.returncode == 0:
        size_mb = dmg_path.stat().st_size / (1024 * 1024)
        print(f"   Created: {dmg_name} ({size_mb:.1f} MB)")
        return True
    else:
        print(f"   DMG creation failed: {result.stderr}")
        return False


def main():
    """Main build process"""
    print(f"""
{'='*60}
  EPA Dashboard - macOS Build (Fixed Version)
{'='*60}
""")

    if not check_requirements():
        return 1

    clean_build()

    if not build_app():
        return 1

    customize_plist()
    sign_and_fix_security()
    create_dmg()

    print(f"""
{'='*60}
  Build Complete!
{'='*60}

Output: {DIST_DIR}

Files created:
  - {APP_BUNDLE_NAME} (Application)
  - EPA_Dashboard_v{APP_VERSION}.dmg (Installer)

To distribute:
  1. Share the .dmg file
  2. Users drag the app to Applications
  3. First launch: Right-click > Open to bypass Gatekeeper

To test locally:
  open "{DIST_DIR / APP_BUNDLE_NAME}"

""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
