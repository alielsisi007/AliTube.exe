"""AliTube - a lightweight YouTube downloader for Windows."""
import sys
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow
from app.utils.logger import setup_logging

def main() -> int:
    setup_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("AliTube")
    app.setOrganizationName("AliTube")
    app.setApplicationDisplayName("AliTube")
    window = MainWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
