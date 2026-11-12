import unittest
from pathlib import Path

from app.core.models import (
    ACTIVE_STATES, ALLOWED_TRANSITIONS, AudioFormat, Container, DownloadJob,
    DownloadMode, DownloadOptions, DownloadState as S, FormatInfo, InvalidTransition,
    PlaylistInfo, PlaylistEntry,
)


def make_job(**kw) -> DownloadJob:
    return DownloadJob(url="https://youtu.be/abc", options=DownloadOptions(output_dir=Path("x")), **kw)


class FormatInfoTests(unittest.TestCase):
    def test_video_audio_flags(self):
        v = FormatInfo("137", "mp4", vcodec="avc1.640028", acodec="none", height=1080)
        a = FormatInfo("140", "m4a", vcodec="none", acodec="mp4a.40.2", abr=128)
        self.assertTrue(v.has_video and not v.has_audio)
        self.assertTrue(a.has_audio and not a.has_video)

    def test_size_prefers_exact(self):
        self.assertEqual(FormatInfo("1", "mp4", filesize=10, filesize_approx=20).size_bytes, 10)
        self.assertEqual(FormatInfo("1", "mp4", filesize_approx=20).size_bytes, 20)
        self.assertIsNone(FormatInfo("1", "mp4").size_bytes)

    def test_lossless_detection(self):
        self.assertTrue(FormatInfo("1", "flac", vcodec="none", acodec="flac").is_lossless_audio)
        self.assertFalse(FormatInfo("140", "m4a", vcodec="none", acodec="mp4a.40.2").is_lossless_audio)
        self.assertFalse(FormatInfo("251", "webm", vcodec="none", acodec="opus").is_lossless_audio)
        self.assertFalse(FormatInfo("1", "mp4", vcodec="avc1", acodec="none").is_lossless_audio)


class OptionsTests(unittest.TestCase):
    def test_defaults_valid(self):
        DownloadOptions().validate()

    def test_invalid_values(self):
        for kw in ({"height": 999}, {"audio_bitrate": 100}, {"subtitle_format": "ass"}):
            with self.assertRaises(ValueError):
                DownloadOptions(**kw).validate()

    def test_best_quality_is_none(self):
        self.assertIsNone(DownloadOptions().height)


class StateMachineTests(unittest.TestCase):
    def test_happy_path(self):
        j = make_job()
        for s in (S.FETCHING, S.DOWNLOADING, S.PROCESSING, S.COMPLETED):
            j.transition(s)
        self.assertEqual(j.progress, 100.0)
        self.assertTrue(j.is_finished)

    def test_every_pair_matches_table(self):
        for src in S:
            for dst in S:
                j = make_job()
                j.state = src
                if dst in ALLOWED_TRANSITIONS[src]:
                    j.transition(dst)
                    self.assertEqual(j.state, dst)
                else:
                    with self.assertRaises(InvalidTransition, msg=f"{src}->{dst}"):
                        j.transition(dst)
                    self.assertEqual(j.state, src)

    def test_completed_is_final(self):
        self.assertEqual(ALLOWED_TRANSITIONS[S.COMPLETED], frozenset())

    def test_retry_clears_error(self):
        j = make_job()
        j.state = S.FAILED
        j.error_code, j.error_message = "network", "boom"
        j.transition(S.QUEUED)
        self.assertIsNone(j.error_code)
        self.assertIsNone(j.error_message)

    def test_pause_resume_cycle(self):
        j = make_job()
        j.state = S.DOWNLOADING
        j.speed_bps = 1000.0
        j.transition(S.PAUSED)
        self.assertIsNone(j.speed_bps)
        j.transition(S.QUEUED)
        self.assertEqual(j.state, S.QUEUED)

    def test_active_states(self):
        self.assertEqual(ACTIVE_STATES, {S.FETCHING, S.DOWNLOADING, S.PROCESSING})

    def test_dedupe_key(self):
        a, b = make_job(), make_job()
        self.assertEqual(a.dedupe_key(), b.dedupe_key())
        b.options.height = 720
        self.assertNotEqual(a.dedupe_key(), b.dedupe_key())
        self.assertNotEqual(a.job_id, b.job_id)


class PlaylistTests(unittest.TestCase):
    def test_count(self):
        p = PlaylistInfo("id", "t", "u", [PlaylistEntry("a", "A", "ua", 1), PlaylistEntry("b", "B", "ub", 2)])
        self.assertEqual(p.count, 2)


if __name__ == "__main__":
    unittest.main()
