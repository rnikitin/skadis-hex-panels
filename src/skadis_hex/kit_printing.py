"""Native multi-plate PETG kit and matching standalone PLA panel project.

The Bambu Studio 2.8 CLI crashes when a later plate uses filament index 2.
Each delivered project therefore has one material; no G-code is patched.
The documented --load-assemble-list interface creates plate membership.
"""

from pathlib import Path
import json
import os
import shutil
import subprocess
import zipfile
from xml.etree import ElementTree as ET
from . import kit


def assembly_list(panel_only=False):
    def obj(name, x, y, support=False):
        result = dict(
            path=f"stl/{name}.stl",
            count=1,
            filaments=[1],
            pos_x=[x],
            pos_y=[y],
            pos_z=[0],
            print_params={"enable_support": "1" if support else "0"},
        )
        if support:
            result["print_params"].update(
                support_type="tree(auto)", support_on_build_plate_only="1"
            )
        return result

    def plate(name, objects):
        return dict(
            plate_name=name,
            need_arrange=False,
            objects=objects,
            plate_params={
                "filament_map_mode": "Auto For Flush",
                "filament_map": "1",
                "filament_volume_map": "0",
            },
        )

    if panel_only:
        return dict(
            plates=[
                plate("S01 panel - PLA alternative", [obj(kit.PANEL_NAME, 8.2, 28.2)])
            ]
        )
    return dict(
        plates=[
            plate("01 S01 panel A - PETG", [obj(kit.PANEL_NAME, 8.2, 28.2)]),
            plate("02 S01 panel B - PETG", [obj(kit.PANEL_NAME, 8.2, 28.2)]),
            plate(
                "03 Eight wall shoes - PETG",
                [
                    obj(kit.SHOE_NAME, 42 + 44 * x, 56 + 64 * y)
                    for y in range(2)
                    for x in range(4)
                ],
            ),
            plate("04 Flat alignment jig - PETG", [obj(kit.JIG_NAME, 82, 98)]),
        ]
    )


