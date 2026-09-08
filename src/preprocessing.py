"""Shared signal preprocessing for both standards engines (ADR-1).

Single implementation point for the standard 5 Hz Butterworth low-pass
filter (ISO 17842-1 section I.2.1 / ASTM F2137), sensor column mapping,
unit conversion and axis inversion. UI-free by project convention
section 4: imports only numpy/scipy/pandas, returns plain data structures.
"""

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


def standardize_signal_frame(
    df: pd.DataFrame,
    column_mapping: dict[str, str],
    sampling_rate: float | None = None,
    unit_conversions: dict[str, str] | None = None,
    axis_inversions: dict[str, bool] | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Map a raw logger frame onto the canonical time/ax/ay/az layout.

    Applies per-column unit conversion (e.g. "m/s2" -> "g") and per-axis
    sign inversion, then returns the standardized frame plus a metadata
    dict describing everything that was applied.
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

    if TIME_COLUMN in frame.columns:
        frame[TIME_COLUMN] = pd.to_numeric(frame[TIME_COLUMN], errors="raise")
        frame = frame.sort_values(TIME_COLUMN).reset_index(drop=True)
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
