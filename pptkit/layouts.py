"""Page recipes that recur in every paper talk.

Each function builds a whole slide (taking the Deck) or a whole row of elements
(taking the slide). Positions follow the layout grid in skill/paper-ppt/design.md.
"""
from __future__ import annotations

from pptx.enum.text import PP_ALIGN

from .deck import arrow, box, caption, circle, num_card, rect, textbox
from .theme import LIGHT, NAVY, SLIDE_W, SUB, TEXT, WARN, WARN_BG, light_of


# ------------------------------------------------------------------ whole slides
def title_slide(deck, kicker, title_lines, subtitle, hero=None, hero_caption=None):
    """NAVY band on top with kicker / two-line title / paper list; hero figure below."""
    s = deck.blank_slide()
    rect(s, 0, 0, SLIDE_W, 3.35, NAVY)
    textbox(s, 0.7, 0.45, 12, 0.5, kicker, size=18, color="9EC5FE", bold=True)
    textbox(s, 0.7, 0.95, 12, 1.4, title_lines, size=36, color="FFFFFF", bold=True, spacing=1.0)
    textbox(s, 0.7, 2.55, 12, 0.5, subtitle, size=16, color="C9D3E3")
    if hero:
        deck.pic(s, hero, 0.7, 3.6, 11.9, 3.1)
    if hero_caption:
        caption(s, 0.7, 6.72, 11.9, hero_caption, 12)
    return s


def outline_slide(deck, items, closing=None, title="汇报提纲"):
    """items: [(num, title, one-line description, color)]; closing: optional summary pill text."""
    s = deck.new_slide(title)
    step = 1.1 if len(items) <= 4 else 0.9
    for k, (num, t, d, col) in enumerate(items):
        y = 1.75 + k * step
        h = step - 0.2
        box(s, 0.9, y, 1.1, h, num, fill=col, size=30 if h > 0.8 else 24, color="FFFFFF", bold=True)
        box(s, 2.15, y, 10.2, h, "", fill=LIGHT)
        textbox(s, 2.4, y + 0.06, 9.8, 0.45, t, size=22 if h > 0.8 else 19, color=NAVY, bold=True)
        textbox(s, 2.4, y + h * 0.55, 9.8, 0.4, d, size=14, color=SUB)
    if closing:
        y = 1.75 + len(items) * step + 0.05
        box(s, 2.15, y, 10.2, 0.55, closing, fill="F1E9F8", size=15, color="7B2CBF", bold=True)
    return s


def discussion_slide(deck, questions, color, title="讨论", thanks="谢谢"):
    """questions: [(label, question, hint)], at most 3."""
    s = deck.new_slide(title, title, color)
    for k, (q, t, d) in enumerate(questions):
        y = 2.0 + k * 1.9
        box(s, 0.9, y, 1.1, 1.4, q, fill=color, size=30, color="FFFFFF", bold=True)
        box(s, 2.15, y, 10.2, 1.4, "", fill=LIGHT)
        textbox(s, 2.4, y + 0.18, 9.8, 0.5, t, size=22, color=NAVY, bold=True)
        textbox(s, 2.4, y + 0.78, 9.8, 0.45, d, size=14, color=SUB)
    if thanks:
        textbox(s, 0.6, 2.0 + len(questions) * 1.9 + 0.1, 12.1, 0.6, thanks, size=24, color=NAVY, bold=True,
                align=PP_ALIGN.CENTER)
    return s


def figure_slide(deck, title, name, cap, color, tag="备用"):
    """One full-width paper figure (backup pages, qualitative results)."""
    s = deck.new_slide(title, tag, color)
    deck.pic(s, name, 0.6, 1.65, 12.1, 5.0)
    caption(s, 0.6, 6.68, 12.1, cap)
    return s


# ------------------------------------------------------------------ layouts A / B / E / F (see design.md)
def _body_top(subtitle):
    return 1.95 if subtitle else 1.6


def layout_fig_text(deck, s, fig, cap, color, points=None, bullets_=None, conclusion=None, subtitle=False,
                    fig_w=6.6):
    """A: figure left, reasons or bullets right, optional solid conclusion box bottom-right."""
    from .deck import bullets
    top = _body_top(subtitle)
    fig_h = 6.25 - top
    deck.pic(s, fig, 0.6, top + 0.05, fig_w, fig_h)
    caption(s, 0.6, top + fig_h + 0.08, fig_w, cap)
    rx, rw = 0.6 + fig_w + 0.3, 12.85 - (0.6 + fig_w + 0.3)
    if points:
        numbered_points(s, points, color, x=rx, y=top + 0.15, w=rw, step=1.85)
    elif bullets_:
        bullets(s, rx, top + 0.15, rw, 3.6, bullets_, size=15, accent=color, gap=10)
    if conclusion:
        box(s, rx, 5.55, rw, 1.1, conclusion, fill=color, size=16, color="FFFFFF", bold=True)


def layout_fig_cards(deck, s, fig, cap, cards, color, subtitle=False, fig_h=2.75, card_h=1.35, bar=None):
    """B: full-width figure on top, a row of 2-4 cards below, optional bottom bar."""
    top = _body_top(subtitle)
    deck.pic(s, fig, 0.6, top, 12.1, fig_h)
    caption(s, 0.6, top + fig_h, 12.1, cap)
    y = top + fig_h + 0.4
    if bar:
        card_h = min(card_h, 6.25 - y)
    card_row(s, cards, color, y, card_h)
    if bar:
        bottom_bar(s, bar, color, solid=False, y=6.4, size=14)


