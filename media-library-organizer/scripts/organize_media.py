#!/usr/bin/env python3
"""Safe, metadata-driven movie and TV library organizer.

The implementation intentionally uses only the Python standard library.  A
JSON catalog is the bundled Metadata Provider; callers can replace it by
implementing the MetadataProvider protocol and using the library classes.
"""

from __future__ import annotations

import argparse
import dataclasses
import gzip
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import uuid
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable, Protocol


VIDEO_EXTENSIONS = {".mkv", ".mp4", ".avi", ".ts", ".m2ts"}
SIDECAR_EXTENSIONS = {".srt", ".ass", ".ssa", ".vtt", ".nfo", ".jpg", ".jpeg", ".png"}
IGNORED_WORDS = {"sample", "trailer", "extras", "extra", "featurette", "proof"}
LANGUAGE_TAGS = {"zh", "zh-cn", "zh-tw", "en", "ja", "ko", "forced", "default", "sdh"}
NOISE_WORDS = {
    "2160p", "1080p", "720p", "576p", "480p", "4k", "8k", "bluray", "bdrip",
    "web-dl", "webdl", "webrip", "hdtv", "dvdrip", "x264", "x265", "hevc",
    "av1", "lpcm", "dts", "aac", "atmos", "proper", "repack", "remux",
}
YEAR_RE = re.compile(r"(?<!\d)(19\d{2}|20\d{2})(?!\d)")
EPISODE_RE = re.compile(r"(?i)(?:^|[. _-])s(\d{1,2})(?:e(\d{1,3}))+")
EPISODE_PART_RE = re.compile(r"(?i)e(\d{1,3})")


class MetadataProvider(Protocol):
    def search_title(self, title: str, year: int | None, media_type: str | None) -> list[dict[str, Any]]:
        ...

    def get_title(self, imdb_id: str) -> dict[str, Any] | None:
        ...


class MetadataUnavailableError(RuntimeError):
    """The configured default metadata source is not available."""


class ProviderUnavailableError(RuntimeError):
    """A Provider cannot be queried during this invocation."""


def metadata_score(wanted_title: str, record: dict[str, Any], year: int | None) -> float:
    score = SequenceMatcher(None, normalize_text(wanted_title), normalize_text(str(record["title"]))).ratio()
    if normalize_text(wanted_title) == normalize_text(str(record["title"])):
        score = 1.0
    record_year = record.get("year", record.get("start_year"))
    if year and record_year:
        try:
            difference = abs(int(record_year) - year)
        except (TypeError, ValueError):
            difference = 99
        score += 0.15 if difference == 0 else (-0.15 if difference > 1 else 0)
    return score


class ProviderChain:
    """Run Providers in order and stop at the first non-empty result."""

    def __init__(self, providers: Iterable[tuple[str, MetadataProvider]]):
        self.providers = list(providers)
        self.unavailable: list[str] = []

    def search_title(self, title: str, year: int | None, media_type: str | None) -> tuple[str | None, list[dict[str, Any]]]:
        for name, provider in self.providers:
            if name.casefold() == "tvdb" and media_type == "movie":
                continue
            try:
                candidates = provider.search_title(title, year, media_type)
            except (ProviderUnavailableError, MetadataUnavailableError, OSError, TimeoutError):
                self.unavailable.append(name)
                continue
            if candidates:
                return name, candidates
        return None, []


@dataclasses.dataclass(frozen=True)
class NfoEvidence:
    path: Path
    unique_ids: dict[str, str]
    title: str | None
    original_title: str | None
    year: int | None
    season: int | None
    episode: int | None
    parse_error: str | None = None


class NfoOperation:
    VALIDATED_ONLY = "VALIDATED_ONLY"
    MOVED_UNCHANGED = "MOVED_UNCHANGED"
    RENAMED_UNCHANGED = "RENAMED_UNCHANGED"
    LEFT_IN_PLACE = "LEFT_IN_PLACE"


