"""Error taxonomy. Every failure shown to a user comes from here; raw tracebacks never do.

`detail` holds technical text for the log file only.
"""
from __future__ import annotations

import errno


class AppError(Exception):
    code = "unknown"
    user_message = "Something went wrong."
    suggestion = "Check the log in Settings > Advanced for details."
    transient = False                     # safe to auto-retry?

    def __init__(self, detail: str = "") -> None:
        super().__init__(detail or self.user_message)
        self.detail = detail


class InvalidURL(AppError):
    code = "invalid_url"
    user_message = "That doesn't look like a valid URL."
    suggestion = "Paste a full link, for example https://www.youtube.com/watch?v=..."


class UnsupportedURL(AppError):
    code = "unsupported_url"
    user_message = "This link isn't supported."
    suggestion = "Only YouTube video and playlist links are supported."


class NetworkError(AppError):
    code = "network"
    user_message = "Network problem while contacting the server."
    suggestion = "Check your internet connection. The download will retry automatically."
    transient = True


class VideoUnavailable(AppError):
    code = "video_unavailable"
    user_message = "This video is unavailable."
    suggestion = "It may have been removed or made unavailable by the uploader."


class PrivateVideo(AppError):
    code = "private_video"
    user_message = "This video is private or requires sign-in."
    suggestion = "This app can't access restricted content. Only download videos you can view publicly."


class GeoRestricted(AppError):
    code = "geo_restricted"
    user_message = "This video isn't available in your region."
    suggestion = "The uploader has restricted it by country. This app doesn't work around that."


class FFmpegMissing(AppError):
    code = "ffmpeg_missing"
    user_message = "FFmpeg was not found."
    suggestion = "Set the FFmpeg path in Settings > Advanced, or reinstall the app."


class DiskSpaceError(AppError):
    code = "disk_space"
    user_message = "Not enough free disk space."
    suggestion = "Free some space or choose another download folder."


class PermissionDenied(AppError):
    code = "permission_denied"
    user_message = "The app can't write to that folder."
    suggestion = "Choose a folder you have permission to write to."


class UnsupportedFormat(AppError):
    code = "unsupported_format"
    user_message = "The requested format isn't available for this video."
    suggestion = "Pick another quality or container."


class ExtractionFailed(AppError):
    code = "extraction_failed"
    user_message = "Couldn't read this video's information."
    suggestion = "Try again later. If it keeps failing, update yt-dlp in Settings > Advanced."


class DownloadCancelled(AppError):
    code = "cancelled"
    user_message = "Download cancelled."
    suggestion = ""


class InterruptedDownload(AppError):
    code = "interrupted"
    user_message = "The download was interrupted."
    suggestion = "Press Retry to try again."
    transient = True


# Order matters: first match wins. (substring list, error class)
_MESSAGE_RULES: list[tuple[tuple[str, ...], type[AppError]]] = [
    (("private video", "sign in to confirm your age", "sign in if you've been granted",
      "members-only", "members only", "join this channel", "login required",
      "confirm you're not a bot", "confirm you’re not a bot"), PrivateVideo),
    (("not available in your country", "geo restrict", "geo-restrict",
      "blocked it in your country", "uploader has not made this video available in your country"),
     GeoRestricted),
    (("unsupported url",), UnsupportedURL),
    (("requested format is not available", "requested format not available",
      "no video formats found"), UnsupportedFormat),
    (("ffmpeg is not installed", "ffmpeg not found", "ffprobe and ffmpeg not found",
      "ffmpeg could not be found"), FFmpegMissing),
    (("no space left", "not enough space", "disk full"), DiskSpaceError),
    (("video unavailable", "this video is unavailable", "has been removed",
      "no longer available", "video has been terminated", "does not exist"), VideoUnavailable),
    (("timed out", "timeout", "connection reset", "connection aborted", "connection refused",
      "temporary failure in name resolution", "name or service not known",
      "getaddrinfo failed", "network is unreachable", "unable to download webpage",
      "http error 429", "http error 500", "http error 502", "http error 503",
      "http error 504", "incomplete read", "remote end closed"), NetworkError),
]


def _walk_chain(exc: BaseException):
    seen: set[int] = set()
    cur: BaseException | None = exc
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        yield cur
        # yt-dlp's DownloadError keeps the original in exc_info[1]
        info = getattr(cur, "exc_info", None)
        inner = info[1] if isinstance(info, tuple) and len(info) > 1 else None
        cur = cur.__cause__ or cur.__context__ or inner


def map_exception(exc: BaseException) -> AppError:
    """Translate any exception into an AppError. Never raises."""
    if isinstance(exc, AppError):
        return exc
    detail = f"{type(exc).__name__}: {exc}"

    for e in _walk_chain(exc):
        if isinstance(e, PermissionError):
            return PermissionDenied(detail)
        if isinstance(e, OSError) and e.errno == errno.ENOSPC:
            return DiskSpaceError(detail)
        if isinstance(e, FileNotFoundError) and "ffmpeg" in str(e).lower():
            return FFmpegMissing(detail)
        if isinstance(e, (TimeoutError, ConnectionError)):
            return NetworkError(detail)

    text = " | ".join(str(e) for e in _walk_chain(exc)).lower()
    for needles, cls in _MESSAGE_RULES:
        if any(n in text for n in needles):
            return cls(detail)

    if type(exc).__name__ in ("ExtractorError", "DownloadError", "ExtractionError"):
        return ExtractionFailed(detail)
    return AppError(detail)
