#!/usr/bin/env python3
"""Lint a .pptx for layout problems and render it to page images + contact sheets.

    python tools/check_deck.py deck.pptx                 # lint + render to <deck_dir>/check/
    python tools/check_deck.py deck.pptx --pages 5 12    # also print paths of those pages
    python tools/check_deck.py deck.pptx --no-render     # lint only

Lint rules (heuristic, CJK-aware text measurement):
  OUT      shape leaves the 13.333 x 7.5 canvas
  OVERFLOW text needs more height than its card / table row gives it
  OVERLAP  two elements partially overlap (pictures, tables, charts, cards, text)
  SMALL    font below 10 pt
  DENSE    more than --max-chars characters of text on one slide
  BLURRY   picture placed at < 110 px per inch
Containment (text inside a card, label inside a figure) is not an overlap.
  MISSING  placeholder for an asset that does not exist yet
  STACK    pictures stacked on purpose (info only)
Exit code 1 if any OUT / OVERFLOW / OVERLAP / MISSING issue is found.
"""
from __future__ import annotations

import argparse
import math
import os
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.shapes.connector import Connector

EMU = 914400
SW, SH = 13.333, 7.5


# ------------------------------------------------------------------ text measurement
def char_em(ch):
    if ch == " ":
        return 0.28
    if unicodedata.east_asian_width(ch) in ("W", "F"):
        return 1.0
    if ch in "ilIjft.,:;'|!()[]{}":
        return 0.3
    if ch.isupper() or ch in "mwMW@%&":
        return 0.64
    return 0.5


def para_size(p, default=18.0):
    for r in p.runs:
        if r.font.size:
            return r.font.size.pt
    return default


def text_height(tf, width_in, default_size=18.0, leading=1.2):
    """Estimated rendered height (inches) of a text frame at a given inner width.

    leading=1.2 approximates PowerPoint's single line pitch; 1.0 approximates the glyph extent.
    """
    total = 0.0
    paras = list(tf.paragraphs)
    for k, p in enumerate(paras):
        size = para_size(p, default_size)
        em_in = size / 72
        text = "".join(r.text for r in p.runs) or " "
        indent = 0.0
        pPr = p._p.pPr
        if pPr is not None and pPr.get("marL"):
            indent = int(pPr.get("marL")) / EMU
        avail = max(width_in - indent, 0.2)
        lines = 0
        for seg in text.split("\n"):
            w = sum(char_em(c) for c in seg) * em_in
            lines += max(1, math.ceil(w / avail))
        spacing = p.line_spacing if isinstance(p.line_spacing, float) else 1.0
        after = p.space_after.pt / 72 if p.space_after is not None and k < len(paras) - 1 else 0.0
        total += lines * em_in * leading * spacing + after
    return total


def single_line_width(tf):
    """Widest paragraph width (inches) if no paragraph contains a line break, else None."""
    widest = 0.0
    for p in tf.paragraphs:
        text = "".join(r.text for r in p.runs)
        if "\n" in text:
            return None
        widest = max(widest, sum(char_em(c) for c in text) * para_size(p) / 72)
    return widest


def frame_margins(tf):
    def m(v, d):
        return (v if v is not None else d) / EMU
    return (m(tf.margin_left, 91440), m(tf.margin_right, 91440), m(tf.margin_top, 45720), m(tf.margin_bottom, 45720))


# ------------------------------------------------------------------ element extraction
class El:
    def __init__(self, kind, x, y, w, h, label, text_len=0, sizes=()):
        self.kind, self.x, self.y, self.w, self.h = kind, x, y, w, h
        self.label, self.text_len, self.sizes = label, text_len, sizes

    @property
    def box(self):
        return self.x, self.y, self.x + self.w, self.y + self.h

    def area(self):
        return max(self.w, 0) * max(self.h, 0)


def short(text, n=18):
    t = " ".join(text.split())
    return t if len(t) <= n else t[:n] + "…"


