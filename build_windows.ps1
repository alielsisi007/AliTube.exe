$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python launcher 'py' was not found. Install Python 3.12+ first."
}

if (-not (Test-Path ".venv")) {
    py -3.12 -m venv .venv
}
& ".venv\Scripts\python.exe" -m pip install --upgrade pip
& ".venv\Scripts\python.exe" -m pip install -r requirements-dev.txt

if (-not (Test-Path "installer\ffmpeg\ffmpeg.exe")) {
    Write-Host "Bundled FFmpeg not found. Fetching and checking LGPL build..."
    powershell -ExecutionPolicy Bypass -File "installer\fetch_ffmpeg.ps1"
}

& ".venv\Scripts\pyinstaller.exe" --noconfirm --clean "AliTube.spec"
Write-Host ""
Write-Host "Build complete: dist\AliTube\AliTube.exe"
Write-Host "Distribute the whole dist\AliTube folder, not only the EXE."
