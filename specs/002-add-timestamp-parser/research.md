# Phase 0 Research: Add Timestamp Parser (002)

Feature: convert Hekmat logger clock stamps (`HH:MM:SS.mmm`) to a numeric seconds
timeline. All unknowns from the plan's Technical Context were already resolved by the
phase-5 diagnostic study (Task 5.0, `docs/task_log.md`) on the seven reference
recordings; this document records the decisions and their rationale.

## D1 — Where the conversion lives

- **Decision**: extend the shared ingestion module `src/preprocessing.py`: a pure helper
  for the stamp→seconds conversion, integrated into `standardize_signal_frame` so there is
  exactly one ingestion entry point.
- **Rationale**: convention section 4 + ADR-1 make preprocessing the single shared stage
  for both standards engines; a second entry point in `app.py` would violate constitution
  principle I.
- **Alternatives considered**: app-side helper (rejected: UI-layer logic); separate new
  module (rejected: single-purpose module split for one function adds import surface).

## D2 — Time representation

- **Decision**: float64 seconds relative to the first stamp: `h*3600 + m*60 + s.mmm`.
- **Rationale**: the whole downstream pipeline (5 Hz filter, `da/dt`, impulse/dose
  geometry) already consumes numeric seconds in a `time` column; float64 keeps 1 ms
  precision far beyond the ~60k-row scale (error ≪ 1 µs at 15-minute spans).
- **Alternatives considered**: datetime objects (heavier, breaks downstream contract);
  integer milliseconds (changes the canonical `time` semantics everywhere).

## D3 — Stamp detection (numeric vs clock)

- **Decision**: per-value format detection, vectorized:
  1. numeric-looking values (already seconds) → passthrough unchanged (FR-005);
  2. strings matching the clock grammar `^HH:MM:SS(.mmm)?(\s+\d+)?$` → clock conversion
     (optional trailing counter tolerated and ignored — clarification session
     2026-09-19);
  3. anything else → explicit error naming the offending line (FR-006).
- **Rationale**: naive "try to parse as datetime first" would misinterpret numeric
  seconds like `3.2` as `00:00:03.2` — silently corrupting every existing dataset.
  Grammar-first detection is the only safe order.
- **Alternatives considered**: column dtype heuristic only (fails on files read as all
  strings); always-datetime (wrong, see above).

## D4 — Ordering, ties, jitter

- **Decision**: stable sort by converted time (file order breaks ties); no row is dropped,
  merged, or invented. Ties counted in metadata.
- **Rationale**: FR-003/FR-004; observed data has 0 ms duplicate steps and backwards
  jitter of a few ms — sorting restores order without data loss.
- **Alternatives considered**: deduplication (forbidden: data loss); resampling here
  (out of scope by spec).

## D5 — Rollover / large backward jump policy

- **Decision**: after sorting, any backwards jump larger than 60 s (default, overridable)
  aborts with an explicit error (rollover or foreign-file pattern).
- **Rationale**: observed serial artifacts top out at ≈1.2 s bursts; 60 s gives a wide
  margin while catching midnight rollovers (which look like ≈−hours). Refusing loudly
  protects verdicts; auto-adding 86 400 s would mask real corruption.
- **Alternatives considered**: silent rollover correction (masks errors); no check
  (wrong verdicts on foreign files).

## D6 — Malformed input behavior

- **Decision**: first malformed line aborts with an error containing the 1-based line
  number and the expected grammar; blank lines are skipped; structurally broken lines
  (missing fields) raise the same class of explicit error.
- **Rationale**: US3/FR-006 — bad files must never reach a verdict.
- **Alternatives considered**: skip-and-warn (silently biased timelines; rejected).

## D7 — Metadata contract

- **Decision**: extend the existing conversion metadata dict with: detected time format,
  input/output row counts, tied-stamp count, applied mapping (keys aligned with the
  existing metadata style).
- **Rationale**: constitution principle IV (traceability) with zero new surface —
  consumers already receive this dict.
- **Alternatives considered**: separate report object (new API surface for no benefit).

## D8 — Performance approach

- **Decision**: vectorized parsing (single regex pass + arithmetic), no per-row Python
  datetime parsing.
- **Rationale**: measured in the diagnostic: 48k lines parsed well under 1 s; SC-003
  (2 s budget) is achievable with margin.
- **Alternatives considered**: `pd.to_datetime` with format string (slower on 60k rows,
  and silently accepts multiple formats — weaker than the strict grammar).
