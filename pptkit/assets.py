"""Asset generation: paper figures -> PNG, LaTeX formulas -> transparent PNG, figure saving.

Typical make_assets.py:

    from pptkit.assets import AssetDir
    A = AssetDir(TALK / "ppt" / "assets")
    A.fig("sc_pipeline", PAPERS / "scaffold-gs/src/images/pipeline.pdf")      # paths from papers/<key>/index.md
    A.fig("sc_ours", PAPERS / "scaffold-gs/src/images/main.pdf", clip=(222, 26, 428, 155))  # one panel, PDF points
    A.fig("px_framework", PAPERS / "proxy-gs/src/figures/framework.png")
    A.formulas({"f_mu": r"$\\mu = x_v + O \\odot l_v$"})
    fig, ax = plt.subplots(); ...; A.save_fig(fig, "d_overview")
"""
from __future__ import annotations

import os
import re
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")

import fitz  # noqa: E402
import matplotlib  # noqa: E402
from PIL import Image, ImageChops, ImageDraw  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

CJK_FONTS = [
    ("/Library/Fonts/Arial Unicode.ttf", "Arial Unicode MS"),
    ("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", "Arial Unicode MS"),
    ("/System/Library/Fonts/Hiragino Sans GB.ttc", "Hiragino Sans GB"),
    ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "Noto Sans CJK SC"),
]


def setup_matplotlib():
    """CJK-capable sans font for diagrams, Computer Modern for mathtext."""
    for path, family in CJK_FONTS:
        if Path(path).exists():
            font_manager.fontManager.addfont(path)
            plt.rcParams["font.family"] = family
            break
    plt.rcParams["mathtext.fontset"] = "cm"
    plt.rcParams["axes.unicode_minus"] = False


setup_matplotlib()


def trim(img, pad=6):
    """Crop surrounding white margin."""
    bg = Image.new("RGB", img.size, (255, 255, 255))
    bbox = ImageChops.difference(img.convert("RGB"), bg).getbbox()
    if not bbox:
        return img
    l, t, r, b = bbox
    return img.crop((max(l - pad, 0), max(t - pad, 0), min(r + pad, img.width), min(b + pad, img.height)))


def _flatten(im):
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[-1])
        return bg
    return im.convert("RGB")


# mathtext has no \text, \operatorname, \boldsymbol variants beyond these; map common LaTeX to it
_TEX_FIXES = [
    (r"\\text\{", r"\\mathrm{"),
    (r"\\textrm\{", r"\\mathrm{"),
    (r"\\textbf\{", r"\\mathbf{"),
    (r"\\operatorname\*?\{", r"\\mathrm{"),
    (r"\\bm\{", r"\\boldsymbol{"),
    (r"\\mathbbm\{", r"\\mathbb{"),
    (r"\\coloneqq", r":="),
    (r"\\eqqcolon", r"=:"),
    (r"\\left\\\|", r"\\|"),
    (r"\\right\\\|", r"\\|"),
    (r"\\tfrac", r"\\frac"),
    (r"\\mathds\{", r"\\mathbb{"),
]


def sanitize_tex(tex):
    for a, b in _TEX_FIXES:
        tex = re.sub(a, b, tex)
    if not tex.strip().startswith("$"):
        tex = f"${tex.strip()}$"
    return tex