class NfoReader:
    """Read only identity fields from an existing NFO."""

    def read(self, path: Path) -> NfoEvidence:
        try:
            root = ET.parse(path).getroot()
            values: dict[str, str] = {}
            unique_ids: dict[str, str] = {}
            for element in root.iter():
                name = element.tag.casefold().split("}")[-1]
                if name == "uniqueid" and element.text:
                    unique_ids[(element.attrib.get("type") or "unknown").casefold()] = element.text.strip()
                elif name in {"title", "originaltitle", "year", "season", "episode", "id"} and element.text:
                    values.setdefault(name, element.text.strip())
            if values.get("id") and not unique_ids:
                unique_ids["imdb" if values["id"].casefold().startswith("tt") else "unknown"] = values["id"]
            return NfoEvidence(path, unique_ids, values.get("title"), values.get("originaltitle"),
                               _int_or_none(values.get("year")), _int_or_none(values.get("season")),
                               _int_or_none(values.get("episode")))
        except (ET.ParseError, OSError, UnicodeError) as exc:
            return NfoEvidence(path, {}, None, None, None, None, None, str(exc))


def _int_or_none(value: str | None) -> int | None:
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


class JsonMetadataProvider:
    """Metadata provider backed by a caller-supplied JSON array.

    Each item should contain imdb_id, title, media_type (movie or series), and
    optionally year/start_year.  This keeps matching deterministic and avoids
    silently scraping or depending on an undocumented web endpoint.
    """

    def __init__(self, records: Iterable[dict[str, Any]]):
        self.records = [r for r in records if isinstance(r, dict)]

    @classmethod
    def from_file(cls, path: Path) -> "JsonMetadataProvider":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get("titles", [])
        if not isinstance(data, list):
            raise ValueError("metadata file must contain a JSON array or {\"titles\": [...]}")
        return cls(data)

    def search_title(self, title: str, year: int | None, media_type: str | None) -> list[dict[str, Any]]:
        wanted = normalize_text(title)
        scored: list[tuple[float, dict[str, Any]]] = []
        for record in self.records:
            if not record.get("imdb_id") or not record.get("title"):
                continue
            record_type = str(record.get("media_type", "")).lower()
            if media_type and record_type != media_type:
                continue
            scored.append((metadata_score(title, record, year), record))
        return [record for _, record in sorted(scored, key=lambda item: item[0], reverse=True)]

    def get_title(self, imdb_id: str) -> dict[str, Any] | None:
        return next((r for r in self.records if r.get("imdb_id") == imdb_id), None)


