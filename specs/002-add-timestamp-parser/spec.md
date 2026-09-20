# Feature Specification: Add Timestamp Parser (clock-time → seconds)

**Feature Branch**: `002-add-timestamp-parser`

**Created**: 2026-09-19

**Status**: Draft

**Input**: User description: "برطرف کردن مشکل پردازش داده های مهندس حکمت. باید یک مرحله پیش پردازش داده اضافه کنیم که بتوان داده های مهندس رو در ستون زمان که به فرمت خاص هست رو به فرمت ثانیه درآورد."

## Clarifications

### Session 2026-09-19

- Q: Hekmat logger lines fuse the clock stamp and sample counter into one leading token (`16:06:01.213 12533899`); which layer separates them? → A: Option A — the core tolerates an optional trailing numeric counter after whitespace (`HH:MM:SS.mmm <counter>`); the counter is read and ignored, and `app.py` needs no new logic.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Inspector loads a Hekmat logger file without touching the time column (Priority: P1)

A field inspector receives a real serial-logger recording (سورتمه / صاعقه / ساختگی) whose
first column is a wall-clock stamp such as `16:06:01.213 12533899,0.108,0.029,-1.024,…`.
Today the standard ingestion path rejects it. With this feature the inspector loads the
file as-is, the clock stamps become a numeric seconds timeline relative to the first
sample, and the full acceleration evaluation runs end-to-end with no manual timestamp
editing and no spreadsheet pre-processing.

**Why this priority**: Without this conversion none of engineer Hekmat's recordings can be
evaluated at all; every downstream verdict is blocked. It is the single blocking gap
identified in the phase-5 diagnostic study.

**Independent Test**: Can be fully tested by feeding one real logger file through the
standard ingestion path and observing a numeric seconds axis plus a completed evaluation —
delivers the ability to assess real rides.

**Acceptance Scenarios**:

1. **Given** a logger file whose time column holds `HH:MM:SS.mmm` stamps, **When** the file
   is loaded through the standard ingestion path, **Then** the time axis is numeric seconds
   relative to the first sample and the acceleration evaluation completes without error.
2. **Given** the same file, **When** the converted timeline is inspected, **Then** stamp
   precision is preserved to the millisecond and the first sample sits at 0 s.
3. **Given** an existing numeric-seconds dataset (synthetic edge-case files), **When** it is
   loaded through the same path, **Then** its timeline passes through unchanged — zero
   behavior change for current users.

---

### User Story 2 - Engineer trusts the converted timeline on messy serial data (Priority: P2)

Serial logging jitters and drops: timestamps occasionally repeat (0 ms step) or jump
backwards by a few milliseconds, and lines can arrive out of order. The engineer needs a
deterministic rule set: order is restored by sorting on the original clock stamp, tied
stamps keep their file order, and no data row is ever dropped or invented — so the filter
and rate-of-change stages operate on a timeline whose integrity is provable, not assumed.

**Why this priority**: A silently corrupted timeline produces wrong safety verdicts; trust
in timeline integrity is the second-most valuable outcome after basic loading.

**Independent Test**: Can be fully tested by loading the recording known to contain
repeated and backward-stepping stamps and asserting the output timeline is non-decreasing
with an exactly preserved row count.

**Acceptance Scenarios**:

1. **Given** a recording containing out-of-order and repeated clock stamps, **When** it is
   converted, **Then** the output timeline is non-decreasing and every input data row maps
   to exactly one output row (none dropped, none fabricated).
2. **Given** a converted file, **When** metadata is inspected, **Then** it states the
   detected time format, input/output row counts, and how many tied stamps were kept.

---

### User Story 3 - Operator gets a clear refusal instead of a wrong verdict (Priority: P3)

When a time value cannot be understood (garbled text, wrong format) or the recording
crosses a boundary this stage does not support (e.g., a backwards jump of many seconds —
a clock rollover or a foreign file), the operator sees one explicit error naming the
offending line and the expected format, rather than a silently wrong evaluation.

**Why this priority**: Protects verdict trustworthiness at the edges; valuable but not
required for the primary loading workflow.

**Independent Test**: Can be fully tested by loading crafted bad files and asserting each
produces a specific, human-readable error instead of a verdict.

**Acceptance Scenarios**:

1. **Given** a file with an unparseable time value on line N, **When** it is loaded, **Then**
   the error names line N and states the expected `HH:MM:SS.mmm` format.
2. **Given** a file whose clock jumps backwards by far more than one sample period (clock
   rollover pattern), **When** it is loaded, **Then** the conversion refuses with an
   explicit rollover message rather than reordering or misinterpreting the data.

---

### Edge Cases

