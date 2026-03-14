#!/usr/bin/env python3
"""
macOS Application Builder for EPA Dashboard
Creates a .app bundle and optionally a .dmg installer
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import plistlib

# Configuration
APP_NAME = "EPA Dashboard"
APP_BUNDLE_NAME = "EPA_Dashboard.app"
APP_VERSION = "1.0.0"
APP_IDENTIFIER = "com.epai.dashboard"
MAIN_SCRIPT = "main.py"
ICON_FILE = "assets/logo.png"  # Will be converted to .icns

# Directories
PROJECT_ROOT = Path(__file__).parent
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
DMG_DIR = PROJECT_ROOT / "dmg_temp"

def check_requirements():
    """Check if required tools are installed"""
    print("\n🔍 Checking requirements...")

    # Check PyInstaller
    try:
        import PyInstaller
        print("✓ PyInstaller is installed")
    except ImportError:
        print("✗ PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller installed")

    # Check if we're on macOS
    if sys.platform != "darwin":
        print("⚠️  Warning: This script is designed for macOS")
        print("   You're running on:", sys.platform)
        response = input("   Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return False

    return True

def clean_build_folders():
    """Remove old build and dist folders"""
    print("\n📁 Cleaning old build folders...")
    for folder in [BUILD_DIR, DIST_DIR, DMG_DIR]:
        if folder.exists():
            shutil.rmtree(folder)
            print(f"   Removed: {folder}")

def convert_icon_to_icns():
    """Convert PNG icon to macOS .icns format"""
    print("\n🎨 Preparing application icon...")

    icon_png = PROJECT_ROOT / ICON_FILE
    if not icon_png.exists():
        print(f"   ⚠️  Icon not found: {icon_png}")
        return None

    # Create iconset directory
    iconset_dir = PROJECT_ROOT / "icon.iconset"
    iconset_dir.mkdir(exist_ok=True)

    # Required icon sizes for macOS
    sizes = [16, 32, 64, 128, 256, 512]

    try:
        # Use sips (macOS built-in tool) to resize
        for size in sizes:
            output_file = iconset_dir / f"icon_{size}x{size}.png"
            subprocess.run([
                "sips", "-z", str(size), str(size),
                str(icon_png), "--out", str(output_file)
            ], check=True, capture_output=True)

            # Also create @2x versions
            if size <= 256:
                output_file_2x = iconset_dir / f"icon_{size}x{size}@2x.png"
                subprocess.run([
                    "sips", "-z", str(size * 2), str(size * 2),
                    str(icon_png), "--out", str(output_file_2x)
                ], check=True, capture_output=True)

        # Convert iconset to icns
        icns_file = PROJECT_ROOT / "icon.icns"
        subprocess.run([
            "iconutil", "-c", "icns",
            str(iconset_dir), "-o", str(icns_file)
        ], check=True, capture_output=True)

        # Cleanup iconset directory
        shutil.rmtree(iconset_dir)

        print(f"   ✓ Icon created: {icns_file}")
        return icns_file

    except subprocess.CalledProcessError as e:
        print(f"   ⚠️  Icon conversion failed: {e}")
        return None
    except FileNotFoundError:
        print("   ⚠️  sips or iconutil not found (required on macOS)")
        return None

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

def build_app_bundle():
    """Build the macOS .app bundle using PyInstaller"""
    print("\n🔨 Building macOS application bundle...")

    # Convert icon
    icns_file = convert_icon_to_icns()
    
    # Create runtime hook
    runtime_hook = create_runtime_hook()

    # Base PyInstaller command for macOS
    cmd = [
        "pyinstaller",
        "--name", APP_NAME.replace(" ", "_"),
        "--windowed",  # Create .app bundle (no terminal)
        "--onedir",    # Directory mode (better for large apps with many dependencies)
        "--clean",
        "--noconfirm",
    ]

    # Add icon if created
    if icns_file and icns_file.exists():
        cmd.extend(["--icon", str(icns_file)])
    
    # Add runtime hook
    if runtime_hook and runtime_hook.exists():
        cmd.extend(["--runtime-hook", str(runtime_hook)])

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
            cmd.extend(["--add-data", f"{src}:{dst}"])
            print(f"   ✓ {src} -> {dst}")

    # Add spaCy models - CRITICAL FIX for NLP functionality
    print("\n📦 Including spaCy models:")
    spacy_models = get_spacy_data_paths()
    for src, dst in spacy_models:
        cmd.extend(["--add-data", f"{src}:{dst}"])
        print(f"   ✓ {dst}")

    # Add YAKE stopwords - CRITICAL FIX for YAKE keyword extraction
    print("\n📦 Including YAKE stopwords:")
    yake_data = get_yake_stopwords_path()
    if yake_data:
        src, dst = yake_data
        cmd.extend(["--add-data", f"{src}:{dst}"])
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

        # NLP
        "rake_nltk",
        "keybert",
        "yake",
        "spacy",
        "spacy.lang.es",
        "spacy.lang.en",

        # Standard
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

        # ML
        "sentence_transformers",
        "torch",
        "numpy",

        # Selenium
        "selenium",
        "selenium.webdriver",
        "selenium.webdriver.chrome",
        "scrapy",
    ]

    print("\n📦 Adding hidden imports:")
    for module in hidden_imports:
        cmd.extend(["--hidden-import", module])
        print(f"   ✓ {module}")

    # macOS specific options
    cmd.extend([
        "--osx-bundle-identifier", APP_IDENTIFIER,
    ])

    # Detect architecture and set target
    import platform
    machine = platform.machine()

    if machine == "arm64":
        # Apple Silicon - check if Python is universal or ARM-only
        try:
            import subprocess
            result = subprocess.run(
                ["file", sys.executable],
                capture_output=True,
                text=True
            )
            if "universal" in result.stdout.lower() or "x86_64" in result.stdout:
                # Universal Python - can build universal
                cmd.extend(["--target-arch", "universal2"])
                print("   ℹ️  Building universal binary (Intel + ARM)")
            else:
                # ARM-only Python (like Miniforge) - build ARM only
                cmd.extend(["--target-arch", "arm64"])
                print("   ℹ️  Building ARM-only binary (Apple Silicon)")
                print("   ⚠️  This will NOT run on Intel Macs")
        except:
            # Fallback to ARM only
            cmd.extend(["--target-arch", "arm64"])
            print("   ℹ️  Building ARM-only binary (Apple Silicon)")
    else:
        # Intel Mac - build Intel only
        cmd.extend(["--target-arch", "x86_64"])
        print("   ℹ️  Building Intel-only binary")

    # Add main script
    cmd.append(MAIN_SCRIPT)

    # Run PyInstaller
    print(f"\n🔧 Running PyInstaller...\n")
    try:
        subprocess.check_call(cmd)
        print("\n✓ .app bundle created successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed: {e}")
        return False

def customize_app_info():
    """Customize the Info.plist file in the .app bundle"""
    print("\n📝 Customizing application info...")

    app_bundle = DIST_DIR / APP_BUNDLE_NAME
    info_plist = app_bundle / "Contents" / "Info.plist"

    if not info_plist.exists():
        print(f"   ⚠️  Info.plist not found at {info_plist}")
        return

    try:
        # Read existing plist
        with open(info_plist, 'rb') as f:
            plist_data = plistlib.load(f)

        # Update with custom info
        plist_data.update({
            'CFBundleDisplayName': APP_NAME,
            'CFBundleName': APP_NAME,
            'CFBundleVersion': APP_VERSION,
            'CFBundleShortVersionString': APP_VERSION,
            'CFBundleIdentifier': APP_IDENTIFIER,
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '10.13.0',  # macOS High Sierra
            'NSHumanReadableCopyright': '© 2025 EPAI Project',
            'CFBundleDocumentTypes': [],
            'NSRequiresAquaSystemAppearance': False,  # Support dark mode
        })

        # Write back
        with open(info_plist, 'wb') as f:
            plistlib.dump(plist_data, f)

        print(f"   ✓ Info.plist updated")

    except Exception as e:
        print(f"   ⚠️  Failed to update Info.plist: {e}")

def create_dmg_installer():
    """Create a .dmg installer for distribution"""
    print("\n📀 Creating DMG installer...")

    app_bundle = DIST_DIR / APP_BUNDLE_NAME
    if not app_bundle.exists():
        print(f"   ✗ .app bundle not found: {app_bundle}")
        return False

    # Create temporary DMG directory
    DMG_DIR.mkdir(exist_ok=True)

    # Copy .app to DMG directory
    dmg_app = DMG_DIR / APP_BUNDLE_NAME
    if dmg_app.exists():
        shutil.rmtree(dmg_app)
    shutil.copytree(app_bundle, dmg_app, symlinks=True)
    print(f"   ✓ Copied .app to DMG folder")

    # Create symbolic link to Applications folder
    applications_link = DMG_DIR / "Applications"
    if applications_link.exists():
        applications_link.unlink()
    applications_link.symlink_to("/Applications")
    print(f"   ✓ Created Applications symlink")

    # Create README
    readme_file = DMG_DIR / "README.txt"
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(f"""
{APP_NAME} - macOS Installer
{'=' * 50}

