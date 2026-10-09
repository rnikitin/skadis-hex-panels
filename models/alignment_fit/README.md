# Historical front alignment jig trial

The user selected 5.2 mm. Current print files are in the [full-size kit](../full_kit/README.md).

Start with `projects/front_jig_fit_strips_P2S_PETG.3mf`: three labelled two-locator strips, about 32 minutes / 15.71 g PETG on P2S 0.4. Select a sliding fit on an existing printed panel before printing the matching `stl/front_jig_*.stl`.

See the [English test and assembly guide](../../docs/front-alignment-jig.md). The full four-point jig must be tested dry across a horizontal and an oblique seam. Physical fit remains unverified.

- `stl/`: three strips and three full jig sizes, flat body face at z=0 for printing.
- `step/`: editable inspection solids in their design coordinates.
- `projects/*_geometry.3mf`: geometry only, without printer presets.
- `projects/*_P2S_PETG.3mf`: native sliced project with the verified PETG profile.
- `parameters.json`: dimensions, mesh integrity and all-six-edge placement evidence.
- `*_slicing.json`: actual slicer statistics and material checks.
- `manifest.json`: SHA-256 hashes of the delivered files.

These are placement tools, not permanent panel connectors or load-bearing wall hardware.
