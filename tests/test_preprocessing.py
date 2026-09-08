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
