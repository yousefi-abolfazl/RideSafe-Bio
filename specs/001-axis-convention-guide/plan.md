# Implementation Plan: Axis Convention Guide Figure

**Branch**: `chatbox/axis-guide-4.5` | **Date**: 2026-09-14 | **Spec**: [specs/001-axis-convention-guide/spec.md](specs/001-axis-convention-guide/spec.md)

**Input**: Feature specification from `/specs/001-axis-convention-guide/spec.md`

## Summary

Add a neutral, presentation-layer-only axis-convention guide above the
Signal / Evaluation / Risk Passport tabs: one `st.expander` (first-visit
expanded via session state) rendering a single self-contained
`assets/axis_guide.svg` with two flat 2D panels (top X/Y + side X/Z),
exact English direction/body-feel labels, and a sensor-placement caption
pointing at the existing sidebar Invert checkboxes. No `src/` changes, no
new dependencies, no plot changes; new `tests/test_axis_guide.py` keeps the
suite green on top of the 121-test baseline.

## Technical Context

**Language/Version**: Python 3.10+ (developed on 3.14)

**Primary Dependencies**: streamlit + plotly (already in requirements.txt);
NO new pip dependencies

**Storage**: One static vector asset `assets/axis_guide.svg` (self-contained:
no external fonts/images); session-state flag only (no persistence layer)

**Testing**: pytest (`tests/test_axis_guide.py`: asset exists + valid XML,
six tokens + Forward/Rearward/Up/Down present, app.py references
asset/expander, no UI imports in `src/`); full suite
`.venv/bin/pytest tests/ -q`; smoke `.venv/bin/streamlit run app.py` →
HTTP 200, zero Traceback

**Target Platform**: Streamlit dashboard (Linux server + field laptop
browser, incl. narrow viewports)

**Project Type**: Web dashboard presentation-layer addition (no compute)

**Performance Goals**: Guide render <1s; existing WebGL time-series and 3D
ellipsoid untouched and unslowed (SC-002)

**Constraints**: Touch ONLY `app.py` + `assets/axis_guide.svg` (+ tests/docs);
zero changes under `src/`; single self-contained SVG; forbidden colors
(red/green/RB badge palette #6a1b9a/#880e4f/#e65100/#0277bd/#2e7d32) MUST
not appear; X = navy/blues, Y = teals, Z = purples; + = solid, − =
hollow/dashed; light background matching app theme; PEP 8 ≤100 cols;
English-only identifiers/comments

**Scale/Scope**: One figure, six arrows, five label rows + one caption line;
single dashboard insertion point (title/subheader → guide → tabs)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] I. UI-Agnostic Core — change is presentation-only (`app.py` +
  `assets/`); `src/` untouched, no streamlit/plotly/matplotlib imports
  added to `src/`; verified by FR-009 test (4).
- [x] II. Standards as Config — no normative thresholds, envelopes, or
  RB entries involved; nothing added to `src/config.py` or logic.
- [x] III. Test-First Verification — new `tests/test_axis_guide.py`
  written alongside the asset before dashboard wiring counts as done;
  121-test baseline must stay green; boundary datasets untouched (guide
  adds no computational rule).
- [x] IV. Rule-to-Clause Traceability — verdict mapping untouched; task
  4.5 logged in `docs/task_log.md` (⏳→✅); new ADR in `docs/decisions.md`
  (two-2D-views rationale + color-reservation rule); headers dated
  2026-09-14.
- [x] V. Format-Agnostic Ingestion — no column names hardcoded; caption
  only references existing `Invert ax/ay/az` checkboxes (meaning-fixed /
  sign-flips); pipeline reproducibility unchanged.

Post-design re-check: no new violations introduced (see research.md R-4
fallback and contracts/ for enforcement). No Complexity Tracking entry
needed — no gate violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/001-axis-convention-guide/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── guide-section.md # Expander placement/behavior contract
│   ├── svg-asset.md     # SVG content/color/structure contract
│   └── test-contract.md # Test enforcement contract
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
app.py                    # ADD: session-state flag + st.expander + render above st.tabs
assets/
└── axis_guide.svg       # NEW: single self-contained two-panel vector figure
tests/
├── test_axis_guide.py   # NEW: 4 test groups per FR-009
└── test_app.py          # UNTOUCHED (regression baseline)
src/                      # UNTOUCHED (constitutional ban)
docs/
├── task_log.md          # ADD: task 4.5 entry ⏳→✅
├── roadmap.md           # UPDATE: phase 4 row + header date 2026-09-14
└── decisions.md         # ADD: ADR two-2D-views + color reservation
```

**Structure Decision**: Single-project Streamlit layout (repository root
`app.py` + `src/` + `tests/` + `docs/` + `data/`). No backend/frontend
split, no new packages: the feature is one static asset plus one dashboard
insertion block plus one test module, exactly matching the approved
touch-only-`app.py`-plus-asset constraint.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations — table intentionally empty.
