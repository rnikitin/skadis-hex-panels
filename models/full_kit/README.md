# Current full-size S01 test kit

Open `projects/S01_full_test_kit_P2S_PETG_flat_jig.3mf` for two PETG panel plates, eight PETG wall shoes and one flat alignment jig. Supports are disabled on every plate.

Use `projects/S01_panel_P2S_PLA.3mf` as the alternative panel material. The geometry is identical.

- `stl/`: the panel, 2.2 mm-pilot wall shoe and flat 5.2 mm-fit jig with 4.4 mm locators.
- `step/`: editable CAD parts and mounted one/two-panel assemblies.
- `projects/*_geometry.3mf`: geometry-only plates without printer settings.
- `projects/*_P2S*.3mf`: native, sliced P2S 0.4 projects.
- `parameters.json`, `validation.json` and `slicing_*.json`: dimensions, CAD checks and native slicing evidence.
- `manifest.json`: SHA-256 hashes of the delivered files.

See [printing and assembly](../../docs/assembly.md), [hardware](../../docs/hardware.md) and [design](../../docs/design.md). The 5.2 mm PETG strip fit was selected physically; the deeper full-size jig and selected screw pilot are the next physical assembly test.
