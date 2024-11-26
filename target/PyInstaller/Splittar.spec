# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['E:\\David\\Documents\\CODE\\split_tar_gui\\src\\main\\python\\main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=['C:\\Users\\david\\anaconda3\\envs\\splitar_pyqt\\Lib\\site-packages\\fbs\\freeze\\hooks'],
    hooksconfig={},
    runtime_hooks=['E:\\David\\Documents\\CODE\\split_tar_gui\\target\\PyInstaller\\fbs_pyinstaller_hook.py'],
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
    name='Splittar',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='E:\\David\\Documents\\CODE\\split_tar_gui\\target\\PyInstaller\\version_info.py',
    icon=['E:\\David\\Documents\\CODE\\split_tar_gui\\src\\main\\icons\\Icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Splittar',
)
