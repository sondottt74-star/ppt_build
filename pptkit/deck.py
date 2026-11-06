"""Slide chrome and native PowerPoint components (python-pptx).

All coordinates are inches on a 13.333 x 7.5 canvas. Component functions take the
slide as their first argument; `Deck` owns the presentation, page numbers, footers,
breadcrumbs and image placement.
"""
from __future__ import annotations

from pathlib import Path

from lxml import etree
from PIL import Image
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

from .theme import (FONT, FOOT_GREY, LATIN, LIGHT, LINE, NAVY, ORANGE, RED, SLIDE_H, SLIDE_W, SUB, TEXT,
                    WARN_CELL, YELLOW, C1L)


def I(v):
    return Emu(int(v * 914400))


def rgb(h):
    return RGBColor.from_string(h)


# ------------------------------------------------------------------ text
def style_run(run, size, bold=False, color=TEXT, italic=False):
    f = run.font
    f.size = Pt(size)
    f.bold = bold
    f.italic = italic
    f.color.rgb = rgb(color)
    rPr = run._r.get_or_add_rPr()
    for tag, face in (("a:latin", LATIN), ("a:ea", FONT), ("a:cs", LATIN)):
        el = rPr.find(qn(tag))
        if el is None:
            el = etree.SubElement(rPr, qn(tag))
        el.set("typeface", face)


def fill_para(p, text, size, color=TEXT, bold=False, accent=None):
    """`**x**` segments are bold and drawn in `accent` (default NAVY)."""
    for k, seg in enumerate(text.split("**")):
        if not seg:
            continue
        r = p.add_run()
        r.text = seg
        hl = k % 2 == 1
        style_run(r, size, bold=bold or hl, color=(accent or NAVY) if hl else color)


def _margins(tf, lr=0.04, tb=0.04):
    tf.margin_left = tf.margin_right = I(lr)
    tf.margin_top = tf.margin_bottom = I(tb)


