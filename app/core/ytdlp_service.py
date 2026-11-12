from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

import yt_dlp

ProgressCallback = Callable[[dict[str, Any]], None]


def get_ffmpeg_location() -> str | None:
    """Find bundled FFmpeg first, then a system installation."""
    import sys

    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    bundled = root / "installer" / "ffmpeg"
    if (bundled / "ffmpeg.exe").exists() or (bundled / "ffmpeg").exists():
        return str(bundled)
    system = shutil.which("ffmpeg")
    return str(Path(system).parent) if system else None


def _base_ydl_options() -> dict[str, Any]:
    """Options shared by metadata extraction and downloads."""
    options: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "retries": 10,
        "fragment_retries": 10,
        "extractor_retries": 3,
        "file_access_retries": 3,
        "retry_sleep": {"http": "exponential", "fragment": "exponential"},
    }
    # Modern YouTube extraction may need a supported JS runtime for challenge solving.
    if shutil.which("deno"):
        options["js_runtimes"] = {"deno": {}}
    elif shutil.which("node"):
        options["js_runtimes"] = {"node": {}}
    return options


def inspect_video(url: str) -> dict[str, Any]:
    host = (urlparse(url).hostname or "").lower()
    allowed = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "music.youtube.com"}
    if host not in allowed:
        raise ValueError("Please enter a valid YouTube video URL.")

    opts = _base_ydl_options()
    opts.update({"skip_download": True, "extract_flat": False})
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)


def _format_size(size: int | float | None) -> str:
    if not size or size <= 0:
        return "الحجم غير متاح"
    mib = size / (1024 * 1024)
    if mib >= 1024:
        return f"~{mib / 1024:.2f} GB"
    return f"~{mib:.0f} MB"


def available_qualities(info: dict[str, Any]) -> list[dict[str, Any]]:
    """Return available heights and a best-effort total-size estimate."""
    formats = info.get("formats") or []
    duration = info.get("duration") or 0
    audio_formats = [
        f for f in formats
        if f.get("acodec") not in (None, "none") and f.get("vcodec") in (None, "none")
    ]
    best_audio = max(audio_formats, key=lambda f: f.get("abr") or f.get("tbr") or 0, default=None)

    heights = sorted({
        int(f["height"]) for f in formats
        if f.get("height") and f.get("vcodec") not in (None, "none")
    }, reverse=True)

    result: list[dict[str, Any]] = []
    for height in heights:
        candidates = [f for f in formats if f.get("height") == height and f.get("vcodec") not in (None, "none")]
        best_video = max(candidates, key=lambda f: f.get("tbr") or f.get("vbr") or 0)
        size = best_video.get("filesize") or best_video.get("filesize_approx")

        # Progressive formats already contain audio; adaptive formats need audio added.
        has_audio = best_video.get("acodec") not in (None, "none")
        if size and not has_audio and best_audio:
            audio_size = best_audio.get("filesize") or best_audio.get("filesize_approx")
            if audio_size:
                size += audio_size

        if not size and duration:
            video_rate = best_video.get("tbr") or best_video.get("vbr")
            audio_rate = 0 if has_audio else ((best_audio or {}).get("abr") or (best_audio or {}).get("tbr") or 0)
            if video_rate:
                size = (video_rate + audio_rate) * 1000 * duration / 8

        result.append({"height": height, "size": size, "size_label": _format_size(size)})
    return result


