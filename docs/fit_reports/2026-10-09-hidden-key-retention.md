# Hidden-key print feedback — 2026-10-09

## Observed outcome

The user reports that the printed key falls out of the rear-open receiver easily, does not seat tightly, and allows the board assembly to wobble. The current retention design has failed its physical fit test. The user is comfortable reducing the key length.

The exact printed revision and material have been requested and are not yet reconfirmed for this particular test. A close-up of the printed receiver is needed to distinguish missing/rounded retaining features from dimensional clearance.

## Verified design facts for v2

- Key neck width: 4 mm.
- Peak retaining throat: 3.8 mm, giving only 0.1 mm nominal overlap per arm.
- Receiver-outline allowance: 0.25 mm per side.
- Retainers are small triangular ramps rather than a continuous rear capture shelf.
- Ramp depth range: 12.5–13.2 mm, with the maximum projection at 12.85 mm.
- The supplied slicing profile uses 0.2 mm layers.

Ideal section sampling at layer mid-planes 12.7/12.9/13.1 mm reaches approximately 0/0.05/0 mm overlap. This is an analysis of the CAD ramp and layer sampling, not a measurement of the actual printed extrusion boundary.

## Current hypothesis and next evidence

The nominal capture is too small to be robust to the slicing and printed dimensions; the generous receiver clearance separately explains part of the play. This hypothesis has not yet been confirmed by measuring the actual print.

Inspect the printed retaining features and measure the key neck and receiver width before selecting the next dimensions. The replacement should have a clearly defined rear capture feature and controlled alignment clearance. A shorter key is permitted; its spring travel and release path must be checked again rather than scaling the previous key blindly.

The existing CAD tests only establish a possible insertion envelope under prescribed arm deformation. They do not validate holding force. No replacement connection is released by this report.
