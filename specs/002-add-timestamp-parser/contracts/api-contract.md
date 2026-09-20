# API Contract: Add Timestamp Parser (002)

Public surface of the ingestion stage. Consumers: `app.py` dashboard flow, tests,
`scripts/evaluate_hekmat_samples.py` (temporary). All names follow the project's English
self-explanatory convention.

## Extended entry point (existing function, backward-compatible behavior)

```python
standardize_signal_frame(
    df,                          # raw frame: time column may now be clock stamps
    column_mapping,              # {canonical: source}; unchanged meaning
    sampling_rate=None,
    unit_conversions=None,
    axis_inversions=None,
    rollover_threshold_s=60.0,   # NEW, optional parser policy (see plan Constitution Check)
) -> tuple[pd.DataFrame, dict]
```

### Behavior contract

| Input time column content | Behavior |
|---|---|
| Numeric seconds | Identity — returned unchanged; metadata `time_format_detected="seconds"` (existing behavior) |
| `HH:MM:SS(.mmm)?(\s+\d+)?` strings | Converted to float seconds relative to first stamp; stable sort by time; ties kept in file order; metadata `time_format_detected="clock_hhmmss"` (NEW). An optional trailing counter after whitespace is read and ignored (clarification 2026-09-19) |
| Mixed / malformed / broken | `ValueError` naming the 1-based line number and the expected grammar (NEW) |
| Backwards jump > `rollover_threshold_s` in file order (clock path) | `ValueError` — rollover refusal (NEW); jitter-level steps are sorted away |

### Invariants (all paths)

1. Row cardinality preserved: one output row per input data row; blank lines skipped.
2. Output timeline non-decreasing.
3. Metadata carries `time_format_detected`, `rows_in`, `rows_out`, `tied_stamps`,
   `rollover_threshold_s`, `time_column` (additions only — existing keys untouched).
4. No UI/visualization imports added to `src/`.
5. `sampling_rate` estimation continues to work on the converted seconds timeline.

## New pure helper (testable unit, used internally)

```python
def convert_clock_timestamps(
    stamps: pd.Series,           # raw time-column values (strings or numbers)
    rollover_threshold_s: float = 60.0,
) -> tuple[np.ndarray, dict]    # (seconds relative to first, per-rule metadata)
```

- Pure function: no I/O, no globals; raises `ValueError` with line-numbered messages.
- Grammar (strict): one-or-two-digit hours 00–23, two-digit minutes/seconds, optional
  `.` + 1–3 fractional digits. An optional trailing sample counter separated by
  whitespace (`HH:MM:SS.mmm <counter>`) is tolerated and ignored (clarification
  2026-09-19). Leading/trailing whitespace tolerated; inner whitespace within the stamp
  itself not.
- Detection: value parses as finite number → seconds path; matches grammar → clock path;
  otherwise → error. Per-value detection with column-level consistency check (a column
  mixing paths is an error).

## Error contract

| Condition | Message must contain |
|---|---|
| Unparseable stamp at line N | line number, expected `HH:MM:SS.mmm` grammar |
| Broken line (too few fields) | same as above (raised by the loader before this stage) |
| Rollover (backwards jump > threshold) | the threshold value and both offending stamps |
| Mixed numeric/clock column | both offending values |

## Out of contract (explicit non-goals)

Resampling, gap splitting, sampling-rate derivation from the counter, unit conversion
changes, any rendering concern.