Installation Instructions:
--------------------------
1. Drag "{APP_NAME}.app" to the Applications folder
2. Open Applications and double-click "{APP_NAME}"
3. If macOS asks about opening an app from the internet,
   go to System Preferences > Security & Privacy and click "Open Anyway"

System Requirements:
--------------------
- macOS 10.13 (High Sierra) or later
- 500 MB available disk space
- Chrome browser (for Chrome integration features)

First Launch:
-------------
On first launch, macOS may show a security warning.
This is normal for applications downloaded from the internet.

To allow the app to run:
1. Open System Preferences
2. Go to Security & Privacy
3. Click "Open Anyway" next to "{APP_NAME}"

Features:
---------
- Personal Learning Environment (PLE) Management
- Chrome History Integration
- Intelligent Keyword Extraction (NLP)
- Course Recommendations
- Multi-profile Support

Support:
--------
For issues or questions, please contact:
- Project website: https://epai.grisenergia.pt
- Email: support@epai.grisenergia.pt

Version: {APP_VERSION}
Build Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}

© 2025 EPAI Project. All rights reserved.
""")
    print(f"   ✓ Created README.txt")

    # Create DMG
    dmg_name = f"{APP_NAME.replace(' ', '_')}_v{APP_VERSION}.dmg"
    dmg_path = DIST_DIR / dmg_name

    # Remove old DMG if exists
    if dmg_path.exists():
        dmg_path.unlink()

    print(f"\n   Creating {dmg_name}...")
    try:
        # Use hdiutil to create DMG
        subprocess.run([
            "hdiutil", "create",
            "-volname", APP_NAME,
            "-srcfolder", str(DMG_DIR),
            "-ov",
            "-format", "UDZO",  # Compressed
            str(dmg_path)
        ], check=True, capture_output=True)

        print(f"   ✓ DMG created: {dmg_path}")

        # Cleanup temp directory
        shutil.rmtree(DMG_DIR)

        return True

    except subprocess.CalledProcessError as e:
        print(f"   ✗ DMG creation failed: {e}")
        return False
    except FileNotFoundError:
        print("   ✗ hdiutil not found (required on macOS)")
        return False

def sign_app(app_bundle):
    """Code sign the application (optional, requires Apple Developer ID)"""
    print("\n🔐 Code signing...")

    # Check if signing identity exists
    try:
        result = subprocess.run([
            "security", "find-identity", "-v", "-p", "codesigning"
        ], capture_output=True, text=True)

        if "0 valid identities found" in result.stdout:
            print("   ⚠️  No code signing identity found")
            print("   → App will not be signed (users will see security warning)")
            return False

        # If you have a Developer ID, uncomment and customize:
        # signing_identity = "Developer ID Application: Your Name (TEAM_ID)"
        # subprocess.run([
        #     "codesign", "--force", "--deep", "--sign",
        #     signing_identity,
        #     str(app_bundle)
        # ], check=True)
        # print(f"   ✓ App signed with: {signing_identity}")

        print("   ⚠️  Skipping code signing (no identity configured)")
        return False

    except Exception as e:
        print(f"   ⚠️  Code signing skipped: {e}")
        return False

def notarize_app(dmg_path):
    """Notarize the app with Apple (optional, requires Apple Developer account)"""
    print("\n📮 Notarization...")
    print("   ⚠️  Notarization skipped (requires Apple Developer account)")
    print("   → Users will need to manually allow the app in System Preferences")
    return False

def create_installer_script():
    """Create a simple installer script"""
    installer_script = DIST_DIR / "install.sh"

    with open(installer_script, 'w', encoding='utf-8') as f:
        f.write(f"""#!/bin/bash
