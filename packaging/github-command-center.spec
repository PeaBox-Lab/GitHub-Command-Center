# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('github_command_center')

a = Analysis(
    ['github_command_center/launcher.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('README.md','.'),('CHANGELOG.md','.'),('RELEASE_NOTES.md','.'),
        ('USER_GUIDE.md','.'),('ARCHITECTURE.md','.'),('ROADMAP.md','.'),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas,
    [], name='GitHubCommandCenter', debug=False, bootloader_ignore_signals=False,
    strip=False, upx=True, console=False, disable_windowed_traceback=False,
)