def layout_two_figs(deck, s, left, right, color, bar=None, subtitle=False, fig_h=None):
    """F: two figures side by side, each (asset, caption); optional takeaway bar."""
    top = _body_top(subtitle)
    fig_h = fig_h or (6.0 - top if bar else 6.45 - top)
    for k, (fig, cap) in enumerate((left, right)):
        x = 0.55 + k * 6.25
        deck.pic(s, fig, x, top + 0.05, 6.0, fig_h)
        caption(s, x, top + fig_h + 0.07, 6.0, cap)
    if bar:
        bottom_bar(s, bar, color, solid=False, y=6.45, h=0.5, x=0.55, w=12.25, size=15)


def layout_table_chart(s, data, color, chart=None, cards=None, col_w=None, hl_row=None, merges=None,
                       subtitle=True, row_h=0.42, size=12):
    """E: results table left (x 0.55, w 7.3), native bar chart right, key-number cards below.

    chart: dict of bar_chart kwargs (cats, series, colors, title, ...), placed at (8.05, top, 4.8, 3.2).
    cards: [(big, small, is_warning)].
    """
    from .deck import bar_chart, merge_col0, table
    top = _body_top(subtitle)
    t = table(s, 0.55, top + 0.05, 7.3, data, col_w=col_w, size=size, row_h=row_h, hl_row=hl_row,
              hl_fill=light_of(color))
    if merges:
        merge_col0(t, merges)
    if chart:
        bar_chart(s, 8.05, top, 4.8, 3.2, **chart)
    if cards:
        num_card_row(s, cards, color)
    return t


# ------------------------------------------------------------------ rows / blocks
def flow_row(slide, steps, color, y=5.15, x0=0.55, total_w=12.25, h=1.05, gap=0.25, size=12, last_solid=True):
    """Horizontal pipeline of boxes joined by arrows. A step may contain '\\n'."""
    n = len(steps)
    w = (total_w - (n - 1) * gap) / n
    light = light_of(color)
    for k, t in enumerate(steps):
        x = x0 + k * (w + gap)
        solid = last_solid and k == n - 1
        box(slide, x, y, w, h, t.split("\n"), fill=color if solid else light, line=color, size=size,
            color="FFFFFF" if solid else TEXT, bold=solid)
        if k < n - 1:
            arrow(slide, x + w + 0.02, y + h / 2, x + w + gap - 0.02, y + h / 2, color=color)


def card_row(slide, cards, color, y, h, x0=0.6, total_w=12.1, gap=0.22, size=13, fill=None, line=True):
    """Equal-width cards; each card is a list of lines ('**x**' = accent)."""
    n = len(cards)
    w = (total_w - (n - 1) * gap) / n
    for k, lines in enumerate(cards):
        box(slide, x0 + k * (w + gap), y, w, h, lines, fill=fill or light_of(color), line=color if line else None,
            size=size, accent=color)
    return w


def num_card_row(slide, items, color, y=5.45, h=1.35, x0=0.55, total_w=12.3, gap=0.15):
    """items: [(big, small, is_warning)] -> key-number cards under an experiment table."""
    n = len(items)
    w = (total_w - (n - 1) * gap) / n
    for k, (big, small, warn) in enumerate(items):
        num_card(slide, x0 + k * (w + gap), y, w, h, big, small, fill=WARN_BG if warn else light_of(color),
                 accent=WARN if warn else color)


def numbered_points(slide, points, color, x=7.5, y=1.75, w=5.3, step=1.85, title_size=17, size=13):
    """Numbered reasons: circle + bold title + short bullet lines."""
    from .deck import bullets
    for k, (t, lines) in enumerate(points):
        yy = y + k * step
        circle(slide, x, yy, 0.45, str(k + 1), color)
        textbox(slide, x + 0.6, yy - 0.02, w - 0.6, 0.45, t, size=title_size, color=NAVY, bold=True)
        bullets(slide, x + 0.6, yy + 0.5, w - 0.55, step - 0.55, lines, size=size, accent=color, gap=3)


def formula_blocks(deck, slide, blocks, color, x=0.6, y=1.7, w=6.2, step=1.75):
    """blocks: [(heading, formula_asset, one-line meaning)] stacked vertically."""
    for k, (t, f, d) in enumerate(blocks):
        yy = y + k * step
        textbox(slide, x, yy, w, 0.4, t, size=15, color=color, bold=True)
        deck.pic(slide, f, x + 0.15, yy + 0.45, w=w - 0.3, h=0.62, align="left")
        textbox(slide, x + 0.15, yy + 1.12, w - 0.2, 0.4, d, size=13, color=SUB)


def limitation_grid(slide, lims, x0=0.6, y0=1.75, w=6.0, h=2.1, gx=6.15, gy=2.3):
    """2x2 warning cards: [(title, description)]."""
    for k, (t, d) in enumerate(lims):
        x, y = x0 + (k % 2) * gx, y0 + (k // 2) * gy
        box(slide, x, y, w, h, "", fill=WARN_BG)
        circle(slide, x + 0.2, y + 0.2, 0.45, str(k + 1), WARN)
        textbox(slide, x + 0.8, y + 0.18, w - 0.95, 0.45, t, size=16, color=WARN, bold=True)
        textbox(slide, x + 0.8, y + 0.7, w - 0.95, h - 0.8, d, size=13)


def bottom_bar(slide, text, color, solid=True, y=6.4, h=0.5, x=0.6, w=12.15, size=15):
    """One-sentence takeaway / transition to the next paper at the bottom of a slide."""
    return box(slide, x, y, w, h, text, fill=color if solid else light_of(color), size=size,
               color="FFFFFF" if solid else color, bold=True)
