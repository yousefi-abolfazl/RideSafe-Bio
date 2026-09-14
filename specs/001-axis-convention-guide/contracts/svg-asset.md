# Contract: SVG Asset (`assets/axis_guide.svg`)

**Applies to**: `assets/axis_guide.svg` | **Spec**: FR-003, FR-004, FR-006, FR-007

## Structure (FR-003)

- ONE self-contained SVG file: inline `<rect>/<circle>/<path>/<line>/<text>`
  only; no `<image>`, no external CSS/fonts (system font stack); light
  background matching the app theme; `viewBox` responsive so panels scale
  without clipping on narrow viewports.
- TWO panels, left-to-right: **Top view (X/Y plane)** — seat/vehicle
  schematic from above + seated rider icon + four arrows (+X, −X, +Y, −Y);
  **Side view (X/Z plane)** — seat from the side + small rider + two
  vertical arrows (+Z, −Z). Flat minimal vector style. NO 3D view.

## Labels (FR-004, exact strings — tests grep for tokens + keywords)

- `+X | Forward | pressed into backrest`
- `-X | Rearward / Braking | thrown forward vs restraint` (tests also
  accept `−X` U+2212)
- `±Y | Right / Left (symmetric) | pressed sideways` (tests accept `+Y`/`-Y`
  tokens individually)
- `+Z | Up | pressed into seat (heavier)`
- `-Z | Down | airtime / lift-off risk` (tests also accept `−Z` U+2212)
- Machine-checkable set: `+X`, `-X`, `+Y`, `-Y`, `+Z`, `-Z` (U+2212 variants
  accepted) + words `Forward`, `Rearward`, `Up`, `Down`.

## Color language (FR-006, test-enforced)

- X family: navy/blues · Y family: teals · Z family: purples.
- Positive arrows: solid filled; negative arrows: hollow/dashed.
- FORBIDDEN (case-insensitive substring scan fails the suite): any red or
  green fill/stroke, and `#6a1b9a`, `#880e4f`, `#e65100`, `#0277bd`,
  `#2e7d32`.

## Self-containment (FR-007)

- No external fonts/images; renders identically offline; single file read at
  render time (<1s budget, zero impact on existing plots).
