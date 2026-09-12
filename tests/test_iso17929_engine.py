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


# --- Task 3.2: impulse detection and cumulative dose (B.4 / B.15) ---------------



from src.config import (  # noqa: E402

    DOSE_TOLERANCE_GS,

    IMPULSE_MIN_AMPLITUDE_G,

    RECOVERY_THRESHOLD_G,
)
from src.iso17929_engine import Impulse, detect_impulses, compute_cumulative_dose  # noqa: E402





def _az_only(frame: pd.DataFrame) -> pd.DataFrame:

    return frame[[TIME, "az"]]





def test_trapezoid_area_matches_analytic():
    rate, amp, hold = 5.0, 2.0, 1.0
    from src.synthetic_gen import generate_trapezoid_pulse
    raw = generate_trapezoid_pulse(FS, 6.0, plateau_amplitude=amp,
                                   ramp_rate_g_per_s=rate, start_time=1.0,
                                   hold_time=hold, axis="az")
    impulses = detect_impulses(raw, axis="az")
    assert len(impulses) == 1
    imp = impulses[0]
    ramp = amp / rate
    analytic_area = amp * hold + amp * ramp  # rectangle + two half-triangles
    assert abs(imp.area_g_s - analytic_area) < 0.02
    assert abs(imp.peak_g - amp) < 1e-9
    assert abs(imp.mean_rise_rate_g_per_s - rate) < 0.1
    assert abs(imp.mean_fall_rate_g_per_s - rate) < 0.1
    assert imp.sign == 1


def test_detects_two_pulses_in_safe_family():
    build_all_datasets()
    frame = pd.read_csv("data/data_safe_family.csv")
    impulses = detect_impulses(frame, axis="az")
    assert len(impulses) == 2
    assert all(abs(i.peak_g - 1.5) < 0.1 for i in impulses)
    assert all(i.mean_rise_rate_g_per_s < 5.0 for i in impulses)


def test_negative_pulse_sign():
    from src.synthetic_gen import generate_trapezoid_pulse
    raw = generate_trapezoid_pulse(FS, 4.0, plateau_amplitude=1.0,
                                   ramp_rate_g_per_s=2.0, start_time=0.5,
                                   hold_time=0.8, axis="ax")
    raw["ax"] = -raw["ax"]
    impulses = detect_impulses(raw, axis="ax")
    assert len(impulses) == 1 and impulses[0].sign == -1


def test_subthreshold_stays_silent():
    t = np.arange(int(2 * FS)) / FS
    frame = pd.DataFrame({"time": t, "ax": 0.1 * np.ones_like(t),
                          "ay": np.zeros_like(t), "az": np.zeros_like(t)})
    assert detect_impulses(frame, axis="ax") == []


def test_configurable_threshold():
    t = np.arange(int(2 * FS)) / FS
    frame = pd.DataFrame({"time": t, "az": 0.3 * np.ones_like(t)})
    # 0.3 g is above the 0.2 g default: detected. Raise the gate: silent.
    assert len(detect_impulses(frame, axis="az", amplitude_threshold=0.2)) == 1
    assert detect_impulses(frame, axis="az", amplitude_threshold=0.5) == []


def test_impulse_defaults_use_config():
    assert IMPULSE_MIN_AMPLITUDE_G == 0.2
    assert RECOVERY_THRESHOLD_G == 2.0
    assert DOSE_TOLERANCE_GS == 11129.0


def test_dose_compliant_on_safe_family():
    build_all_datasets()
    frame = pd.read_csv("data/data_safe_family.csv")
    impulses = detect_impulses(frame, axis="az")
    dose = compute_cumulative_dose(impulses, recovery_signal=frame)
    assert dose["dose_compliant"] is True
    assert dose["recovery_compliant"] is True
    assert dose["recovery_violations"] == []
    assert dose["impulse_count"] == 2


