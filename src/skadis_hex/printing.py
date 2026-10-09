from pathlib import Path
import sys, json, subprocess, zipfile, shutil
from .three_mf import plate


def slice_geometry_project(output, geometry_stem, project_stem, slicer=None):
    import os

    ROOT = Path(output).resolve()
    default = "/Applications/BambuStudio.app/Contents/MacOS/BambuStudio"
    executable = str(
        slicer
        or os.environ.get("BAMBU_STUDIO")
        or shutil.which("BambuStudio")
        or default
    )
    if not Path(executable).is_file():
        raise RuntimeError(
            "Bambu Studio was not found; pass --slicer /path/to/executable"
        )
    work = ROOT.parent / f"slice-work-{ROOT.name}"
    work.mkdir(parents=True, exist_ok=True)
    profiles = work / "profiles"
    profiles.mkdir(exist_ok=True)
    original = Path(__file__).with_name("print_profiles")
    for name in ("machine", "filament"):
        shutil.copy2(original / f"{name}.json", profiles / f"{name}.json")
    p = json.loads((original / "process.json").read_text())
    p.update(
        wall_generator="arachne",
        initial_layer_speed=["25"] * 3,
        initial_layer_infill_speed=["40"] * 3,
        outer_wall_speed=["60"] * 3,
        inner_wall_speed=["120"] * 3,
    )
    (profiles / "process.json").write_text(json.dumps(p, indent=2) + "\n")
    cmd = [
        executable,
        "--datadir",
        str(work / "bambu-data"),
        "--load-settings",
        str(profiles / "machine.json") + ";" + str(profiles / "process.json"),
        "--load-filaments",
        str(profiles / "filament.json"),
        "--arrange",
        "0",
        "--orient",
        "0",
        "--slice",
        "0",
        "--export-3mf",
        f"{project_stem}.3mf",
        "--outputdir",
        str(work),
        str(ROOT / "projects" / f"{geometry_stem}_geometry.3mf"),
    ]
    with (work / "cli.log").open("w") as log:
        r = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT)
    assert r.returncode == 0, work / "cli.log"
    file = work / f"{project_stem}.3mf"
    with zipfile.ZipFile(file) as z:
        assert z.testzip() is None
        names = [n for n in z.namelist() if n.endswith(".gcode")]
        assert names
        g = z.read(names[0]).decode()
        stats = [
            line
            for line in g.splitlines()[:160]
            if "model printing time:" in line or "total filament weight" in line
        ]
        cfg = json.loads(z.read("Metadata/project_settings.config"))
        assert (
            cfg["wall_generator"] == "arachne"
            and cfg["sparse_infill_density"] == "100%"
        )
        (ROOT / "images" / "test_plate.png").write_bytes(z.read("Metadata/plate_1.png"))
    shutil.copy2(file, ROOT / "projects" / file.name)
    (ROOT / "slicing_validation.json").write_text(
        json.dumps(
            dict(
                exit_code=0,
                toolpaths_generated=True,
                statistics=stats,
                settings="P2S0.4/PLA/0.2mm/4walls/100%/Arachne",
                physical_print_started=False,
            ),
            indent=2,
        )
        + "\n"
    )
    print(stats)


def main(output, slicer=None):
    ROOT = Path(output).resolve()
    parts = {
        p["name"]: p
        for p in json.loads((ROOT / "parameters.json").read_text())["parts"]
    }
    names = ["corner_NEW", "corner_EXISTING_oblique", "corner_EXISTING_horizontal"] + [
        "spring_key_24x8x3p2"
    ] * 4
    placements = []
    x = y = 12.0
    row = 0
    for name in sorted(names, key=lambda n: -parts[n]["size_mm"][1]):
        w, h, _ = parts[name]["size_mm"]
        if x + w > 244:
            x = 12
            y += row + 8
            row = 0
        assert y + h < 244
        placements.append((name, x, y))
        x += w + 8
        row = max(row, h)
    plate(ROOT, "corner_fit_test", placements)
    slice_geometry_project(
        ROOT, "corner_fit_test", "corner_fit_test_24x8x3p2_P2S", slicer
    )
