"""Central configuration for standard-defined processing parameters.

Project convention section 6 (No Hardcoded Limits): every normative value
lives here with its reference; engine logic never embeds thresholds inline.
"""

# ISO 17842-1:2023 section I.2.1 / ASTM F2137: "4-pole, single pass,
# Butterworth low pass filter with 5 Hz cutoff".
# zero_phase=False is the standard-mandated behavior; True switches to a
# zero-phase cascade (sosfiltfilt) for exploratory analysis only (ADR-7).
FILTER_DEFAULTS = {
    "filter_kind": "butter",
    "order": 4,
    "cutoff_hz": 5.0,
    "zero_phase": False,
}

# Standard gravity: conversion factor from m/s^2 to g.
MS2_TO_G = 9.80665

# Canonical internal signal layout (post-ingestion column names).
TIME_COLUMN = "time"
ACCELERATION_COLUMNS = ("ax", "ay", "az")


# ISO 17929 section B.5: maximum recommended rise/fall rates of the trapezoid

# impulse envelope, per device extremity class.

JERK_LIMITS = {
    "family": 7.0,
    "general": 10.0,
    "extreme": 15.0,
}


# ISO 17929 section B.5: minimum outer-edge rate of the envelope. Geometric

# property of the packet only — gentler than 1 g/s is NOT a safety violation.

JERK_MIN_RATE = 1.0

JERK_CLAUSE = "ISO 17929 §B.5"


# ISO 17929 section B.4 / B.14: 0.2 g onset of dynamic perception and the

# personal-restraint floor; used as the impulse detection threshold (A4).

IMPULSE_MIN_AMPLITUDE_G = 0.2



# ISO 17929 section B.15: 5 g impulses may repeat only if the amplitude

# falls to <= 2 g between them.

RECOVERY_THRESHOLD_G = 2.0

# ISO 17929 section B.15: example cumulative tolerance area of the Z-axis

# tolerance line (Cobra roller-coaster profile) — reconstructed value (A7).

DOSE_TOLERANCE_GS = 11129.0

DOSE_CLAUSE = "ISO 17929 §B.15"


# ISO 17929 sections B.11-B.14: discrete acceleration packets per axis and

# polarity. Values are (duration_s, limit_g) pairs sorted ascending by

# duration; reconstructed from the WIP figures (accuracy ≈ ±0.1-0.2 g).

AXIS_PACKETS: dict[str, list[tuple[float, float]]] = {

    "+x": [(6, 5.0), (12, 4.0), (24, 3.0), (300, 2.0)],

    "-x": [(6, 3.0), (12, 2.5), (40, 1.7), (300, 1.0)],

    "y": [(4, 2.0), (40, 1.0), (300, 1.0)],

    "+z": [(1, 6.0), (3, 5.0), (6, 4.0), (12, 3.0), (240, 2.0)],

    "-z": [(0.2, 2.0), (4, 1.5)],

}



# ISO 17929 section B.16: combined combinations shorter than 0.2 s are

# excluded from verdicts (reported informationally only).

COMBINED_EXCLUSION_S = 0.2

COMBINED_CLAUSE = "ISO 17929 §B.6"