- What happens when a clock stamp carries a trailing sample counter after whitespace
  (`16:06:01.213 12533899`)? The token pair is accepted; the counter is read and ignored,
  and the tie/row-preservation rules are unaffected.
- What happens when the time column already holds numeric seconds? The value passes
  through unchanged; numeric input is never misread as a clock stamp.
- What happens when two lines share the exact same millisecond stamp? Both rows are kept,
  ordered by file position; the tie is reported in metadata.
- What happens when a stamp steps backwards by roughly one sample period (serial jitter of
  a few milliseconds)? Sorting restores order; the row count is unchanged.
- What happens when the stamp jumps backwards by minutes/hours (midnight rollover or a
  second day)? The conversion refuses with an explicit error; rollover support is out of
  scope for this stage.
- What happens when a line is blank or carries fewer fields than expected? Blank lines are
  skipped; structurally broken lines raise the explicit error of User Story 3.
- What happens when acceleration fields are non-numeric? The same explicit-error behavior
  applies; a bad file must never reach a verdict.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The ingestion stage MUST convert a wall-clock time column in
  `HH:MM:SS.mmm` format into numeric seconds relative to the first sample, preserving
  millisecond precision. A stamp token MAY carry an optional trailing sample counter
  separated by whitespace (`HH:MM:SS.mmm <counter>`); the counter is read and ignored.
- **FR-002**: The conversion MUST be format-agnostic: the caller names which source column
  carries the time stamp; no sensor-specific column name may be hardcoded (convention
  section 5 / constitution principle V).
- **FR-003**: The stage MUST order samples by their original clock stamp with a stable,
  deterministic tie-break, and MUST NOT drop, merge, or invent any data row.
- **FR-004**: The output timeline MUST be non-decreasing; repeated stamps are allowed but
  must be reported in conversion metadata.
- **FR-005**: The stage MUST accept numeric-seconds time columns unchanged so existing
  datasets and all current workflows behave exactly as before.
- **FR-006**: The stage MUST reject with an explicit, line-numbered error any unparseable
  time value, structurally broken line, or backwards clock jump larger than 60 s
  (rollover pattern), instead of producing a verdict.
- **FR-007**: The conversion MUST record traceability metadata: detected time format,
  input/output row counts, tied-stamp count, and the applied column mapping.
- **FR-008**: The implementation MUST live in the UI-agnostic computational core and MUST
  NOT import any presentation or visualization library (constitution principle I); the
  dashboard consumes it without new dependencies.
- **FR-009**: Every new behavior MUST be covered by deterministic tests written
  failing-first, and the full existing test suite MUST remain 100% green.

### Key Entities *(include if feature involves data)*

- **RawLoggerRecording**: one serial-logger file; a clock stamp column, an optional
  sample counter, and acceleration columns; may contain jitter, ties, and dropped bursts.
- **SecondsTimeline**: the converted, non-decreasing numeric time axis relative to the
  first sample, millisecond precision, one value per data row.
- **ConversionMetadata**: traceability record of the conversion — detected format, row
  counts in/out, tie count, column mapping — surfaced with every evaluation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the seven reference recordings (2 simulated + 3 سورتمه + 2 صاعقه)
  load through the standard ingestion path with zero manual timestamp editing.
- **SC-002**: On all seven reference recordings the converted timeline is non-decreasing
  with exactly zero rows dropped and zero rows invented, relative to the first sample.
- **SC-003**: Converting and evaluating a 10-minute recording (≈60,000 rows) completes in
  under 5 seconds end-to-end, with the conversion stage itself under 2 seconds.
- **SC-004**: Zero regressions: the existing 128-test baseline stays 100% green, with new
  tests added on top.
- **SC-005**: 100% of crafted malformed recordings produce the explicit line-numbered
  error of FR-006 — none reach a verdict.

## Assumptions

- Recordings are single-day and shorter than a clock rollover; a backwards jump larger
  than 60 s is treated as rollover/foreign data and refused (explicit error), not
  reinterpreted.
- Millisecond precision in the stamps is sufficient for 5 Hz-filtered analysis.
- The sample counter column of the real logger is metadata for this stage and is not
  required to build the seconds timeline.
- Uniform resampling, gap splitting, and sampling-rate derivation from the counter are
  explicitly OUT of scope for this feature; they remain follow-up ingestion work.
- Acceleration values stay in g; unit conversion remains the existing separate step.
- The temporary diagnostic script currently emulating this conversion remains the
  behavioral reference until this feature lands, and is retired afterwards.
- Governance: implementation follows the project constitution (UI-agnostic core, no
  hardcoded sensor names); task logging and failing-first tests are mandatory per the
  engineering conventions.