def extract(slide):
    els, issues = [], []
    for sh in slide.shapes:
        if isinstance(sh, Connector) or sh.width is None:
            continue
        if sh.name.startswith("MISSING:"):
            issues.append(("MISSING", f"缺图占位：{sh.name[8:]}"))
            continue
        x, y, w, h = sh.left / EMU, sh.top / EMU, sh.width / EMU, sh.height / EMU
        if sh.shape_type == MSO_SHAPE_TYPE.PICTURE:
            el = El("picture", x, y, w, h, f"图片 {Path(sh.image.filename or 'img').stem}")
            try:
                px_w = sh.image.size[0]
                el.ppi = px_w / max(w, 1e-3)
            except Exception:
                el.ppi = None
            els.append(el)
            continue
        if sh.has_chart:
            els.append(El("chart", x, y, w, h, "图表"))
            continue
        if sh.has_table:
            tbl = sh.table
            real_h, tlen, sizes = 0.0, 0, []
            for r_i, row in enumerate(tbl.rows):
                need = row.height / EMU
                for c_i, cell in enumerate(row.cells):
                    if cell.is_spanned:
                        continue
                    cw = tbl.columns[c_i].width / EMU
                    if cell.is_merge_origin:
                        cw = sum(tbl.columns[c_i + k].width for k in range(cell.span_width)) / EMU
                    l, r, t, b = frame_margins(cell.text_frame)
                    th = text_height(cell.text_frame, cw - l - r, leading=1.1) + t + b
                    if cell.is_merge_origin and cell.span_height > 1:
                        th /= cell.span_height
                    need = max(need, th)
                    tlen += len(cell.text_frame.text)
                    sizes += [para_size(p, 18) for p in cell.text_frame.paragraphs if p.runs]
                real_h += need
            el = El("table", x, y, w, real_h, "表格", tlen, sizes)
            if real_h > h + 0.08:
                issues.append(("OVERFLOW", f"表格行被文字撑高：标称高 {h:.2f}，估计实际 {real_h:.2f} in"))
            els.append(el)
            continue
        if not sh.has_text_frame:
            els.append(El("shape", x, y, w, h, "形状"))
            continue
        tf = sh.text_frame
        text = tf.text.strip()
        sizes = [para_size(p, 18) for p in tf.paragraphs if p.runs]
        is_textbox = sh.shape_type == MSO_SHAPE_TYPE.TEXT_BOX
        if not text:
            els.append(El("card", x, y, w, h, "空卡片"))
            continue
        l, r, t, b = frame_margins(tf)
        if is_textbox:
            # textboxes do not clip; use the estimated glyph extent (top-anchored) for overlap tests
            need = text_height(tf, w - l - r, leading=1.0) + t + b
            eff_h = need if tf.vertical_anchor in (None, MSO_ANCHOR.TOP) else max(h, need)
            eff_x, eff_w = x, w
            tw = single_line_width(tf)
            if tw is not None and tw + l + r < w:
                eff_w = tw + l + r
                align = tf.paragraphs[0].alignment
                if align == PP_ALIGN.CENTER:
                    eff_x = x + (w - eff_w) / 2
                elif align == PP_ALIGN.RIGHT:
                    eff_x = x + w - eff_w
            els.append(El("text", eff_x, y, eff_w, eff_h, f"文字「{short(text)}」", len(text), sizes))
        else:
            need = text_height(tf, w - l - r, leading=1.1) + t + b
            if need > h + 0.06:
                issues.append(("OVERFLOW", f"卡片「{short(text)}」放不下：高 {h:.2f}，需要约 {need:.2f} in"))
            els.append(El("card", x, y, w, h, f"卡片「{short(text)}」", len(text), sizes))
    return els, issues


def inter(a, b):
    """(area, thinnest side) of the intersection rectangle."""
    ax0, ay0, ax1, ay1 = a.box
    bx0, by0, bx1, by1 = b.box
    iw = max(0, min(ax1, bx1) - max(ax0, bx0))
    ih = max(0, min(ay1, by1) - max(ay0, by0))
    return iw * ih, min(iw, ih)


def contains(a, b, tol=0.03):
    ax0, ay0, ax1, ay1 = a.box
    bx0, by0, bx1, by1 = b.box
    return ax0 - tol <= bx0 and ay0 - tol <= by0 and bx1 <= ax1 + tol and by1 <= ay1 + tol


def lint_slide(slide, max_chars):
    els, issues = extract(slide)
    full_bg = [e for e in els if e.w >= SW - 0.05 and e.h >= 3.0]
    els = [e for e in els if e not in full_bg]
    for e in els:
        x0, y0, x1, y1 = e.box
        if x0 < -0.02 or y0 < -0.02 or x1 > SW + 0.02 or y1 > SH + 0.02:
            issues.append(("OUT", f"{e.label} 超出画布：({x0:.2f}, {y0:.2f}) – ({x1:.2f}, {y1:.2f})"))
        if e.kind == "picture" and getattr(e, "ppi", None) and e.ppi < 110:
            issues.append(("BLURRY", f"{e.label} 分辨率偏低：{e.ppi:.0f} px/in"))
        if any(s < 10 for s in e.sizes):
            issues.append(("SMALL", f"{e.label} 字号 {min(e.sizes):.0f} pt < 10"))
    for i in range(len(els)):
        for j in range(i + 1, len(els)):
            a, b = els[i], els[j]
            ov, thin = inter(a, b)
            if ov <= 0.015 or thin < 0.08:
                continue
            if contains(a, b) or contains(b, a):
                continue
            small = min(a.area(), b.area())
            if small <= 0 or ov / small < 0.04:
                continue
            if a.kind in ("card", "shape") and b.kind in ("card", "shape") and not (a.text_len and b.text_len):
                continue
            kind = "STACK" if a.kind == b.kind == "picture" and ov / small > 0.5 else "OVERLAP"
            issues.append((kind, f"{a.label} ↔ {b.label}：重叠 {ov:.2f} in²（{ov / small:.0%}）"))
    chars = sum(e.text_len * (0.5 if e.kind == "table" else 1) for e in els)
    if chars > max_chars:
        issues.append(("DENSE", f"文字约 {chars:.0f} 字 > {max_chars}，考虑拆页或删句"))
    return issues


