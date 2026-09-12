"""ISO 17929 core evaluation engine — phase 3.


Task 3.1: jerk (da/dt) module. Task 3.2: impulse detection (rise/plateau/
fall segmentation, B.4) and cumulative dose evaluation (B.15). Central
second-order difference and packet-slope fits on the already-filtered
5 Hz signal (project convention 7). Pure data in/out, no UI.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.config import (
    ACCELERATION_COLUMNS,
    AXIS_PACKETS,
    COMBINED_CLAUSE,
    COMBINED_EXCLUSION_S,
    DOSE_CLAUSE,
    DOSE_TOLERANCE_GS,
    IMPULSE_MIN_AMPLITUDE_G,
    JERK_CLAUSE,
    JERK_LIMITS,
    RB_ACCELERATION_TABLE,
    RB_CLAUSE,
    RB_EXTREMITY_MAP,
    RB_SPEED_TABLE,
    RECOVERY_THRESHOLD_G,
    RESTRAINT_REQUIREMENTS,
    TIME_COLUMN,
)

# ISO 17929 section B.15 (example): impulses with peaks >= 5 g may repeat

# only under the recovery rule.

REPEATABLE_IMPULSE_FLOOR_G = 5.0


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




# --- Task 3.2: impulse detection and cumulative dose (B.4 / B.15) ---------------





@dataclass

class Impulse:

    """One acceleration impulse segmented into rise / plateau / fall (B.4)."""



    impulse_id: int

    axis: str

    sign: int  # +1 or -1: polarity of the peak

    start_s: float

    rise_end_s: float

    plateau_end_s: float

    end_s: float

    peak_g: float

    mean_rise_rate_g_per_s: float

    mean_fall_rate_g_per_s: float

    area_g_s: float  # unsigned area under |a| for this impulse

    clause: str = "ISO 17929 §B.4"





def detect_impulses(
    df: pd.DataFrame,
    axis: str = "az",
    amplitude_threshold: float = IMPULSE_MIN_AMPLITUDE_G,
    min_duration_s: float = 0.02,
) -> list[Impulse]:
    """Segment one acceleration axis into impulses (B.4 rise/plateau/fall).

    Gated on |a| > threshold. Gates shorter than min_duration_s are noise
    blips. Chained pulses that never drop below the threshold (B.15 dose
    pattern) are split at the |a| valleys between their plateau peaks.
    """
    if axis not in df.columns:
        raise ValueError(f"Axis column {axis!r} not found in input frame")
    if amplitude_threshold <= 0 or not np.isfinite(amplitude_threshold):
        raise ValueError(
            f"amplitude_threshold must be finite and positive, got {amplitude_threshold}"
        )
    time = df[TIME_COLUMN].to_numpy(dtype=float)
    values = df[axis].to_numpy(dtype=float)
    above = np.abs(values) > amplitude_threshold

    fs_step = float(np.median(np.diff(time)))
    min_samples = max(int(round(min_duration_s / fs_step)), 3)

    edges = np.flatnonzero(np.diff(above.astype(np.int8)) != 0) + 1
    bounds = np.r_[0, edges, above.size]
    gates: list[tuple[int, int]] = [
        (int(s), int(e)) for s, e in zip(bounds[:-1], bounds[1:])
        if above[s] and e - s >= min_samples
    ]

    impulses: list[Impulse] = []
    for gate_start, gate_end in gates:
        pieces = _split_at_valleys(
            time[gate_start:gate_end], values[gate_start:gate_end]
        )
        for piece_time, piece_values in pieces:
            impulses.append(
                _profile_impulse(len(impulses) + 1, axis, piece_time, piece_values)
            )
    return impulses


def _split_at_valleys(
    time: np.ndarray, values: np.ndarray
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Split a gate at |a| valleys when it chains several plateau peaks."""
    from scipy.signal import find_peaks

    magnitude = np.abs(values)
    peaks, _ = find_peaks(magnitude, height=REPEATABLE_IMPULSE_FLOOR_G * 0.6,
                          distance=max(len(magnitude) // 10, 5))
    if len(peaks) <= 1:
        return [(time, values)]
    cuts = [int(np.argmin(magnitude[a:b])) + a for a, b in zip(peaks[:-1], peaks[1:])]
    bounds = np.r_[0, cuts, magnitude.size]
    return [
        (time[bounds[k]:bounds[k + 1]], values[bounds[k]:bounds[k + 1]])
        for k in range(len(bounds) - 1)
    ]
def _profile_impulse(
    impulse_id: int, axis: str, time: np.ndarray, values: np.ndarray,
) -> Impulse:
    """Geometry of one gated segment: peak, phase boundaries, rates, area."""
    sign = 1 if values[np.argmax(np.abs(values))] >= 0 else -1
    magnitude = np.abs(values)
    peak_g = float(magnitude.max())
    half_level = 0.5 * peak_g

    above_half = magnitude > half_level
    plateau_idx = np.flatnonzero(above_half)
    rise_end_idx = plateau_idx[0]
    plateau_end_idx = plateau_idx[-1]

    rise_window = slice(0, rise_end_idx + 1)
    fall_window = slice(plateau_end_idx, magnitude.size)
    rise_rate = _slope(time[rise_window], magnitude[rise_window])
    fall_rate = abs(_slope(time[fall_window], magnitude[fall_window]))

    # unsigned trapezoidal area of |a| over the whole gated segment
    area = float(np.trapezoid(magnitude, time))
    return Impulse(
        impulse_id=impulse_id,
        axis=axis,
        sign=sign,
        start_s=float(time[0]),
        rise_end_s=float(time[rise_end_idx]),
        plateau_end_s=float(time[plateau_end_idx]),
        end_s=float(time[-1]),
        peak_g=peak_g,
        mean_rise_rate_g_per_s=float(rise_rate),
        mean_fall_rate_g_per_s=float(fall_rate),
        area_g_s=area,
    )


def _slope(time: np.ndarray, values: np.ndarray) -> float:
    if time.size < 2:
        return 0.0
    return float(np.polyfit(time, values, 1)[0])


def compute_cumulative_dose(
    impulses: list[Impulse],
    tolerance_g_s: float = DOSE_TOLERANCE_GS,
    recovery_threshold_g: float = RECOVERY_THRESHOLD_G,
    recovery_signal: pd.DataFrame | None = None,
) -> dict:
    """Cumulative dose per B.15: Σ impulse areas vs tolerance-line area.

    recovery_signal (optional, the axis frame) enables the inter-impulse
    recovery check: impulses >= 5 g may repeat only if the signal falls to
    <= recovery_threshold_g between consecutive peaks.
    """
    if tolerance_g_s <= 0 or not np.isfinite(tolerance_g_s):
        raise ValueError(f"tolerance_g_s must be finite and positive, got {tolerance_g_s}")

    total_dose = float(sum(imp.area_g_s for imp in impulses))
    result = {
        "total_dose_g_s": total_dose,
        "tolerance_g_s": float(tolerance_g_s),
        "dose_ratio": total_dose / float(tolerance_g_s),
        "dose_compliant": total_dose <= float(tolerance_g_s),
        "recovery_compliant": True,
        "recovery_violations": [],
        "impulse_count": len(impulses),
        "clause": DOSE_CLAUSE,
    }

    big = [imp for imp in impulses if imp.peak_g >= REPEATABLE_IMPULSE_FLOOR_G]
    if len(big) < 2 or recovery_signal is None:
        return result

    time = recovery_signal[TIME_COLUMN].to_numpy(dtype=float)
    values = recovery_signal[axis_column].to_numpy(dtype=float) \
        if (axis_column := f"jerk_{big[0].axis}") in recovery_signal.columns \
        else recovery_signal[big[0].axis].to_numpy(dtype=float)
    for prev, nxt in zip(big[:-1], big[1:]):
        # recovery window: from prev fall start to next impulse rise end
        window = (time >= prev.plateau_end_s) & (time <= nxt.rise_end_s)
        if window.any():
            minimum = float(np.abs(values[window]).min())
            if minimum > recovery_threshold_g:
                result["recovery_compliant"] = False
                result["recovery_violations"].append(
                    {
                        "between_ids": [prev.impulse_id, nxt.impulse_id],
                        "min_g": minimum,
                        "threshold_g": float(recovery_threshold_g),
                        "clause": DOSE_CLAUSE,
                    }
                )
    return result




# --- Task 3.3: combined multi-axis inequality (B.6, B.16) ------------------------





def lookup_adm(axis: str, polarity: int, duration_s: float) -> float:

    """Permissible acceleration adm (g) for an exposure duration (B.11-B.14).



    Linear interpolation between discrete packet vertices (ambiguity A1);

    below the first vertex the packet maximum applies; beyond the last the

    sustained value holds.
    """
    if axis not in ("x", "y", "z"):
        raise ValueError(f"axis must be 'x', 'y' or 'z', got {axis!r}")
    key = f"{'+' if polarity >= 0 else '-'}{axis}" if axis in ("x", "z") else "y"
    if key not in AXIS_PACKETS:
        raise ValueError(f"Unknown axis packet {key!r}; available: {sorted(AXIS_PACKETS)}")
    points = AXIS_PACKETS[key]
    times = [p[0] for p in points]
    limits = [p[1] for p in points]
    if duration_s < times[0]:
        return limits[0]
    if duration_s > times[-1]:
        return limits[-1]
    return float(np.interp(duration_s, times, limits))


def evaluate_3d_combined_inequality(
    df: pd.DataFrame,
    duration_s: float | None = None,
    exclusion_s: float = COMBINED_EXCLUSION_S,
) -> dict:
    """Per-sample 3D ellipsoid check (B.6) with pairwise breakdown (B.3-B.5).

    adm per sample uses the instantaneous polarity of ax/az (y symmetric) and
    a common exposure duration: explicit override, else the contiguous
    above-0.2 g span of each axis (ambiguity A6, conservative variant).
    Ratio>1 runs shorter than exclusion_s land in excluded_transients (B.16)
    and do not affect compliance.
    """
    for axis in ("ax", "ay", "az"):
        if axis not in df.columns:
            raise ValueError(f"Acceleration column {axis!r} missing for combined check")
    time = df[TIME_COLUMN].to_numpy(dtype=float)
    ax, ay, az = (df[c].to_numpy(dtype=float) for c in ("ax", "ay", "az"))

    exposure_x = _exposure(duration_s, np.abs(ax), time)
    exposure_y = _exposure(duration_s, np.abs(ay), time)
    exposure_z = _exposure(duration_s, np.abs(az), time)
    adm_x = np.array([lookup_adm("x", 1 if v >= 0 else -1, d)
                      for v, d in zip(ax, exposure_x)])
    adm_y = np.array([lookup_adm("y", 1, d) for d in exposure_y])
    adm_z = np.array([lookup_adm("z", 1 if v >= 0 else -1, d)
                      for v, d in zip(az, exposure_z)])

    ratio_xy = (ax / adm_x) ** 2 + (ay / adm_y) ** 2
    ratio_xz = (ax / adm_x) ** 2 + (az / adm_z) ** 2
    ratio_yz = (ay / adm_y) ** 2 + (az / adm_z) ** 2
    ratio_3d = ratio_xy + (az / adm_z) ** 2

    sample_ratios = pd.DataFrame(
        {"time": time, "ratio_xy": ratio_xy, "ratio_xz": ratio_xz,
         "ratio_yz": ratio_yz, "ratio_3d": ratio_3d}
    )

    triaxial_all = _ratio_intervals(time, ratio_3d)
    triaxial = [i for i in triaxial_all if i["duration_s"] >= exclusion_s]
    excluded = [i for i in triaxial_all if i["duration_s"] < exclusion_s]
    pairwise = {
        pair: {
            "max_ratio": float(r.max()),
            "compliant": not any(i["duration_s"] >= exclusion_s
                                 for i in _ratio_intervals(time, r)),
        }
        for pair, r in (("XY", ratio_xy), ("XZ", ratio_xz), ("YZ", ratio_yz))
    }
    return {
        "compliant": not triaxial and all(p["compliant"] for p in pairwise.values()),
        "max_ratio_3d": float(ratio_3d.max()),
        "triaxial_violations": triaxial,
        "excluded_transients": excluded,
        "pairwise_results": pairwise,
        "sample_ratios": sample_ratios,
        "clause": COMBINED_CLAUSE,
    }


def _exposure(
    duration_override: float | None, magnitude: np.ndarray, time: np.ndarray
) -> np.ndarray:
    """Per-sample exposure duration for adm lookup.

    Explicit override applies everywhere; otherwise the contiguous span above
    IMPULSE_MIN_AMPLITUDE_G that each sample belongs to (its impulse length).
    """
    if duration_override is not None:
        return np.full_like(magnitude, float(duration_override))
    above = magnitude > IMPULSE_MIN_AMPLITUDE_G
    spans = np.full_like(magnitude, float(time[-1] - time[0]))
    edges = np.flatnonzero(np.diff(above.astype(np.int8)) != 0) + 1
    bounds = np.r_[0, edges, magnitude.size]
    for s, e in zip(bounds[:-1], bounds[1:]):
        if above[s]:
            spans[s:e] = time[e - 1] - time[s]
    return spans




def _ratio_intervals(time: np.ndarray, ratios: np.ndarray) -> list[dict]:

    """Contiguous ratio > 1 intervals with their geometry (B.6)."""

    mask = ratios > 1.0

    intervals: list[dict] = []

    if not mask.any():
        return intervals

    edges = np.flatnonzero(np.diff(mask.astype(np.int8)) != 0) + 1

    starts = np.r_[0, edges]
    ends = np.r_[edges, mask.size]
    for s, e in zip(starts, ends):
        if not mask[s]:
            continue
        intervals.append(
            {
                "start_s": float(time[s]),
                "end_s": float(time[e - 1]),
                "duration_s": float(time[e - 1] - time[s]),
                "peak_ratio": float(ratios[s:e].max()),
                "clause": COMBINED_CLAUSE,
            }
        )
    return intervals




# --- Task 3.4: biomechanical risk classification (Table B.1) ---------------------





@dataclass

class RiskAssessment:

    """RB risk classification result (ISO 17929 Table B.1)."""



    acceleration_rb: str

    overall_rb: str

    extremity: str

    per_axis_levels: dict[str, str | None]

    metadata_status: str

    test_required: bool  # Note 3: RB-1/RB-2 require physical testing

    restraints: list[dict]

    clause: str = RB_CLAUSE





_RB_ORDER = ["RB-4", "RB-3", "RB-2", "RB-1"]

_NO_METADATA_MESSAGE = (

    "Speed/Height not provided; evaluated based on biomechanical acceleration only"

)





def _boundaries_level(
    value: float, bounds: dict[str, tuple[float, float]], axis_key: str = ""
) -> str:
    """Map a value onto [min, max) bands; upper edge belongs to higher level.

    -az has no numeric RB-4 band: RB-4 applies only when no negative -az
    excursion exists (peak == 0).
    """
    if axis_key == "-az" and value <= 0.0:
        return "RB-4"
    for rb in _RB_ORDER:
        if rb not in bounds:
            continue
        low, high = bounds[rb]
        if low <= value < high:
            return rb
    return "RB-1"  # value above every finite upper bound




def classify_risk_level(

    peaks: dict[str, float],

    device_meta: dict | None = None,

) -> RiskAssessment:

    """Classify the device into RB-1..RB-4 from peak accelerations (B.1).



    Worst-case reading: the final level is the most severe across all rows.
    device_meta may carry speed_mps / heights to add the kinematic rows.
    """
    per_axis: dict[str, str | None] = {}
    levels: list[str] = []

    for key, bounds in RB_ACCELERATION_TABLE.items():
        if key.startswith(("+", "-")):
            base_axis = key[1:]
        else:
            base_axis = key
        if key in peaks:
            level = _boundaries_level(float(peaks[key]), bounds)
        elif base_axis in peaks:
            level = _boundaries_level(float(peaks[base_axis]), bounds)
        else:
            level = None
        per_axis[key] = level
        if level is not None:
            levels.append(level)

    if not levels:
        raise ValueError("peaks must contain at least one classified axis value")

    acceleration_rb = max(levels, key=_RB_ORDER.index)
    overall_rb = acceleration_rb
    meta_used = False
    if device_meta:
        if "speed_mps" in device_meta and device_meta["speed_mps"] is not None:
            levels.append(
                _boundaries_level(float(device_meta["speed_mps"]), RB_SPEED_TABLE)
            )
            meta_used = True
        overall_rb = max(levels, key=_RB_ORDER.index)

    metadata_status = (
        "Speed/Height metadata applied to classification"
        if meta_used else _NO_METADATA_MESSAGE
    )
    return RiskAssessment(
        acceleration_rb=acceleration_rb,
        overall_rb=overall_rb,
        extremity=RB_EXTREMITY_MAP[overall_rb],
        per_axis_levels=per_axis,
        metadata_status=metadata_status,
        test_required=overall_rb in ("RB-1", "RB-2"),
        restraints=[],
    )


def extract_restraint_requirements(
    peaks: dict[str, float],
    durations: dict[str, float] | None = None,
) -> list[dict]:
    """Evaluate V11 restraint rules against peak amplitudes (B.11-B.14)."""
    durations = durations or {}
    results: list[dict] = []
    for rule in RESTRAINT_REQUIREMENTS:
        axis_key = rule["axis"]
        threshold = float(rule["threshold_g"])
        strict = rule.get("strict", False)
        peak = float(peaks.get(axis_key, 0.0))

        met = peak > threshold if strict else peak >= threshold
        duration_note = None
        if "duration_s" in rule:
            alt_threshold = float(rule.get("alt_threshold_g", threshold))
            alt_duration = float(rule.get("alt_duration_s", float("inf")))
            exposure = float(durations.get(axis_key, 0.0))
            duration_met = (
                (peak > threshold and exposure > float(rule["duration_s"]))
                or (peak > alt_threshold and exposure > alt_duration)
            )
            if peak >= threshold and exposure <= 0.0:
                met = False
                duration_note = "duration unknown; cannot evaluate"
            else:
                met = duration_met

        results.append(
            {
                "condition": rule["condition"],
                "requirement": rule["requirement"],
                "met": bool(met),
                "peak_g": peak,
                "clause": rule["clause"],
                **({"note": duration_note} if duration_note else {}),
            }
        )
    return results
