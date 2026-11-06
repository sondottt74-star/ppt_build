#!/usr/bin/env python3
"""Check a 逐字稿 against the deck text: is it a talk, or the slides read aloud?

    python tools/check_script.py <talk>/逐字稿.md <talk>/check/slides.md

slides.md comes from check_deck.py. Per page (### P{n} in the script, ## P{n} in slides.md):
  COPY     > --max-copy of the spoken characters are verbatim runs (>= 6 chars) of slide text
  THIN     content page with fewer than --min-chars spoken characters
  POINTING more than 2 【指…】 cues: the page is narrated element by element
  NOINSIGHT content page without a single "understanding" sentence (why / analogy / cost / comparison)
  BRIDGE   page does not open with a link to what came before (承上) — info, see SKILL.md step 7
  MISSING  page exists in the deck but not in the script (or the other way round)
Per paper section:
  INSIGHT  no sentence that adds understanding (why / intuition / comparison / cost / caveat)
  TIME     section length differs from its '（约 N 分钟）' heading by > 25%; whole talk vs --minutes by > 10%
Exit code 1 if COPY, POINTING, NOINSIGHT, MISSING, INSIGHT or TIME issues are found.
"""
import argparse
import re
import sys
from pathlib import Path

CJK = re.compile(r"[\u4e00-\u9fff]")
PUNCT = re.compile(r"[\s，。、；：！？“”‘’（）《》【】\[\]()…—\-·,.;:!?\"'/|*`>#]+")
BRIDGE = ("刚才", "上一页", "前面", "前一篇", "上一篇", "那么", "那", "所以", "于是", "接下来", "接着", "问题是", "可是",
          "但是", "不过", "换句话说", "回到", "有了", "既然", "这就", "这样", "这里", "说完", "讲完", "看完", "带着",
          "最后", "第一", "大家好", "为什么", "怎么", "如果", "光", "只")
INSIGHT = ("为什么", "换句话说", "直觉", "本质", "说白了", "关键在于", "好处是", "代价", "我的理解", "我理解", "类比", "相当于",
           "可以把", "想象", "反过来", "对比", "相比", "区别在于", "意味着", "也就是说", "之所以", "注意", "值得", "其实",
           "问题在于", "局限", "前提是", "如果", "要是", "比如", "理解", "我觉得", "说明", "原因", "因为", "换来", "取舍",
           "问号", "意外", "巧妙", "揭示", "诚实", "为了", "不是", "而是", "误解")


def norm(t):
    t = re.sub(r"【[^】]*】", "", t)
    return PUNCT.sub("", t)


def sections(md, level):
    out, cur, buf = {}, None, []
    pat = re.compile(r"^" + "#" * level + r"\s+P(\d+)\b(.*)$")
    for line in md.splitlines():
        m = pat.match(line)
        if m:
            if cur is not None:
                out[cur] = "\n".join(buf)
            cur, buf = int(m.group(1)), [m.group(2)]
        elif re.match(r"^#{1,%d}\s" % level, line):
            if cur is not None:
                out[cur] = "\n".join(buf)
            cur, buf = None, []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        out[cur] = "\n".join(buf)
    return out


