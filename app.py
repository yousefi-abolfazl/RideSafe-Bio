"""RideSafe-Bio — Streamlit dashboard (phase 4).

Presentation layer only: all computation lives in src/ modules (project
convention section 4). UI language: English technical terminology.
State: st.session_state (client-approved).
Import-safe: the Streamlit script body runs under render_dashboard();
pure helpers stay importable for unit tests.
"""

import io
import json
from pathlib import Path


import numpy as np
import pandas as pd
import streamlit as st

from src.config import (
    ACCELERATION_COLUMNS,
    FILTER_DEFAULTS,
    JERK_LIMITS,
    RB_BADGE_COLORS,
    TIME_COLUMN,
)
from src.datasets import DATASET_BUILDERS
from src.iso17929_engine import (
    calculate_jerk_rate,
    classify_risk_level,
    compute_cumulative_dose,
    detect_impulses,
    evaluate_3d_combined_inequality,
    evaluate_jerk_compliance,
    extract_restraint_requirements,
)
from src.preprocessing import (
    apply_butterworth_lowpass,
    standardize_signal_frame,
)

st.set_page_config(page_title="RideSafe-Bio", page_icon="🎡", layout="wide")
CANONICAL = {"time": TIME_COLUMN, "ax": "ax", "ay": "ay", "az": "az"}

AXIS_GUIDE_PATH = Path(__file__).resolve().parent / "assets" / "axis_guide.svg"
AXIS_GUIDE_TITLE = "🧭 Axis Convention — how to read directions"
AXIS_GUIDE_FALLBACK_LINES = (
    "+X | Forward | pressed into backrest",
    "-X | Rearward / Braking | thrown forward vs restraint",
    "±Y (+Y / -Y) | Right / Left (symmetric) | pressed sideways",
    "+Z | Up | pressed into seat (heavier)",
    "-Z | Down | airtime / lift-off risk",
)
AXIS_GUIDE_CAPTION = (
    "Sensor is seat-mounted near the rider torso/heart. "
    "If the sensor is mounted reversed, use the Invert checkboxes "
    "in the sidebar — arrow meanings stay the same, "
    "only the signal sign flips."
)


def load_axis_guide_svg() -> str | None:
    """Read assets/axis_guide.svg; None when missing/unreadable."""
    try:
        return AXIS_GUIDE_PATH.read_text(encoding="utf-8")
    except OSError:
        return None


def build_axis_guide_fallback_markdown() -> str:
    """Text-only direction summary when the SVG asset is unavailable."""
    return "\n".join(f"- {line}" for line in AXIS_GUIDE_FALLBACK_LINES)


# --- pure helpers (unit-tested in tests/test_app.py) -----------------------------


def detect_delimiter(sample: str) -> str:
    """Pick the delimiter that yields the most consistent column count."""
    import re

    candidates = [(",", str.split), (";", str.split), ("\t", str.split),
                  (r"\s+", lambda line, _: re.split(r"\s+", line))]
    best, best_score = ",", 0
    for delim, splitter in candidates:
        counts = [
            len(splitter(line.strip(), delim))
            for line in sample.strip().splitlines()[:10]
            if line.strip()
        ]
        if not counts or min(counts) < 2:
            continue
        consistent = len(set(counts)) == 1
        score = int(consistent) * 1000 + max(counts)
        if score > best_score:
            best, best_score = delim, score
    return best


def suggest_default_mapping(columns: list[str]) -> dict[str, str]:
    """Guess canonical axis mapping from common logger column names."""
    lowered = [c.lower() for c in columns]
    return {
        "time": next((c for c, l in zip(columns, lowered) if l in ("time", "t")), "(none)"),
        "ax": next((c for c, l in zip(columns, lowered) if l in ("ax", "acc_x", "x")), "(none)"),
        "ay": next((c for c, l in zip(columns, lowered) if l in ("ay", "acc_y", "y")), "(none)"),
        "az": next((c for c, l in zip(columns, lowered) if l in ("az", "acc_z", "z")), "(none)"),
    }