def download_media(
    url: str, output_dir: str, mode: str, quality: str, container: str,
    audio_format: str, progress: ProgressCallback, cancelled: Callable[[], bool]
) -> None:
    output = str(Path(output_dir) / "%(title).180B [%(id)s].%(ext)s")
    ffmpeg_location = get_ffmpeg_location()
    if mode == "audio":
        fmt = "bestaudio/best"
        postprocessors = [{"key": "FFmpegExtractAudio", "preferredcodec": audio_format,
                           "preferredquality": "192"}]
    else:
        height = int(quality) if quality != "Best" else None
        cap = f"[height<={height}]" if height else ""
        if container == "mp4":
            fmt = (f"bestvideo{cap}[ext=mp4]+bestaudio[ext=m4a]/"
                   f"best{cap}[ext=mp4]/best{cap}")
        elif container == "webm":
            fmt = f"bestvideo{cap}[ext=webm]+bestaudio[ext=webm]/best{cap}[ext=webm]/best{cap}"
        else:
            fmt = f"bestvideo{cap}+bestaudio/best{cap}"
        postprocessors = []

    opts: dict[str, Any] = _base_ydl_options()
    opts.update({
        "format": fmt,
        "outtmpl": output,
        "continuedl": True,
        "overwrites": False,
        "progress_hooks": [progress],
        "merge_output_format": container if mode == "video" else None,
        "postprocessors": postprocessors,
    })
    if ffmpeg_location:
        opts["ffmpeg_location"] = ffmpeg_location

    def hook(data: dict[str, Any]) -> None:
        if cancelled():
            raise yt_dlp.utils.DownloadError("Download cancelled by user")
        progress(data)

    opts["progress_hooks"] = [hook]
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])



def inspect_playlist(url: str) -> dict[str, Any]:
    """Extract playlist metadata without downloading videos."""
    opts = _base_ydl_options()
    opts.update({
        "skip_download": True,
        "extract_flat": True,
        "noplaylist": False,
        "ignoreerrors": True,
    })

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    if not info:
        raise ValueError("Could not read this YouTube playlist.")

    entries = []
    for index, item in enumerate(info.get("entries") or [], start=1):
        if not item:
            continue

        video_id = item.get("id")
        video_url = item.get("url") or item.get("webpage_url")

        if not video_url and video_id:
            video_url = f"https://www.youtube.com/watch?v={video_id}"

        if video_url and not video_url.startswith(("http://", "https://")):
            if video_id:
                video_url = f"https://www.youtube.com/watch?v={video_id}"
            else:
                continue

        if not video_url:
            continue

        entries.append({
            "id": video_id or "",
            "title": item.get("title") or f"Video {index}",
            "url": video_url,
            "index": index,
            "duration": item.get("duration"),
            "thumbnail": item.get("thumbnail"),
        })

    if not entries:
        raise ValueError("No available videos were found in this playlist.")

    return {
        "id": info.get("id", ""),
        "title": info.get("title") or "YouTube Playlist",
        "url": url,
        "entries": entries,
        "count": len(entries),
    }


def download_playlist(
    entries: list[dict[str, Any]],
    output_dir: str,
    mode: str,
    quality: str,
    container: str,
    audio_format: str,
    progress: ProgressCallback,
    cancelled: Callable[[], bool],
    playlist_title: str = "YouTube Playlist",
) -> list[dict[str, Any]]:
    """Download playlist videos sequentially; continue after individual failures."""

    safe_title = "".join(
        c for c in playlist_title
        if c not in '<>:"/\\|?*' and ord(c) >= 32
    ).strip(" .") or "YouTube Playlist"

    playlist_dir = Path(output_dir) / safe_title
    playlist_dir.mkdir(parents=True, exist_ok=True)

    results = []

    for index, entry in enumerate(entries, start=1):
        if cancelled():
            break

        title = entry.get("title") or f"Video {index}"
        video_url = entry["url"]

        def playlist_progress(data: dict[str, Any]) -> None:
            payload = dict(data)
            payload.update({
                "playlist_index": index,
                "playlist_count": len(entries),
                "playlist_title": title,
            })
            progress(payload)

        try:
            download_media(
                video_url,
                str(playlist_dir),
                mode,
                quality,
                container,
                audio_format,
                playlist_progress,
                cancelled,
            )
            results.append({
                "index": index,
                "title": title,
                "status": "completed",
            })
        except Exception as exc:
            if cancelled():
                break

            results.append({
                "index": index,
                "title": title,
                "status": "failed",
                "error": str(exc),
            })

            progress({
                "status": "playlist_video_failed",
                "playlist_index": index,
                "playlist_count": len(entries),
                "playlist_title": title,
                "error": str(exc),
            })

    return results
