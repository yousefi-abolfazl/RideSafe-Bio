"""Deterministic unit tests for src/preprocessing.py (project convention 7)."""

import numpy as np
import pandas as pd
import pytest

from src.config import MS2_TO_G
from src.preprocessing import (
    apply_butterworth_lowpass,
    standardize_signal_frame,
)

FS = 500.0
MAPPING = {"time": "t", "ax": "acc_x", "ay": "acc_y", "az": "acc_z"}


def make_frame(frequencies, amplitudes, duration=4.0, fs=FS, phase=0.0):
    t = np.arange(int(duration * fs)) / fs
    frequencies = np.broadcast_to(np.asarray(frequencies), (3,))
    amplitudes = np.broadcast_to(np.asarray(amplitudes), (3,))
    data = {"t": t}
    for column, frequency, amplitude in zip(
        ("acc_x", "acc_y", "acc_z"), frequencies, amplitudes
    ):
        data[column] = amplitude * np.sin(2 * np.pi * frequency * t + phase)
    return pd.DataFrame(data)
def mapped(df):
    # make_frame already emits canonical names; rename is a no-op passthrough
    # kept for future logger-style fixtures.
    return df.copy()
# --- apply_butterworth_lowpass -------------------------------------------------


def test_filter_preserves_signal_length():
    df = mapped(make_frame([1.0], [1.0, 1.0, 1.0]))
    out = apply_butterworth_lowpass(df, MAPPING, FS)
    assert len(out) == len(df)
    assert list(out.columns) == list(df.columns)


def test_step_response_converges_to_dc_gain():
    # A sustained step must asymptotically pass with unity gain (correct DC).
    n = int(20 * FS)
    df = pd.DataFrame(
        {
            "time": np.arange(n) / FS,
            "ax": np.ones(n),
            "ay": np.zeros(n),
            "az": np.zeros(n),
        }
    )
    mapping = {"time": "time", "ax": "ax"}
    out = apply_butterworth_lowpass(df, mapping, FS)
    tail = out["ax"].iloc[-50:]
    assert np.allclose(tail, 1.0, atol=1e-3)


def test_high_frequency_attenuated_near_zero():
    # 50 Hz tone must be strongly attenuated by the 5 Hz low-pass.
    df = mapped(make_frame([50.0], [1.0, 0.0, 0.0]))
    out = apply_butterworth_lowpass(df, MAPPING, FS)
    assert np.max(np.abs(out["acc_x"].to_numpy())) < 0.1


def test_low_frequency_passband_untouched():
    # 0.5 Hz tone lies far below cutoff: amplitude ~ preserved.
    df = make_frame([0.5], [1.0, 0.0, 0.0], duration=16.0)
    out = apply_butterworth_lowpass(df, MAPPING, FS)
    envelope = np.max(np.abs(out["acc_x"].to_numpy()))
    assert 0.9 < envelope <= 1.05


def test_zero_phase_option_returns_different_causal_result():
    rng = np.random.default_rng(42)
    df = make_frame([2.0], [1.0, 1.0, 1.0])
    df["acc_x"] += rng.normal(0, 0.05, len(df))
    causal = apply_butterworth_lowpass(df, MAPPING, FS)
    zero_phase = apply_butterworth_lowpass(df, MAPPING, FS, {"zero_phase": True})
    assert not np.allclose(causal["acc_x"], zero_phase["acc_x"])


def test_invalid_sampling_rate_raises():
    df = mapped(make_frame([1.0], [1.0, 1.0, 1.0]))
    with pytest.raises(ValueError):
        apply_butterworth_lowpass(df, MAPPING, 0.0)
    with pytest.raises(ValueError):
        apply_butterworth_lowpass(df, MAPPING, float("nan"))


def test_cutoff_above_nyquist_raises():
    df = mapped(make_frame([1.0], [1.0, 1.0, 1.0]))
    with pytest.raises(ValueError, match="Nyquist"):
        apply_butterworth_lowpass(df, MAPPING, FS, {"cutoff_hz": FS / 2})


# --- standardize_signal_frame --------------------------------------------------


