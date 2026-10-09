"""Publish only current print files, CAD and evidence from a checked build."""

from pathlib import Path
import sys, shutil, json, hashlib

root = Path(__file__).resolve().parents[1]
build = Path(sys.argv[1] if len(sys.argv) > 1 else "build/full-kit").resolve()
files = {
    "stl/S01_panel.stl": "PRINT_THIS/S01_panel.stl",
    "stl/wall_shoe_3x16_pilot_2p2.stl": "PRINT_THIS/S01_wall_mount_2p2.stl",
    "stl/front_jig_5p2_deep_flat.stl": "PRINT_THIS/S01_alignment_jig_5p2.stl",
    "projects/S01_full_test_kit_P2S_PETG_flat_jig.3mf": "PRINT_THIS/S01_complete_kit_PETG_P2S.3mf",
    "projects/S01_panel_P2S_PLA.3mf": "PRINT_THIS/S01_panel_PLA_P2S.3mf",
    "step/S01_panel.step": "cad/S01_panel.step",
    "step/S01_with_four_shoes.step": "cad/S01_with_four_shoes.step",
    "step/two_hexes_with_jig.step": "cad/two_hexes_with_jig.step",
    "step/wall_shoe_3x16_pilot_2p2.step": "cad/S01_wall_mount_2p2.step",
    "step/front_jig_5p2_deep_flat.step": "cad/S01_alignment_jig_5p2.step",
}
for name in [
    "parameters.json",
    "validation.json",
    "slicing_PETG.json",
    "slicing_PLA.json",
    "slicing_validation.json",
]:
    files[name] = "verification/current/" + name
for name in [
    "PETG_plate_1.png",
    "PETG_plate_2.png",
    "PETG_plate_3.png",
    "PETG_plate_4.png",
    "PLA_plate_1.png",
]:
    files["images/" + name] = "verification/current/images/" + name
assert all((build / src).is_file() for src in files), (
    "Build and slice both material projects before publishing"
)
for src, dest in files.items():
    target = root / dest
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(build / src, target)
paths = [root / dest for dest in files.values()] + [
    root / "PRINT_THIS/README.md",
    root / "docs/images/kit_overview.png",
]
manifest = {
    str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
    for p in sorted(paths)
    if p.exists()
}
(root / "verification/current/manifest.json").write_text(
    json.dumps(manifest, indent=2) + "\n"
)
print("Published current files in PRINT_THIS, cad and verification/current")
