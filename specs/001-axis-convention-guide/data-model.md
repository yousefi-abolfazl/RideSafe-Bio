# Data Model: Axis Convention Guide Figure

**Feature**: specs/001-axis-convention-guide/spec.md | **Date**: 2026-09-14

This feature adds no computational data, no storage schema, and no signal
entities. The "model" is the static figure's content contract plus the
ephemeral UI state — documented here so plan, contracts, and tests share one
vocabulary.

## Entity 1: AxisDirection (static content row, ×6 visual arrows / 5 label rows)

| Field | Values / Rules |
|-------|----------------|
| token | One of `+X`, `−X`/`-X`, `+Y`, `−Y`/`-Y`, `+Z`, `−Z`/`-Z` (both hyphen U+002D and minus U+2212 accepted by tests) |
| plane | `X/Y` (top view) for X/Y tokens; `X/Z` (side view) for Z tokens |
| heading | `Forward` (+X) · `Rearward / Braking` (−X) · `Right / Left (symmetric)` (±Y) · `Up` (+Z) · `Down` (−Z) |
| body_feel | `pressed into backrest` (+X) · `thrown forward vs restraint` (−X) · `pressed sideways` (±Y) · `pressed into seat (heavier)` (+Z) · `airtime / lift-off risk` (−Z) |
| family_color | X → navy/blues · Y → teals · Z → purples (MUST avoid forbidden set) |
| polarity_style | positive (`+`) → solid filled arrow; negative (`−`/`-`) → hollow/dashed arrow; ±Y pair shows both styles symmetrically |

Validation rules (from FR-004/FR-006): all six tokens and the words
Forward/Rearward/Up/Down MUST be present as machine-checkable substrings;
no element's color may match red, green, or #6a1b9a/#880e4f/#e65100/#0277bd/#2e7d32.

Relationships: ±Y is a single symmetric pair (one label row, two arrows);
all other rows are one token → one arrow.

## Entity 2: GuideSectionState (ephemeral UI state, session-scoped)

| Field | Type / Rule |
|-------|-------------|
| expanded | bool — `True` on first visit (flag absent), then persists visitor's last toggle |
| seen_flag | session-state key (e.g. `axis_guide_seen`) marking a non-first visit |

State transitions: absent flag → expanded=True + set flag on first render;
visitor collapses/expands → flag stays set, widget state persists per
session. No cross-session persistence, no URL contract.

## Entity 3: SensorCaption (static text line under the figure)

Required content atoms: (a) seat-mounted placement near rider torso/heart;
(b) reference to the existing sidebar `Invert ax/ay/az` checkboxes;
(c) reassurance: arrow meanings stay fixed, only the signal sign flips.
No new sidebar controls — reference only.

## Entity 4: ColorContract (invariant, test-enforced)

Allowed families: navy/blues (X), teals (Y), purples (Z). Forbidden:
any red, any green, and RB badge hexes #6a1b9a, #880e4f, #e65100, #0277bd,
#2e7d32 (case-insensitive scan of `assets/axis_guide.svg`). Rationale: the
guide MUST never read as a PASS/FAIL verdict or RB badge.
