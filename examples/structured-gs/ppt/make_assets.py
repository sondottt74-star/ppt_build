"""结构化高斯组会汇报: paper figures, mathtext formulas and matplotlib diagrams -> ppt/assets/.

Expects arXiv sources under papers/<key>/src (see tools/ingest_papers.py):
    python ~/research/ppt_build/tools/ingest_papers.py papers \\
        scaffold-gs=2312.00109v1 octree-gs=2403.17898v2 proxy-gs=2509.24421v5
    python ppt/make_assets.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TALK = ROOT.parent
sys.path.insert(0, os.environ.get("PPT_BUILD", str(TALK.parents[1])))

import numpy as np  # noqa: E402
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle  # noqa: E402,F401
from PIL import Image  # noqa: E402

from pptkit.assets import AssetDir, plt  # noqa: E402
from pptkit.draw import (BLUE, BUILD, EDGE, GREY, IDLE, NAVY, OCC, TEAL, VIS, WIN, View, arrow,  # noqa: E402,F401
                         building_iso, camera_iso, cov_wh, draw_blob, panel)

PAPERS = Path(os.environ.get("PAPERS_DIR", TALK / "papers"))
SC = PAPERS / "scaffold-gs" / "src"
OC = PAPERS / "octree-gs" / "src"
PX = PAPERS / "proxy-gs" / "src"

A = AssetDir(ROOT / "assets")
OUT = A.out
RED, GREEN = "#E63946", "#2A9D8F"


def save_fig(fig, name):
    A.save_fig(fig, name)


# ---------------------------------------------------------------- paper figures
def convert_paper_figs():
    pdfs = {
        "sc_teaser": SC / "images/scaffold-teaser-1118.pdf",
        "sc_pipeline": SC / "images/scaffold-pipeline-1118-fix.pdf",
        "sc_voxel": SC / "images/voxel.pdf",
        "sc_featbank": SC / "images/scaffold-featbank.pdf",
        "sc_mlps": SC / "images/MLPs_structure.pdf",
        "sc_growing": SC / "images/scaffold-intern.pdf",
        "sc_init_refine": SC / "images/init_refine_truck.pdf",
        "sc_main": SC / "images/scaffold-main_1118.pdf",
        "sc_selector": SC / "images/selector.pdf",
        "sc_google": SC / "images/google.pdf",
        "oc_teaser": OC / "fig/Teaser.pdf",
        "oc_overview": OC / "fig/Overview.pdf",
        "oc_anchorinit": OC / "fig/AnchorInit.pdf",
        "oc_protraining": OC / "fig/ProTraining.pdf",
        "oc_viewfreq": OC / "fig/ViewFrequency.pdf",
        "oc_streetview": OC / "fig/StreetView.pdf",
        "oc_multiscale": OC / "fig/MultiScale.pdf",
        "oc_lodbias_full": OC / "fig/LODBias.pdf",
        "oc_largescale": OC / "fig/LargeScale.pdf",
        "px_teaser": PX / "figures/teaser_1834.pdf",
        "px_gamma": PX / "figures/gamma.pdf",
        "px_time": PX / "figures/comparison_1113.pdf",
        "px_proxy_quality": PX / "figures/matrix_reduce.pdf",
        "px_meshes": PX / "figures/meshes_new.pdf",
        "px_matrix": PX / "figures/matrix.pdf",
    }
    for name, path in pdfs.items():
        A.pdf(name, path)
    A.image("px_framework", PX / "figures/framework.png")
    A.image("px_vis", PX / "figures/vis_1901.png")

    # crops checked against the PDF image grid (PDF points)
    main = SC / "images/scaffold-main_1118.pdf"
    A.pdf("sc_train1", main, clip=(6, 26, 208, 158))       # Mip360-Room GT
    A.pdf("sc_train2", main, clip=(658, 20, 875, 162))     # Mip360-Counter GT
    A.pdf("sc_train3", main, clip=(6, 325, 208, 445))      # Tanks&Temples Train GT
    A.pdf("sc_ours", main, clip=(222, 26, 428, 155))       # Room, Ours cell
    for n in ("sc_train1", "sc_train2", "sc_train3", "sc_ours"):
        A.frame(n, pad=12)
    A.pdf("sc_anchor", SC / "images/scaffold-teaser-1118.pdf", clip=(310, 15, 710, 295))
    # top two rows only: LOD Bias + Rendering w/o Bias (row 3 starts at y=1653)
    A.pdf("oc_lodbias", OC / "fig/LODBias.pdf", clip=(0, 0, 4527, 1648), pad=2)
    # bottom-right cell of matrix_reduce: 20% vertex noise, including its caption
    A.pdf("px_noise20", PX / "figures/matrix_reduce.pdf", clip=(553.6, 117.5, 726, 231), pad=2)


# ---------------------------------------------------------------- formulas
FORMULAS = {
    "f_gauss": r"$G(x)=\exp\!\left(-\frac{1}{2}(x-\mu)^{T}\Sigma^{-1}(x-\mu)\right)$",
    "f_cov": r"$\Sigma=RSS^{T}R^{T}$",
    "f_blend": r"$C(x')=\sum_{i}c_{i}\sigma_{i}\prod_{j<i}(1-\sigma_{j}),\ \ \sigma_{i}=\alpha_{i}G'_{i}(x')$",
    "f_voxel": r"$\mathbf{V}=\{\lfloor\mathbf{P}/\epsilon\rceil\}\cdot\epsilon$",
    "f_mu": r"$\boldsymbol{\mu}_{v,j}=\mathbf{x}_{v}+\mathbf{O}_{v,j}\odot\mathbf{l}_{v}$",
    "f_dist": r"$\delta_{vc}=\|\mathbf{x}_{v}-\mathbf{x}_{c}\|_{2},\ \ \vec{\mathbf{d}}_{vc}=(\mathbf{x}_{v}-\mathbf{x}_{c})/\delta_{vc}$",
    "f_mlp": r"$\{\alpha_{j}\},\{c_{j}\},\{q_{j}\},\{s_{j}\}=F_{\alpha,c,q,s}(\hat{f}_{v},\delta_{vc},\vec{\mathbf{d}}_{vc})$",
    "f_loss": r"$\mathcal{L}=\mathcal{L}_{1}+\lambda_{\mathrm{SSIM}}\mathcal{L}_{\mathrm{SSIM}}+\lambda_{\mathrm{vol}}\mathcal{L}_{\mathrm{vol}}$",
    "f_delta": r"$\delta_{L}=\delta/2^{L}$",
    "f_K": r"$K=\lfloor\log_{2}(\hat{d}_{\max}/\hat{d}_{\min})\rceil+1$",
    "f_VL": r"$\mathbf{V}_{L}=\{\lfloor\mathbf{P}/(\delta/2^{L})\rceil\cdot\delta/2^{L}\}$",
    "f_lod": r"$L^{*}=\Phi\!\left(\log_{2}\dfrac{\hat{d}_{\max}}{d\cdot s}\right)+\Delta L,\ \ \hat{L}=\lfloor L^{*}\rfloor$",
    "f_lambda": r"$\lambda=L^{*}-\hat{L}\in[0,1)$",
    "f_tau": r"$\tau_{g}^{L}=\tau_{g}\cdot 2^{\beta L}$",
    "f_cull": r"$z_{\mathrm{anchor}}>z_{\mathrm{proxy}}+\gamma \ \Rightarrow\ \mathrm{skip}$",
    # backup page
    "f_bank": r"$\hat{f}_{v}=w\,f_{v}+w_{1}\,f_{v_{\downarrow 1}}+w_{2}\,f_{v_{\downarrow 2}}$",
    "f_grow": r"$\epsilon_{g}^{(m)}=\epsilon_{g}/4^{\,m-1},\quad \tau_{g}^{(m)}=\tau_{g}\cdot 2^{\,m-1}$",
    "f_depth": r"$d=\dfrac{n\,f}{f-z_{hw}\,(f-n)}$",
}


# ---------------------------------------------------------------- d_gs_blend (template fig_pixel_blend_screen, relabeled)
F = 2.4
PLANE_Y, PLANE_Z = 1.5, 1.1
PIX = 0.25
PIX_C = np.array([0.125, 0.125])
GAUSS = [
    (4.2, np.array([0.0, 0.05, -0.08]), (0.22, 0.6, 0.3), 30, RED, "G1"),
    (5.9, np.array([0.0, -0.18, 0.12]), (0.3, 0.38, 0.78), -20, GREEN, "G2"),
    (7.6, np.array([0.0, 0.22, 0.04]), (0.35, 0.9, 0.42), 10, BLUE, "G3"),
]


def _rot_z(deg):
    a = np.radians(deg)
    return np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])


def project_gaussian(c, Sigma, f):
    x, y, z = c
    mu = np.array([f * y / x, f * z / x])
    J = np.array([[-f * y / x ** 2, f / x, 0], [-f * z / x ** 2, 0, f / x]])
    return mu, J @ Sigma @ J.T


def gaussians_world():
    ray_dir = np.array([F, PIX_C[0], PIX_C[1]]) / F
    out = []
    for t, off, s, ang, col, lab in GAUSS:
        c = t * ray_dir + off
        R = _rot_z(ang)
        Sigma = R @ np.diag(np.square(s)) @ R.T
        out.append((c, Sigma, col, lab))
    return out


def fig_gs_blend():
    fig, ax = plt.subplots(figsize=(5.6, 3.15))
    ax.set_aspect("equal")
    for y in np.arange(-PLANE_Y, PLANE_Y + 1e-6, PIX):
        ax.plot([y, y], [-PLANE_Z, PLANE_Z], color="#C9D3E3", lw=0.7, zorder=1)
    for z in np.arange(-PLANE_Z, PLANE_Z + 1e-6, PIX):
        ax.plot([-PLANE_Y, PLANE_Y], [z, z], color="#C9D3E3", lw=0.7, zorder=1)
    label_at = {"G1": (0.95, -0.02), "G2": (0.12, 0.95), "G3": (-0.72, -0.42)}
    for c, Sigma, col, lab in reversed(gaussians_world()):
        mu, cov = project_gaussian(c, Sigma, F)
        draw_blob(ax, mu, cov, col, nsig=2.0, layer_alpha=0.17, z=2, highlight=False)
        ax.text(*label_at[lab], lab, color=col, fontsize=15, fontweight="bold", ha="center", va="center", zorder=6,
                bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none", alpha=0.92))
    ax.add_patch(Rectangle(PIX_C - PIX / 2, PIX, PIX, fc="none", ec="black", lw=2.6, zorder=7))
    ax.set_xlim(-PLANE_Y, PLANE_Y)
    ax.set_ylim(-PLANE_Z, PLANE_Z)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(NAVY)
        s.set_linewidth(1.6)
    save_fig(fig, "d_gs_blend")


# ---------------------------------------------------------------- d_building3
def _stage(ax):
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-1.15, 1.15)
    ax.set_ylim(-0.95, 1.05)


def fig_building3():
    view = View([-0.72, -1.05, 0.62])
    fig, axes = plt.subplots(1, 3, figsize=(12.4, 2.85))

    # 1. orbit
    ax = axes[0]
    _stage(ax)
    building_iso(ax, view, -0.34, -0.28, 0, 0.7, 0.55, 0.95, rows=4, cols=3, zorder=3)
    for ang, rad in ((165, 1.35), (255, 1.45), (345, 1.35)):
        th = np.radians(ang)
        pos = (rad * np.cos(th), rad * np.sin(th), 0.05)
        camera_iso(ax, view, pos, scale=0.32, z=5)
    ax.annotate("", xy=(0.72, 0.55), xytext=(0.15, 0.85),
                arrowprops=dict(arrowstyle="-|>", color=NAVY, lw=1.3, connectionstyle="arc3,rad=-0.35"))
    ax.text(0, -0.88, "①", fontsize=15, ha="center", color=NAVY, fontweight="bold")

    # 2. walk closer: far (coarse) then near (windows)
    ax = axes[1]
    _stage(ax)
    building_iso(ax, view, -0.95, -0.15, 0, 0.38, 0.30, 0.48, rows=2, cols=2, zorder=3)
    camera_iso(ax, view, (-0.95, -0.85, 0.05), scale=0.26, z=5)
    ax.text(-0.72, -0.78, "远", fontsize=13, color=NAVY, ha="center")
    building_iso(ax, view, 0.15, -0.22, 0, 0.62, 0.48, 0.92, rows=5, cols=3, zorder=3)
    camera_iso(ax, view, (0.28, -0.95, 0.02), scale=0.32, z=5)
    ax.text(0.55, -0.82, "近", fontsize=13, color=NAVY, ha="center")
    arrow(ax, (-0.15, -0.15), (0.05, -0.05), color=NAVY, lw=1.4, ms=12, z=6)
    ax.text(0, -0.88, "②", fontsize=15, ha="center", color=NAVY, fontweight="bold")

    # 3. occlusion: camera — front building — red back building, collinear
    ax = axes[2]
    _stage(ax)
    camera_iso(ax, view, (-1.05, -0.15, 0.05), scale=0.32, z=5)
    building_iso(ax, view, -0.35, -0.22, 0, 0.48, 0.40, 0.78, rows=4, cols=2, zorder=4)
    building_iso(ax, view, 0.45, -0.16, 0, 0.42, 0.36, 0.7, color="#E7A19A", rows=3, cols=2,
                 zorder=2, win="#F6D5D2")
    # sight line along the row of objects
    a = view.p([-0.85, -0.05, 0.35])
    b = view.p([0.85, -0.05, 0.35])
    ax.plot([a[0], b[0]], [a[1], b[1]], color=OCC, lw=1.2, ls="--", zorder=6)
    ax.text(0, -0.88, "③", fontsize=15, ha="center", color=NAVY, fontweight="bold")
    fig.tight_layout(w_pad=0.4)
    save_fig(fig, "d_building3")


# ---------------------------------------------------------------- d_vanilla_vs_struct
def fig_vanilla_vs_struct():
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 2.75))
    rng = np.random.default_rng(7)
    ax = axes[0]
    panel(ax, "普通 3DGS")
    ax.set_xlim(-0.2, 10.2)
    ax.set_ylim(-0.3, 6.4)
    spots = [(1.2, 4.6, 1.5, 0.7, 25), (3.4, 5.0, 1.1, 0.85, -20), (5.6, 4.5, 1.6, 0.55, 50),
             (8.0, 4.8, 1.3, 0.9, -40), (2.0, 2.2, 1.4, 0.6, 15), (4.6, 2.0, 1.7, 0.7, -30),
             (7.2, 2.4, 1.2, 0.85, 60), (9.0, 1.6, 1.0, 0.7, 10)]
    cols = [BLUE, TEAL, "#F4A261", RED, BLUE, TEAL, "#F4A261", RED]
    for (x, y, w, h, ang), col in zip(spots, cols):
        draw_blob(ax, (x, y), cov_wh(w, h, ang), col, nsig=2.0, layer_alpha=0.18, z=2, highlight=False)
        ax.text(x, y - h * 1.15, "μ  s  q  α  SH", fontsize=9, color=EDGE, ha="center", va="top", zorder=5,
                bbox=dict(boxstyle="round,pad=0.05", fc="white", ec="none", alpha=0.85))
    ax.text(5.1, 0.15, "每个椭球各自存一份参数", fontsize=13, color=EDGE, ha="center")

    ax = axes[1]
    panel(ax, "结构化高斯")
    ax.set_xlim(-0.4, 10.6)
    ax.set_ylim(-0.3, 6.4)
    # shared MLP
    ax.add_patch(FancyBboxPatch((4.15, 2.55), 2.3, 1.35, boxstyle="round,pad=0.08,rounding_size=0.15",
                                fc=BLUE, ec=BLUE, zorder=5))
    ax.text(5.3, 3.22, "共享 MLP", fontsize=14, color="white", ha="center", va="center", fontweight="bold", zorder=6)
    anchors = [(1.5, 5.15), (8.7, 5.15), (1.5, 1.15), (8.7, 1.15)]
    for i, (x, y) in enumerate(anchors):
        for k, (dx, dy, w, h, ang) in enumerate([
            (-0.55, 0.35, 0.7, 0.38, 20), (0.15, 0.45, 0.62, 0.42, -25),
            (0.55, -0.05, 0.7, 0.32, 40), (-0.2, -0.35, 0.66, 0.36, -10),
        ]):
            draw_blob(ax, (x + dx, y + dy), cov_wh(w, h, ang), BLUE if i % 2 == 0 else TEAL,
                      nsig=2.0, layer_alpha=0.16, z=2, highlight=False, levels=6)
        ax.add_patch(Circle((x, y), 0.13, fc="black", ec="white", lw=0.6, zorder=7))
        arrow(ax, (5.3, 3.22), (x, y), color=BLUE, lw=1.1, ms=11, z=4)
    ax.text(5.3, 0.15, "anchor 带出 Gaussian，属性由同一个 MLP 解码", fontsize=13, color=EDGE, ha="center")

    # big arrow between the two panels, drawn in figure coordinates
    fig.tight_layout(w_pad=1.6)
    fig.add_artist(FancyArrowPatch((0.478, 0.52), (0.535, 0.52), transform=fig.transFigure,
                                   arrowstyle="-|>", mutation_scale=22, lw=2.6, color=NAVY))
    save_fig(fig, "d_vanilla_vs_struct")


# ---------------------------------------------------------------- d_view_ellipse
def _screen(ax, x, y, cov, color, title):
    ax.add_patch(FancyBboxPatch((x, y), 1.7, 1.25, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc="#F7F9FC", ec="#C9D3E3", lw=1.0, zorder=2))
    draw_blob(ax, (x + 0.85, y + 0.62), cov, color, nsig=2.0, layer_alpha=0.2, z=3, highlight=False)
    ax.text(x + 0.85, y + 1.38, title, fontsize=13, color=NAVY, ha="center")


def fig_view_ellipse():
    fig, ax = plt.subplots(figsize=(6.6, 4.7))
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-0.2, 10.4)
    ax.set_ylim(-0.15, 7.5)
    ax.text(5.2, 7.15, "普通 3DGS：两台相机看到同一个椭球", fontsize=15, color=NAVY, ha="center", fontweight="bold")
    ax.text(5.2, 3.55, "Scaffold-GS：两台相机看到不同的椭球", fontsize=15, color=BLUE, ha="center", fontweight="bold")
    same = cov_wh(1.05, 0.48, 28)

    def _cam(x, y, lab):
        ax.add_patch(FancyBboxPatch((x, y), 0.62, 0.42, boxstyle="round,pad=0.02,rounding_size=0.06",
                                    fc=NAVY, ec=NAVY, zorder=5))
        ax.add_patch(Polygon([[x + 0.62, y + 0.1], [x + 0.95, y - 0.02], [x + 0.95, y + 0.44], [x + 0.62, y + 0.32]], fc=NAVY, zorder=5))
        ax.text(x + 0.28, y - 0.42, lab, fontsize=13, color=NAVY, ha="center")

    _cam(0.15, 5.35, "正看")
    _cam(5.55, 5.35, "侧看")
    _screen(ax, 1.35, 5.0, same, GREY, "")
    _screen(ax, 6.75, 5.0, same, GREY, "")
    ax.add_patch(Circle((5.15, 5.55), 0.09, fc="black", zorder=6))
    ax.text(5.15, 4.72, "anchor", fontsize=12, color=EDGE, ha="center")

    _cam(0.15, 1.45, "正看")
    _cam(5.55, 1.45, "侧看")
    _screen(ax, 1.35, 1.1, cov_wh(0.78, 0.62, 8), BLUE, "")
    _screen(ax, 6.75, 1.1, cov_wh(1.25, 0.34, -32), TEAL, "")
    ax.add_patch(Circle((5.15, 1.65), 0.09, fc="black", zorder=6))
    ax.text(5.15, 0.82, "同一 anchor", fontsize=12, color=EDGE, ha="center")
    save_fig(fig, "d_view_ellipse")


# ---------------------------------------------------------------- d_anchor_spawn
def fig_anchor_spawn():
    fig, axes = plt.subplots(1, 3, figsize=(12.2, 2.45))
    rng = np.random.default_rng(2)

    ax = axes[0]
    panel(ax, "①")
    ax.set_xlim(-0.2, 6.2)
    ax.set_ylim(-0.2, 4.4)
    pts = rng.uniform([0.3, 0.3], [5.8, 4.0], size=(46, 2))
    ax.scatter(pts[:, 0], pts[:, 1], s=18, c=NAVY, zorder=3)

    ax = axes[1]
    panel(ax, "②")
    ax.set_xlim(-0.2, 6.2)
    ax.set_ylim(-0.2, 4.4)
    for i in range(4):
        for j in range(3):
            ax.add_patch(Rectangle((0.3 + i * 1.4, 0.3 + j * 1.25), 1.4, 1.25, fc="none", ec="#C9D3E3", lw=1.0, zorder=1))
            ax.add_patch(Circle((1.0 + i * 1.4, 0.92 + j * 1.25), 0.16, fc="black", zorder=4))

    ax = axes[2]
    panel(ax, "③")
    ax.set_xlim(-0.3, 6.4)
    ax.set_ylim(-0.3, 4.6)
    # one anchor, scale box, k offsets
    ax.add_patch(Rectangle((1.15, 0.7), 3.5, 2.8, fc="#F4F7FB", ec=BLUE, lw=1.2, ls="--", zorder=1))
    ax.text(4.55, 3.35, r"$\mathbf{l}_{v}$", fontsize=13, color=BLUE, ha="left")
    ax.add_patch(Circle((2.3, 1.7), 0.11, fc="black", zorder=6))
    ax.text(2.3, 1.28, r"$\mathbf{x}_{v}$", fontsize=13, color="black", ha="center")
    offs = [(3.3, 3.0), (4.15, 2.45), (4.3, 1.7), (3.9, 1.05), (3.1, 0.95),
            (1.55, 3.15), (0.7, 2.5), (0.85, 1.55), (1.5, 2.45), (3.6, 2.0)]
    for i, (x, y) in enumerate(offs):
        draw_blob(ax, (x, y), cov_wh(0.55, 0.32, 20 + 15 * (i % 3)), BLUE, nsig=2.0,
                  layer_alpha=0.18, z=3, highlight=False, levels=5)
        arrow(ax, (2.4, 1.8), (x - 0.05, y - 0.02), color=NAVY, lw=0.8, ms=8, z=4)
    ax.text(5.15, 2.15, r"$\mathbf{O}_{v,j}$", fontsize=13, color=NAVY)
    ax.text(3.2, 0.15, "k = 10", fontsize=13, color=NAVY, ha="center", fontweight="bold")
    fig.tight_layout(w_pad=0.6)
    save_fig(fig, "d_anchor_spawn")


# ---------------------------------------------------------------- d_octree_levels
def _building_mask(nx, ny):
    """Occupancy of a building silhouette on a unit grid."""
    occ = np.zeros((ny, nx), dtype=bool)
    for j in range(ny):
        for i in range(nx):
            # tower + podium
            in_podium = 0.5 <= i <= nx - 1.5 and j <= ny * 0.45
            in_tower = nx * 0.28 <= i <= nx * 0.72 and j <= ny * 0.92
            occ[j, i] = in_podium or in_tower
    return occ


def fig_octree_levels():
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 3.05))
    labels = [(0, "LOD 0", r"$\delta$"), (1, "LOD 1", r"$\delta/2$"), (2, "LOD 2", r"$\delta/4$")]
    for ax, (level, title, delta) in zip(axes, labels):
        panel(ax, title)
        n = 2 * (2 ** level)  # 2, 4, 8 across
        nx, ny = n, n
        occ = _building_mask(nx, ny)
        ax.set_xlim(-0.4, nx + 0.4)
        ax.set_ylim(-1.15, ny + 0.35)
        for j in range(ny):
            for i in range(nx):
                ax.add_patch(Rectangle((i, j), 1, 1, fc=BUILD if occ[j, i] else "none",
                                       ec="#D5DDE8", lw=0.6, zorder=1))
                if occ[j, i]:
                    ax.add_patch(Circle((i + 0.5, j + 0.5), 0.12, fc=VIS, ec="white", lw=0.4, zorder=3))
        ax.text(nx / 2, -0.75, delta, fontsize=15, color=NAVY, ha="center")
    fig.tight_layout(w_pad=0.5)
    save_fig(fig, "d_octree_levels")


# ---------------------------------------------------------------- d_lod_curve
def fig_lod_curve():
    d = np.logspace(np.log10(1.4), np.log10(16), 500)
    Ls = np.clip(np.log2(16.0 / d), 0, 4)
    Lh = np.floor(Ls + 1e-8)
    Lb = np.clip(Ls + 0.6, 0, 4)
    fig, ax = plt.subplots(figsize=(5.9, 3.55))
    ax.plot(d, Ls, color=TEAL, lw=2.2, label=r"$L^{*}$")
    ax.step(d, Lh, where="post", color=NAVY, lw=1.8, label=r"$\hat{L}$")
    ax.plot(d, Lb, color=TEAL, lw=1.5, ls="--", label=r"$\Delta L>0$")
    for dist, txt in ((8, "用到 LOD 1"), (4, "用到 LOD 2"), (2, "用到 LOD 3")):
        ax.axvline(dist, color="#C9D3E3", lw=1.0, ls="--", zorder=0)
        ax.text(dist, 4.15, txt, fontsize=12, color=NAVY, ha="center")
    ax.set_xscale("log")
    ax.set_xlim(1.4, 16)
    ax.set_ylim(-0.2, 4.55)
    ax.set_xlabel(r"相机距离 $d$（对数）", fontsize=13)
    ax.set_ylabel("层号", fontsize=13)
    ax.set_xticks([2, 4, 8, 16])
    ax.set_xticklabels(["2", "4", "8", "16"])
    ax.tick_params(labelsize=11)
    ax.legend(frameon=False, fontsize=12, loc="center left", bbox_to_anchor=(1.02, 0.55))
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    save_fig(fig, "d_lod_curve")


# ---------------------------------------------------------------- d_occlusion  (top view)
def fig_occlusion():
    fig, ax = plt.subplots(figsize=(6.05, 4.45))
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-0.4, 10.6)
    ax.set_ylim(-0.5, 7.3)
    # frustum
    frustum = np.array([[0.7, 3.4], [9.6, 6.5], [9.6, 0.5], [0.7, 3.4]])
    ax.add_patch(Polygon(frustum, closed=True, fc="#EAF3F1", ec=TEAL, lw=1.2, alpha=0.55, zorder=0))
    # camera
    ax.add_patch(FancyBboxPatch((-0.05, 3.15), 0.7, 0.5, boxstyle="round,pad=0.02,rounding_size=0.06", fc=NAVY, zorder=5))
    ax.add_patch(Polygon([[0.65, 3.28], [1.05, 3.1], [1.05, 3.7], [0.65, 3.52]], fc=NAVY, zorder=5))
    ax.text(0.35, 2.7, "相机", fontsize=14, color=NAVY, ha="center")
    # foreground building
    ax.add_patch(FancyBboxPatch((3.15, 2.15), 1.7, 2.5, boxstyle="round,pad=0.02,rounding_size=0.05",
                                fc=BUILD, ec=EDGE, lw=1.0, zorder=3))
    ax.text(4.0, 4.8, "前景楼", fontsize=14, color=NAVY, ha="center")
    # background building, red
    ax.add_patch(FancyBboxPatch((6.7, 2.35), 1.7, 2.3, boxstyle="round,pad=0.02,rounding_size=0.05",
                                fc="#E7A19A", ec=OCC, lw=1.2, zorder=3))
    ax.text(7.55, 4.85, "后景楼", fontsize=14, color=OCC, ha="center")
    # anchors: green on the visible face, red on the back building, gray outside the frustum
    for x, y in ((3.35, 2.5), (3.35, 3.15), (3.35, 3.8), (3.7, 2.7), (3.7, 3.5)):
        ax.add_patch(Circle((x, y), 0.13, fc=VIS, ec="white", lw=0.5, zorder=4))
    for x, y in ((6.95, 2.7), (6.95, 3.3), (6.95, 3.95), (7.4, 2.9), (7.4, 3.6), (7.9, 3.2)):
        ax.add_patch(Circle((x, y), 0.13, fc=OCC, ec="white", lw=0.5, zorder=4))
    for x, y in ((2.2, 6.3), (4.5, 6.4), (8.4, 6.55), (2.4, 0.55), (5.2, 0.4), (8.6, 0.45)):
        ax.add_patch(Circle((x, y), 0.12, fc=IDLE, ec="white", lw=0.4, zorder=4))
    ax.text(7.55, 1.55, "过了 LOD，但被挡住", fontsize=13, color=OCC, ha="center")
    # legend
    ax.add_patch(Circle((0.4, 0.15), 0.12, fc=VIS, zorder=4))
    ax.text(0.7, 0.15, "可见", fontsize=13, color=EDGE, va="center")
    ax.add_patch(Circle((2.2, 0.15), 0.12, fc=OCC, zorder=4))
    ax.text(2.5, 0.15, "被挡住", fontsize=13, color=EDGE, va="center")
    ax.add_patch(Circle((4.5, 0.15), 0.12, fc=IDLE, zorder=4))
    ax.text(4.8, 0.15, "视锥外", fontsize=13, color=EDGE, va="center")
    save_fig(fig, "d_occlusion")


# ---------------------------------------------------------------- d_depth_test  (side view)
def fig_depth_test():
    fig, ax = plt.subplots(figsize=(6.15, 2.55))
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-0.3, 10.5)
    ax.set_ylim(-0.85, 3.15)
    # ray
    arrow(ax, (0.2, 1.35), (9.8, 1.35), color=NAVY, lw=1.5, ms=12, z=2)
    ax.add_patch(FancyBboxPatch((0.0, 1.05), 0.7, 0.6, boxstyle="round,pad=0.02,rounding_size=0.06", fc=NAVY, zorder=4))
    ax.text(0.35, 0.7, "相机", fontsize=13, color=NAVY, ha="center")
    # proxy surface
    ax.plot([4.15, 4.15], [0.25, 2.55], color=EDGE, lw=2.0, zorder=3)
    ax.text(4.15, 2.7, r"$z_{\mathrm{proxy}}$", fontsize=14, color=NAVY, ha="center")
    # gamma band
    ax.add_patch(Rectangle((4.15, 0.25), 1.35, 2.3, fc="#FDEDE8", ec="none", zorder=1))
    ax.plot([5.5, 5.5], [0.25, 2.55], color=OCC, lw=1.2, ls="--", zorder=3)
    ax.annotate("", xy=(5.5, 0.45), xytext=(4.15, 0.45),
                arrowprops=dict(arrowstyle="<->", color=OCC, lw=1.1))
    ax.text(4.82, 0.05, r"$\gamma$", fontsize=14, color=OCC, ha="center")
    # anchors
    ax.add_patch(Circle((3.15, 1.35), 0.16, fc=VIS, ec="white", lw=0.6, zorder=5))
    ax.text(3.15, 1.75, "保留", fontsize=13, color=VIS, ha="center", fontweight="bold")
    ax.add_patch(Circle((7.3, 1.35), 0.16, fc=OCC, ec="white", lw=0.6, zorder=5))
    ax.text(7.3, 1.75, "跳过", fontsize=13, color=OCC, ha="center", fontweight="bold")
    # building hint behind the surface
    ax.add_patch(Rectangle((4.2, 0.55), 2.4, 1.7, fc=BUILD, ec=EDGE, lw=0.8, alpha=0.35, zorder=0))
    save_fig(fig, "d_depth_test")


# ---------------------------------------------------------------- d_densify
def fig_densify():
    fig, axes = plt.subplots(1, 2, figsize=(6.0, 4.35))
    for ax in axes:
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_xlim(-0.4, 6.6)
        ax.set_ylim(-0.85, 5.6)
        ax.add_patch(FancyBboxPatch((1.8, 0.8), 2.5, 3.3, boxstyle="round,pad=0.03,rounding_size=0.06",
                                    fc=BUILD, ec=EDGE, lw=1.1, zorder=2))
        # windows
        for i in range(2):
            for j in range(4):
                ax.add_patch(Rectangle((2.15 + i * 1.05, 1.15 + j * 0.7), 0.55, 0.4, fc=WIN, ec="none", zorder=3))
        ax.add_patch(FancyBboxPatch((0.05, 2.3), 0.7, 0.45, boxstyle="round,pad=0.02,rounding_size=0.05", fc=NAVY, zorder=4))
        ax.add_patch(Polygon([[0.75, 2.4], [1.1, 2.25], [1.1, 2.8], [0.75, 2.65]], fc=NAVY, zorder=4))

    ax = axes[0]
    ax.set_title("原 growing", fontsize=15, color=OCC, fontweight="bold", pad=2)
    # anchors behind the building that fail the depth test
    for x, y in ((4.7, 1.5), (5.15, 2.3), (4.85, 3.2), (5.4, 3.7)):
        ax.plot(x, y, marker="x", ms=11, mew=2.2, color=OCC, zorder=5)
    ax.text(5.15, -0.05, "长在楼后面\n过不了深度测试", fontsize=13, color=OCC, ha="center", va="top")

    ax = axes[1]
    ax.set_title("proxy-guided", fontsize=15, color=VIS, fontweight="bold", pad=2)
    # error pixels back-project onto the surface
    for y in (1.4, 2.2, 3.0, 3.6):
        ax.plot([1.05, 1.85], [2.55, y], color="#F4A261", lw=1.0, ls="--", zorder=1)
        ax.add_patch(Circle((1.95, y), 0.13, fc=VIS, ec="white", lw=0.5, zorder=5))
    ax.text(4.85, -0.05, "误差像素反投影\n长在表面上", fontsize=13, color=VIS, ha="center", va="top")
    fig.tight_layout(w_pad=0.8)
    save_fig(fig, "d_densify")


if __name__ == "__main__":
    convert_paper_figs()
    A.formulas(FORMULAS)
    fig_gs_blend()
    fig_building3()
    fig_vanilla_vs_struct()
    fig_view_ellipse()
    fig_anchor_spawn()
    fig_octree_levels()
    A.crop_frac("d_octree_levels", "d_octree_one", (0, 0, 0.345, 1))
    fig_lod_curve()
    fig_occlusion()
    fig_depth_test()
    fig_densify()
    A.report()
