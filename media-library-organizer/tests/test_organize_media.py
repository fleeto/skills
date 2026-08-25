import gzip
import json
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from scripts.organize_media import ProviderChain, build_parser, process


class FakeProvider:
    def __init__(self, result=None, error=None):
        self.result = result or []
        self.error = error
        self.calls = 0

    def search_title(self, title, year, media_type):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result

    def get_title(self, imdb_id):
        return None


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

    def test_default_imdb_dataset_provider_matches_without_json_catalog(self):
        dataset_dir = self.root / "imdb"
        dataset_dir.mkdir()
        header = "tconst\ttitleType\tprimaryTitle\toriginalTitle\tisAdult\tstartYear\tendYear\truntimeMinutes\tgenres\n"
        row = "tt0074887\tmovie\tThe Magic Blade\tThe Magic Blade\t0\t1976\t\\N\t105\tAction\n"
        with gzip.open(dataset_dir / "title.basics.tsv.gz", "wt", encoding="utf-8") as handle:
            handle.write(header + row)
        video = self.downloads / "[TTG] The.Magic.Blade.1976.1080p.BluRay.x265.10bit.LPCM-WiKi.mkv"
        video.write_bytes(b"movie")

        report = process(self.args(
            "--mode", "import", "--source-path", str(self.downloads),
            "--movie-library-path", str(self.movies), "--series-library-path", str(self.tv),
            "--metadata-dir", str(dataset_dir), "--dry-run",
        ))

        self.assertEqual(report["counts"].get("PLANNED"), 1)
        self.assertIn("The Magic Blade (1976) [imdbid-tt0074887]", report["items"][0]["target_paths"][0])

    def test_missing_default_dataset_is_explicitly_reported(self):
        video = self.downloads / "The.Magic.Blade.1976.mkv"
        video.write_bytes(b"movie")
        report = process(self.args(
            "--mode", "import", "--source-path", str(self.downloads),
            "--movie-library-path", str(self.movies), "--series-library-path", str(self.tv),
            "--metadata-dir", str(self.root / "missing"), "--dry-run",
        ))
        self.assertEqual(report["counts"].get("PROVIDER_UNAVAILABLE"), 1)
        self.assertFalse(any(self.movies.rglob("*")))

    def test_provider_chain_stops_after_first_success(self):
        first = FakeProvider([{"imdb_id": "tt1", "title": "Movie", "media_type": "movie", "year": 2020}])
        second = FakeProvider([{"imdb_id": "tt2", "title": "Movie", "media_type": "movie", "year": 2020}])
        chain = ProviderChain([("imdb_dataset", first), ("tmdb", second)])
        name, candidates = chain.search_title("Movie", 2020, "movie")
        self.assertEqual(name, "imdb_dataset")
        self.assertEqual(candidates[0]["imdb_id"], "tt1")
        self.assertEqual(first.calls, 1)
        self.assertEqual(second.calls, 0)

    def test_provider_chain_continues_when_unavailable(self):
        first = FakeProvider(error=OSError("offline"))
        second = FakeProvider([{"imdb_id": "tt2", "title": "Movie", "media_type": "movie", "year": 2020}])
        chain = ProviderChain([("imdb_dataset", first), ("tmdb", second)])
        name, _ = chain.search_title("Movie", 2020, "movie")
        self.assertEqual(name, "tmdb")
        self.assertEqual(chain.unavailable, ["imdb_dataset"])

    def test_import_does_not_copy_or_modify_nfo(self):
        video = self.downloads / "The.Magic.Blade.1976.mkv"
        nfo = self.downloads / "movie.nfo"
        video.write_bytes(b"movie")
        original = b"<movie><uniqueid type=\"imdb\">tt0074887</uniqueid><title>The Magic Blade</title><year>1976</year></movie>"
        nfo.write_bytes(original)
        report = process(self.args(
            "--mode", "import", "--source-path", str(self.downloads),
            "--movie-library-path", str(self.movies), "--series-library-path", str(self.tv),
            "--metadata-file", str(self.catalog), "--no-dry-run",
        ))
        self.assertEqual(report["counts"].get("SUCCESS"), 1)
        self.assertEqual(nfo.read_bytes(), original)
        self.assertTrue(nfo.exists())
        self.assertFalse(any(path.name.endswith(".nfo") for path in self.movies.rglob("*")))

    def test_nfo_conflict_performs_no_filesystem_operation(self):
        video = self.downloads / "The.Magic.Blade.1977.mkv"
        nfo = self.downloads / "movie.nfo"
        video.write_bytes(b"movie")
        nfo.write_text("<movie><uniqueid type=\"imdb\">tt0074887</uniqueid><title>The Magic Blade</title><year>1976</year></movie>", encoding="utf-8")
        report = process(self.args(
            "--mode", "import", "--source-path", str(self.downloads),
            "--movie-library-path", str(self.movies), "--series-library-path", str(self.tv),
            "--metadata-file", str(self.catalog), "--no-dry-run",
        ))
        self.assertEqual(report["counts"].get("METADATA_CONFLICT"), 1)
        self.assertFalse(any(self.movies.rglob("*")))

    def test_organize_moves_nfo_without_changing_bytes(self):
        video = self.movies / "The.Magic.Blade.1976.mkv"
        nfo = self.movies / "movie.nfo"
        video.write_bytes(b"movie")
        original = b"<movie><uniqueid type=\"imdb\">tt0074887</uniqueid><title>The Magic Blade</title><year>1976</year></movie>"
        nfo.write_bytes(original)
        report = process(self.args(
            "--mode", "organize", "--library-path", str(self.movies),
            "--metadata-file", str(self.catalog), "--no-dry-run",
        ))
        target = self.movies / "The Magic Blade (1976) [imdbid-tt0074887]"
        self.assertEqual(report["counts"].get("SUCCESS"), 1)
        self.assertEqual((target / "movie.nfo").read_bytes(), original)
        self.assertFalse(video.exists())

    def test_organize_rolls_back_video_when_nfo_move_fails(self):
        video = self.movies / "The.Magic.Blade.1976.mkv"
        nfo = self.movies / "movie.nfo"
        video.write_bytes(b"movie")
        nfo.write_text("<movie><uniqueid type=\"imdb\">tt0074887</uniqueid><title>The Magic Blade</title><year>1976</year></movie>", encoding="utf-8")
        import scripts.organize_media as organizer
        original_move = organizer.atomic_move

        def fail_nfo(source, target):
            if source.suffix == ".nfo":
                raise OSError("simulated NFO failure")
            return original_move(source, target)

        with mock.patch.object(organizer, "atomic_move", side_effect=fail_nfo):
            report = process(self.args(
                "--mode", "organize", "--library-path", str(self.movies),
                "--metadata-file", str(self.catalog), "--no-dry-run",
            ))
        self.assertEqual(report["counts"].get("FAILED"), 1)
        self.assertTrue(video.exists())
        self.assertTrue(nfo.exists())


if __name__ == "__main__":
    unittest.main()
