"""Axis Convention guide figure tests (task 4.5 + client asset swap).

Presentation-layer only: validates the client-provided reference figure
(raster PNG), the direction summary fallback, the dashboard wiring, and the
UI-agnostic core rule.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GUIDE_PATH = REPO_ROOT / "assets" / "axis_guide.png"
APP_PATH = REPO_ROOT / "app.py"
SRC_DIR = REPO_ROOT / "src"

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

# The client-approved reference figure is a raster image: direction tokens
# live in the text fallback, not in the pixels.
def _fallback_text() -> str:
    from app import build_axis_guide_fallback_markdown

    return build_axis_guide_fallback_markdown()


def test_asset_exists_and_is_valid_png():
    assert GUIDE_PATH.is_file(), "assets/axis_guide.png is missing"
    data = GUIDE_PATH.read_bytes()
    assert data.startswith(PNG_MAGIC), "asset is not a valid PNG"
    assert len(data) > 10_000, "asset suspiciously small for a guide figure"


def test_app_references_asset_and_expander():
    source = APP_PATH.read_text(encoding="utf-8")
    assert "assets/axis_guide.png" in source, "app.py missing asset reference"
    assert "Axis guide" in source, "app.py missing expander title"
    assert "st.image" in source, "app.py must render the guide via st.image"


def test_fallback_direction_tokens_and_keywords_present():
    text = _fallback_text()
    for token in ("+X", "+Y", "+Z"):
        assert token in text, f"missing token {token}"
    neg = "[-\u2212]"
    for axis in ("X", "Y", "Z"):
        assert re.search(rf"{neg}{axis}", text), f"missing negative token -{axis}"
    for word in ("Forward", "Rearward", "Up", "Down"):
        assert word in text, f"missing keyword {word}"


def test_fallback_body_feel_phrases_present():
    text = _fallback_text()
    for phrase in (
        "pressed into backrest",
        "thrown forward vs restraint",
        "pressed sideways",
        "pressed into seat",
        "airtime / lift-off risk",
    ):
        assert phrase in text, f"missing body-feel phrase: {phrase}"


def test_no_ui_imports_in_src():
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
