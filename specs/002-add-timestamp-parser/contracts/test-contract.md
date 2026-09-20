# Test Contract: Add Timestamp Parser (002)

Framework: pytest, deterministic, isolated; failing-first per convention section 7 and
constitution principle III. Files: `tests/test_preprocessing.py` (extended).

## Test matrix (scenario → assertion → spec anchor)

| # | Scenario | Assertion | Anchor |
|---|---|---|---|
| T1 | Numeric-seconds column passthrough | output equals input; metadata `time_format_detected="seconds"` | FR-005, US1.3 |
| T2 | Clock column converted correctly | leading tokens `16:06:01.213 12533899` (fused counter) and bare `16:06:01.224` both convert → `0.000, 0.011, …` with ms precision; first value 0; counter ignored | FR-001, SC-002 |
| T3 | Unsorted input restored | shuffled rows → non-decreasing output; row count preserved | FR-003/004, US2.1 |
| T4 | Tied stamps kept | two rows with equal stamp → both present, file order, `tied_stamps == 1` | FR-003/004, US2.2 |
| T5 | Small backwards jitter sorted | −8 ms step case → non-decreasing, no row lost | FR-003, US2.1 |
| T6 | Rollover refused | backwards jump of hours → `ValueError` mentioning threshold | FR-006, US3.2 |
| T7 | Malformed stamp refused | garbage value at line N → `ValueError` containing line number + grammar | FR-006, US3.1 |
| T8 | Mixed column refused | numeric value beside clock value → `ValueError` | contract, US3 |
| T9 | Broken line refused | missing fields → error with line number | FR-006 |
| T10 | Downstream integration | converted frame flows through filter + engine (jerk/impulses/3D) without error on one reference recording | FR-008, US1.1 |
| T11 | Row-count preservation on reference data | all seven recordings: `rows_out == rows_in` (blank lines excluded) | FR-003, SC-002 |
| T12 | Existing suite regression | full suite 128/128 stays green | FR-009, SC-004 |

## Reference data for T2/T10/T11 (untracked study data)

`Acceleration effects on passengers/Datasets_acc_safe/data/`:
`ساختگی/simulated_unsafe_imu.txt`, `ساختگی/combined test self gen.txt`,
`سورتمه/سری اول/serial_20250831_151156.txt`, `سورتمه/سری اول/serial_20250831_152128.txt`,
`سورتمه/سری دوم/serial_20250831_154241.txt`, `صاعقه/serial_20250831_160601.txt`,
`صاعقه/serial_20250831_160606.txt`.

Tests that depend on the untracked study data must skip gracefully (clear skip message)
when the folder is absent so the suite stays green on a fresh clone.

## Performance check (SC-003)

Smoke assertion: converting the largest reference file (48k rows) stays under 2 s;
measured once per suite run, tolerant margin on slow field laptops (assert < 2 s).

## Failing-first protocol

T2 (or the integration twin T10) is written and observed failing before implementation;
the numeric passthrough T1 is written first to pin existing behavior, then the new
behavior tests, then implementation, then full-suite re-run (T12 last).