def test_dose_recovery_violation_on_cumulative_dataset():
    build_all_datasets()
    frame = pd.read_csv("data/data_cumulative_dose_violation.csv")
    impulses = detect_impulses(frame, axis="az")
    assert len(impulses) == 3
    assert all(i.peak_g >= 5.0 for i in impulses)
    dose = compute_cumulative_dose(impulses, recovery_signal=frame)
    assert dose["dose_compliant"] is True  # area still within tolerance
    assert dose["recovery_compliant"] is False
    assert len(dose["recovery_violations"]) == 2
    for violation in dose["recovery_violations"]:
        assert violation["min_g"] > RECOVERY_THRESHOLD_G
        assert violation["clause"] == "ISO 17929 §B.15"


def test_dose_tolerance_override():
    build_all_datasets()
    frame = pd.read_csv("data/data_safe_family.csv")
    impulses = detect_impulses(frame, axis="az")
    tiny = compute_cumulative_dose(impulses, tolerance_g_s=0.01)
    assert tiny["dose_compliant"] is False
    assert tiny["tolerance_g_s"] == 0.01


def test_invalid_tolerance_and_axis():
    with pytest.raises(ValueError, match="tolerance_g_s"):
        compute_cumulative_dose([], tolerance_g_s=0.0)
    with pytest.raises(ValueError, match="not found"):
        detect_impulses(pd.DataFrame({"time": [0, 1]}), axis="az")
    with pytest.raises(ValueError, match="amplitude_threshold"):
        detect_impulses(pd.DataFrame({"time": np.arange(10), "az": np.ones(10)}),
                        axis="az", amplitude_threshold=-1.0)


def test_impulse_ids_are_sequential_and_traceable():
    build_all_datasets()
    frame = pd.read_csv("data/data_cumulative_dose_violation.csv")
    impulses = detect_impulses(frame, axis="az")
    assert [i.impulse_id for i in impulses] == [1, 2, 3]
    assert all(i.clause == "ISO 17929 §B.4" for i in impulses)


# --- Task 3.3: three-axis combined inequality (B.6 / B.16) -----------------------



from src.config import AXIS_PACKETS, COMBINED_EXCLUSION_S  # noqa: E402

from src.iso17929_engine import lookup_adm, evaluate_3d_combined_inequality  # noqa: E402





def test_lookup_adm_vertex_values_exact():
    assert lookup_adm("z", 1, 1.0) == 6.0
    assert lookup_adm("z", 1, 3.0) == 5.0
    assert lookup_adm("z", 1, 240.0) == 2.0
    assert lookup_adm("x", -1, 6.0) == 3.0
    assert lookup_adm("y", 1, 4.0) == 2.0


def test_lookup_adm_interpolates_and_clamps():
    # between +z vertices 1 s (6 g) and 3 s (5 g): midpoint 5.5
    assert lookup_adm("z", 1, 2.0) == pytest.approx(5.5)
    # below first vertex: packet maximum (6 g)
    assert lookup_adm("z", 1, 0.1) == 6.0
    # beyond last vertex: sustained value (2 g)
    assert lookup_adm("z", 1, 500.0) == 2.0
    assert lookup_adm("x", 1, 400.0) == 2.0
    assert lookup_adm("x", -1, 400.0) == 1.0


def test_lookup_adm_polarity_and_errors():
    assert lookup_adm("x", -1, 40.0) == 1.7
    assert lookup_adm("x", 1, 40.0) == pytest.approx(
        np.interp(40, [6, 12, 24, 300], [5, 4, 3, 2]))
    with pytest.raises(ValueError, match="axis must be"):
        lookup_adm("w", 1, 1.0)

def test_3d_violation_dataset_triaxial_fail_pairwise_pass():
    build_all_datasets()
    frame = pd.read_csv("data/data_3d_combined_violation.csv")
    result = evaluate_3d_combined_inequality(frame)
    assert result["compliant"] is False
    assert result["max_ratio_3d"] > 1.0
    assert len(result["triaxial_violations"]) >= 1
    for violation in result["triaxial_violations"]:
        assert violation["duration_s"] >= COMBINED_EXCLUSION_S
        assert violation["clause"] == "ISO 17929 §B.6"
    for pair, check in result["pairwise_results"].items():
        assert check["compliant"] is True, f"{pair} must stay under 1.0"
        assert check["max_ratio"] <= 1.0