def build_column_mapping(user_mapping: dict[str, str]) -> dict[str, str]:
    """Invert UI selection {canonical: source} for standardize_signal_frame."""
    mapping = {c: s for c, s in user_mapping.items() if s and s != "(none)"}
    missing = [c for c in ("time", "ax", "ay", "az") if c not in mapping]
    if missing:
        raise ValueError(f"Column mapping incomplete: {missing} not assigned")
    return mapping


def apply_axis_settings(frame: pd.DataFrame, invert: dict[str, bool]) -> pd.DataFrame:
    """Apply per-axis sign inversion checkboxes on the standardized frame."""
    out = frame.copy()
    for axis, flip in invert.items():
        if flip and axis in out.columns:
            out[axis] = -out[axis].to_numpy(dtype=float)
    return out


def build_risk_badge_html(level: str, extremity: str, color: str) -> str:
    """HTML for the big RB badge (client-approved palette)."""
    return (
        f'<div style="display:inline-flex;align-items:center;gap:14px;'
        f'padding:10px 22px;border-radius:12px;background:{color}1a;'
        f'border:2px solid {color};margin:4px 0;">'
        f'<span style="font-size:34px;font-weight:800;color:{color};">'
        f'{level}</span>'
        f'<span style="font-size:16px;font-weight:600;'
        f'text-transform:uppercase;letter-spacing:1px;color:{color};">'
        f'{extremity} extremity</span></div>'
    )


def build_compliance_banner_html(compliant: bool) -> str:
    """HTML for the overall PASS/FAIL banner (red reserved for FAIL)."""
    if compliant:
        return (
            '<div style="padding:14px 24px;border-radius:12px;'
            'background:#2e7d321a;border:2px solid #2e7d32;'
            'font-size:22px;font-weight:800;color:#2e7d32;margin:4px 0;">'
            '&#10004; PASS — Compliant with ISO 17929</div>'
        )
    return (
        '<div style="padding:14px 24px;border-radius:12px;'
        'background:#b71c1c1a;border:2px solid #b71c1c;'
        'font-size:22px;font-weight:800;color:#b71c1c;margin:4px 0;">'
        '&#10006; NON-COMPLIANT — ISO 17929 criteria violated</div>'
    )


def build_per_axis_table(levels: dict[str, str | None]) -> pd.DataFrame:
    """Per-axis classification rows with badge colors for conditional styling."""
    rows = []
    for axis, level in levels.items():
        rows.append(
            {
                "Axis / Polarity": axis,
                "Risk Level": level if level else "not evaluated",
                "color": RB_BADGE_COLORS.get(level, "#9e9e9e"),
            }
        )
    return pd.DataFrame(rows)


def build_report(results: dict) -> dict:
    """Structured JSON assessment report (technical passport source of truth)."""
    from datetime import datetime, timezone

    assessment: RiskAssessment = results["assessment"]
    jerk_verdict: dict = results["jerk_verdict"]
    dose: dict = results["dose"]
    combined: dict = results["combined"]
    filtered: pd.DataFrame = results["filtered"]

    return {
        "report_type": "ridesafe_bio_assessment",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "standard": "ISO/CD 17929:2026 (ISO 17842-1 prevails)",
        "signal": {
            "fs_hz": float(results["fs"]),
            "n_samples": int(len(filtered)),
            "duration_s": float(
                filtered[TIME_COLUMN].iloc[-1] - filtered[TIME_COLUMN].iloc[0]
            ),
            "unit": "g",
            "inversions": results["metadata"]["axis_inversions"],
            "mapped_columns": results["metadata"]["mapped_columns"],
        },
        "verdicts": {
            "jerk_b5": {
                "compliant": jerk_verdict["compliant"],
                "device_class": jerk_verdict["device_class"],
                "active_limit_g_per_s": jerk_verdict["active_limit_g_per_s"],
                "max_jerk_g_per_s": jerk_verdict["max_jerk_g_per_s"],
                "violations": jerk_verdict["violation_intervals"],
            },
            "dose_b15": {
                "dose_compliant": dose["dose_compliant"],
                "recovery_compliant": dose["recovery_compliant"],
                "total_dose_g_s": dose["total_dose_g_s"],
                "tolerance_g_s": dose["tolerance_g_s"],
                "impulse_count": dose["impulse_count"],
                "recovery_violations": dose["recovery_violations"],
            },
            "combined_b6": {
                "compliant": combined["compliant"],
                "max_ratio_3d": combined["max_ratio_3d"],
                "triaxial_violations": combined["triaxial_violations"],
                "excluded_transients": combined["excluded_transients"],
                "pairwise_results": combined["pairwise_results"],
            },
        },
        "risk": {
            "acceleration_rb": assessment.acceleration_rb,
            "overall_rb": assessment.overall_rb,
            "extremity": assessment.extremity,
            "per_axis_levels": assessment.per_axis_levels,
            "metadata_status": assessment.metadata_status,
            "test_required": assessment.test_required,
            "clause": assessment.clause,
        },
        "restraints": assessment.restraints,
    }


