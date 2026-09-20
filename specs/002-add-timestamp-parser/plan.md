# Implementation Plan: Add Timestamp Parser (clock-time → seconds)

**Branch**: `002-add-timestamp-parser` | **Date**: 2026-09-19 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-add-timestamp-parser/spec.md`

## Summary

Extend the shared ingestion stage so a logger time column holding wall-clock stamps
(`HH:MM:SS.mmm`, as produced by engineer Hekmat's serial logger) is converted to a numeric
seconds timeline relative to the first sample — with deterministic ordering, preserved row
counts, explicit refusals for rollover/malformed data, and traceability metadata. Numeric
seconds input passes through unchanged. Resampling, gap splitting, and counter-derived
sampling rates stay out of scope. The conversion lives in the UI-agnostic core; the
dashboard consumes it through the existing column-mapping flow with no new dependencies.

## Technical Context

**Language/Version**: Python 3.10+ (development environment runs 3.14)

**Primary Dependencies**: NumPy, pandas (existing stack); SciPy untouched by this feature

**Storage**: N/A (file ingestion; no persistence added)

**Testing**: pytest (`tests/test_preprocessing.py` extended; baseline 128 tests must stay green)

**Target Platform**: Linux field laptop + Streamlit dashboard (existing runtime)

**Project Type**: computational library (`src/`) consumed by a dashboard (`app.py`)

**Performance Goals**: conversion of a 10-minute recording (≈60k rows) under 2 s; full
evaluate pipeline under 5 s end-to-end (spec SC-003). Diagnostic already parsed a 48k-line
file in well under 1 s, so the goal is validated as achievable.

**Constraints**: no UI/visualization imports in the core (constitution I); no sensor-specific
column names hardcoded (convention 5 / constitution V); millisecond precision preserved;
row counts preserved exactly; every existing behavior unchanged (numeric path).

**Scale/Scope**: single recordings up to ≈60k rows / ~15 minutes; seven reference files in
`Acceleration effects on passengers/Datasets_acc_safe/data/` (untracked study data).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design: **PASS** (see
post-design note below).*

| Principle | Gate | Status |
|---|---|---|
| I — UI-agnostic core | Conversion implemented in `src/preprocessing.py`; imports limited to numpy/pandas; rendering untouched | ✅ PASS (planned) |
| II — No hardcoded limits | No ISO-normative values introduced. The rollover threshold (60 s) and the stamp grammar are non-normative parser policies; they ship as documented function defaults overridable by argument, not as standard limits | ✅ PASS (justified) |
| III — Test-first with boundary datasets | Failing-first tests; numeric passthrough + seven reference recordings cover the boundary scenarios | ✅ PASS |
| IV — Rule-to-clause traceability | Conversion metadata (format, row counts, ties, mapping) recorded and surfaced; task_log entry required at implement time | ✅ PASS |
| V — Format-agnostic ingestion | Caller-provided column mapping; no hardcoded logger names; numeric input stays byte-compatible | ✅ PASS |

**Post-design re-check (after Phase 1)**: contracts keep the conversion inside
`src/preprocessing.py` with no new imports and no new config keys; `app.py` change limited
to routing the existing mapping through the same entry point. Gate remains **PASS**.
Clarification session 2026-09-19 (fused `stamp counter` token tolerated in the core,
ignored) is reflected in research.md D3, data-model.md, contracts/, and quickstart.md —
no gate impact: still zero app.py logic and zero normative values.

## Project Structure

### Documentation (this feature)

```text
specs/002-add-timestamp-parser/
├── plan.md              # This file
├── research.md          # Phase 0 output: decisions D1–D8
├── data-model.md        # Phase 1 output: entities + validation rules
├── quickstart.md        # Phase 1 output: runnable validation guide
├── contracts/           # Phase 1 output: api-contract.md, test-contract.md
└── tasks.md             # Phase 2 output (/speckit.tasks — not created here)
```

### Source Code (repository root)

```text
src/
├── preprocessing.py     # EXTENDED: clock-stamp → seconds helper + standardize integration
└── config.py            # unchanged (no normative values added)

tests/
└── test_preprocessing.py  # EXTENDED: failing-first parser tests

app.py                   # consumer only: existing mapping flow routes here; no logic added
scripts/
└── evaluate_hekmat_samples.py  # temporary behavioral reference; retired after landing
```

**Structure Decision**: single-project layout as-is; the feature extends the one shared
ingestion module instead of adding a new module (convention: single preprocessing point,
ADR-1/ADR-7 lineage). No new package, no new dependency.

## Complexity Tracking

No constitution violations to justify — table intentionally empty.
