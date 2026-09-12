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


# ISO 17929 Table B.1: biomechanical risk classification by acceleration

# amplitude per axis/polarity. Bounds: [min, max) per level — the upper edge

# belongs to the higher risk level (client-approved conservative reading):

# e.g. ax = 3.0 g is RB-1, not RB-2.

RB_ACCELERATION_TABLE: dict[str, dict[str, tuple[float, float]]] = {

    "ax": {
        "RB-1": (3.0, float("inf")),
        "RB-2": (1.0, 3.0),
        "RB-3": (0.2, 1.0),
        "RB-4": (0.0, 0.2),
    },
    "ay": {
        "RB-1": (1.0, float("inf")),
        "RB-2": (0.5, 1.0),
        "RB-3": (0.2, 0.5),
        "RB-4": (0.0, 0.2),
    },
    "-az": {
        "RB-1": (2.0, float("inf")),
        "RB-2": (1.0, 2.0),
        "RB-3": (0.0, 1.0),
        # RB-4 (no negative excursion) is assigned only when the -az peak
        # equals zero; no numeric band can express it.
    },

    "+az": {

        "RB-1": (5.0, float("inf")),

        "RB-2": (3.0, 5.0),

        "RB-3": (2.0, 3.0),

        "RB-4": (0.0, 2.0),

    },


}



# ISO 17929 Table B.1 rows for relative speed (m/s) — optional metadata.

RB_SPEED_TABLE: dict[str, tuple[float, float]] = {

    "RB-1": (20.0, float("inf")),

    "RB-2": (10.0, 20.0),

    "RB-3": (3.0, 10.0),

    "RB-4": (0.0, 3.0),

}



# ISO 17929 Table B.1 extremity symbol per risk level.

RB_EXTREMITY_MAP = {

    "RB-1": "high",

    "RB-2": "medium",

    "RB-3": "low",

    "RB-4": "negligible",

}



# ISO 17929 B.11-B.14 (V11): restraint requirements triggered by amplitude

# (and duration where the clause demands it). Duration conditions evaluate

# only when exposure durations are supplied.

RESTRAINT_REQUIREMENTS: list[dict] = [

    {"condition": "+az >= 4", "axis": "+az", "threshold_g": 4.0,

     "requirement": "Head backrest + waist bar + shoulder harness",

     "clause": "ISO 17929 §B.11"},

    {"condition": "ax(+) >= 3", "axis": "+ax", "threshold_g": 3.0,

     "requirement": "Rear restraint (back support)",

     "clause": "ISO 17929 §B.24"},

    {"condition": "ax(|) > 1", "axis": "ax", "threshold_g": 1.0, "strict": True,

     "requirement": "Head support", "clause": "ISO 17929 §B.24"},

    {"condition": "-ax >= 2", "axis": "-ax", "threshold_g": 2.0,

     "requirement": "Lap bar (between thigh and pelvis)",

     "clause": "ISO 17929 §B.26"},

    {"condition": "y > 0.5 (30 s) or y > 1 (10 s)", "axis": "ay",

     "threshold_g": 0.5, "duration_s": 30.0, "alt_threshold_g": 1.0,

     "alt_duration_s": 10.0, "requirement": "Lap restraint + shoulder stop",

     "clause": "ISO 17929 §B.28"},

    {"condition": "y 0.2-0.5", "axis": "ay", "threshold_g": 0.2,

     "upper_g": 0.5, "requirement": "Passive safety (handrail/support)",

     "clause": "ISO 17929 §B.28"},

]



RB_CLAUSE = "ISO 17929 Table B.1"