class ImdbDatasetProvider:
    """Provider for IMDb's public ``title.basics.tsv.gz`` dataset.

    The dataset is downloaded separately by ``update_imdb_dataset.py``.  This
    provider intentionally streams the compressed file and caches each query,
    avoiding a dependency on an online API or a multi-gigabyte in-memory index.
    """

    MOVIE_TYPES = {"movie", "tvMovie"}
    SERIES_TYPES = {"tvSeries", "tvMiniSeries", "tvSpecial"}

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir.expanduser().resolve()
        self.basics_path = self.data_dir / "title.basics.tsv.gz"
        if not self.basics_path.is_file():
            raise MetadataUnavailableError(
                f"IMDb dataset not found: {self.basics_path}. "
                "Run scripts/update_imdb_dataset.py or provide --metadata-file."
            )
        self._cache: dict[tuple[str, int | None, str | None], list[dict[str, Any]]] = {}

    def search_title(self, title: str, year: int | None, media_type: str | None) -> list[dict[str, Any]]:
        key = (normalize_text(title), year, media_type)
        if key in self._cache:
            return self._cache[key]
        wanted_types = self.MOVIE_TYPES if media_type == "movie" else self.SERIES_TYPES if media_type == "series" else self.MOVIE_TYPES | self.SERIES_TYPES
        scored: list[tuple[float, dict[str, Any]]] = []
        with gzip.open(self.basics_path, "rt", encoding="utf-8", newline="") as handle:
            header = next(handle).rstrip("\n").split("\t")
            columns = {name: index for index, name in enumerate(header)}
            for line in handle:
                fields = line.rstrip("\n").split("\t")
                title_type = fields[columns["titleType"]]
                if title_type not in wanted_types:
                    continue
                start_year = fields[columns["startYear"]]
                record: dict[str, Any] = {
                    "imdb_id": fields[columns["tconst"]],
                    "title": fields[columns["primaryTitle"]],
                    "original_title": fields[columns["originalTitle"]],
                    "media_type": "movie" if title_type in self.MOVIE_TYPES else "series",
                }
                if start_year != "\\N":
                    record["year"] = int(start_year)
                    if record["media_type"] == "series":
                        record["start_year"] = int(start_year)
                score = metadata_score(title, record, year)
                if score >= 0.55:
                    scored.append((score, record))
        result = [record for _, record in sorted(scored, key=lambda item: item[0], reverse=True)]
        self._cache[key] = result
        return result

    def get_title(self, imdb_id: str) -> dict[str, Any] | None:
        with gzip.open(self.basics_path, "rt", encoding="utf-8", newline="") as handle:
            header = next(handle).rstrip("\n").split("\t")
            columns = {name: index for index, name in enumerate(header)}
            for line in handle:
                fields = line.rstrip("\n").split("\t")
                if fields[columns["tconst"]] == imdb_id:
                    media_type = fields[columns["titleType"]]
                    return {
                        "imdb_id": imdb_id,
                        "title": fields[columns["primaryTitle"]],
                        "original_title": fields[columns["originalTitle"]],
                        "media_type": "movie" if media_type in self.MOVIE_TYPES else "series",
                        "year": None if fields[columns["startYear"]] == "\\N" else int(fields[columns["startYear"]]),
                    }
        return None


@dataclasses.dataclass(frozen=True)
class ParsedName:
    title: str
    year: int | None
    season: int | None = None
    episode: int | None = None


@dataclasses.dataclass
class MediaItem:
    primary_video: Path
    sidecars: list[Path]
    parsed: ParsedName
    media_type: str | None = None
    metadata: dict[str, Any] | None = None
    status: str = "PENDING"
    reason: str | None = None
    target_root: Path | None = None
    target_video: Path | None = None
    target_sidecars: list[tuple[Path, Path]] = dataclasses.field(default_factory=list)
    nfo_path: Path | None = None
    nfo_evidence: NfoEvidence | None = None
    target_nfo: Path | None = None
    nfo_operation: str = NfoOperation.VALIDATED_ONLY
    identity_source: str | None = None
    provider: str | None = None
    metadata_conflicts: list[str] = dataclasses.field(default_factory=list)

    def result(self, action: str | None = None, error_code: str | None = None) -> dict[str, Any]:
        return {
            "status": self.status,
            "action": action,
            "source_paths": [str(self.primary_video), *(str(p) for p in self.sidecars)],
            "target_paths": ([str(self.target_video), *(str(dst) for _, dst in self.target_sidecars),
                              *((str(self.target_nfo),) if self.target_nfo and self.nfo_operation != NfoOperation.LEFT_IN_PLACE else ())]
                             if self.target_video else []),
            "imdb_id": self.metadata.get("imdb_id") if self.metadata else None,
            "confirmed_provider_ids": {
                key: self.metadata.get(key) for key in ("imdb_id", "tmdb_id", "tvdb_id")
                if self.metadata and self.metadata.get(key)
            },
            "identity_source": self.identity_source,
            "provider": self.provider,
            "nfo_path": str(self.nfo_path) if self.nfo_path else None,
            "nfo_validation_status": (
                "UNPARSEABLE" if self.nfo_evidence and self.nfo_evidence.parse_error
                else "VALID" if self.nfo_evidence else "ABSENT"
            ),
            "nfo_operation": self.nfo_operation,
            "metadata_conflicts": self.metadata_conflicts,
            "media_type": self.media_type,
            "season": self.parsed.season,
            "episode": self.parsed.episode,
            "error_code": error_code,
            "reason": self.reason,
        }


