# Full-size test print and assembly

The next print is the full S01 panel kit. The 5.2 mm PETG locator width was selected from the printed strip trial; the user selected a 2.2 mm wall-shoe pilot and requested no further small calibration prints.

## Choose the print project

Open [S01_full_test_kit_P2S_PETG_flat_jig.3mf](../PRINT_THIS/S01_complete_kit_PETG_P2S.3mf) for the complete PETG kit:

| Plate | Contents | Estimated time | Material |
|---|---|---:|---:|
| 1 | One S01 panel | 6 h 45 min | 238.87 g PETG |
| 2 | A second identical S01 panel | 6 h 45 min | 238.87 g PETG |
| 3 | Eight wall shoes, 2.2 mm pilot | 2 h 39 min | 77.07 g PETG |
| 4 | One flat alignment jig, 5.2 mm fit | 39 min | 20.96 g PETG |

For a PLA panel, use [S01_panel_P2S_PLA.3mf](../PRINT_THIS/S01_panel_PLA_P2S.3mf): 6 h 43 min / 240.59 g. It has exactly the same panel geometry. This is an alternative to a PETG panel plate, not an additional required panel. To compare materials, print one panel from each project and the PETG hardware plates.

All projects target P2S / 0.4 mm, 0.2 mm layers, four walls, 100% infill and Arachne. They use resolved Generic PLA and Generic PETG presets from the installed Bambu Studio distribution. Match the selected material preset and plate type to the actual spool and bed before printing. Keep scale at 100%.

The installed Bambu Studio 2.8 command-line slicer failed when switching filament indices between PLA and PETG plates in one run. The delivered projects each use one material and were independently sliced and checked. No G-code was manually patched.

## Print orientation and supports

- Panels: flat visible face on the bed, ribs upward. No supports.
- Wall shoes: broad adhesive base on the bed, post and pilot upward. No supports.
- Jig: flat body face on the bed, locators upward. No supports.

The jig locators are 5.2 × 15.2 mm and project 4.4 mm, with a 0.4 mm tip lead-in. They stop 0.6 mm before the back of the 5 mm panel face. The body is flat; the requested pull knob was removed to eliminate support printing.

## Mount each panel

1. Use four printed shoes and four purchased pointed 3 × 16 mm self-tapping screws per panel. No nuts or washers are specified.
2. Place the shoes behind the four dedicated 3.4 mm mounting holes. On the upper pair, the longer part of the adhesive base points upward; rotate the lower pair 180° so it points downward.
3. Drive each screw through the panel into the 2.2 mm pilot using a hand tool. Tighten only until the head seats and the shoe no longer moves. Do not drive a bare screw fully into an uncovered shoe: the panel's 5 mm thickness is part of the screw-length stack.
4. Apply a 30 × 50 mm tape strip to each 34 × 54 mm base.
5. Position the first panel. For its neighbour, support the new panel by hand, bring it close to the installed panel's face plane, and engage two jig locators in each panel before the adhesive contacts the wall. Use complete slots; keep the locator ovals vertical for every seam.
6. Press the new panel's shoes to the wall with both panel faces seated against the jig. Hold the panels in place and pull the jig straight forward by its central spine or edges. The jig is an alignment aid; each panel remains supported by its own four shoes.

The nominal contour gap is 0.3 mm. Do not squeeze the edges together to eliminate it: the hole lattice sets the panel-centre positions.

## What this full-size test should establish

Check the increased jig insertion depth and removal, screw seating in the selected pilot, actual accessory movement behind the rim, and accessories spanning two rows or crossing a seam. The confirmed strip fit does not establish the full four-point jig fit on both PLA and PETG panels. The 2.2 mm pilot is user-selected and has not yet been physically tried with the purchased screws.

The tape is an unverified 30 mm product and the wall is wallpaper. Adhesive retention and a full-panel load rating remain unestablished. The historical 3 kg / 100 mm stiffness calculation is an earlier-geometry comparison, not a rating for this kit.
