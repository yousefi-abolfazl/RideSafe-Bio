# Contract: Guide Section (Expander Placement & Behavior)

**Applies to**: `app.py` insertion block | **Spec**: FR-001, FR-002, FR-005, FR-008

## Placement (FR-001)

- The guide block MUST sit after `st.title(...)` + `st.caption(...)` and
  before `st.tabs([...Signal... Evaluation... Risk Passport...])`.
- Order on the page: title → subheader caption → **guide expander** → tabs.
- No other widget may be inserted between the guide and the tabs.

## Widget (FR-002)

- Exactly one `st.expander("🧭 Axis Convention — how to read directions",
  expanded=<flag>)` — title string verbatim (emoji + en-dash).
- First visit (session flag absent): `expanded=True`; flag is set on render.
- Later renders: widget honors the visitor's toggle; collapsible at all times.

## Contents

1. Rendered `assets/axis_guide.svg` (inline, vector-sharp, responsive width,
   light background matching app theme).
2. Caption line below the figure (FR-005): seat-mounted placement near rider
   torso/heart + sidebar Invert-checkbox reference + meaning-fixed/sign-flips
   reassurance — see `svg-asset.md` for the exact sentence atoms.
3. Missing-asset fallback: text-only direction summary (the five FR-004 label
   rows as markdown) inside the same expander; dashboard continues, zero
   Traceback.

## Non-goals (FR-008)

- No changes under `src/`; no new imports in `app.py` beyond stdlib file
  handling already available; no change to time-series or 3D-ellipsoid code
  paths or performance.
