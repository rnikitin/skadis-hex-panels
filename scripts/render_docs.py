"""Render English documentation figures from saved results and current geometry."""

from pathlib import Path
import json
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path as MPath
from matplotlib.patches import PathPatch
from shapely.geometry import box, LineString
from shapely.ops import unary_union
from skadis_hex import joints as j

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "docs/images"
BG = "#f5f2ea"
INK = "#243b3b"


def draw(ax, polygon, colour):
    paths = []
    for ring in [polygon.exterior, *polygon.interiors]:
        xy = np.array(ring.coords)
        paths.append(
            MPath(
                xy, [MPath.MOVETO] + [MPath.LINETO] * (len(xy) - 2) + [MPath.CLOSEPOLY]
            )
        )
    ax.add_patch(
        PathPatch(
            MPath.make_compound_path(*paths), facecolor=colour, edgecolor=INK, lw=0.7
        )
    )


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    old = unary_union(
        [
            box(-6.35, -1.2, 6.35, 1.2),
            box(-7.35, -2.2, -6.35, 2.2),
            box(6.35, -2.2, 7.35, 2.2),
        ]
    )
    for sign in (-1, 1):
        old = old.difference(
            LineString([(sign * 1.1, 0), (sign * 8, 0)]).buffer(0.4, quad_segs=16)
        )
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), facecolor=BG)
    fig.subplots_adjust(top=0.72, bottom=0.22, left=0.06, right=0.96, wspace=0.25)
    fig.text(
        0.06,
        0.91,
        "Larger replaceable alignment key",
        fontsize=23,
        weight="bold",
        color=INK,
    )
    fig.text(
        0.06,
        0.82,
        "Both views use the same scale. Current key: 24 x 8 x 3.2 mm.",
        fontsize=12,
        color=INK,
    )
    for ax, shape, colour, title, size in zip(
        axes,
        [old, j.key_plan()],
        ["#bfaa84", "#408bac"],
        ["Previous v1", "Current v2"],
        ["14.7 x 4.4 x 2.4 mm", "24 x 8 x 3.2 mm"],
    ):
        draw(ax, shape, colour)
        ax.set_xlim(-14, 14)
        ax.set_ylim(-6, 6)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(title, fontsize=16, color=INK, pad=18)
        ax.text(
            0.5,
            -0.15,
            size,
            ha="center",
            fontsize=13,
            color=INK,
            transform=ax.transAxes,
        )
    fig.text(
        0.06,
        0.06,
        "Use matching v2 receivers. Physical fit and retention remain to be tested.",
        fontsize=11,
        color=INK,
    )
    fig.savefig(DEST / "key-size-comparison.png", dpi=160, facecolor=BG)
    plt.close(fig)

    data = json.loads((ROOT / "analysis/v3/calculation_summary.json").read_text())
    values = [case["max_out_of_plane_mm"] for case in data["cases"]]
    fig, ax = plt.subplots(figsize=(8, 4.8), facecolor=BG)
    ax.set_facecolor(BG)
    bars = ax.bar(
        ["Centre", "Side", "Upper edge"],
        values,
        color=["#9bb8ad", "#729ca9", "#be935a"],
    )
    ax.bar_label(bars, labels=[f"{value:.3f} mm" for value in values], padding=5)
    ax.set_ylim(0, 1.35)
    ax.set_ylabel("Maximum out-of-plane displacement (mm)")
    ax.set_title("Historical v3: 3 kg at 100 mm from the wall", pad=16)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(
        0.08,
        0.02,
        "Earlier geometry and idealized supports; not a current-panel or adhesive load rating.",
        fontsize=9,
        color=INK,
    )
    fig.subplots_adjust(bottom=0.15, top=0.84)
    fig.savefig(DEST / "v3-deflections.png", dpi=160, facecolor=BG)
    plt.close(fig)


if __name__ == "__main__":
    main()
