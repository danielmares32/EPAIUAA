# PyInstaller runtime hook for resource path handling
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
