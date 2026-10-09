# Front alignment jig fit trial implementation plan

> **For agentic workers:** Execute this bounded CAD task inline, with geometry tests and native slicer verification. User approved the displayed open-front jig concept on 2026-10-09.

**Goal:** Deliver a small PETG fit trial and matching full jig variants for independently mounted S01 panels.

**Architecture:** Add an independent alignment module using the existing lattice, CAD helpers, STL export conventions and core-3MF plate writer. Preserve superseded key geometry as historical data; the new jig never needs a panel pocket or rear access. Extend the shared slicer entry point to select and verify PETG explicitly.

**Tech stack:** Python 3.12, CadQuery 2.8, Shapely 2.2, trimesh 5.1, Bambu Studio P2S 0.4.

## Constraints

- Repository documentation is English.
- Full jig: 92 × 60 × 4 mm body; two 20 mm horizontal bars and a 16 mm central spine.
- Four vertical capsule locators, 80 × 40 mm centre spacing, 3.5 mm projection.
- Candidate widths 4.9, 5.1, 5.2 mm; capsule overall length equals width + 10 mm.
- Locator tips have a 0.4 mm lead-in; the constant locating section stays at the named size.
- Calibration strips: 16 × 60 × 4 mm, two locators spaced 40 mm, engraved numeric width.
- Print flat body face down, locators up, without supports or XY scaling.
- Sliding fit and physical alignment remain unverified until the user's print test.

## Task 1: Geometry and fit evidence

Files: `src/skadis_hex/alignment.py`, `tests/test_alignment.py`, `src/skadis_hex/cli.py`.

Interfaces: `make_jig(width)`, `make_fit_strip(width)` return one CadQuery solid; `verify_placements()` returns all six lattice placements; `build(output)` writes STL, STEP, geometry 3MF and JSON evidence.

- [x] Write tests first: validate connected solids and dimensions, sample the locating cross-section below the lead-in, verify each placement uses two whole slots per panel, and assert at least 7.5 mm clearance from purchased 4.9 mm screw heads.
- [x] Run `work/.venv/bin/python -m pytest tests/test_alignment.py -q`; expect missing module before implementation.
- [x] Implement the two-bar outline as the union of `box(-46,-30,46,-10)`, `box(-46,10,46,30)`, `box(-8,-10,8,10)`. Extrude 4 mm and add vertical capsules at `(±40,±20)`. Use the same locator builder for the two-point strip at `(0,±20)`.
- [x] Export three strips and three full jigs. Put only the strips on the first test plate. Write all-six-edge placement coordinates, physical-fit status and mesh integrity to JSON.
- [x] Run the new geometry tests and complete build; expect valid connected solids and watertight meshes for all six parts.

## Task 2: PETG project and delivery

Files: `src/skadis_hex/printing.py`, `src/skadis_hex/print_profiles/filament_petg.json`, `docs/front-alignment-jig.md`, `models/alignment_fit/`, README and history.

Interfaces: `slice_geometry_project(..., material='PLA')` preserves PLA behavior; material `PETG` selects a fully resolved installed-vendor profile and checks exported material metadata.

- [x] Resolve the installed Generic PETG P2S parent/include chain; verify PETG type, 1.27 density and 255 °C nozzle / 70 °C textured plate settings from vendor files.
- [x] Add `jig-fit` and `slice-jig-fit` CLI actions. Slice the three-strip geometry plate with PETG and preserve separate named validation/preview outputs.
- [x] Verify the exported 3MF contains PETG in both project metadata and G-code, 0.2 mm layers, four walls, 100% infill, and no supports.
- [x] Run all package tests, inspect the plate preview, document first-print selection criteria and the later full-jig check across two panels.
- [x] Record the superseded key trial and current removable-jig direction, copy checked files into `models/alignment_fit`, commit and update the existing public-repository branch.

## Delivery boundaries

The first print contains calibration strips only. A successful two-point strip does not by itself validate all four locators over 80 mm, so the selected full jig must be tried dry on two panels before applying adhesive. Every panel remains independently mounted. Wall-shoe pilot selection remains a separate pending physical test.

## Outcome

Six connected, watertight parts exported. All six seam placements pass. The package suite passes 16 tests, including straight front withdrawal and a PETG material regression. Native P2S PETG toolpaths estimate 32m17s / 15.71 g; labels were inspected in the generated plate preview. Physical fit remains pending. Public branch update is recorded by the commit containing this plan.
