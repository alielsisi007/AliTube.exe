<#
 Downloads an LGPL-only FFmpeg build into installer\ffmpeg\ and REFUSES to continue if the
 build is GPL or lacks the encoders this app needs. Run on Windows before PyInstaller.

 Usage:  powershell -ExecutionPolicy Bypass -File installer\fetch_ffmpeg.ps1 [-Url <zip url>]

 Default source: BtbN/FFmpeg-Builds "win64-lgpl" release (a third-party build; FFmpeg itself is
 not distributed by FFmpeg.org as Windows binaries). Pin a specific tagged release URL for
 reproducible builds and record it in THIRD_PARTY_NOTICES.md.
#>
param(
  [string]$Url = "https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/ffmpeg-master-latest-win64-lgpl.zip"
)
$ErrorActionPreference = "Stop"
$dest = Join-Path $PSScriptRoot "ffmpeg"
$tmp  = Join-Path $env:TEMP "ffmpeg-lgpl.zip"
$ext  = Join-Path $env:TEMP "ffmpeg-lgpl-extract"

Invoke-WebRequest -Uri $Url -OutFile $tmp
if (Test-Path $ext) { Remove-Item $ext -Recurse -Force }
Expand-Archive $tmp -DestinationPath $ext -Force
$root = Get-ChildItem $ext -Directory | Select-Object -First 1

New-Item -ItemType Directory -Force $dest | Out-Null
Copy-Item (Join-Path $root.FullName "bin\*") $dest -Recurse -Force
foreach ($f in "LICENSE.txt","LICENSE","COPYING.LGPLv3","COPYING.LGPLv2.1") {
  $p = Join-Path $root.FullName $f
  if (Test-Path $p) { Copy-Item $p $dest -Force }
}

# ---- Verification: fail the build rather than ship the wrong binary ----
$exe = Join-Path $dest "ffmpeg.exe"
$probe = Join-Path $dest "ffprobe.exe"
if (-not (Test-Path $probe)) {
    throw "ffprobe.exe is missing from the FFmpeg build."
}
$ver = & $exe -version | Out-String
if ($ver -match "--enable-gpl")      { throw "This FFmpeg build is GPL (--enable-gpl). Use an LGPL build." }
if ($ver -match "--enable-nonfree")  { throw "This FFmpeg build is non-free and not redistributable." }
$enc = & $exe -hide_banner -encoders | Out-String
foreach ($need in "libmp3lame"," aac ","flac","pcm_s16le") {
  if ($enc -notmatch [regex]::Escape($need)) { throw "Required encoder missing: $need" }
}
$ver.Split("`n")[0] | Set-Content (Join-Path $dest "BUILD_INFO.txt")
$ver | Add-Content (Join-Path $dest "BUILD_INFO.txt")
Write-Host "OK: LGPL FFmpeg verified in $dest"
Write-Host ($ver.Split("`n")[0])
