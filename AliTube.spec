# PyInstaller spec for AliTube (Windows onedir build).
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

root = Path(SPECPATH)
datas = []
binaries = []
hiddenimports = []

for package in ("yt_dlp", "PySide6"):
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(package)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden

ffmpeg_dir = root / "installer" / "ffmpeg"
if ffmpeg_dir.exists():
    datas.append((str(ffmpeg_dir), "installer/ffmpeg"))

a = Analysis(
    ["main.py"],
    pathex=[str(root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "test", "unittest"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="AliTube",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(root / "assets" / "icons" / "alitube.ico") if (root / "assets" / "icons" / "alitube.ico").exists() else None,
)
coll = COLLECT(
    exe, a.binaries, a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AliTube",
)
