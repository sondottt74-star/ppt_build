"""pptkit: build paper-reading group-meeting decks with python-pptx + matplotlib.

    from pptkit import *            # Deck, components, layouts, theme colors
    from pptkit.assets import AssetDir
    from pptkit import draw         # matplotlib diagram helpers
"""
from pptx.enum.shapes import MSO_SHAPE  # noqa: F401
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN  # noqa: F401

from .deck import (Deck, I, arrow, bar_chart, box, bullets, caption, circle, fill_para, hline,  # noqa: F401
                   legend_marks, merge_col0, num_card, rect, rgb, style_run, table, textbox)
from .layouts import (bottom_bar, card_row, discussion_slide, figure_slide, flow_row,  # noqa: F401
                      formula_blocks, layout_fig_cards, layout_fig_text, layout_table_chart, layout_two_figs,
                      limitation_grid, num_card_row, numbered_points, outline_slide, title_slide)
from .theme import *  # noqa: F401,F403
