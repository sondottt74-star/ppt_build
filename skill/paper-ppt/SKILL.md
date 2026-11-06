---
name: paper-ppt
description: >-
  Turns several research papers given as LaTeX source (arXiv tarballs, extracted source folders,
  or arXiv ids) into a polished Chinese group-meeting deck (.pptx) plus a verbatim speaking script
  (逐字稿), using the ppt_build repo (pptkit + tools): original paper figures embedded from the tex
  source, mathtext formulas, matplotlib diagrams, native tables/charts, rendered QA loop. Use when the
  user asks for 组会汇报 / 论文汇报 PPT / 论文精读 PPT / 逐字稿 / 讲稿, or gives 2-5 papers and wants
  slides and a talk.
---

# 论文 → 组会 PPT + 逐字稿

输入：几篇论文的 **LaTeX 源码**（arXiv `.tar.gz`、解压后的源码目录、或 arXiv id），可选主题、时长、听众。
输出：`<talk>/<标题>.pptx`、`<talk>/大纲.md`、`<talk>/逐字稿.md`，以及渲染检查图 `<talk>/check/`。

代码全在仓库 `ppt_build`（下称 `$PB`，默认 `~/research/ppt_build`）。不要在对话里临时手写一套 pptx 辅助函数，一律用 `pptkit`。

## 0. 准备

```bash
PB=~/research/ppt_build
[ -d $PB ] || git clone https://github.com/sondottt74-star/ppt_build.git $PB
git -C $PB pull --ff-only
python3 -c "import pptx, fitz, matplotlib, PIL, lxml" || python3 -m pip install --user -r $PB/requirements.txt
which soffice || echo "需要 LibreOffice 做渲染检查：brew install --cask libreoffice"
```

写工作区以外的路径、下载 arXiv 源码、调用 LibreOffice 时需要沙箱外权限（Cursor：Shell 加 `required_permissions: ["all"]`；Codex：按提示申请提权）。

## 1. 建工程（一条命令）

key 用 2–3 个字母，按讲的顺序排，它也是素材前缀（`sc_`、`oc_`、`px_`）：

```bash
python3 $PB/tools/new_talk.py <talk_dir> --title "<汇报标题>" \
    sc=<论文1源码.tar.gz 或目录 或 arXiv id> oc=<论文2> px=<论文3>
```

`<talk_dir>` 默认放在用户论文所在目录旁边或当前工作区。命令会生成：

- `papers/<key>/index.md`：标题、摘要、章节、**全部图（F#：源文件路径 + caption + label）**、**全部表（T#，已转成 markdown，最好/次好用 `**x**` / `__x__` / `‹颜色名›` 标出）**、**全部编号公式（E#，宏已展开）**
- `papers/<key>/flat.tex`：主文件展开 `\input` 后的全文，读方法和实验细节用它
- `papers/<key>/figures_sheet_*.png`：每张图的缩略图和 F# 编号，**用 Read 看图来挑图**
- `ppt/make_assets.py`（FIGS 里已列出全部候选图，注释状态）、`ppt/build_ppt.py`（可直接运行的骨架）、`大纲.md`、`逐字稿.md` 模板

## 2. 工作流程

复制这份清单并逐项勾选：

```
- [ ] 1 读论文：index.md + flat.tex + figures_sheet，每篇写 notes/<key>.md
- [ ] 2 定主线：主题、顺序、贯穿例子、每篇“改了什么”→ 与用户确认
- [ ] 3 写 大纲.md：每页“讲什么 / 怎么做”
- [ ] 4 make_assets.py：论文原图、公式、示意图，逐张看图验证
- [ ] 5 build_ppt.py：按大纲逐页实现
- [ ] 6 检查循环：check_deck 无阻塞问题 + 看渲染图逐页过
- [ ] 7 写 逐字稿.md：按实际页码和页面文字
- [ ] 8 交付与归档
```

### 第 1 步：读论文

每篇写 `notes/<key>.md`（≤ 1 页）：解决什么问题；相比前作改了哪几点（先说结论）；为什么（动机）；方法流程和关键公式（引用 E#）；训练技巧；主结果和消融（引用 T#，抄准数字和数据集）；局限；能直接用的图（F#，说明用在哪页）。数字只能来自 T# 或正文，不要凭记忆。

### 第 2 步：定主线（最重要）

按 [narrative.md](narrative.md) 的规则定：

1. **一个主题**，全场只服务它（例：主题是“结构化高斯”，而不是“怎么只用必要的 Gaussian 把场景画好”）。
2. **递进顺序**：前一篇的局限 = 下一篇的动机。
3. **一个贯穿例子**（例：同一栋建筑——换角度看 / 从远走近 / 被前楼挡住），开场、每篇动机、总结都用它。
4. 每篇一句话“这一篇让 X 往前走了哪一步”。

