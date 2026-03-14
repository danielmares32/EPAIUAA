# 🍎 macOS Installer Build Guide

Complete guide for building EPA Dashboard for macOS.

---

## 📋 Prerequisites

### 1. System Requirements
- **macOS 10.13** or later
- **Python 3.8+** installed
- **Xcode Command Line Tools** (for icon conversion)

### 2. Install Xcode Command Line Tools
```bash
xcode-select --install
```

### 3. Install Python Dependencies
```bash
# Activate your virtual environment (if using one)
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Install PyInstaller
pip install pyinstaller
```

### 4. Verify spaCy Models
```bash
# Check if Spanish model is installed
python -m spacy download es_core_news_sm

# Check if English model is installed
python -m spacy download en_core_web_sm
```

---

## 🚀 Quick Start

### Build Everything (Recommended)
```bash
python build_mac.py
```

This single command will:
1. ✅ Create icon in .icns format
2. ✅ Build .app bundle
3. ✅ Bundle all assets and data
4. ✅ Include spaCy NLP models
5. ✅ Create .dmg installer
6. ✅ Generate installation instructions

---

## 📦 Build Output

After running `build_mac.py`, you'll find:

```
dist/
├── EPA_Dashboard.app/              # macOS application bundle
│   ├── Contents/
│   │   ├── MacOS/
│   │   │   └── EPA_Dashboard      # Executable
│   │   ├── Resources/             # Icons and resources
│   │   ├── Frameworks/            # Bundled libraries
│   │   └── Info.plist            # App metadata
│
├── EPA_Dashboard_v1.0.0.dmg       # Installer (drag & drop)
└── install.sh                      # Command-line installer
```

### File Sizes (Approximate)
- **.app bundle**: 300-500 MB
- **.dmg installer**: 250-400 MB (compressed)

Large size due to:
- PyQt5 (~100MB)
- spaCy models (~100MB)
- PyTorch/Transformers (~200MB)

---

## 🎨 Icon Setup

The build script automatically converts your PNG logo to macOS .icns format.

### Required Icon
- Source: `assets/logo.png`
- Minimum resolution: 512x512 pixels
- Format: PNG with transparency

### Icon Conversion Process
The script creates these sizes automatically:
- 16x16, 32x32 (for Finder)
- 64x64, 128x128 (for various views)
- 256x256, 512x512 (for Retina displays)
- @2x versions for Retina

If icon conversion fails, the app will still build without a custom icon.

---

## 🔧 Advanced Build Options

### Option 1: Build .app Only (No DMG)
```bash
# Edit build_mac.py and comment out:
# create_dmg_installer()

python build_mac.py
```

### Option 2: Build with Console (for Debugging)
Edit `build_mac.py` line ~180:
```python
# Change from:
"--windowed",  # Create .app bundle (no terminal)

# To:
# "--windowed",  # Commented out = console mode
```

Then build:
```bash
python build_mac.py
```

### Option 3: Universal Binary (Intel + Apple Silicon)
Already enabled by default:
```python
"--target-arch", "universal2",  # Support both architectures
```

### Option 4: Custom App Metadata
Edit `build_mac.py` configuration section:
```python
APP_NAME = "EPA Dashboard"           # Display name
APP_VERSION = "1.0.0"                # Version number
APP_IDENTIFIER = "com.epai.dashboard"  # Bundle identifier
```

---

## 📝 App Bundle Structure

Understanding the .app structure:

```
EPA_Dashboard.app/
├── Contents/
│   ├── Info.plist                 # App metadata
│   ├── MacOS/
│   │   └── EPA_Dashboard          # Main executable
│   ├── Resources/
│   │   ├── icon.icns              # App icon
│   │   ├── assets/                # Images, resources
│   │   ├── es_core_news_sm/       # Spanish NLP model
│   │   └── en_core_web_sm/        # English NLP model
│   └── Frameworks/
│       ├── Python.framework        # Python runtime
│       ├── PyQt5/                  # GUI framework
│       └── [other libraries]
```

### Info.plist Configuration
Automatically configured with:
```xml
<key>CFBundleName</key>
<string>EPA Dashboard</string>

<key>CFBundleVersion</key>
<string>1.0.0</string>

<key>CFBundleIdentifier</key>
<string>com.epai.dashboard</string>

<key>NSHighResolutionCapable</key>
<true/>  <!-- Retina display support -->

<key>LSMinimumSystemVersion</key>
<string>10.13.0</string>  <!-- macOS High Sierra -->
```

---

## 🔐 Code Signing & Notarization

### Why Sign Your App?
Without code signing:
- ❌ "App is damaged and can't be opened" warning
- ❌ macOS Gatekeeper blocks the app
- ✅ Users must manually allow in System Preferences

### Getting a Developer ID
1. Enroll in **Apple Developer Program** ($99/year)
2. Create **Developer ID Application** certificate
3. Download and install certificate in Keychain

### How to Sign

