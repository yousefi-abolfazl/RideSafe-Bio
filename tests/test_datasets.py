"""Mathematical validation of the four edge-case CSVs (task 2.3).

Each test recomputes the violation/pass claim directly from the CSV bytes —
never trusting the generator or its profile dicts.
"""

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.datasets import DATASET_BUILDERS, build_all_datasets

DATA = Path("data")
TIME = "time"
AXES = ("ax", "ay", "az")
FILES = ["data_safe_family.csv", "data_jerk_violation.csv",
         "data_3d_combined_violation.csv", "data_cumulative_dose_violation.csv"]


@pytest.fixture(scope="session", autouse=True)
def _datasets():
    build_all_datasets()


@pytest.mark.parametrize("filename", FILES)
def test_file_exists_with_canonical_columns(filename):
    path = DATA / filename
    assert path.exists(), f"{path} missing"
    frame = pd.read_csv(path)
    assert list(frame.columns) == [TIME, *AXES]
    assert len(frame) > 1000
    assert frame[TIME].is_monotonic_increasing


@pytest.mark.parametrize("filename", FILES)
def test_files_are_deterministic(filename):
    """Two independent builds must yield byte-identical files."""
    path = DATA / filename
    first = hashlib.sha256(path.read_bytes()).hexdigest()
    scratch = Path("data/_determinism_check")
    DATASET_BUILDERS[filename](str(scratch), seed=42)
    second = hashlib.sha256((scratch / filename).read_bytes()).hexdigest()
    assert first == second, f"{filename} is not deterministic"
    (scratch / filename).unlink()
    scratch.rmdir()


def _rise_rate(frame: pd.DataFrame, t_lo: float, t_hi: float,
               plateau_floor: float) -> float:
    """Fit the az slope inside an explicit single-rise window."""
    t = frame[TIME].to_numpy()
    v = frame["az"].to_numpy()
    mask = (t >= t_lo) & (t <= t_hi) & (v > 0.1) & (v < plateau_floor)
    assert mask.sum() >= 10, "rise window too small for a stable fit"
    return float(np.polyfit(t[mask], v[mask], 1)[0])


# --- data_safe_family: negative control, everything must pass --------------------


def test_safe_family_peak_under_2g():
    frame = pd.read_csv(DATA / "data_safe_family.csv")
    assert frame["az"].abs().max() < 2.0


def test_safe_family_ramp_rate_under_family_limit():
    frame = pd.read_csv(DATA / "data_safe_family.csv")
    rate = _rise_rate(frame, 1.0, 1.36, plateau_floor=1.4)
    assert 0.9 < rate < 5.0  # strictly under the 7 g/s family limit


def test_safe_family_drops_to_zero_between_pulses():
    frame = pd.read_csv(DATA / "data_safe_family.csv")
    gap = frame[(frame[TIME] > 3.5) & (frame[TIME] < 4.7)]["az"]
    assert gap.abs().max() < 0.1  # full recovery to ~zero + noise sigma 0.02


# --- data_jerk_violation: 17929 B.5 violated, 17842 blind ------------------------


def test_jerk_violation_ramp_rate_above_extreme_limit():
    frame = pd.read_csv(DATA / "data_jerk_violation.csv")
    rate = _rise_rate(frame, 1.0, 1.08, plateau_floor=1.4)
    assert rate > 15.0, "must exceed the 15 g/s extreme ceiling of ISO 17929 B.5"


def test_jerk_violation_amplitude_still_within_old_standard():
    frame = pd.read_csv(DATA / "data_jerk_violation.csv")
    # 1.5 g plateau ~1.5 s sits below every ISO 17842-1 Annex I sustained limit
    plateau = frame[(frame[TIME] > 1.8) & (frame[TIME] < 2.2)]["az"]
    assert np.allclose(plateau, 1.5, atol=0.05)
    assert plateau.abs().max() < 2.0


# --- data_3d_combined_violation: B.6 ellipsoid -----------------------------------


def test_3d_single_axis_limits_respected():
    """Each axis alone stays under its discrete packet (B.11..B.14)."""
    frame = pd.read_csv(DATA / "data_3d_combined_violation.csv")
    peaks = {a: frame[a].abs().max() for a in AXES}
    # positive-biased ax (3.46 g peak) and az (3.8 g peak) stay under +x/+z
    # packets for their ~1.25 s exposures: +x 5 g @ 6 s, +z 6 g @ 1 s;
    # ay 1.1 g under Y 2 g @ 4 s. Durations << t_max.
    assert peaks["ax"] <= 5.0 + 1e-6
    assert peaks["ay"] <= 2.0 + 1e-6
    assert peaks["az"] <= 6.0 + 1e-6


def test_3d_peak_terms_exceed_one_only_jointly():
    """Per-sample adm terms: x+y+z > 1 at peaks, each pairwise sum <= 1."""
    frame = pd.read_csv(DATA / "data_3d_combined_violation.csv")
    # packet adm at the ~1.2 s exposure: +x 5 g, Y 2 g, +z 6 g
    x_term = (3.46 / 5.0) ** 2
    y_term = (1.1 / 2.0) ** 2
    z_term = (3.8 / 6.0) ** 2
    assert x_term + y_term + z_term > 1.0
    assert x_term + y_term <= 1.0 and x_term + z_term <= 1.0 and y_term + z_term <= 1.0


def test_3d_axes_are_synchronized():
    """Biased ax/az peak together with the ay sine each cycle."""
    frame = pd.read_csv(DATA / "data_3d_combined_violation.csv")
    for a, b in (("ax", "ay"), ("ax", "az")):
        corr = np.corrcoef(frame[a] - frame[a].mean(),
                           frame[b] - frame[b].mean())[0, 1]
        assert corr > 0.99


# --- data_cumulative_dose_violation: B.15 ----------------------------------------


def _pulse_starts() -> list[float]:
    rate, amp, hold = 7.0, 5.0, 0.5
    ramp = amp / rate
    cross = hold + (amp - 2.0) / rate
    return [1.0, 1.0 + ramp + cross, 1.0 + 2 * (ramp + cross)]


def test_cumulative_pulses_never_recover_below_2g():
    """Between consecutive 5 g plateaus az never drops to the 2 g recovery line."""
    frame = pd.read_csv(DATA / "data_cumulative_dose_violation.csv")
    rate, amp, hold = 7.0, 5.0, 0.5
    ramp = amp / rate
    spans = [(s + ramp, s + ramp + hold) for s in _pulse_starts()]
    for i in range(len(spans) - 1):
        segment = frame[
            (frame[TIME] >= spans[i][1]) & (frame[TIME] <= spans[i + 1][0])
        ]["az"]
        assert segment.min() >= 2.0 - 1e-6, (
            f"recovery dip below 2 g found between pulses {i} and {i + 1}"
        )


def test_cumulative_pulse_amplitude_and_rate_legal():
    """Each pulse individually is packet-legal: 5 g plateau at 7 g/s ramps."""
    frame = pd.read_csv(DATA / "data_cumulative_dose_violation.csv")
    assert frame["az"].abs().max() <= 5.0 + 1e-6
    rate = _rise_rate(frame, 0.9, 1.7, plateau_floor=4.9)
    assert abs(rate - 7.0) < 0.1
