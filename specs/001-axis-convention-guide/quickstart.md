# Quickstart: Axis Convention Guide Figure

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Date**: 2026-09-14

Validates the guide end-to-end (figure → dashboard → suite → smoke → docs/git).
Implementation details belong in `tasks.md`; this is the run guide.

## Prerequisites

- Branch `chatbox/axis-guide-4.5`; repo root `/home/ebi927/projects/RideSafe`.
- Virtualenv with existing requirements (no new deps):
  `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
- Baseline: 121/121 tests green before starting.

## 1. Static asset check

- Confirm `assets/axis_guide.svg` opens sharp at multiple zoom levels; both
  panels (top X/Y, side X/Z) legible on a laptop-width window and stacked /
  unclipped on a narrow viewport.
- Confirm exact label strings per [contracts/svg-asset.md](contracts/svg-asset.md)
  and zero forbidden colors (no red/green/RB hexes).

## 2. Dashboard check

- `.venv/bin/streamlit run app.py` → open http://localhost:8501.
- Expect: expander `🧭 Axis Convention — how to read directions` below the
  title and above the Signal / Evaluation / Risk Passport tabs; expanded on
  first visit, toggle persists afterwards; caption names seat-mounted
  placement + sidebar Invert checkboxes.
- Existing WebGL time-series and 3D ellipsoid render and behave as before.

## 3. Automated tests

- `.venv/bin/pytest tests/test_axis_guide.py -q` → new tests green.
- `.venv/bin/pytest tests/ -q` → full suite 100% green (121 baseline + new).

## 4. Smoke

- Dashboard serves HTTP 200 on http://localhost:8501 with zero Traceback in
  server logs (see [contracts/test-contract.md](contracts/test-contract.md)).

## 5. Docs + git

- `docs/task_log.md`: task 4.5 ⏳ → ✅ with Goal/Checkpoints/Changes/Result.
- `docs/roadmap.md`, `docs/decisions.md` (new ADR): headers
  **آخرین بازنگری:** 2026-09-14.
- `git status` clean except `app.py`, `assets/axis_guide.svg`,
  `tests/test_axis_guide.py`, the three docs, and the `specs/` plan
  artifacts; single commit `feat: axis convention guide figure (task 4.5)`
  + `Co-authored-by: Chatbox <chatbox@chatboxai.com>`; do NOT push.