def build_text_report(results: dict, source_name: str = "signal") -> str:
    """One-page printable inspection summary (client-approved format)."""
    report = build_report(results)
    risk = report["risk"]
    verdicts = report["verdicts"]
    overall_pass = all(
        (verdicts["jerk_b5"]["compliant"],
         verdicts["dose_b15"]["dose_compliant"],
         verdicts["dose_b15"]["recovery_compliant"],
         verdicts["combined_b6"]["compliant"])
    )
    line = "-" * 62
    lines = [
        "=" * 62,
        "RideSafe-Bio — Acceleration Safety Inspection Report",
        f"Standard : {report['standard']}",
        f"Source   : {source_name}",
        f"Generated: {report['generated_at']}",
        line,
        f"Overall Verdict : "
        f"{'PASS — COMPLIANT' if overall_pass else 'NON-COMPLIANT'}",
        f"Risk Level      : {risk['overall_rb']}"
        f" ({risk['extremity'].upper()} extremity)",
        f"  acceleration_rb = {risk['acceleration_rb']}"
        f" | test_required = {risk['test_required']}",
        f"  {risk['metadata_status']}",
        line,
        "Evaluation Criteria:",
        f"  [{'PASS' if verdicts['jerk_b5']['compliant'] else 'FAIL'}] Jerk B.5"
        f" — max {verdicts['jerk_b5']['max_jerk_g_per_s']:.2f} g/s"
        f" (limit {verdicts['jerk_b5']['active_limit_g_per_s']},"
        f" {verdicts['jerk_b5']['device_class']})",
        f"  [{'PASS' if verdicts['dose_b15']['dose_compliant'] else 'FAIL'}]"
        f" Dose B.15 — {verdicts['dose_b15']['total_dose_g_s']:.0f}/"
        f"{verdicts['dose_b15']['tolerance_g_s']:.0f} g·s,"
        f" recovery {'PASS' if verdicts['dose_b15']['recovery_compliant'] else 'FAIL'}"
        f", {verdicts['dose_b15']['impulse_count']} impulses",
        f"  [{'PASS' if verdicts['combined_b6']['compliant'] else 'FAIL'}]"
        f" 3D Combined B.6 — max ratio"
        f" {verdicts['combined_b6']['max_ratio_3d']:.3f}",
        line,
        "Active Restraint Requirements:",
    ]
    lines += [
        f"  [{'x' if r['met'] else ' '}] {r['requirement']}"
        f" ({r['condition']}, {r['clause']})"
        for r in report["restraints"]
    ]
    lines += [line, "Violation Traceability:"]
    lines += [
        f"  Jerk B.5: {v['start_s']:.2f}-{v['end_s']:.2f} s"
        f" peak {v['peak_jerk_g_per_s']:.2f} g/s"
        for v in verdicts["jerk_b5"]["violations"]
    ]
    lines += [
        f"  3D B.6  : {v['start_s']:.2f}-{v['end_s']:.2f} s"
        f" peak {v['peak_ratio']:.2f}"
        for v in verdicts["combined_b6"]["triaxial_violations"]
    ]
    if not (verdicts["jerk_b5"]["violations"]
            or verdicts["combined_b6"]["triaxial_violations"]):
        lines.append("  (none)")
    lines += [line, "RideSafe-Bio — auto-generated; ISO 17842-1 prevails."]
    return "\n".join(lines)


