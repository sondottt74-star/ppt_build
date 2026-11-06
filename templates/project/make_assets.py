"""{{TITLE}}: paper figures, formulas and diagrams -> ppt/assets/.

    python ppt/make_assets.py

Figure paths come from papers/<key>/index.md (F# entries); look at papers/<key>/figures_sheet_*.png
to choose. Crop one panel with tools/fig_grid.py to read PDF-point coordinates.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TALK = ROOT.parent
sys.path.insert(0, os.environ.get("PPT_BUILD", "{{PPT_BUILD}}"))

import numpy as np  # noqa: E402,F401
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle  # noqa: E402,F401

from pptkit.assets import AssetDir, plt  # noqa: E402
from pptkit.draw import (BLUE, BUILD, EDGE, IDLE, NAVY, OCC, TEAL, VIS, arrow, cov_wh, draw_blob,  # noqa: E402,F401
                         panel, round_box)

PAPERS = TALK / "papers"
A = AssetDir(ROOT / "assets")

# ---------------------------------------------------------------- paper figures
# name prefix = paper prefix from the outline (e.g. p1_, p2_ or sc_, oc_)
FIGS = {
{{FIGS}}
}
# single panels: name -> (paper-relative path, clip in PDF points | crop in pixels)
CROPS = {
    # "p1_ours": ("p1/src/images/main.pdf", (222, 26, 428, 155)),
}

# ---------------------------------------------------------------- formulas (mathtext; no Chinese, no \text)
FORMULAS = {
    # "f_mu": r"$\mu = x_v + O_v \odot l_v$",
}


# ---------------------------------------------------------------- diagrams (one function per d_ asset)
def fig_example():
    fig, ax = plt.subplots(figsize=(6.0, 3.0))
    panel(ax)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    round_box(ax, 0.5, 1.5, 3, 2, "输入", fc="#E8F0FE", ec=BLUE)
    arrow(ax, (3.7, 2.5), (6.2, 2.5))
    round_box(ax, 6.5, 1.5, 3, 2, "输出", fc="#E6F4F1", ec=TEAL)
    A.save_fig(fig, "d_example")


if __name__ == "__main__":
    for name, rel in FIGS.items():
        A.fig(name, PAPERS / rel)
    for name, (rel, box) in CROPS.items():
        path = PAPERS / rel
        A.fig(name, path, **({"clip": box} if path.suffix.lower() == ".pdf" else {"crop": box}))
    if FORMULAS:
        A.formulas(FORMULAS)
    fig_example()
    A.report()