class AssetDir:
    """Writes every asset as <out>/<name>.png. Name prefixes: one per paper (e.g. sc_, oc_),
    f_ for formulas, d_ for self-drawn diagrams."""

    def __init__(self, out, max_px=3000):
        self.out = Path(out)
        self.out.mkdir(parents=True, exist_ok=True)
        self.max_px = max_px

    def path(self, name):
        return self.out / f"{name}.png"

    # -------------------------------------------------- paper figures
    def _dpi(self, rect, dpi):
        # keep raster width <= max_px; fitz needs an int dpi
        return max(1, int(min(dpi, self.max_px * 72 / rect.width)))

    def pdf(self, name, path, clip=None, page=0, pad=6, dpi=260):
        """Rasterize a figure PDF (arXiv source figures are usually one-page PDFs).

        clip = (x0, y0, x1, y1) in PDF points of that page.
        """
        doc = fitz.open(str(path))
        pg = doc[page]
        rect = fitz.Rect(*clip) if clip else pg.rect
        pix = pg.get_pixmap(dpi=self._dpi(rect, dpi), alpha=False, clip=rect if clip else None)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        trim(img, pad).save(self.path(name))
        doc.close()
        return self.path(name)

    page = pdf  # cropping a region from the full paper PDF is the same call with page/clip

    def fig(self, name, path, clip=None, crop=None, pad=6):
        """Any figure file from the LaTeX source: .pdf (clip in PDF points), .png/.jpg (crop in pixels), .eps."""
        path = Path(path)
        ext = path.suffix.lower()
        if ext == ".pdf":
            return self.pdf(name, path, clip=clip, pad=pad)
        if ext in (".eps", ".ps"):
            im = Image.open(path)
            im.load(scale=4)  # needs ghostscript (brew install ghostscript)
            return self.image(name, im, crop=crop, pad=pad)
        return self.image(name, path, crop=crop, pad=pad)

    def image(self, name, path, crop=None, pad=6):
        """Copy a raster figure (png/jpg or an opened PIL image), flattening alpha onto white. crop = pixel box."""
        im = _flatten(path if isinstance(path, Image.Image) else Image.open(path))
        if crop:
            im = im.crop(crop)
        im = trim(im, pad)
        if im.width > self.max_px:
            im = im.resize((self.max_px, round(im.height * self.max_px / im.width)), Image.LANCZOS)
        im.save(self.path(name))
        return self.path(name)

    def frame(self, name, pad=14, outline=(201, 211, 227)):
        """Add a white mat and thin border (for stacked thumbnails)."""
        im = Image.open(self.path(name)).convert("RGB")
        canvas = Image.new("RGB", (im.width + 2 * pad, im.height + 2 * pad), "white")
        canvas.paste(im, (pad, pad))
        ImageDraw.Draw(canvas).rectangle([0, 0, canvas.width - 1, canvas.height - 1], outline=outline)
        canvas.save(self.path(name))

    def crop_frac(self, src, name, box):
        """Crop an existing asset by fractions (l, t, r, b) in [0, 1]."""
        im = Image.open(self.path(src))
        l, t, r, b = box
        im.crop((int(l * im.width), int(t * im.height), int(r * im.width), int(b * im.height))).save(self.path(name))

    # -------------------------------------------------- formulas & figures
    def formulas(self, mapping, fontsize=30, dpi=250, color="#1B1B1B"):
        """Render {name: tex}. Chinese never goes inside formulas; put it in a slide textbox."""
        failed = []
        for name, tex in mapping.items():
            fig = plt.figure(figsize=(0.1, 0.1))
            fig.text(0, 0, sanitize_tex(tex), fontsize=fontsize, color=color)
            try:
                fig.savefig(self.path(name), dpi=dpi, bbox_inches="tight", pad_inches=0.04, transparent=True)
            except ValueError as e:
                failed.append((name, str(e).splitlines()[0]))
            plt.close(fig)
        for name, err in failed:
            print(f"[formula FAILED] {name}: {err}")
        if failed:
            raise SystemExit(f"{len(failed)} formula(s) failed; simplify them for mathtext")

    def save_fig(self, fig, name, dpi=220):
        fig.savefig(self.path(name), dpi=dpi, bbox_inches="tight", pad_inches=0.04, transparent=True)
        plt.close(fig)
        return self.path(name)

    def report(self):
        files = sorted(self.out.glob("*.png"))
        print(f"assets -> {self.out}  count {len(files)}")
        return files
