---
name: media-library-organizer
description: Safely identify and organize messy movie and TV files for Jellyfin or local NAS libraries. Use whenever the user asks to rename, classify, import, deduplicate by identity, arrange seasons/episodes, preserve subtitles, or clean up a movie/TV download directory. Always use the bundled deterministic planner for filesystem changes and require a metadata catalog or an explicitly configured Metadata Provider; never guess an IMDb ID or overwrite existing media.
compatibility: Python 3.10+; standard library only; no network access is required by the bundled CLI.
---

# Media Library Organizer

Use this skill to turn a download directory or an existing library into a safe,
Jellyfin-friendly layout. The bundled CLI performs deterministic planning and
execution; it does not scrape IMDb or invent metadata. By default it uses an
IMDb Public Dataset Provider backed by `title.basics.tsv.gz`. A caller can
replace that provider with a JSON metadata catalog or another implementation of
the same `search_title` / `get_title` contract.

## Safety contract

- Start with `--dry-run` (the default) and inspect the structured report before
  allowing writes with `--no-dry-run`.
- Never guess an IMDb ID. Missing, ambiguous, stale, or unavailable metadata
  must remain unchanged and be reported.
- Import mode copies and leaves source files untouched. Organize mode may move
  files only inside the specified library and never deletes or overwrites.
- Treat `CONFLICT`, `BLOCKED`, `FAILED`, `UNMATCHED`, `AMBIGUOUS`, and
  `UNMATCHED_SIDECAR` as exceptions requiring review.
- Do not pass a source path and library path that overlap in import mode.
- Symlinks are not followed. Do not broaden a path after validation.

## Default Metadata Provider

The default provider reads the official IMDb public title basics dataset from:

```text
$IMDB_DATASET_DIR/title.basics.tsv.gz
```

If `IMDB_DATASET_DIR` is unset, the default is
`~/.cache/media-library-organizer/imdb`. Download or update it explicitly:

```bash
python3 scripts/update_imdb_dataset.py \
  --dataset-dir ~/.cache/media-library-organizer/imdb
```

The update uses a temporary file and replaces the dataset only after the
download completes. The organizer itself never downloads data during a media
operation. If the dataset is unavailable, items receive
`METADATA_UNAVAILABLE` and no filesystem changes are made.

For small fixtures, offline operation, or a host-provided metadata snapshot,
use `--metadata-file` instead.

## JSON metadata catalog

The bundled provider accepts either a JSON array or an object with a `titles`
array. Each title should contain:

```json
[
  {
    "imdb_id": "tt0903747",
    "title": "Breaking Bad",
    "media_type": "series",
    "start_year": 2008
  },
  {
    "imdb_id": "tt0074887",
    "title": "The Magic Blade",
    "media_type": "movie",
    "year": 1976
  }
]
```

The catalog is a fixture or cache, not a license to scrape IMDb. If a network
provider is added by the host application, keep it behind the provider
interface and cache results with the provider version.

## Commands

Run from this skill directory:

```bash
python3 scripts/organize_media.py \
  --mode import \
  --source-path /volume/downloads \
  --movie-library-path /volume/media/Movies \
  --series-library-path /volume/media/TV \
  --metadata-file metadata.json \
  --dry-run \
  --report report.json
```

Omit `--metadata-file` to use the default IMDb dataset provider, or pass
`--metadata-dir` to select a dataset location. After reviewing `report.json`,
repeat with `--no-dry-run` to copy. For an existing library, use:

```bash
python3 scripts/organize_media.py \
  --mode organize \
  --library-path /volume/media/Movies \
  --metadata-file metadata.json \
  --dry-run
```

Use separate runs when movie and TV libraries have separate roots. `--source-path`
is accepted as an alias for `--library-path` in organize mode.

## Output and interpretation

The CLI prints JSON containing `scanned_files`, `media_items`, a `counts` map,
and one result per media item. Important statuses are:

- `MATCHED` — metadata was resolved and a target plan was made.
- `PLANNED` — dry-run plan; no filesystem changes occurred.
- `SUCCESS` — all planned video and associated Sidecars were committed.
- `NOOP` — target already contains identical content.
- `CONFLICT` — target exists with different content; nothing was overwritten.
- `UNMATCHED` / `AMBIGUOUS` — identity could not be safely resolved.
- `UNMATCHED_SIDECAR` — a Sidecar had no unique primary video.
- `METADATA_UNAVAILABLE` — reserved for an unavailable external provider.
- `BLOCKED` — path or symlink safety validation failed.
- `FAILED` — an individual filesystem operation failed; other independent
  media items continue.

The implementation supports single-file movies, `SxxEyy` TV episodes,
`Season + Episode`, Season 00 specials, common video extensions, subtitles,
NFO files, and common images. It intentionally does not guess multi-episode
files, disc splits, absolute episode numbering, editions, or multiple versions.

## Implementation notes

Read `scripts/organize_media.py` only when implementation details are needed.
It uses a temporary file, content verification, and an atomic no-overwrite link
for imports. Keep the provider interface and safety checks intact when adding
new metadata sources or naming rules.
