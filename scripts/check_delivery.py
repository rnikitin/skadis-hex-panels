"""Check discoverability, immutable delivery hashes and native ready-to-print projects."""

from pathlib import Path
import json, zipfile, hashlib, re
from xml.etree import ElementTree as ET

root = Path(__file__).resolve().parents[1]
expected = {
    "S01_panel.stl",
    "S01_wall_mount_2p2.stl",
    "S01_alignment_jig_5p2.stl",
    "S01_complete_kit_PETG_P2S.3mf",
    "S01_panel_PLA_P2S.3mf",
    "README.md",
}
assert {p.name for p in (root / "PRINT_THIS").iterdir() if p.is_file()} == expected
manifest = json.loads((root / "verification/current/manifest.json").read_text())
for path, digest in manifest.items():
    assert hashlib.sha256((root / path).read_bytes()).hexdigest() == digest, path
for file, material, counts in [
    ("S01_complete_kit_PETG_P2S.3mf", "PETG", [1, 1, 8, 1]),
    ("S01_panel_PLA_P2S.3mf", "PLA", [1]),
]:
    with zipfile.ZipFile(root / "PRINT_THIS" / file) as z:
        assert z.testzip() is None
        cfg = json.loads(z.read("Metadata/project_settings.config"))
        assert cfg["filament_type"] == [material]
        assert (
            cfg["layer_height"] == "0.2"
            and cfg["wall_loops"] == "4"
            and cfg["sparse_infill_density"] == "100%"
        )
        plates = ET.fromstring(z.read("Metadata/slice_info.config")).findall("plate")
        assert len(plates) == len(counts)
        for i, (p, count) in enumerate(zip(plates, counts), 1):
            md = {m.get("key"): m.get("value") for m in p.findall("metadata")}
            assert md["outside"] == "false" and md["support_used"] == "false"
            layout = json.loads(z.read(f"Metadata/plate_{i}.json"))
            assert len(layout["bbox_objects"]) == count
            assert len(z.read(f"Metadata/plate_{i}.gcode")) > 1000
for p in [
    root / "README.md",
    root / "PRINT_THIS/README.md",
    root / "CONTRIBUTING.md",
    *(root / "docs").rglob("*.md"),
]:
    for target in re.findall(r"\]\(([^)]+)\)", p.read_text()):
        if not target.startswith(("http:", "https:", "mailto:", "#")):
            assert (p.parent / target.split("#")[0]).exists(), (p, target)
print(
    "PASS: only final print files are exposed; hashes, native projects and documentation links verified"
)
