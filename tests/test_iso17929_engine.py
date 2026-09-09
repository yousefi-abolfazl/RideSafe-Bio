"""Deterministic unit tests for src/iso17929_engine.py (task 3.1)."""

import numpy as np
import pandas as pd
import pytest

from src.config import JERK_CLAUSE, JERK_LIMITS
from src.datasets import build_all_datasets
from src.iso17929_engine import calculate_jerk_rate, evaluate_jerk_compliance
from src.preprocessing import apply_butterworth_lowpass

FS = 500.0
CANONICAL_MAPPING = {"time": "time", "ax": "ax", "ay": "ay", "az": "az"}


def _filtered(frame: pd.DataFrame) -> pd.DataFrame:
    return apply_butterworth_lowpass(frame, CANONICAL_MAPPING, FS)


# --- calculate_jerk_rate ---------------------------------------------------------


def test_sine_jerk_matches_analytic_derivative():
    amplitude, frequency = 2.0, 0.9
    t = np.arange(int(6 * FS)) / FS
    frame = pd.DataFrame(
        {"time": t, "ax": np.zeros_like(t),
         "ay": np.zeros_like(t),
         "az": amplitude * np.sin(2 * np.pi * frequency * t)}
    )
    jerk = calculate_jerk_rate(frame, FS)
    expected = amplitude * 2 * np.pi * frequency * np.cos(2 * np.pi * frequency * t)
    interior = slice(50, -50)  # avoid edge effects of the central difference
    error = np.max(np.abs(jerk["jerk_az"].to_numpy()[interior] - expected[interior]))
    relative = error / (amplitude * 2 * np.pi * frequency)
    assert relative < 0.01


def test_trapezoid_plateau_has_zero_jerk_and_rise_matches_rate():
    from src.synthetic_gen import generate_trapezoid_pulse

    frame = _filtered(
        generate_trapezoid_pulse(
            FS, 6.0, plateau_amplitude=1.5, ramp_rate_g_per_s=7.0,
            start_time=1.0, hold_time=1.5, axis="az",
        )
    )
    jerk = calculate_jerk_rate(frame, FS)
    t = jerk["time"].to_numpy()
    plateau = jerk[(t > 1.6) & (t < 2.3)]["jerk_az"].to_numpy()
    assert np.abs(plateau).max() < 0.5  # ~0 on the plateau (filter ringing small)
    # Single-pass Butterworth turns the linear ramp into an S-curve: the
    # instantaneous jerk peaks slightly above the nominal rate mid-rise and
    # decays at both ends. Assert the S-curve band, not a constant.
    rise = jerk[(t > 1.02) & (t < 1.34)]["jerk_az"].to_numpy()
    assert 5.5 < np.median(rise) <= 8.5
    assert rise.max() > 6.0  # genuinely ramps, not noise

def test_jerk_output_shape_and_columns():
    t = np.arange(1000) / FS
    frame = pd.DataFrame({"time": t, "ax": t, "ay": t, "az": t})
    jerk = calculate_jerk_rate(frame, FS)
    assert list(jerk.columns) == ["time", "jerk_ax", "jerk_ay", "jerk_az"]
    assert len(jerk) == len(frame)


def test_jerk_rejects_missing_columns_and_bad_fs():
    frame = pd.DataFrame({"time": np.arange(10), "ax": np.arange(10)})
    with pytest.raises(ValueError, match="missing"):
        calculate_jerk_rate(frame, FS)
    full = pd.DataFrame({"ax": np.arange(10), "ay": np.arange(10), "az": np.arange(10)})
    with pytest.raises(ValueError, match="Time column"):
        calculate_jerk_rate(full, FS)
    good = pd.DataFrame({"time": np.arange(10), "ax": np.arange(10),
                         "ay": np.arange(10), "az": np.arange(10)})
    with pytest.raises(ValueError, match="sampling_rate"):
        calculate_jerk_rate(good, 0.0)


# --- evaluate_jerk_compliance ----------------------------------------------------


def _engine_jerk(frame: pd.DataFrame) -> pd.DataFrame:
    return calculate_jerk_rate(_filtered(frame), FS)


def test_safe_family_dataset_is_compliant():
    build_all_datasets()
    frame = pd.read_csv("data/data_safe_family.csv")
    verdict = evaluate_jerk_compliance(_engine_jerk(frame), axis="az", device_class="family")
    assert verdict["compliant"] is True
    assert verdict["violation_intervals"] == []
    assert verdict["active_limit_g_per_s"] == JERK_LIMITS["family"]


def test_jerk_violation_dataset_flags_b5_violation():
    build_all_datasets()
    frame = pd.read_csv("data/data_jerk_violation.csv")
    verdict = evaluate_jerk_compliance(_engine_jerk(frame), axis="az", device_class="extreme")
    assert verdict["compliant"] is False
    assert len(verdict["violation_intervals"]) >= 2  # rise and fall both exceed
    assert verdict["violation_intervals"][0]["clause"] == JERK_CLAUSE
    assert verdict["violation_intervals"][0]["peak_jerk_g_per_s"] > 15.0


def test_jerk_violation_dataset_passes_under_wrong_class_is_impossible():
    """18 g/s must fail even the extreme class; but a 1.5 g/s ramp would pass."""
    build_all_datasets()
    frame = pd.read_csv("data/data_jerk_violation.csv")
    for device_class, limit in JERK_LIMITS.items():
        verdict = evaluate_jerk_compliance(_engine_jerk(frame), axis="az",
                                           device_class=device_class)
        assert verdict["compliant"] is False, f"{device_class} ({limit} g/s) must fail"


def test_gentle_signal_compliant_and_traceable():
    t = np.arange(int(3 * FS)) / FS
    frame = pd.DataFrame({"time": t, "ax": np.zeros_like(t), "ay": np.zeros_like(t),
                          "az": 0.5 * np.ones_like(t)})
    verdict = evaluate_jerk_compliance(calculate_jerk_rate(frame, FS), axis="az")
    assert verdict["compliant"] is True
    assert verdict["clause"] == "ISO 17929 §B.5"


def test_min_rate_is_not_a_violation():
    """Below-1-g/s gentle onset must NOT be flagged (client clarification)."""
    t = np.arange(int(3 * FS)) / FS
    frame = pd.DataFrame({"time": t, "ax": np.zeros_like(t), "ay": np.zeros_like(t),
                          "az": 0.3 * t / t.max()})
    verdict = evaluate_jerk_compliance(calculate_jerk_rate(frame, FS), axis="az",
                                       device_class="family")
    assert verdict["compliant"] is True


def test_invalid_device_class_raises():
    jerk = pd.DataFrame({"time": np.arange(10), "jerk_az": np.zeros(10)})
    with pytest.raises(ValueError, match="device_class"):
        evaluate_jerk_compliance(jerk, axis="az", device_class="kids")


def test_missing_jerk_column_raises():
    with pytest.raises(ValueError, match="not found"):
        evaluate_jerk_compliance(pd.DataFrame({"time": np.arange(10)}), axis="az")