# ------------------------------------------------------------------ rendering
def find_soffice():
    for c in ("soffice", "libreoffice", "/Applications/LibreOffice.app/Contents/MacOS/soffice"):
        p = shutil.which(c) or (c if Path(c).exists() else None)
        if p:
            return p
    return None


def render(pptx, out, dpi=80, cols=3, rows=4):
    import fitz
    from PIL import Image, ImageDraw, ImageFont

    soffice = find_soffice()
    if not soffice:
        print("[render] LibreOffice not found (brew install --cask libreoffice); skipped")
        return None
    out.mkdir(parents=True, exist_ok=True)
    profile = Path(tempfile.gettempdir()) / "lo_profile_check_deck"
    cmd = [soffice, f"-env:UserInstallation=file://{profile}", "--headless", "--convert-to", "pdf",
           "--outdir", str(out), str(pptx)]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
    pdf = out / (pptx.stem + ".pdf")
    pages_dir = out / "pages"
    if pages_dir.exists():
        shutil.rmtree(pages_dir)
    pages_dir.mkdir()
    doc = fitz.open(str(pdf))
    paths = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=dpi, alpha=False)
        p = pages_dir / f"p{i + 1:02d}.png"
        pix.save(str(p))
        paths.append(p)
    doc.close()

    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
    except Exception:
        font = ImageFont.load_default()
    sheets = []
    per = cols * rows
    for s in range(0, len(paths), per):
        ims = [Image.open(p) for p in paths[s:s + per]]
        w, h = ims[0].size
        pad, lab = 12, 30
        sheet = Image.new("RGB", (cols * (w + pad) + pad, rows * (h + pad + lab) + pad), (226, 230, 236))
        d = ImageDraw.Draw(sheet)
        for k, im in enumerate(ims):
            cx, cy = pad + (k % cols) * (w + pad), pad + (k // cols) * (h + pad + lab)
            d.text((cx, cy), f"P{s + k + 1}", fill=(31, 58, 95), font=font)
            sheet.paste(im, (cx, cy + lab))
        p = out / f"sheet_{s // per + 1:02d}.png"
        sheet.save(p)
        sheets.append(p)
    return pdf, paths, sheets


def dump_slides(prs, path):
    """Page number, title and every text run per slide: the 逐字稿 is written against this file."""
    L = []
    for n, slide in enumerate(prs.slides, 1):
        texts, title, best = [], "", 0
        for sh in slide.shapes:
            if sh.has_text_frame and sh.text_frame.text.strip():
                t = " / ".join(t for t in sh.text_frame.text.split("\n") if t.strip())
                texts.append(t)
                size = max((para_size(p, 0) for p in sh.text_frame.paragraphs if p.runs), default=0)
                if size > best and not t.isdigit():
                    title, best = t, size
            elif getattr(sh, "has_table", False) and sh.has_table:
                texts.append("[表格] " + " | ".join(c.text_frame.text for c in sh.table.rows[0].cells))
            elif getattr(sh, "has_chart", False) and sh.has_chart:
                texts.append("[图表] " + (sh.chart.chart_title.text_frame.text if sh.chart.has_title else ""))
            elif sh.shape_type == MSO_SHAPE_TYPE.PICTURE:
                texts.append("[图片]")
        body = [t for t in texts if not t.isdigit()]
        L.append(f"## P{n} {title}")
        L += [f"- {t}" for t in body]
        L.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(L))
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pptx", type=Path)
    ap.add_argument("--out", type=Path, help="default: <pptx dir>/check")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--dpi", type=int, default=80, help="page image dpi (use 150 to inspect one page)")
    ap.add_argument("--max-chars", type=int, default=450)
    ap.add_argument("--pages", type=int, nargs="*", help="print paths for these page numbers")
    args = ap.parse_args()

    pptx = args.pptx.resolve()
    prs = Presentation(str(pptx))
    severe = 0
    print(f"== lint {pptx.name}: {len(prs.slides)} slides, {pptx.stat().st_size / 1e6:.1f} MB")
    for n, slide in enumerate(prs.slides, 1):
        for kind, msg in lint_slide(slide, args.max_chars):
            severe += kind in ("OUT", "OVERFLOW", "OVERLAP", "MISSING")
            print(f"  P{n:<3} {kind:<8} {msg}")
    print(f"== {severe} blocking issue(s)" if severe else "== no blocking issues")
    out = (args.out or pptx.parent / "check").resolve()
    print(f"== slide text: {dump_slides(prs, out / 'slides.md')}")

    if not args.no_render:
        res = render(pptx, out, dpi=args.dpi)
        if res:
            pdf, pages, sheets = res
            print(f"== rendered {pdf}")
            for s in sheets:
                print(f"   sheet: {s}")
            for n in args.pages or []:
                if 1 <= n <= len(pages):
                    print(f"   page {n}: {pages[n - 1]}")
    sys.exit(1 if severe else 0)


if __name__ == "__main__":
    main()
