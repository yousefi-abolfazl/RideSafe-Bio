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


# --- Task 4.2: plotly charts (structure + performance, no browser) ---------------



from src.datasets import build_all_datasets  # noqa: E402

from src.iso17929_engine import (  # noqa: E402

    calculate_jerk_rate,
    evaluate_3d_combined_inequality,
    evaluate_jerk_compliance,
)
from src.preprocessing import apply_butterworth_lowpass  # noqa: E402
from app import plot_3d_ellipsoid, plot_time_series  # noqa: E402



FS = 500.0
CANONICAL = {"time": "time", "ax": "ax", "ay": "ay", "az": "az"}



@pytest.fixture(scope="module")

def jerk_dataset_results():

    build_all_datasets()

    filtered = apply_butterworth_lowpass(
        pd.read_csv("data/data_jerk_violation.csv"), CANONICAL, FS
    )
    jerk = evaluate_jerk_compliance(
        calculate_jerk_rate(filtered, FS), axis="az", device_class="extreme"
    )
    combined = evaluate_3d_combined_inequality(filtered)
    combined["_adm_x"] = np.full(len(filtered), 5.0)
    combined["_adm_y"] = np.full(len(filtered), 2.0)
    combined["_adm_z"] = np.full(len(filtered), 6.0)
    return filtered, jerk, combined





def test_time_series_structure(jerk_dataset_results):

    filtered, jerk_verdict, combined = jerk_dataset_results

    fig = plot_time_series(filtered, jerk_verdict, combined)

    scatter_traces = [t for t in fig.data if t.type in ("scatter", "scattergl")]
    assert len(scatter_traces) == 3  # ax, ay, az

    shapes = list(fig.layout.shapes)
    assert len(shapes) == len(jerk_verdict["violation_intervals"]) \
        + len(combined["triaxial_violations"]) \
        + len(combined["excluded_transients"])





def test_time_series_vrects_on_jerk_dataset(jerk_dataset_results):

    filtered, jerk_verdict, combined = jerk_dataset_results

    fig = plot_time_series(filtered, jerk_verdict, combined)

    red_shapes = [s for s in fig.layout.shapes
                  if s.fillcolor == "rgba(255,0,0,0.15)"]
    assert len(red_shapes) >= 2  # rise + fall jerk violations
    for shape in red_shapes:
        assert shape.x0 < shape.x1





def test_3d_scatter_color_split(jerk_dataset_results):

    filtered, _, combined = jerk_dataset_results

    fig = plot_3d_ellipsoid(filtered, combined)

    scatters = [t for t in fig.data if t.type == "scatter3d"]

    assert len(scatters) == 2  # inside (safe) + outside (violation)

    assert scatters[0].name == "inside (safe)"

    assert scatters[1].name == "outside (violation)"

    mesh = [t for t in fig.data if t.type == "mesh3d"]

    assert len(mesh) == 1  # envelope surface





def test_3d_no_violation_points_on_safe_data():

    build_all_datasets()

    filtered = apply_butterworth_lowpass(
        pd.read_csv("data/data_safe_family.csv"), CANONICAL, FS

    )
    combined = evaluate_3d_combined_inequality(filtered)

    combined["_adm_x"] = np.full(len(filtered), 5.0)
    combined["_adm_y"] = np.full(len(filtered), 2.0)
    combined["_adm_z"] = np.full(len(filtered), 6.0)

    fig = plot_3d_ellipsoid(filtered, combined)

    inside, outside = fig.data[0], fig.data[1]

    assert len(inside.x) > 0
    assert len(outside.x) == 0  # safe dataset: nothing outside the envelope





def test_chart_render_time_under_one_second(jerk_dataset_results):

    import time

    filtered, jerk_verdict, combined = jerk_dataset_results

    start = time.perf_counter()
    plot_time_series(filtered, jerk_verdict, combined)
    plot_3d_ellipsoid(filtered, combined)

    elapsed = time.perf_counter() - start
    assert elapsed < 1.0, f"chart generation took {elapsed:.3f} s"


# --- Task 4.3: risk passport panel (badges + table) ------------------------------



from src.config import RB_BADGE_COLORS  # noqa: E402
from app import build_compliance_banner_html, build_per_axis_table, build_risk_badge_html  # noqa: E402



def test_risk_badge_html_contains_level_color_and_extremity():

    html = build_risk_badge_html("RB-1", "high", RB_BADGE_COLORS["RB-1"])

    assert "RB-1" in html and "extremity" in html

    assert RB_BADGE_COLORS["RB-1"] in html

    # red (FAIL color #b71c1c) must NOT appear in the classification badge

    assert "#b71c1c" not in html





def test_risk_badge_palette_distinct_from_fail_red():

    for level, color in RB_BADGE_COLORS.items():
        html = build_risk_badge_html(level, "x", color)
        assert color in html
        assert "#b71c1c" not in html  # FAIL-only color





