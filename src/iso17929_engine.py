"""ISO 17929 core evaluation engine — phase 3.

Task 3.1: jerk (da/dt) module. Central second-order difference on the
already-filtered 5 Hz signal (project convention 7); compliance evaluated
against JERK_LIMITS from config by device class. Pure data in/out, no UI.
"""

import numpy as np
import pandas as pd

from src.config import (
    ACCELERATION_COLUMNS,
    JERK_CLAUSE,
    JERK_LIMITS,
    TIME_COLUMN,
)


def calculate_jerk_rate(
    df: pd.DataFrame,
    sampling_rate: float,
    axes: tuple[str, ...] = ACCELERATION_COLUMNS,
) -> pd.DataFrame:
    """Time derivative da/dt of each filtered acceleration axis in g/s.

    np.gradient uses second-order central differences (zero phase shift);
    input must already be the 5 Hz-filtered signal (convention section 7).
    """
    if sampling_rate <= 0 or not np.isfinite(sampling_rate):
        raise ValueError(f"sampling_rate must be finite and positive, got {sampling_rate}")
    missing = [a for a in axes if a not in df.columns]
    if missing:
        raise ValueError(f"Acceleration columns missing for jerk: {missing}")
    if TIME_COLUMN not in df.columns:
        raise ValueError(f"Time column {TIME_COLUMN!r} missing from input frame")

    jerk = pd.DataFrame({TIME_COLUMN: df[TIME_COLUMN].to_numpy(dtype=float)})
    for axis in axes:
        jerk[f"jerk_{axis}"] = np.gradient(
            df[axis].to_numpy(dtype=float), 1.0 / float(sampling_rate)
        )
    return jerk


def evaluate_jerk_compliance(
    jerk_df: pd.DataFrame,
    axis: str = "az",
    device_class: str = "general",
    jerk_limits: dict[str, float] | None = None,
) -> dict:
    """Flag |jerk| intervals above the active device-class limit (B.5).

    Only |jerk| > limit is a violation: the 1 g/s minimum outer edge is a
    geometric packet property, not a safety floor (client clarification).
    """
    limits = dict(jerk_limits if jerk_limits is not None else JERK_LIMITS)
    if device_class not in limits:
        raise ValueError(
            f"device_class must be one of {sorted(limits)}, got {device_class!r}"
        )
    jerk_column = f"jerk_{axis}"
    if jerk_column not in jerk_df.columns:
        raise ValueError(f"Jerk column {jerk_column!r} not found in input frame")

    limit = float(limits[device_class])
    jerk = jerk_df[jerk_column].to_numpy(dtype=float)
    time = jerk_df[TIME_COLUMN].to_numpy(dtype=float)
    violation_mask = np.abs(jerk) > limit

    intervals = _contiguous_intervals(time, jerk, violation_mask)
    return {
        "compliant": not intervals,
        "device_class": device_class,
        "active_limit_g_per_s": limit,
        "axis": axis,
        "clause": JERK_CLAUSE,
        "max_jerk_g_per_s": float(np.abs(jerk).max()) if jerk.size else 0.0,
        "violation_intervals": intervals,
    }


def _contiguous_intervals(
    time: np.ndarray, jerk: np.ndarray, mask: np.ndarray
) -> list[dict]:
    """Group violation samples into contiguous [start_s, end_s] intervals."""
    intervals: list[dict] = []
    if not mask.any():
        return intervals
    edges = np.flatnonzero(np.diff(mask.astype(np.int8)) != 0) + 1
    starts = np.r_[0, edges]
    ends = np.r_[edges, mask.size]
    for s, e in zip(starts, ends):
        if not mask[s]:
            continue
        segment_jerk = np.abs(jerk[s:e])
        intervals.append(
            {
                "start_s": float(time[s]),
                "end_s": float(time[e - 1]),
                "peak_jerk_g_per_s": float(segment_jerk.max()),
                "clause": JERK_CLAUSE,
            }
        )
    return intervals
