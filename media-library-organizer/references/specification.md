# Media organizer implementation specification

## Public boundaries

- `MetadataProvider`: `search_title(title, year?, media_type?)` and optional `get_title(imdb_id)`.
- `ProviderChain`: invokes providers sequentially, stops at the first reliable unique result, and has no disk cache.
- `NfoReader` / `NfoEvidence`: read-only NFO identity evidence.
- `NfoOperation`: only `VALIDATED_ONLY`, `MOVED_UNCHANGED`, `RENAMED_UNCHANGED`, or `LEFT_IN_PLACE`.
- `OperationPlan` and report records: source, target, action, status, rollback/error, identity, and NFO validation fields.

NFO operations must never expose `CREATED`, `COPIED`, `UPDATED`, or `DELETED`.

## Resolution

Scan and group first, then parse title/year/type/season/episode. Read a reliable
NFO before querying Providers. NFO disagreement is `METADATA_CONFLICT`; an
unparseable NFO is `NFO_UNPARSEABLE` and may continue to filename evidence and
the Provider chain. A unique Provider result ends resolution. No later Provider
is queried for cross-validation. No result is `UNMATCHED`; unavailable results
continue the chain and are recorded as `PROVIDER_UNAVAILABLE`; unresolved
multiple candidates are `AMBIGUOUS`.

## Transactions

`import` atomically copies video/subtitles/non-NFO sidecars, verifies content,
and leaves all source paths unchanged. `organize` atomically moves/renames
video, subtitles, and existing NFO paths within the library. Validate every
target before staging, refuse existing targets, and roll back every committed
path for an item if any member fails. Continue independent items.

## Acceptance invariants

- Reliable NFO causes zero Provider calls.
- Import never copies or edits source NFO.
- Organize preserves NFO bytes.
- Dry-run performs no writes.
- Ambiguity, conflict, unavailable metadata without fallback, and unmatched
  identity produce no target files.
- Repeating the same operation produces `NOOP`.
- No Provider query cache file is created.
