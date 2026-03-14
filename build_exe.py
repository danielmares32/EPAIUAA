#!/usr/bin/env python3
"""
Build script to generate Windows .exe using PyInstaller
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Configuration
APP_NAME = "EPA_Dashboard"
MAIN_SCRIPT = "main.py"
ICON_FILE = "assets/icon.ico"  # Change if you have a custom icon

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

def build_exe():
    """Build the .exe file"""
    print("\n🔨 Building executable...")

    # Base PyInstaller command
    cmd = [
        "pyinstaller",
        "--name", APP_NAME,
        "--windowed",  # No console window
        "--onefile",   # Single .exe file
        "--clean",     # Clean cache
    ]

    # Add icon if exists
    icon_path = PROJECT_ROOT / ICON_FILE
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
        print(f"   Using icon: {icon_path}")

    # Add data files and folders
    data_includes = [
        ("assets", "assets"),
        ("config", "config"),
        ("qt_views", "qt_views"),
        ("services", "services"),
        ("app", "app"),
    ]

    for src, dst in data_includes:
        src_path = PROJECT_ROOT / src
        if src_path.exists():
            cmd.extend(["--add-data", f"{src}{os.pathsep}{dst}"])
            print(f"   Including: {src}")

    # Hidden imports for PyQt5 and other modules
    hidden_imports = [
        "PyQt5.QtCore",
        "PyQt5.QtGui",
        "PyQt5.QtWidgets",
        "rake_nltk",
        "keybert",
        "yake",
        "spacy",
        "requests",
        "sqlite3",
    ]

    for module in hidden_imports:
        cmd.extend(["--hidden-import", module])

    # Add main script
    cmd.append(MAIN_SCRIPT)

    # Run PyInstaller
    print(f"\n   Command: {' '.join(cmd)}\n")
    try:
        subprocess.check_call(cmd)
        print("\n✓ Build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed with error: {e}")
        return False

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
    print(f"   Copied: {APP_NAME}.exe")

    # Copy config folder if exists
    config_src = PROJECT_ROOT / "config"
    if config_src.exists():
        config_dst = portable_dir / "config"
        if config_dst.exists():
            shutil.rmtree(config_dst)
        shutil.copytree(config_src, config_dst)
        print(f"   Copied: config/")

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
- Windows 7 or later
- No additional software required (all dependencies included)

Notes:
------
- Configuration files are stored in the 'config' folder
- User data is stored in the application directory

For support or issues, please contact the development team.

Build date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")
    print(f"   Created: README.txt")

    print(f"\n✓ Portable package created at: {portable_dir}")
    return True

def main():
    """Main build process"""
    print(f"""
╔═══════════════════════════════════════╗
║   EPA Dashboard - EXE Builder        ║
╚═══════════════════════════════════════╝
""")

    # Check requirements
    if not check_pyinstaller():
        print("✗ Failed to install PyInstaller")
        return 1

    # Check if main script exists
    if not (PROJECT_ROOT / MAIN_SCRIPT).exists():
        print(f"✗ Main script not found: {MAIN_SCRIPT}")
        return 1

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

🚀 You can now distribute the .exe file or the portable folder!
""")
    return 0

if __name__ == "__main__":
    sys.exit(main())
