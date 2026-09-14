# Feature Specification: Axis Convention Guide Figure

**Feature Branch**: `chatbox/axis-guide-4.5`

**Created**: 2026-09-14

**Status**: Draft

**Input**: User description: "TASK 4.5 — Axis Convention guide figure in the Streamlit dashboard (APPROVED, implement now). Two flat 2D views (top X/Y + side X/Z) in an st.expander above the three tabs, with exact English direction/body-feel labels, sensor-placement caption referencing sidebar Invert checkboxes, strict color rules (no red/green/RB palette), presentation-layer only, with tests, docs, and git requirements."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Inspector reads axis directions before interpreting results (Priority: P1)

A field inspector opens the dashboard and, before loading any signal, expands
the Axis Convention guide and learns which way +X/−X/±Y/+Z/−Z point and what
each direction feels like in the body (pressed into backrest, thrown forward
vs restraint, pressed sideways, pressed into seat, airtime/lift-off risk).

**Why this priority**: Without a shared direction vocabulary every downstream
verdict (PASS/FAIL, RB level) is misreadable. This is the sole user value of
the feature.

**Independent Test**: Open the dashboard with no data loaded; the guide is
visible above the analysis tabs, shows both views side by side with all six
direction labels, and no data or verdict is required.

**Acceptance Scenarios**:

1. **Given** the dashboard home page with no file loaded, **When** the
   inspector looks below the title, **Then** a guide section titled
   "Axis Convention — how to read directions" is present above the
   Signal / Evaluation / Risk Passport tabs.
2. **Given** the guide is visible, **When** the inspector reads the left view,
   **Then** the top (X/Y plane) view shows +X Forward, −X Rearward, and ±Y
   Right/Left with their body-feel phrases.
3. **Given** the guide is visible, **When** the inspector reads the right view,
   **Then** the side (X/Z plane) view shows +Z Up and −Z Down with their
   body-feel phrases.
4. **Given** a first-time visitor, **When** the page loads, **Then** the guide
   starts expanded; on later visits it remembers its collapsed/expanded state
   and stays collapsible.

---

### User Story 2 - Inspector with a reversed sensor mount recovers correct reading (Priority: P2)

An inspector whose accelerometer is mounted backwards reads the caption under
the figure, learns the sensor is expected seat-mounted near the rider
torso/heart, and learns to use the Invert checkboxes in the sidebar — with the
reassurance that arrow meanings stay fixed and only the signal sign flips.

**Why this priority**: Wrong-sign data inverts every verdict; the caption is
the cheapest prevention.

**Independent Test**: Read the caption line under the figure; it names the
expected sensor placement and points to the sidebar Invert checkboxes.

**Acceptance Scenarios**:

1. **Given** the guide figure, **When** the inspector reads the caption below
   it, **Then** the caption states the seat-mounted placement near the rider
   torso/heart AND references the sidebar Invert checkboxes with the
   meaning-fixed/sign-flips reassurance.

---

### User Story 3 - Inspector never mistakes the guide for a verdict (Priority: P3)

An inspector glances at the guide and never reads it as a PASS/FAIL or risk
badge: it uses its own axis-family color language and contains no verdict
colors.

**Why this priority**: A guide that looks like a result actively harms trust
in real verdicts.

**Independent Test**: Inspect the figure's colors; none match the reserved
verdict/risk palette.

**Acceptance Scenarios**:

1. **Given** the rendered guide, **When** its colors are inspected,
   **Then** no element uses red, green, or any RB badge color
   (#6a1b9a, #880e4f, #e65100, #0277bd, #2e7d32).

---

### Edge Cases

- What happens when the static figure asset is missing or unreadable at
  startup? The dashboard MUST still load and render all existing tabs and
  plots; the guide section degrades to a text-only direction summary rather
  than a traceback or blank page.
- How does the guide behave on a narrow (mobile/field-laptop) viewport? The
  two views stack or scale so all labels remain legible; no horizontal
  clipping of arrow labels.
- What happens when the figure is viewed zoomed or on a low-resolution field
  laptop? All lines and text stay sharp (vector rendering, no raster blur).
- How does the existing test suite react? All 121 pre-existing tests keep
  passing; new guide tests add on top.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Guide section MUST appear below the dashboard title/subheader
  and above the Signal / Evaluation / Risk Passport tabs.
- **FR-002**: Guide MUST be a single collapsible section titled
  "🧭 Axis Convention — how to read directions", expanded on first visit
  (session-state flag) and collapsible thereafter.
- **FR-003**: Guide MUST present exactly two side-by-side flat 2D views:
  LEFT = top view (X/Y plane: seat/vehicle schematic from above + seated
  rider icon with +X, −X, ±Y arrows); RIGHT = side view (X/Z plane: seat from
  the side + small rider with +Z, −Z vertical arrows). No 3D view.
- **FR-004**: Figure MUST carry the exact English labels: "+X | Forward |
  pressed into backrest"; "−X | Rearward / Braking | thrown forward vs
  restraint"; "±Y | Right / Left (symmetric) | pressed sideways";
  "+Z | Up | pressed into seat (heavier)"; "−Z | Down | airtime / lift-off
  risk" (tokens +X/−X/+Y/−Y/+Z/−Z plus words Forward/Rearward/Up/Down MUST all
  be present and machine-checkable).
