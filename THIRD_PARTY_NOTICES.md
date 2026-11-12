# Third-party notices

This application bundles or depends on the following. Complete this file with exact versions
when building a release (Stage 11).

| Component | Use | License | Source |
|---|---|---|---|
| FFmpeg (LGPL build, separate executable) | Merging / conversion | LGPL v2.1+ | https://ffmpeg.org/ (record exact build + source URL from `installer/ffmpeg/BUILD_INFO.txt`) |
| yt-dlp | Media extraction/download | Unlicense | https://github.com/yt-dlp/yt-dlp |
| PySide6 / Qt for Python | GUI | LGPL v3 (dynamic linking) | https://www.qt.io/qt-for-python |
| Python | Runtime | PSF License | https://www.python.org/ |

Qt/PySide6 is distributed under the LGPL; the PyInstaller one-folder build keeps Qt as separate
DLLs so users can replace them. (Prefer `--onedir` over `--onefile` for this reason.)

FFmpeg is a trademark of Fabrice Bellard, originator of the FFmpeg project. This application is
not endorsed by or affiliated with the FFmpeg project.

The full text of each license must be included in the installer under `licenses/`.
