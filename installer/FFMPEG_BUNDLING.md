# FFmpeg bundling policy

Decision: FFmpeg is **bundled** with the installer, as a **separate `ffmpeg.exe` process**
(the app never links FFmpeg libraries into its own code), using an **LGPL-only** build.

## Requirements the build must satisfy
- `ffmpeg -version` must NOT contain `--enable-gpl` or `--enable-nonfree`.
- Must provide encoders: `libmp3lame` (MP3), `aac` (M4A / MP4 audio), `flac`, `pcm_s16le` (WAV).
- `installer/fetch_ffmpeg.ps1` enforces both and aborts the build otherwise.

## Consequences for the app design
- LGPL builds exclude `libx264`/`libx265`. The app therefore **never promises H.264 re-encoding**.
  MP4 output is produced by stream copy (remux) when the source is H.264/AAC. When the source is
  VP9/AV1/Opus, MP4 is not offered as a lossless remux; the UI offers MKV/WebM, and any transcode
  uses whatever encoders the bundled build reports at runtime (probed in Stage 5), with a visible warning.
- Encoder availability is **probed at runtime** (`ffmpeg -encoders`), not assumed.

## LGPL obligations checklist (this is engineering guidance, not legal advice; have counsel confirm)
1. Ship the LGPL license text next to the binary (`installer/ffmpeg/COPYING.LGPL*`, copied by the script).
2. Ship `THIRD_PARTY_NOTICES.md` and show it in About > Licenses.
3. Provide the source: link to the exact upstream source/commit of the build you ship
   (record it from `BUILD_INFO.txt`) and keep it available.
4. Keep FFmpeg as a replaceable standalone executable so users can swap in their own build
   (Settings > Advanced > FFmpeg path supports this).
5. Do not imply endorsement by the FFmpeg project; use their name/trademarks only descriptively.
6. Patent note: some codecs (e.g. AAC, H.264) may carry patent licensing considerations in some
   jurisdictions independent of copyright license. Review before commercial distribution.
