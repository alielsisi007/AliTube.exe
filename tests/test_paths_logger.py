import logging
import os
import tempfile
import unittest
from pathlib import Path

from app.utils import logger as L
from app.utils import paths as P


class PathsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._old = os.environ.get("YTD_DATA_DIR")
        os.environ["YTD_DATA_DIR"] = self.tmp.name

    def tearDown(self):
        if self._old is None:
            os.environ.pop("YTD_DATA_DIR", None)
        else:
            os.environ["YTD_DATA_DIR"] = self._old
        self.tmp.cleanup()

    def test_override_and_subdirs(self):
        self.assertEqual(P.app_data_dir(), Path(self.tmp.name))
        self.assertTrue(P.logs_dir().is_dir())
        self.assertEqual(P.database_path().parent, Path(self.tmp.name))

    def test_resource_path_points_into_project(self):
        self.assertTrue(P.resource_path("pyproject.toml").exists())


class LoggerTests(unittest.TestCase):
    def test_file_logging_and_idempotence(self):
        with tempfile.TemporaryDirectory() as d:
            log = L.setup_logging(Path(d))
            log = L.setup_logging(Path(d))          # second call must not duplicate handlers
            self.assertEqual(len(log.handlers), 1)
            L.get_logger("test").error("hello-log")
            for h in log.handlers:
                h.flush()
            text = (Path(d) / L.LOG_FILE_NAME).read_text(encoding="utf-8")
            self.assertIn("hello-log", text)
            for h in list(log.handlers):            # release file (needed on Windows)
                log.removeHandler(h)
                h.close()

    def test_exception_info_logged(self):
        with tempfile.TemporaryDirectory() as d:
            log = L.setup_logging(Path(d))
            try:
                raise ValueError("boom-detail")
            except ValueError:
                L.get_logger("t").exception("failed")
            for h in log.handlers:
                h.flush()
            self.assertIn("boom-detail", (Path(d) / L.LOG_FILE_NAME).read_text(encoding="utf-8"))
            for h in list(log.handlers):
                log.removeHandler(h)
                h.close()


if __name__ == "__main__":
    unittest.main()
