
# PyInstaller spec for AliTube (Windows single-file build)

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

if not (ffmpeg_dir / "ffmpeg.exe").exists():
    raise FileNotFoundError("FFmpeg not found")

if not (ffmpeg_dir / "ffprobe.exe").exists():
    raise FileNotFoundError("FFprobe not found")

binaries += [
    (str(ffmpeg_dir / "ffmpeg.exe"), "installer/ffmpeg"),
    (str(ffmpeg_dir / "ffprobe.exe"), "installer/ffmpeg"),
]

for license_file in ffmpeg_dir.glob("*"):
    if license_file.suffix.lower() in (".txt", ".md"):
        datas.append((str(license_file), "installer/ffmpeg"))

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
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="AliTube",
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
    icon=str(root / "assets" / "icons" / "alitube.ico")
    if (root / "assets" / "icons" / "alitube.ico").exists()
    else None,
)
