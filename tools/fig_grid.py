#!/usr/bin/env python3
"""Overlay a labelled coordinate grid on a figure to pick crop boxes for one panel.

    python tools/fig_grid.py papers/scaffold-gs/src/images/main.pdf          # -> /tmp/fig_grid/main_grid.png
    python tools/fig_grid.py fig.png --step 100 --out check/fig_grid.png

PDF figures are labelled in PDF points (use as AssetDir.fig(..., clip=(x0, y0, x1, y1)));
raster figures in pixels (use as crop=(l, t, r, b)). Read the output image, then verify the crop
by rendering it and reading that too.
"""
import argparse
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("figure", type=Path)
    ap.add_argument("--page", type=int, default=0)
    ap.add_argument("--step", type=float, help="grid step in figure units (default: ~12 lines across)")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    if args.figure.suffix.lower() == ".pdf":
        page = fitz.open(str(args.figure))[args.page]
        W, H = page.rect.width, page.rect.height
        scale = min(1600 / W, 1600 / H, 6)
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        unit = "pt"
    else:
        im = Image.open(args.figure).convert("RGB")
        W, H = im.size
        scale = min(1600 / W, 1600 / H, 1.0)
        im = im.resize((round(W * scale), round(H * scale)))
        unit = "px"
    step = args.step or max(1, round(max(W, H) / 12, -1 if max(W, H) > 200 else 0))
    d = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
    except Exception:
        font = ImageFont.load_default()
    def label(xy, text, color):
        box = d.textbbox(xy, text, font=font)
        d.rectangle([box[0] - 2, box[1] - 1, box[2] + 2, box[3] + 1], fill="white")
        d.text(xy, text, fill=color, font=font)

    v = 0.0
    while v <= W:
        x = v * scale
        d.line([(x, 0), (x, im.height)], fill=(255, 0, 80), width=1)
        label((x + 3, 3), f"{v:g}", (255, 0, 80))
        v += step
    v = 0.0
    while v <= H:
        y = v * scale
        d.line([(0, y), (im.width, y)], fill=(0, 120, 255), width=1)
        label((3, y + 3), f"{v:g}", (0, 120, 255))
        v += step
    out = args.out or Path("/tmp/fig_grid") / f"{args.figure.stem}_grid.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out)
    print(f"{out}  ({W:g} x {H:g} {unit}, grid every {step:g} {unit})")


if __name__ == "__main__":
    main()