#### Step 1: Find Your Signing Identity
```bash
security find-identity -v -p codesigning
```

Output example:
```
1) ABC123... "Developer ID Application: Your Name (TEAM123)"
```

#### Step 2: Update build_mac.py
Uncomment and edit the signing section (~line 385):
```python
signing_identity = "Developer ID Application: Your Name (TEAM123)"
subprocess.run([
    "codesign", "--force", "--deep", "--sign",
    signing_identity,
    str(app_bundle)
], check=True)
```

#### Step 3: Build with Signing
```bash
python build_mac.py
```

### Notarization (Optional but Recommended)

Notarization removes the security warning completely.

```bash
# After building and signing
xcrun notarytool submit EPA_Dashboard_v1.0.0.dmg \
    --apple-id "your@email.com" \
    --team-id "TEAM123" \
    --password "app-specific-password"

# Wait for approval (5-30 minutes)

# Staple the notarization ticket
xcrun stapler staple EPA_Dashboard_v1.0.0.dmg
```

**Note**: Requires Apple Developer account and app-specific password.

---

## 📀 Creating the DMG Installer

The DMG provides a professional installation experience.

### What's Inside the DMG
```
EPA_Dashboard_v1.0.0.dmg (mounted view)
├── EPA_Dashboard.app        # Your application
├── Applications →           # Symlink to /Applications
└── README.txt              # Installation instructions
```

### Users Install By:
1. Double-click the .dmg
2. Drag "EPA Dashboard.app" to Applications folder
3. Eject the DMG
4. Launch from Applications

### Customizing DMG Appearance
For a custom background image and window layout, use tools like:
- **create-dmg**: `brew install create-dmg`
- **DMG Canvas** (paid app)
- **DropDMG** (paid app)

Example with create-dmg:
```bash
create-dmg \
  --volname "EPA Dashboard" \
  --volicon "icon.icns" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "EPA_Dashboard.app" 150 200 \
  --hide-extension "EPA_Dashboard.app" \
  --app-drop-link 450 200 \
  "EPA_Dashboard_v1.0.0.dmg" \
  "dist/"
```

---

## 🧪 Testing Your Build

### Test Checklist

#### 1. Basic Functionality Test
```bash
# Open the .app directly
open dist/EPA_Dashboard.app

# Check:
- [ ] App launches without errors
- [ ] Window appears correctly
- [ ] Logo/images display
- [ ] Login works
```

#### 2. Clean Machine Test
**CRITICAL**: Test on a Mac without Python installed

```bash
# On a test Mac:
1. Download ONLY the .dmg file
2. Install the app
3. Launch and verify all features work
```

#### 3. Architecture Test
```bash
# Check if universal binary
file dist/EPA_Dashboard.app/Contents/MacOS/EPA_Dashboard

# Should show:
# Mach-O universal binary with 2 architectures:
# - x86_64 (Intel)
# - arm64 (Apple Silicon)
```

#### 4. Permissions Test
```bash
# Test Chrome integration
# Verify app can access:
- [ ] Chrome profiles
- [ ] Chrome history database
- [ ] Chrome preferences
```

#### 5. Full Feature Test
- [ ] User registration/login
- [ ] PLE loading and display
- [ ] Chrome profile detection
- [ ] Keyword extraction (all 4 methods)
- [ ] Settings persistence
- [ ] API synchronization

---

## 🐛 Troubleshooting

### Issue: "App is damaged and can't be opened"

**Cause**: macOS Gatekeeper blocking unsigned app

**Solution 1** (For testing):
```bash
# Remove quarantine attribute
xattr -cr dist/EPA_Dashboard.app
```

**Solution 2** (User instruction):
1. Right-click the app
2. Select "Open"
3. Click "Open" in the dialog

**Solution 3** (Permanent):
- Code sign and notarize the app

---

### Issue: Icon not showing

**Check if icon.icns was created:**
```bash
ls -la icon.icns
```

**Manually create icon:**
```bash
# Create iconset directory
mkdir icon.iconset

# Use sips to create all sizes
for size in 16 32 64 128 256 512; do
    sips -z $size $size assets/logo.png \
        --out icon.iconset/icon_${size}x${size}.png
done

# Convert to icns
iconutil -c icns icon.iconset -o icon.icns
```

**Rebuild with icon:**
```bash
python build_mac.py
```

---

### Issue: spaCy models not found

**Verify models are bundled:**
```bash
# Check .app contents
ls dist/EPA_Dashboard.app/Contents/Resources/es_core_news_sm
ls dist/EPA_Dashboard.app/Contents/Resources/en_core_web_sm
```

**If missing, reinstall models:**
```bash
python -m spacy download es_core_news_sm
python -m spacy download en_core_web_sm

# Rebuild
python build_mac.py
```

---

### Issue: "Python not found" error

**Cause**: PyInstaller didn't bundle Python correctly