def test_3d_safe_family_dataset_fully_compliant():
    build_all_datasets()
    frame = pd.read_csv("data/data_safe_family.csv")
    result = evaluate_3d_combined_inequality(frame)
    assert result["compliant"] is True
    assert result["triaxial_violations"] == []
    assert result["max_ratio_3d"] <= 1.0


def test_3d_duration_override_changes_verdict():
    """Same data with a long exposure override (stricter adm) must violate."""
    build_all_datasets()
    frame = pd.read_csv("data/data_3d_combined_violation.csv")
    relaxed = evaluate_3d_combined_inequality(frame, duration_s=1.0)
    strict = evaluate_3d_combined_inequality(frame, duration_s=300.0)
    assert strict["max_ratio_3d"] > relaxed["max_ratio_3d"]


def test_3d_transient_exclusion_under_200ms():
    """A spike violating the ratio for < 0.2 s is excluded (B.16)."""
    from src.synthetic_gen import generate_transient_spike
    # 6 g spike on +z (adm 6 g below the 1 s vertex) plus 1.4 g static ax:
    # ratio peaks at 1.078 > 1 but the >1 run lasts ~0.03 s < 0.2 s.
    frame = generate_transient_spike(FS, 2.0, peak_amplitude=6.0,
                                     spike_width_s=0.1, axis="az")
    frame["ax"] = 1.4
    result = evaluate_3d_combined_inequality(frame)
    assert result["triaxial_violations"] == []
    assert result["compliant"] is True
    assert len(result["excluded_transients"]) >= 1
    assert result["max_ratio_3d"] > 1.0  # exceeded, but excluded by duration


def test_3d_sample_ratios_frame_shape():
    build_all_datasets()
    frame = pd.read_csv("data/data_3d_combined_violation.csv")
    result = evaluate_3d_combined_inequality(frame)
    ratios = result["sample_ratios"]
    assert list(ratios.columns) == ["time", "ratio_xy", "ratio_xz", "ratio_yz", "ratio_3d"]
    assert len(ratios) == len(frame)
    assert np.allclose(ratios["time"], frame["time"])


# --- Task 3.4: RB classification and restraints (Table B.1) ----------------------



from src.iso17929_engine import RiskAssessment, classify_risk_level, extract_restraint_requirements  # noqa: E402





def test_ax_boundary_belongs_to_higher_level():
    # conservative reading: 3.0 g is RB-1, 2.9 g is RB-2
    assert classify_risk_level({"ax": 3.0}).overall_rb == "RB-1"
    assert classify_risk_level({"ax": 2.9}).overall_rb == "RB-2"
    assert classify_risk_level({"ax": 1.0}).overall_rb == "RB-2"
    assert classify_risk_level({"ax": 0.2}).overall_rb == "RB-3"
    assert classify_risk_level({"ax": 0.1}).overall_rb == "RB-4"


def test_az_boundaries():
    assert classify_risk_level({"+az": 5.0}).overall_rb == "RB-1"
    assert classify_risk_level({"+az": 4.9}).overall_rb == "RB-2"
    assert classify_risk_level({"+az": 3.0}).overall_rb == "RB-2"
    assert classify_risk_level({"+az": 1.9}).overall_rb == "RB-4"  # < 2 g
    assert classify_risk_level({"-az": 2.0}).overall_rb == "RB-1"
    assert classify_risk_level({"-az": 1.0}).overall_rb == "RB-2"
    assert classify_risk_level({"-az": 0.5}).overall_rb == "RB-3"


