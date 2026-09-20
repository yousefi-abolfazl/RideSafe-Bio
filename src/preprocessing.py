"""Shared signal preprocessing for both standards engines (ADR-1).

Single implementation point for the standard 5 Hz Butterworth low-pass
filter (ISO 17842-1 section I.2.1 / ASTM F2137), sensor column mapping,
unit conversion and axis inversion. UI-free by project convention
section 4: imports only numpy/scipy/pandas, returns plain data structures.
"""

import re

import numpy as np
import pandas as pd
from scipy.signal import butter, sosfilt, sosfiltfilt

from src.config import (
    ACCELERATION_COLUMNS,
    FILTER_DEFAULTS,
    MS2_TO_G,
    TIME_COLUMN,
)


def apply_butterworth_lowpass(
    df: pd.DataFrame,
    column_mapping: dict[str, str],
    sampling_rate: float,
    filter_params: dict | None = None,
) -> pd.DataFrame:
    """Apply the standard 4-pole 5 Hz Butterworth low-pass to accel columns.

    ISO 17842-1 section I.2.1 mandates a single-pass filter, so the default
    implementation is sosfilt (causal, one pass). zero_phase=True switches
    to the zero-phase cascade sosfiltfilt for exploratory work only (ADR-7).
    """
    params = dict(FILTER_DEFAULTS)
    if filter_params:
        params.update(filter_params)

    order = params["order"]
    cutoff = params["cutoff_hz"]
    if order < 1:
        raise ValueError(f"Filter order must be >= 1, got {order}")
    if cutoff <= 0:
        raise ValueError(f"Cutoff frequency must be positive, got {cutoff}")
    _validate_sampling_rate(sampling_rate)
    if cutoff >= sampling_rate / 2:
        raise ValueError(
            f"Cutoff {cutoff} Hz must be below Nyquist "
            f"{sampling_rate / 2} Hz for sampling_rate={sampling_rate}"
        )

    sos = butter(
        int(order),
        float(cutoff),
        btype="low",
        output="sos",
        fs=float(sampling_rate),
    )

    accel_columns = [c for c in column_mapping.values() if c in df.columns]
    accel_columns = [c for c in accel_columns if c != TIME_COLUMN]
    if not accel_columns:
        raise ValueError(
            "No acceleration columns found via column_mapping "
            f"(mapping={column_mapping}, columns={list(df.columns)})"
        )

    filtered = df.copy()
    method = "filtfilt" if params.get("zero_phase") else "sos"
    for column in accel_columns:
        values = filtered[column].to_numpy(dtype=float)
        if method == "filtfilt":
            values = sosfiltfilt(sos, values)
        else:
            values = sosfilt(sos, values)
        filtered[column] = values
    return filtered


def convert_clock_timestamps(
    stamps: pd.Series,
    rollover_threshold_s: float = 60.0,
) -> tuple[np.ndarray, dict]:
    """Convert a raw time column to seconds relative to the earliest sample.

    Per-value detection (research D3): finite numbers pass through as seconds;
    strings matching the clock grammar ``HH:MM:SS(.mmm)?( counter)?`` convert
    (the optional trailing sample counter is read and ignored — clarification
    2026-09-19); anything else raises with the 1-based line number. Returned
    values stay ALIGNED to the input row order, relative to the earliest
    sample; the caller sorts the frame (stable, file order breaks ties) to
    obtain the final non-decreasing timeline. A backwards jump beyond
    ``rollover_threshold_s`` in file order is refused (research D5).
    """
    if rollover_threshold_s <= 0 or not np.isfinite(rollover_threshold_s):
        raise ValueError(
            "rollover_threshold_s must be finite and positive, "
            f"got {rollover_threshold_s}"
        )
    raw = stamps.reset_index(drop=True)
    clock_pattern = re.compile(r"^(\d{1,2}):([0-5]\d):([0-5]\d)(?:\.(\d{1,3}))?"
                               r"(?:\s+\d+)?$")
    is_numeric = pd.to_numeric(raw, errors="coerce").notna().to_numpy()

    seconds = np.empty(len(raw), dtype=float)
    has_clock = False
    for index, value in enumerate(raw):
        if is_numeric[index]:
            seconds[index] = float(value)
            continue
        text = str(value).strip()
        match = clock_pattern.match(text)
        if match is None:
            raise ValueError(
                f"Unparseable time value at line {index + 1}: {value!r}; "
                "expected HH:MM:SS.mmm (optionally followed by a sample "
                "counter separated by whitespace) or numeric seconds"
            )
        hours, minutes, secs, frac = match.groups()
        seconds[index] = (
            int(hours) * 3600 + int(minutes) * 60 + int(secs)
            + (int(frac) / 10 ** len(frac) if frac else 0.0)
        )
        has_clock = True

    if is_numeric.any() and has_clock:
        first_numeric = int(np.flatnonzero(is_numeric)[0])
        first_clock = int(np.flatnonzero(~is_numeric)[0])
        raise ValueError(
            "Mixed time column: numeric seconds and clock stamps cannot be "
            f"combined (line {first_numeric + 1} is numeric "
            f"{raw.iloc[first_numeric]!r} but line {first_clock + 1} is "
            f"clock stamp {raw.iloc[first_clock]!r})"
        )

    # Rollover refusal (research D5): a large backwards jump in FILE order is
    # the rollover/foreign-data signature — sorted jitter was handled above.
    jumps = np.diff(seconds)
    worst = int(np.argmin(jumps)) if jumps.size else -1
    if worst >= 0 and jumps[worst] < -rollover_threshold_s:
        raise ValueError(
            f"Clock jumped backwards by {-jumps[worst]:.3f} s between lines "
            f"{worst + 1} and {worst + 2} ({seconds[worst]:.3f} -> "
            f"{seconds[worst + 1]:.3f}); rollover threshold is "
            f"{rollover_threshold_s} s"
        )

    seconds -= seconds.min()  # relative to the earliest sample (FR-001)

    ties = int(len(seconds) - np.unique(seconds).size)
    metadata = {
        "time_format_detected": "clock_hhmmss" if has_clock else "seconds",
        "rows_in": int(len(raw)),
        "rows_out": int(len(raw)),
        "tied_stamps": ties,
        "rollover_threshold_s": float(rollover_threshold_s),
    }
    return seconds, metadata

