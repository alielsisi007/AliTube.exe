"""Filesystem locations. Set YTD_DATA_DIR to override the data root (used by tests)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from app import APP_ID


def app_data_dir() -> Path:
    override = os.environ.get("YTD_DATA_DIR")
    if override:
        base = Path(override)
    elif sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / APP_ID
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / APP_ID
    base.mkdir(parents=True, exist_ok=True)
    return base


def logs_dir() -> Path:
    p = app_data_dir() / "logs"
    p.mkdir(parents=True, exist_ok=True)
    return p


def database_path() -> Path:
    return app_data_dir() / "app.db"


def default_download_dir() -> Path:
    return Path.home() / "Downloads" / "YT Downloader"


def resource_path(relative: str) -> Path:
    """Resolve a bundled resource both in dev and inside a PyInstaller bundle."""
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return root / relative
