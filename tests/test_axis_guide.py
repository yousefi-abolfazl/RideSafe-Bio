"""Axis Convention guide figure tests (task 4.5, FR-009).

Presentation-layer only: validates the static SVG asset, the exact
direction labels, the dashboard wiring, and the UI-agnostic core rule.
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SVG_PATH = REPO_ROOT / "assets" / "axis_guide.svg"
APP_PATH = REPO_ROOT / "app.py"
SRC_DIR = REPO_ROOT / "src"

# RB badge palette (src/config.py RB_BADGE_COLORS) + verdict colors.
FORBIDDEN_HEXES = ("#6a1b9a", "#880e4f", "#e65100", "#0277bd", "#2e7d32")
NEG = "[-\u2212]"  # ASCII hyphen or U+2212 minus


def _svg_text() -> str:
    return SVG_PATH.read_text(encoding="utf-8")


def test_asset_exists_and_is_valid_svg():
    assert SVG_PATH.is_file(), "assets/axis_guide.svg is missing"
    text = _svg_text()
    assert len(text.strip()) > 0, "assets/axis_guide.svg is empty"
    assert "<svg" in text, "asset has no <svg root"
    root = ET.fromstring(text)  # raises on malformed XML
    assert root.tag.endswith("svg"), f"unexpected root tag {root.tag}"


def test_all_direction_tokens_and_keywords_present():
    text = _svg_text()
    for token in ("+X", "+Y", "+Z"):
        assert token in text, f"missing token {token}"
    for axis in ("X", "Y", "Z"):
        assert re.search(rf"{NEG}{axis}", text), f"missing negative token -{axis}"
    for word in ("Forward", "Rearward", "Up", "Down"):
        assert word in text, f"missing keyword {word}"


def test_body_feel_phrases_present():
    text = _svg_text()
    for phrase in (
        "pressed into backrest",
        "thrown forward vs restraint",
        "pressed sideways",
        "pressed into seat",
        "airtime / lift-off risk",
    ):
        assert phrase in text, f"missing body-feel phrase: {phrase}"


def test_app_references_asset_and_expander():
    source = APP_PATH.read_text(encoding="utf-8")
    assert "assets/axis_guide.svg" in source, "app.py missing asset reference"
    assert "Axis Convention" in source, "app.py missing expander title"


def test_no_verdict_or_risk_colors_in_svg():
    text = _svg_text().lower()
    for forbidden in FORBIDDEN_HEXES:
        assert forbidden not in text, f"forbidden RB color in guide: {forbidden}"


def test_src_stays_ui_free():
    offenders = []
    for path in sorted(SRC_DIR.glob("*.py")):
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            stripped = line.split("#", 1)[0]
            if re.search(
                r"(^\s*import\s+(streamlit|plotly|matplotlib)\b|"
                r"^\s*from\s+(streamlit|plotly|matplotlib)\b)",
                stripped,
            ):
                offenders.append(f"{path.name}:{lineno}: {line.strip()}")
    assert not offenders, f"UI imports in src/: {offenders}"
