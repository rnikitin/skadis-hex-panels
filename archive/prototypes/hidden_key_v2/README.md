# Current prototype files

This directory contains the reviewed CAD exports and generated Bambu Studio test project for hidden joint v2 (24 × 8 × 3.2 mm key), plus the accepted M4 wall shoe.

**Superseded physical trial:** the key falls out and the assembly is loose. Permanent inter-panel keys have been abandoned. The current print files are in the [full-size kit](../../../PRINT_THIS/README.md). These files remain historical reference geometry; see the [fit report](../../../docs/fit_reports/2026-10-09-hidden-key-retention.md).

- `projects/corner_fit_test_24x8x3p2_P2S.3mf`: first physical test, three fragments and four keys.
- `stl/`: individual current test parts and the wall shoe.
- `step/`: full prototype panel, three-panel assembly and wall shoe for inspection.
- JSON files: dimensions, geometry checks, coupon crop, slicer result and file hashes.

The full panel STEP is a development model. A full printable current-panel STL has not been released. Geometry checks and slicer success do not establish physical snap fit, hook compatibility or adhesive capacity.

To regenerate, run `skadis-hex legacy-build --output build/legacy-key`, then validate and optionally slice as described in the root README. Rebuilding may change STEP headers and mesh ordering while preserving geometry.
