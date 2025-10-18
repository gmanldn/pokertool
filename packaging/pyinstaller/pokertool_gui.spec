# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

block_cipher = None

project_root = Path(__file__).resolve().parents[2]

a = Analysis(
    ['standalone/gui_entry.py'],
    pathex=[str(project_root / 'src')],
    binaries=[],
    datas=[(str(project_root / 'assets'), 'assets')],
    hiddenimports=[
        'cv2',
        'numpy',
        'PIL',
        'pytesseract',
        'mss',
        'requests',
        'websocket',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PokerToolGUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PokerToolGUI',
)