def test_compliance_banner_pass_and_fail_variants():

    ok = build_compliance_banner_html(True)

    fail = build_compliance_banner_html(False)

    assert "PASS" in ok and "Compliant with ISO 17929" in ok

    assert "NON-COMPLIANT" in fail

    assert "#2e7d32" in ok and "#b71c1c" in fail  # green vs red





def test_per_axis_table_rows_and_fallback_color():
    table = build_per_axis_table({"+az": "RB-2", "ax": None, "-az": "RB-3"})
    assert list(table.columns) == ["Axis / Polarity", "Risk Level", "color"]
    assert len(table) == 3
    rb2_row = table[table["Axis / Polarity"] == "+az"].iloc[0]
    assert rb2_row["color"] == RB_BADGE_COLORS["RB-2"]
    none_row = table[table["Axis / Polarity"] == "ax"].iloc[0]
    assert none_row["Risk Level"] == "not evaluated"
    assert none_row["color"] == "#9e9e9e"  # gray fallback


# --- Task 4.4: export report builders --------------------------------------------



import json as _json  # noqa: E402

from app import build_report, build_text_report, report_file_stem  # noqa: E402





@pytest.fixture(scope="module")

def safe_results():

    build_all_datasets()

    raw = pd.read_csv("data/data_safe_family.csv")

    from app import CANONICAL, run_evaluation_pipeline

    return run_evaluation_pipeline(

        raw, CANONICAL, 500.0, None,

        {"ax": False, "ay": False, "az": False}, "family",

    )





def test_report_structure_required_keys(safe_results):

    report = build_report(safe_results)

    for key in ("report_type", "generated_at", "standard", "signal",
                "verdicts", "risk", "restraints"):

        assert key in report

    assert report["report_type"] == "ridesafe_bio_assessment"

    for key in ("jerk_b5", "dose_b15", "combined_b6"):

        assert key in report["verdicts"]

    assert report["risk"]["clause"] == "ISO 17929 Table B.1"





def test_report_is_json_serializable(safe_results):

    payload = _json.dumps(build_report(safe_results), ensure_ascii=False)

    assert "ridesafe_bio_assessment" in payload





def test_report_determinism_excluding_timestamp(safe_results):

    a = build_report(safe_results)

    b = build_report(safe_results)

    a.pop("generated_at"), b.pop("generated_at")

    assert a == b





def test_report_field_values_match_engine(safe_results):
    report = build_report(safe_results)
    assert report["risk"]["overall_rb"] == report["risk"]["acceleration_rb"]
    assert (
        report["verdicts"]["jerk_b5"]["compliant"]
        == safe_results["jerk_verdict"]["compliant"]
    )
    assert (
        report["verdicts"]["dose_b15"]["impulse_count"]
        == len(safe_results["impulses"])
    )





def test_text_report_contains_verdict_and_rb(safe_results):

    text = build_text_report(safe_results, source_name="data_safe_family.csv")

    assert "Inspection Report" in text

    assert "PASS — COMPLIANT" in text or "NON-COMPLIANT" in text

    assert "RB-" in text

    assert "Violation Traceability" in text





def test_text_report_flags_failure_on_violating_dataset():

    build_all_datasets()

    raw = pd.read_csv("data/data_jerk_violation.csv")

    from app import CANONICAL, run_evaluation_pipeline

    results = run_evaluation_pipeline(

        raw, CANONICAL, 500.0, None,

        {"ax": False, "ay": False, "az": False}, "extreme",

    )

    text = build_text_report(results, source_name="data_jerk_violation.csv")

    assert "NON-COMPLIANT" in text

    assert "FAIL] Jerk B.5" in text





def test_report_file_stem_format():

    import re

    assert re.fullmatch(r"ridesafe_report_\d{8}_\d{4}", report_file_stem())

def test_pipeline_surfaces_hard_braking_lap_bar():
    """Hard braking (ax impulses <= -2 g) must surface as a -ax polarity peak
    and activate the B.26 lap-bar restraint through the dashboard pipeline."""
    build_all_datasets()
    from src.synthetic_gen import generate_trapezoid_pulse
    raw = generate_trapezoid_pulse(
        FS, 6.0, plateau_amplitude=2.5, ramp_rate_g_per_s=5.0,
        start_time=1.0, hold_time=1.5, axis="ax",
    )
    raw["ax"] = -raw["ax"]
    from app import CANONICAL, run_evaluation_pipeline
    results = run_evaluation_pipeline(
        raw, CANONICAL, 500.0, None,
        {"ax": False, "ay": False, "az": False}, "general",
    )
    assert results["peaks"]["-ax"] >= 2.0
    assert results["peaks"]["+ax"] == 0.0
    lap = next(r for r in results["assessment"].restraints
               if r["condition"] == "-ax >= 2")
    assert lap["met"] is True
