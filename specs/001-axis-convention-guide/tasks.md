# Tasks: Axis Convention Guide Figure

**Input**: Design documents from `/specs/001-axis-convention-guide/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Included — explicitly requested in spec FR-009/FR-010 (new `tests/test_axis_guide.py`, full-suite green, smoke check).

**Organization**: Tasks grouped by user story; each story independently testable. Touch ONLY `app.py` + `assets/axis_guide.svg` (+ tests/docs). Zero changes under `src/`.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Branch, baseline proof, task registration before any code.

- [X] T001 Create and switch to branch chatbox/axis-guide-4.5 (git checkout -b from repo root)
- [X] T002 [P] Record 121/121 green baseline by running `.venv/bin/pytest tests/ -q` in tests/
- [X] T003 Register task 4.5 as ⏳ with Goal/Checkpoints skeleton in docs/task_log.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Failing-first test module that all story work must satisfy (Constitution III + research R-5).

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Create failing-first `tests/test_axis_guide.py` in tests/test_axis_guide.py covering all four contract groups: (1) `assets/axis_guide.svg` exists, non-empty, parses as XML with `<svg` root; (2) raw SVG text contains tokens `+X -X +Y -Y +Z -Z` (accept U+2212 `−` variants) AND words `Forward`, `Rearward`, `Up`, `Down`; (3) `app.py` source contains `assets/axis_guide.svg` AND `Axis Convention`; (4) walk every `.py` file under `src/` asserting no `streamlit`/`plotly`/`matplotlib` import; plus forbidden-color scan (no red/green, none of `#6a1b9a`, `#880e4f`, `#e65100`, `#0277bd`, `#2e7d32` case-insensitive) — confirm all fail before implementation (5 failed / 1 passed: only src UI-free passed)

**Checkpoint**: Test file exists and fails (no asset, no wiring yet) — story implementation can now begin.

---

## Phase 3: User Story 1 — Inspector reads axis directions (Priority: P1) 🎯 MVP

**Goal**: Expander above the tabs renders both 2D views with all six direction labels and body-feel phrases; first-visit expanded, collapsible after.

**Independent Test**: Open dashboard with no data loaded — guide visible below title, above Signal/Evaluation/Risk Passport tabs; left panel shows +X Forward/−X Rearward/±Y Right-Left, right panel shows +Z Up/−Z Down; no data needed.

### Tests for User Story 1

> **NOTE: Written in T004 FIRST — confirm they FAIL before T005/T006.**

### Implementation for User Story 1

- [X] T005 [US1] Create two-panel flat vector figure with exact FR-004 label strings (`+X | Forward | pressed into backrest`, `-X | Rearward / Braking | thrown forward vs restraint`, `±Y | Right / Left (symmetric) | pressed sideways`, `+Z | Up | pressed into seat (heavier)`, `-Z | Down | airtime / lift-off risk`) in assets/axis_guide.svg (single self-contained SVG: inline shapes/text only, no `<image>`, system font stack, light background, responsive `viewBox`, per contracts/svg-asset.md)
- [X] T006 [US1] Insert session-state first-visit flag plus single `st.expander("🧭 Axis Convention — how to read directions", expanded=<flag>)` between `st.title`/`st.caption` and `st.tabs`, rendering the SVG inline via existing `st.markdown(..., unsafe_allow_html=True)` path with missing-asset text-only fallback (five FR-004 rows as markdown, zero Traceback) in app.py
- [X] T007 [US1] Run `.venv/bin/pytest tests/test_axis_guide.py -q` in tests/test_axis_guide.py and confirm US1-related test groups (asset valid, labels, wiring) turn green (6/6 green)

**Checkpoint**: US1 fully functional and testable independently — guide renders, both views legible, fallback safe.

---

## Phase 4: User Story 2 — Reversed sensor mount recovery (Priority: P2)

**Goal**: Caption under the figure gives seat-mounted placement and Invert-checkbox recovery with meaning-fixed/sign-flips reassurance.

**Independent Test**: Read caption under figure — states placement near rider torso/heart AND references sidebar Invert checkboxes with the fixed-meaning/flipped-sign reassurance.

### Implementation for User Story 2

- [X] T008 [US2] Add caption line with all three SensorCaption atoms ((a) seat-mounted near rider torso/heart, (b) existing sidebar `Invert ax/ay/az` checkboxes, (c) arrow meanings fixed / only signal sign flips) below the figure inside the same expander in app.py (no sidebar changes)
- [X] T009 [US2] Verify caption atoms by loading the dashboard and reading the caption text in app.py (manual check against contracts/guide-section.md; no new automated test file needed)

**Checkpoint**: US1 AND US2 both work independently — directions plus recovery guidance visible together.

---

## Phase 5: User Story 3 — Never mistaken for a verdict (Priority: P3)

**Goal**: Figure uses only the axis-family color language; automated scan proves zero verdict/risk colors.

**Independent Test**: Inspect figure colors — none match red, green, or any RB badge hex.

### Implementation for User Story 3