def normalize_text(value: str) -> str:
    value = value.casefold().replace("_", " ").replace(".", " ")
    value = re.sub(r"[^\w\s-]", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()


def safe_component(value: str) -> str:
    value = re.sub(r"[<>:\"/\\|?*\x00-\x1f]", " - ", value)
    value = re.sub(r"\s+", " ", value).strip(" .")
    return value or "Unknown Title"


def is_ignored(path: Path) -> bool:
    tokens = set(re.split(r"[. _()\[\]-]+", path.stem.casefold()))
    return bool(tokens & IGNORED_WORDS) or any(part.casefold() in IGNORED_WORDS for part in path.parts)


def parse_release_name(path: Path) -> ParsedName | None:
    stem = path.stem
    episode_match = EPISODE_RE.search(stem)
    season = episode = None
    if episode_match:
        season = int(episode_match.group(1))
        episodes = EPISODE_PART_RE.findall(episode_match.group(0))
        if len(episodes) != 1:
            return None
        episode = int(episodes[0])

    year_match = YEAR_RE.search(stem)
    year = int(year_match.group(1)) if year_match else None
    end = episode_match.start() if episode_match else (year_match.start() if year_match else len(stem))
    title = stem[:end]
    title = re.sub(r"^\[[^]]+\]\s*", "", title)
    title = re.sub(r"(?i)\b(?:season|episode)\s*\d+.*$", "", title)
    tokens = re.split(r"[. _-]+", title)
    while tokens and (tokens[-1].casefold() in NOISE_WORDS or not tokens[-1]):
        tokens.pop()
    title = " ".join(tokens).strip(" -._")
    if not title:
        return None
    return ParsedName(title=title, year=year, season=season, episode=episode)


def is_sidecar(path: Path) -> bool:
    return path.suffix.casefold() in SIDECAR_EXTENSIONS


def scan_files(root: Path) -> tuple[list[Path], list[Path]]:
    videos: list[Path] = []
    sidecars: list[Path] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        suffix = path.suffix.casefold()
        if suffix in VIDEO_EXTENSIONS:
            if not is_ignored(path):
                videos.append(path)
        elif suffix in SIDECAR_EXTENSIONS:
            sidecars.append(path)
    return videos, sidecars


def sidecar_candidates(video: Path, sidecars: Iterable[Path]) -> list[Path]:
    candidates = []
    video_key = normalize_text(video.stem)
    for sidecar in sidecars:
        if sidecar.suffix.casefold() == ".nfo":
            continue
        if sidecar.parent != video.parent:
            continue
        sidecar_key = normalize_text(sidecar.stem)
        if sidecar_key == video_key or sidecar_key.startswith(video_key + " "):
            candidates.append(sidecar)
    return sorted(candidates)


def nfo_candidates(video: Path, sidecars: Iterable[Path]) -> list[Path]:
    names = {f"{video.stem.casefold()}.nfo", "movie.nfo", "tvshow.nfo", "season.nfo"}
    return sorted(path for path in sidecars
                  if path.parent == video.parent and path.name.casefold() in names)


def attach_nfo(item: MediaItem, candidates: list[Path]) -> None:
    if not candidates:
        return
    # A same-directory specific NFO wins over a directory-level NFO. Multiple
    # directory-level NFO files are ambiguous local evidence.
    specific = [path for path in candidates if path.stem.casefold() == item.primary_video.stem.casefold()]
    if len(specific) == 1:
        item.nfo_path = specific[0]
    elif len(candidates) == 1:
        item.nfo_path = candidates[0]
    else:
        item.status = "AMBIGUOUS"
        item.reason = "Multiple NFO candidates"
        return
    item.nfo_evidence = NfoReader().read(item.nfo_path)
    if item.nfo_evidence.parse_error:
        item.status = "NFO_UNPARSEABLE"
        item.reason = item.nfo_evidence.parse_error


def nfo_identity_matches(item: MediaItem) -> bool:
    evidence = item.nfo_evidence
    if not evidence or evidence.parse_error:
        return False
    nfo_title = evidence.title or evidence.original_title
    if nfo_title and normalize_text(nfo_title) != normalize_text(item.parsed.title):
        item.metadata_conflicts.append(f"NFO title conflicts with filename: {nfo_title}")
        return False
    if evidence.year and item.parsed.year and evidence.year != item.parsed.year:
        item.metadata_conflicts.append(f"NFO year conflicts with filename: {evidence.year}")
        return False
    if evidence.season is not None and item.parsed.season is not None and evidence.season != item.parsed.season:
        item.metadata_conflicts.append("NFO season conflicts with filename")
        return False
    if evidence.episode is not None and item.parsed.episode is not None and evidence.episode != item.parsed.episode:
        item.metadata_conflicts.append("NFO episode conflicts with filename")
        return False
    return bool(evidence.unique_ids or nfo_title)


def match_metadata(item: MediaItem, provider: MetadataProvider | ProviderChain | None) -> None:
    if item.nfo_evidence and not item.nfo_evidence.parse_error:
        if not nfo_identity_matches(item):
            item.status, item.reason = "METADATA_CONFLICT", "; ".join(item.metadata_conflicts)
            return
        ids: dict[str, str] = {}
        for key, value in item.nfo_evidence.unique_ids.items():
            if key in {"imdb", "imdbid"}:
                ids["imdb_id"] = value
            elif key in {"tmdb", "tmdbid"}:
                ids["tmdb_id"] = value
            elif key in {"tvdb", "tvdbid"}:
                ids["tvdb_id"] = value
        item.metadata = {
            **ids,
            "title": item.nfo_evidence.title or item.nfo_evidence.original_title or item.parsed.title,
            "year": item.nfo_evidence.year or item.parsed.year,
            "start_year": item.nfo_evidence.year or item.parsed.year,
            "media_type": "series" if item.parsed.season is not None else "movie",
        }
        item.media_type = item.metadata["media_type"]
        item.identity_source = "nfo"
        item.provider = "nfo"
        item.status = "MATCHED"
        return
    if provider is None:
        item.status, item.reason = "PROVIDER_UNAVAILABLE", "No usable Metadata Provider was configured"
        return
    requested_type = "series" if item.parsed.season is not None else None
    provider_name = None
    if isinstance(provider, ProviderChain):
        provider_name, candidates = provider.search_title(item.parsed.title, item.parsed.year, requested_type)
    else:
        try:
            candidates = provider.search_title(item.parsed.title, item.parsed.year, requested_type)
        except (ProviderUnavailableError, MetadataUnavailableError, OSError, TimeoutError):
            item.status, item.reason = "PROVIDER_UNAVAILABLE", "Metadata Provider unavailable"
            return
        provider_name = provider.__class__.__name__
    if not candidates:
        if isinstance(provider, ProviderChain) and provider.unavailable:
            item.status, item.reason = "PROVIDER_UNAVAILABLE", ", ".join(provider.unavailable)
        else:
            item.status, item.reason = "UNMATCHED", "No metadata candidate"
        return
    first = candidates[0]
    first_title = normalize_text(str(first.get("title", "")))
    title_score = SequenceMatcher(None, normalize_text(item.parsed.title), first_title).ratio()
    first_year = first.get("year", first.get("start_year"))
    year_ok = not item.parsed.year or not first_year or int(first_year) == item.parsed.year
    if title_score < 0.78 or not year_ok:
        item.status, item.reason = "AMBIGUOUS", "Top metadata candidate did not meet title/year checks"
        return
    if len(candidates) > 1:
        second = candidates[1]
        second_score = SequenceMatcher(None, normalize_text(item.parsed.title), normalize_text(str(second.get("title", "")))).ratio()
        if abs(title_score - second_score) < 0.10:
            item.status, item.reason = "AMBIGUOUS", "Multiple metadata candidates are too close"
            return
    if requested_type == "series" and str(first.get("media_type", "")).lower() != "series":
        item.status, item.reason = "AMBIGUOUS", "Episode matched a non-series title"
        return
    item.metadata = first
    item.provider = provider_name
    item.identity_source = provider_name
    item.media_type = "series" if requested_type == "series" else str(first.get("media_type", "movie")).lower()
    if item.media_type not in {"movie", "series"}:
        item.status, item.reason = "AMBIGUOUS", "Unsupported metadata media type"
        item.metadata = None
        return
    item.status = "MATCHED"


def find_existing_series(library: Path, metadata: dict[str, Any]) -> Path | None:
    markers = [f"[{key[:-3]}id-{metadata[key]}]".casefold()
               for key in ("imdb_id", "tmdb_id", "tvdb_id") if metadata.get(key)]
    for path in library.rglob("*"):
        if path.is_dir() and any(marker in path.name.casefold() for marker in markers):
            return path
    return None


def provider_id_suffix(metadata: dict[str, Any]) -> str:
    labels = (("imdb_id", "imdbid"), ("tmdb_id", "tmdbid"), ("tvdb_id", "tvdbid"))
    return "".join(f" [{label}-{metadata[key]}]" for key, label in labels if metadata.get(key))


def build_targets(item: MediaItem, movie_library: Path | None, series_library: Path | None) -> None:
    assert item.metadata is not None
    title = safe_component(str(item.metadata.get("title") or item.parsed.title))
    year = item.metadata.get("year", item.metadata.get("start_year", item.parsed.year))
    year_text = f" ({int(year)})" if year else ""
    ids_text = provider_id_suffix(item.metadata)
    if not ids_text:
        item.status, item.reason = "UNMATCHED", "Winning metadata had no confirmed provider ID"
        return
    if item.media_type == "movie":
        assert movie_library is not None
        root = movie_library / f"{title}{year_text}{ids_text}"
        item.target_root = root
        item.target_video = root / f"{root.name}{item.primary_video.suffix.lower()}"
        for sidecar in item.sidecars:
            suffix = sidecar.stem[len(item.primary_video.stem):]
            target_name = item.target_video.stem + suffix + sidecar.suffix.lower()
            item.target_sidecars.append((sidecar, root / target_name))
        if item.nfo_path:
            item.target_nfo = root / ("movie.nfo" if item.nfo_path.stem.casefold() == "movie" else item.target_video.stem + ".nfo")
        return
    assert series_library is not None
    root = find_existing_series(series_library, item.metadata)
    if root is None:
        root = series_library / f"{title}{year_text}{ids_text}"
    season = item.parsed.season or 0
    season_dir = root / f"Season {season:02d}"
    item.target_root = root
    item.target_video = season_dir / f"{title} S{season:02d}E{item.parsed.episode or 0:02d}{item.primary_video.suffix.lower()}"
    suffix = item.primary_video.stem
    for sidecar in item.sidecars:
        remainder = sidecar.stem[len(suffix):] if sidecar.stem.startswith(suffix) else ""
        if not remainder:
            remainder = sidecar.stem[len(item.primary_video.stem):]
        target_name = item.target_video.stem + remainder + sidecar.suffix.lower()
        item.target_sidecars.append((sidecar, item.target_video.parent / target_name))
    if item.nfo_path:
        item.target_nfo = (root / "tvshow.nfo" if item.nfo_path.name.casefold() == "tvshow.nfo"
                           else season_dir / "season.nfo" if item.nfo_path.name.casefold() == "season.nfo"
                           else item.target_video.parent / (item.target_video.stem + ".nfo"))


def path_is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
        return True
    except ValueError:
        return False


def has_symlink_component(path: Path, stop: Path) -> bool:
    current = path
    stop = stop.resolve(strict=False)
    while True:
        if current.exists() and current.is_symlink():
            return True
        if current == stop or current.parent == current:
            return False
        current = current.parent


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def same_content(source: Path, target: Path) -> bool:
    return source.stat().st_size == target.stat().st_size and digest(source) == digest(target)


def validate_item(item: MediaItem, source_root: Path, target_root: Path) -> None:
    if item.target_video is None or item.target_root is None:
        item.status, item.reason = "FAILED", "Target was not generated"
        return
    for source in [item.primary_video, *item.sidecars]:
        if source.is_symlink() or not path_is_within(source, source_root):
            item.status, item.reason = "BLOCKED", "Source path is a symlink or outside source root"
            return
    for target in [item.target_video, *(dst for _, dst in item.target_sidecars)]:
        if not path_is_within(target, target_root) or has_symlink_component(target.parent, target_root):
            item.status, item.reason = "BLOCKED", "Target path is outside library root or crosses a symlink"
            return


def atomic_copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    os.close(fd)
    temp = Path(temp_name)
    try:
        shutil.copy2(source, temp)
        if not same_content(source, temp):
            raise IOError("copy verification failed")
        os.link(temp, target)
        temp.unlink()
    finally:
        if temp.exists():
            temp.unlink()


def atomic_move(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    os.link(source, target)
    try:
        source.unlink()
    except Exception:
        target.unlink(missing_ok=True)
        raise


def execute_item(item: MediaItem, mode: str, dry_run: bool, target_root: Path) -> dict[str, Any]:
    assert item.target_video is not None
    sources_targets = [(item.primary_video, item.target_video), *item.target_sidecars]
    if mode == "organize" and item.nfo_path and item.target_nfo:
        sources_targets.append((item.nfo_path, item.target_nfo))
        item.nfo_operation = (NfoOperation.RENAMED_UNCHANGED
                              if item.nfo_path.name != item.target_nfo.name
                              else NfoOperation.MOVED_UNCHANGED)
    elif mode == "import" and item.nfo_path:
        item.nfo_operation = NfoOperation.LEFT_IN_PLACE
        item.target_nfo = None
    if all(dst.exists() and same_content(src, dst) for src, dst in sources_targets):
        item.status = "NOOP"
        return item.result("noop")
    if any(dst.exists() for _, dst in sources_targets):
        item.status, item.reason = "CONFLICT", "Target path already exists with different content"
        return item.result("skip", "TARGET_EXISTS")
    action = "copy" if mode == "import" else "move"
    if dry_run:
        item.status = "PLANNED"
        return item.result(action)
    committed: list[tuple[Path, Path]] = []
    try:
        for source, target in sources_targets:
            if mode == "import":
                atomic_copy(source, target)
            else:
                atomic_move(source, target)
            committed.append((source, target))
        item.status = "SUCCESS"
        return item.result(action)
    except Exception as exc:  # report and continue with independent items
        for source, target in reversed(committed):
            try:
                if mode == "import":
                    target.unlink(missing_ok=True)
                elif target.exists() and not source.exists():
                    atomic_move(target, source)
            except OSError:
                # Keep the original failure as the primary report; the
                # remaining filesystem state is visible in the item paths.
                pass
        item.status, item.reason = "FAILED", str(exc)
        return item.result(action, "FILESYSTEM_ERROR")


def process(args: argparse.Namespace) -> dict[str, Any]:
    if args.mode == "organize":
        source_value = args.library_path or args.source_path
        if not source_value:
            raise ValueError("organize mode requires --library-path (or --source-path)")
        source_root = Path(source_value).expanduser().resolve()
    else:
        if not args.source_path:
            raise ValueError("import mode requires --source-path")
        source_root = Path(args.source_path).expanduser().resolve()
    movie_library = Path(args.movie_library_path).expanduser().resolve() if args.movie_library_path else None
    series_library = Path(args.series_library_path).expanduser().resolve() if args.series_library_path else None
    if args.mode == "organize":
        movie_library = movie_library or source_root
        series_library = series_library or source_root
    if not source_root.is_dir():
        raise ValueError(f"source_path is not a directory: {source_root}")
    if args.mode == "import":
        if movie_library is None or series_library is None:
            raise ValueError("import mode requires movie_library_path and series_library_path")
        if any(path_is_within(source_root, root) or path_is_within(root, source_root)
               for root in (movie_library, series_library)):
            raise ValueError("source_path and library paths must not overlap in import mode")
    provider_error: str | None = None
    if args.metadata_file:
        provider: MetadataProvider | ProviderChain | None = ProviderChain(
            [("metadata_catalog", JsonMetadataProvider.from_file(Path(args.metadata_file)))]
        )
    else:
        dataset_dir = Path(args.metadata_dir or os.environ.get(
            "IMDB_DATASET_DIR", str(Path.home() / ".cache" / "media-library-organizer" / "imdb")
        ))
        try:
            provider = ProviderChain([("imdb_dataset", ImdbDatasetProvider(dataset_dir))])
        except MetadataUnavailableError as exc:
            provider = None
            provider_error = str(exc)
        else:
            provider_error = None
    videos, sidecars = scan_files(source_root)
    results: list[dict[str, Any]] = []
    associated_sidecars: set[Path] = set()
    for video in videos:
        parsed = parse_release_name(video)
        if parsed is None or (parsed.season is not None and parsed.episode is None):
            results.append({"status": "UNSUPPORTED_FORMAT", "source_paths": [str(video)], "error_code": "UNSUPPORTED_FORMAT"})
            continue
        item = MediaItem(video, sidecar_candidates(video, sidecars), parsed)
        attach_nfo(item, nfo_candidates(video, sidecars))
        if item.nfo_path:
            associated_sidecars.add(item.nfo_path)
        if item.status in {"AMBIGUOUS", "METADATA_CONFLICT"}:
            results.append(item.result(error_code=item.status))
            continue
        associated_sidecars.update(item.sidecars)
        match_metadata(item, provider)
        if item.status in {"METADATA_UNAVAILABLE", "PROVIDER_UNAVAILABLE"}:
            item.reason = provider_error
        if item.status != "MATCHED":
            results.append(item.result(error_code=item.status))
            continue
        build_targets(item, movie_library, series_library)
        if item.status != "MATCHED":
            results.append(item.result(error_code=item.status))
            continue
        library_root = movie_library if item.media_type == "movie" else series_library
        assert library_root is not None
        validate_item(item, source_root, library_root)
        if item.status == "BLOCKED":
            results.append(item.result(error_code="PATH_SAFETY"))
            continue
        results.append(execute_item(item, args.mode, args.dry_run, library_root))
    for sidecar in sidecars:
        if sidecar.suffix.casefold() == ".nfo":
            # Existing NFO is handled as identity evidence, and in organize
            # mode as an unchanged path operation. It is never an unmatched
            # copy candidate.
            continue
        if sidecar not in associated_sidecars:
            results.append({
                "status": "UNMATCHED_SIDECAR",
                "source_paths": [str(sidecar)],
                "target_paths": [],
                "error_code": "UNMATCHED_SIDECAR",
                "reason": "No unique primary video association",
            })
    counts: dict[str, int] = {}
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1
    return {"scanned_files": len(videos) + len(sidecars), "media_items": len(results), "counts": counts, "items": results}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Safely organize movies and TV episodes for Jellyfin.")
    parser.add_argument("--mode", choices=("import", "organize"), required=True)
    parser.add_argument("--source-path")
    parser.add_argument("--library-path", help="Library root for organize mode")
    parser.add_argument("--movie-library-path")
    parser.add_argument("--series-library-path")
    parser.add_argument("--metadata-file", help="JSON metadata catalog; omit to use the default IMDb dataset provider")
    parser.add_argument("--metadata-dir", help="IMDb dataset directory; defaults to IMDB_DATASET_DIR or ~/.cache/media-library-organizer/imdb")
    parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--report", type=Path, help="Write the structured report to this JSON file")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = process(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAILED", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.report:
        args.report.write_text(rendered + "\n", encoding="utf-8")
    return 0 if not report["counts"].get("FAILED") and not report["counts"].get("BLOCKED") else 1


if __name__ == "__main__":
    raise SystemExit(main())
