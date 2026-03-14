# 🚀 Quick Start - macOS Installer

**Build your macOS .app and .dmg in 2 minutes!**

---

## ⚡ Super Quick Build

```bash
# 1. Make sure you're in the project directory
cd /Users/danielmares/Downloads/EPAIUAAmain-1

# 2. Install PyInstaller (if not already installed)
pip install pyinstaller

# 3. Build everything!
python build_mac.py
```

**That's it!** ✅

Find your files in `dist/`:
- `EPA_Dashboard.app` - macOS application
- `EPA_Dashboard_v1.0.0.dmg` - Installer

---

## 📦 What Gets Created

### The .app Bundle
```
dist/EPA_Dashboard.app
```
- Double-click to run
- Contains everything needed (Python, libraries, assets)
- Size: ~300-500 MB

### The .dmg Installer
```
dist/EPA_Dashboard_v1.0.0.dmg
```
- Drag-and-drop installer
- Professional distribution format
- Size: ~250-400 MB (compressed)

---

## ✅ Testing Your App

### Test on Your Mac
```bash
# Open the app
open dist/EPA_Dashboard.app

# Check if everything works:
# ✓ App launches
# ✓ Images load
# ✓ Login works
# ✓ Chrome integration works
```

### Test on Another Mac (IMPORTANT!)
1. Copy the .dmg to a Mac **without Python installed**
2. Double-click the .dmg
3. Drag app to Applications
4. Launch and test all features

---

## ⚠️ First Launch Warning

Users will see a security warning:

> "EPA Dashboard" cannot be opened because it is from an unidentified developer.

**How to open it:**
1. Right-click the app
2. Click "Open"
3. Click "Open" again in the dialog

**Why?** App is not code-signed. See full docs for signing instructions.

---

## 🐛 Quick Troubleshooting

### Build Failed?
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Reinstall PyInstaller
pip install --upgrade pyinstaller

# Try again
python build_mac.py
```

### Icon Not Showing?
Check if `assets/logo.png` exists and is at least 512x512px.

### spaCy Models Missing?
```bash
# Install Spanish model
python -m spacy download es_core_news_sm

# Install English model
python -m spacy download en_core_web_sm

# Rebuild
python build_mac.py
```

### Images Not Loading?
Make sure `main.py` uses the `resource_path()` helper (already fixed).

---

## 📖 Full Documentation

For detailed instructions, see:
- **MAC_BUILD_INSTRUCTIONS.md** - Complete guide
- **EXE_BUILD_FIXES.md** - Windows build fixes

---

## 🎯 Distribution Checklist

Before sharing your app:

- [ ] Tested on your Mac ✅
- [ ] Tested on Mac without Python ✅
- [ ] Tested on Intel Mac (if applicable)
- [ ] Tested on Apple Silicon Mac (if applicable)
- [ ] All features work ✅
- [ ] Included README with instructions ✅

---

## 🚀 You're Ready!

Your macOS app is built and ready to distribute.

Upload the `.dmg` file to:
- Your website
- GitHub Releases
- Cloud storage (Google Drive, Dropbox, etc.)

**Users download, install, and run!**

---

**Need Help?**
- Full docs: `MAC_BUILD_INSTRUCTIONS.md`
- Windows build: `EXE_BUILD_FIXES.md`
- Issues: Check console with `--debug all` flag

🎉 **Happy distributing!**
