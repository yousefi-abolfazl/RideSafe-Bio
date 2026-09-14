# Contract: Test Enforcement (`tests/test_axis_guide.py`)

**Applies to**: `tests/test_axis_guide.py` | **Spec**: FR-009, FR-010

## Group 1 — Asset exists + valid (FR-009.1)

- `assets/axis_guide.svg` exists, is non-empty, parses as XML, root tag is
  `<svg` (namespace-tolerant).

## Group 2 — Labels present (FR-009.2)

- Raw SVG text contains all six tokens `+X -X +Y -Y +Z -Z` (accepting U+2212
  `−` variants for the negative tokens) AND all four words `Forward`,
  `Rearward`, `Up`, `Down` (case-sensitive, matching the exact English
  labels).

## Group 3 — Dashboard wiring (FR-009.3)

- `app.py` source contains the asset reference (`assets/axis_guide.svg`)
  AND the expander title fragment (`Axis Convention`).

## Group 4 — Core stays UI-free (FR-009.4, Constitution I)

- Walk every `.py` file under `src/`; assert no line imports
  `streamlit`, `plotly`, or `matplotlib` (covers `import x` and
  `from x import ...` forms).

## Suite gate (FR-010)

- `.venv/bin/pytest tests/ -q` → 121 baseline + new tests, 100% green.
- Smoke: `.venv/bin/streamlit run app.py` → HTTP 200 on
  http://localhost:8501, zero Traceback.
