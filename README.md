# ppt_build

论文 LaTeX 源码 → 组会汇报 PPT（python-pptx）+ 逐字稿。配合 Cursor / Claude skill `paper-ppt` 使用（`skill/paper-ppt/`）。

```
ppt_build/
├── pptkit/                 # 可复用库
│   ├── theme.py            # 配色、字体、字号
│   ├── deck.py             # Deck（页框架、页码、面包屑、页脚、图片自动降采样）+ 文本/卡片/箭头/表格/柱状图
│   ├── layouts.py          # 整页配方（标题/提纲/讨论/备用）和版式 A–F
│   ├── assets.py           # AssetDir：论文原图 pdf/png/eps → PNG、裁剪、mathtext 公式、保存示意图
│   └── draw.py             # matplotlib 示意图：Gaussian 椭球、伪 3D 楼块、相机、箭头
├── tools/
│   ├── new_talk.py         # 一条命令建工程：解包源码 + 建索引 + 填好模板
│   ├── ingest_papers.py    # tex 源码 → index.md（图 F# / 表 T# / 公式 E#）、flat.tex、图缩略图
│   ├── fig_grid.py         # 给论文图叠坐标网格，选单格裁剪框
│   └── check_deck.py       # 版面检查（越界/溢出/重叠/缺图/过密）+ LibreOffice 渲染 + 缩略总览 + 页面文字导出
├── templates/project/      # 新工程的 make_assets.py / build_ppt.py 骨架
├── skill/paper-ppt/        # skill：SKILL.md + narrative/design/大纲模板/逐字稿模板
└── examples/
    ├── structured-gs/      # Scaffold-GS / Octree-GS / Proxy-GS，39 页，含大纲和逐字稿
    └── 3dgs-basics/        # 最早的 3DGS 精读范本（独立脚本，未改用 pptkit）
```

## 快速开始

```bash
python3 -m pip install --user -r requirements.txt      # 渲染检查另需 LibreOffice：brew install --cask libreoffice
./install_skill.sh                                     # 把 skill 装到 ~/.cursor、~/.claude、~/.codex 的 skills 目录

python3 tools/new_talk.py ~/research/my-talk --title "我的汇报" \
    sc=~/dl/arXiv-2312.00109v1.tar.gz oc=~/dl/arXiv-2403.17898v2/ px=2509.24421v5
cd ~/research/my-talk
python3 ppt/make_assets.py && python3 ppt/build_ppt.py
python3 ~/research/ppt_build/tools/check_deck.py 我的汇报.pptx
```

论文来源可以是 arXiv 源码压缩包、解压后的目录、单个 `.tex`，或 arXiv id（自动下载 e-print）。

## 工程目录约定

```
<talk>/
├── papers/<key>/{src/, index.md, flat.tex, figures.json, figures_sheet_*.png}
├── notes/<key>.md          # 每篇精读笔记
├── ppt/{make_assets.py, build_ppt.py, assets/}
├── 大纲.md  逐字稿.md
├── check/{*.pdf, sheet_*.png, pages/, slides.md}
└── <标题>.pptx
```

## 复现示例

```bash
cd examples/structured-gs
python3 ../../tools/ingest_papers.py papers scaffold-gs=2312.00109v1 octree-gs=2403.17898v2 proxy-gs=2509.24421v5
python3 ppt/make_assets.py && python3 ppt/build_ppt.py
python3 ../../tools/check_deck.py 结构化高斯组会汇报.pptx
```
