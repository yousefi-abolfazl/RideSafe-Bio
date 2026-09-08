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
