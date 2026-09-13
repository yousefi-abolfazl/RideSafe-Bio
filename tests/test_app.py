"""Unit tests for pure helpers in app.py (project convention 7)."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import (  # noqa: E402
    apply_axis_settings,
    build_column_mapping,
    detect_delimiter,
    load_uploaded_file,
)


def test_detect_delimiter_comma():
    assert detect_delimiter("t,ax,ay,az\n0,1,2,3\n1,4,5,6\n") == ","


def test_detect_delimiter_semicolon():
    assert detect_delimiter("t;ax;ay;az\n0;1;2;3\n1;4;5;6\n") == ";"


def test_detect_delimiter_tab():
    assert detect_delimiter("t\tax\tay\taz\n0\t1\t2\t3\n") == "\t"


def test_detect_delimiter_whitespace():
    assert detect_delimiter("t ax ay az\n0 1 2 3\n1 4 5 6\n") == r"\s+"


def test_build_column_mapping_direct():
    mapping = build_column_mapping({"time": "t", "ax": "acc_x",
                                    "ay": "acc_y", "az": "acc_z"})
    assert mapping == {"time": "t", "ax": "acc_x", "ay": "acc_y", "az": "acc_z"}


def test_build_column_mapping_rejects_unassigned():
    with pytest.raises(ValueError, match="incomplete"):
        build_column_mapping({"time": "t", "ax": "", "ay": "y", "az": "z"})


def test_apply_axis_inversion():
    frame = pd.DataFrame({"time": [0.0, 1.0], "ax": [1.0, -1.0],
                          "ay": [2.0, 2.0], "az": [0.0, 0.0]})
    out = apply_axis_settings(frame, {"ax": True, "ay": False, "az": False})
    assert np.allclose(out["ax"], [-1.0, 1.0])
    assert np.allclose(out["ay"], [2.0, 2.0])
    assert apply_axis_settings(frame, {"ax": False, "ay": False, "az": False})[
        "ax"
    ].equals(frame["ax"])


def test_load_uploaded_file_csv(tmp_path):
    import io

    path = tmp_path / "sample.csv"
    path.write_text("time,ax,ay,az\n0,1,2,3\n0.002,4,5,6\n")
    buffer = io.BytesIO(path.read_bytes())
    frame = load_uploaded_file(buffer, "sample.csv")
    assert list(frame.columns) == ["time", "ax", "ay", "az"]
    assert len(frame) == 2


def test_load_uploaded_file_semicolon_txt(tmp_path):
    import io

    path = tmp_path / "sample.txt"
    path.write_text("time;ax;ay;az\n0;1;2;3\n0.002;4;5;6\n")
    buffer = io.BytesIO(path.read_bytes())
    frame = load_uploaded_file(buffer, "sample.txt")
    assert list(frame.columns) == ["time", "ax", "ay", "az"]
