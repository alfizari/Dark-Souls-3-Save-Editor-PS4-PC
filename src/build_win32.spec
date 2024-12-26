# -*- mode: python ; coding: utf-8 -*-
import os
from glob import glob

# Add Debug folder path
debug_folder = os.path.join(os.getcwd(), 'src', 'Resources', 'Debug')

a = Analysis(
    ['Final.py'],
    pathex=[os.getcwd()],
    binaries=[],
    datas=[
        (os.path.join(os.getcwd(), 'src', 'Resources'), 'Resources'),
        # Add Debug folder and its contents
        (debug_folder, os.path.join('Resources', 'Debug')),
        # Include all files from Debug folder
        *[(os.path.join(debug_folder, f), os.path.join('Resources', 'Debug')) 
          for f in os.listdir(debug_folder) if os.path.isfile(os.path.join(debug_folder, f))]
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe_windows = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Dark_Souls_3_Save_Editor_WIN32',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