def validate_project(file, output, material, panel_only=False):
    output = Path(output)
    result = []
    expected_counts = [1] if panel_only else [1, 1, 8, 1]
    with zipfile.ZipFile(file) as z:
        assert z.testzip() is None
        cfg = json.loads(z.read("Metadata/project_settings.config"))
        assert cfg["filament_type"] == [material], cfg["filament_type"]
        assert cfg["layer_height"] == "0.2" and cfg["wall_loops"] == "4"
        assert (
            cfg["sparse_infill_density"] == "100%"
            and cfg["wall_generator"] == "arachne"
        )
        settings = ET.fromstring(z.read("Metadata/model_settings.config"))
        plates = settings.findall("plate")
        assert len(plates) == len(expected_counts), len(plates)
        info = ET.fromstring(z.read("Metadata/slice_info.config")).findall("plate")
        assert len(info) == len(expected_counts)
        objects = settings.findall("object")
        assert len(objects) == sum(expected_counts), len(objects)
        support_objects = []
        for o in objects:
            md = {m.get("key"): m.get("value") for m in o.findall("metadata")}
            if md.get("enable_support") == "1":
                support_objects.append(md["name"])
        assert not support_objects, support_objects
        for i, (plate, count) in enumerate(zip(plates, expected_counts), 1):
            md = {m.get("key"): m.get("value") for m in info[i - 1].findall("metadata")}
            supports = False
            assert md["outside"] == "false", (i, md)
            assert md["support_used"] == str(supports).lower(), (i, md["support_used"])
            actual = {
                f.get("type")
                for f in info[i - 1].findall("filament")
                if float(f.get("used_g", "0")) > 0
            }
            assert actual == {material}, (i, actual)
            layout = json.loads(z.read(f"Metadata/plate_{i}.json"))
            assert len(layout["bbox_objects"]) == count, (
                i,
                len(layout["bbox_objects"]),
            )
            assert layout["filament_ids"] == [0], (i, layout["filament_ids"])
            bounds = layout["bbox_all"]
            assert min(bounds[:2]) >= 0 and max(bounds[2:]) <= 256, (i, bounds)
            gcode = z.read(f"Metadata/plate_{i}.gcode").decode()
            assert (
                "; CHANGE_LAYER" in gcode or "; layer num/total_layer_count:" in gcode
            )
            (output / "images" / f"{material}_plate_{i}.png").write_bytes(
                z.read(f"Metadata/plate_{i}.png")
            )
            result.append(
                dict(
                    plate=i,
                    name=assembly_list(panel_only)["plates"][i - 1]["plate_name"],
                    material=material,
                    objects=count,
                    seconds=int(md["prediction"]),
                    grams=float(md["weight"]),
                    supports=supports,
                    bounds_mm=bounds,
                    warnings=[w.attrib for w in info[i - 1].findall("warning")],
                )
            )
    report = dict(
        status="PASS",
        native_project=Path(file).name,
        plates=result,
        layer_height_mm=0.2,
        walls=4,
        infill="100%",
        physical_print_started=False,
    )
    (output / f"slicing_{material}.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))
    return report


def _slice_one(output, slicer, material, panel_only):
    project = (
        "S01_panel_P2S_PLA" if panel_only else "S01_full_test_kit_P2S_PETG_flat_jig"
    )
    work = output.parent / f"slice-work-{output.name}-{material}"
    work.mkdir(parents=True, exist_ok=True)
    profiles = work / "profiles"
    profiles.mkdir(exist_ok=True)
    original = Path(__file__).with_name("print_profiles")
    shutil.copy2(original / "machine.json", profiles / "machine.json")
    filament = (
        "filament_pla_generic.json" if material == "PLA" else "filament_petg.json"
    )
    shutil.copy2(original / filament, profiles / "filament.json")
    p = json.loads((original / "process.json").read_text())
    p.update(
        wall_generator="arachne",
        initial_layer_speed=["25"] * 3,
        initial_layer_infill_speed=["40"] * 3,
        outer_wall_speed=["60"] * 3,
        inner_wall_speed=["120"] * 3,
        enable_support="0",
        filament_map=["1"],
        filament_volume_map=["0"],
        filament_map_mode="Auto For Flush",
    )
    (profiles / "process.json").write_text(json.dumps(p, indent=2) + "\n")
    assembly = output / "projects" / f"{material}_assembly.json"
    assembly.write_text(json.dumps(assembly_list(panel_only), indent=2) + "\n")
    executable = str(
        slicer
        or os.environ.get("BAMBU_STUDIO")
        or shutil.which("BambuStudio")
        or "/Applications/BambuStudio.app/Contents/MacOS/BambuStudio"
    )
    if not Path(executable).is_file():
        raise RuntimeError("Bambu Studio executable not found")
    cmd = [
        executable,
        "--datadir",
        str(work / "bambu-data"),
        "--load-settings",
        f"{profiles}/machine.json;{profiles}/process.json",
        "--load-filaments",
        str(profiles / "filament.json"),
        "--load-assemble-list",
        str(assembly),
        "--arrange",
        "0",
        "--orient",
        "0",
        "--slice",
        "0",
        "--export-3mf",
        project + ".3mf",
        "--outputdir",
        str(work),
    ]
    with (work / "cli.log").open("w") as log:
        result = subprocess.run(cmd, cwd=output, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(
            f"Bambu Studio exit {result.returncode}; see {work / 'cli.log'}"
        )
    file = work / (project + ".3mf")
    report = validate_project(file, output, material, panel_only)
    shutil.copy2(file, output / "projects" / file.name)
    return report


def slice_project(output, slicer=None):
    output = Path(output).resolve()
    reports = [
        _slice_one(output, slicer, "PETG", False),
        _slice_one(output, slicer, "PLA", True),
    ]
    (output / "slicing_validation.json").write_text(
        json.dumps(dict(status="PASS", projects=reports), indent=2) + "\n"
    )
    return reports