def test_column_mapping_renames_columns():
    df = make_frame([1.0], [1.0, 1.0, 1.0], duration=1.0)
    out, meta = standardize_signal_frame(df, MAPPING, sampling_rate=FS)
    assert list(out.columns) == ["time", "ax", "ay", "az"]
    assert meta["mapped_columns"] == MAPPING
    assert meta["sampling_rate"] == FS


def test_unit_conversion_ms2_to_g():
    df = make_frame([1.0], [MS2_TO_G, MS2_TO_G, MS2_TO_G], duration=1.0)
    out, meta = standardize_signal_frame(
        df, MAPPING, sampling_rate=FS, unit_conversions={"ax": "m/s2_to_g"}
    )
    peak = np.max(np.abs(out["ax"].to_numpy()))
    assert abs(peak - 1.0) < 1e-9
    assert meta["unit_conversions"] == {"ax": "m/s2_to_g"}


def test_axis_inversion_flips_sign():
    df = make_frame([1.0], [2.0, 0.0, 0.0], duration=0.2)
    out, meta = standardize_signal_frame(
        df, MAPPING, sampling_rate=FS, axis_inversions={"ax": True, "ay": False}
    )
    assert np.allclose(out["ax"].to_numpy(), -2.0 * np.sin(
        2 * np.pi * 1.0 * out["time"].to_numpy()
    ))
    assert np.allclose(out["ay"], 0.0)
    assert meta["axis_inversions"] == {"ax": True, "ay": False}


def test_missing_time_column_with_fs_builds_synthetic_time():
    df = make_frame([1.0], [1.0, 1.0, 1.0], duration=1.0)
    canonical = df.rename(columns={v: k for k, v in MAPPING.items()}).drop(columns=["time"])
    out, meta = standardize_signal_frame(canonical, {}, sampling_rate=FS)
    expected = np.arange(len(canonical)) / FS
    assert np.allclose(out["time"].to_numpy(), expected)
    assert meta["sampling_rate"] == FS


def test_missing_time_and_fs_raises_value_error():
    df = make_frame([1.0], [1.0, 1.0, 1.0], duration=1.0)
    canonical = df.rename(columns={v: k for k, v in MAPPING.items()}).drop(columns=["time"])
    with pytest.raises(ValueError, match="Neither a time column nor a sampling_rate"):
        standardize_signal_frame(canonical, {}, sampling_rate=None)


def test_estimates_fs_from_time_column():
    df = make_frame([1.0], [1.0, 1.0, 1.0], duration=1.0)
    out, meta = standardize_signal_frame(df, MAPPING, sampling_rate=None)
    assert abs(meta["sampling_rate"] - FS) < 1e-9
    assert np.allclose(out["time"], df["t"].to_numpy())


def test_mapping_to_missing_columns_raises():
    df = make_frame([1.0], [1.0, 1.0, 1.0], duration=0.2)
    bad_mapping = {"time": "t", "ax": "does_not_exist"}
    with pytest.raises(ValueError, match="missing columns"):
        standardize_signal_frame(df, bad_mapping, sampling_rate=FS)

# --- clock-time ingestion (feature 002-add-timestamp-parser) ---------------------

from pathlib import Path  # noqa: E402

from src.iso17929_engine import (  # noqa: E402
    calculate_jerk_rate,
    evaluate_jerk_compliance,
)

DATA_ROOT = Path("Acceleration effects on passengers/Datasets_acc_safe/data")
REFERENCE_FILES = [
    DATA_ROOT / "ساختگی/simulated_unsafe_imu.txt",
    DATA_ROOT / "ساختگی/combined test self gen.txt",
    DATA_ROOT / "سورتمه/سری اول/serial_20250831_151156.txt",
    DATA_ROOT / "سورتمه/سری اول/serial_20250831_152128.txt",
    DATA_ROOT / "سورتمه/سری دوم/serial_20250831_154241.txt",
    DATA_ROOT / "صاعقه/serial_20250831_160601.txt",
    DATA_ROOT / "صاعقه/serial_20250831_160606.txt",
]
CANONICAL_MAPPING = {"time": "time", "ax": "ax", "ay": "ay", "az": "az"}
LOGGER_MAPPING = {"time": 0, "ax": 1, "ay": 2, "az": 3}

