"""结构化高斯组会汇报 (Scaffold-GS / Octree-GS / Proxy-GS): assemble ppt/assets/ into the .pptx.

Reference example for the paper-ppt skill. Run after make_assets.py:
    python ppt/build_ppt.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TALK = ROOT.parent
sys.path.insert(0, os.environ.get("PPT_BUILD", str(TALK.parents[1])))

from pptkit import *  # noqa: E402,F401,F403

A = ROOT / "assets"
OUT = TALK / "结构化高斯组会汇报.pptx"

FOOT_ALL = "结构化 3D Gaussian Splatting · Scaffold-GS / Octree-GS / Proxy-GS"
deck = Deck(
    OUT, A, footer=FOOT_ALL,
    footers={
        C1: "Scaffold-GS: Structured 3D Gaussians for View-Adaptive Rendering · CVPR 2024",
        C2: "Octree-GS: Towards Consistent Real-time Rendering with LOD-Structured 3D Gaussians",
        C3: "Proxy-GS: Unified Occlusion Priors for Training and Inference in Structured 3D Gaussian Splatting",
    },
    crumbs={
        C1: ["1 改了什么", "2 为什么", "3 方法", "4 训练", "5 实验", "6 局限"],
        C2: ["1 改了什么", "2 LOD", "3 方法", "4 训练", "5 实验", "6 局限"],
        C3: ["1 缺口", "2 改了什么", "3 遮挡判断", "4 训练", "5 实验", "6 局限"],
    },
)
new_slide, section_slide, pic = deck.new_slide, deck.section_slide, deck.pic

# ================================================================== 开场
# P1 title
title_slide(deck, "组会论文汇报", ["结构化 3D Gaussian Splatting", "从 Anchor 到 LOD 与遮挡先验"],
            "Scaffold-GS（CVPR 2024）  ·  Octree-GS  ·  Proxy-GS", hero="sc_teaser",
            hero_caption="论文原图（Scaffold-GS）：从初始点到 anchor 生成的 Gaussian，以及与 3DGS 的对比")

# P2 outline
outline_slide(deck, [
    ("00", "背景", "3DGS 怎么表示场景，什么是结构化高斯", S_TASK),
    ("01", "Scaffold-GS", "提出结构化高斯：anchor + 共享 MLP", C1),
    ("02", "Octree-GS", "结构有层级：远处用粗层，近处加细层", C2),
    ("03", "Proxy-GS", "结构知道遮挡：解码前跳过被挡住的 anchor", C3),
], closing="总结：三篇对照 + 讨论问题")

# P3 task -----------------------------------------------------------------
s = new_slide("任务：从多视图重建可渲染的 Gaussian 场景", "00 背景", S_TASK,
              "输入照片、位姿和稀疏点云，输出能从任意新视角实时渲染的场景", footer=FOOT_ALL)
textbox(s, 0.55, 2.0, 2.0, 0.4, "训练阶段", size=16, color=S_TASK, bold=True)
for k, nm in enumerate(["sc_train1", "sc_train2", "sc_train3"]):
    pic(s, nm, 0.6 + k * 0.16, 2.45 + k * 0.14, w=1.9, h=1.27, border="FFFFFF")
textbox(s, 0.55, 3.95, 2.4, 0.6, ["多视角 RGB 照片", "（静态场景）"], size=13, align=PP_ALIGN.CENTER, space_after=0)
arrow(s, 2.85, 3.15, 3.3, 3.15)
box(s, 3.35, 2.65, 1.6, 1.0, ["COLMAP", "SfM"], fill="E3ECF7", line=S_TASK, size=15, bold=True, color=NAVY)
arrow(s, 5.0, 3.15, 5.45, 3.15)
box(s, 5.5, 2.45, 2.3, 1.4, ["**相机位姿**", "+ 稀疏点云"], fill=LIGHT, line=LINE, size=14)
arrow(s, 7.85, 3.15, 8.3, 3.15)
box(s, 8.35, 2.55, 2.0, 1.2, ["结构化 Gaussian", "优化"], fill=S_TASK, size=15, bold=True, color="FFFFFF")
arrow(s, 10.4, 3.15, 10.85, 3.15)
pic(s, "sc_anchor", 10.9, 2.45, w=1.95, h=1.35)
textbox(s, 10.7, 3.85, 2.4, 0.4, "Gaussian 场景", size=13, align=PP_ALIGN.CENTER, space_after=0)
hline(s, 0.55, 4.6, 12.25)
textbox(s, 0.55, 4.75, 2.0, 0.4, "渲染阶段", size=16, color=S_TASK, bold=True)
box(s, 0.6, 5.3, 2.4, 1.0, ["训练好的场景", "+ 新相机位姿"], fill=LIGHT, line=LINE, size=13)
arrow(s, 3.05, 5.8, 3.65, 5.8)
box(s, 3.7, 5.3, 3.3, 1.0, ["生成 Gaussian → 投影 → α 混合"], fill=S_TASK, size=14, color="FFFFFF", bold=True)
arrow(s, 7.05, 5.8, 7.6, 5.8)
pic(s, "sc_ours", 7.65, 4.95, w=2.2, h=1.7)
textbox(s, 10.05, 5.0, 2.8, 0.8, ["**新视角 RGB 图像**", "实时渲染"], size=14, accent=S_TASK)
box(s, 10.05, 6.05, 2.8, 0.5, "不输出：精确 mesh / 语义 / 动态", fill=WARN_BG, size=12, color=WARN)

# P4 3DGS basics ----------------------------------------------------------
s = new_slide("普通 3DGS：一堆独立的椭球", "00 背景", S_TASK, footer=FOOT_ALL)
blocks = [
    ("① 一个 Gaussian 是一个椭球", "f_gauss", "μ 是中心，Σ 决定椭球的形状"),
    ("② 形状 = 缩放 + 旋转", "f_cov", "S 是三轴尺度，R 是旋转；另有颜色 c 和不透明度 α"),
    ("③ 投影后从前往后混合", "f_blend", "越靠前、越不透明，对像素贡献越大"),
]
for k, (t, f, d) in enumerate(blocks):
    y = 1.7 + k * 1.75
    textbox(s, 0.6, y, 6.2, 0.4, t, size=15, color=S_TASK, bold=True)
    pic(s, f, 0.75, y + 0.45, w=5.9, h=0.62, align="left")
    textbox(s, 0.75, y + 1.12, 6.0, 0.4, d, size=13, color=SUB)
pic(s, "d_gs_blend", 7.3, 1.65, 5.4, 3.1)
caption(s, 7.3, 4.75, 5.4, "示意：三个椭圆在同一像素处叠加")
box(s, 7.1, 5.15, 2.8, 1.75, ["**参数冗余**", "每个 Gaussian 独立存约 59 个参数，相邻的在重复表达同一块"],
    fill=WARN_BG, size=13, color=WARN, accent=WARN)
box(s, 10.05, 5.15, 2.8, 1.75, ["**计算不分远近**", "远处的、被挡住的 Gaussian 也要算"],
    fill=WARN_BG, size=13, color=WARN, accent=WARN)

# P5 storyline ------------------------------------------------------------
s = new_slide("结构化高斯：先建结构，再由结构生成 Gaussian", "00 主线", S_TASK, footer=FOOT_ALL)
box(s, 0.6, 1.62, 12.1, 0.7,
    "普通 3DGS：直接优化独立的 Gaussian　→　结构化高斯：**anchor（结构）+ 共享 MLP（生成规则）→ Gaussian**",
    fill="E3ECF7", line=S_TASK, size=15, accent=S_TASK)
pic(s, "d_building3", 0.6, 2.45, 12.1, 2.55)
for k, t in enumerate(["换一个角度看", "从远处走近", "被前面的楼挡住"]):
    textbox(s, 0.6 + k * 4.03, 4.95, 4.03, 0.35, t, size=13, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
cards = [("Scaffold-GS", "单层 anchor", "椭球随位姿变化", C1),
         ("Octree-GS", "多层 anchor", "远粗近细", C2),
         ("Proxy-GS", "多层 anchor + 粗几何", "跳过被挡住的", C3)]
for k, (t, a, b, col) in enumerate(cards):
    x = 0.6 + k * 4.12
    box(s, x, 5.45, 3.7, 1.4, [f"**{t}**", a, b], fill="FFFFFF", line=col, size=14, accent=col, line_w=2)
    if k < 2:
        arrow(s, x + 3.75, 6.15, x + 4.07, 6.15, color=NAVY)

# ================================================================== 01 Scaffold-GS
section_slide("01", "Scaffold-GS", "提出结构化高斯：anchor 组织 Gaussian，共享 MLP 生成属性", C1)

# P6
s = new_slide("相比普通 3DGS，结构化高斯改了两点", "01 Scaffold-GS", C1,
              "用一个共享 MLP 学 Gaussian 的属性；Gaussian 挂在 anchor 上", step=0)
pic(s, "d_vanilla_vs_struct", 0.6, 1.95, 12.1, 2.75)
for k, (t, d) in enumerate([("属性由共享 MLP 解码", "不再逐个存不透明度、颜色、尺度、旋转，而是用一个所有地方共用的小 MLP，根据当前视角解码"),
                            ("Gaussian 由 anchor 带出", "点云体素化，每个体素中心是一个 anchor，每个 anchor 生成附近的一组 Gaussian（默认 10 个）")]):
    x = 0.6 + k * 6.15
    box(s, x, 4.85, 5.95, 1.35, "", fill=C1L, line=C1)
    circle(s, x + 0.15, 5.0, 0.42, "①②"[k], C1)
    textbox(s, x + 0.7, 4.93, 5.1, 0.4, t, size=16, color=NAVY, bold=True)
    textbox(s, x + 0.7, 5.35, 5.1, 0.8, d, size=13, color=TEXT)
box(s, 0.6, 6.35, 12.1, 0.5, "渲染方式没变：最后仍是 Gaussian 投影 + α 混合。变的是 Gaussian 从哪里来。",
    fill=LIGHT, size=14, color=SUB)

# P7
s = new_slide("为什么要做成结构化高斯", "01 Scaffold-GS", C1, step=1)
pic(s, "d_view_ellipse", 0.6, 1.65, 6.6, 4.6)
caption(s, 0.6, 6.3, 6.6, "示意：同一个 anchor，两台相机。上：普通 3DGS 椭球固定；下：Scaffold-GS 椭球随视角变化")
reasons = [
    ("初始化就有结构", ["点云先整理成 anchor，而不是一堆互不相关的 Gaussian",
                    "一开始就知道哪些 Gaussian 属于同一块区域、这块区域多大"]),
    ("学 MLP，而不是学固定椭球", ["普通 3DGS 的椭球训完就固定，换位姿形状不变",
                           "Scaffold-GS 按相机到 anchor 的**距离和方向**重新解码尺度和旋转"]),
]
for k, (t, lines) in enumerate(reasons):
    y = 1.75 + k * 1.85
    circle(s, 7.5, y, 0.45, str(k + 1), C1)
    textbox(s, 8.1, y - 0.02, 4.7, 0.45, t, size=17, color=NAVY, bold=True)
    bullets(s, 8.1, y + 0.5, 4.75, 1.3, lines, size=13, accent=C1, gap=3)
box(s, 7.5, 5.55, 5.3, 1.1, "同一处场景，在不同位姿下得到更合适的高斯椭球", fill=C1, size=16, color="FFFFFF", bold=True)

# P8
s = new_slide("整体流程：从 SfM 点云到渲染图像", "01 Scaffold-GS", C1, step=2)
pic(s, "sc_pipeline", 0.6, 1.6, 12.1, 3.1)
caption(s, 0.6, 4.7, 12.1, "论文原图（Scaffold-GS）：(a) 体素化得到 anchor；(b) 视锥内 anchor 生成 k 个 neural Gaussian，属性由 MLP 解码；(c) 过滤低不透明度后光栅化")
steps = ["体素化 → anchor", "每个 anchor 存\nfeature / 尺度 / offset", "只取视锥内 anchor",
         "MLP 解码\nk 个 Gaussian", "丢掉不透明度\n过低的", "渲染 → 损失 → 反传"]
for k, t in enumerate(steps):
    x = 0.55 + k * 2.1
    last = k == 5
    box(s, x, 5.15, 1.85, 1.05, t.split("\n"), fill=C1 if last else C1L, line=C1, size=12,
        color="FFFFFF" if last else TEXT, bold=last)
    if k < 5:
        arrow(s, x + 1.87, 5.67, x + 2.08, 5.67, color=C1)
textbox(s, 0.55, 6.4, 12.2, 0.4, "第 1–2 步见下一页，第 3–5 步见“视角怎么进 MLP”，第 6 步见“训练”", size=13, color=SUB)

# P9
s = new_slide("Anchor 怎么来，Gaussian 放在哪", "01 Scaffold-GS", C1,
              "anchor 决定区域；offset 决定区域内部的位置", step=2)
_, (gx, gy, gw, gh) = pic(s, "d_anchor_spawn", 0.6, 1.95, 12.1, 2.35)
for k, t in enumerate(["SfM 点云", "体素化，每格留中心", "一个 anchor 发出 k 个 Gaussian"]):
    textbox(s, gx + k * gw / 3, gy + gh, gw / 3, 0.35, t, size=12, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
textbox(s, 0.6, 4.75, 6.0, 0.4, "① 体素化", size=15, color=C1, bold=True)
pic(s, "f_voxel", 0.75, 5.15, w=3.2, h=0.55, align="left")
textbox(s, 4.0, 5.2, 2.8, 0.5, "同一格只留一个代表：格子中心", size=12, color=SUB)
textbox(s, 0.6, 5.8, 6.0, 0.4, "② Gaussian 中心", size=15, color=C1, bold=True)
pic(s, "f_mu", 0.75, 6.2, w=3.2, h=0.5, align="left")
textbox(s, 4.0, 6.15, 2.8, 0.7, "anchor 定区域，offset 定位置，尺度定 offset 放多大", size=12, color=SUB)
table(s, 7.0, 4.75, 5.8, [
    ["参数", "维度", "负责什么", "是否学习"],
    ["位置 x_v", "3", "体素中心，定区域", "初始化后固定"],
    ["feature f_v", "32", "这块区域的样子", "学习"],
    ["尺度 l_v", "3", "区域大小", "学习"],
    ["offset O_v", "k×3", "k 个 Gaussian 怎么摆", "学习"],
], col_w=[1.4, 0.8, 2.1, 1.5], size=12, row_h=0.4)

# P10
s = new_slide("视角怎么进 MLP：feature + 距离 + 方向", "01 Scaffold-GS", C1, step=2)
for k, t in enumerate(["anchor feature f̂_v", "距离 δ_vc", "方向 d_vc"]):
    y = 1.85 + k * 0.95
    box(s, 0.6, y, 2.0, 0.7, t, fill=C1L, line=C1, size=13, bold=True, color=NAVY)
    arrow(s, 2.62, y + 0.35, 3.05, 2.95, color=C1)
box(s, 3.1, 2.0, 1.6, 1.95, ["共享 MLP", "所有 anchor", "共用"], fill=C1, size=14, color="FFFFFF", bold=True)
outs = [("不透明度 α", False), ("颜色 c", False), ("旋转 q", True), ("尺度 s", True)]
for k, (t, em) in enumerate(outs):
    y = 1.8 + k * 0.62
    arrow(s, 4.72, 2.97, 5.15, y + 0.25, color=C1, width=1.5)
    box(s, 5.2, y, 1.65, 0.5, t, fill="FFFFFF", line=C1, size=13, line_w=2.5 if em else 1, bold=em, color=NAVY)
textbox(s, 5.0, 4.32, 2.1, 0.35, "q、s 决定椭球形状", size=11, color=C1, bold=True, align=PP_ALIGN.CENTER)
pic(s, "f_dist", 0.7, 4.8, w=6.0, h=0.5, align="left")
pic(s, "f_mlp", 0.7, 5.45, w=6.0, h=0.5, align="left")
pic(s, "sc_featbank", 7.3, 1.6, 5.5, 1.75)
caption(s, 7.3, 3.35, 5.5, "论文原图：从一个 feature 切片重复出粗、中、细三种粒度，按视角混合")
pic(s, "sc_mlps", 7.3, 3.75, 5.5, 2.35)
caption(s, 7.3, 6.1, 5.5, "论文原图：四个属性 MLP 的结构")
box(s, 0.6, 6.15, 3.2, 0.65, "每个 anchor 自己的：feature、尺度、offset", fill=LIGHT, size=12, color=NAVY)
box(s, 3.85, 6.15, 3.0, 0.65, "所有 anchor 共享的：MLP", fill=C1L, line=C1, size=12, color=NAVY, bold=True)

# P11
s = new_slide("训练：误差反传，同时增删 anchor", "01 Scaffold-GS", C1, step=3)
textbox(s, 0.6, 1.68, 2.3, 0.45, "训练损失：", size=15, color=NAVY, bold=True)
pic(s, "f_loss", 2.4, 1.62, w=6.5, h=0.5, align="left")
textbox(s, 8.9, 1.68, 4.0, 0.45, "前两项贴近真图，体积项让 Gaussian 别太大", size=12, color=SUB)
pic(s, "sc_growing", 0.6, 2.35, 6.6, 3.3)
caption(s, 0.6, 5.65, 6.6, "论文原图（Scaffold-GS）：Gaussian 放进多分辨率格子，梯度大的格子加 anchor")
pic(s, "sc_init_refine", 7.45, 2.3, 2.45, 3.4)
caption(s, 7.3, 5.7, 2.75, "论文原图：Truck 初始 anchor（青）与训练后（橙）", size=10)
box(s, 10.15, 2.4, 2.7, 1.5, ["**Growing**", "梯度大 → 加 anchor"], fill=C1L, line=C1, size=14, accent=C1)
box(s, 10.15, 4.1, 2.7, 1.5, ["**Pruning**", "长期透明 → 删 anchor"], fill=LIGHT, line=SUB, size=14, accent=SUB)
box(s, 0.6, 6.3, 12.25, 0.55, "growing 补初始化没覆盖到的地方，pruning 把多余的 anchor 收回来",
    fill=C1L, size=15, color=NAVY, bold=True)

# P12
s = new_slide("实验：质量相当或更好，存储小 4–10 倍", "01 Scaffold-GS", C1,
              "论文主表：Mip-NeRF360 / Tanks&Temples / Deep Blending，均训练 30k iter", step=4)
t = table(s, 0.55, 2.0, 7.3, [
    ["数据集", "方法", "PSNR↑", "SSIM↑", "LPIPS↓", "FPS", "存储"],
    ["Mip-NeRF360", "3DGS", "28.69", "0.870‹r›", "0.182‹r›", "97", "693 MB"],
    ["", "Scaffold-GS", "28.84‹r›", "0.848", "0.220", "102‹r›", "156 MB‹r›"],
    ["Tanks&Temples", "3DGS", "23.14", "0.841", "0.183", "123‹r›", "411 MB"],
    ["", "Scaffold-GS", "23.96‹r›", "0.853‹r›", "0.177‹r›", "110", "87 MB‹r›"],
    ["Deep Blending", "3DGS", "29.41", "0.903", "0.243‹r›", "109", "676 MB"],
    ["", "Scaffold-GS", "30.21‹r›", "0.906‹r›", "0.254", "139‹r›", "66 MB‹r›"],
], col_w=[1.55, 1.25, 0.9, 0.9, 0.9, 0.75, 1.05], size=12, row_h=0.42, hl_row=[2, 4, 6])
merge_col0(t, [(1, 2), (3, 4), (5, 6)])
legend_y = 5.0
box(s, 0.6, legend_y, 0.28, 0.2, fill=RED, shape=MSO_SHAPE.RECTANGLE)
textbox(s, 0.92, legend_y - 0.06, 3.5, 0.3, "两者中更好的一项", size=10, color=SUB)
bar_chart(s, 8.05, 1.95, 4.8, 3.2, ["Mip-NeRF360", "Tanks&Temples", "Deep Blending"],
          [("3DGS", (693, 411, 676)), ("Scaffold-GS", (156, 87, 66))], [GREY_BAR, C1], "模型存储（MB）",
          vmin=0, vmax=800, legend=True)
for k, (big, small, warn) in enumerate([("≈ / ↑", "PSNR 相当或更高", False), ("4.4–10.2×", "存储更小", False),
                                        ("~100 FPS", "仍然实时", False),
                                        ("注意", "Mip-NeRF360 上 SSIM / LPIPS 不如 3DGS", True)]):
    x = 0.55 + k * 3.1
    num_card(s, x, 5.45, 2.95, 1.35, big, small, fill=WARN_BG if warn else C1L, accent=WARN if warn else C1)

# P13
s = new_slide("实验：椭球随位姿变化，远近变化大时更稳", "01 Scaffold-GS", C1, step=4)
pic(s, "sc_selector", 0.6, 1.6, 6.0, 2.65)
caption(s, 0.6, 4.25, 6.0, "论文原图：同一个 neural Gaussian，不同观察位置解码出的尺度（左）和不透明度（右）")
pic(s, "sc_google", 6.8, 1.6, 6.0, 2.65)
caption(s, 6.8, 4.25, 6.0, "论文原图：BungeeNeRF 拉近到未见距离，3DGS 出现针状伪影")
textbox(s, 0.6, 4.65, 6.0, 0.35, "消融（DB-Playroom）", size=14, color=C1, bold=True)
table(s, 0.6, 5.02, 6.0, [
    ["设置", "PSNR", "存储"],
    ["不做 anchor 增删", "28.45", "24 MB"],
    ["+ growing", "30.54", "71 MB"],
    ["+ growing + pruning（完整）", "30.62‹r›", "63 MB"],
], col_w=[3.2, 1.4, 1.4], size=12, row_h=0.33, hl_row=3)
num_card(s, 6.8, 4.75, 2.95, 1.35, "24.89 → 27.01", "BungeeNeRF PSNR", fill=C1L, accent=C1)
num_card(s, 9.9, 4.75, 2.95, 1.35, "1606 → 203 MB", "BungeeNeRF 存储", fill=C1L, accent=C1)
box(s, 6.8, 6.3, 6.05, 0.55, "对应前面：不同位姿下，重新解码的椭球比固定椭球更稳", fill=C1, size=13,
    color="FFFFFF", bold=True)

# P14
s = new_slide("局限：结构只有一层", "01 Scaffold-GS", C1, step=5)
bullets(s, 0.6, 1.75, 6.1, 3.1, [
    "**依赖初始点云**：无纹理区域点很少，growing 补不了完全没覆盖的地方",
    "**anchor 不是真实表面**：只是组织 Gaussian 的方式，几何不一定准",
    "**“更好的椭球”有范围**：限于训练见过的视角，离得太远 MLP 不保证可靠",
], size=15, accent=C1, gap=12)
box(s, 0.6, 4.75, 6.1, 1.6, ["**只有一套 anchor 粒度**",
                             "远看那栋楼时，栏杆这种细节 anchor 只要在视锥里，仍要先过 MLP，再靠不透明度丢掉"],
    fill=WARN_BG, size=14, color=WARN, accent=WARN, align=PP_ALIGN.LEFT)
pic(s, "d_octree_one", 7.4, 1.7, 2.6, 3.2)
box(s, 10.2, 2.4, 2.6, 1.6, ["远处也要", "这么细吗？"], fill="FFFFFF", line=C1, size=18, color=C1, bold=True, dash=True)
box(s, 7.0, 5.2, 5.85, 1.1, "→ Octree-GS：让结构有层级", fill=C2, size=20, color="FFFFFF", bold=True)

# ================================================================== 02 Octree-GS
section_slide("02", "Octree-GS", "让结构有层级：远处用粗层，近处加细层", C2)

# P15
s = new_slide("相比 Scaffold-GS，结构从一层变成多层", "02 Octree-GS", C2,
              "同一空间放多层 anchor；解码之前先按距离选层", step=0)
pic(s, "oc_teaser", 0.6, 1.95, 12.1, 2.75)
caption(s, 0.6, 4.7, 12.1, "论文原图（Octree-GS）：与 Scaffold-GS、Hierarchical-GS 对比，下排为 Gaussian 分布，标注 FPS 和每视角 Gaussian 数")
table(s, 0.6, 5.1, 12.1, [
    ["对比项", "Scaffold-GS", "Octree-GS"],
    ["anchor 结构", "一层", "多层"],
    ["什么时候筛选", "解码之后，看不透明度", "解码之前，看距离"],
    ["远看那栋楼 / 走到栏杆前", "细 anchor 仍要解码 / 还是同一套 anchor", "只用粗层 / 加上细层"],
], col_w=[2.9, 4.6, 4.6], size=13, row_h=0.42, header_fill=NAVY)

# P16
s = new_slide("八叉树与 LOD：把空间一层层切细", "02 Octree-GS", C2, step=1)
_, (gx, gy, gw, gh) = pic(s, "d_octree_levels", 0.6, 1.6, 7.2, 2.9)
pic(s, "f_delta", 8.15, 1.7, w=2.0, h=0.6, align="left")
bullets(s, 8.1, 2.45, 4.75, 2.1, [
    "沿三个方向各切一刀 → 8 个子块，有内容的地方继续切",
    "第 0 层最粗，每往下一层，边长减半",
    "**格子不参与渲染**：只决定 anchor 放哪、属于哪层",
], size=13, accent=C2, gap=5)
pic(s, "oc_anchorinit", 0.6, 4.7, 7.2, 2.05)
caption(s, 0.6, 6.72, 7.2, "论文原图（Octree-GS）：建八叉树 → 保留有效层 → 各层初始化 anchor", size=10)
box(s, 8.1, 4.7, 4.75, 2.1, "", fill=C2L, line=C2)
textbox(s, 8.3, 4.78, 4.4, 0.4, "面向的场景", size=15, color=C2, bold=True)
bullets(s, 8.3, 5.2, 4.45, 1.6, [
    "MatrixCity、MegaNeRF、UrbanScene3D、BungeeNeRF：城市、航拍、长轨迹",
    "共同点：远近跨度大——远处要形状，近处要窗户和栏杆",
], size=12, accent=C2, gap=4)

# P17
s = new_slide("多层 anchor 怎么初始化", "02 Octree-GS", C2, "先决定分几层，再在每一层上各做一次体素化", step=2)
pic(s, "oc_overview", 0.6, 1.95, 12.1, 2.55)
caption(s, 0.6, 4.5, 12.1, "论文原图（Octree-GS）：(a) 按视角选层，花瓶从 LOD 0 到 LOD 2 细节逐层累加；(b) 八叉树 anchor 初始化")
textbox(s, 0.6, 4.9, 6.0, 0.4, "① 分几层", size=15, color=C2, bold=True)
pic(s, "f_K", 0.75, 5.3, w=3.6, h=0.46, align="left")
textbox(s, 4.4, 5.32, 2.4, 0.4, "距离每翻一倍，多分一层", size=12, color=SUB)
textbox(s, 0.6, 5.85, 6.0, 0.4, "② 每层放 anchor", size=15, color=C2, bold=True)
pic(s, "f_VL", 0.75, 6.25, w=3.6, h=0.46, align="left")
textbox(s, 4.4, 6.27, 2.4, 0.4, "格子边长逐层减半", size=12, color=SUB)
textbox(s, 7.0, 4.88, 5.8, 0.35, "例：d̂_min = 1，d̂_max = 16 → K = 5", size=13, color=NAVY, bold=True)
table(s, 7.0, 5.25, 5.8, [
    ["LOD", "格子边长", "负责什么"],
    ["0", "δ", "楼的体块"],
    ["1", "δ/2", "立面分区"],
    ["2", "δ/4", "窗户"],
    ["…", "…", "栏杆、招牌"],
], col_w=[1.0, 1.8, 3.0], size=12, row_h=0.32, header_fill=C2)

# P18
s = new_slide("当前相机选哪几层：越远越粗", "02 Octree-GS", C2, step=2)
pic(s, "f_lod", 0.7, 1.65, w=6.0, h=0.85, align="left")
syms = [("d", "相机到 anchor 的距离，越远越粗"), ("s", "焦距、分辨率修正"),
        ("Φ", "把层号夹在 0 到 K−1"), ("ΔL", "anchor 自己的偏置，复杂处多给细节")]
for k, (sym, d) in enumerate(syms):
    y = 2.65 + k * 0.5
    circle(s, 0.7, y, 0.4, sym, C2, size=11)
    textbox(s, 1.2, y + 0.02, 5.5, 0.4, d, size=13)
box(s, 0.6, 4.7, 6.1, 0.55, "anchor 所在层 ≤ L̂ 就选中，否则不进 MLP", fill=C2, size=14, color="FFFFFF", bold=True)
pic(s, "oc_lodbias", 0.6, 5.35, 6.1, 1.35)
caption(s, 0.6, 6.7, 6.1, "论文原图：学到的 LOD bias 集中在建筑边缘；去掉 bias 边缘变糊", size=10)
pic(s, "d_lod_curve", 7.0, 1.6, 5.85, 3.45)
caption(s, 7.0, 5.03, 5.85, "示意：d̂_max = 16，s = 1；虚线为 ΔL > 0 的 anchor", size=10)
table(s, 7.0, 5.4, 5.85, [
    ["距离 d", "L*", "用到的层"],
    ["8", "1", "LOD 0–1"],
    ["4", "2", "LOD 0–2"],
    ["2", "3", "LOD 0–3"],
], col_w=[1.6, 1.4, 2.85], size=12, row_h=0.33, header_fill=C2)

# P19
s = new_slide("层是累加的，训练要先粗后细", "02 Octree-GS", C2, step=3)
cols_lod = [("1F6F66", "LOD 0"), ("6FC1B6", "LOD 1"), ("CDEBE6", "LOD 2")]
bars = [("远", 1, False), ("中", 2, True), ("近", 3, False)]
base_y, seg_h = 4.1, 0.65
for k, (lab, n, fade) in enumerate(bars):
    x = 0.9 + k * 1.8
    for j in range(n):
        col, name = cols_lod[j]
        is_fade = fade and j == n - 1
        box(s, x, base_y - (j + 1) * seg_h, 1.2, seg_h - 0.04, name, fill="EEF7F5" if is_fade else col,
            line=C2 if is_fade else None, dash=is_fade, size=11, color=NAVY if j > 0 else "FFFFFF",
            shape=MSO_SHAPE.RECTANGLE)
    textbox(s, x - 0.2, base_y + 0.03, 1.6, 0.35, lab, size=14, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
pic(s, "f_lambda", 0.7, 1.75, w=2.2, h=0.45, align="left")
textbox(s, 3.0, 1.8, 3.6, 0.4, "“中”的 LOD 1 是虚线框：正在按 λ 淡入", size=11, color=C2)
box(s, 0.6, 4.75, 3.0, 2.0, ["**累加**", "细层在粗层上补细节，不替换粗层"], fill=C2L, line=C2, size=13, accent=C2)
box(s, 3.75, 4.75, 3.0, 2.0, ["**淡入**", "下一层不透明度乘 λ，相机走近时逐渐变实，避免切换闪烁"], fill=C2L,
    line=C2, size=13, accent=C2)
pic(s, "oc_protraining", 7.0, 1.6, 5.85, 4.0)
caption(s, 7.0, 5.6, 5.85, "论文原图（Octree-GS）：上行先粗后细训练，各层分工清楚；下行所有层一起训，Gaussian 缠在一起", size=10)
box(s, 7.0, 6.1, 5.85, 0.7, "先训粗层，再逐步加入细层；粗层训练时间更长", fill=C2L, size=13, color=NAVY, bold=True)

# P20
s = new_slide("增删 anchor 也要考虑层级", "02 Octree-GS", C2, step=3)
box(s, 0.6, 1.85, 2.0, 0.8, "梯度大的 Gaussian", fill=NAVY, size=13, color="FFFFFF", bold=True)
arrow(s, 2.62, 2.25, 2.95, 2.25)
box(s, 3.0, 1.6, 3.3, 1.3, ["梯度 > 下一层", "门槛？"], fill="FFFFFF", line=C2, size=13,
    shape=MSO_SHAPE.FLOWCHART_DECISION, bold=True, color=NAVY)
arrow(s, 5.2, 2.85, 5.6, 3.3, color=C2)
textbox(s, 5.45, 2.85, 0.5, 0.3, "是", size=12, color=C2, bold=True)
arrow(s, 4.1, 2.85, 3.6, 3.3, color=SUB)
textbox(s, 3.4, 2.85, 0.5, 0.3, "否", size=12, color=SUB, bold=True)
box(s, 2.3, 3.35, 2.4, 0.65, "留在本层加 anchor", fill=LIGHT, size=12, color=SUB)
box(s, 4.85, 3.35, 2.0, 0.65, "升到更细一层", fill=C2L, line=C2, size=12, color=NAVY, bold=True)
pic(s, "f_tau", 0.7, 4.15, w=2.2, h=0.55, align="left")
textbox(s, 3.0, 4.2, 3.8, 0.5, "层越细，门槛越高：栏杆能进细层，平墙不必变细", size=12, color=SUB)
box(s, 0.6, 4.9, 3.0, 1.8, ["**按不透明度**", "长期透明 → 删", "（同 Scaffold-GS）"], fill=LIGHT, line=SUB, size=13,
    accent=SUB)
box(s, 3.75, 4.9, 3.0, 1.8, ["**按被选中频率**", "训练视角里很少被选中 → 没训好，容易成漂浮物 → 删"], fill=C2L,
    line=C2, size=13, accent=C2, line_w=2.5)
pic(s, "oc_viewfreq", 7.0, 1.7, 5.85, 4.2)
caption(s, 7.0, 5.95, 5.85, "论文原图（Octree-GS）：只按不透明度删仍有伪影；加上被选中频率后伪影消失，存储也降")

# P21
s = new_slide("实验：每视角 Gaussian 更少，大场景快很多", "02 Octree-GS", C2,
              "Scaffold-GS 数字取自 Octree-GS 论文的对照实验，不要和上一篇论文的数字混着比", step=4)
t = table(s, 0.55, 2.0, 7.4, [
    ["数据集", "方法", "PSNR↑", "每视角 Gaussian", "存储"],
    ["Mip-NeRF360", "Scaffold-GS", "27.90", "666k", "197.5 MB"],
    ["", "Octree-GS", "28.05‹r›", "657k‹r›", "139.6 MB‹r›"],
    ["Tanks&Temples", "Scaffold-GS", "24.48", "626k", "167.5 MB"],
    ["", "Octree-GS", "24.68‹r›", "443k‹r›", "88.5 MB‹r›"],
    ["Deep Blending", "Scaffold-GS", "30.28", "207k", "125.5 MB"],
    ["", "Octree-GS", "30.49‹r›", "112k‹r›", "71.7 MB‹r›"],
], col_w=[1.7, 1.5, 1.2, 1.6, 1.4], size=12, row_h=0.42, hl_row=[2, 4, 6], hl_fill=C2L)
merge_col0(t, [(1, 2), (3, 4), (5, 6)])
bar_chart(s, 8.2, 1.95, 4.65, 3.3, ["T1", "T2", "T3"],
          [("Scaffold-GS", (6.69, 7.37, 8.04)), ("Octree-GS", (40.91, 35.17, 40.31))], [GREY_BAR, C2],
          "MatrixCity 2K 平均 FPS（实时线 30）", vmin=0, vmax=50, fmt="0.0", legend=True)
for k, (big, small, warn) in enumerate([("PSNR 略高", "三个小数据集都高于 Scaffold-GS", False),
                                        ("~5×", "MatrixCity FPS：约 7–8 → 35–41", False),
                                        ("注意", "省的是每视角计算，不是总存储（Block_All 约 1.6 GB）", True)]):
    x = 0.55 + k * 4.12
    num_card(s, x, 5.5, 3.9, 1.3, big, small, fill=WARN_BG if warn else C2L, accent=WARN if warn else C2)

# P22
s = new_slide("实验：远近都对，每个模块都有用", "02 Octree-GS", C2, step=4)
pic(s, "oc_streetview", 0.6, 1.6, 6.0, 2.5)
caption(s, 0.6, 4.1, 6.0, "论文原图：街景中的栏杆、招牌、路面")
pic(s, "oc_multiscale", 6.8, 1.6, 6.0, 2.5)
caption(s, 6.8, 4.1, 6.0, "论文原图：BungeeNeRF Barcelona，近处起重机与远处楼面")
abl = [("去掉升到细层", 27.64), ("去掉选中频率", 27.74), ("去掉 ΔL", 27.85), ("去掉渐进训练", 27.86), ("完整模型", 28.05)]
bar_chart(s, 0.6, 4.45, 6.0, 2.5, [a for a, _ in abl], [("PSNR", [v for _, v in abl])], [C2],
          "Mip-NeRF360 平均 PSNR（消融）", vmin=27.4, vmax=28.2, fmt="0.00", horizontal=True,
          point_colors=["A8D5CF"] * 4 + [C2])
bullets(s, 6.9, 4.55, 5.95, 2.4, [
    "**去掉升到细层**：27.64，细节补不上",
    "**去掉 ΔL**：27.85，建筑边缘变差",
    "**去掉先粗后细训练**：27.86，Gaussian 变多，各层重复",
    "**去掉按选中频率删除**：存储涨到 244.4 MB，伪影变多",
], size=13, accent=C2, gap=5)

# P23
s = new_slide("局限：LOD 只看距离，不看遮挡", "02 Octree-GS", C2, step=5)
box(s, 0.6, 1.75, 6.1, 1.7, ["**不知道遮挡**",
                             "那栋楼被前面的楼挡住时，只要距离合适，它的 anchor 仍会被选中、被解码，但对画面没有贡献"],
    fill=WARN_BG, size=14, color=WARN, accent=WARN, align=PP_ALIGN.LEFT)
bullets(s, 0.6, 3.7, 6.1, 2.4, [
    "**只看距离不够准**：要靠 ΔL 和 growing 补救，参数不对时细层要么出不来，要么太多",
    "**依赖尺度**：点云尺度不稳，或训练测试焦距不一致，选层会偏",
], size=14, accent=C2, gap=10)
pic(s, "d_occlusion", 7.0, 1.7, 5.85, 3.55)
box(s, 7.0, 5.45, 5.85, 1.1, "→ Proxy-GS：让结构知道遮挡", fill=C3, size=20, color="FFFFFF", bold=True)
textbox(s, 0.6, 6.0, 6.1, 0.6, "层级结构解决了“需要多少细节”，没解决“看不看得见”", size=14, color=NAVY, bold=True)

# ================================================================== 03 Proxy-GS
section_slide("03", "Proxy-GS", "让结构知道遮挡：解码之前跳过被挡住的 anchor", C3)

# P24
s = new_slide("层级结构仍然不知道：哪些 anchor 被挡住了", "03 Proxy-GS", C3, step=0)
pic(s, "d_occlusion", 0.55, 1.65, 6.0, 4.4)
caption(s, 0.55, 6.05, 6.0, "示意：绿色可见，红色过了视锥和 LOD 却被挡住，灰色在视锥外")
pic(s, "px_teaser", 6.8, 1.65, 6.0, 4.4)
caption(s, 6.8, 6.05, 6.0, "论文原图（Proxy-GS）：与 Octree-GS 相比，解码的 anchor 集中到可见表面附近")
box(s, 0.55, 6.45, 12.25, 0.5, "不透明度要解码后才知道 → 需要在 MLP 之前就判断遮挡", fill=C3L, size=15, color=C3, bold=True)

# P25
s = new_slide("相比 Octree-GS：给结构加一个粗几何", "03 Proxy-GS", C3,
              "用粗网格画深度图，在 MLP 之前判断谁挡住谁", step=1)
pic(s, "px_framework", 0.6, 1.95, 12.1, 2.75)
caption(s, 0.6, 4.68, 12.1, "论文原图（Proxy-GS）：构建 proxy mesh → 硬件光栅化取深度（<1 ms）→ 剔除被遮挡 anchor；训练时还沿网格表面长 anchor", size=10)
pic(s, "px_meshes", 0.6, 5.0, 12.1, 0.78)
for k, (t, d) in enumerate([("为什么粗就够", "只判断前后关系，不参与渲染"),
                            ("从哪来", "COLMAP / LiDAR / 深度 / MapAnything"),
                            ("为什么快", "硬件光栅化只画深度，约 1 ms")]):
    x = 0.6 + k * 4.12
    box(s, x, 5.92, 3.9, 0.95, [f"**{t}**", d], fill=C3L, line=C3, size=13, accent=C3)

# P26
s = new_slide("遮挡怎么判断：比 proxy 深度更远就跳过", "03 Proxy-GS", C3, step=2)
for k, t in enumerate(["画 proxy 深度图", "anchor 投影到像素", "比较深度", "更远 → 跳过"]):
    x = 0.6 + k * 3.1
    last = k == 3
    box(s, x, 1.65, 2.75, 0.8, t, fill=C3 if last else C3L, line=C3, size=14, bold=True,
        color="FFFFFF" if last else NAVY)
    if k < 3:
        arrow(s, x + 2.77, 2.05, x + 3.08, 2.05, color=C3)
pic(s, "d_depth_test", 0.6, 2.65, 6.1, 2.45)
pic(s, "f_cull", 0.8, 5.2, w=5.0, h=0.55, align="left")
textbox(s, 0.6, 5.8, 6.1, 0.5, "γ = 安全裕度（论文取 0.3），防止网格误差误删可见 anchor", size=13, color=SUB)
pic(s, "px_gamma", 7.0, 2.6, 2.9, 3.6)
caption(s, 7.0, 6.15, 2.9, "论文原图：γ 太小，近处边界出现伪影", size=10)
pic(s, "px_time", 10.0, 2.6, 2.85, 3.6)
caption(s, 10.0, 6.15, 2.85, "论文原图：取深度只占很小一段", size=10)
box(s, 0.6, 6.5, 12.25, 0.45, "在 MLP 之前：被挡住的 anchor 不解码，也不生成要渲染的 Gaussian", fill=C3, size=14,
    color="FFFFFF", bold=True)

# P27
s = new_slide("训练也用同一套遮挡规则，新 anchor 长在表面上", "03 Proxy-GS", C3, step=3)
box(s, 0.6, 1.75, 2.85, 1.95, ["**只在测试时删**", "训练依赖过的 anchor 突然消失 → 画面缺一块"], fill=WARN_BG,
    size=13, color=WARN, accent=WARN)
box(s, 3.5, 2.45, 0.5, 0.5, "≠", fill="FFFFFF", size=22, color=WARN, bold=True)
box(s, 4.05, 1.75, 2.75, 1.95, ["**训练也删**", "训练和测试看到的是同一批 anchor"], fill=C2L, size=13, accent=C2)
steps = ["找误差大的图像区域", "用 proxy 深度反投影到表面", "在表面附近加 anchor", "同一格不重复加"]
for k, t in enumerate(steps):
    y = 3.95 + k * 0.7
    box(s, 0.6, y, 6.2, 0.55, f"{k + 1}  {t}", fill=C3L, line=C3, size=13, color=NAVY, bold=True, align=PP_ALIGN.LEFT)
    if k < 3:
        arrow(s, 3.7, y + 0.56, 3.7, y + 0.69, color=C3, width=1.5)
pic(s, "d_densify", 7.0, 1.7, 5.85, 4.25)
caption(s, 7.0, 5.95, 5.85, "示意：左 原 growing 长在楼后面；右 proxy-guided 长在表面上")
box(s, 7.0, 6.3, 5.85, 0.6, "Gaussian 和 Octree 层级没变；变的是哪些 anchor 被解码、被训练、长在哪里",
    fill=LIGHT, size=12, color=NAVY)

# P28
s = new_slide("实验：遮挡强的场景快 3–4 倍，质量不降", "03 Proxy-GS", C3, "MatrixCity 与真实场景，对比 Octree-GS", step=4)
table(s, 0.55, 2.0, 6.5, [
    ["场景", "Octree PSNR / FPS", "Proxy PSNR / FPS", "解码 anchor"],
    ["Block 1&2", "21.94 / 32", "22.11 / 126‹r›", "800k → 190k"],
    ["Block 3&4", "20.95 / 30", "21.06 / 134‹r›", "1040k → 190k"],
    ["Block 5", "21.41 / 48", "21.68 / 151‹r›", "720k → 80k"],
], col_w=[1.3, 1.75, 1.75, 1.7], size=12, row_h=0.45)
for k, (big, small) in enumerate([("3–4×", "MatrixCity FPS"), ("七到九成", "解码 anchor 减少"), ("≈ / ↑", "PSNR")]):
    num_card(s, 0.55 + k * 2.2, 4.0, 2.05, 1.3, big, small, fill=C3L, accent=C3)
box(s, 0.55, 5.55, 6.5, 1.0, ["**注意**：Berlin 遮挡弱，FPS 只从 263 到 275", "不能把 3–4 倍说成所有场景的加速"],
    fill=WARN_BG, size=13, color=WARN, accent=WARN)
bar_chart(s, 7.3, 1.9, 5.55, 2.55, ["Small City", "CUHK-LOWER", "Berlin"],
          [("Octree-GS", (51, 212, 263)), ("Proxy-GS", (139, 239, 275))], [GREY_BAR, C3],
          "FPS：遮挡越强，收益越大", vmin=0, vmax=320, legend=True)
pic(s, "px_vis", 7.3, 4.55, 5.55, 2.05)
caption(s, 7.3, 6.6, 5.55, "论文原图（Proxy-GS）：定性对比", size=10)

# P29
s = new_slide("实验：训练推理一致是关键", "03 Proxy-GS", C3, "Block 5 消融 + proxy 质量的影响", step=4)
table(s, 0.55, 1.95, 6.3, [
    ["设置", "PSNR", "FPS", "解码 anchor"],
    ["Octree-GS", "21.41", "48", "719k"],
    ["只在测试时跳过", "19.06‹w›", "165", "82k"],
    ["训练和测试都跳过", "21.50", "147", "93k"],
    ["+ 新 anchor 长在表面上", "21.68‹r›", "143", "106k"],
], col_w=[2.6, 1.1, 1.1, 1.5], size=12, row_h=0.38, hl_row=4, hl_fill=C3L)
bar_chart(s, 0.55, 3.95, 6.3, 2.45, ["Octree-GS", "只测试时跳过", "训练测试都跳过", "+ 表面生长"],
          [("PSNR", (21.41, 19.06, 21.50, 21.68))], [C3], "Block 5 PSNR", vmin=18.5, vmax=22, fmt="0.00",
          point_colors=[GREY_BAR, "E63946", "F5B7A6", C3])
pic(s, "px_proxy_quality", 7.1, 1.95, 5.75, 3.0)
caption(s, 7.1, 4.9, 5.75, "论文原图（Proxy-GS）：上行降低网格分辨率，下行加顶点噪声", size=10)
num_card(s, 7.1, 5.2, 2.8, 1.15, "108 MB → 824 KB", "网格变粗，质量几乎不变", fill=C2L, accent=C2)
num_card(s, 10.05, 5.2, 2.8, 1.15, "顶点噪声", "前后关系错了，质量明显下降", fill=WARN_BG, accent=WARN)
box(s, 0.55, 6.5, 12.3, 0.45, "只在测试时删会伤质量；网格可以粗，但前后关系不能错", fill=C3L, size=14, color=C3, bold=True)

# P30
s = new_slide("局限：依赖 proxy，遮挡少时收益小", "03 Proxy-GS", C3, step=5)
lims = [("proxy 不准会误删", "位置偏了、前后关系错了，可见物体会被切掉；室内无纹理时网格本身可能不可靠"),
        ("一张深度图表达不了半透明", "玻璃、树叶、栅栏这种没有单一深度的地方，硬性深度测试不够用"),
        ("遮挡少的场景收益小", "开阔场景本来就没多少能跳过的 anchor，画深度和测试的开销可能抵消节省"),
        ("需要额外准备几何", "要先生成、简化、对齐一个网格，流程比前两篇更复杂")]
for k, (t, d) in enumerate(lims):
    x = 0.6 + (k % 2) * 6.15
    y = 1.75 + (k // 2) * 2.3
    box(s, x, y, 6.0, 2.1, "", fill=WARN_BG)
    circle(s, x + 0.2, y + 0.2, 0.45, str(k + 1), WARN)
    tw = 3.6 if k == 0 else 5.1
    textbox(s, x + 0.8, y + 0.18, tw, 0.45, t, size=16, color=WARN, bold=True)
    textbox(s, x + 0.8, y + 0.7, tw, 1.3, d, size=13)
    if k == 0:
        pic(s, "px_noise20", x + 4.55, y + 0.25, 1.3, 1.6)
box(s, 0.6, 6.4, 12.15, 0.5, "→ 总结：三篇是同一个结构化高斯框架里，结构一步步变完整", fill=S_EXP, size=15,
    color="FFFFFF", bold=True)

# ================================================================== 总结
s = new_slide("三篇放在一起：结构一步步变完整", "总结", S_EXP, footer=FOOT_ALL)
pic(s, "d_building3", 0.6, 1.55, 12.1, 1.95)
table(s, 0.6, 3.7, 7.4, [
    ["那栋建筑", "方法", "结构", "做了什么"],
    ["换一个角度看", "Scaffold-GS", "单层 anchor", "共享 MLP 根据位姿生成椭球"],
    ["从远处走近", "Octree-GS", "多层 anchor", "远处粗层，近处加细层"],
    ["被前面的楼挡住", "Proxy-GS", "多层 + 粗几何", "解码前跳过被挡住的 anchor"],
], col_w=[1.6, 1.4, 1.5, 2.9], size=13, row_h=0.6, first_col_colors=[C1, C2, C3])
flow = [("普通 3DGS：独立 Gaussian", SUB), ("+ anchor 和共享 MLP", C1), ("+ 层级", C2), ("+ 遮挡", C3)]
for k, (t, col) in enumerate(flow):
    y = 3.7 + k * 0.68
    box(s, 8.3, y, 4.5, 0.52, t, fill="FFFFFF", line=col, size=14, color=NAVY, bold=True, line_w=1.8)
    if k < 3:
        arrow(s, 10.55, y + 0.53, 10.55, y + 0.67, color=col)
box(s, 0.6, 6.45, 12.2, 0.48,
    "Scaffold-GS 用结构生成高斯 → Octree-GS 让结构有层级 → Proxy-GS 让结构知道遮挡；后两篇的筛选都在 MLP 解码之前",
    fill=S_EXPL, size=13, color=S_EXP, bold=True)


discussion_slide(deck, [
    ("Q1", "proxy 几何不准时，怎样降低误删的风险？", "例如按深度置信度放大 γ，或在不确定区域不剔除"),
    ("Q2", "LOD 和遮挡筛选结合后，计算瓶颈会转移到哪里？", "proxy 深度、剩余 anchor 的 MLP，还是 Gaussian 排序？遮挡弱的场景呢？"),
], S_EXP)

# ================================================================== 备用页
figure_slide(deck, "备用：Scaffold-GS 定性对比", "sc_main", "论文原图（Scaffold-GS）：与 3DGS 在多个数据集上的定性对比", C1)
figure_slide(deck, "备用：Octree-GS 大场景定性", "oc_largescale", "论文原图（Octree-GS）：MegaNeRF / UrbanScene3D / MatrixCity 对比", C2)
figure_slide(deck, "备用：Proxy-GS 顶点噪声细节", "px_matrix", "论文原图（Proxy-GS）：Block 5 上不同顶点噪声的影响", C3)

s = new_slide("备用：被删掉的公式细节", "备用", NAVY, footer=FOOT_ALL)
for k, (t, f, d) in enumerate([
    ("Scaffold-GS feature bank", "f_bank", "从一个 32 维 feature 切片重复出三种粒度，按距离和方向的 Softmax 权重混合"),
    ("Scaffold-GS 多分辨率 growing 阈值", "f_grow", "格子越细，梯度阈值越高"),
    ("Proxy-GS 深度线性化", "f_depth", "硬件深度 z_hw ∈ [0,1] 用近远平面 n、f 换成线性深度，再加 γ 比较"),
]):
    y = 1.75 + k * 1.7
    textbox(s, 0.6, y, 12, 0.4, t, size=16, color=NAVY, bold=True)
    pic(s, f, 0.75, y + 0.45, w=6.5, h=0.7, align="left")
    textbox(s, 7.5, y + 0.5, 5.3, 0.8, d, size=13, color=SUB)

deck.save()
