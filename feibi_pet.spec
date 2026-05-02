# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

project_root = Path(SPECPATH)
python_root = Path(sys.base_prefix)


def collect_top_level_tree(source_dir, target_dir):
    return [
        (str(Path(target_dir) / path.relative_to(source_dir)), str(path), 'PKG')
        for path in source_dir.rglob('*')
        if path.is_file()
    ]


top_level_files = [
    # COLLECT places DATA entries under contents_directory; PKG keeps these editable files beside the exe.
    ('pet_config.json', str(project_root / 'pet_config.json'), 'PKG'),
    *collect_top_level_tree(project_root / 'assets', 'assets'),
    *collect_top_level_tree(project_root / 'skills', 'skills'),
]

a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=[
        (str(python_root / 'DLLs' / '_tkinter.pyd'), '.'),
        (str(python_root / 'DLLs' / 'tcl86t.dll'), '.'),
        (str(python_root / 'DLLs' / 'tk86t.dll'), '.'),
    ],
    datas=[
        (str(python_root / 'Lib' / 'tkinter'), 'tkinter'),
        (str(python_root / 'tcl' / 'tcl8.6'), 'tcl/tcl8.6'),
        (str(python_root / 'tcl' / 'tk8.6'), 'tcl/tk8.6'),
    ],
    hiddenimports=[
        'feibi_pet',
        'feibi_pet.app',
        'feibi_pet.pet',
        'feibi_pet.config',
        'feibi_pet.audio',
        'feibi_pet.chat_client',
        'feibi_pet.chat_memory',
        'feibi_pet.chat_ui',
        'PIL._tkinter_finder',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(project_root / 'pyi_rth_tkinter_manual.py')],
    excludes=[
        'matplotlib',
        'scipy',
        'pandas',
        'pytest',
        'IPython',
        'jupyter',
    ],
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
    name='FeibiPet',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    exclude_binaries=True,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    contents_directory='_internal',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    top_level_files,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FeibiPet',
)
