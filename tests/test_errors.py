import errno
import unittest

from app.core import errors as E


class FakeDownloadError(Exception):
    """Mimics yt_dlp.utils.DownloadError (matched by class name)."""
    def __init__(self, msg, exc_info=None):
        super().__init__(msg)
        self.exc_info = exc_info


FakeDownloadError.__name__ = "DownloadError"


class MapperTests(unittest.TestCase):
    CASES = [
        ("ERROR: [youtube] x: Private video. Sign in if you've been granted access", E.PrivateVideo),
        ("ERROR: Sign in to confirm your age", E.PrivateVideo),
        ("ERROR: The uploader has not made this video available in your country", E.GeoRestricted),
        ("ERROR: Unsupported URL: https://example.com", E.UnsupportedURL),
        ("ERROR: Requested format is not available", E.UnsupportedFormat),
        ("ERROR: Video unavailable", E.VideoUnavailable),
        ("ERROR: ffmpeg is not installed", E.FFmpegMissing),
        ("ERROR: Unable to download webpage: <urlopen error timed out>", E.NetworkError),
        ("ERROR: HTTP Error 503: Service Unavailable", E.NetworkError),
        ("ERROR: something weird happened", E.ExtractionFailed),
    ]

    def test_message_rules(self):
        for msg, cls in self.CASES:
            with self.subTest(msg=msg):
                self.assertIsInstance(E.map_exception(FakeDownloadError(msg)), cls)

    def test_os_errors(self):
        self.assertIsInstance(E.map_exception(PermissionError("denied")), E.PermissionDenied)
        self.assertIsInstance(E.map_exception(OSError(errno.ENOSPC, "No space left on device")), E.DiskSpaceError)
        self.assertIsInstance(E.map_exception(ConnectionResetError("reset")), E.NetworkError)
        self.assertIsInstance(E.map_exception(TimeoutError()), E.NetworkError)
        self.assertIsInstance(E.map_exception(FileNotFoundError("ffmpeg.exe")), E.FFmpegMissing)

    def test_wrapped_cause_is_inspected(self):
        inner = PermissionError("nope")
        outer = FakeDownloadError("ERROR: failed", exc_info=(PermissionError, inner, None))
        self.assertIsInstance(E.map_exception(outer), E.PermissionDenied)

    def test_apperror_passthrough_and_fallback(self):
        e = E.InvalidURL("x")
        self.assertIs(E.map_exception(e), e)
        self.assertEqual(E.map_exception(ValueError("odd")).code, "unknown")

    def test_transient_flags(self):
        self.assertTrue(E.NetworkError().transient)
        self.assertTrue(E.InterruptedDownload().transient)
        for cls in (E.PrivateVideo, E.GeoRestricted, E.DiskSpaceError, E.FFmpegMissing):
            self.assertFalse(cls().transient)

    def test_user_message_hides_traceback(self):
        err = E.map_exception(ValueError("Traceback (most recent call last): secret"))
        self.assertNotIn("Traceback", err.user_message)
        self.assertIn("secret", err.detail)

    def test_unique_codes(self):
        codes = [c.code for c in vars(E).values()
                 if isinstance(c, type) and issubclass(c, E.AppError) and c is not E.AppError]
        self.assertEqual(len(codes), len(set(codes)))


if __name__ == "__main__":
    unittest.main()
