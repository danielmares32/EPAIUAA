# 🔧 EXE Build Fixes Documentation

## Issues Identified and Fixed

### 1. ❌ **Images Not Loading in EXE**

**Problem:**
- Images referenced with relative paths like `"assets/logo.png"` don't work in PyInstaller executables
- PyInstaller extracts files to a temporary directory (`sys._MEIPASS`) at runtime
- Hardcoded paths break when running from the bundled .exe

**Root Causes:**
1. `main.py:22` - `QIcon("assets/logo.png")` uses relative path
2. PyInstaller doesn't automatically fix resource paths
3. Assets folder not properly bundled in the .exe

**Solutions Applied:**

✅ **Created `resource_path.py` helper module:**
```python
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except Exception:
        base_path = os.path.abspath(".")  # Development mode
    return os.path.join(base_path, relative_path)
```

✅ **Updated `main.py` to use resource_path():**
```python
icon_file = resource_path("assets/logo.png")
if os.path.exists(icon_file):
    qt_app.setWindowIcon(QIcon(icon_file))
```

✅ **Updated `build_exe_fixed.py` to bundle assets:**
```python
data_includes = [
    ("assets", "assets"),  # Properly bundle entire assets folder
    ...
]
```

**Files Modified:**
- ✏️ `main.py` - Added resource_path usage
- 📝 `resource_path.py` - NEW helper module
- 📝 `build_exe_fixed.py` - NEW improved build script

---

### 2. ❌ **Chrome Functionality Not Working**

**Problem:**
- spaCy NLP models not found in bundled executable
- Missing hidden imports for Chrome/Selenium dependencies
- Large ML models not properly packaged

**Root Causes:**
1. spaCy models (`es_core_news_sm`, `en_core_web_sm`) stored in site-packages
2. PyInstaller doesn't auto-detect data files for ML models
3. Missing hidden imports for:
   - `selenium.webdriver.chrome`
   - `spacy.lang.es` and `spacy.lang.en`
   - Transformers, sentence-transformers

**Solutions Applied:**

✅ **Auto-detect and bundle spaCy models:**
```python
def get_spacy_data_paths():
    """Find spaCy model data directories"""
    import site
    spacy_models = []

    for site_dir in site.getsitepackages():
        site_path = Path(site_dir)
        es_model = site_path / "es_core_news_sm"
        if es_model.exists():
            spacy_models.append((str(es_model), "es_core_news_sm"))

        en_model = site_path / "en_core_web_sm"
        if en_model.exists():
            spacy_models.append((str(en_model), "en_core_web_sm"))

    return spacy_models
```

✅ **Expanded hidden imports list:**
```python
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
    "spacy.lang.es",  # ← CRITICAL for Spanish
    "spacy.lang.en",  # ← CRITICAL for English

    # Selenium/Chrome
    "selenium",
    "selenium.webdriver",
    "selenium.webdriver.chrome",  # ← CRITICAL for Chrome integration

    # ML models
    "sentence_transformers",
    "torch",
    "numpy",

    # Web scraping
    "scrapy",
]
```

✅ **Fixed spaCy model loading in `app/chrome/service.py:19-31`:**
The existing fallback mechanism is good, but ensure models are bundled:
```python
try:
    spacy_nlp = spacy.load("es_core_news_sm")
except OSError:
    try:
        spacy_nlp = spacy.load("en_core_web_sm")
    except OSError:
        # Fallback to blank model
        spacy_nlp = spacy.blank("en")
```

**Files Modified:**
- 📝 `build_exe_fixed.py` - Added spaCy model detection and bundling

---

### 3. ⚡ **Additional Improvements**

✅ **Runtime hook for better initialization:**
- Created `pyinstaller_hooks/runtime_hook.py`
- Automatically changes working directory to bundle location
- Adds bundle directory to Python path

✅ **Better error handling:**
- Added existence checks before loading images
- Prints warnings instead of crashing silently

✅ **Portable package creation:**
- Includes config folder
- Comprehensive README.txt for end users
- Clear troubleshooting instructions

---

## 📋 How to Use the Fixed Build

### Step 1: Run the Fixed Build Script

```bash
python build_exe_fixed.py
```

This will:
1. ✅ Auto-detect spaCy models
2. ✅ Bundle all assets and data files
3. ✅ Include all hidden imports
4. ✅ Create runtime hooks
5. ✅ Generate portable package

### Step 2: Test the Executable

On a **clean Windows machine** (without Python installed):

```bash
cd dist
EPA_Dashboard.exe
```

**What to test:**
- [ ] Application launches without errors
- [ ] Logo/images display correctly
- [ ] Chrome profile detection works
- [ ] Keyword extraction (NLP) works
- [ ] All UI elements render properly