def report_file_stem() -> str:
    """Timestamped file stem: ridesafe_report_YYYYMMDD_HHMM."""
    from datetime import datetime

    return f"ridesafe_report_{datetime.now().strftime('%Y%m%d_%H%M')}"


def plot_time_series(
    filtered: pd.DataFrame,
    jerk_verdict: dict,
    combined: dict,
) -> "go.Figure":
    """Interactive 3-axis time series with red shading over violation runs."""
    import plotly.graph_objects as go

    fig = go.Figure()
    colors = {"ax": "#1f77b4", "ay": "#2ca02c", "az": "#9467bd"}
    for axis in ACCELERATION_COLUMNS:
        fig.add_trace(go.Scattergl(
            x=filtered[TIME_COLUMN], y=filtered[axis],
            mode="lines", name=axis, line=dict(color=colors[axis], width=1),
        ))

    for verdict, label, key in (
        (jerk_verdict, "Jerk violation (B.5)", "violation_intervals"),
        (combined, "3D ratio violation (B.6)", "triaxial_violations"),
    ):
        for i, interval in enumerate(verdict[key]):
            fig.add_vrect(
                x0=interval["start_s"], x1=interval["end_s"],
                fillcolor="rgba(255,0,0,0.15)", line_width=0,
                annotation_text=f"{label} #{i + 1}",
                annotation_position="top left",
                annotation_font_size=10,
            )
    for i, transient in enumerate(combined["excluded_transients"]):
        fig.add_vrect(
            x0=transient["start_s"], x1=transient["end_s"],
            fillcolor="rgba(128,128,128,0.15)", line_width=0,
            annotation_text=f"excluded #{i + 1}",
            annotation_position="bottom left", annotation_font_size=9,
        )
    fig.update_layout(
        xaxis_title="time (s)", yaxis_title="acceleration (g)",
        height=420, margin=dict(l=40, r=20, t=30, b=30), legend_orientation="h",
    )
    return fig


def plot_3d_ellipsoid(
    filtered: pd.DataFrame,
    combined: dict,
    max_points: int = 8000,
) -> "go.Figure":
    """3D scatter of the acceleration vector vs the B.6 ellipsoid surface."""
    import plotly.graph_objects as go

    ratios = combined["sample_ratios"]
    stride = max(int(np.ceil(len(filtered) / max_points)), 1)
    ax = filtered["ax"].to_numpy()[::stride]
    ay = filtered["ay"].to_numpy()[::stride]
    az = filtered["az"].to_numpy()[::stride]
    ratio = ratios["ratio_3d"].to_numpy()[::stride]

    inside = ratio <= 1.0
    fig = go.Figure()
    fig.add_trace(go.Scatter3d(
        x=ax[inside], y=ay[inside], z=az[inside],
        mode="markers", name="inside (safe)",
        marker=dict(size=2.5, color="rgba(44,160,44,0.55)",
                    colorbar=None),
    ))
    fig.add_trace(go.Scatter3d(
        x=ax[~inside], y=ay[~inside], z=az[~inside],
        mode="markers", name="outside (violation)",
        marker=dict(size=3.5, color="rgba(214,39,40,0.85)", symbol="x"),
    ))

    # unit-sphere surface scaled by the per-sample adm along the full grid
    adm_x = combined["_adm_x"]
    adm_y = combined["_adm_y"]
    adm_z = combined["_adm_z"]
    mid = len(filtered) // 2
    scale_x, scale_y, scale_z = adm_x[mid], adm_y[mid], adm_z[mid]
    u = np.linspace(0, 2 * np.pi, 36)
    v = np.linspace(0, np.pi, 18)
    xs = scale_x * np.outer(np.cos(u), np.sin(v))
    ys = scale_y * np.outer(np.sin(u), np.sin(v))
    zs = scale_z * np.outer(np.ones_like(u), np.cos(v))
    fig.add_trace(go.Mesh3d(
        x=xs.ravel(), y=ys.ravel(), z=zs.ravel(),
        opacity=0.25, color="#1f77b4", name="B.6 envelope",
        hoverinfo="name",
    ))
    fig.update_layout(
        scene=dict(
            xaxis_title="ax (g)", yaxis_title="ay (g)", zaxis_title="az (g)",
        ),
        height=520, margin=dict(l=0, r=0, t=20, b=0),
        legend_orientation="h",
    )
    return fig


