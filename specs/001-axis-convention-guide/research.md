# Research: Axis Convention Guide Figure

**Feature**: specs/001-axis-convention-guide/spec.md | **Date**: 2026-09-14

All Technical Context items were already resolved by the approved design and
repo inspection — no NEEDS CLARIFICATION remained. Each finding below was
verified against `app.py`, `src/config.py`, and the existing test suite
rather than assumed.

## R-1: Expander placement + first-visit default (FR-001, FR-002)

- Decision: Insert one `st.expander("🧭 Axis Convention — how to read
  directions", expanded=...)` between the title block (`st.title` +
  `st.caption`, app.py:510-511) and the tabs block (`st.tabs`, app.py:550),
  gated by a session-state flag (e.g. `axis_guide_seen`) that defaults to
  expanded on first visit and persists the visitor's toggle afterwards.
- Rationale: FR-001 mandates below-title/above-tabs; FR-002 mandates
  first-visit-expanded then collapsible; session state is already the
  client-approved state mechanism (module docstring) and is used in app.py
  for `loaded_path` (app.py:479-482).
- Alternatives considered: always-expanded (rejected — annoys returning
  inspectors); always-collapsed (rejected — first-time visitors miss the
  vocabulary); query-param memory (rejected — session state already
  established, no URL contract exists).

## R-2: SVG rendering path with zero new dependencies (FR-007)

- Decision: Single self-contained `assets/axis_guide.svg` (inline shapes +
  text, system font stack, no `<image>`, no external CSS/fonts), rendered
  from `app.py` via the existing HTML path (`st.markdown(...,
  unsafe_allow_html=True)` embedding the SVG inline, the same mechanism
  already used for the compliance banner app.py:631-634 and RB badge
  app.py:637-644) so no new package is needed.
- Rationale: `st.image` rasterizes/scales and would soften small labels on
  field laptops; inline SVG stays vector-sharp at any zoom and inherits the
  light app background; both `st.markdown` and file I/O (`io`, `pathlib`)
  are already imported/used in app.py. Render is one small static file read
  — far below the 1s budget, zero impact on WebGL plots.
- Alternatives considered: `st.image("assets/axis_guide.svg")` (rejected —
  rasterization risk + less control over responsive sizing); Plotly
  figure (rejected — abuses a data-plotting engine for a static diagram,
  loads WebGL for no reason); Matplotlib PNG (rejected — raster blur at
  zoom + banned-from-`src` is irrelevant but PNG fails the sharpness edge
  case).

## R-3: Color contract disjoint from verdict palette (FR-006)

- Decision: X family navy/blues, Y family teals, Z family purples; positive
  = solid filled arrow, negative = hollow/dashed; audit the SVG hex codes
  against the forbidden set: pure reds/greens plus RB badge values from
  `src/config.py` `RB_BADGE_COLORS` (#6a1b9a, #880e4f, #e65100, #0277bd,
  #2e7d32) — enforced by an automated test scanning the SVG for those
  strings (case-insensitive) plus a red/green-family regex guard.
- Rationale: Red is reserved for FAIL and green for PASS (config.py:230-232
  comment; RB badge deliberately avoids red per app.py:636); any overlap
  would let an inspector read the guide as a result. The test makes the
  rule self-enforcing for future edits.
- Alternatives considered: Grayscale + labels only (rejected — axis families
  are user-mandated and aid scanning); reusing app accent blue for all axes
  (rejected — X/Y/Z become indistinguishable).

## R-4: Missing-asset fallback (Edge Case 1)

- Decision: If `assets/axis_guide.svg` is missing/unreadable, catch the
  exception at render time and show a compact text-only direction summary
  (the five FR-004 label rows as markdown) inside the same expander — the
  dashboard and all tabs/plots continue normally, never a traceback.
- Rationale: Spec edge case mandates degrade-to-text, not crash; matches
  existing app.py pattern of surfacing configuration problems via
  `st.error` + early return (app.py:539-541) without breaking the page.
- Alternatives considered: hiding the expander entirely (rejected — loses
  the vocabulary with no explanation); letting the exception propagate
  (rejected — violates the smoke test's zero-Traceback requirement).

## R-5: Test strategy on top of the 121-test baseline (FR-009, FR-010)

- Decision: New `tests/test_axis_guide.py` with four groups: (1) asset
  exists + parses as XML with `<svg` root; (2) all six tokens
  (+X/−X/+Y/−Y/+Z/−Z — accepting both ASCII-hyphen and U+2212 variants)
  plus Forward/Rearward/Up/Down substrings; (3) `app.py` source references
  the asset path and the expander title string; (4) walk `src/` asserting no
  file imports streamlit/plotly/matplotlib. Existing `tests/test_app.py`
  untouched.
- Rationale: Mirrors FR-009 verbatim so each requirement has exactly one
  failing-first test; source-grep tests (3, 4) follow the existing
  import-safety precedent (app.py module docstring: pure helpers stay
  importable for unit tests). Full suite must read 121+N green.
- Alternatives considered: extending `tests/test_app.py` (rejected —
  separate module keeps blame clean and matches `test_<module>.py`
  convention); browser/screenshot test (rejected — no harness in
  requirements, smoke check covers serving).

## R-6: Docs + git mechanics (FR-011)

- Decision: `docs/task_log.md` gets task 4.5 ⏳ at start → ✅ on green
  suite + smoke; `docs/roadmap.md` phase-4 row notes the guide;
  `docs/decisions.md` gains one ADR (two-2D-views readability rationale +
  color-reservation rule); all three headers bumped to
  **آخرین بازنگری:** 2026-09-14. Branch `chatbox/axis-guide-4.5`, single
  commit `feat: axis convention guide figure (task 4.5)` + trailer
  `Co-authored-by: Chatbox <chatbox@chatboxai.com>`, no push.
- Rationale: FR-011 prescribes every string; matches constitution workflow
  gates (task log Goal/Checkpoints/Changes/Result; ADR subject/cause/impact/
  status ✅/⏳).
- Alternatives considered: none — fully prescribed.