### Step 3: Verify Chrome Integration

1. Open the app
2. Navigate to Chrome integration
3. Test:
   - [ ] Profile detection
   - [ ] History extraction
   - [ ] Keyword generation (RAKE, KeyBERT, YAKE, spaCy)

---

## 🔍 Debugging Tips

### If images still don't load:

1. **Check if assets are bundled:**
```bash
# Extract .exe to see bundled files
7z x EPA_Dashboard.exe -o extracted/
ls extracted/assets/
```

2. **Enable console mode for debugging:**
In `build_exe_fixed.py`, change:
```python
"--windowed",  # No console window
```
to:
```python
"--console",  # Show console for debugging
```

3. **Check resource paths at runtime:**
Add to `main.py`:
```python
print(f"Base path: {resource_path('.')}")
print(f"Icon path: {resource_path('assets/logo.png')}")
print(f"Icon exists: {os.path.exists(resource_path('assets/logo.png'))}")
```

### If Chrome functionality doesn't work:

1. **Verify spaCy models are bundled:**
```bash
# Check extracted exe contents
ls extracted/es_core_news_sm/
ls extracted/en_core_web_sm/
```

2. **Test spaCy loading:**
Add to your code:
```python
import spacy
try:
    nlp = spacy.load("es_core_news_sm")
    print("✓ Spanish model loaded")
except:
    print("✗ Spanish model failed")
```

3. **Check Selenium/Chrome drivers:**
- Ensure ChromeDriver is accessible
- Selenium needs Chrome browser installed on target machine

### If .exe is too large:

Current size will be ~200-400MB due to:
- PyQt5 (~100MB)
- spaCy models (~50MB each)
- Transformers/PyTorch (~150MB)

**To reduce size:**
1. Exclude unused models
2. Use `--exclude-module` for unused libraries
3. Consider `--onedir` instead of `--onefile` (faster but multiple files)

---

## 📁 File Structure After Build

```
dist/
├── EPA_Dashboard.exe (200-400MB)
└── EPA_Dashboard_Portable/
    ├── EPA_Dashboard.exe
    ├── config/
    │   └── [config files]
    └── README.txt
```

When the .exe runs, PyInstaller extracts to:
```
C:\Users\USERNAME\AppData\Local\Temp\_MEI123456\
├── assets/
│   ├── logo.png
│   ├── logo_header.png
│   └── ...
├── es_core_news_sm/
│   └── [spaCy Spanish model]
├── en_core_web_sm/
│   └── [spaCy English model]
├── app/
├── qt_views/
├── services/
└── [bundled libraries]
```

---

## 🚀 Next Steps

### Apply resource_path() to ALL image references:

Search for all image/asset loading in your codebase:
```bash
grep -r "assets/" --include="*.py" | grep -v venv
```

Update each occurrence to use `resource_path()`:

**Before:**
```python
logo = QPixmap("assets/logo_header.png")
```

**After:**
```python
from resource_path import resource_path
logo = QPixmap(resource_path("assets/logo_header.png"))
```

### Files that likely need updates:
- `qt_views/login_interface.py` - Logo images
- `qt_views/components/Header.py` - Header logo
- Any other UI components loading images

---

## ✅ Verification Checklist

Before distributing the .exe:

- [ ] Tested on Windows 7 (if supporting)
- [ ] Tested on Windows 10
- [ ] Tested on Windows 11
- [ ] All images load correctly
- [ ] Chrome integration works
- [ ] Keyword extraction works (all 4 methods)
- [ ] Login/authentication works
- [ ] Database operations work
- [ ] API calls work
- [ ] No antivirus false positives
- [ ] Installer/portable package created
- [ ] README included with instructions

---

## 📞 Still Having Issues?

### Common PyInstaller Problems:

1. **"Failed to execute script"**
   - Build with `--console` to see error
   - Check for missing hidden imports

2. **"ModuleNotFoundError"**
   - Add module to `hidden_imports` list
   - Verify module is installed: `pip list`

3. **"FileNotFoundError" for data files**
   - Ensure file is in `--add-data`
   - Use `resource_path()` helper

4. **Antivirus quarantines .exe**
   - Use code signing certificate
   - Submit to antivirus vendors as false positive
   - Build with `--debug` flag temporarily

### Getting Help:

1. Enable console mode
2. Run the .exe and copy full error message
3. Check PyInstaller logs in `build/` folder
4. Search PyInstaller GitHub issues
5. Contact development team with:
   - Full error message
   - Build command used
   - Python version
   - PyInstaller version

---

**Last Updated:** 2025-10-19
**PyInstaller Version:** 6.0+
**Python Version:** 3.12
**Build Script:** `build_exe_fixed.py`