def load_uploaded_file(buffer: io.BytesIO, name: str) -> pd.DataFrame:
    """Read an uploaded CSV/TXT with delimiter sniffing."""
    raw = buffer.read()
    text = raw.decode("utf-8", errors="replace")
    delim = detect_delimiter(text[:4096])
    kwargs = {"sep": delim, "engine": "python"} if delim != "," else {}
    return pd.read_csv(io.StringIO(text), **kwargs)


def run_evaluation_pipeline(
    raw_frame: pd.DataFrame,
    column_mapping: dict[str, str],
    sampling_rate: float | None,
    unit_conversions: dict | None,
    axis_inversions: dict[str, bool],
    device_class: str,
) -> dict:
    """Standardize → filter → jerk → impulses → dose → 3D → RB."""
    standardized, metadata = standardize_signal_frame(
        raw_frame,
        column_mapping,
        sampling_rate=sampling_rate,
        unit_conversions=unit_conversions,
        axis_inversions=axis_inversions,
    )
    fs = metadata["sampling_rate"]
    filtered = apply_butterworth_lowpass(standardized, CANONICAL, fs, FILTER_DEFAULTS)

    jerk = calculate_jerk_rate(filtered, fs)
    jerk_verdict = evaluate_jerk_compliance(jerk, axis="az", device_class=device_class)

    impulses = detect_impulses(filtered, axis="az")
    dose = compute_cumulative_dose(impulses, recovery_signal=filtered)
    combined = evaluate_3d_combined_inequality(filtered)

    from src.iso17929_engine import _exposure, lookup_adm

    time_values = filtered[TIME_COLUMN].to_numpy(dtype=float)
    adm_x_arr = np.array([
        lookup_adm("x", 1 if v >= 0 else -1, d)
        for v, d in zip(filtered["ax"].to_numpy(dtype=float),
                        _exposure(None, np.abs(filtered["ax"].to_numpy(dtype=float)),
                                  time_values))
    ])
    adm_y_arr = np.full(len(filtered), lookup_adm("y", 1, 1.0))
    adm_z_arr = np.array([
        lookup_adm("z", 1 if v >= 0 else -1, d)
        for v, d in zip(filtered["az"].to_numpy(dtype=float),
                        _exposure(None, np.abs(filtered["az"].to_numpy(dtype=float)),
                                  time_values))
    ])
    combined["_adm_x"] = adm_x_arr
    combined["_adm_y"] = adm_y_arr
    combined["_adm_z"] = adm_z_arr

    peaks: dict[str, float] = {}
    for axis in ACCELERATION_COLUMNS:
        part = filtered[[TIME_COLUMN, axis]]
        found = detect_impulses(part, axis=axis)
        positive = max((i.peak_g for i in found if i.sign > 0), default=0.0)
        negative = max((i.peak_g for i in found if i.sign < 0), default=0.0)
        peaks[axis] = max(positive, negative)  # magnitude row (ax/ay tables symmetric)
        if axis in ("ax", "az"):
            # polarity keys: -ax drives the B.26 lap-bar rule, -az the B.1 row
            peaks[f"+{axis}"] = positive
            peaks[f"-{axis}"] = negative

    assessment = classify_risk_level(peaks)
    assessment.restraints = extract_restraint_requirements(
        peaks,
        durations={
            axis: float(filtered[TIME_COLUMN].iloc[-1] - filtered[TIME_COLUMN].iloc[0])
            for axis in ACCELERATION_COLUMNS
        },
    )
    return {
        "fs": fs,
        "metadata": metadata,
        "filtered": filtered,
        "jerk_verdict": jerk_verdict,
        "impulses": impulses,
        "dose": dose,
        "combined": combined,
        "assessment": assessment,
        "peaks": peaks,
    }


