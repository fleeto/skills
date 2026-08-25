---
name: media-library-organizer
description: Safely organize local movies, TV episodes, subtitles, and existing NFO files into Jellyfin-compatible paths using local evidence and a strict Provider chain. Use whenever the user asks to sort, rename, import, normalize, or dry-run a Jellyfin/NAS media library or download directory. Never create, delete, copy, or edit NFO content; never guess an identity or overwrite media.
compatibility: Python 3.10+; standard library only; bundled CLI is offline and performs no network queries.
---

# Media Library Organizer

Use the bundled deterministic planner at `scripts/organize_media.py`. Always
start with `--dry-run` and inspect its JSON report before using
`--no-dry-run`. The unit of work is one primary video plus uniquely associated
sidecars, not an arbitrary directory.

## Safety contract

- Follow `Identify → Plan → Validate → Stage → Verify → Commit → Report`.
- Never guess an identity, overwrite a target, or use a later Provider to
  cross-validate an earlier successful Provider.
- Never persist query results or write a Provider cache file. In-process reuse
  during one invocation is allowed.
- Import copies video, subtitles, and explicitly allowed non-NFO sidecars while
  leaving all source files unchanged. Organize moves/renames within the library.
- Dry-run and validation perform no filesystem writes.
- On a failed item, roll back all video, subtitle, and NFO path operations for
  that item; continue independent items.

## Identity resolution

Use this fixed order and stop at the first reliable unique result:

1. Existing reliable NFO evidence.
2. IMDb `title.basics.tsv.gz`.
3. TMDB.
4. TVDB for television.
5. IMDb API.
6. OMDb or AniDB where applicable.
7. `UNMATCHED`.

The bundled CLI provides the local IMDb dataset adapter and a JSON fixture
adapter. Hosts may add TMDB/TVDB/API adapters through the same
`MetadataProvider` interface; unavailable adapters continue the chain.

An NFO is a local identity Provider only. Read `uniqueid`, `id`, `title`,
`originaltitle`, `year`, `season`, and `episode`. A reliable NFO ends lookup;
an NFO disagreement with filename or Provider evidence is
`METADATA_CONFLICT`; an unparseable NFO is `NFO_UNPARSEABLE` and may continue
resolution without being changed. Multiple indistinguishable candidates stop
as `AMBIGUOUS`.

The normalized result is:

```text
provider, imdb_id?, tmdb_id?, tvdb_id?, canonical_title, year,
media_type, season?, episode?
```

Only IDs returned by the winning Provider may appear in output paths.

## NFO rules

NFO content is never created, copied, updated, or deleted.

- `organize`: an existing NFO may move or be renamed with its video, byte for
  byte unchanged. Directory-level names remain `movie.nfo`, `tvshow.nfo`, or
  `season.nfo`.
- `import`: leave source NFO at its original path, filename, and bytes; do not
  copy it or create a replacement.

Represent NFO work with `NfoReader`, `NfoEvidence`, and `NfoOperation`.
`NfoOperation` is restricted to `VALIDATED_ONLY`, `MOVED_UNCHANGED`,
`RENAMED_UNCHANGED`, and `LEFT_IN_PLACE`.

## Canonical Jellyfin paths

Movie:

```text
{Title} ({Year}) [imdbid-...] [tmdbid-...] [tvdbid-...]/
└── {Title} ({Year}) [imdbid-...] [tmdbid-...] [tvdbid-...].mkv
```

Series IDs belong only on the root; reuse an existing root by confirmed series
identity and never create a duplicate for another season:

```text
{Series Title} ({Start Year}) [provider ids]/
└── Season 03/
    └── {Series Title} S03E04.mkv
```

Use `Season 00` for Specials. Preserve subtitle language and Jellyfin tags in
the basename, such as `.zh-CN`, `.en`, `.forced`, `.default`, and `.sdh`.

## Grouping, conflicts, and reports

Associate sidecars only by unique normalized basename. Report unassociated
sidecars as `UNMATCHED_SIDECAR`; do not bind them opportunistically. Ignore
`sample`, `trailer`, `extras`, and `featurette`. Do not guess multi-episode,
disc, absolute-number, edition, or multi-version layouts.

Validate path boundaries, symlink safety, permissions, target collisions, and
the complete item plan before staging. Existing targets are `CONFLICT`; an
unchanged repeated operation is `NOOP`.

Each result includes `status`, `source_paths`, `target_paths`,
`identity_source`, `provider`, `confirmed_provider_ids`, `nfo_path`,
`nfo_validation_status`, `nfo_operation`, `metadata_conflicts`, `action`,
and `error`. Use `METADATA_CONFLICT`, `NFO_UNPARSEABLE`,
`PROVIDER_UNAVAILABLE`, `UNMATCHED_SIDECAR`, `AMBIGUOUS`, `UNMATCHED`,
`CONFLICT`, `FAILED`, `BLOCKED`, `SUCCESS`, and `NOOP` as applicable.
