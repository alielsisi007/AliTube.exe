from __future__ import annotations
import os
from pathlib import Path
from PySide6.QtCore import Qt, QThread, QUrl
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QFileDialog, QProgressBar, QGroupBox,
    QMessageBox, QFormLayout
)
from app.workers.qt_workers import InspectWorker, DownloadWorker

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AliTube")
        self.setMinimumSize(600, 520)
        self.resize(760, 640)
        self.info = None
        self.inspect_thread = None
        self.download_thread = None
        self.download_worker = None
        self.output_dir = str(Path.home() / "Downloads")
        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        self.main_layout = layout
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        brand = QLabel("▶  AliTube")
        brand.setObjectName("brand")
        subtitle = QLabel("Simple Video Downloader")
        subtitle.setObjectName("muted")
        header.addWidget(brand)
        header.addStretch()
        header.addWidget(subtitle)
        layout.addLayout(header)

        url_group = QGroupBox("Video link")
        url_layout = QVBoxLayout(url_group)
        row = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste a YouTube video URL...")
        self.analyze_btn = QPushButton("Analyze")
        self.analyze_btn.clicked.connect(self.analyze)
        row.addWidget(self.url_input, 1)
        row.addWidget(self.analyze_btn)
        url_layout.addLayout(row)
        layout.addWidget(url_group)

        self.video_title = QLabel("Paste a link and click Analyze.")
        self.video_title.setWordWrap(True)
        self.video_title.setObjectName("videoTitle")
        self.video_meta = QLabel("")
        self.video_meta.setObjectName("muted")
        layout.addWidget(self.video_title)
        layout.addWidget(self.video_meta)

        options = QGroupBox("Download options")
        form = QFormLayout(options)
        self.form_layout = form
        self.mode = QComboBox()
        self.mode.addItem("Video", "video")
        self.mode.addItem("Audio only", "audio")
        self.mode.currentIndexChanged.connect(self._mode_changed)
        self.quality = QComboBox()
        self.quality.addItem("Best available", "Best")
        for h in (4320, 2160, 1440, 1080, 720, 480, 360, 240):
            self.quality.addItem(f"{h}p", str(h))
        self.container = QComboBox()
        self.container.addItems(["mp4", "mkv", "webm"])
        self.audio_format = QComboBox()
        self.audio_format.addItems(["mp3", "m4a", "wav"])
        form.addRow("Mode", self.mode)
        form.addRow("Quality", self.quality)
        form.addRow("Video format", self.container)
        form.addRow("Audio format", self.audio_format)
        layout.addWidget(options)

        folder_row = QHBoxLayout()
        self.folder_label = QLabel(self.output_dir)
        self.folder_label.setObjectName("muted")
        self.folder_label.setWordWrap(True)
        browse = QPushButton("Choose folder")
        browse.clicked.connect(self.choose_folder)
        folder_row.addWidget(QLabel("Save to:" ))
        folder_row.addWidget(self.folder_label, 1)
        folder_row.addWidget(browse)
        layout.addLayout(folder_row)

        action_row = QHBoxLayout()
        self.download_btn = QPushButton("Download")
        self.download_btn.setObjectName("primary")
        self.download_btn.setEnabled(False)
        self.download_btn.clicked.connect(self.start_download)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_download)
        action_row.addWidget(self.download_btn, 1)
        action_row.addWidget(self.cancel_btn)
        layout.addLayout(action_row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        layout.addWidget(self.progress)
        self.status = QLabel("Ready")
        self.status.setObjectName("muted")
        layout.addWidget(self.status)

        bottom = QHBoxLayout()
        bottom.addStretch()
        open_folder = QPushButton("Open download folder")
        open_folder.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(self.output_dir)))
        bottom.addWidget(open_folder)
        layout.addLayout(bottom)
        self._mode_changed()

    def _apply_style(self):
        self._update_responsive_layout()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_responsive_layout()

    def _update_responsive_layout(self):
        if not hasattr(self, "main_layout"):
            return

        scale = min(
            1.0,
            self.width() / 760,
            self.height() / 640
        )
        scale = max(0.78, scale)

        control_height = round(40 * scale)
        font_size = max(9, round(13 * scale))
        group_padding = round(12 * scale)
        button_padding = round(10 * scale)

        margin = round(22 * scale)
        spacing = round(11 * scale)

        self.main_layout.setContentsMargins(
            margin, margin, margin, margin
        )
        self.main_layout.setSpacing(spacing)

        self.form_layout.setVerticalSpacing(round(11 * scale))
        self.form_layout.setHorizontalSpacing(round(16 * scale))

        self.setFont(QFont("Segoe UI", max(8, round(10 * scale))))

        rules = [
            "QMainWindow, QWidget { background: #17191f; color: #edf0f5; }",

            f"QGroupBox {{ border: 1px solid #343944; border-radius: 9px; "
            f"margin-top: 9px; padding: {group_padding}px; font-weight: 600; "
            f"font-size: {font_size}px; }}",

            "QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; }",

            f"QLineEdit, QComboBox {{ background: #252a35; "
            f"border: 1px solid #4a5363; border-radius: 8px; "
            f"min-height: {control_height}px; padding: 3px 9px; "
            f"font-size: {font_size}px; color: #ffffff; }}",

            f"QComboBox {{ min-width: {round(110 * scale)}px; }}",

            f"QComboBox::drop-down {{ width: {round(32 * scale)}px; "
            "border: none; border-left: 1px solid #414958; }",

            f"QComboBox QAbstractItemView {{ background: #252a35; "
            f"color: #ffffff; selection-background-color: #e32636; "
            f"selection-color: white; font-size: {font_size}px; }}",

            f"QPushButton {{ background: #303642; border: 0; "
            f"border-radius: 6px; min-height: {round(34 * scale)}px; "
            f"padding: 3px {button_padding}px; font-size: {font_size}px; "
            "color: white; }",

            "QPushButton:hover { background: #414a5a; }",
            "QPushButton:disabled { color: #818895; background: #282d36; }",

            "QPushButton#primary { background: #e32636; font-weight: 700; }",
            "QPushButton#primary:hover { background: #c91e2c; }",

            f"QLabel {{ font-size: {font_size}px; }}",
            f"QLabel#brand {{ font-size: {round(23 * scale)}px; "
            "font-weight: 800; color: #ffffff; }",

            f"QLabel#videoTitle {{ font-size: {round(15 * scale)}px; "
            "font-weight: 650; }",

            "QLabel#muted { color: #aab1bf; }",

            f"QProgressBar {{ border: 0; border-radius: 5px; "
            f"background: #303642; min-height: {round(12 * scale)}px; "
            "text-align: center; }",

            "QProgressBar::chunk { background: #e32636; border-radius: 5px; }"
        ]

        self.setStyleSheet("\\n".join(rules))

    def _mode_changed(self):
        audio = self.mode.currentData() == "audio"
        self.quality.setEnabled(not audio)
        self.container.setEnabled(not audio)
        self.audio_format.setEnabled(audio)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose download folder", self.output_dir)
        if folder:
            self.output_dir = folder
            self.folder_label.setText(folder)

    def analyze(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.information(self, "AliTube", "Paste a YouTube URL first.")
            return
        if self.inspect_thread and self.inspect_thread.isRunning():
            return
        self.analyze_btn.setEnabled(False)
        self.download_btn.setEnabled(False)
        self.status.setText("Reading video information...")
        self.inspect_thread = QThread()
        self.inspect_worker = InspectWorker(url)
        self.inspect_worker.moveToThread(self.inspect_thread)
        self.inspect_thread.started.connect(self.inspect_worker.run)
        self.inspect_worker.finished.connect(self._on_inspected)
        self.inspect_worker.failed.connect(self._on_error)
        self.inspect_worker.finished.connect(self.inspect_thread.quit)
        self.inspect_worker.failed.connect(self.inspect_thread.quit)
        self.inspect_thread.finished.connect(self.inspect_worker.deleteLater)
        self.inspect_thread.finished.connect(self.inspect_thread.deleteLater)
        self.inspect_thread.start()

    def _on_inspected(self, info):
        self.info = info
        self.video_title.setText(info["title"])

        if info.get("type") == "playlist":
            count = info.get("count", len(info.get("entries", [])))
            self.video_meta.setText(f"YouTube Playlist  •  {count} videos")

            self.quality.clear()
            self.quality.addItem("Best available", "Best")

        else:
            duration = info.get("duration")
            mins = (
                f"{int(duration)//60}:{int(duration)%60:02d}"
                if duration else "Unknown duration"
            )

            self.video_meta.setText(
                f'{info.get("channel") or "YouTube"}  •  {mins}'
            )

            qualities = info.get("qualities") or []

            self.quality.clear()
            self.quality.addItem("Best available", "Best")

            for item in qualities:
                height = item["height"]
                size_label = item.get("size_label") or "الحجم غير متاح"
                self.quality.addItem(
                    f"{height}p  •  {size_label}",
                    str(height)
                )

            if not qualities:
                self.quality.addItem(
                    "Best available (quality details unavailable)", "Best"
                )

        self.download_btn.setEnabled(True)
        self.analyze_btn.setEnabled(True)
        self.status.setText("Analysis completed. Choose options and download.")

    def _on_error(self, message):
        self.analyze_btn.setEnabled(True)
        self.download_btn.setEnabled(False)
        self.status.setText("Could not analyze video.")
        QMessageBox.warning(self, "AliTube", message[:700])

    def start_download(self):
        if not self.info:
            return
        if self.download_thread and self.download_thread.isRunning():
            return
        self.download_btn.setEnabled(False)
        self.analyze_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress.setValue(0)
        self.status.setText("Starting download...")
        self.download_thread = QThread()
        self.download_worker = DownloadWorker(
            self.url_input.text().strip(),
            self.output_dir,
            self.mode.currentData(),
            self.quality.currentData(),
            self.container.currentText(),
            self.audio_format.currentText(),
            info=self.info,
        )
        self.download_worker.moveToThread(self.download_thread)
        self.download_thread.started.connect(self.download_worker.run)
        self.download_worker.progress.connect(self._on_progress)
        self.download_worker.finished.connect(self._on_download_finished)
        self.download_worker.failed.connect(self._on_download_failed)
        self.download_worker.finished.connect(self.download_thread.quit)
        self.download_worker.failed.connect(self.download_thread.quit)
        self.download_thread.finished.connect(self.download_worker.deleteLater)
        self.download_thread.finished.connect(self.download_thread.deleteLater)
        self.download_thread.start()

    def cancel_download(self):
        if self.download_worker:
            self.download_worker.cancel()
            self.cancel_btn.setEnabled(False)
            self.status.setText("Cancelling download...")

    def _on_progress(self, data):
        status = data.get("status")
        if status == "downloading":
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            downloaded = data.get("downloaded_bytes", 0)
            if total:
                self.progress.setValue(int(downloaded * 100 / total))
            speed = data.get("_speed_str", "--")
            eta = data.get("_eta_str", "--")
            self.status.setText(f"Downloading  •  {speed}  •  ETA {eta}")
        elif status == "finished":
            self.progress.setValue(100)
            self.status.setText("Processing media...")

    def _on_download_finished(self):
        self.progress.setValue(100)
        self.status.setText("Download completed.")
        self.download_btn.setEnabled(True)
        self.analyze_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        QMessageBox.information(self, "AliTube", "Your download is complete.")

    def _on_download_failed(self, message):
        self.status.setText("Download stopped or failed.")
        self.download_btn.setEnabled(True)
        self.analyze_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        QMessageBox.warning(self, "AliTube", message[:700])