def standardize_signal_frame(
    df: pd.DataFrame,
    column_mapping: dict[str, str],
    sampling_rate: float | None = None,
    unit_conversions: dict[str, str] | None = None,
    axis_inversions: dict[str, bool] | None = None,
    rollover_threshold_s: float = 60.0,
) -> tuple[pd.DataFrame, dict]:
    """Map a raw logger frame onto the canonical time/ax/ay/az layout.

    Applies per-column unit conversion (e.g. "m/s2" -> "g") and per-axis
    sign inversion, then returns the standardized frame plus a metadata
    dict describing everything that was applied. A time column of clock
    stamps is converted to seconds first (see convert_clock_timestamps).
    """
    if column_mapping is None:
        raise ValueError("column_mapping must not be None; use {} for canonical input")
    missing = [m for m in column_mapping.values() if m not in df.columns]
    if missing:
        raise ValueError(
            f"column_mapping refers to missing columns: {missing}; "
            f"available: {list(df.columns)}"
        )
    frame = df.rename(columns={v: k for k, v in column_mapping.items()})

    time_metadata: dict = {}
    if TIME_COLUMN in frame.columns:
        seconds, time_metadata = convert_clock_timestamps(
            frame[TIME_COLUMN], rollover_threshold_s=rollover_threshold_s
        )
        frame[TIME_COLUMN] = seconds
        frame = frame.sort_values(TIME_COLUMN, kind="stable").reset_index(drop=True)
        if sampling_rate is None:
            sampling_rate = _estimate_sampling_rate(frame[TIME_COLUMN])
        applied_sampling_rate = float(sampling_rate)
    elif sampling_rate is not None:
        _validate_sampling_rate(sampling_rate)
        frame[TIME_COLUMN] = np.arange(len(frame)) / float(sampling_rate)
        applied_sampling_rate = float(sampling_rate)
    else:
        raise ValueError(
            "Neither a time column nor a sampling_rate was provided; "
            "cannot reconstruct the time base. Supply one of them."
        )

    conversions_applied: dict[str, str] = {}
    if unit_conversions:
        for axis, conversion in unit_conversions.items():
            if axis not in frame.columns:
                raise ValueError(f"Unit conversion target {axis!r} is not a column")
            if conversion == "m/s2_to_g":
                frame[axis] = frame[axis].to_numpy(dtype=float) / MS2_TO_G
                conversions_applied[axis] = conversion
            else:
                raise ValueError(f"Unsupported unit conversion: {conversion!r}")

    inversions_applied: dict[str, bool] = {}
    if axis_inversions:
        for axis, invert in axis_inversions.items():
            if axis not in frame.columns:
                raise ValueError(f"Inversion target {axis!r} is not a column")
            if invert:
                frame[axis] = -frame[axis].to_numpy(dtype=float)
            inversions_applied[axis] = bool(invert)

    standard_columns = [TIME_COLUMN, *ACCELERATION_COLUMNS]
    missing_standard = [c for c in standard_columns if c not in frame.columns]
    if missing_standard:
        raise ValueError(
            f"Standard columns missing after mapping: {missing_standard}"
        )

    metadata = {
        "sampling_rate": applied_sampling_rate,
        "mapped_columns": dict(column_mapping),
        "unit_conversions": conversions_applied,
        "axis_inversions": inversions_applied,
    }
    if time_metadata:
        metadata.update(time_metadata)
        metadata["time_column"] = column_mapping.get("time", TIME_COLUMN)
    return frame[standard_columns].reset_index(drop=True), metadata


def _estimate_sampling_rate(time_values: pd.Series) -> float:
    """Infer fs as inverse of the median time step (robust to dropouts)."""
    time = time_values.to_numpy(dtype=float)
    if time.size < 2:
        raise ValueError("Need at least 2 time samples to estimate fs")
    steps = np.diff(time)
    positive = steps[steps > 0]
    if positive.size == 0:
        raise ValueError("Time column is non-increasing; cannot estimate fs")
    median_step = float(np.median(positive))
    if median_step <= 0:
        raise ValueError("Median time step is not positive; cannot estimate fs")
    return 1.0 / median_step


def _validate_sampling_rate(sampling_rate: float) -> None:
    value = float(sampling_rate)
    if not np.isfinite(value) or value <= 0:
        raise ValueError(f"sampling_rate must be finite and positive, got {sampling_rate}")
