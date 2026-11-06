#!/usr/bin/env python3
"""Generate the 讲稿规划 (script plan) table from the built deck, with a character budget per page.

    python tools/script_plan.py <talk>/check/slides.md --minutes 25 --out <talk>/讲稿规划.md

Fill the table BEFORE writing 逐字稿.md. Each content page gets one row:
    承上   the question / contrast / consequence from the previous page this page picks up
    核心点 the one thing the listener should remember (not on the slide verbatim)
    理解   which move adds understanding: 为什么 / 类比 / 对比前作 / 代价·前提 / 我的判断 — and its content
    启下   the question this page leaves for the next one (= next row's 承上)
    预算   spoken characters for this page (from --minutes at --cpm characters per minute)
Section pages get a short budget, backup pages none.
"""
import argparse
import re
from pathlib import Path


def pages(md):
    out = []
    for block in re.split(r"^## ", md, flags=re.M)[1:]:
        head, *lines = block.splitlines()
        m = re.match(r"P(\d+)\s*(.*)", head)
        if not m:
            continue
        text = " ".join(l[2:] for l in lines if l.startswith("- "))
        out.append((int(m.group(1)), m.group(2).strip(), text))
    return out


def kind(title, text):
    if "备用" in text[:60] or title.startswith("备用"):
        return "backup"
    if len(re.sub(r"\s", "", text)) < 80:
        return "section"
    return "content"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slides", type=Path)
    ap.add_argument("--minutes", type=float, required=True, help="target talk length (main part, no backup)")
    ap.add_argument("--cpm", type=int, default=260, help="spoken Chinese characters per minute")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    ps = [(n, t, x, kind(t, x)) for n, t, x in pages(args.slides.read_text())]
    total = args.minutes * args.cpm
    n_sec = sum(k == "section" for *_, k in ps)
    n_con = sum(k == "content" for *_, k in ps)
    sec_budget = 60
    con_budget = max(80, round((total - n_sec * sec_budget) / max(n_con, 1), -1))

    L = [f"# 讲稿规划（{args.minutes:g} 分钟 × {args.cpm} 字/分钟 ≈ {total:.0f} 字；内容页每页约 {con_budget:.0f} 字）", "",
         "先填这张表再写逐字稿。“启下”必须等于下一行的“承上”，整张表的承上/启下连起来就是全场的问题链。",
         "“理解”一栏写具体内容，不写类别名，例如“为什么不取最大值：单个噪点会带偏；取平均会淹没小划痕”。", "",
         "| 页 | 标题 | 承上 | 核心点（听众记住什么） | 理解（为什么/类比/对比/代价/判断） | 启下 | 预算 |",
         "|---|---|---|---|---|---|---|"]
    for n, t, _, k in ps:
        if k == "backup":
            L.append(f"| P{n} | {t} | — | 被问到时说什么 | — | — | 备用 |")
        elif k == "section":
            L.append(f"| P{n} | {t} | 接上一篇的局限 | 一句话定位 | 带着什么问题看这篇 | — | {sec_budget} |")
        else:
            L.append(f"| P{n} | {t} |  |  |  |  | {con_budget:.0f} |")
    L += ["", "## 每篇的评价（写在该篇局限页）", "", "| 论文 | 一句优点 | 一句代价 | 引出下一篇的问题 | 可能被问（1–2 条） |",
          "|---|---|---|---|---|", "|  |  |  |  |  |", ""]
    text = "\n".join(L) + "\n"
    if args.out:
        if args.out.exists():
            raise SystemExit(f"{args.out} exists; delete it to regenerate")
        args.out.write_text(text)
        print(f"wrote {args.out}: {len(ps)} pages, {n_con} content pages × {con_budget:.0f} 字")
    else:
        print(text)


if __name__ == "__main__":
    main()
