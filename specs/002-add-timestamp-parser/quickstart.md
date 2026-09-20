# Quickstart Validation: Add Timestamp Parser (002)

End-to-end validation guide. Prerequisites, commands, and expected outcomes only —
implementation detail lives in [contracts/](contracts/) and the future `tasks.md`.

## Prerequisites

- Repository checked out on branch `002-add-timestamp-parser`
- Virtual environment present: `.venv/` (Python 3.10+; dev machine runs 3.14)
- Baseline state: full suite green (128 tests) before any change
- Reference recordings (untracked study data) at
  `Acceleration effects on passengers/Datasets_acc_safe/data/` — if absent, data-dependent
  tests skip with a clear message and the rest of the suite must still pass

## 1. Pin existing behavior (before implementation)

```bash
.venv/bin/python -m pytest tests/test_preprocessing.py -q
.venv/bin/python -m pytest tests/ -q
```

Expected: all green (numeric-passthrough test T1 included, currently trivially true).

## 2. Watch the new behavior fail first

```bash
.venv/bin/python -m pytest tests/test_preprocessing.py -q -k "clock or timestamp or stamp"
```

Expected: new tests fail (conversion not implemented yet); nothing else red.

## 3. Implement, then prove the contract

```bash
.venv/bin/python -m pytest tests/test_preprocessing.py -q
.venv/bin/python -m pytest tests/ -q
```

Expected: parser tests green; full suite 128 + new tests, zero regressions (SC-004).
A pre-existing UI-free check in the suite continues to enforce `src/` imports (FR-008).

## 4. Prove the real recordings load (SC-001/SC-002)

Load each of the seven reference recordings through the standard ingestion path with the
time column mapped from the file's first column (mapping supplied by the caller) and check:

- conversion metadata reports `time_format_detected="clock_hhmmss"`
- the fused `stamp counter` leading token loads without any pre-splitting step
  (clarification 2026-09-19)
- `rows_out == rows_in` on every file (no rows dropped or invented)
- timeline starts at 0 s and is non-decreasing

The seven paths are listed in [contracts/test-contract.md](contracts/test-contract.md).

## 5. Prove end-to-end evaluation (US1)

Feed one real recording (e.g. سورتمه first run) through standardize → filter → evaluation
engine. Expected: the full 17929 verdict chain completes with no error, matching the
behavior of the temporary diagnostic script (`scripts/evaluate_hekmat_samples.py`), which
is retired after this feature lands.

## 6. Prove refusal behavior (US3)

Craft three tiny bad files (unparseable stamp, missing fields, hourly backwards jump) and
confirm each raises the explicit line-numbered error instead of producing a verdict.

## 7. Performance smoke (SC-003)

Convert the largest reference file (≈48k rows): the conversion stage stays under 2 s and
the full pipeline under 5 s on the development laptop.