def _clock_frame(stamps):
    n = len(stamps)
    return pd.DataFrame(
        {
            "time": list(stamps),
            "ax": np.linspace(0.1, 0.5, n),
            "ay": np.zeros(n),
            "az": np.zeros(n),
        }
    )

def test_numeric_seconds_pass_through_unchanged():
    df = make_frame([1.0], [1.0, 1.0, 1.0], duration=1.0)
    out, _ = standardize_signal_frame(df, MAPPING, sampling_rate=FS)
    assert np.array_equal(out["time"].to_numpy(), df["t"].to_numpy())

def test_clock_stamps_convert_to_relative_seconds():
    from src.preprocessing import convert_clock_timestamps  # lands with T006

    stamps = [
        "16:06:01.213 12533899",
        "16:06:01.224 12533809",
        "16:06:01.238 12533819",
    ]
    values, meta = convert_clock_timestamps(pd.Series(stamps))
    assert np.allclose(values, [0.0, 0.011, 0.025], atol=1e-9)
    assert meta["time_format_detected"] == "clock_hhmmss"
    assert meta["rows_in"] == meta["rows_out"] == 3

def test_standardize_converts_clock_time_column():
    df = _clock_frame(["00:00:00.000 0", "00:00:00.020 1", "00:00:00.040 2"])
    out, meta = standardize_signal_frame(df, CANONICAL_MAPPING, sampling_rate=FS)
    assert np.allclose(out["time"].to_numpy(), [0.0, 0.02, 0.04])
    assert meta["time_format_detected"] == "clock_hhmmss"

def test_conversion_metadata_keys_on_both_paths():
    df = make_frame([1.0], [1.0, 1.0, 1.0], duration=1.0)
    _, numeric_meta = standardize_signal_frame(df, MAPPING, sampling_rate=FS)
    clock_meta = standardize_signal_frame(
        _clock_frame(["00:00:00.000 0", "00:00:00.020 1"]), CANONICAL_MAPPING,
        sampling_rate=FS,
    )[1]
    expected = {
        "time_format_detected", "rows_in", "rows_out", "tied_stamps",
        "rollover_threshold_s", "time_column",
    }
    for meta in (numeric_meta, clock_meta):
        assert expected <= meta.keys()
    assert numeric_meta["time_format_detected"] == "seconds"
    assert numeric_meta["time_column"] == "t"
    assert clock_meta["time_format_detected"] == "clock_hhmmss"
    assert clock_meta["time_column"] == "time"

def test_reference_recording_flows_through_filter_and_jerk():
    path = REFERENCE_FILES[2]  # سورتمه run 1
    if not path.exists():
        pytest.skip(f"reference data missing: {path}")
    raw = pd.read_csv(path, sep=",", header=None)
    standardized, meta = standardize_signal_frame(raw, LOGGER_MAPPING)
    assert meta["time_format_detected"] == "clock_hhmmss"
    fs = meta["sampling_rate"]
    filtered = apply_butterworth_lowpass(standardized, CANONICAL_MAPPING, fs)
    jerk = calculate_jerk_rate(filtered, fs)
    verdict = evaluate_jerk_compliance(jerk, axis="az", device_class="general")
    assert {"compliant", "violation_intervals", "clause"} <= verdict.keys()

# --- US2: timeline integrity on messy serial data -------------------------------

def test_unsorted_rows_restore_order_and_count():
    df = _clock_frame(["00:00:01.000 3", "00:00:00.000 1", "00:00:00.500 2"])
    out, meta = standardize_signal_frame(df, CANONICAL_MAPPING, sampling_rate=FS)
    assert meta["rows_out"] == 3
    assert np.all(np.diff(out["time"].to_numpy()) >= 0)
    assert np.allclose(out["time"].to_numpy(), [0.0, 0.5, 1.0])

