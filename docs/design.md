# Design specification

## Shared lattice

Slot centres use `x = 20 i + 20`, `y = 40 j + 20 (i mod 2)`. The nominal lattice is preserved across tile translations `(180, 100)` and `(0, 200)`, including the 40 mm vertical spacing required by two-row accessories.

The S01 nominal outline has vertices `(120,0), (60,100), (-60,100), (-120,0), (-60,-100), (60,-100)`. It is 240 × 200 mm before the contour inset. A 0.15 mm inward offset creates the nominal 0.3 mm seam without changing the lattice or centre positions. The panel can rotate by 180°.

Working slots are 5.3 × 15.3 mm capsules. Slots intersecting a boundary remain partial slots and are completed by the neighbouring tile. Near-seam positions are never shifted to make the outline look cleaner.

## Panel structure

The face is 5 mm thick. Four diagonal ribs follow `x+y=±40` and `x−y=±40`, with a 2.4 mm width and 10 mm height. The rear envelope is 15 mm from the face. The perimeter rib is 3.2 mm wide, with local slot-shaped hook relief rather than the early 16 × 34 mm rectangular exclusions.

The current rear relief starts with a 2 mm local allowance and an additional 3 mm vertical travel allowance. It is mirrored above/below to retain 180° use. The actual hook body and its downward insertion movement still require physical verification. These rear clearances do not enlarge the front working slots.

## Hidden alignment key

The current key envelope is 24 × 8 × 3.2 mm. Its centre web is 4 mm wide; rounded longitudinal splits create 1 mm spring arms with a nominal 9.7 mm working length. The wider tapered shoulders provide handling area and locate the panels.

Key-shaped receiver pockets are open toward the wall. A 0.25 mm outline allowance provides installation clearance. Small 45° ramps create a nominal 0.1 mm interference per arm. The key sits at depth 9–12.2 mm; retaining ramps occupy 12.5–13.2 mm, inside the 15 mm rib envelope.

On sloping seams the key follows a 45° free corridor in the lattice. Key centres alternate inside/outside the seam; the corresponding pockets on the opposite tile match. Horizontal seams use keys perpendicular to the seam. One key shape serves all six directions; two keys are planned per complete seam.

The keys control relative alignment. They are not the load path for a neighbouring panel: every panel has four independent wall shoes.

## Validation boundaries

The CAD insertion check prescribes 0.18 mm spring-tip movement and checks continuous swept volumes. It establishes geometric room for the proposed deformation, not the real insertion force, friction, printed anisotropy, strength or fatigue life.

The analytical uniform-beam root-strain estimate is about 0.29%. It is only a design estimate. The physical fit test remains necessary.
