# Design history

All items below describe earlier experiments. The active implementation is under `src/skadis_hex`; the printable full-size kit is under `PRINT_THIS`.

| Stage | Result and decision |
|---|---|
| Initial 240 × 200 panel with whole slots only | Too many omitted edge slots; rejected |
| Candidate C, 160 × 240 | Preserved a whole-slot layout but deviated too much from the preferred hex shape |
| Symmetric search: S01, S02, S06 | Allowed split boundary slots; lattice reconstruction checked in a 3 × 3 assembly |
| Dense ribbed S01/S02/S06 | User's printed sample felt overbuilt; reduced rib count requested |
| Small rear butterfly keys | Printed fit varied, markings were hard to read, rear caps added depth, and adding wall-mounted neighbours was inconvenient; rejected |
| v3 front screw bridges and four adhesive shoes | Shoe positions and independent panel mounting retained; front seam bridges superseded |
| Four-diagonal layout and v3 stiffness study | Selected for the next prototype; user accepted the predicted deflections as a useful comparison |
| v4 removable registration jig | Used working slots during positioning; user preferred hidden permanent alignment in the perimeter |
| Continuous perimeter with local hook relief | Replaced the excessive 16 × 34 mm rear clearance boxes; extra downward hook travel requested |
| Hidden joint v1, 14.7 × 4.4 × 2.4 key | Geometric insertion prototype; user requested a larger handling size |
| Hidden joint v2, 24 × 8 × 3.2 key | PETG physical test failed retention and showed excessive play. Permanent keys, dowels and receivers were subsequently abandoned |
| Missing triangular coupon patch | A crop split off a small face island and the export kept only the largest solid. Crop boundaries moved; filtering removed; regression check now preserves the patch |
| Removable front jig, revisited | User approved two horizontal bars and a central spine, four short locators on an 80 × 40 grid. Open sides clear wall screw heads. Three labelled PETG fit strips precede the full jig |

The final kit uses 4.4 mm-deep locators with the selected 5.2 mm width. A pull knob was briefly added, then removed at the user’s request to eliminate supports. Panels have PLA and PETG project variants; hardware uses PETG.

## Retained findings

- Preserve one global slot lattice, including two-row accessory spacing.
- Keep the nominal tile translations fixed when adding a seam gap.
- Preserve the preferred S01 outline and 180° use.
- Keep four diagonal ribs and a substantially continuous perimeter.
- Leave room for the hook's downward movement behind boundary slots.
- Every tile has four independent wall mounts; inter-panel features serve alignment.
- Adding a tile beside multiple existing neighbours must use a common approach toward the wall.
- Use a removable front jig for positioning; leave no permanent inter-panel hardware.

## Remaining physical work

- The 5.2 mm strip fit was selected. Check the deeper full jig across both seam orientations during the full-size assembly.
- The user selected a 2.2 mm pilot. Check screw seating during the full-size assembly.
- Check actual printed accessories, particularly two-row accessories and seam-spanning mounts.
- Check the local rear hook relief and front screw-head clearance.
- Test the chosen tape on the actual wallpaper over time.
- Release a full printable current panel only after the fit prototype is accepted.
