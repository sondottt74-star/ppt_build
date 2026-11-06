"""Palette, fonts and type sizes shared by every deck.

Colors are hex strings without '#', as python-pptx expects. Use `mpl(c)` to get the
matplotlib form.
"""

FONT, LATIN = "PingFang SC", "Arial"

SLIDE_W, SLIDE_H = 13.333, 7.5

NAVY, TEXT, SUB = "1F3A5F", "222222", "5C677D"
LIGHT, LINE = "F3F6FA", "C9D3E3"
FOOT_GREY = "9AA5B8"

S_TASK = "457B9D"                  # opening / storyline pages
S_EXP, S_EXPL = "7B2CBF", "F1E9F8"  # summary / discussion pages
WARN_BG, WARN = "FDEDEC", "9B2C2C"  # limitations, "don't over-claim" cards

# One main color per paper, in talk order. (main, light background)
PAPER_COLORS = [
    ("3A86FF", "E8F0FE"),  # blue
    ("2A9D8F", "E6F4F1"),  # teal
    ("E76F51", "FDEDE8"),  # coral
    ("E09F3E", "FCF3E3"),  # amber
    ("6D597A", "EFEAF2"),  # plum
]
(C1, C1L), (C2, C2L), (C3, C3L), (C4, C4L), (C5, C5L) = PAPER_COLORS

# table rank fills: append ‹r› / ‹o› / ‹y› / ‹w› to a cell string
RED, ORANGE, YELLOW, WARN_CELL = "F4B6B6", "FAD7A0", "FFF3B0", "F7C6C6"
GREY_BAR = "C9D3E3"                 # baseline bars in charts

# type scale (pt)
SIZE = dict(title=28, subtitle=15, body=15, card=13, table=12, caption=11, footer=10,
            section_num=72, section_title=40, section_sub=18)


def light_of(color):
    for main, light in PAPER_COLORS:
        if main == color:
            return light
    return {S_TASK: "E3ECF7", S_EXP: S_EXPL, NAVY: LIGHT}.get(color, LIGHT)


def mpl(color):
    return color if color.startswith("#") else f"#{color}"