def test_worst_case_across_axes():
    peaks = {"ax": 1.2, "ay": 0.7, "+az": 3.2, "-az": 0.5}
    assessment = classify_risk_level(peaks)
    assert assessment.per_axis_levels["ax"] == "RB-2"
    assert assessment.per_axis_levels["ay"] == "RB-2"
    assert assessment.per_axis_levels["+az"] == "RB-2"
    assert assessment.per_axis_levels["-az"] == "RB-3"
    assert assessment.acceleration_rb == "RB-2"
    assert assessment.overall_rb == "RB-2"
    assert assessment.extremity == "medium"


def test_metadata_speed_raises_overall_level():
    peaks = {"ax": 1.2, "ay": 0.7, "+az": 3.2}  # RB-2 from acceleration
    baseline = classify_risk_level(peaks)
    assert baseline.acceleration_rb == "RB-2"
    assert baseline.overall_rb == "RB-2"
    assert "not provided" in baseline.metadata_status

    with_speed = classify_risk_level(peaks, device_meta={"speed_mps": 25.0})
    assert with_speed.acceleration_rb == "RB-2"
    assert with_speed.overall_rb == "RB-1"  # speed 25 m/s is RB-1
    assert "applied" in with_speed.metadata_status


def test_note3_testing_flag():
    assert classify_risk_level({"+az": 5.5}).test_required is True
    assert classify_risk_level({"+az": 3.5}).test_required is True
    assert classify_risk_level({"+az": 2.5}).test_required is False


def test_empty_peaks_raises():
    with pytest.raises(ValueError, match="at least one classified axis"):
        classify_risk_level({})


def test_restraints_headrest_rule_at_4g():
    rules = extract_restraint_requirements({"+az": 4.0, "ax": 0.0, "ay": 0.0, "-ax": 0.0})
    headrest = next(r for r in rules if r["condition"] == "+az >= 4")
    assert headrest["met"] is True
    assert "waist bar" in headrest["requirement"]
    assert headrest["clause"] == "ISO 17929 §B.11"
    # just below: not required
    rules = extract_restraint_requirements({"+az": 3.9, "ax": 0.0, "ay": 0.0, "-ax": 0.0})
    assert next(r for r in rules if r["condition"] == "+az >= 4")["met"] is False


def test_restraints_lap_bar_on_negative_ax():
    rules = extract_restraint_requirements({"-ax": 2.0, "ax": 0.0, "ay": 0.0, "+az": 0.0})
    lap = next(r for r in rules if r["condition"] == "-ax >= 2")
    assert lap["met"] is True


def test_restraints_duration_unknown_reported():
    rules = extract_restraint_requirements({"ay": 1.2})
    y_rule = next(r for r in rules if r["condition"].startswith("y > 0.5"))
    assert y_rule["met"] is False
    assert y_rule["note"] == "duration unknown; cannot evaluate"


def test_restraints_duration_evaluated_when_provided():
    rules = extract_restraint_requirements(
        {"ay": 1.2}, durations={"ay": 40.0}
    )
    y_rule = next(r for r in rules if r["condition"].startswith("y > 0.5"))
    assert y_rule["met"] is True  # 1.2 g > 1.0 for > 10 s


def test_rb_datasets_classification():
    build_all_datasets()
    dose = pd.read_csv("data/data_cumulative_dose_violation.csv")
    peaks = {"+az": float(dose["az"].max()), "-az": 0.0}
    assert classify_risk_level(peaks).overall_rb == "RB-1"  # 5 g +az

    safe = pd.read_csv("data/data_safe_family.csv")
    peaks = {"+az": float(safe["az"].max()), "-az": 0.0}
    assessment = classify_risk_level(peaks)
    assert assessment.overall_rb in ("RB-2", "RB-3")  # 1.57 g +az


def test_risk_assessment_is_dataclass():
    assessment = classify_risk_level({"ax": 3.5})
    assert isinstance(assessment, RiskAssessment)
    assert assessment.clause == "ISO 17929 Table B.1"
    assert assessment.extremity == "high"
