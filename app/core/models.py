"""Plain data models. No Qt, no yt-dlp imports, so they are trivially testable."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

LOSSLESS_AUDIO_CODECS = frozenset({"flac", "alac", "wav", "pcm_s16le", "pcm_s24le"})


# --------------------------------------------------------------------------- media
@dataclass(frozen=True, slots=True)
class FormatInfo:
    format_id: str
    ext: str
    vcodec: str | None = None
    acodec: str | None = None
    height: int | None = None
    width: int | None = None
    fps: float | None = None
    abr: float | None = None        # audio bitrate, kbit/s
    vbr: float | None = None
    tbr: float | None = None
    filesize: int | None = None
    filesize_approx: int | None = None
    protocol: str | None = None
    format_note: str | None = None

    @property
    def has_video(self) -> bool:
        return bool(self.vcodec) and self.vcodec != "none"

    @property
    def has_audio(self) -> bool:
        return bool(self.acodec) and self.acodec != "none"

    @property
    def size_bytes(self) -> int | None:
        return self.filesize or self.filesize_approx

    @property
    def is_lossless_audio(self) -> bool:
        if not self.has_audio:
            return False
        codec = (self.acodec or "").lower().split(".")[0]
        return codec in LOSSLESS_AUDIO_CODECS


@dataclass(frozen=True, slots=True)
class SubtitleTrack:
    lang: str
    name: str
    exts: tuple[str, ...]
    automatic: bool = False


@dataclass(slots=True)
class VideoInfo:
    video_id: str
    url: str
    title: str
    channel: str = ""
    duration: int | None = None     # seconds
    thumbnail: str | None = None
    is_live: bool = False
    formats: list[FormatInfo] = field(default_factory=list)
    subtitles: list[SubtitleTrack] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class PlaylistEntry:
    video_id: str
    title: str
    url: str
    index: int
    duration: int | None = None
    thumbnail: str | None = None


@dataclass(slots=True)
class PlaylistInfo:
    playlist_id: str
    title: str
    url: str
    entries: list[PlaylistEntry] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.entries)


# --------------------------------------------------------------------------- options
class DownloadMode(str, Enum):
    VIDEO = "video"
    AUDIO = "audio"


class Container(str, Enum):
    MP4 = "mp4"
    MKV = "mkv"
    WEBM = "webm"


class AudioFormat(str, Enum):
    MP3 = "mp3"
    M4A = "m4a"
    WAV = "wav"
    FLAC = "flac"


VALID_VIDEO_HEIGHTS = (4320, 2160, 1440, 1080, 720, 480, 360, 240)
VALID_AUDIO_BITRATES = (128, 192, 256, 320)


@dataclass(slots=True)
class DownloadOptions:
    mode: DownloadMode = DownloadMode.VIDEO
    height: int | None = None                 # None = best available
    container: Container = Container.MP4
    audio_format: AudioFormat = AudioFormat.MP3
    audio_bitrate: int = 192
    subtitle_langs: tuple[str, ...] = ()
    subtitle_format: str = "srt"              # "srt" | "vtt"
    embed_subtitles: bool = False
    output_dir: Path = field(default_factory=Path)
    filename_template: str = "%(title)s"
    playlist_folder: bool = True

    def validate(self) -> None:
        if self.height is not None and self.height not in VALID_VIDEO_HEIGHTS:
            raise ValueError(f"Unsupported height: {self.height}")
        if self.audio_bitrate not in VALID_AUDIO_BITRATES:
            raise ValueError(f"Unsupported audio bitrate: {self.audio_bitrate}")
        if self.subtitle_format not in ("srt", "vtt"):
            raise ValueError(f"Unsupported subtitle format: {self.subtitle_format}")


# --------------------------------------------------------------------------- jobs
class DownloadState(str, Enum):
    QUEUED = "queued"
    FETCHING = "fetching"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


S = DownloadState
ALLOWED_TRANSITIONS: dict[DownloadState, frozenset[DownloadState]] = {
    S.QUEUED: frozenset({S.FETCHING, S.CANCELLED}),
    S.FETCHING: frozenset({S.DOWNLOADING, S.FAILED, S.CANCELLED}),
    S.DOWNLOADING: frozenset({S.PAUSED, S.PROCESSING, S.COMPLETED, S.FAILED, S.CANCELLED}),
    S.PAUSED: frozenset({S.QUEUED, S.CANCELLED}),
    S.PROCESSING: frozenset({S.COMPLETED, S.FAILED, S.CANCELLED}),
    S.COMPLETED: frozenset(),
    S.FAILED: frozenset({S.QUEUED, S.CANCELLED}),
    S.CANCELLED: frozenset({S.QUEUED}),
}
ACTIVE_STATES = frozenset({S.FETCHING, S.DOWNLOADING, S.PROCESSING})
TERMINAL_STATES = frozenset({S.COMPLETED, S.FAILED, S.CANCELLED})


class InvalidTransition(Exception):
    def __init__(self, current: DownloadState, target: DownloadState) -> None:
        super().__init__(f"Cannot move download from {current.value} to {target.value}")
        self.current, self.target = current, target


@dataclass(slots=True)
class DownloadJob:
    url: str
    options: DownloadOptions
    title: str = ""
    thumbnail: str | None = None
    job_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    state: DownloadState = DownloadState.QUEUED
    progress: float = 0.0                     # 0..100
    speed_bps: float | None = None
    downloaded_bytes: int = 0
    total_bytes: int | None = None
    eta_seconds: int | None = None
    output_path: Path | None = None
    error_code: str | None = None
    error_message: str | None = None
    retries: int = 0
    resumable: bool = False                   # set only when the source proves range support
    created_at: float = field(default_factory=time.time)

    def can_transition(self, target: DownloadState) -> bool:
        return target in ALLOWED_TRANSITIONS[self.state]

    def transition(self, target: DownloadState) -> None:
        if not self.can_transition(target):
            raise InvalidTransition(self.state, target)
        self.state = target
        if target is S.COMPLETED:
            self.progress, self.speed_bps, self.eta_seconds = 100.0, None, 0
        elif target is S.QUEUED:
            self.error_code = self.error_message = None
        if target in (S.PAUSED, S.FAILED, S.CANCELLED, S.COMPLETED):
            self.speed_bps = None

    @property
    def is_active(self) -> bool:
        return self.state in ACTIVE_STATES

    @property
    def is_finished(self) -> bool:
        return self.state in TERMINAL_STATES

    def dedupe_key(self) -> tuple:
        """Two jobs with the same key would produce the same file; used to block duplicates."""
        o = self.options
        return (self.url, o.mode.value, o.height, o.container.value,
                o.audio_format.value, o.audio_bitrate)
