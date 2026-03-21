# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import site
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

# Base directory (where this .spec file lives)
# SPECPATH is always set by PyInstaller when running a .spec file
try:
    BASE_DIR = os.path.abspath(os.path.dirname(SPECPATH))
except NameError:
    BASE_DIR = os.path.abspath('.')

# Validate BASE_DIR by checking for a known project file.
# GitHub Actions checkout can place the repo one level deeper.
if not os.path.isfile(os.path.join(BASE_DIR, 'main.py')):
    for entry in os.listdir(BASE_DIR):
        candidate = os.path.join(BASE_DIR, entry)
        if os.path.isdir(candidate) and os.path.isfile(os.path.join(candidate, 'main.py')):
            BASE_DIR = candidate
            break

print(f"[SPEC] BASE_DIR = {BASE_DIR}")
print(f"[SPEC] Contents: {os.listdir(BASE_DIR)}")

def rel(path):
    """Resolve a path relative to the project root."""
    return os.path.join(BASE_DIR, path)

# Find site-packages for spaCy models
site_packages = None
try:
    candidates = site.getsitepackages() + [site.getusersitepackages()]
except Exception:
    candidates = []
for sp in candidates:
    if os.path.isdir(sp):
        site_packages = sp
        break
# Fallback: look for a local venv or .venv
if not site_packages or not os.path.isdir(site_packages):
    for venv_name in ['.venv', 'venv']:
        if sys.platform == 'win32':
            venv_sp = os.path.join(BASE_DIR, venv_name, 'Lib', 'site-packages')
        else:
            venv_sp = os.path.join(BASE_DIR, venv_name, 'lib', f'python{sys.version_info.major}.{sys.version_info.minor}', 'site-packages')
        if os.path.isdir(venv_sp):
            site_packages = venv_sp
            break

print(f"[SPEC] site_packages = {site_packages}")

# Find NLTK data (check common locations)
nltk_data_dir = None
_nltk_candidates = [
    os.path.join(str(Path.home()), 'nltk_data'),
    os.path.join(BASE_DIR, 'nltk_data'),
]
if sys.platform == 'win32':
    _appdata = os.getenv('APPDATA', '')
    if _appdata:
        _nltk_candidates.insert(0, os.path.join(_appdata, 'nltk_data'))
else:
    _nltk_candidates += ['/usr/share/nltk_data', '/usr/local/share/nltk_data']
for candidate in _nltk_candidates:
    if os.path.isdir(candidate):
        nltk_data_dir = candidate
        break

datas = [
    (rel('assets'), 'assets'),
    (rel('config'), 'config'),
    (rel('qt_views'), 'qt_views'),
    (rel('services'), 'services'),
    (rel('app'), 'app'),
    (rel('secret.txt'), '.'),
]

# Add spaCy models if found
if site_packages:
    en_model = os.path.join(site_packages, 'en_core_web_sm')
    es_model = os.path.join(site_packages, 'es_core_news_sm')
    if os.path.isdir(en_model):
        datas.append((en_model, 'en_core_web_sm'))
    if os.path.isdir(es_model):
        datas.append((es_model, 'es_core_news_sm'))

# Add NLTK data if found
if nltk_data_dir:
    stopwords = os.path.join(nltk_data_dir, 'corpora', 'stopwords')
    punkt = os.path.join(nltk_data_dir, 'tokenizers', 'punkt')
    if os.path.isdir(stopwords):
        datas.append((stopwords, 'nltk_data/corpora/stopwords'))
    if os.path.isdir(punkt):
        datas.append((punkt, 'nltk_data/tokenizers/punkt'))

binaries = []
hiddenimports = ['PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'PyQt5.sip', 'PyQt5.QtNetwork', 'PyQt5.QtPrintSupport', 'flask', 'flask.json', 'flask.json.provider', 'werkzeug', 'werkzeug.routing', 'werkzeug.utils', 'jinja2', 'markupsafe', 'itsdangerous', 'click', 'sqlalchemy', 'sqlalchemy.ext.declarative', 'sqlalchemy.orm', 'sqlalchemy.engine', 'sqlalchemy.pool', 'spacy', 'spacy.lang', 'spacy.lang.es', 'spacy.lang.en', 'spacy.tokenizer', 'spacy.vocab', 'spacy.pipeline', 'thinc', 'thinc.api', 'thinc.layers', 'thinc.model', 'cymem', 'cymem.cymem', 'preshed', 'preshed.maps', 'murmurhash', 'srsly', 'srsly.msgpack', 'srsly.json', 'wasabi', 'catalogue', 'confection', 'weasel', 'nltk', 'nltk.tokenize', 'nltk.corpus', 'nltk.stem', 'yake', 'rake_nltk', 'keybert', 'keybert.model', 'torch', 'torch.nn', 'torch.optim', 'torch.utils', 'torch.utils.data', 'torch._C', 'torch.cuda', 'torch.backends', 'transformers', 'transformers.models', 'transformers.tokenization_utils', 'transformers.modeling_utils', 'huggingface_hub', 'safetensors', 'sentence_transformers', 'sentence_transformers.models', 'sentence_transformers.util', 'sklearn', 'sklearn.feature_extraction', 'sklearn.metrics', 'sklearn.utils', 'sklearn.preprocessing', 'numpy', 'numpy.core', 'numpy.linalg', 'numpy.fft', 'scipy', 'scipy.sparse', 'scipy.spatial', 'pandas', 'regex', 'filelock', 'packaging', 'tqdm', 'selenium', 'selenium.webdriver', 'selenium.webdriver.chrome', 'selenium.webdriver.chrome.service', 'selenium.webdriver.common', 'webdriver_manager', 'scrapy', 'scrapy.spiders', 'scrapy.http', 'bcrypt', 'bcrypt._bcrypt', 'requests', 'urllib3', 'certifi', 'charset_normalizer', 'idna', 'sqlite3', 'json', 'base64', 'tempfile', 'shutil', 'platform', 'threading', 'queue', 'logging', 'pathlib', 'collections', 'functools', 'itertools', 'typing', 'dataclasses', 'networkx', 'PIL', 'PIL.Image']
tmp_ret = collect_all('spacy')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('thinc')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('torch')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('transformers')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('sentence_transformers')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# Platform-specific icon
icon_path = rel('icon.icns') if sys.platform == 'darwin' else rel('icon.ico')
if not os.path.exists(icon_path):
    icon_path = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='EPA_Dashboard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,  # Auto-detect (was hardcoded to arm64)
    codesign_identity=None,
    entitlements_file=None,
    icon=[icon_path] if icon_path else [],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EPA_Dashboard',
)

# macOS .app bundle (only on macOS)
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='EPA_Dashboard.app',
        icon=icon_path,
        bundle_identifier='com.epai.dashboard',
    )
