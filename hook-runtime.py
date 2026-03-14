# PyInstaller runtime hook
# This ensures Flask doesn't try to use the reloader in bundled apps

import os
import sys

# Disable Flask reloader
os.environ['WERKZEUG_RUN_MAIN'] = 'true'

# Ensure we're not in debug mode
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = '0'

# Fix for macOS app bundles
if getattr(sys, 'frozen', False):
    # Running in a bundle
    os.environ['PYINSTALLER'] = '1'
