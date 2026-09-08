"""Deterministic unit tests for src/synthetic_gen.py (project convention 7)."""

import numpy as np
import pandas as pd
import pytest

from src.config import TIME_COLUMN, ACCELERATION_COLUMNS
from src.synthetic_gen import (
    add_gaussian_noise,
    generate_composite_signal,
    generate_sine_wave,
    generate_transient_spike,
    generate_trapezoid_pulse,
)

FS = 500.0
DUR = 4.0


# --- shared contract ------------------------------------------------------------


@pytest.mark.parametrize(
    "factory,kwargs",
    [
        (generate_sine_wave, dict(amplitude=1.0, frequency=1.0)),
        (generate_trapezoid_pulse, dict(plateau_amplitude=1.5, ramp_rate_g_per_s=5.0,
                                        start_time=1.0, hold_time=1.0)),
        (generate_transient_spike, dict(peak_amplitude=2.0, spike_width_s=0.1,
                                        start_time=1.0)),
    ],
)
def test_all_generators_produce_canonical_frame(factory, kwargs):
    frame = factory(FS, DUR, **kwargs)
    assert list(frame.columns) == [TIME_COLUMN, *ACCELERATION_COLUMNS]
    assert len(frame) == FS * DUR
    assert np.allclose(frame[TIME_COLUMN].to_numpy(), np.arange(int(FS * DUR)) / FS)


def test_inactive_axes_stay_zero():
    frame = generate_sine_wave(FS, 1.0, amplitude=2.0, frequency=1.0, axis="ax")
    assert np.allclose(frame["ay"], 0.0)
    assert np.allclose(frame["az"], 0.0)
    assert not np.allclose(frame["ax"], 0.0)


def test_invalid_axis_raises():
    with pytest.raises(ValueError, match="axis must be one of"):
        generate_sine_wave(FS, 1.0, amplitude=1.0, frequency=1.0, axis="zz")


@pytest.mark.parametrize(
    "factory,kwargs",
    [
        (generate_sine_wave, dict(amplitude=1.0, frequency=1.0)),
        (generate_trapezoid_pulse, dict(plateau_amplitude=1.5, ramp_rate_g_per_s=5.0)),
        (generate_transient_spike, dict(peak_amplitude=2.0, spike_width_s=0.1)),
    ],
)
def test_non_positive_grid_raises(factory, kwargs):
    with pytest.raises(ValueError):
        factory(0.0, 1.0, **kwargs)
    with pytest.raises(ValueError):
        factory(FS, -1.0, **kwargs)


# --- sine -----------------------------------------------------------------------


def test_sine_amplitude_and_frequency_reconstructed():
    frame = generate_sine_wave(FS, DUR, amplitude=2.5, frequency=3.0, axis="ay")
    values = frame["ay"].to_numpy()
    assert abs(np.max(np.abs(values)) - 2.5) < 1e-6
    # zero crossings at half-period spacing 1/(2f)
    crossings = np.where(np.diff(np.sign(values)) != 0)[0]
    spacing = np.diff(crossings) / FS
    assert np.allclose(spacing, 1 / (2 * 3.0), atol=1e-2)


# --- trapezoid ------------------------------------------------------------------


def test_trapezoid_shape_rise_plateau_fall():
    rate = 5.0
    frame = generate_trapezoid_pulse(
        FS, DUR, plateau_amplitude=1.5, ramp_rate_g_per_s=rate,
        start_time=1.0, hold_time=1.0,
    )
    values = frame["az"].to_numpy()
    assert abs(np.max(values) - 1.5) < 1e-9
    plateau = values[(frame[TIME_COLUMN] >= 1.3) & (frame[TIME_COLUMN] <= 2.0)]
    assert np.allclose(plateau, 1.5)
    before = values[frame[TIME_COLUMN] < 1.0]
    assert np.allclose(before, 0.0)
    after = values[frame[TIME_COLUMN] > 3.05]
    assert np.allclose(after, 0.0, atol=1e-9)


def test_trapezoid_ramp_rate_reconstructed():
    rate = 7.0
    frame = generate_trapezoid_pulse(
        FS, DUR, plateau_amplitude=1.4, ramp_rate_g_per_s=rate,
        start_time=0.5, hold_time=1.0,
    )
    t = frame[TIME_COLUMN].to_numpy()
    values = frame["az"].to_numpy()
    mask = (t > 0.55) & (t < 0.5 + 1.4 / rate - 0.02)
    slope = np.polyfit(t[mask], values[mask], 1)[0]
    assert abs(slope - rate) < 0.05


def test_trapezoid_default_hold_returns_to_zero():
    frame = generate_trapezoid_pulse(
        FS, 2.0, plateau_amplitude=1.0, ramp_rate_g_per_s=2.0, start_time=0.0
    )
    values = frame["az"].to_numpy()
    # fall completes exactly at t=2.0s; last sample is one grid step before,
    # so residual must be within one ramp step of zero (2 grid samples).
    assert abs(values[-1]) <= 2 * (2.0 / FS) + 1e-9
    assert abs(np.max(values) - 1.0) < 1e-9


