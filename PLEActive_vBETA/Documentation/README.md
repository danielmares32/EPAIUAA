# EPA Dashboard - Documentation Index

This folder contains archived and current documentation for building and distributing the EPA Dashboard application.

## Current Documentation (Root Folder)

### Essential Files
- **`README.md`** - Main project documentation and overview
- **`BUILD_FIXES_SUMMARY.md`** - Complete guide to all build fixes and configuration (MOST IMPORTANT)

## Archived Documentation (archive/)

The following files have been archived as they contain older/duplicate information now consolidated in `BUILD_FIXES_SUMMARY.md`:

- `BUILD_COMPLETE.md` - Old macOS build completion report
- `BUILD_INSTRUCTIONS.md` - Old general build guide
- `BUILD_SUMMARY.md` - Old build overview
- `CLEANUP_LOG.md` - Project cleanup history
- `EXE_BUILD_FIXES.md` - Old Windows build fixes (now in BUILD_FIXES_SUMMARY.md)
- `MAC_BUILD_INSTRUCTIONS.md` - Old macOS guide (now in BUILD_FIXES_SUMMARY.md)
- `QUICK_START_MAC.md` - Old quick start (now in BUILD_FIXES_SUMMARY.md)
- `TROUBLESHOOTING_MAC.md` - Old troubleshooting (now in BUILD_FIXES_SUMMARY.md)

## Build Scripts (Root Folder)

### Active Scripts
- **`build_mac.py`** - macOS .app and .dmg builder (CURRENT)
- **`build_exe_fixed.py`** - Windows .exe builder (CURRENT)
- **`EPA_Dashboard.spec`** - PyInstaller spec file for macOS

### Removed Scripts
The following unused scripts have been removed:
- ~~`build_exe.py`~~ - Old Windows builder (superseded by build_exe_fixed.py)
- ~~`setup.sh`~~ - Old setup script (not needed)
- ~~`setup.bat`~~ - Old setup script (not needed)
- ~~`build_exe.bat`~~ - Old build script (not needed)

## Quick Reference

### Build on macOS
```bash
source venv/bin/activate
python build_mac.py
# OR
pyinstaller --clean --noconfirm EPA_Dashboard.spec
```

### Build on Windows
```bash
venv\Scripts\activate
python build_exe_fixed.py
```

### For Complete Build Instructions
See: **`BUILD_FIXES_SUMMARY.md`** in the root folder

---

Last Updated: October 19, 2025
