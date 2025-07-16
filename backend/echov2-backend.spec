# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from pathlib import Path

# Get the backend directory path
backend_dir = Path('.').absolute()
project_root = backend_dir.parent

# Define paths
main_script = backend_dir / 'main.py'
config_dir = backend_dir / 'config'
api_dir = backend_dir / 'api'
core_dir = backend_dir / 'core'
services_dir = backend_dir / 'services'
utils_dir = backend_dir / 'utils'

# Configuration files to include
config_files = [
    (str(project_root / 'config' / 'development.yaml'), 'config'),
    (str(project_root / 'config' / 'production.yaml'), 'config'),
]

# Analysis configuration
a = Analysis(
    [str(main_script)],
    pathex=[str(backend_dir)],
    binaries=[],
    datas=config_files,
    hiddenimports=[
        # FastAPI and Uvicorn dependencies
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets.websockets_impl',
        'uvicorn.protocols.http.httptools_impl',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.logging',
        
        # FastAPI dependencies
        'fastapi.responses',
        'fastapi.middleware.cors',
        'fastapi.staticfiles',
        
        # Pydantic
        'pydantic.json',
        'pydantic.types',
        'pydantic.validators',
        
        # Backend modules
        'config.settings',
        'api.routes.health',
        'api.routes.chat',
        'api.routes.plugins',
        'core.models.registry',
        'core.models.manager',
        'core.plugins.ollama_provider',
        'core.plugins.openai_provider',
        'core.plugins.anthropic_provider',
        'services.chat_service',
        'services.health_service',
        
        # HTTP clients
        'httpx',
        'requests',
        'aiofiles',
        
        # AI providers
        'openai',
        'anthropic',
        
        # YAML processing
        'yaml',
        'pyyaml',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'pygame',
        'wx',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove unnecessary files
a.binaries = TOC([x for x in a.binaries if not x[0].startswith('lib')])

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='echov2-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for GUI app (no console window)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # macOS specific options
    icon=None,
    bundle_identifier='com.echov2.backend',
)

# For macOS, create app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='echov2-backend.app',
        icon=None,
        bundle_identifier='com.echov2.backend',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'LSBackgroundOnly': 'True',  # Background app, no dock icon
        },
    )