"""Create an English contact sheet from verified native Bambu previews."""

from pathlib import Path
from PIL import Image
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parents[1] / "models/full_kit/images"
parts = [
    ("PETG_plate_1.png", "S01 panel", "239.65 × 199.70 × 15 mm"),
    ("PETG_plate_3.png", "Eight wall shoes", "3 × 16 mm screws · 2.2 mm pilots"),
    ("PETG_plate_4.png", "Flat alignment jig", "5.2 × 15.2 × 4.4 mm locators"),
]
fig, axs = plt.subplots(1, 3, figsize=(12, 4.2), facecolor="#111111")
for ax, (file, title, caption) in zip(axs, parts):
    img = Image.open(root / file).convert("RGBA")
    bounds = img.getbbox()
    if bounds:
        img = img.crop(bounds)
    ax.imshow(img)
    ax.set_axis_off()
    ax.set_title(title, color="#eeeeee", fontsize=14, pad=14)
    ax.text(
        0.5,
        -0.07,
        caption,
        transform=ax.transAxes,
        ha="center",
        color="#dddddd",
        fontsize=10,
    )
fig.subplots_adjust(left=0.03, right=0.97, bottom=0.13, top=0.85, wspace=0.14)
fig.savefig(root / "kit_overview.png", dpi=150, facecolor=fig.get_facecolor())
plt.close(fig)
