from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from app.core.ytdlp_service import (
    inspect_video,
    inspect_playlist,
    available_qualities,
    download_media,
    download_playlist,
)


class InspectWorker(QObject):
    finished = Signal(dict)
    failed = Signal(str)

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def run(self):
        try:
            # لو الرابط يحتوي على list= يبقى Playlist
            if "list=" in self.url:
                info = inspect_playlist(self.url)

                self.finished.emit({
                    "type": "playlist",
                    "id": info.get("id", ""),
                    "title": info.get("title", "YouTube Playlist"),
                    "url": info.get("url", self.url),
                    "entries": info.get("entries", []),
                    "count": info.get("count", 0),
                    "qualities": [],
                })
                return

            # رابط فيديو عادي
            info = inspect_video(self.url)

            self.finished.emit({
                "type": "video",
                "id": info.get("id", ""),
                "title": info.get("title", "Untitled"),
                "channel": info.get("channel") or info.get("uploader") or "",
                "duration": info.get("duration"),
                "thumbnail": info.get("thumbnail"),
                "qualities": available_qualities(info),
            })

        except Exception as exc:
            self.failed.emit(str(exc))


class DownloadWorker(QObject):
    progress = Signal(dict)
    finished = Signal()
    failed = Signal(str)

    def __init__(
        self,
        url,
        folder,
        mode,
        quality,
        container,
        audio_format,
        info=None,
    ):
        super().__init__()

        self.args = (
            url,
            folder,
            mode,
            quality,
            container,
            audio_format,
        )
        self.info = info
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            if self._cancelled:
                self.failed.emit("Download cancelled.")
                return

            if self.info and self.info.get("type") == "playlist":
                entries = self.info.get("entries", [])

                if not entries:
                    raise ValueError("Playlist contains no downloadable videos.")

                results = download_playlist(
                    entries=entries,
                    output_dir=self.args[1],
                    mode=self.args[2],
                    quality=self.args[3],
                    container=self.args[4],
                    audio_format=self.args[5],
                    progress=self.progress.emit,
                    cancelled=lambda: self._cancelled,
                    playlist_title=self.info.get("title", "YouTube Playlist"),
                )

                if self._cancelled:
                    self.failed.emit("Download cancelled.")
                    return

                completed = sum(
                    1 for item in results
                    if item.get("status") == "completed"
                )
                failed = sum(
                    1 for item in results
                    if item.get("status") == "failed"
                )

                self.progress.emit({
                    "status": "playlist_summary",
                    "completed": completed,
                    "failed": failed,
                    "total": len(entries),
                })

                if completed == 0:
                    raise RuntimeError(
                        f"All {failed} playlist videos failed to download."
                    )

                self.finished.emit()
                return

            # تحميل فيديو فردي
            download_media(
                *self.args,
                progress=self.progress.emit,
                cancelled=lambda: self._cancelled,
            )

            self.finished.emit()

        except Exception as exc:
            if self._cancelled:
                self.failed.emit("Download cancelled.")
            else:
                self.failed.emit(str(exc))