# EPA Dashboard Installer for macOS

APP_NAME="{APP_BUNDLE_NAME}"
INSTALL_DIR="/Applications"

echo "======================================"
echo "  {APP_NAME} Installer"
echo "======================================"
echo ""

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then
    echo "ℹ️  Installing to /Applications requires admin privileges"
    echo "   Please enter your password when prompted"
    echo ""
fi

# Copy app to Applications
if [ -d "$APP_NAME" ]; then
    echo "📦 Installing $APP_NAME..."
    sudo cp -R "$APP_NAME" "$INSTALL_DIR/"

    if [ $? -eq 0 ]; then
        echo "✅ Installation successful!"
        echo ""
        echo "You can now find {APP_NAME} in your Applications folder"
        echo ""
        echo "To launch: open '$INSTALL_DIR/$APP_NAME'"
    else
        echo "❌ Installation failed"
        exit 1
    fi
else
    echo "❌ $APP_NAME not found in current directory"
    exit 1
fi
""")

    # Make executable
    installer_script.chmod(0o755)
    print(f"   ✓ Created installer script: {installer_script}")

def main():
    """Main build process"""
    print(f"""
╔════════════════════════════════════════════╗
║   EPA Dashboard - FIXED macOS Builder    ║
╚════════════════════════════════════════════╝

