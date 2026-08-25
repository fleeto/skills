import json
import tempfile
import unittest
from pathlib import Path

from scripts.organize_media import build_parser, process


class OrganizerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.downloads = self.root / "downloads"
        self.movies = self.root / "movies"
        self.tv = self.root / "tv"
        self.downloads.mkdir()
        self.movies.mkdir()
        self.tv.mkdir()
        self.catalog = self.root / "metadata.json"
        self.catalog.write_text(json.dumps([
            {"imdb_id": "tt0074887", "title": "The Magic Blade", "media_type": "movie", "year": 1976},
            {"imdb_id": "tt0903747", "title": "Breaking Bad", "media_type": "series", "start_year": 2008},
            {"imdb_id": "tt9999999", "title": "Crash", "media_type": "movie", "year": 2004},
            {"imdb_id": "tt8888888", "title": "Crash", "media_type": "movie", "year": 2004},
        ]), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def args(self, *values):
        return build_parser().parse_args(values)

    def test_dry_run_does_not_write_and_preserves_sidecar_plan(self):
        video = self.downloads / "[TTG] The.Magic.Blade.1976.1080p.BluRay.mkv"
        subtitle = self.downloads / "[TTG] The.Magic.Blade.1976.1080p.BluRay.zh-CN.ass"
        video.write_bytes(b"movie")
        subtitle.write_bytes(b"subtitle")

        report = process(self.args(
            "--mode", "import", "--source-path", str(self.downloads),
            "--movie-library-path", str(self.movies), "--series-library-path", str(self.tv),
            "--metadata-file", str(self.catalog), "--dry-run",
        ))

        self.assertEqual(report["counts"].get("PLANNED"), 1)
        self.assertEqual(report["counts"].get("UNMATCHED_SIDECAR", 0), 0)
        self.assertTrue(video.exists())
        self.assertFalse(any(self.movies.rglob("*")))

    def test_import_copies_video_and_subtitle_and_is_idempotent(self):
        video = self.downloads / "Breaking.Bad.S03E04.1080p.mkv"
        subtitle = self.downloads / "Breaking.Bad.S03E04.1080p.zh-CN.ass"
        video.write_bytes(b"episode")
        subtitle.write_bytes(b"subtitle")
        args = self.args(
            "--mode", "import", "--source-path", str(self.downloads),
            "--movie-library-path", str(self.movies), "--series-library-path", str(self.tv),
            "--metadata-file", str(self.catalog), "--no-dry-run",
        )

        first = process(args)
        target = self.tv / "Breaking Bad (2008) [imdbid-tt0903747]" / "Season 03" / "Breaking Bad S03E04.mkv"
        target_subtitle = target.with_name("Breaking Bad S03E04.zh-CN.ass")
        self.assertEqual(first["counts"].get("SUCCESS"), 1)
        self.assertTrue(target.exists())
        self.assertTrue(target_subtitle.exists())
        self.assertTrue(video.exists())
        self.assertTrue(subtitle.exists())

        second = process(args)
        self.assertEqual(second["counts"].get("NOOP"), 1)

    def test_ambiguous_match_does_not_create_target(self):
        video = self.downloads / "Crash.2004.mkv"
        video.write_bytes(b"ambiguous")
        report = process(self.args(
            "--mode", "import", "--source-path", str(self.downloads),
            "--movie-library-path", str(self.movies), "--series-library-path", str(self.tv),
            "--metadata-file", str(self.catalog), "--no-dry-run",
        ))
        self.assertEqual(report["counts"].get("AMBIGUOUS"), 1)
        self.assertFalse(any(self.movies.rglob("*")))

    def test_conflict_does_not_overwrite(self):
        video = self.downloads / "The.Magic.Blade.1976.mkv"
        video.write_bytes(b"new")
        target_dir = self.movies / "The Magic Blade (1976) [imdbid-tt0074887]"
        target_dir.mkdir()
        target = target_dir / f"{target_dir.name}.mkv"
        target.write_bytes(b"existing")
        report = process(self.args(
            "--mode", "import", "--source-path", str(self.downloads),
            "--movie-library-path", str(self.movies), "--series-library-path", str(self.tv),
            "--metadata-file", str(self.catalog), "--no-dry-run",
        ))
        self.assertEqual(report["counts"].get("CONFLICT"), 1)
        self.assertEqual(target.read_bytes(), b"existing")

    def test_unmatched_sidecar_is_reported(self):
        video = self.downloads / "The.Magic.Blade.1976.mkv"
        subtitle = self.downloads / "unrelated.zh-CN.ass"
        video.write_bytes(b"movie")
        subtitle.write_bytes(b"subtitle")
        report = process(self.args(
            "--mode", "import", "--source-path", str(self.downloads),
            "--movie-library-path", str(self.movies), "--series-library-path", str(self.tv),
            "--metadata-file", str(self.catalog), "--dry-run",
        ))
        self.assertEqual(report["counts"].get("PLANNED"), 1)
        self.assertEqual(report["counts"].get("UNMATCHED_SIDECAR"), 1)


if __name__ == "__main__":
    unittest.main()