- **FR-005**: Caption below the figure MUST state the seat-mounted sensor
  placement (near rider torso/heart) AND reference the existing sidebar Invert
  checkboxes, stating arrow meanings stay the same and only the signal sign
  flips.
- **FR-006**: Figure MUST use the axis-family color language (X = navy/blues,
  Y = teals, Z = purples; positive = solid filled arrow, negative =
  hollow/dashed arrow) and MUST NOT use red, green, or any RB badge palette
  color (#6a1b9a, #880e4f, #e65100, #0277bd, #2e7d32).
- **FR-007**: Figure MUST be a single self-contained vector asset (sharp at any
  zoom, light background matching the app theme, no external
  fonts/images), rendered with the existing dashboard stack only — no new
  runtime dependencies.
- **FR-008**: Guide MUST NOT modify the computational core: no changes under
  `src/`, no new imports of UI/visualization libraries into `src/`, and no
  change to existing time-series or 3D-ellipsoid rendering behavior or speed.
- **FR-009**: Automated tests MUST cover: (1) figure asset exists and is valid
  vector markup; (2) all six direction tokens plus Forward/Rearward/Up/Down
  present; (3) dashboard references the asset/expander; (4) no UI imports
  anywhere in `src/`.
- **FR-010**: Full test suite MUST remain 100% green (121/121 baseline kept,
  new tests on top); dashboard smoke check MUST serve HTTP 200 with zero
  Traceback.
- **FR-011**: Task MUST be registered as 4.5 ⏳ in `docs/task_log.md` then
  flipped to ✅ on success; `docs/roadmap.md` and `docs/decisions.md` (new ADR
  recording the two-2D-views rationale and the color-reservation rule) MUST be
  updated with revision header 2026-09-14; work MUST land on branch
  `chatbox/axis-guide-4.5` as `feat: axis convention guide figure (task 4.5)`
  with trailer `Co-authored-by: Chatbox <chatbox@chatboxai.com>` and MUST NOT
  be pushed unless asked.

### Key Entities

- **Axis Guide Figure**: the visual explainer; attributes: two 2D views (top
  X/Y, side X/Z), six direction arrows with body-feel labels, caption with
  sensor-placement and Invert-checkbox guidance.
- **Guide Section State**: first-visit expanded default with persistent
  collapsed/expanded memory per visitor session.
- **Color Contract**: axis families (X navy/blues, Y teals, Z purples;
  solid = positive, hollow/dashed = negative) disjoint from the reserved
  verdict/risk palette.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A first-time inspector can name all six axis directions and
  their body-feel meanings from the guide alone within 2 minutes, without
  loading any data.
- **SC-002**: Guide renders in under 1 second and the dashboard's existing
  plots show no perceptible slowdown versus baseline.
- **SC-003**: Zero regressions — all 121 pre-existing tests pass and the
  dashboard smoke check serves successfully with no errors.
- **SC-004**: Zero verdict-confusion reports — every inspector shown the guide
  identifies it as a neutral reference (not a PASS/FAIL or risk badge) on
  first glance.
- **SC-005**: An inspector with a reversed sensor mount finds the Invert
  recovery instruction in the caption without asking for help.

## Assumptions

- Dashboard UI language is English technical; figure labels stay English.
- The sidebar Invert checkboxes already exist; the caption only references
  them, no sidebar changes needed.
- Existing runtime stack (dashboard framework + plotting library already in
  requirements) suffices; no new pip dependencies.
- The seated-human + body-feel + restraint-link idea is borrowed from the
  old-standard reference site; its single-cluttered-3D-sketch layout is
  explicitly NOT reused — two separated 2D views replace it for
  non-technical readability.
- Constitution constraints apply: presentation-layer-only change
  (Traceability and UI-agnostic-core principles); docs carry revision header
  2026-09-14.
