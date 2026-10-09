"""Fit trial for user-supplied nominal3x16 socket-head self-tappers.

Product diagram: thread3, under-head length16, head4.9 diameter x3 height.
No metric nut or modeled thread is used. Pilot retention requires a print test.
"""

from pathlib import Path
import json, math
import cadquery as cq
import trimesh
from shapely.geometry import LineString, Point
from shapely.ops import unary_union
from . import geometry as g, joints
from .wall_mount import make_self_tapping_wall_shoe
from .three_mf import plate

PILOTS = (2.2, 2.4, 2.6)
COLUMNS = (-24, 0, 24)


def _engraved_label(label, x):
    # Portable5mm vector digits: no OS/font dependency and no tiny L/N/T marks.
    paths = {
        "a": [(0, 5), (3, 5)],
        "b": [(3, 5), (3, 2.5)],
        "c": [(3, 2.5), (3, 0)],
        "d": [(0, 0), (3, 0)],
        "e": [(0, 0), (0, 2.5)],
        "f": [(0, 2.5), (0, 5)],
        "g": [(0, 2.5), (3, 2.5)],
    }
    digits = {"2": "abged", "4": "fgbc", "6": "afgecd"}
    shapes = []
    for index, char in enumerate(label):
        offset = x - 4.2 + index * 3.6
        if char == ".":
            shapes.append(Point(offset + 0.6, -11.7).buffer(0.35))
            continue
        for segment in digits[char]:
            shapes.append(
                LineString(
                    [(offset + px, -12 + py) for px, py in paths[segment]]
                ).buffer(0.3, cap_style=2)
            )
    return unary_union(shapes)


def pilot_test_block():
    base = cq.Workplane("XY").rect(70, 30).extrude(3).val()
    posts = [g.cylinder(6, 3, 15, x, 3) for x in COLUMNS]
    shape = base.fuse(*posts).clean()
    cuts = []
    for x, pilot in zip(COLUMNS, PILOTS):
        cuts.append(g.cylinder(pilot / 2, 4.5, 13.6, x, 3))
        cuts.append(cq.Solid.makeCone(pilot / 2, 1.7, 0.6, cq.Vector(x, 3, 17.4)))
        cuts.extend(
            g.extrude(p, 2.35, 0.75)
            for p in g.pieces(_engraved_label(f"{pilot:.1f}", x))
        )
    return shape.cut(*cuts).clean()


def five_mm_test_plate():
    shape = cq.Workplane("XY", origin=(0, 3, 0)).rect(70, 14).extrude(5).val()
    return shape.cut(*[g.cylinder(1.7, -0.1, 5.2, x, 3) for x in COLUMNS]).clean()


def mounting_panel_coupon():
    crop = g.extrude(g.box(22, 8, 58, 72), -0.1, 15.2)
    part = joints.panel(wall_hole_diameter=3.4).intersect(crop).clean()
    assert len(part.Solids()) == 1
    return part


def _export(output, name, shape, flip=False):
    assert shape.isValid() and len(shape.Solids()) == 1, name
    printable = shape.rotate((0, 0, 0), (1, 0, 0), 180) if flip else shape
    bb = printable.BoundingBox()
    printable = printable.translate((-bb.xmin, -bb.ymin, -bb.zmin))
    cq.exporters.export(
        printable,
        str(output / "stl" / f"{name}.stl"),
        tolerance=0.012,
        angularTolerance=0.08,
    )
    cq.exporters.export(shape, str(output / "step" / f"{name}.step"))
    mesh = trimesh.load_mesh(output / "stl" / f"{name}.stl", process=True)
    assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split()) == 1
    return dict(
        name=name,
        size_mm=[bb.xlen, bb.ylen, bb.zlen],
        volume_cm3=shape.Volume() / 1000,
        watertight=True,
    )


def build(output):
    output = Path(output).resolve()
    for folder in ("stl", "step", "projects", "images"):
        (output / folder).mkdir(parents=True, exist_ok=True)
    parts = [
        _export(output, "pilot_test_2p2_2p4_2p6", pilot_test_block()),
        _export(output, "five_mm_clearance_plate_3p4", five_mm_test_plate()),
        _export(output, "mounting_coupon_self_tapping_3p4", mounting_panel_coupon()),
    ]
    for pilot in PILOTS:
        parts.append(
            _export(
                output,
                f"wall_shoe_self_tapping_3x16_pilot_{str(pilot).replace('.', 'p')}",
                make_self_tapping_wall_shoe(pilot),
                True,
            )
        )
    names = [
        "pilot_test_2p2_2p4_2p6",
        "five_mm_clearance_plate_3p4",
        "mounting_coupon_self_tapping_3p4",
        "wall_shoe_self_tapping_3x16_pilot_2p4",
    ]
    data = {p["name"]: p for p in parts}
    positions = []
    x = y = 12.0
    row = 0
    for name in sorted(names, key=lambda n: -data[n]["size_mm"][1]):
        w, h, _ = data[name]["size_mm"]
        if x + w > 244:
            x = 12
            y += row + 8
            row = 0
        assert y + h < 244
        positions.append((name, x, y))
        x += w + 8
        row = max(row, h)
    plate(output, "self_tapping_3x16_fit", positions)
    plate(
        output,
        "self_tapping_3x16_pilot_test",
        [
            ("pilot_test_2p2_2p4_2p6", 12, 12),
            ("five_mm_clearance_plate_3p4", 12, 50),
        ],
    )
    report = dict(
        status="nominal geometry checked; pilot retention and actual screw tolerances pending",
        product_diagram=dict(
            major_diameter_mm=3,
            under_head_length_mm=16,
            head_diameter_mm=4.9,
            head_height_mm=3,
            source="user-supplied product dimension diagram",
        ),
        panel_thickness_mm=5,
        panel_clearance_hole_mm=3.4,
        pilot_candidates_mm=PILOTS,
        prototype_default_pilot_mm=2.4,
        pilot_selected_by_physical_test=False,
        shoe_front_z_mm=5,
        pilot_floor_z_mm=18.5,
        adhesive_surface_z_mm=23,
        tip_z_mm=16,
        penetration_into_shoe_including_point_mm=11,
        clearance_to_pilot_floor_mm=2.5,
        clearance_to_adhesive_mm=7,
        head_radial_bearing_margin_mm=(4.9 - 3.4) / 2,
        previous_4p5_hole_head_radial_margin_mm=(4.9 - 4.5) / 2,
        bearing_area_mm2=math.pi / 4 * (4.9**2 - 3.4**2),
        nut_required=False,
        washer_in_trial=False,
        parts=parts,
        important="Test through the5mm plate: bare16mm screw exceeds the13.5mm pilot depth",
        thread_pitch="not specified; no ISO metric nut compatibility assumed",
        physical_fit="NOT TESTED",
        load_rating_kg=None,
    )
    (output / "parameters.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Built self-tapping fit trial:", output)
    return report
