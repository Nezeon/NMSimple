# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('resources', 'resources'),
    ],
    hiddenimports=[
        # PySide6 modules
        'PySide6.QtCore',
        'PySide6.QtWidgets',
        'PySide6.QtGui',
        'PySide6.QtNetwork',
        
        # SNMP modules
        'pysnmp.hlapi',
        'pysnmp.hlapi.asyncio',
        'pysnmp.carrier.asyncio.dispatch',
        'pysnmp.proto.rfc1902',
        'pysnmp.smi.rfc1902',
        
        # Network and SSH
        'paramiko',
        'paramiko.client',
        'paramiko.ssh_exception',
        
        # Async and threading
        'asyncio',
        'threading',
        'concurrent.futures',
        
        # Scheduler
        'apscheduler',
        'apscheduler.schedulers.background',
        'apscheduler.triggers.interval',
        'apscheduler.triggers.cron',
        
        # Database and standard library
        'sqlite3',
        'platform',
        'subprocess',
        'json',
        'datetime',
        'collections',
        'typing',
        'logging',
        'os',
        'sys',
        'random',
        'math',
        'time',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'PyQt5',
        'PyQt6',
        'unittest',
        'pydoc',
        'doctest',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NMSimple',
    debug=False,      # Changed back to False
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,    # Changed back to False - no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
