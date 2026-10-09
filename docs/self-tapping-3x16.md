# Selected 3 × 16 mm self-tapping screw — fit trial

The user-selected black socket-head screw has these nominal dimensions in the supplied product diagram:

| Dimension | Nominal value |
|---|---:|
| Major thread diameter | 3 mm |
| Length under the head, including point | 16 mm |
| Head diameter | 4.9 mm |
| Head height | 3 mm |

This is a coarse pointed self-tapper. The seller's `M3` label does not establish an ISO metric nut fit. Thread pitch, driver size and actual batch tolerances have not been supplied.

## Candidate wall mount

The outer shoe shape is preserved: 34 × 54 mm base, 30 × 50 mm tape area, 12 mm post diameter and 23 mm from panel face to adhesive surface. The post is solid except for a blind pilot bore; the M4 nut pocket and side channel are removed.

Use a 3.4 mm mounting clearance hole in the panel instead of the released 4.5 mm hole. With a 4.9 mm head, the radial bearing ledge increases from 0.2 to 0.75 mm; the nominal annular bearing area is about 9.78 mm². There is no washer in the trial. The head protrudes approximately 3 mm from the panel face. Its physical bearing and clamping performance still require a print test.

The 5 mm panel leaves 11 mm of the screw inside the shoe, including its point. The screw ends at depth 16 mm; the blind pilot ends at 18.5 mm and the adhesive surface is at 23 mm. Nominal clearances are 2.5 mm to the pilot floor and 7 mm to the adhesive. These are geometric clearances, not a pull-out load rating.

## Choose the pilot by testing

Three candidates are provided: **2.2, 2.4 and 2.6 mm**. The 2.4 mm bore is only a starting trial, not a physically selected final diameter. Actual printed holes and the screw's thread profile determine the useful fit. Manufacturer guidance recommends material-specific pilot design and prototype assembly tests; these candidates are not a manufacturer specification for this unidentified screw or printed PLA. [Bossard construction recommendations](https://www.bossard.com/-/media/bossard-group/website/documents/technical-resources-old/construction-recommendations.pdf).

The test project contains:

- A three-post block with large 5 mm-high engraved pilot labels.
- A separate 5 mm plate with matching 3.4 mm clearance holes.
- One complete candidate wall shoe with a 2.4 mm pilot.
- A panel fragment with a 3.4 mm mounting hole and two complete working slots 40 mm apart, for checking an actual two-row accessory and head clearance.

A smaller pilot-only project contains just the three-post block and 5 mm plate. Use it first to select a bore without printing a complete wall shoe.

[Download the pilot-only test](../models/self_tapping_fit/projects/self_tapping_3x16_pilot_test_P2S.3mf) — about 40 minutes / 21.42 g. The [complete trial](../models/self_tapping_fit/projects/self_tapping_3x16_fit_P2S.3mf) is about 1 h 21 min / 47.58 g.

Test the screw **through the 5 mm plate**. The bare 16 mm screw is longer than the 13.5 mm pilot depth and must not be driven fully into an uncovered test post. Use controlled hand tightening. Start with 2.4 mm; compare the other fresh bores if it is too tight or does not hold. Check cracking, seating, stripping and repeated removal before selecting the final shoe. No torque or load rating is assigned from the product image.

The test-block post orientation, 12 mm diameter, lead-in and blind depth match the corresponding wall-shoe features. Its base is a test fixture, not an adhesive mount.

## Build and slice

```sh
uv run skadis-hex screw-fit --output build/self-tapping-fit
uv run skadis-hex slice-screw-fit --output build/self-tapping-fit
# Smaller first test:
uv run skadis-hex slice-screw-fit --output build/self-tapping-fit --pilot-only
```

The default full-joint build and the published v0.1.0 files still use the legacy M4 shoe. Keep the self-tapping trial separate until its pilot fit is selected. `joints.panel(wall_hole_diameter=3.4)` generates the matching candidate panel geometry; its default 4.5 mm hole remains unchanged for reproducibility.

The shape and nominal dimensions have been checked in CAD. Physical fit, pull-out resistance, long-term retention and adhesive/wall strength remain unverified.