**Solution**: Rebuild with verbose output
```bash
# Edit build_mac.py, add to PyInstaller command:
"--debug", "all",

python build_mac.py
```

Check logs in `build/EPA_Dashboard/` for errors.

---

### Issue: Images not loading in bundled app

**Ensure resource_path() is used:**
```python
# Check main.py has:
from resource_path import resource_path

# All image paths should use:
icon_file = resource_path("assets/logo.png")
```

**Test in development first:**
```bash
python main.py  # Should work without .app
```

---

### Issue: App crashes on launch

**Enable console mode for debugging:**
```python
# In build_mac.py, comment out:
# "--windowed",

# Rebuild
python build_mac.py

# Run from terminal to see errors
./dist/EPA_Dashboard.app/Contents/MacOS/EPA_Dashboard
```

**Common causes:**
1. Missing hidden import
2. Missing data file
3. Incorrect resource path
4. Database permissions

---

### Issue: Large .app size

**Current size**: ~300-500 MB

**To reduce:**

1. **Exclude unused models:**
```python
# In build_mac.py, remove:
# sentence_transformers
# torch (if not using PyTorch)
```

2. **Use --onedir instead of --onefile:**
```python
# Replace:
"--onefile",
# With:
"--onedir",
```
Results in faster startup but multiple files.

3. **Exclude development files:**
```python
excludes = [
    "matplotlib",
    "IPython",
    "notebook",
]

for module in excludes:
    cmd.extend(["--exclude-module", module])
```

---

## 📊 Comparison: Windows vs macOS Build

| Feature | Windows (.exe) | macOS (.app) |
|---------|---------------|--------------|
| **Format** | Single .exe file | .app bundle (directory) |
| **Size** | 200-400 MB | 300-500 MB |
| **Installer** | .exe or setup.exe | .dmg or .pkg |
| **Signing** | Optional (Authenticode) | Recommended (Developer ID) |
| **Notarization** | N/A | Recommended |
| **Architecture** | x64 or x86 | Universal (Intel + ARM) |
| **Distribution** | Direct download | App Store or DMG |

---

## 📤 Distribution Methods

### 1. Direct Download (Easiest)
```
Upload to your server:
- EPA_Dashboard_v1.0.0.dmg (for Mac users)
- EPA_Dashboard.exe (for Windows users)
```

### 2. GitHub Releases
```bash
# Tag your release
git tag v1.0.0
git push origin v1.0.0

# Upload files to GitHub Releases:
- EPA_Dashboard_v1.0.0.dmg
- EPA_Dashboard_v1.0.0_Windows.exe
- Source code (automatic)
```

### 3. Mac App Store (Advanced)
Requires:
- Apple Developer Program membership
- Mac App Store compatible build
- App Store review process
- Sandbox requirements

### 4. Self-Hosted Update Server
Use frameworks like:
- **Sparkle** (macOS) - Automatic updates
- **Squirrel** (Windows) - Automatic updates

---

## ✅ Pre-Distribution Checklist

Before distributing your macOS app:

- [ ] Tested on macOS 10.13 - 14.x
- [ ] Tested on Intel Mac
- [ ] Tested on Apple Silicon Mac (M1/M2/M3)
- [ ] All images load correctly
- [ ] Chrome integration works
- [ ] NLP/keyword extraction works
- [ ] Database operations work
- [ ] API synchronization works
- [ ] App launches on clean Mac (no Python)
- [ ] Icon displays correctly
- [ ] Version number is correct in Info.plist
- [ ] README.txt is included
- [ ] Code signed (if possible)
- [ ] Notarized (if possible)
- [ ] DMG tested on multiple Macs
- [ ] Installation instructions verified

---

## 🎯 Next Steps

1. **Build the macOS app:**
   ```bash
   python build_mac.py
   ```

2. **Test thoroughly:**
   - Test on your Mac first
   - Test on a clean Mac without Python
   - Test on both Intel and Apple Silicon

3. **Optional improvements:**
   - Get Apple Developer ID for signing
   - Notarize for seamless installation
   - Create custom DMG background

4. **Distribute:**
   - Upload to your website
   - Create GitHub release
   - Share with users

---

## 📞 Support & Resources

### Official Documentation
- **PyInstaller**: https://pyinstaller.org
- **Apple Developer**: https://developer.apple.com
- **Code Signing Guide**: https://developer.apple.com/support/code-signing/

### Common Issues
- PyInstaller + macOS: https://github.com/pyinstaller/pyinstaller/wiki/FAQ
- Qt on macOS: https://doc.qt.io/qt-5/macos.html

### Getting Help
If you encounter issues:
1. Check the console output with `--debug all`
2. Review build logs in `build/` directory
3. Search PyInstaller GitHub issues
4. Contact development team

---

**Created**: 2025-10-19
**Script**: `build_mac.py`
**Python**: 3.12+
**macOS**: 10.13+
**PyInstaller**: 6.0+

🎉 **Happy building!**
