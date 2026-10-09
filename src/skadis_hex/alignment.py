"""Removable front alignment jig and labelled PETG fit strips. Units: mm."""

from functools import lru_cache
from pathlib import Path
import json

import cadquery as cq
import trimesh
from shapely.affinity import translate
from shapely.geometry import box, Point, LineString
from shapely.ops import unary_union

from . import geometry as g
from .three_mf import plate

WIDTHS = (4.9, 5.1, 5.2)
PIN_POINTS = [(-40, -20), (40, -20), (-40, 20), (40, 20)]
BODY = 4.0
PROJECTION = 3.5


def jig_plan():
    return unary_union(
        [box(-46, -30, 46, -10), box(-46, 10, 46, 30), box(-8, -10, 8, 10)]
    )


@lru_cache(None)
def make_locator(width):
    if not 0 < width < 5.3:
        raise ValueError(
            "Locator width must be positive and smaller than the 5.3 mm slot"
        )
    return (
        cq.Workplane("XY", origin=(0, 0, BODY))
        .slot2D(width + 10, width, 90)
        .extrude(PROJECTION)
        .faces(">Z")
        .edges()
        .chamfer(min(0.4, width / 4))
        .val()
    )


def _label_plan(value):
    # Six-mm seven-segment numerals, independent of installed fonts.
    segments = {
        "a": [(0, 6), (3.6, 6)],
        "b": [(3.6, 6), (3.6, 3)],
        "c": [(3.6, 3), (3.6, 0)],
        "d": [(0, 0), (3.6, 0)],
        "e": [(0, 3), (0, 0)],
        "f": [(0, 6), (0, 3)],
        "g": [(0, 3), (3.6, 3)],
    }
    digits = {"1": "bc", "2": "abged", "4": "fgbc", "5": "afgcd", "9": "abfgcd"}
    strokes = []
    cursor = 0
    for char in value:
        if char == ".":
            strokes.append(Point(cursor + 0.35, 0.15).buffer(0.4))
            cursor += 1.8
        else:
            strokes.extend(
                LineString([(cursor + x, y) for x, y in segments[s]]).buffer(
                    0.32, cap_style=2
                )
                for s in digits[char]
            )
            cursor += 4.9
    shape = unary_union(strokes)
    x0, y0, x1, y1 = shape.bounds
    return translate(shape, -(x0 + x1) / 2, -(y0 + y1) / 2)


def _make_body(plan, points, width):
    shape = (
        g.extrude(plan, 0, BODY)
        .fuse(*[make_locator(width).translate((x, y, 0)) for x, y in points])
        .clean()
    )
    shape = shape.cut(
        *[g.extrude(p, BODY - 0.6, 0.7) for p in g.pieces(_label_plan(f"{width:.1f}"))]
    ).clean()
    assert shape.isValid() and len(shape.Solids()) == 1
    return shape


@lru_cache(None)
def make_jig(width=5.1):
    return _make_body(jig_plan(), PIN_POINTS, width)


@lru_cache(None)
def make_fit_strip(width):
    return _make_body(box(-8, -30, 8, 30), [(0, -20), (0, 20)], width)


def verify_placements():
    slots = {
        p: LineString([(p[0], p[1] - 5), (p[0], p[1] + 5)]).buffer(2.65, quad_segs=32)
        for p in g.CENTRES
    }
    rows = []
    for frame in g.frames():
        delta = tuple(float(v) for v in 2 * frame["mid"])
        other = translate(g.P, *delta)
        heads = unary_union(
            [
                Point(x + dx, y + dy).buffer(2.45)
                for dx, dy in [(0, 0), delta]
                for x, y in g.MOUNTS
            ]
        )
        choices = []
        for x, y in g.CENTRES:
            points = [(x, y), (x + 80, y), (x, y + 40), (x + 80, y + 40)]
            if not all(p in slots for p in points):
                continue
            owner = [
                0 if g.P.contains(slots[p]) else 1 if other.contains(slots[p]) else -1
                for p in points
            ]
            if owner.count(0) != 2 or owner.count(1) != 2:
                continue
            if not (
                owner[0] == owner[1]
                and owner[2] == owner[3]
                or owner[0] == owner[2]
                and owner[1] == owner[3]
            ):
                continue
            body = translate(jig_plan(), x + 40, y + 20)
            clearance = body.distance(heads)
            if clearance < 0.5:
                continue
            rank = (x + 40 - frame["mid"][0]) ** 2 + (y + 20 - frame["mid"][1]) ** 2
            choices.append((rank, points, owner, clearance))
        assert choices, f"No whole-slot placement for edge {frame['edge']}"
        _, points, owner, clearance = min(choices)
        rows.append(
            dict(
                edge=frame["edge"],
                neighbour_translation_mm=delta,
                locator_centres_mm=points,
                panel_ownership=owner,
                minimum_head_clearance_mm=float(clearance),
                minimum_slot_to_edge_mm=min(
                    slots[p].distance((g.P if o == 0 else other).boundary)
                    for p, o in zip(points, owner)
                ),
            )
        )
    return rows


def _export(output, name, shape):
    bb = shape.BoundingBox()
    placed = shape.translate((-bb.xmin, -bb.ymin, -bb.zmin))
    cq.exporters.export(
        placed,
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
        connected_components=1,
    )


def build(output):
    output = Path(output).resolve()
    for folder in ("stl", "step", "projects", "images"):
        (output / folder).mkdir(parents=True, exist_ok=True)
    parts = []
    strip_placements = []
    for i, width in enumerate(WIDTHS):
        size = str(width).replace(".", "p")
        strip = f"fit_strip_{size}"
        jig = f"front_jig_{size}"
        parts.append(_export(output, strip, make_fit_strip(width)))
        parts.append(_export(output, jig, make_jig(width)))
        strip_placements.append((strip, 85 + i * 26, 95))
        plate(output, jig, [(jig, 82, 95)])
    plate(output, "front_jig_fit_strips", strip_placements)
    report = dict(
        status="geometry checked; physical fit pending",
        body_mm=[92, 60, 4],
        locator_grid_mm=[80, 40],
        locator_projection_mm=PROJECTION,
        locator_lead_in_mm=0.4,
        locator_width_candidates_mm=WIDTHS,
        slot_mm=[5.3, 15.3],
        panel_face_mm=5,
        remaining_depth_to_panel_rear_mm=1.5,
        placement_checks=verify_placements(),
        print_orientation="flat front face on bed; locators upward",
        first_print="three labelled two-locator strips only",
        physical_fit_tested=False,
        full_four_locator_test_required=True,
        permanent_panel_connection=False,
        parts=parts,
    )
    (output / "parameters.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Built front alignment jig trial:", output)
    return report
