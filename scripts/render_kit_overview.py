"""Create an English contact sheet from studio renders of the released STL files."""

from pathlib import Path
from PIL import Image
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parents[1] / "docs/images"
parts = [
    ("S01_rear_oblique.png", "Two S01 panels", "239.65 × 199.70 × 15 mm"),
    ("S01_mounts.png", "Eight wall shoes", "3 × 16 mm screws · 2.2 mm pilots"),
    ("S01_jig.png", "Flat alignment jig", "5.2 × 15.2 × 4.4 mm locators"),
]
fig, axs = plt.subplots(1, 3, figsize=(12, 4.2), facecolor="#e6e8e9")
for ax, (file, title, caption) in zip(axs, parts):
    img = Image.open(root / file).convert("RGBA")
    bounds = img.getbbox()
    if bounds:
        img = img.crop(bounds)
    ax.imshow(img)
    ax.set_axis_off()
    ax.set_title(title, color="#24272a", fontsize=14, pad=14)
    ax.text(
        0.5,
        -0.07,
        caption,
        transform=ax.transAxes,
        ha="center",
        color="#34383c",
        fontsize=10,
    )
fig.subplots_adjust(left=0.03, right=0.97, bottom=0.13, top=0.85, wspace=0.14)
fig.savefig(
    root / "kit_overview.png",
    dpi=150,
    facecolor=fig.get_facecolor(),
)
plt.close(fig)
