# Current S01 design

## Shared lattice and contour

Slot centres use `x = 20 i + 20`, `y = 40 j + 20 (i mod 2)`. Tile translations `(180,100)` and `(0,200)` preserve this lattice, including 40 mm vertical spacing for two-row accessories.

The nominal 240 × 200 mm hex has vertices `(120,0), (60,100), (-60,100), (-120,0), (-60,-100), (60,-100)`. A 0.15 mm inward contour offset produces a 0.3 mm nominal seam without changing centre positions. Actual bounds are approximately 239.65 × 199.70 mm. The panel is symmetric and can rotate by 180°.

Working slots are 5.3 × 15.3 mm capsules. Boundary slots are completed by the neighbouring tile; no lattice positions are shifted or deliberately omitted near a seam.

## Structure

The face is 5 mm thick. Four 2.4 mm wide diagonal ribs follow `x+y=±40` and `x−y=±40`, reaching depth 15 mm from the front face. The perimeter rib is 3.2 mm wide and reaches the same rear plane.

Perimeter reliefs are local 9.3 × 25.3 mm capsules, allowing 2 mm around the working slot plus 3 mm additional vertical travel in both directions. Mirroring this allowance preserves 180° use. The actual hook body and downward insertion movement remain part of the full-size physical test.

There are no key receivers, retaining lips, dowel sockets or connector pads in the current panel. Four separate 3.4 mm mounting holes at `(±40,±40)` keep working SKÅDIS slots available.

## Wall mounting

Each panel has four independent PETG shoes. The selected 2.2 mm blind pilot accepts the user's nominal 3 × 16 mm self-tapper as a thread-forming assembly. The adhesive plane is 23 mm behind the panel face. See [hardware](hardware.md) for the screw stack and orientation.

## Removable alignment jig

The 92 × 60 × 4 mm body consists of two horizontal bars and a central spine. Four locators occupy an 80 × 40 mm rectangle. The user selected 5.2 mm width from the PETG strip trial; locator length is 15.2 mm. The full kit increases projection from 3.5 to 4.4 mm, retaining 0.6 mm before the panel's rear face.

The jig is one flat printable solid. It sits directly on the bed with the locators upward and needs no supports. A pull-knob variant was rejected because of its support requirements.

The same jig fits all six seam directions with vertical locators. Each placement uses two complete slots per panel. Its planar body clears the selected screw heads by at least 7.55 mm. The tool withdraws straight forward and leaves no hardware in the slots.

## Evidence boundaries

CAD checks cover connected watertight meshes, symmetry, open slots, shoe collisions, six seam placements and 18 insertion poses. Native Bambu projects have verified material assignments, support settings, plate bounds, object counts and generated toolpaths.

The 5.2 mm PETG strip is the physically selected fit. The deeper flat jig, selected screw pilot, full panel, accessories and adhesive mounting remain the next physical test. No new structural load rating is claimed. Superseded key geometry remains available through the `legacy-*` commands and archived release files.
