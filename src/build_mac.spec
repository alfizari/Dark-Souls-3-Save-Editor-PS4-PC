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

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Dark_Souls_3_Save_Editor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    windowed=True,
)

app = BUNDLE(
    exe,
    name='Dark_Souls_3_Save_Editor_App.app',
    icon=None,
    bundle_identifier=None,
)