def test_tied_stamps_kept_in_file_order():
    df = _clock_frame(["00:00:01.000 5", "00:00:01.000 6", "00:00:02.000 7"])
    out, meta = standardize_signal_frame(df, CANONICAL_MAPPING, sampling_rate=FS)
    assert len(out) == 3
    assert np.allclose(out["time"].to_numpy(), [0.0, 0.0, 1.0])
    assert meta["tied_stamps"] == 1
    assert np.all(np.diff(out["ax"].to_numpy()) > 0)  # stable: file order kept

def test_small_backwards_jitter_sorts_without_loss():
    df = _clock_frame(["00:00:02.000 2", "00:00:01.992 1"])
    out, meta = standardize_signal_frame(df, CANONICAL_MAPPING, sampling_rate=FS)
    assert meta["rows_in"] == meta["rows_out"] == 2
    assert np.allclose(out["time"].to_numpy(), [0.0, 0.008])

def test_reference_recordings_preserve_row_count():
    for path in REFERENCE_FILES:
        if not path.exists():
            pytest.skip(f"reference data missing: {DATA_ROOT}")
        raw = pd.read_csv(path, sep=",", header=None)
        out, meta = standardize_signal_frame(raw, LOGGER_MAPPING)
        assert meta["rows_in"] == meta["rows_out"] == len(raw), path.name
        assert np.all(np.diff(out["time"].to_numpy()) >= 0), path.name
        assert out["time"].iloc[0] == 0.0, path.name

# --- US3: loud refusals instead of wrong verdicts --------------------------------

def test_unparseable_stamp_error_names_line_and_grammar():
    from src.preprocessing import convert_clock_timestamps

    with pytest.raises(ValueError, match="line 2") as excinfo:
        convert_clock_timestamps(pd.Series(["00:00:01.000", "not-a-time"]))
    assert "HH:MM:SS" in str(excinfo.value)

def test_mixed_time_column_refused():
    from src.preprocessing import convert_clock_timestamps

    with pytest.raises(ValueError, match="[Mm]ixed"):
        convert_clock_timestamps(pd.Series(["0.002", "00:00:01.000"]))

def test_broken_stamp_error_names_line():
    df = _clock_frame(["00:00:01.000", "12:05", "00:00:02.000"])
    with pytest.raises(ValueError, match="line 2"):
        standardize_signal_frame(df, CANONICAL_MAPPING, sampling_rate=FS)

def test_rollover_refused_and_threshold_override_honored():
    from src.preprocessing import convert_clock_timestamps

    stamps = ["23:59:50.000 1", "00:00:10.000 2"]  # backwards jump ≈ −86380 s
    with pytest.raises(ValueError, match="rollover threshold is 60"):
        convert_clock_timestamps(pd.Series(stamps))
    values, meta = convert_clock_timestamps(
        pd.Series(stamps), rollover_threshold_s=1e5
    )
    assert np.allclose(np.sort(values), [0.0, 86380.0], atol=1e-6)
    assert values[0] > values[1]  # file order preserved, aligned to input rows
    assert meta["rows_out"] == 2

def test_invalid_rollover_threshold_raises():
    from src.preprocessing import convert_clock_timestamps

    with pytest.raises(ValueError, match="rollover_threshold_s"):
        convert_clock_timestamps(pd.Series(["00:00:01.000"]), rollover_threshold_s=0.0)

# --- Polish: conversion performance (SC-003) --------------------------------------

def test_conversion_of_largest_reference_file_under_two_seconds():
    from src.preprocessing import convert_clock_timestamps
    import time as time_module

    paths = [p for p in REFERENCE_FILES if p.exists()]
    if not paths:
        pytest.skip(f"reference data missing: {DATA_ROOT}")
    largest = max(paths, key=lambda p: p.stat().st_size)
    stamps = pd.read_csv(largest, sep=",", header=None)[0]
    start = time_module.perf_counter()
    values, meta = convert_clock_timestamps(stamps)
    elapsed = time_module.perf_counter() - start
    assert elapsed < 2.0, f"conversion took {elapsed:.3f} s"
    assert len(values) == len(stamps)
    assert meta["rows_out"] == len(stamps)
