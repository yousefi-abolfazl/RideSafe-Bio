"""Synthetic acceleration signal generators for edge-case test datasets.

Deterministic (seeded) waveform factories producing acceleration in g.
Pure computation: no UI imports, no clamping, no domain censoring.
Violation detection is the exclusive job of the evaluation engines.
"""

import numpy as np
import pandas as pd

from src.config import TIME_COLUMN, ACCELERATION_COLUMNS


def _new_frame(n_samples: int, fs: float) -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            TIME_COLUMN: np.arange(n_samples) / float(fs),
            **{axis: np.zeros(n_samples) for axis in ACCELERATION_COLUMNS},
        }
    )
    return frame


def _rng(seed: int | None) -> np.random.Generator:
    return np.random.default_rng(seed)


def _resolve_axis(axis: str) -> str:
    if axis not in ACCELERATION_COLUMNS:
        raise ValueError(
            f"axis must be one of {ACCELERATION_COLUMNS}, got {axis!r}"
        )
    return axis


def _validate_grid(fs: float, duration: float) -> int:
    if fs <= 0 or not np.isfinite(fs):
        raise ValueError(f"fs must be finite and positive, got {fs}")
    if duration <= 0 or not np.isfinite(duration):
        raise ValueError(f"duration must be finite and positive, got {duration}")
    return int(round(duration * fs))


def generate_sine_wave(
    fs: float,
    duration: float,
    amplitude: float,
    frequency: float,
    axis: str = "az",
    phase: float = 0.0,
    offset: float = 0.0,
    seed: int | None = None,
) -> pd.DataFrame:
    """Sinusoid (optionally DC-offset) in g on one axis; other axes zero."""
    n = _validate_grid(fs, duration)
    frame = _new_frame(n, fs)
    axis = _resolve_axis(axis)
    frame[axis] = offset + amplitude * np.sin(
        2 * np.pi * frequency * frame[TIME_COLUMN].to_numpy() + phase
    )
    return frame
def generate_trapezoid_pulse(
    fs: float,
    duration: float,
    plateau_amplitude: float,
    ramp_rate_g_per_s: float,
    axis: str = "az",
    start_time: float = 0.0,
    hold_time: float | None = None,
    seed: int | None = None,
) -> pd.DataFrame:
    """Trapezoidal impulse: linear rise, plateau, linear fall (ISO 17929 B.5).

    ramp_rate_g_per_s governs both rise and fall; hold_time defaults to the
    value that lets the fall return exactly to zero within the grid.
    """
    n = _validate_grid(fs, duration)
    if ramp_rate_g_per_s <= 0 or not np.isfinite(ramp_rate_g_per_s):
        raise ValueError(
            f"ramp_rate_g_per_s must be finite and positive, got {ramp_rate_g_per_s}"
        )
    if plateau_amplitude < 0:
        raise ValueError(
            f"plateau_amplitude must be non-negative, got {plateau_amplitude}"
        )
    if hold_time is None:
        ramp_time = plateau_amplitude / ramp_rate_g_per_s
        hold_time = max(duration - start_time - 2 * ramp_time, 0.0)
    if hold_time < 0:
        raise ValueError(f"hold_time must be non-negative, got {hold_time}")

    axis = _resolve_axis(axis)
    t = np.arange(n) / float(fs)
    rise_end = start_time + plateau_amplitude / ramp_rate_g_per_s
    plateau_end = rise_end + hold_time
    fall_end = plateau_end + plateau_amplitude / ramp_rate_g_per_s

    values = np.zeros(n)
    rising = (t > start_time) & (t <= rise_end)
    values[rising] = (t[rising] - start_time) * ramp_rate_g_per_s
    plateau = (t > rise_end) & (t <= plateau_end)
    values[plateau] = plateau_amplitude
    falling = (t > plateau_end) & (t <= fall_end)
    values[falling] = plateau_amplitude - (t[falling] - plateau_end) * ramp_rate_g_per_s

    frame = _new_frame(n, fs)
    frame[axis] = values
    return frame


def generate_transient_spike(
    fs: float,
    duration: float,
    peak_amplitude: float,
    spike_width_s: float,
    axis: str = "az",
    start_time: float = 0.0,
    seed: int | None = None,
) -> pd.DataFrame:
    """Short transient (typically < 200 ms: outside ISO 17842-1 scope, A12).

    Gaussian bell: peak at start_time + spike_width_s / 2.
    """
    n = _validate_grid(fs, duration)
    if peak_amplitude < 0:
        raise ValueError(f"peak_amplitude must be non-negative, got {peak_amplitude}")
    if spike_width_s <= 0 or not np.isfinite(spike_width_s):
        raise ValueError(f"spike_width_s must be finite and positive, got {spike_width_s}")

    axis = _resolve_axis(axis)
    t = np.arange(n) / float(fs)
    center = start_time + spike_width_s / 2.0
    sigma = spike_width_s / 6.0
    frame = _new_frame(n, fs)
    frame[axis] = peak_amplitude * np.exp(-((t - center) ** 2) / (2 * sigma ** 2))
    return frame


def add_gaussian_noise(
    df: pd.DataFrame,
    noise_std_g: float,
    seed: int | None = None,
) -> pd.DataFrame:
    """Additive zero-mean Gaussian noise on acceleration axes only."""
    if noise_std_g < 0 or not np.isfinite(noise_std_g):
        raise ValueError(f"noise_std_g must be finite and non-negative, got {noise_std_g}")
    out = df.copy()
    rng = _rng(seed)
    for axis in ACCELERATION_COLUMNS:
        if axis in out.columns:
            out[axis] = out[axis].to_numpy(dtype=float) + rng.normal(
                0.0, noise_std_g, len(out)
            )
    return out


def generate_composite_signal(
    fs: float,
    duration: float,
    components: list[tuple],
    seed: int | None = None,
) -> pd.DataFrame:
    """Linear superposition of component generators on a shared time grid.

    Each component is (generator_name, kwargs_dict). Generators receive a
    forced duration matching this call so grids align; their outputs sum
    with no clamping.
    """
    _validate_grid(fs, duration)
    generators = {
        "sine": generate_sine_wave,
        "trapezoid": generate_trapezoid_pulse,
        "spike": generate_transient_spike,
    }
    total = _new_frame(_validate_grid(fs, duration), fs)
    for entry in components:
        if len(entry) != 2:
            raise ValueError(
                "Each component must be (name, kwargs) tuple, got: "
                f"{entry!r}"
            )
        name, kwargs = entry
        if name not in generators:
            raise ValueError(
                f"Unknown generator {name!r}; available: {sorted(generators)}"
            )
        piece = generators[name](
            fs=fs,
            duration=duration,
            **kwargs,
        )
        for axis in ACCELERATION_COLUMNS:
            total[axis] = total[axis].to_numpy() + piece[axis].to_numpy()
    return total