def textbox(slide, x, y, w, h, lines, size=16, color=TEXT, bold=False, align=PP_ALIGN.LEFT,
            anchor=MSO_ANCHOR.TOP, accent=None, spacing=1.15, space_after=4):
    tb = slide.shapes.add_textbox(I(x), I(y), I(w), I(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    _margins(tf)
    for i, line in enumerate([lines] if isinstance(lines, str) else lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        p.space_after = Pt(space_after)
        fill_para(p, line, size, color, bold, accent)
    return tb


def bullets(slide, x, y, w, h, items, size=16, color=TEXT, accent=None, bullet_color=None, gap=6):
    """items: str or (str, level). Level-1 items are 2 pt smaller and grey."""
    tb = slide.shapes.add_textbox(I(x), I(y), I(w), I(h))
    tf = tb.text_frame
    tf.word_wrap = True
    _margins(tf)
    for i, it in enumerate(items):
        text, lvl = (it, 0) if isinstance(it, str) else it
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = 1.12
        p.space_after = Pt(gap)
        pPr = p._p.get_or_add_pPr()
        pPr.set("marL", str(int(I(0.26 + 0.3 * lvl))))
        pPr.set("indent", str(-int(I(0.24))))
        clr = etree.SubElement(etree.SubElement(pPr, qn("a:buClr")), qn("a:srgbClr"))
        clr.set("val", bullet_color or accent or NAVY)
        etree.SubElement(pPr, qn("a:buSzPct")).set("val", "100000")
        etree.SubElement(pPr, qn("a:buFont")).set("typeface", LATIN)
        etree.SubElement(pPr, qn("a:buChar")).set("char", "•" if lvl == 0 else "–")
        fill_para(p, text, size if lvl == 0 else size - 2, color if lvl == 0 else SUB, False, accent)
    return tb


def box(slide, x, y, w, h, text="", fill=LIGHT, line=None, size=14, color=TEXT, bold=False,
        shape=MSO_SHAPE.ROUNDED_RECTANGLE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
        accent=None, line_w=1.25, radius=0.12, dash=False):
    """Card / pill / circle / diamond. `text` may be a list of lines."""
    s = slide.shapes.add_shape(shape, I(x), I(y), I(w), I(h))
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    s.shadow.inherit = False
    if fill:
        s.fill.solid()
        s.fill.fore_color.rgb = rgb(fill)
    else:
        s.fill.background()
    if line:
        s.line.color.rgb = rgb(line)
        s.line.width = Pt(line_w)
        if dash:
            etree.SubElement(s.line._get_or_add_ln(), qn("a:prstDash")).set("val", "dash")
    else:
        s.line.fill.background()
    tf = s.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    _margins(tf, 0.08, 0.04)
    for i, line_text in enumerate(text if isinstance(text, list) else [text]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = 1.08
        fill_para(p, line_text, size, color, bold, accent)
    return s


def circle(slide, x, y, d, text, fill, size=14):
    return box(slide, x, y, d, d, text, fill=fill, size=size, color="FFFFFF", bold=True, shape=MSO_SHAPE.OVAL)


def rect(slide, x, y, w, h, fill):
    r = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, I(x), I(y), I(w), I(h))
    r.fill.solid()
    r.fill.fore_color.rgb = rgb(fill)
    r.line.fill.background()
    r.shadow.inherit = False
    return r


def hline(slide, x, y, w, color=LINE, h=0.02):
    return rect(slide, x, y, w, h, color)


def arrow(slide, x1, y1, x2, y2, color=NAVY, width=2.0, dash=False):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, I(x1), I(y1), I(x2), I(y2))
    c.line.color.rgb = rgb(color)
    c.line.width = Pt(width)
    ln = c.line._get_or_add_ln()
    if dash:
        etree.SubElement(ln, qn("a:prstDash")).set("val", "dash")
    t = etree.SubElement(ln, qn("a:tailEnd"))
    t.set("type", "triangle")
    t.set("w", "med")
    t.set("len", "med")
    return c


def caption(slide, x, y, w, text, size=11, align=PP_ALIGN.CENTER):
    """Figure caption. Write '论文原图（Paper）：…' or '示意：…'."""
    return textbox(slide, x, y, w, 0.35, text, size=size, color=SUB, align=align)


def num_card(slide, x, y, w, h, big, small, fill=LIGHT, accent=NAVY, line=None):
    """Big number on top, one-line meaning below."""
    return box(slide, x, y, w, h, [f"**{big}**", small], fill=fill, line=line, size=13, accent=accent)


# ------------------------------------------------------------------ tables & charts
_MARKS = (("‹r›", RED), ("‹o›", ORANGE), ("‹y›", YELLOW), ("‹w›", WARN_CELL))


def table(slide, x, y, w, data, col_w=None, size=11, header_rows=1, row_h=0.32,
          header_fill=NAVY, first_col_bold=True, hl_row=None, hl_fill=C1L, first_col_colors=None):
    """Native table. Cell strings may end with ‹r›/‹o›/‹y›/‹w› (best / 2nd / 3rd / warning).

    hl_row: row index (or list) of "our method" rows. None cells are left empty.
    """
    rows, cols = len(data), len(data[0])
    gt = slide.shapes.add_table(rows, cols, I(x), I(y), I(w), I(row_h * rows))
    t = gt.table
    tblPr = t._tbl.tblPr
    tblPr.set("bandRow", "0")
    tblPr.set("firstRow", "0")
    if col_w:
        for j, cw in enumerate(col_w):
            t.columns[j].width = I(cw)
    hls = hl_row if isinstance(hl_row, (list, tuple, set)) else ([] if hl_row is None else [hl_row])
    for i in range(rows):
        t.rows[i].height = I(row_h)
        for j in range(cols):
            raw = data[i][j]
            cell = t.cell(i, j)
            if raw is None:
                continue
            mark = None
            for m, col in _MARKS:
                if raw.endswith(m):
                    raw, mark = raw[: -len(m)], col
            cell.margin_left = cell.margin_right = I(0.04)
            cell.margin_top = cell.margin_bottom = I(0.02)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER if j > 0 or i < header_rows else PP_ALIGN.LEFT
            r = p.add_run()
            r.text = raw
            is_head, is_hl = i < header_rows, i in hls
            col = "FFFFFF" if is_head else TEXT
            if not is_head and j == 0 and first_col_colors:
                col = first_col_colors[i - header_rows]
            elif is_hl and j == 0:
                col = NAVY
            style_run(r, size, bold=is_head or (j == 0 and first_col_bold) or is_hl, color=col)
            cell.fill.solid()
            if is_head:
                cell.fill.fore_color.rgb = rgb(header_fill)
            elif mark:
                cell.fill.fore_color.rgb = rgb(mark)
            elif is_hl:
                cell.fill.fore_color.rgb = rgb(hl_fill)
            else:
                cell.fill.fore_color.rgb = rgb("FFFFFF" if i % 2 else "F7F9FC")
    return t


def merge_col0(t, pairs):
    """Merge first-column cells for (start_row, end_row) pairs, e.g. one dataset over two methods."""
    for a, b in pairs:
        keep = t.cell(a, 0).text_frame.text
        t.cell(a, 0).merge(t.cell(b, 0))
        tf = t.cell(a, 0).text_frame
        for p in list(tf.paragraphs)[1:]:
            p._p.getparent().remove(p._p)
        if tf.paragraphs[0].runs:
            tf.paragraphs[0].runs[0].text = keep
        t.cell(a, 0).fill.solid()
        t.cell(a, 0).fill.fore_color.rgb = rgb("FFFFFF")


def legend_marks(slide, x, y, labels=("最好", "第二", "第三")):
    """Small swatches explaining ‹r›/‹o›/‹y› under a table."""
    for k, (lab, col) in enumerate(zip(labels, (RED, ORANGE, YELLOW))):
        rect(slide, x + k * 1.3, y + 0.05, 0.28, 0.2, col)
        textbox(slide, x + k * 1.3 + 0.33, y - 0.01, 0.95, 0.3, lab, size=10, color=SUB)


def bar_chart(slide, x, y, w, h, cats, series, colors, title, vmin=None, vmax=None, fmt="0", horizontal=False,
              point_colors=None, legend=False, label_size=10):
    """Native clustered bar chart. series: [(name, values)], colors: one per series.

    point_colors recolors individual bars of the first series (highlight "ours").
    """
    cd = CategoryChartData()
    cd.categories = cats
    for name, vals in series:
        cd.add_series(name, vals)
    kind = XL_CHART_TYPE.BAR_CLUSTERED if horizontal else XL_CHART_TYPE.COLUMN_CLUSTERED
    ch = slide.shapes.add_chart(kind, I(x), I(y), I(w), I(h), cd).chart
    ch.has_legend = legend
    if legend:
        ch.legend.position = XL_LEGEND_POSITION.TOP
        ch.legend.include_in_layout = False
        ch.legend.font.size = Pt(10)
    ch.has_title = True
    ch.chart_title.text_frame.text = title
    style_run(ch.chart_title.text_frame.paragraphs[0].runs[0], 12, bold=True, color=NAVY)
    va = ch.value_axis
    if vmin is not None:
        va.minimum_scale = vmin
    if vmax is not None:
        va.maximum_scale = vmax
    va.has_major_gridlines = False
    va.tick_labels.font.size = Pt(9)
    ch.category_axis.tick_labels.font.size = Pt(10)
    plot = ch.plots[0]
    plot.gap_width = 60
    plot.overlap = -10 if len(series) > 1 else 0
    plot.has_data_labels = True
    plot.data_labels.font.size = Pt(label_size)
    plot.data_labels.number_format = fmt
    plot.data_labels.number_format_is_linked = False
    plot.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
    for si, s in enumerate(plot.series):
        s.format.fill.solid()
        s.format.fill.fore_color.rgb = rgb(colors[si])
        if point_colors and si == 0:
            for idx, pt in enumerate(s.points):
                pt.format.fill.solid()
                pt.format.fill.fore_color.rgb = rgb(point_colors[idx])
    return ch


# ------------------------------------------------------------------ deck
class Deck:
    """Presentation + chrome.

    footer:  default footer text (talk title / paper list)
    footers: {color: footer}  per-paper footer, looked up by the slide's tag color
    crumbs:  {color: [step names]}  per-paper breadcrumb steps (new_slide(step=k))
    img_dpi: pictures are downsampled to this many pixels per placed inch
    """

    def __init__(self, out, assets, footer="", footers=None, crumbs=None, img_dpi=220):
        self.out = Path(out)
        self.assets = Path(assets)
        self.footer = footer
        self.footers = footers or {}
        self.crumbs = crumbs or {}
        self.img_dpi = img_dpi
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = I(SLIDE_W), I(SLIDE_H)
        self.blank = self.prs.slide_layouts[6]
        self.page = 0
        self.missing = []
        self._cache = self.assets / ".pptcache"

    # -------------------------------------------------- slides
    def blank_slide(self):
        self.page += 1
        return self.prs.slides.add_slide(self.blank)

    def _crumbs(self, slide, color, idx):
        steps = self.crumbs[color]
        gap = 0.1
        w = min(1.62, (7.4 - (len(steps) - 1) * gap) / len(steps))
        x0 = 12.8 - len(steps) * w - (len(steps) - 1) * gap
        for k, t in enumerate(steps):
            on = k == idx
            box(slide, x0 + k * (w + gap), 0.32, w, 0.36, t, fill=color if on else "FFFFFF", line=color, size=11,
                color="FFFFFF" if on else color, bold=on, radius=0.5, line_w=1)

    def new_slide(self, title, tag=None, tag_color=NAVY, subtitle=None, step=None, footer=None):
        """Content slide: tag pill, breadcrumbs, 28pt title, optional subtitle, accent bar, footer, page no.

        Body area: y in [1.6, 6.95] without subtitle, [1.95, 6.95] with one; x in [0.55, 12.85].
        """
        s = self.blank_slide()
        if tag:
            box(s, 0.55, 0.32, 1.9, 0.36, tag, fill=tag_color, size=12, color="FFFFFF", bold=True, radius=0.5)
        if step is not None and tag_color in self.crumbs:
            self._crumbs(s, tag_color, step)
        textbox(s, 0.55, 0.72, 12.2, 0.7, title, size=28, color=NAVY, bold=True)
        if subtitle:
            textbox(s, 0.57, 1.36, 12.2, 0.4, subtitle, size=15, color=SUB)
        rect(s, 0.55, 1.8 if subtitle else 1.4, 1.0, 0.06, tag_color)
        textbox(s, 0.55, 7.08, 10, 0.3, footer or self.footers.get(tag_color, self.footer), size=10, color=FOOT_GREY)
        textbox(s, 12.0, 7.08, 0.8, 0.3, str(self.page), size=10, color=FOOT_GREY, align=PP_ALIGN.RIGHT)
        return s

    def section_slide(self, num, title, sub, color):
        s = self.blank_slide()
        rect(s, 0, 0, SLIDE_W, SLIDE_H, NAVY)
        rect(s, 0, 3.05, 0.35, 1.5, color)
        textbox(s, 1.0, 2.2, 3, 1.3, num, size=72, color=color, bold=True)
        textbox(s, 1.0, 3.45, 11, 0.9, title, size=40, color="FFFFFF", bold=True)
        textbox(s, 1.0, 4.4, 11, 0.6, sub, size=18, color="C9D3E3")
        return s

    # -------------------------------------------------- pictures
    def asset(self, name):
        p = Path(name)
        if p.suffix:
            return p if p.is_absolute() else self.assets / p
        return self.assets / f"{name}.png"

    def _fit_image(self, path, w_in):
        """Downsample to img_dpi at the placed width; photos without alpha become JPEG."""
        im = Image.open(path)
        target = int(w_in * self.img_dpi)
        big = im.width > target * 1.15
        heavy = path.stat().st_size > 1_500_000 and im.mode in ("RGB", "L")
        if not (big or heavy):
            return path
        self._cache.mkdir(exist_ok=True)
        ext = ".jpg" if im.mode in ("RGB", "L") else ".png"
        out = self._cache / f"{path.stem}_{min(target, im.width)}{ext}"
        if out.exists() and out.stat().st_mtime >= path.stat().st_mtime:
            return out
        if big:
            im = im.resize((target, round(im.height * target / im.width)), Image.LANCZOS)
        if ext == ".jpg":
            im.convert("RGB").save(out, quality=90, optimize=True)
        else:
            im.save(out, optimize=True)
        return out

    def pic(self, slide, name, x, y, w=None, h=None, align="center", border=None):
        """Place an asset fitted inside (w, h) keeping aspect ratio.

        With both w and h the image is centered vertically and aligned horizontally by
        `align` ('center' | 'left' | 'right'). Returns (picture, (x, y, w, h)) of the
        actual placement so captions can be attached under it.
        """
        path = self.asset(name)
        if not path.exists():
            return self._missing(slide, name, x, y, w, h)
        iw, ih = Image.open(path).size
        ar = iw / ih
        if w and h:
            nw, nh = (h * ar, h) if w / h > ar else (w, w / ar)
            ox = {"center": (w - nw) / 2, "left": 0, "right": w - nw}[align]
            x, y, w, h = x + ox, y + (h - nh) / 2, nw, nh
        elif w:
            h = w / ar
        else:
            w = h * ar
        p = slide.shapes.add_picture(str(self._fit_image(path, w)), I(x), I(y), I(w), I(h))
        if border:
            p.line.color.rgb = rgb(border)
            p.line.width = Pt(1)
        return p, (x, y, w, h)

    def _missing(self, slide, name, x, y, w, h):
        """Dashed placeholder so the layout can be reviewed before every asset exists."""
        w, h = w or 3.0, h or (w or 3.0) * 0.6
        s = box(slide, x, y, w, h, f"缺图：{name}", fill="F7F9FC", line="E63946", size=12, color="E63946", dash=True)
        s.name = f"MISSING:{name}"
        self.missing.append((self.page, name))
        return s, (x, y, w, h)

    def save(self):
        for page, name in self.missing:
            print(f"[missing asset] P{page}: {name}")
        self.out.parent.mkdir(parents=True, exist_ok=True)
        self.prs.save(self.out)
        size_mb = self.out.stat().st_size / 1e6
        print(f"saved {self.out}  slides: {len(self.prs.slides)}  size: {size_mb:.1f} MB")
        return self.out