# --- streamlit script -------------------------------------------------------------


def render_dashboard() -> None:
    """Streamlit script body: settings sidebar + evaluation tabs."""
    with st.sidebar:
        st.header("Data Source")
        source_mode = st.radio("Input", ("Synthetic datasets", "Upload file"))

        raw_frame: pd.DataFrame | None = None
        if source_mode == "Synthetic datasets":
            dataset_name = st.selectbox(
                "Edge-case dataset", sorted(DATASET_BUILDERS), index=0
            )
            if st.button("Generate & Load", type="primary"):
                DATASET_BUILDERS[dataset_name]("data")
                st.session_state["loaded_path"] = f"data/{dataset_name}"
            if "loaded_path" in st.session_state:
                raw_frame = pd.read_csv(st.session_state["loaded_path"])
                st.caption(f"Loaded: {st.session_state['loaded_path']}")
        else:
            upload = st.file_uploader("CSV / TXT", type=("csv", "txt"))
            if upload is not None:
                try:
                    raw_frame = load_uploaded_file(upload, upload.name)
                    st.caption(f"Loaded: {upload.name} ({len(raw_frame)} rows)")
                except Exception as exc:  # noqa: BLE001 — surface to operator
                    st.error(f"Failed to parse file: {exc}")

        st.divider()
        st.header("Signal Settings")
        invert = {
            "ax": st.checkbox("Invert ax"),
            "ay": st.checkbox("Invert ay"),
            "az": st.checkbox("Invert az"),
        }
        unit_choice = st.selectbox("Input unit", ("g", "m/s²"))
        fs_mode = st.radio("Sampling rate", ("Auto (from time)", "Manual"))
        fs_manual = st.number_input(
            "fs (Hz)", min_value=1.0, value=500.0, step=50.0,
            disabled=fs_mode != "Manual",
        )
        device_class = st.selectbox(
            "Device class", tuple(JERK_LIMITS), index=1,
            help="Jerk limit: family 7 / general 10 / extreme 15 g/s (B.5)",
        )

    st.title("🎡 RideSafe-Bio — Acceleration Safety Assessment")
    st.caption("ISO/CD 17929:2026 biomechanical evaluation — ISO 17842-1 prevails")

    if "axis_guide_seen" not in st.session_state:
        st.session_state["axis_guide_seen"] = True
        guide_open = True
    else:
        guide_open = False
    with st.expander(AXIS_GUIDE_TITLE, expanded=guide_open):
        guide_svg = load_axis_guide_svg()
        if guide_svg is not None:
            st.markdown(guide_svg, unsafe_allow_html=True)
        else:
            st.markdown(build_axis_guide_fallback_markdown())
        st.caption(AXIS_GUIDE_CAPTION)

    if raw_frame is None:
        st.info("Load a dataset or upload a signal file from the sidebar to begin.")
        return

    st.subheader("Column Mapping")
    st.caption("Map the uploaded logger columns onto the canonical axes.")
    columns = ["(none)"] + list(raw_frame.columns)
    default_map = suggest_default_mapping(list(raw_frame.columns))
    mapping_selection = {
        canonical: st.selectbox(
            canonical, columns, index=columns.index(default_map[canonical])
        )
        for canonical in ("time", "ax", "ay", "az")
    }

    try:
        column_mapping = build_column_mapping(mapping_selection)
        sampling_rate = None if fs_mode == "Auto (from time)" else float(fs_manual)
        unit_conversions = (
            {a: "m/s2_to_g" for a in ACCELERATION_COLUMNS}
            if unit_choice == "m/s²" else None
        )
        results = run_evaluation_pipeline(
            raw_frame, column_mapping, sampling_rate,
            unit_conversions, invert, device_class,
        )
    except Exception as exc:  # noqa: BLE001 — surface to operator
        st.error(f"Configuration error: {exc}")
        return

    metadata = results["metadata"]
    st.success(
        f"Signal ready — {len(results['filtered'])} samples @ {results['fs']:.1f} Hz · "
        f"unit {'m/s²→g' if unit_choice == 'm/s²' else 'g'} · inverted: "
        f"{', '.join(a for a, v in metadata['axis_inversions'].items() if v) or 'none'}"
    )

    tab_signal, tab_eval, tab_passport = st.tabs(
        ["📈 Signal", "🔍 Evaluation", "🎫 Risk Passport"]
    )

    with tab_signal:
        filtered = results["filtered"]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Peak ax", f"{filtered['ax'].abs().max():.2f} g")
        m2.metric("Peak ay", f"{filtered['ay'].abs().max():.2f} g")
        m3.metric("Peak az", f"{filtered['az'].abs().max():.2f} g")
        m4.metric(
            "Total Duration",
            f"{filtered[TIME_COLUMN].iloc[-1] - filtered[TIME_COLUMN].iloc[0]:.2f} s",
        )
        st.plotly_chart(
            plot_time_series(filtered, results["jerk_verdict"], results["combined"]),
            use_container_width=True,
        )
        st.dataframe(filtered, use_container_width=True, height=300)
        st.caption("Filtered (4-pole Butterworth 5 Hz single-pass, SOS) — full dataset.")
        st.download_button(
            "Download filtered CSV",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="ridesafe_filtered_signal.csv",
            mime="text/csv",
        )

    with tab_eval:
        jerk_verdict = results["jerk_verdict"]
        dose = results["dose"]
        combined = results["combined"]
        c1, c2, c3 = st.columns(3)
        c1.metric(
            "Max |Jerk| (az)", f"{jerk_verdict['max_jerk_g_per_s']:.2f} g/s",
            f"limit {jerk_verdict['active_limit_g_per_s']} · "
            f"{'PASS' if jerk_verdict['compliant'] else 'FAIL'}",
        )
        c2.metric(
            "Impulses (az)", len(results["impulses"]),
            f"dose {dose['total_dose_g_s']:.0f} g·s · "
            f"{'PASS' if dose['dose_compliant'] else 'FAIL'} · recovery "
            f"{'PASS' if dose['recovery_compliant'] else 'FAIL'}",
        )
        c3.metric(
            "3D Ratio max", f"{combined['max_ratio_3d']:.3f}",
            f"{'PASS' if combined['compliant'] else 'FAIL'}",
        )

        if jerk_verdict["violation_intervals"]:
            st.warning(
                f"Jerk (B.5): {len(jerk_verdict['violation_intervals'])} violation "
                "interval(s) — details in Risk Passport."
            )
        if combined["triaxial_violations"]:
            st.warning(
                f"3D combined (B.6): {len(combined['triaxial_violations'])} violation "
                "interval(s)."
            )
        for transient in combined["excluded_transients"]:
            st.caption(
                f"Excluded transient (B.16): {transient['duration_s']:.3f} s at "
                f"{transient['start_s']:.2f} s (peak {transient['peak_ratio']:.2f})"
            )
        st.plotly_chart(
            plot_3d_ellipsoid(results["filtered"], combined),
            use_container_width=True,
        )
        st.caption(
            "Acceleration vector vs the B.6 ellipsoid (green: inside, red x: outside)."
        )

    with tab_passport:
        assessment = results["assessment"]

        # overall compliance banner (red reserved for FAIL verdicts)
        overall_ok = (
            results["jerk_verdict"]["compliant"]
            and results["dose"]["dose_compliant"]
            and results["dose"]["recovery_compliant"]
            and results["combined"]["compliant"]
        )
        st.markdown(
            build_compliance_banner_html(overall_ok),
            unsafe_allow_html=True,
        )

        # RB badge (client-approved palette; red is NOT used here)
        st.markdown(
            build_risk_badge_html(
                assessment.overall_rb,
                assessment.extremity,
                RB_BADGE_COLORS[assessment.overall_rb],
            ),
            unsafe_allow_html=True,
        )
        st.caption(f"{assessment.clause} · {assessment.metadata_status}")
        if assessment.test_required:
            st.info(
                "Note 3 (Table B.1): RB-1/RB-2 amplitudes require physical test "
                "verification (ASTM F2137 / GOST R 56066-2014) recorded in the "
                "technical passport."
            )

        st.markdown("**Per-Axis Classification**")
        axis_table = build_per_axis_table(assessment.per_axis_levels)
        st.dataframe(
            axis_table.drop(columns=["color"]),
            use_container_width=True, hide_index=True,
        )

        active = sum(1 for r in assessment.restraints if r["met"])
        st.metric("Active Requirements", active,
                  f"of {len(assessment.restraints)} evaluated (V11)")
        st.markdown("**Restraint Requirements**")
        for rule in assessment.restraints:
            icon = "🟠" if rule["met"] else "⚪"
            weight = "600" if rule["met"] else "400"
            color = "#e65100" if rule["met"] else "#9e9e9e"
            st.markdown(
                f'<div style="padding:6px 10px;border-left:3px solid {color};'
                f'margin:4px 0;">{icon} <b style="color:{color};font-weight:{weight};">'
                f'{rule["requirement"]}</b><br>'
                f'<small>{rule["condition"]} · {rule["clause"]}'
                + (f' · <i>{rule["note"]}</i>' if rule.get("note") else "")
                + "</small></div>",
                unsafe_allow_html=True,
            )

        st.markdown("**Violation Traceability**")
        trace_rows = []
        for interval in results["jerk_verdict"]["violation_intervals"]:
            trace_rows.append({
                "Rule": "Jerk (B.5)", "Start Time": interval["start_s"],
                "End Time": interval["end_s"],
                "Peak Value": f'{interval["peak_jerk_g_per_s"]:.2f} g/s',
                "Clause": interval["clause"],
            })
        for interval in results["combined"]["triaxial_violations"]:
            trace_rows.append({
                "Rule": "3D combined (B.6)", "Start Time": interval["start_s"],
                "End Time": interval["end_s"],
                "Peak Value": f'{interval["peak_ratio"]:.2f}',
                "Clause": interval["clause"],
            })
        for violation in results["dose"]["recovery_violations"]:
            trace_rows.append({
                "Rule": "Cumulative dose recovery (B.15)",
                "Start Time": f'between impulses {violation["between_ids"][0]}'
                              f'-{violation["between_ids"][1]}',
                "End Time": None,
                "Peak Value": f'min {violation["min_g"]:.2f} g',
                "Clause": violation["clause"],
            })
        if trace_rows:
            st.dataframe(pd.DataFrame(trace_rows), use_container_width=True,
                         hide_index=True)
        else:
            st.success("No violations recorded — full traceability table is empty.")

        st.divider()
        st.markdown("**Export Report**")
        source_label = st.session_state.get("loaded_path", "uploaded signal")
        json_report = build_report(results)
        text_report = build_text_report(results, source_name=source_label)
        stem = report_file_stem()
        dl1, dl2 = st.columns(2)
        dl1.download_button(
            "📄 Download JSON Report",
            data=json.dumps(json_report, indent=2, ensure_ascii=False).encode("utf-8"),
            file_name=f"{stem}.json",
            mime="application/json",
        )
        dl2.download_button(
            "📝 Download Summary Text",
            data=text_report.encode("utf-8"),
            file_name=f"{stem}.txt",
            mime="text/plain",
        )

render_dashboard()