用户没给主题时，给 2–3 个候选主线（有 AskQuestion 工具就用它，否则直接在对话里列出）（每个一句话 + 论文顺序）让用户选。用户说“直接做 / 快一点”时，自己定主线，在交付时说明。

### 第 3 步：大纲

照 [outline-template.md](outline-template.md) 写 `大纲.md`。每页必须有“讲什么”（要点，口语化）和“怎么做”（版式代号、`pptkit` 函数、素材名、关键坐标）。版式、配色、组件见 [design.md](design.md)。页数参考：每篇 9–11 页（含章节页），开场 4–5 页，总结 + 讨论 2 页，备用页放最后。用户要求先看大纲时停在这里等反馈；之后用户改大纲只改他指定的部分。

### 第 4 步：素材（`ppt/make_assets.py`）

- **论文原图直接嵌入**：在 `FIGS` 里取消注释要用的行，`A.fig(name, path)` 自动处理 pdf / png / jpg / eps。只要多联图里的一格：`python3 $PB/tools/fig_grid.py <图>` 画坐标网格，Read 网格图读出 `clip=(x0, y0, x1, y1)`（PDF 用 pt，位图用像素），写进 `CROPS`，渲染后再 Read 一次确认裁对了。
- **公式**：从 index.md 的 E# 抄 tex，改成 mathtext 能渲染的形式放进 `FORMULAS`（不支持 `\text`、`\operatorname`、`aligned`、中文；`sanitize_tex` 会自动替换常见写法），中文解释写在幻灯片文本框里。一页最多 2–3 个公式。
- **示意图**：论文里没有合适的图才自绘（概念对比、贯穿例子、判断流程）。用 `pptkit.draw` 的 `draw_blob / building_iso / camera_iso / round_box / arrow`；同一概念全场同一颜色（见 design.md）。
- 运行 `python3 ppt/make_assets.py`，然后 **Read 每张新生成的 d_ / f_ 图** 检查中文、遮挡、比例。

### 第 5 步：组装（`ppt/build_ppt.py`）

骨架已能运行，缺的图显示为红色虚线“缺图”占位。按大纲逐页替换 TODO：先用 `layout_*` / `*_row` 现成函数，不够再用 `box / textbox / bullets / pic / table / bar_chart / arrow` 自由排。完整示例：`$PB/examples/structured-gs/ppt/build_ppt.py`（39 页，三篇结构化高斯）。

### 第 6 步：检查循环（必须做，不能跳过）

```bash
python3 ppt/build_ppt.py && python3 $PB/tools/check_deck.py "<标题>.pptx"
```

1. 修完所有 `OUT / OVERFLOW / OVERLAP / MISSING`（`STACK` 是有意叠放可忽略，`DENSE` 要删字或拆页，`SMALL` 改到 ≥ 10 pt）。
2. Read 每张 `check/sheet_*.png`（每张 12 页）通看；可疑页用 `--dpi 150 --pages N` 放大后 Read `check/pages/pNN.png`。
3. 逐页对照 [design.md](design.md) 的“检查清单”：图文是否一致（文字说的 LOD 1 图里就得是 LOD 1）、图注是否压住下一元素、卡片字是否超过两行、配色是否属于当前论文。
4. 改完重新 build + check，直到无阻塞问题且看图无问题。

### 第 7 步：逐字稿

先运行一次 check_deck，它会生成 `check/slides.md`（每页实际页码、标题、全部文字）。照 [script-template.md](script-template.md) 写 `逐字稿.md`：**标题用 deck 实际页码 `P{n}` 和页面标题**，章节页也写一两句过渡；内容严格按大纲“讲什么”，只讲页面上有的东西；用【指…】标出指向的元素，元素名用页面上的原词；每个公式用一句大白话解释；每篇结尾一句过渡到下一篇。语速按 250–280 字/分钟，头部写总字数和预计时长，与用户要求的时长核对。

### 第 8 步：交付

- 回复用户：pptx / 逐字稿 / 大纲路径，页数，预计时长，主线一句话，需要用户自己确认的地方（例如自己定了主线、某张图找不到原图改为自绘），并嵌入 1–2 张 `check/sheet_*.png`。
- 若 `~/research/组会汇报ppt/` 存在，复制一份为 `YYYY-MM-DD<标题>.pptx` 和 `YYYY-MM-DD<标题>-逐字稿.md`。
- 后续用户提修改：改 `大纲.md` 对应页 → 改 `build_ppt.py` → 重跑检查 → 同步改 `逐字稿.md` 同一页。

## 参考

- [narrative.md](narrative.md)：内容与讲法规则（主线、每篇六步、措辞、数字）
- [design.md](design.md)：画布、配色、页面框架、版式 A–F、组件 API、示意图规范、检查清单
- [outline-template.md](outline-template.md)：大纲模板
- [script-template.md](script-template.md)：逐字稿模板
- 示例：`$PB/examples/structured-gs/`（大纲.md、逐字稿.md、make_assets.py、build_ppt.py）