This build script includes fixes for:
✓ Image loading (proper resource bundling)
✓ Chrome functionality (all dependencies)
✓ spaCy models (bundled NLP models)
✓ YAKE stopwords (keyword extraction data)
✓ Database path (AppData folder)
✓ Resource path resolution

This script will create:
✓ .app bundle (macOS application)
✓ .dmg installer (drag-and-drop installer)
✓ README and installation instructions
""")

    # Check requirements
    if not check_requirements():
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

    # Build .app bundle
    if not build_app_bundle():
        return 1

    # Customize app info
    customize_app_info()

    # Optional: Sign the app
    app_bundle = DIST_DIR / APP_BUNDLE_NAME
    sign_app(app_bundle)

    # Create DMG installer
    dmg_created = create_dmg_installer()

    # Create installer script (alternative to DMG)
    create_installer_script()

    print(f"""
╔════════════════════════════════════════════╗
║   Build completed successfully! ✅         ║
╚════════════════════════════════════════════╝

📂 Output location:
   {DIST_DIR}

📝 Files created:
   ✓ {APP_BUNDLE_NAME} (macOS application)
   {'✓ ' + APP_NAME.replace(' ', '_') + '_v' + APP_VERSION + '.dmg (installer)' if dmg_created else '✗ DMG creation failed'}
   ✓ install.sh (command-line installer)

🚀 Distribution Options:

1. DMG Installer (Recommended):
   → Distribute the .dmg file
   → Users drag .app to Applications folder

2. Direct .app:
   → Zip the .app bundle
   → Users unzip and move to Applications

3. Command-line:
   → Run: ./install.sh
   → Requires admin password

⚠️  IMPORTANT NOTES:

1. First Launch Security:
   Users must allow the app in System Preferences > Security & Privacy
   (This happens because the app is not code signed)

2. Images are now bundled - use resource_path() helper:
   from resource_path import resource_path
   icon_path = resource_path("assets/logo.png")

3. spaCy models and YAKE stopwords are included in the .app

4. To avoid security warnings (optional):
   - Get an Apple Developer ID ($99/year)
   - Code sign the app
   - Notarize with Apple

5. Chrome Integration:
   - Requires Chrome browser installed
   - May need permissions for accessing Chrome data

6. Testing:
   - Test on a clean Mac without Python installed
   - Test on both Intel and Apple Silicon Macs

📖 For detailed instructions, see:
   {DIST_DIR}/README.txt

🎉 Ready to distribute your macOS application!
""")

    return 0

if __name__ == "__main__":
    sys.exit(main())
