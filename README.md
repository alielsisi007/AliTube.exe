# AliTube

AliTube is a small Windows desktop application for downloading YouTube videos
and audio that you own or are authorized to download.

## Features in this MVP

- Simple single-window interface.
- Analyze a public YouTube video before downloading.
- Choose an available video resolution.
- Download video as MP4, MKV, or WebM where the source formats permit it.
- Extract audio as MP3, M4A, or WAV.
- Choose the output folder.
- Show download progress, speed, and ETA.
- Cancel an active download.
- Uses yt-dlp and FFmpeg; no DRM, private-video, sign-in, or access-control bypass.

## Run from source (Windows 10/11)

Install Python 3.12 or newer, then open PowerShell in this folder:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

FFmpeg is needed to merge separate audio/video streams and convert audio.
To fetch the configured LGPL build, run:

```powershell
powershell -ExecutionPolicy Bypass -File installer\fetch_ffmpeg.ps1
```

## Build the Windows application

Run PowerShell as a normal user in the project folder:

```powershell
powershell -ExecutionPolicy Bypass -File build_windows.ps1
```

The build creates `dist\AliTube\AliTube.exe`. Copy the entire `dist\AliTube`
folder when distributing the onedir build; do not copy the EXE alone.

## Tests

```powershell
python -m unittest discover -s tests -v
```

## Important

Download only content you own, have permission to download, or are otherwise
legally authorized to save. Follow YouTube's terms and applicable laws.

## Run from source (Linux Mint / Ubuntu)

```bash
sudo apt install python3-venv python3-pip ffmpeg -y
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

For current YouTube extraction, keep `yt-dlp` updated. A supported JavaScript
runtime (Deno recommended; Node.js is also detected when available) is useful
for YouTube challenge solving. FFmpeg is used for merging and audio conversion.

Quality sizes shown by AliTube are estimates when the source exposes enough
bitrate or file-size information; actual output size can differ.
# AliTube.exe
# AliTube.exe
