"""Build and verify the complete two-panel S01 physical-test kit."""

from pathlib import Path
import json
import cadquery as cq
import trimesh
from shapely.affinity import translate
from shapely.geometry import Point
from . import geometry as g, panel, alignment
from .wall_mount import make_self_tapping_wall_shoe
from .three_mf import plate

PANEL_NAME = "S01_panel"
SHOE_NAME = "wall_shoe_3x16_pilot_2p2"
JIG_NAME = "front_jig_5p2_deep_flat"


def mounted_shoes(dx=0, dy=0):
    for x, y in g.MOUNTS:
        shoe = make_self_tapping_wall_shoe(2.2)
        if y < 0:
            shoe = shoe.rotate((0, 0, 0), (0, 0, 1), 180)
        yield shoe.translate((x + dx, y + dy, 0))


def export_part(output, name, shape, flip=False):
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
        components=1,
    )


def build(output):
    output = Path(output).resolve()
    for folder in ("stl", "step", "projects", "images"):
        (output / folder).mkdir(parents=True, exist_ok=True)
    p = panel.make_panel()
    j = alignment.make_flat_jig()
    shoe = make_self_tapping_wall_shoe(2.2)
    parts = [
        export_part(output, PANEL_NAME, p),
        export_part(output, SHOE_NAME, shoe, True),
        export_part(output, JIG_NAME, j),
    ]
    a = cq.Assembly(name="S01_mounted_panel")
    a.add(p, name="panel", color=cq.Color(0.72, 0.78, 0.74))
    for n, s in enumerate(mounted_shoes()):
        a.add(s, name=f"shoe_{n + 1}", color=cq.Color(0.25, 0.5, 0.65))
    a.export(str(output / "step" / "S01_with_four_shoes.step"))
    a = cq.Assembly(name="two_hexes_with_front_jig")
    for n, (dx, dy) in enumerate(((0, 0), (180, 100))):
        a.add(
            p.translate((dx, dy, 0)),
            name=f"panel_{n + 1}",
            color=cq.Color(0.72, 0.78, 0.74),
        )
        for k, s in enumerate(mounted_shoes(dx, dy)):
            a.add(
                s, name=f"panel_{n + 1}_shoe_{k + 1}", color=cq.Color(0.25, 0.5, 0.65)
            )
    a.add(
        j.translate((80, 40, -4)), name="removable_jig", color=cq.Color(0.9, 0.6, 0.25)
    )
    a.export(str(output / "step" / "two_hexes_with_jig.step"))
    plate(output, "S01_panel", [(PANEL_NAME, 8.2, 28.2)])
    positions = [
        (SHOE_NAME, 42 + 44 * i, 56 + 64 * k) for k in range(2) for i in range(4)
    ]
    plate(output, "eight_wall_shoes", positions)
    plate(output, "flat_jig", [(JIG_NAME, 82, 98)])
    report = dict(
        status="full-size physical test kit",
        nominal_panel_mm=[240, 200],
        face_thickness_mm=5,
        total_panel_depth_mm=15,
        diagonal_ribs=4,
        diagonal_rib_section_mm=[2.4, 10],
        perimeter_width_mm=3.2,
        slot_mm=[5.3, 15.3],
        nominal_seam_gap_mm=0.3,
        wall_holes_mm=3.4,
        wall_pilot_mm=2.2,
        pilot_selection="user-selected; no separate pilot print requested",
        screw_mm=dict(thread=3, under_head_length=16, head_diameter=4.9, head_height=3),
        screw_tip_to_pilot_floor_mm=2.5,
        screw_tip_to_adhesive_mm=7,
        head_radial_bearing_mm=0.75,
        tape_area_per_shoe_mm=[30, 50],
        shoes_per_panel=4,
        adhesive_plane_from_face_mm=23,
        jig_locator_mm=[5.2, 15.2, 4.4],
        jig_rear_depth_reserve_mm=0.6,
        jig_handle=False,
        jig_width_fit="5.2 mm selected by user from PETG strip test",
        jig_new_depth_printed=False,
        no_permanent_seam_connectors=True,
        plate_contents=[
            dict(name="01 S01 panel A PETG", material="PETG", panels=1),
            dict(name="02 S01 panel B PETG", material="PETG", panels=1),
            dict(name="03 Eight wall shoes PETG", material="PETG", wall_shoes=8),
            dict(name="04 Flat jig PETG", material="PETG", jigs=1, supports=False),
        ],
        alternative_panel_project="S01_panel_P2S_PLA.3mf; identical geometry, PLA settings",
        parts=parts,
    )
    (output / "parameters.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Built complete S01 kit:", output)
    return report


def validate(output):
    output = Path(output).resolve()
    p = panel.make_panel()
    j = alignment.make_flat_jig()
    for axis in ((1, 0, 0), (0, 1, 0)):
        assert p.cut(p.mirror(axis)).Volume() < 1e-5
    relevant = [c for c in g.CENTRES if g.P.intersects(Point(c).buffer(12))]
    slots = (
        cq.Workplane("XY", origin=(0, 0, 0.01))
        .pushPoints(relevant)
        .slot2D(15.28, 5.28, 90)
        .extrude(14.98)
    )
    assert p.intersect(cq.Compound.makeCompound(slots.vals())).Volume() < 1e-6
    for s in mounted_shoes():
        assert p.intersect(s).Volume() < 1e-6
    placements = alignment.verify_placements()
    poses = []
    for row in placements:
        delta = row["neighbour_translation_mm"]
        assert g.P.intersection(translate(g.P, *delta)).area < 1e-9
        nb = p.translate((*delta, 0))
        points = row["locator_centres_mm"]
        cx = sum(q[0] for q in points) / 4
        cy = sum(q[1] for q in points) / 4
        for offset in (-2.0, -1.0, 0.0):
            tool = j.translate((cx, cy, offset - 4))
            overlap = (
                tool.intersect(p).Volume()
                + tool.intersect(nb.translate((0, 0, offset))).Volume()
            )
            assert overlap < 1e-5, (row["edge"], offset, overlap)
            poses.append(
                dict(
                    edge=row["edge"],
                    new_panel_front_offset_mm=offset,
                    collision_mm3=overlap,
                )
            )
        # Swept locator volume during withdrawal is contained in the seated
        # locator footprint; no barb or rear undercut exists.
    meshes = []
    for file in sorted((output / "stl").glob("*.stl")):
        mesh = trimesh.load_mesh(file, process=True)
        assert (
            mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split()) == 1
        )
        assert all(mesh.extents[:2] < 256)
        meshes.append(
            dict(
                file=file.name,
                watertight=True,
                components=1,
                size_mm=mesh.extents.tolist(),
            )
        )
    report = dict(
        status="PASS",
        symmetry_axes=2,
        open_slot_prisms=len(relevant),
        mounting_shoe_collisions=0,
        placement_checks=placements,
        jig_insertion_poses=poses,
        mesh_checks=meshes,
        physical_status="5.2 mm PETG strip accepted; full kit not yet printed",
        load_rating_kg=None,
    )
    (output / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        "PASS: clean panel, open slots, four shoes, six seams and 18 jig insertion poses"
    )
    return report
