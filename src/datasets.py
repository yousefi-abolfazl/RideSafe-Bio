"""Builders for the four mandated edge-case datasets (task 2.3).

Each builder writes its CSV into data/ and returns a profile dict so tests
can assert violation/pass claims by direct recomputation. Deterministic:
seeded generators only; identical bytes on every run.
"""

import numpy as np
import pandas as pd

from src.synthetic_gen import (
    generate_composite_signal,
    generate_sine_wave,
    generate_trapezoid_pulse,
    add_gaussian_noise,
)

FS = 500.0
DEFAULT_SEED = 42
DATASET_BUILDERS = {}  # name -> builder function, populated below


def _register(name):
    def deco(fn):
        DATASET_BUILDERS[name] = fn
        return fn
    return deco


def _two_safe_pulses(duration: float = 8.0, seed: int = DEFAULT_SEED) -> pd.DataFrame:
    base = generate_composite_signal(
        FS,
        duration,
        [
            ("trapezoid", dict(plateau_amplitude=1.5, ramp_rate_g_per_s=4.0,
                               start_time=1.0, hold_time=1.5, axis="az")),
            ("trapezoid", dict(plateau_amplitude=1.5, ramp_rate_g_per_s=4.0,
                               start_time=5.0, hold_time=1.5, axis="az")),
        ],
        seed=seed,
    )
    return add_gaussian_noise(base, noise_std_g=0.02, seed=seed)


@_register("data_safe_family.csv")
def build_safe_family(output_dir: str = "data", seed: int = DEFAULT_SEED) -> dict:
    frame = _two_safe_pulses(seed=seed)
    path = _write(frame, output_dir, "data_safe_family.csv")
    return {
        "file": path,
        "peak_az_g": float(frame["az"].abs().max()),
        "ramp_rate_g_per_s": 4.0,
        "inter_pulse_min_az_g": float(
            frame.loc[(frame["time"] > 3.5) & (frame["time"] < 4.7), "az"].abs().min()
        ),
        "axes_peak_g": {a: float(frame[a].abs().max()) for a in ("ax", "ay", "az")},
    }


@_register("data_jerk_violation.csv")
def build_jerk_violation(output_dir: str = "data", seed: int = DEFAULT_SEED) -> dict:
    frame = generate_trapezoid_pulse(
        FS, 6.0, plateau_amplitude=1.5, ramp_rate_g_per_s=18.0,
        start_time=1.0, hold_time=1.5, axis="az", seed=seed,
    )
    path = _write(frame, output_dir, "data_jerk_violation.csv")
    return {
        "file": path,
        "peak_az_g": float(frame["az"].abs().max()),
        "ramp_rate_g_per_s": 18.0,
        "extreme_limit_g_per_s": 15.0,
    }


@_register("data_3d_combined_violation.csv")
def build_3d_combined_violation(output_dir: str = "data", seed: int = DEFAULT_SEED) -> dict:
    frame = generate_composite_signal(
        FS, 4.0,
        [
            ("sine", dict(amplitude=1.2, frequency=0.8, axis="ax")),
            ("sine", dict(amplitude=0.5, frequency=0.8, axis="ay")),
            ("sine", dict(amplitude=1.7, frequency=0.8, axis="az")),
        ],
        seed=seed,
    )
    path = _write(frame, output_dir, "data_3d_combined_violation.csv")
    return {
        "file": path,
        "peaks_g": {a: float(frame[a].abs().max()) for a in ("ax", "ay", "az")},
        "frequency_hz": 0.8,
    }


@_register("data_cumulative_dose_violation.csv")
def build_cumulative_dose_violation(output_dir: str = "data", seed: int = DEFAULT_SEED) -> dict:
    # B.15: 5 g impulses may repeat only if az falls to <= 2 g between them.
    # Pulse starts are chained to the 2 g crossing of the preceding fall:
    # fall crosses 2 g at hold + (amp-2)/rate after plateau start; starting the
    # next rise exactly there keeps az >= 2 g across the whole inter-pulse span.
    rate = 7.0
    amp = 5.0
    ramp = amp / rate
    hold = 0.5
    cross_2g = hold + (amp - 2.0) / rate  # fall start -> 2 g crossing
    starts = [1.0, 1.0 + ramp + cross_2g, 1.0 + 2 * (ramp + cross_2g)]
    frame = generate_composite_signal(
        FS, 12.0,
        [
            ("trapezoid", dict(plateau_amplitude=amp, ramp_rate_g_per_s=rate,
                               start_time=s, hold_time=hold, axis="az"))
            for s in starts
        ],
        seed=seed,
    )
    path = _write(frame, output_dir, "data_cumulative_dose_violation.csv")
    between = frame[(frame["time"] > starts[0] + ramp + hold)
                    & (frame["time"] < starts[-1] + ramp)]
    return {
        "file": path,
        "peak_az_g": float(frame["az"].abs().max()),
        "ramp_rate_g_per_s": rate,
        "inter_pulse_min_az_g": float(between["az"].min()),
        "recovery_threshold_g": 2.0,
        "pulse_starts_s": starts,
    }


def _write(frame: pd.DataFrame, output_dir: str, filename: str) -> str:
    from pathlib import Path

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / filename
    frame.to_csv(path, index=False, float_format="%.6f")
    return str(path)


def build_all_datasets(output_dir: str = "data", seed: int = DEFAULT_SEED) -> dict:
    """Build every registered dataset; returns name -> profile dict."""
    return {
        name: builder(output_dir, seed=seed)
        for name, builder in DATASET_BUILDERS.items()
    }
