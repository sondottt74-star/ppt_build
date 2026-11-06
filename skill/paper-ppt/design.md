# 视觉规范（pptkit 已实现，照用即可）

## 画布与字体

- 16:9，`13.333 × 7.5 in`，空白版式；坐标单位英寸。中文 `PingFang SC`、西文 `Arial`（`style_run` 自动写 latin/ea/cs）。
- 字号：标题 28 粗体｜副标题 15｜正文 14–16｜卡片 13–14｜表格 11–13｜图注 10–11｜页脚 10。**不得小于 10。**
- matplotlib：`Arial Unicode MS`，公式 `mathtext.fontset = "cm"`，图内中文 13–17 号。

## 配色（`pptkit.theme`）

| 名称 | 色值 | 用途 |
|---|---|---|
| `NAVY` | 1F3A5F | 标题、表头、章节页底色 |
| `TEXT` / `SUB` | 222222 / 5C677D | 正文 / 次要文字、图注 |
| `LIGHT` / `LINE` | F3F6FA / C9D3E3 | 浅底卡片 / 细线 |
| `S_TASK` | 457B9D | 开场、主线页 |
| `C1..C5`（浅底 `C1L..C5L`） | 3A86FF / 2A9D8F / E76F51 / E09F3E / 6D597A | 第 1–5 篇论文各一色，该篇所有页的标签、面包屑、强调、卡片边框都用它 |
| `S_EXP` / `S_EXPL` | 7B2CBF / F1E9F8 | 总结、讨论 |
| `WARN_BG` / `WARN` | FDEDEC / 9B2C2C | 局限、“注意”卡 |
| 名次 `‹r› ‹o› ‹y›` | F4B6B6 / FAD7A0 / FFF3B0 | 表格第 1/2/3 名；`‹w›` 警示格 |
| `GREY_BAR` | C9D3E3 | 图表里的基线柱 |

示意图语义色（`pptkit.draw`）：中性物体 `BUILD` 浅灰，相机 `NAVY`，保留/可见 `VIS` 绿，删除/被挡 `OCC` 红，未选中 `IDLE` 浅灰。全场同一概念同一颜色。

## 页面框架（`Deck`）

- `Deck(out, assets, footer, footers={color: 论文全名·会议}, crumbs={color: [六步]})`
- `new_slide(title, tag, tag_color, subtitle=None, step=None, footer=None)`：左上标签胶囊、右上面包屑（`step` 高亮）、标题、副标题、标题下色条、页脚论文全名、右下页码。
  - 正文区：无副标题 `y ∈ [1.6, 6.95]`，有副标题 `y ∈ [1.95, 6.95]`；`x ∈ [0.55, 12.85]`。页脚区 `y ≥ 7.0` 不放内容。
- `section_slide(num, title, sub, color)`：全屏 NAVY，主色竖条和 72 号编号。
- `title_slide / outline_slide / discussion_slide / figure_slide`：整页配方。

## 版式（`pptkit.layouts`）

| 代号 | 版式 | 函数 / 典型坐标 |
|---|---|---|
| A | 左图右文 | `layout_fig_text(deck, s, fig, cap, color, points=… 或 bullets_=…, conclusion=…)`；图 `6.6 × 4.6`，右侧 `x = 7.5` |
| B | 上图下卡 | `layout_fig_cards(deck, s, fig, cap, cards, color, bar=…)`；图 `12.1 × 2.75`，卡片等分 |
| C | 左公式右解释 | `formula_blocks(deck, s, [(小标题, f_名, 一句解释)], color)`；右侧放示意图/算例表 `x = 7.1` |
| D | 横向流程 | `flow_row(s, ["步骤", …], color, y=…)`；5–6 个框，最后一个实心 |
| E | 表格 + 图表 + 数字卡 | `layout_table_chart(s, data, color, chart=dict(…), cards=[…])`；表 `(0.55, w 7.3)`，图 `(8.05, 4.8 × 3.2)`，卡 `y = 5.45` |
| F | 双图对照 | `layout_two_figs(deck, s, (fig, cap), (fig, cap), color, bar=…)`；两图各 `6.0` 宽 |

其他行组件：`card_row`、`num_card_row`、`numbered_points`、`limitation_grid`（2×2 警示卡）、`bottom_bar`（底部结论/过渡条，`y = 6.4`）。

## 基础组件（`pptkit.deck`）

| 函数 | 要点 |
|---|---|
| `textbox(s, x, y, w, h, lines, size, color, bold, align, accent)` | `**x**` 片段自动加粗 + 主色 |
| `bullets(s, x, y, w, h, items, size, accent, gap)` | 圆点用主色；`(text, 1)` 为二级 |
| `box(s, x, y, w, h, text, fill, line, size, shape, dash, radius)` | 卡片 / 胶囊 / `MSO_SHAPE.OVAL` 圆 / `FLOWCHART_DECISION` 菱形；`text` 可为多行 list |
| `circle(s, x, y, d, text, fill)` | 编号圆 |
| `arrow(s, x1, y1, x2, y2, color, dash)` | 直线箭头 |
| `deck.pic(s, name, x, y, w, h, align)` | 框内等比居中，返回实际位置；自动按 220 ppi 降采样、大照片转 JPEG；缺图画占位 |
| `caption(s, x, y, w, text)` | 统一写“论文原图（论文名）：……”或“示意：……” |
| `table(s, x, y, w, data, col_w, size, row_h, hl_row, hl_fill, first_col_colors)` + `merge_col0` + `legend_marks` | 表头 NAVY；本文行 `hl_row` 浅主色；单元格末尾 `‹r›‹o›‹y›‹w›` |
| `bar_chart(s, x, y, w, h, cats, series, colors, title, vmin, vmax, fmt, horizontal, point_colors, legend)` | 原生柱状图；基线 `GREY_BAR`，本文主色 |
| `num_card(s, x, y, w, h, big, small, fill, accent)` | 大数字卡 |

## 素材命名

- 论文原图：`<key>_<名>`（例 `sc_pipeline`），图注“论文原图（Scaffold-GS）：……”，用到哪几格就写哪几格。
- 公式：`f_<名>`，透明 PNG，`pic(..., w≤6, h≈0.5–0.85, align="left")`。
- 自绘：`d_<名>`，透明 PNG，图注“示意：……”。

## 检查清单（每页过一遍）

- [ ] 图文一致：文字里提到的编号、层号、颜色、标签和图中完全一致
- [ ] 公式、图注、标签不压在图或别的框上；图注与下一个元素至少隔 0.05 in
- [ ] 卡片里文字 ≤ 2 行（13 pt 时卡高 ≥ 1.0）；表格 ≤ 7 行 × 7 列
- [ ] 本页所有强调色属于当前论文；警示内容用 WARN 色
- [ ] 图注写清“论文原图（谁）”或“示意”
- [ ] 标题是一句结论，不是“实验结果”这类名词
- [ ] 每页文字 ≤ 约 450 字（`DENSE`）；能用图说清的不用文字
- [ ] 数字和论文表格一致，标明数据集