def copy_ratio(spoken, slide, k=6):
    s, t = norm(spoken), norm(slide)
    if not s:
        return 0.0
    grams = {t[i:i + k] for i in range(len(t) - k + 1)}
    covered = [False] * len(s)
    for i in range(len(s) - k + 1):
        g = s[i:i + k]
        # method names, numbers and symbols repeat by necessity; only Chinese phrasing counts as copying
        if g in grams and len(CJK.findall(g)) >= 3:
            for j in range(i, i + k):
                covered[j] = True
    return sum(covered) / len(s)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script", type=Path)
    ap.add_argument("slides", type=Path)
    ap.add_argument("--max-copy", type=float, default=0.30)
    ap.add_argument("--min-chars", type=int, default=90)
    ap.add_argument("--minutes", type=float, help="target length of the main part (excl. backup pages)")
    ap.add_argument("--cpm", type=int, default=260, help="spoken characters per minute")
    args = ap.parse_args()

    script_md = args.script.read_text()
    spoken = sections(script_md, 3)
    slides = sections(args.slides.read_text(), 2)
    blocking, total_c, total_n = 0, 0.0, 0
    prev_tail = ""
    print(f"== {args.script.name}: {len(spoken)} script pages, {len(slides)} deck pages")
    for n in sorted(set(slides) | set(spoken)):
        if n not in spoken:
            print(f"  P{n:<3} MISSING  逐字稿缺这一页")
            blocking += 1
            continue
        if n not in slides:
            print(f"  P{n:<3} MISSING  deck 里没有这一页")
            blocking += 1
            continue
        body = spoken[n].split("\n", 1)[1] if "\n" in spoken[n] else ""
        chars = len(norm(body))
        slide_text = slides[n]
        is_section = len(norm(slide_text)) < 60 or "备用" in slide_text[:60]
        r = copy_ratio(body, slide_text)
        total_c += r * chars
        total_n += chars
        if r > args.max_copy and chars > 40:
            print(f"  P{n:<3} COPY     {r:.0%} 是页面原文（{chars} 字）")
            blocking += 1
        if not is_section and chars < args.min_chars and n > 2:
            print(f"  P{n:<3} THIN     只有 {chars} 字")
        points = body.count("【指")
        if points > 2:
            print(f"  P{n:<3} POINTING {points} 次【指…】：在逐个念页面元素，只留 1–2 次，其余换成解释")
            blocking += 1
        spoken_only = re.sub(r"【[^】]*】", "", body)
        if not is_section and n > 2 and chars >= 40 and not any(w in spoken_only for w in INSIGHT):
            print(f"  P{n:<3} NOINSIGHT 没有一句理解（为什么 / 相当于 / 代价 / 对比 / 前提……）")
            blocking += 1
        first = norm(body)[:30]
        asked = "？" in prev_tail  # previous page ended on the question this page answers
        if n > 1 and not asked and not any(first.startswith(b) or b in first[:12] for b in BRIDGE + ("答案",)):
            print(f"  P{n:<3} BRIDGE   开头没有承上：「{norm(body)[:20]}…」")
        prev_tail = re.sub(r"【[^】]*】", "", body).strip()[-60:]

    # per-section insight check, sections are '## ' headings in the script
    for title, text in re.findall(r"^##\s+([^\n]+)\n(.*?)(?=^##\s|\Z)", script_md, re.S | re.M):
        if "P" not in text:
            continue
        hits = sum(text.count(w) for w in INSIGHT)
        if hits < 3:
            print(f"  ---- INSIGHT  「{title.strip()}」只有 {hits} 处理解性表达（为什么/相当于/代价/对比…）")
            blocking += 1
    # timing: per '## ... （约 N 分钟）' section and overall
    spoken_total = 0
    for title, text in re.findall(r"^##\s+([^\n]+)\n(.*?)(?=^##\s|\Z)", script_md, re.S | re.M):
        if "备用" in title:
            continue
        chars = len(norm(re.sub(r"^###.*$", "", text, flags=re.M)))
        spoken_total += chars
        m = re.search(r"约\s*([\d.]+)(?:[–-]([\d.]+))?\s*分钟", title)
        if m:
            lo = float(m.group(1))
            hi = float(m.group(2) or lo)
            mins = chars / args.cpm
            if mins > hi * 1.25 or mins < lo * 0.75:
                print(f"  ---- TIME     「{title.strip()}」约 {mins:.1f} 分钟（{chars} 字），计划 {m.group(0)[1:]}")
                blocking += 1
    est = spoken_total / args.cpm
    if args.minutes:
        flag = abs(est - args.minutes) > 0.1 * args.minutes
        print(f"== {'TIME     ' if flag else ''}正文约 {spoken_total} 字 ≈ {est:.1f} 分钟（目标 {args.minutes:g} 分钟，{args.cpm} 字/分钟）")
        blocking += flag
    else:
        print(f"== 正文约 {spoken_total} 字 ≈ {est:.1f} 分钟（{args.cpm} 字/分钟；用 --minutes 检查时长）")
    overall = total_c / total_n if total_n else 0
    print(f"== 全文照念比例 {overall:.0%}（目标 ≤ 15%），口播约 {total_n:.0f} 字")
    print(f"== {blocking} blocking issue(s)" if blocking else "== no blocking issues")
    sys.exit(1 if blocking else 0)


if __name__ == "__main__":
    main()