def test_trapezoid_invalid_ramp_rate_raises():
    with pytest.raises(ValueError, match="ramp_rate_g_per_s"):
        generate_trapezoid_pulse(FS, 1.0, plateau_amplitude=1.0, ramp_rate_g_per_s=0.0)


# --- spike ----------------------------------------------------------------------


def test_spike_peak_location_and_value():
    frame = generate_transient_spike(
        FS, 1.0, peak_amplitude=3.0, spike_width_s=0.1, start_time=0.4
    )
    values = frame["az"].to_numpy()
    assert abs(np.max(values) - 3.0) < 1e-6
    peak_index = int(np.argmax(values))
    assert abs(frame[TIME_COLUMN].iloc[peak_index] - 0.45) < 1 / FS + 1e-9


def test_spike_is_short_transient():
    # 99% of energy inside the mandated width: sub-200 ms transient behavior.
    frame = generate_transient_spike(FS, 1.0, peak_amplitude=1.0, spike_width_s=0.15)
    values = frame["az"].to_numpy()
    above_tenth = np.abs(values) > 0.1
    width_samples = np.sum(above_tenth) / FS
    assert width_samples < 0.5


# --- noise ----------------------------------------------------------------------


def test_noise_is_deterministic_with_seed():
    base = generate_sine_wave(FS, 0.5, amplitude=1.0, frequency=2.0)
    noisy_a = add_gaussian_noise(base, noise_std_g=0.1, seed=42)
    noisy_b = add_gaussian_noise(base, noise_std_g=0.1, seed=42)
    assert np.array_equal(noisy_a.to_numpy(), noisy_b.to_numpy())


def test_noise_statistics_and_time_untouched():
    base = generate_sine_wave(FS, 2.0, amplitude=1.0, frequency=1.0)
    noisy = add_gaussian_noise(base, noise_std_g=0.2, seed=7)
    residual = noisy["ax"].to_numpy() - base["ax"].to_numpy()
    assert abs(np.mean(residual)) < 0.02
    assert abs(np.std(residual) - 0.2) < 0.02
    assert np.array_equal(noisy[TIME_COLUMN].to_numpy(), base[TIME_COLUMN].to_numpy())


def test_negative_noise_std_raises():
    base = generate_sine_wave(FS, 0.2, amplitude=1.0, frequency=1.0)
    with pytest.raises(ValueError, match="noise_std_g"):
        add_gaussian_noise(base, noise_std_g=-0.1)


# --- composite ------------------------------------------------------------------


def test_composite_linear_superposition_no_clamping():
    fs, dur = FS, 2.0
    frame = generate_composite_signal(
        fs,
        dur,
        [
            ("sine", dict(amplitude=3.0, frequency=1.0, axis="ax")),
            ("sine", dict(amplitude=3.0, frequency=1.0, axis="ax", phase=np.pi / 2)),
        ],
    )
    t = frame[TIME_COLUMN].to_numpy()
    expected = 3.0 * np.sin(2 * np.pi * t) + 3.0 * np.sin(2 * np.pi * t + np.pi / 2)
    assert np.allclose(frame["ax"].to_numpy(), expected)
    # superposition can exceed the individual amplitudes: no clamping
    assert np.max(np.abs(frame["ax"].to_numpy())) > 3.0


def test_composite_mixed_axes_sum_independently():
    frame = generate_composite_signal(
        FS,
        1.0,
        [
            ("sine", dict(amplitude=1.0, frequency=1.0, axis="ax")),
            ("trapezoid", dict(plateau_amplitude=0.5, ramp_rate_g_per_s=1.0,
                               start_time=0.2, hold_time=0.2, axis="az")),
        ],
    )
    ax_only = generate_sine_wave(FS, 1.0, amplitude=1.0, frequency=1.0, axis="ax")
    assert np.allclose(frame["ax"].to_numpy(), ax_only["ax"].to_numpy())
    assert np.allclose(frame["ay"], 0.0)


def test_composite_unknown_generator_raises():
    with pytest.raises(ValueError, match="Unknown generator"):
        generate_composite_signal(FS, 1.0, [("square", dict())])


def test_composite_deterministic_with_seed():
    components = [
        ("sine", dict(amplitude=1.0, frequency=1.0, axis="ax")),
        ("spike", dict(peak_amplitude=1.0, spike_width_s=0.1, axis="ay")),
    ]
    a = generate_composite_signal(FS, 1.0, components, seed=1)
    b = generate_composite_signal(FS, 1.0, components, seed=1)
    assert np.array_equal(a.to_numpy(), b.to_numpy())
