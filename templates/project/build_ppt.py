"""{{TITLE}}: assemble ppt/assets/ into the .pptx.

    python ppt/build_ppt.py && python {{PPT_BUILD}}/tools/check_deck.py "{{DECK}}"

Runs from day one: missing assets become dashed placeholders that check_deck reports as MISSING.
Replace each TODO slide with the page designed in 大纲.md (same order, same titles).
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TALK = ROOT.parent
sys.path.insert(0, os.environ.get("PPT_BUILD", "{{PPT_BUILD}}"))

from pptkit import *  # noqa: E402,F401,F403

A = ROOT / "assets"
OUT = TALK / "{{DECK}}"

# (key, short name, full title · venue, main color)
PAPERS = [
{{PAPERS}}
]
STEPS = ["1 改了什么", "2 为什么", "3 方法", "4 训练", "5 实验", "6 局限"]
FOOT_ALL = "{{TITLE}} · " + " / ".join(p[1] for p in PAPERS)

deck = Deck(OUT, A, footer=FOOT_ALL,
            footers={p[3]: p[2] for p in PAPERS},
            crumbs={p[3]: STEPS for p in PAPERS})
new_slide, section_slide, pic = deck.new_slide, deck.section_slide, deck.pic

# ================================================================== 开场
title_slide(deck, "组会论文汇报", ["{{TITLE}}", "TODO 副标题：一句话主线"],
            "  ·  ".join(p[1] for p in PAPERS), hero="TODO_hero",
            hero_caption="论文原图（TODO）：……")

outline_slide(deck, [("00", "背景", "TODO：任务和共同框架", S_TASK)] +
              [(f"{k + 1:02d}", p[1], "TODO：这一篇往前推了哪一步", p[3]) for k, p in enumerate(PAPERS)],
              closing="总结：对照 + 讨论问题")

s = new_slide("TODO 任务：输入什么，输出什么", "00 背景", S_TASK, "TODO 一句话", footer=FOOT_ALL)
flow_row(s, ["输入", "预处理", "表示 / 优化", "渲染 / 推理", "输出"], S_TASK, y=2.4, h=1.2, size=14)

s = new_slide("TODO 主线：几篇论文在同一个框架里各推进一步", "00 主线", S_TASK, footer=FOOT_ALL)
pic(s, "d_storyline", 0.6, 1.65, 12.1, 3.0)
card_row(s, [[f"**{p[1]}**", "TODO 结构", "TODO 解决什么"] for p in PAPERS], S_TASK, 5.3, 1.45,
         fill="FFFFFF")

# ================================================================== 每篇论文一节
for k, (key, name, full, color) in enumerate(PAPERS):
    section_slide(f"{k + 1:02d}", name, "TODO：一句话说清这一篇做了什么", color)
    tag = f"{k + 1:02d} {name}"

    s = new_slide(f"相比 TODO 前作，{name} 改了 N 点", tag, color, "TODO 副标题", step=0)
    layout_fig_cards(deck, s, f"{key}_teaser", f"论文原图（{name}）：TODO", [
        ["**① TODO**", "TODO 说明"], ["**② TODO**", "TODO 说明"]], color, subtitle=True,
        bar="TODO：哪些没变，变的是什么")

    s = new_slide("为什么要这样做", tag, color, step=1)
    layout_fig_text(deck, s, f"d_{key}_why", "示意：TODO", color,
                    points=[("TODO 原因一", ["TODO", "TODO"]), ("TODO 原因二", ["TODO", "TODO"])],
                    conclusion="TODO 一句话结论")

    s = new_slide("整体流程：TODO", tag, color, step=2)
    pic(s, f"{key}_pipeline", 0.6, 1.6, 12.1, 3.1)
    caption(s, 0.6, 4.7, 12.1, f"论文原图（{name}）：TODO")
    flow_row(s, ["TODO", "TODO", "TODO", "TODO", "TODO"], color)

    s = new_slide("方法细节：TODO（公式 + 直观解释）", tag, color, step=2)
    formula_blocks(deck, s, [("① TODO", f"f_{key}_1", "TODO 直观解释"),
                             ("② TODO", f"f_{key}_2", "TODO 直观解释")], color)
    pic(s, f"d_{key}_method", 7.1, 1.7, 5.7, 3.6)

    s = new_slide("训练：TODO", tag, color, step=3)
    layout_fig_text(deck, s, f"{key}_train", f"论文原图（{name}）：TODO", color,
                    bullets_=["**TODO**：TODO", "**TODO**：TODO"])

    s = new_slide("实验：TODO 一句话结论", tag, color, "TODO 数据集 / 设置", step=4)
    layout_table_chart(s, [["数据集", "方法", "PSNR↑", "FPS", "存储"],
                           ["TODO", "基线", "0", "0", "0"], ["", name, "0‹r›", "0‹r›", "0‹r›"]], color,
                       hl_row=[2], merges=[(1, 2)],
                       chart=dict(cats=["TODO"], series=[("基线", (1,)), (name, (2,))],
                                  colors=[GREY_BAR, color], title="TODO", legend=True),
                       cards=[("TODO", "TODO", False), ("TODO", "TODO", False), ("注意", "TODO 不要夸大的地方", True)])

    s = new_slide("实验：TODO 消融 / 定性", tag, color, step=4)
    layout_two_figs(deck, s, (f"{key}_qual", f"论文原图（{name}）：TODO"),
                    (f"{key}_ablation", f"论文原图（{name}）：TODO"), color, bar="TODO：对应前面哪个设计")

    s = new_slide("局限：TODO", tag, color, step=5)
    limitation_grid(s, [("TODO", "TODO"), ("TODO", "TODO"), ("TODO", "TODO")])
    nxt = PAPERS[k + 1] if k + 1 < len(PAPERS) else None
    bottom_bar(s, f"→ {nxt[1]}：TODO 下一篇解决什么" if nxt else "→ 总结", nxt[3] if nxt else S_EXP)

# ================================================================== 总结
s = new_slide("放在一起：TODO", "总结", S_EXP, footer=FOOT_ALL)
table(s, 0.6, 1.8, 12.1, [["方法", "结构", "解决什么", "代价"]] +
      [[p[1], "TODO", "TODO", "TODO"] for p in PAPERS], size=14, row_h=0.6,
      first_col_colors=[p[3] for p in PAPERS])
bottom_bar(s, "TODO 一句话总结", S_EXP, solid=False, y=6.3)

discussion_slide(deck, [("Q1", "TODO 讨论问题", "TODO 提示方向"), ("Q2", "TODO 讨论问题", "TODO 提示方向")], S_EXP)

deck.save()
