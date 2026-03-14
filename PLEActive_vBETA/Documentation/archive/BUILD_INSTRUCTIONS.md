# 🔨 Building EPA Dashboard Executable

This document explains how to build a Windows executable (.exe) for EPA Dashboard.

## 📋 Prerequisites

1. **Python 3.8 or higher** installed
2. **All project dependencies** installed:
   ```bash
   pip install -r requirements.txt
   ```
3. **PyInstaller** (will be installed automatically if missing)

## 🚀 Quick Start

### Option 1: Using Python Script (Recommended)

```bash
python build_exe.py
```

This will:
- ✅ Check and install PyInstaller if needed
- ✅ Clean old build folders
- ✅ Build the executable
- ✅ Create a portable package
- ✅ Generate a README for users

### Option 2: Using Batch File (Windows Only)

```bash
build_exe.bat
```

Double-click the `build_exe.bat` file or run it from the command prompt.

### Option 3: Using Spec File (Advanced)

For custom builds with more control:

```bash
pyinstaller EPA_Dashboard.spec
```

## 📂 Output Location

After building, you'll find:

```
dist/
├── EPA_Dashboard.exe          # Standalone executable
└── EPA_Dashboard_Portable/    # Portable package
    ├── EPA_Dashboard.exe
    ├── config/                # Configuration files
    └── README.txt             # User instructions
```

## 🎯 Build Options

### Customizing the Build

Edit `build_exe.py` to customize:

```python
# Configuration
APP_NAME = "EPA_Dashboard"      # Change app name
MAIN_SCRIPT = "main.py"         # Main entry point
ICON_FILE = "assets/icon.ico"   # Custom icon
```

### Advanced Options

Edit `EPA_Dashboard.spec` for fine-grained control:

- **Console mode**: Set `console=True` for debugging
- **UPX compression**: Set `upx=False` to disable compression
- **Exclude modules**: Add to `excludes` list to reduce size
- **Hidden imports**: Add modules that aren't auto-detected

## 🐛 Troubleshooting

### Issue: "PyInstaller not found"
**Solution**: Install manually
```bash
pip install pyinstaller
```

### Issue: "Module not found" errors
**Solution**: Add to hidden imports in build script
```python
hidden_imports = [
    "PyQt5.QtCore",
    "your_missing_module",  # Add here
]
```

### Issue: Large .exe file size
**Solution**:
- Use `--onefile` mode (already enabled)
- Enable UPX compression (already enabled)
- Exclude unnecessary modules in spec file

### Issue: Application doesn't start
**Solution**:
1. Build with console mode enabled:
   ```bash
   pyinstaller --console main.py
   ```
2. Check the console for error messages
3. Verify all data files are included

## 📦 Distribution

### Single File Distribution
Simply distribute: `dist/EPA_Dashboard.exe`

### Portable Package Distribution
Zip the entire folder: `dist/EPA_Dashboard_Portable/`

Users can extract and run without installation.

## 🔍 Testing the Executable

Before distribution:

1. **Test on clean Windows VM** without Python installed
2. **Verify all features** work correctly
3. **Check antivirus** doesn't flag it (false positives are common)
4. **Test different Windows versions** (7, 10, 11)

## 📊 Build Sizes

Typical sizes:
- **One-file executable**: ~150-250 MB
- **One-folder**: ~100-150 MB (faster startup)

Size depends on:
- Python version
- Number of dependencies
- ML models included (spacy, NLTK, etc.)

## 🔐 Code Signing (Optional)

For production releases:

1. Get a code signing certificate
2. Sign the .exe:
   ```bash
   signtool sign /f certificate.pfx /p password EPA_Dashboard.exe
   ```

This prevents Windows SmartScreen warnings.

## 💡 Tips

1. **Clean builds**: Always clean before building
   ```bash
   rmdir /s build dist
   ```

2. **Test in virtual environment**: Ensures clean dependencies
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   python build_exe.py
   ```

3. **Reduce size**: Use `--onefile` but consider startup time trade-off

4. **Faster builds**: Use spec file with cached options

## 📞 Support

If you encounter issues:

1. Check the error messages carefully
2. Review PyInstaller documentation: https://pyinstaller.org
3. Search for similar issues on GitHub
4. Contact the development team

---

**Last Updated**: 2025-10-15
**PyInstaller Version**: 6.0+
**Python Version**: 3.8+
