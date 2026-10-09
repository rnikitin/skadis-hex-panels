# Historical front-jig width trial

The user selected the **5.2 mm** PETG strip. The current [full-size kit](assembly.md) uses a flat jig with 4.4 mm-deep locators and no handle or supports. The original trials below remain reference files; printing them again is not required.

The next print is the [three-strip PETG fit trial](../archive/prototypes/alignment_fit/projects/front_jig_fit_strips_P2S_PETG.3mf). Estimated on P2S with a 0.4 mm nozzle: **32 minutes and 15.71 g**. The project has been sliced; no physical fit has been verified.

## First print and selection

1. Print the three labelled strips in PETG at 100% scale, flat body face down and locators upward. The project uses 0.2 mm layers, four walls, 100% infill, no supports and the installed Generic PETG P2S material preset (255 °C nozzle, 70 °C textured plate). Use settings appropriate to the actual spool if different.
2. On an existing printed panel or test fragment, choose two complete slots in one column, 40 mm centre-to-centre. Do not use slots split by a seam. Support the panel by hand while testing.
3. Start with **4.9**, then try **5.1** and **5.2**. The number is the locator width in millimetres; its overall capsule length is the number plus 10 mm. Both locators must enter simultaneously until the strip's flat back touches the panel face.
4. Select the largest candidate that slides in by hand, has little lateral play and pulls out easily. Do not use a press fit or force a stuck strip. If all are tight or all are loose, report that result before printing the full jig.
5. Report each strip as **loose / sliding fit / tight**, and whether it seats flat and removes easily.

The nominal slot is 5.3 × 15.3 mm. These candidates leave 0.4, 0.2 or 0.1 mm total dimensional clearance respectively, before printing error. The 5.1 mm candidate is provisional, not an already selected fit.

## Full jig after the strip test

Matching full-jig STLs are in [the archived width-trial STLs](../archive/prototypes/alignment_fit/stl): `front_jig_4p9.stl`, `front_jig_5p1.stl`, and `front_jig_5p2.stl`. Print only the selected size.

The body is 92 × 60 × 4 mm: two horizontal 20 mm bars and a 16 mm central spine. The four vertical capsule locators form an 80 × 40 mm rectangle and project 3.5 mm from the seating face, with a 0.4 mm tip lead-in. At full seating they remain 1.5 mm short of the rear of the 5 mm panel face. There are no hooks, rear locks or permanent panel pockets.

Before adhesive mounting, test the full jig on two supported panels across both a horizontal and a sloping seam. A two-point strip checks local fit and a 40 mm pitch, but does not establish the four-point fit over 80 mm. All four locators must engage, both panel faces must seat against the jig, and the jig must withdraw easily without moving the panels.

The six nominal placements have two complete slots per panel and at least 7.55 mm clearance from the purchased 4.9 mm screw heads. The locators stay vertical for every seam; do not rotate the jig by 90°.

## Wall positioning

Keep each panel on its own four wall shoes. Bring the new panel close to its intended plane, engage the jig with both panels while supporting the new panel, and align the lattice before the adhesive touches the wall. Press the shoes onto the wall, hold the panels in position and withdraw the jig straight forward by its central spine or edges.

This tool is an alignment aid; it does not suspend the new panel or establish adhesive capacity. After removal all working slots are available again. The separate [3 × 16 mm wall-shoe pilot trial](self-tapping-3x16.md) remains necessary before choosing a pilot diameter.

## Regeneration

```sh
uv run skadis-hex jig-fit --output build/alignment-fit
uv run skadis-hex slice-jig-fit --output build/alignment-fit
uv run pytest -q
```

`slice-jig-fit` defaults to PETG. Use `--material PLA` only if the physical trial will use PLA. Core geometry 3MF files carry no printer settings; the named `P2S_PETG` project contains the verified slicer settings. STL/STEP, parameters, mesh checks, placement evidence and slicing statistics are retained in the trial directory.