- [X] T010 [US3] Apply ColorContract colors in assets/axis_guide.svg (X family navy/blues with constraint "X → navy/blues", Y family teals with constraint "Y → teals", Z family purples with constraint "Z → purples"; positive `+` arrows solid filled per "positive (`+`) → solid filled arrow", negative `−`/`-` arrows hollow/dashed per "negative (`−`/`-`) → hollow/dashed arrow"; forbidden set "no element's color may match red, green, or #6a1b9a/#880e4f/#e65100/#0277bd/#2e7d32" quoted verbatim from data-model.md)
- [X] T011 [US3] Confirm forbidden-color scan test in tests/test_axis_guide.py passes (re-run group from T004 against final SVG; no new test file)

**Checkpoint**: All three user stories independently functional — readable, recoverable, neutral.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Regression proof, smoke, docs, commit — FR-010/FR-011 acceptance.

- [X] T012 Run full suite `.venv/bin/pytest tests/ -q` in tests/ and confirm 100% green (121 baseline + new tests on top) — 127/127 green
- [X] T013 [P] Smoke `.venv/bin/streamlit run app.py` in app.py serving HTTP 200 on http://localhost:8501 with zero Traceback and unslowed WebGL time-series + 3D ellipsoid (8511: HTTP 200, zero Traceback; 8501 pre-existing server untouched)
- [X] T014 [P] Verify narrow-viewport stacking (no horizontal label clipping) and zoom sharpness of assets/axis_guide.svg in assets/axis_guide.svg (480px window: 414px figure, zero clipping; element shot verified)
- [X] T015 Flip task 4.5 ⏳→✅ with Goal/Checkpoints/Changes-table/Result-Validation in docs/task_log.md
- [X] T016 [P] Update phase-4 row in docs/roadmap.md with header **آخرین بازنگری:** 2026-09-14
- [X] T017 [P] Add ADR (two-2D-views readability rationale + color-reservation rule, status ✅) in docs/decisions.md with header **آخرین بازنگری:** 2026-09-14
- [X] T018 Single commit `feat: axis convention guide figure (task 4.5)` + trailer `Co-authored-by: Chatbox <chatbox@chatboxai.com>` on branch chatbox/axis-guide-4.5 without pushing (verify `git status` clean except `app.py`, `assets/axis_guide.svg`, `tests/test_axis_guide.py`, the three docs, and `specs/` artifacts) — commit 538a334, not pushed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — starts immediately (T001 → T002/T003).
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories (T004 must fail-first before T005+).
- **User Stories (Phases 3–5)**: All depend on Foundational; run sequentially P1 → P2 → P3 (T006 edits the same `app.py` block T008 extends; T010 re-edits the same SVG T005 creates — same-file, never parallel).
- **Polish (Phase 6)**: Depends on all three stories complete (T012 gate before T015–T018).

### User Story Dependencies

- **User Story 1 (P1)**: After Foundational only — no other story dependencies. MVP.
- **User Story 2 (P2)**: After Foundational + US1 (extends the US1 expander block with the caption; independently testable via caption atoms).
- **User Story 3 (P3)**: After Foundational + US1 (recolors the US1 SVG; independently testable via color scan).

### Within Each User Story

- Tests (T004) written and FAIL before implementation (T005/T006).
- Asset before wiring (T005 → T006); content before verification (T006 → T007, T008 → T009, T010 → T011).
- Story checkpoint before next priority.

### Parallel Opportunities

- T002 × T003 (baseline run × task-log registration — different files).
- T013 × T014 × T016 × T017 (smoke × visual check × roadmap × decisions — four different targets, all after T012).
- Stories themselves are NOT parallel-safe (shared `app.py` block + shared SVG file) — single implementer, sequential.
- No two [P] tasks share a file — verified: every [P] pair targets distinct paths.

---

## Parallel Example: Polish Phase (after T012 green)

```bash
# Launch independent polish checks together (different files/targets):
Task: "Smoke .venv/bin/streamlit run app.py in app.py"
Task: "Verify narrow-viewport + zoom of assets/axis_guide.svg in assets/axis_guide.svg"
Task: "Update phase-4 row in docs/roadmap.md"
Task: "Add ADR in docs/decisions.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup: T001–T003) + Phase 2 (Foundational: T004 fail-first).
2. Complete Phase 3 (US1: T005–T007) — expander + both views + fallback.
3. **STOP and VALIDATE**: open dashboard dataless, confirm position/title/views/first-visit behavior; run new tests green.
4. Demo-ready: inspector vocabulary works without captions or final colors.

### Incremental Delivery

1. Setup + Foundational → failing tests define done.
2. + US1 (T005–T007) → Test independently → Demo (MVP: readable directions).
3. + US2 (T008–T009) → Test independently → Demo (recovery caption).
4. + US3 (T010–T011) → Test independently → Demo (verdict-neutral colors).
5. + Polish (T012–T018) → full suite, smoke, docs, commit.

---

## Notes

- [P] = different files, no dependencies (audited above); [USn] maps to spec stories for traceability.
- Each story independently completable and testable per its Independent Test line.
- Commit after each task or logical group; stop at any checkpoint to validate.
- Constitution: `src/` untouched (test group 4 enforces); no new deps; docs headers dated 2026-09-14; single commit, no push.
- Avoid: same-file parallel edits, `src/` changes, red/green/RB colors, new pip packages, Plotly/st.image render paths (see research R-2/R-3).
