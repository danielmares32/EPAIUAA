# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('/Users/danielmares/Downloads/PLEActive_vBETA 3/PLEActive_vBETA/assets', 'assets'), ('/Users/danielmares/Downloads/PLEActive_vBETA 3/PLEActive_vBETA/config', 'config'), ('/Users/danielmares/Downloads/PLEActive_vBETA 3/PLEActive_vBETA/qt_views', 'qt_views'), ('/Users/danielmares/Downloads/PLEActive_vBETA 3/PLEActive_vBETA/services', 'services'), ('/Users/danielmares/Downloads/PLEActive_vBETA 3/PLEActive_vBETA/app', 'app'), ('/Users/danielmares/Downloads/PLEActive_vBETA 3/PLEActive_vBETA/secret.txt', '.'), ('/Users/danielmares/Downloads/PLEActive_vBETA 3/PLEActive_vBETA/venv/lib/python3.12/site-packages/en_core_web_sm', 'en_core_web_sm'), ('/Users/danielmares/Downloads/PLEActive_vBETA 3/PLEActive_vBETA/venv/lib/python3.12/site-packages/es_core_news_sm', 'es_core_news_sm'), ('/Users/danielmares/Downloads/PLEActive_vBETA 3/PLEActive_vBETA/venv/lib/python3.12/site-packages/yake/core/StopwordsList', 'yake/core/StopwordsList'), ('/Users/danielmares/nltk_data/corpora/stopwords', 'nltk_data/corpora/stopwords'), ('/Users/danielmares/nltk_data/tokenizers/punkt', 'nltk_data/tokenizers/punkt')]
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
    target_arch='arm64',
    codesign_identity=None,
    entitlements_file=None,
    icon=['/Users/danielmares/Downloads/PLEActive_vBETA 3/PLEActive_vBETA/icon.icns'],
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
app = BUNDLE(
    coll,
    name='EPA_Dashboard.app',
    icon='/Users/danielmares/Downloads/PLEActive_vBETA 3/PLEActive_vBETA/icon.icns',
    bundle_identifier='com.epai.dashboard',
)
