# Data Model: Add Timestamp Parser (002)

Feature spec: [spec.md](spec.md) · Decisions: [research.md](research.md)

## Entities

### RawLoggerRecording

One serial-logger recording as loaded from disk (pre-standardization).

| Aspect | Rule |
|---|---|
| Time source column | Named by the caller's column mapping (FR-002) — never hardcoded |
| Stamp values | `HH:MM:SS(.mmm)?(\s+\d+)?` clock strings — an optional trailing sample counter after whitespace is read and ignored (clarification 2026-09-19) — OR numeric seconds; mixing the two paths in one column is an error |
| Other columns | Sample counter / gyro / metadata — ignored by this stage, preserved untouched |
| Blank lines | Skipped, not counted as rows |
| Broken lines | Fewer fields than the file's own consistent layout → explicit error with line number |

### SecondsTimeline

Output time axis produced by the conversion.

| Aspect | Rule |
|---|---|
| Unit / origin | Seconds, relative to the first sample (first value = 0) (FR-001) |
| Precision | Milliseconds preserved (FR-001) |
| Monotonicity | Non-decreasing after stable sort; ties allowed and counted (FR-003, FR-004) |
| Cardinality | Exactly one timeline value per input data row — none dropped, none invented (FR-003) |
| Backwards jump | Sorted order may not hide a jump > rollover threshold (default 60 s) → refusal (FR-006) |
| Numeric passthrough | A column already in numeric seconds is returned bit-identical (FR-005) |

### ConversionMetadata

Traceability record attached to the existing standardization metadata (FR-007).

| Key | Content |
|---|---|
| time_format_detected | `"seconds"` or `"clock_hhmmss"` |
| rows_in / rows_out | Data rows before / after (blank lines excluded in both) |
| tied_stamps | Count of stamp values shared by ≥2 rows |
| rollover_threshold_s | The refusal threshold in effect |
| time_column | Which mapped column was converted |

## Validation Rules (requirement → rule)

| Requirement | Enforced rule |
|---|---|
| FR-001 | Converted values equal `h*3600 + m*60 + s.mmm − first`, ±1 ms |
| FR-002 | Function receives the mapping; grep-able absence of logger column names |
| FR-003 | `rows_out == rows_in`; stable tie order = file order |
| FR-004 | `diff(time) >= 0` for all samples post-sort; ties reported |
| FR-005 | Numeric input path: output equals input (identity) |
| FR-006 | Malformed/broken line → error with 1-based line number + expected grammar; backward jump > threshold → rollover error |
| FR-007 | Metadata keys present on every conversion |
| FR-008 | `src/` imports remain UI-free (verified by existing suite test) |
| FR-009 | Every rule above has a failing-first test; baseline 128 stays green |

## State Transitions

None — the conversion is a pure function over one column; no persisted state, no modes.
