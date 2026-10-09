# Hexagonal SKÅDIS-compatible panels

[![Validate CAD prototype](https://github.com/rnikitin/skadis-hex-panels/actions/workflows/validate.yml/badge.svg)](https://github.com/rnikitin/skadis-hex-panels/actions/workflows/validate.yml)

Parametric 3D-printable hexagonal panels with one continuous hole lattice across tile boundaries, four diagonal ribs, independent adhesive wall mounts, and a removable front alignment jig.

**Next print: [front alignment jig fit strips](docs/front-alignment-jig.md)** — three labelled candidates, approximately 32 minutes / 16 g PETG. Each panel supports its own load through four wall mounts; the jig is removed after positioning. Full-jig fit is pending.

The earlier **24 × 8 × 3.2 mm hidden key failed its physical PETG fit test** and was superseded. Its released files are retained for reference, not recommended for the next print. See the [fit report](docs/fit_reports/2026-10-09-hidden-key-retention.md).

![Three labelled alignment fit strips](models/alignment_fit/images/front_jig_fit_strips_P2S_PETG.png)

## Start here

- **Newly selected wall fastener:** [3 × 16 mm self-tapping screw fit trial](docs/self-tapping-3x16.md). The released M4 nut shoe is a different variant; pilot selection is pending.
- **Print next:** [three labelled fit strips / P2S PETG](models/alignment_fit/projects/front_jig_fit_strips_P2S_PETG.3mf).
- **Matching full jigs:** [STL variants](models/alignment_fit/stl/), print after selecting a sliding fit.
- **Historical prototype bundle:** [v0.1.0-prototype](https://github.com/rnikitin/skadis-hex-panels/releases/tag/v0.1.0-prototype), contains the superseded hidden-key trial.
- **Individual parts:** [current STL files](models/current/stl/).
- **Inspect the CAD:** [prototype STEP models](models/current/step/).
- **Assemble it:** [assembly and printing guide](docs/assembly.md).
- **Buy the hardware:** [hardware and wall mounts](docs/hardware.md).
- **Understand the geometry:** [design specification](docs/design.md).
- **See previous decisions:** [design history](docs/history.md).
- **Read the historical analysis:** [v3 stiffness study](analysis/v3/README.md).

The latest trial is documented in the [front-jig guide](docs/front-alignment-jig.md). The legacy panel STEP still contains receiver pockets; a clean full panel will be prepared with the selected wall-mount fit. Do not mix superseded key and receiver versions.

## Build from source

Python 3.12 is the supported development baseline. [uv](https://docs.astral.sh/uv/) is recommended:

```sh
uv sync --extra dev
uv run skadis-hex jig-fit --output build/alignment-fit
uv run skadis-hex slice-jig-fit --output build/alignment-fit
# Reproduce the historical hidden-key prototype:
uv run skadis-hex build --output build/current
uv run skadis-hex validate --output build/current
uv run pytest -q
```

Alternatively:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
skadis-hex build --output build/current
skadis-hex validate --output build/current
```

The build creates STL test parts, STEP assemblies, the wall shoe, dimensions, and a component report. Validation checks solid/mesh integrity, symmetry, all six seam directions, insertion envelopes, two-neighbour installation, and the previously missing triangular coupon patch.

To prepare a Bambu Studio project, install Bambu Studio separately:

```sh
uv run skadis-hex slice --output build/current
# On other installations, provide the executable explicitly:
uv run skadis-hex slice --output build/current --slicer /path/to/BambuStudio
```

This generates a project locally; it does not send anything to a printer. Bundled resolved presets target P2S, a 0.4 mm nozzle, PLA, 0.2 mm layers, four walls, 100% infill, and Arachne walls. Adapt material settings to the actual filament.

## What has been verified

| Item | Status |
|---|---|
| Nominal slot lattice and two-row accessory spacing | Checked geometrically |
| Closed, connected test-part meshes | Checked |
| Insertion alongside two existing neighbours | Checked with prescribed spring-arm deformation |
| Current Bambu Studio test project | Toolpaths generated |
| Physical hidden-key fit and retention | Failed; design superseded |
| Front jig: six seam placements and screw-head clearance | Checked geometrically |
| PETG front-jig fit strips | Toolpaths generated; physical fit pending |
| Actual accessory body and insertion clearance | Pending |
| Adhesive attachment to wallpaper | Pending |
| Full current-panel load rating | Not established |

The historical 3 kg / 100 mm calculation used an earlier v3 geometry and idealized material/support conditions. Its results must not be treated as a current-panel or adhesive load rating.

## Repository map

```text
src/skadis_hex/     Geometry, alignment jig, legacy joint, mounts and print tools
models/alignment_fit/  Latest removable-jig fit trial and matching full jigs
models/current/    Superseded hidden-key prototype and verification records
docs/              English design, assembly, hardware and decision history
analysis/v3/       Historical solver, exact input STEP files and result summaries
archive/           Superseded experiments and search results
tests/             Geometry regression fixtures and package checks
```

All dimensions are in millimetres unless stated otherwise. Source geometry is generated independently; reference models are listed in [references](docs/references.md).
