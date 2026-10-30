"""Generate all image assets for the 3DGS slides: paper figures, formulas, diagrams."""
from pathlib import Path

import fitz
import matplotlib
import numpy as np
from PIL import Image, ImageChops

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.patches import Ellipse, FancyArrowPatch, Polygon, Rectangle  # noqa: E402

ROOT = Path(__file__).resolve().parent
PAPER = ROOT.parent / "arXiv-2308.04079v1"
OUT = ROOT / "assets"
OUT.mkdir(exist_ok=True)

font_manager.fontManager.addfont("/Library/Fonts/Arial Unicode.ttf")
plt.rcParams["font.family"] = "Arial Unicode MS"
plt.rcParams["mathtext.fontset"] = "cm"
plt.rcParams["axes.unicode_minus"] = False

RED, GREEN, BLUE = "#E63946", "#2A9D8F", "#3A86FF"
NAVY, GREY, ORANGE = "#1F3A5F", "#8D99AE", "#F4A261"


# ---------------------------------------------------------------- paper figures
def trim(img, pad=6):
    bg = Image.new(img.mode, img.size, (255, 255, 255))
    bbox = ImageChops.difference(img, bg).getbbox()
    if not bbox:
        return img
    l, t, r, b = bbox
    return img.crop((max(l - pad, 0), max(t - pad, 0), min(r + pad, img.width), min(b + pad, img.height)))


def convert_pdfs():
    pdfs = {
        "teaser": "figures/teaser/teaser_02.pdf",
        "overview": "figures/overview/overview_01.pdf",
        "density_control": "figures/density_control/density_control_01.pdf",
        "abl_7k_30k": "figures/ablations/7K_vs_30K.pdf",
        "abl_densification": "figures/ablations/densification.pdf",
        "abl_aniso": "figures/ablations/isotropy_vs_anisotropy2.pdf",
        "abl_random_sfm": "figures/ablations/random_vs_sfm2.pdf",
    }
    for name, rel in pdfs.items():
        doc = fitz.open(PAPER / rel)
        pix = doc[0].get_pixmap(dpi=260, alpha=False)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        trim(img).save(OUT / f"{name}.png")


# ---------------------------------------------------------------- formulas
FORMULAS = {
    "f_gauss": r"$G(\mathbf{x})=\exp\left(-\frac{1}{2}(\mathbf{x}-\mu)^{T}\,\Sigma^{-1}\,(\mathbf{x}-\mu)\right)$",
    "f_cov": r"$\Sigma = R\,S\,S^{T}R^{T}$",
    "f_proj": r"$\Sigma' = J\,W\,\Sigma\,W^{T}J^{T}$",
    "f_sh": r"$\mathbf{c}(\mathbf{d})=\sum_{\ell=0}^{3}\;\;\sum_{m=-\ell}^{\ell}\;\mathbf{h}_{\ell m}\,Y_{\ell m}(\mathbf{d})$",
    "f_alpha": r"$\tilde{\alpha}_i(\mathbf{p})=\alpha_i\cdot\exp\left(-\frac{1}{2}(\mathbf{p}-\mu_i')^{T}\,\Sigma_i'^{-1}\,(\mathbf{p}-\mu_i')\right)$",
    "f_blend": r"$C(\mathbf{p})=\sum_{i\in\mathcal{N}}\mathbf{c}_i\,\tilde{\alpha}_i\prod_{j=1}^{i-1}(1-\tilde{\alpha}_j)$",
    "f_nerf": r"$C=\sum_{i=1}^{N}T_i\,\alpha_i\,\mathbf{c}_i,\quad T_i=\prod_{j=1}^{i-1}(1-\alpha_j),\quad \alpha_i=1-e^{-\sigma_i\delta_i}$",
    "f_loss": r"$\mathcal{L}=(1-\lambda)\,\mathcal{L}_1+\lambda\,\mathcal{L}_{\mathrm{D\!-\!SSIM}},\quad\lambda=0.2$",
    "f_grad": r"$\frac{1}{|\mathcal{V}_i|}\sum_{k\in\mathcal{V}_i}\left\|\frac{\partial\mathcal{L}_k}{\partial \mu_i'}\right\|\;>\;\tau_{\mathrm{pos}}=0.0002$",
    "f_split": r"$\mathbf{s}_{\mathrm{child}}=\mathbf{s}_{\mathrm{parent}}\,/\,\phi,\quad\phi=1.6$",
    "f_psnr": r"$\mathrm{PSNR}=10\,\log_{10}\frac{\mathrm{MAX}^2}{\mathrm{MSE}}$",
    "f_ssim": r"$\mathrm{SSIM}=\frac{(2\mu_x\mu_y+C_1)(2\sigma_{xy}+C_2)}{(\mu_x^2+\mu_y^2+C_1)(\sigma_x^2+\sigma_y^2+C_2)}$",
    "f_lpips": r"$\mathrm{LPIPS}=\sum_{l}\frac{1}{H_lW_l}\sum_{h,w}\left\|\,w_l\odot(\hat{f}^{\,l}_{hw}(x)-\hat{f}^{\,l}_{hw}(y))\right\|_2^2$",
}


def render_formulas():
    for name, tex in FORMULAS.items():
        fig = plt.figure(figsize=(0.1, 0.1))
        fig.text(0, 0, tex, fontsize=30, color="#1B1B1B")
        fig.savefig(OUT / f"{name}.png", dpi=250, bbox_inches="tight", pad_inches=0.04, transparent=True)
        plt.close(fig)


# ---------------------------------------------------------------- 3D helpers
class View:
    """Orthographic view used to draw 3D illustrations with plain 2D patches."""

    def __init__(self, to_viewer):
        v = np.asarray(to_viewer, float)
        self.v = v / np.linalg.norm(v)
        f = -self.v
        r = np.cross(f, [0, 0, 1.0])
        r /= np.linalg.norm(r)
        u = np.cross(r, f)
        self.P = np.stack([r, u])

    def p(self, X):
        return np.asarray(X, float) @ self.P.T

    def depth(self, X):
        return np.asarray(X, float) @ self.v


def rot(ax_deg, ay_deg, az_deg):
    a, b, c = np.radians([ax_deg, ay_deg, az_deg])
    Rx = np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])
    Ry = np.array([[np.cos(b), 0, np.sin(b)], [0, 1, 0], [-np.sin(b), 0, np.cos(b)]])
    Rz = np.array([[np.cos(c), -np.sin(c), 0], [np.sin(c), np.cos(c), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def ellipse_params(cov2):
    w, V = np.linalg.eigh(cov2)
    angle = np.degrees(np.arctan2(V[1, 1], V[0, 1]))
    return np.sqrt(np.maximum(w[1], 1e-12)), np.sqrt(np.maximum(w[0], 1e-12)), angle


def draw_blob(ax, c2, cov2, color, nsig=2.0, levels=8, layer_alpha=0.16, z=2, edge=True, highlight=True):
    """Draw a Gaussian-looking blob: stacked translucent ellipses + soft highlight."""
    a, b, ang = ellipse_params(cov2)
    for k in range(levels):
        s = nsig * (1 - k / levels)
        ax.add_patch(Ellipse(c2, 2 * s * a, 2 * s * b, angle=ang, fc=color, ec="none", alpha=layer_alpha, zorder=z))
    if edge:
        ax.add_patch(Ellipse(c2, 2 * nsig * a, 2 * nsig * b, angle=ang, fc="none", ec=color, lw=1.4, alpha=0.9, zorder=z))
    if highlight:
        off = np.array([-0.35 * a * np.cos(np.radians(ang)), 0.35 * b]) * 0.8
        ax.add_patch(Ellipse(np.asarray(c2) + off, 0.7 * a, 0.45 * b, angle=ang, fc="white", ec="none", alpha=0.35, zorder=z))


def plane_poly(view, pts3):
    return view.p(np.asarray(pts3))


def ellipse_pts2d(mu, cov, nsig=2.0, n=80):
    a, b, ang = ellipse_params(cov)
    t = np.linspace(0, 2 * np.pi, n)
    th = np.radians(ang)
    R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
    pts = np.stack([nsig * a * np.cos(t), nsig * b * np.sin(t)], 1) @ R.T
    return pts + mu


def project_gaussian(c, Sigma, f):
    """EWA projection onto the image plane x = f (plane coords = (y, z))."""
    x, y, z = c
    mu = np.array([f * y / x, f * z / x])
    J = np.array([[-f * y / x**2, f / x, 0], [-f * z / x**2, 0, f / x]])
    return mu, J @ Sigma @ J.T


def arrow(ax, p0, p1, color=NAVY, lw=1.6, style="-|>", ms=14, z=6, ls="-"):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=ms, color=color, lw=lw, zorder=z, linestyle=ls))


# ---------------------------------------------------------------- diagram: pixel blending
F = 2.4
PLANE_Y, PLANE_Z = 1.5, 1.1
PIX = 0.25
PIX_C = np.array([0.125, 0.125])  # pixel centre in plane coords
GAUSS = [
    # (t along ray, offset, scales, rotation, color, label)
    (4.2, np.array([0.0, 0.05, -0.08]), (0.22, 0.6, 0.3), rot(10, 0, 30), RED, "G1 (近)"),
    (5.9, np.array([0.0, -0.18, 0.12]), (0.3, 0.38, 0.78), rot(0, 20, -20), GREEN, "G2"),
    (7.6, np.array([0.0, 0.22, 0.04]), (0.35, 0.9, 0.42), rot(-25, 0, 10), BLUE, "G3 (远)"),
]


def gaussians_world():
    ray_dir = np.array([F, PIX_C[0], PIX_C[1]]) / F
    out = []
    for t, off, s, R, col, lab in GAUSS:
        c = t * ray_dir + off
        Sigma = R @ np.diag(np.square(s)) @ R.T
        out.append((c, Sigma, col, lab, t * ray_dir))
    return out


def fig_pixel_blend_3d():
    view = View([-0.85, -1.0, 0.5])
    fig, ax = plt.subplots(figsize=(12, 6.2))
    ax.set_aspect("equal")
    ax.axis("off")

    cam = np.zeros(3)
    corners = [np.array([F, sy * PLANE_Y, sz * PLANE_Z]) for sy, sz in [(-1, -1), (1, -1), (1, 1), (-1, 1)]]
    items = []  # (depth, draw_fn)

    def draw_plane():
        ax.add_patch(Polygon(view.p(corners), closed=True, fc="#EEF3FA", ec=NAVY, lw=1.8, alpha=0.82, zorder=3))
        for y in np.arange(-PLANE_Y, PLANE_Y + 1e-6, PIX):
            ax.plot(*view.p([[F, y, -PLANE_Z], [F, y, PLANE_Z]]).T, color="#B8C4D6", lw=0.6, zorder=3)
        for z in np.arange(-PLANE_Z, PLANE_Z + 1e-6, PIX):
            ax.plot(*view.p([[F, -PLANE_Y, z], [F, PLANE_Y, z]]).T, color="#B8C4D6", lw=0.6, zorder=3)
        for c, Sigma, col, lab, _ in reversed(gaussians_world()):
            mu, cov = project_gaussian(c, Sigma, F)
            pts = ellipse_pts2d(mu, cov, nsig=2.0)
            p3 = np.stack([np.full(len(pts), F), pts[:, 0], pts[:, 1]], 1)
            ax.add_patch(Polygon(view.p(p3), closed=True, fc=col, ec=col, lw=1.4, alpha=0.38, zorder=3))
        px = [[F, PIX_C[0] + dy, PIX_C[1] + dz] for dy, dz in [(-.1, -.1), (.1, -.1), (.1, .1), (-.1, .1)]]
        ax.add_patch(Polygon(view.p(px), closed=True, fc="#FFD60A", ec="black", lw=2.0, zorder=3.5))

    items.append((view.depth([F, 0, 0]), draw_plane))
    for c, Sigma, col, lab, hit in gaussians_world():
        def draw_g(c=c, Sigma=Sigma, col=col):
            draw_blob(ax, view.p(c), view.P @ Sigma @ view.P.T, col, nsig=2.0, z=4)
        items.append((view.depth(c), draw_g))
    # painter's order: far from viewer first
    for zord, (_, fn) in enumerate(sorted(items, key=lambda it: it[0])):
        fn()

    # frustum
    for cr in corners:
        ax.plot(*view.p([cam, cr]).T, color=GREY, lw=1.0, ls="--", zorder=2)
    ax.plot(*view.p([cam]).T, "o", color=NAVY, ms=9, zorder=8)
    # ray through pixel
    dir_p = np.array([1, PIX_C[0] / F, PIX_C[1] / F])
    ray_end = 9.6 * dir_p
    ax.plot(*view.p([cam, ray_end]).T, color="black", lw=2.0, zorder=7)
    arrow(ax, view.p(8.9 * dir_p), view.p(ray_end), color="black", z=7)
    for i, (c, Sigma, col, lab, hit) in enumerate(gaussians_world()):
        ax.plot(*view.p([hit]).T, "o", color="white", mec="black", ms=8, zorder=9)
        tp = view.p(c) + np.array([0.0, [0.95, 1.3, 1.05][i]])
        ax.text(*tp, lab, color=col, fontsize=17, fontweight="bold", ha="center", zorder=10)

    ax.text(*(view.p(cam) + [-0.1, -0.45]), "相机中心", fontsize=15, ha="center", color=NAVY)
    ax.text(*(view.p(corners[0]) + [0.55, -0.45]), "图像平面（像素网格）", fontsize=15, ha="center", color=NAVY)
    pp = view.p([F, PIX_C[0], PIX_C[1]])
    ax.annotate("像素 p", xy=pp, xytext=pp + [-1.7, 1.2], fontsize=16, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color="black", lw=1.3), zorder=11)
    ax.text(*(view.p(ray_end) + [0.15, -0.35]), "穿过像素 p 的视线\n（按深度：近 → 远）", fontsize=14, color="black")
    ax.autoscale_view()
    xs, ys = ax.get_xlim(), ax.get_ylim()
    ax.set_xlim(xs[0] - 0.3, xs[1] + 0.3)
    ax.set_ylim(ys[0] - 0.3, ys[1] + 0.3)
    fig.savefig(OUT / "pixel_blend_3d.png", dpi=220, bbox_inches="tight", transparent=True)
    plt.close(fig)


def fig_pixel_blend_screen():
    fig, ax = plt.subplots(figsize=(5.4, 4.2))
    ax.set_aspect("equal")
    for y in np.arange(-PLANE_Y, PLANE_Y + 1e-6, PIX):
        ax.plot([y, y], [-PLANE_Z, PLANE_Z], color="#C9D3E3", lw=0.7, zorder=1)
    for z in np.arange(-PLANE_Z, PLANE_Z + 1e-6, PIX):
        ax.plot([-PLANE_Y, PLANE_Y], [z, z], color="#C9D3E3", lw=0.7, zorder=1)
    for c, Sigma, col, lab, _ in reversed(gaussians_world()):
        mu, cov = project_gaussian(c, Sigma, F)
        draw_blob(ax, mu, cov, col, nsig=2.0, layer_alpha=0.17, z=2, highlight=False)
        w, V = np.linalg.eigh(cov)
        tips = [mu + s * 2.25 * np.sqrt(w[1]) * V[:, 1] for s in (1, -1)]
        tip = max(tips, key=lambda t: np.linalg.norm(t - PIX_C) - 0.3 * abs(t[1]))
        ax.text(*tip, lab.split()[0], color=col, fontsize=14, fontweight="bold", ha="center", va="center", zorder=6,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
    ax.add_patch(Rectangle(PIX_C - PIX / 2, PIX, PIX, fc="none", ec="black", lw=2.6, zorder=7))
    ax.set_xlim(-PLANE_Y, PLANE_Y)
    ax.set_ylim(-PLANE_Z, PLANE_Z)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(NAVY)
        s.set_linewidth(1.8)
    fig.savefig(OUT / "pixel_blend_screen.png", dpi=220, bbox_inches="tight", transparent=True)
    plt.close(fig)


# ---------------------------------------------------------------- diagram: NeRF vs 3DGS
def fig_ray_vs_splat():
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
    for ax in axes:
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_xlim(-0.6, 10.2)
        ax.set_ylim(-2.6, 2.9)
        ax.add_patch(Polygon([[0, 0], [-0.5, 0.35], [-0.5, -0.35]], closed=True, fc=NAVY, zorder=5))
        ax.plot([1.2, 1.2], [-1.6, 1.6], color=NAVY, lw=3, zorder=5)
        ax.text(1.2, -2.0, "图像平面", ha="center", fontsize=13, color=NAVY)
    # left: NeRF
    ax = axes[0]
    ax.add_patch(Ellipse((6.5, 0.2), 2.6, 1.6, angle=15, fc="#CDE7E3", ec=GREEN, lw=1.5, zorder=1))
    ax.text(6.5, 0.2, "物体", ha="center", va="center", fontsize=13, color=GREEN, zorder=2)
    for ang in np.radians([-12, -4, 4, 12]):
        d = np.array([np.cos(ang), np.sin(ang)])
        ax.plot([0, 10 * d[0]], [0, 10 * d[1]], color=GREY, lw=0.9, zorder=2)
        for t in np.linspace(1.6, 9.8, 22):
            p = t * d
            inside = ((p[0] - 6.5) ** 2 / 1.3**2 + (p[1] - 0.2) ** 2 / 0.8**2) < 1.05
            ax.plot(*p, "o", ms=4.5, color=GREEN if inside else "#C8CDD6", zorder=3)
    ax.text(4.8, 2.35, "NeRF：每个像素发射射线，沿线密集采样\n大量样本落在空白区域，逐点查询 MLP",
            ha="center", fontsize=13.5, color="black")
    # right: 3DGS
    ax = axes[1]
    blobs = [((5.0, 0.9), 1.4, 0.5, 25, RED), ((6.6, -0.4), 1.6, 0.6, -35, GREEN), ((8.3, 0.4), 1.2, 0.7, 70, BLUE)]
    for (cx, cy), w, h, ang, col in blobs:
        th = np.radians(ang)
        R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
        cov = R @ np.diag([(w / 2) ** 2, (h / 2) ** 2]) @ R.T
        draw_blob(ax, (cx, cy), cov, col, nsig=2.0, z=2, layer_alpha=0.2)
        ty = 1.2 * cy / cx
        arrow(ax, (cx - 0.3, cy * (cx - 0.3) / cx), (1.25, ty), color=col, lw=1.6, z=4)
        ax.add_patch(Ellipse((1.2, ty), 0.16, 0.5 * h * 1.6 / cx * 2, fc=col, alpha=0.8, zorder=6))
    ax.text(4.8, 2.35, "3DGS：把显式椭球直接“投影/泼溅”到屏幕\n只处理真正存在的元素，适合 GPU 光栅化",
            ha="center", fontsize=13.5, color="black")
    fig.tight_layout()
    fig.savefig(OUT / "ray_vs_splat.png", dpi=220, bbox_inches="tight", transparent=True)
    plt.close(fig)


# ---------------------------------------------------------------- diagram: quality vs speed (Table 1)
def fig_quality_speed():
    data = [  # Mip-NeRF360 dataset, Table 1
        ("Plenoxels", 6.79, 23.08, "25m49s", GREY),
        ("INGP-Base", 11.7, 25.30, "5m37s", GREY),
        ("INGP-Big", 9.43, 25.59, "7m30s", GREY),
        ("Mip-NeRF360", 0.06, 27.69, "48h", ORANGE),
        ("Ours-7K", 160, 25.60, "6m25s", BLUE),
        ("Ours-30K", 134, 27.21, "41m33s", RED),
    ]
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    ax.set_xscale("log")
    ax.axvspan(30, 600, color="#E8F5E9", zorder=0)
    ax.text(70, 23.25, "实时区间\n(≥30 FPS)", fontsize=12, color="#2E7D32", ha="center")
    offs = {"Plenoxels": (8, -4), "INGP-Base": (-20, -24), "INGP-Big": (-38, 10), "Mip-NeRF360": (10, -4),
            "Ours-7K": (-30, -26), "Ours-30K": (-34, 10)}
    for name, fps, psnr, t, col in data:
        ax.scatter(fps, psnr, s=170, color=col, edgecolor="black", zorder=3)
        dx, dy = offs[name]
        ax.annotate(f"{name}\n训练 {t}", (fps, psnr), xytext=(dx, dy), textcoords="offset points",
                    fontsize=11, color="black" if col == GREY else col, fontweight="bold")
    ax.set_xlim(0.03, 600)
    ax.set_ylim(22.7, 28.4)
    ax.set_xlabel("渲染速度 FPS（对数坐标）", fontsize=13)
    ax.set_ylabel("PSNR (dB) ↑", fontsize=13)
    ax.grid(alpha=0.3, which="both")
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "quality_speed.png", dpi=220, transparent=True)
    plt.close(fig)


# ---------------------------------------------------------------- diagram: covariance decomposition
def fig_cov_decomp():
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.6))
    th = np.radians(35)
    R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
    S = np.diag([1.5, 0.5])
    covs = [np.eye(2) * 0.25, S @ S.T * 0.25, R @ S @ S.T @ R.T * 0.25]
    titles = ["单位球", "① S 缩放：三轴尺度 $s_x,s_y,s_z$", "② R 旋转：四元数 q → R"]
    for ax, cov, title, col in zip(axes, covs, titles, [GREY, GREEN, BLUE]):
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_xlim(-1.9, 1.9)
        ax.set_ylim(-1.5, 1.5)
        ax.axhline(0, color="#D0D5DD", lw=0.8)
        ax.axvline(0, color="#D0D5DD", lw=0.8)
        draw_blob(ax, (0, 0), cov, col, nsig=2.0, layer_alpha=0.18)
        w, V = np.linalg.eigh(cov)
        for k in range(2):
            v = V[:, k] * 2 * np.sqrt(w[k])
            arrow(ax, (0, 0), tuple(v), color="black", lw=1.4, ms=11)
        ax.set_title(title, fontsize=14, color=NAVY)
    fig.tight_layout()
    fig.savefig(OUT / "cov_decomp.png", dpi=220, bbox_inches="tight", transparent=True)
    plt.close(fig)


# ---------------------------------------------------------------- diagram: candidate primitives on a surface
def fig_primitives():
    surf = lambda x: 0.55 * np.sin(0.95 * x) + 0.08 * x  # noqa: E731
    slope = lambda x: 0.55 * 0.95 * np.cos(0.95 * x) + 0.08  # noqa: E731
    xs = np.linspace(0, 6.2, 300)
    fig, axes = plt.subplots(2, 2, figsize=(8.2, 4.3))
    panels = [
        ("点：无面积，表面留空洞", RED),
        ("带法向圆盘：稀疏点上法向估不准", RED),
        ("球形 Gaussian：平滑，但贴不住薄表面", ORANGE),
        ("各向异性 Gaussian：平滑且贴合表面", GREEN),
    ]
    rng = np.random.default_rng(3)
    for ax, (title, col) in zip(axes.flat, panels):
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_xlim(-0.3, 6.5)
        ax.set_ylim(-0.95, 1.05)
        ax.plot(xs, surf(xs), color="#B0B7C3", lw=7, solid_capstyle="round", zorder=1)
        ax.set_title(title, fontsize=14, color=col, fontweight="bold", pad=4)
    ax = axes[0, 0]
    px = np.array([0.2, 0.9, 1.3, 2.6, 3.1, 4.5, 5.0, 6.0])
    ax.plot(px, surf(px), "o", color="black", ms=6, zorder=3)
    for gx in (1.95, 3.8, 5.5):
        ax.text(gx, surf(gx) - 0.5, "空洞", fontsize=11, color=RED, ha="center")
    ax = axes[0, 1]
    for k, x in enumerate(np.linspace(0.4, 5.8, 6)):
        noise = rng.normal(0, 0.5) if k % 2 else rng.normal(0, 0.1)
        th = np.arctan(slope(x)) + noise
        t = np.array([np.cos(th), np.sin(th)])
        n = np.array([-t[1], t[0]])
        c = np.array([x, surf(x)])
        bad = abs(noise) > 0.25
        ax.plot(*np.stack([c - 0.38 * t, c + 0.38 * t]).T, color=RED if bad else NAVY, lw=4, zorder=3)
        arrow(ax, tuple(c), tuple(c + 0.55 * n), color=RED if bad else NAVY, lw=1.4, ms=10, z=4)
    ax = axes[1, 0]
    for x in np.linspace(0.2, 6.0, 10):
        draw_blob(ax, (x, surf(x)), np.eye(2) * 0.17**2, ORANGE, nsig=2.0, layer_alpha=0.2, z=3, highlight=False)
    ax = axes[1, 1]
    for x in np.linspace(0.3, 5.9, 7):
        th = np.arctan(slope(x))
        R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
        cov = R @ np.diag([0.25**2, 0.065**2]) @ R.T
        draw_blob(ax, (x, surf(x)), cov, GREEN, nsig=2.0, layer_alpha=0.3, z=3, highlight=False)
    fig.tight_layout(h_pad=1.2, w_pad=1.0)
    fig.savefig(OUT / "primitives.png", dpi=220, bbox_inches="tight", transparent=True)
    plt.close(fig)


# ---------------------------------------------------------------- diagram: one gaussian's parameters
def fig_gaussian_params():
    view = View([-0.6, -1.0, 0.5])
    fig, ax = plt.subplots(figsize=(6.0, 4.6))
    ax.set_aspect("equal")
    ax.axis("off")
    R = rot(15, -20, 35)
    s = np.array([1.5, 0.75, 0.5])
    Sigma = R @ np.diag(s**2) @ R.T
    c = np.zeros(3)
    draw_blob(ax, view.p(c), view.P @ Sigma @ view.P.T, BLUE, nsig=1.0, levels=9, layer_alpha=0.17, highlight=False)
    labels = ["$s_1$", "$s_2$", "$s_3$"]
    for k in range(3):
        tip = R[:, k] * s[k]
        arrow(ax, view.p(c), view.p(tip), color=[RED, GREEN, ORANGE][k], lw=2.2, ms=15, z=8)
        ax.text(*(view.p(tip * 1.18)), labels[k], fontsize=18, color=[RED, GREEN, ORANGE][k], ha="center", va="center", zorder=9)
    ax.plot(*view.p(c), "o", color="black", ms=7, zorder=9)
    ax.text(*(view.p(c) + [0.08, -0.22]), r"$\mu$", fontsize=20, zorder=9)
    ax.autoscale_view()
    ax.set_xlim(-1.9, 1.9)
    ax.set_ylim(-1.3, 1.3)
    fig.savefig(OUT / "gaussian_params.png", dpi=220, bbox_inches="tight", transparent=True)
    plt.close(fig)


# ---------------------------------------------------------------- diagram: 3D -> 2D projection
def fig_projection():
    view = View([-0.5, -1.0, 0.45])
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    ax.set_aspect("equal")
    ax.axis("off")
    f, PY, PZ = 1.6, 1.0, 0.75
    c = np.array([5.0, 0.35, 0.15])
    R = rot(20, 10, 40)
    Sigma = R @ np.diag(np.square([0.28, 0.7, 0.25])) @ R.T
    corners = [np.array([f, sy * PY, sz * PZ]) for sy, sz in [(-1, -1), (1, -1), (1, 1), (-1, 1)]]
    for cr in corners:
        ax.plot(*view.p([np.zeros(3), cr]).T, color=GREY, lw=1.0, ls="--", zorder=1)
    draw_blob(ax, view.p(c), view.P @ Sigma @ view.P.T, BLUE, nsig=2.0, z=2)
    ax.add_patch(Polygon(view.p(corners), closed=True, fc="#EEF3FA", ec=NAVY, lw=1.8, alpha=0.85, zorder=3))
    mu, cov = project_gaussian(c, Sigma, f)
    pts = ellipse_pts2d(mu, cov, 2.0)
    p3 = np.stack([np.full(len(pts), f), pts[:, 0], pts[:, 1]], 1)
    ax.add_patch(Polygon(view.p(p3), closed=True, fc=BLUE, ec=BLUE, alpha=0.5, lw=1.5, zorder=4))
    ax.plot(*view.p([np.zeros(3), c]).T, color="black", lw=1.0, ls=":", zorder=5)
    ax.plot(*view.p([np.zeros(3)]).T, "o", color=NAVY, ms=9, zorder=6)
    ax.text(*(view.p(np.zeros(3)) + [-0.1, -0.45]), "相机", fontsize=14, ha="center", color=NAVY)
    ax.text(*(view.p(c) + [0.0, 0.95]), "世界空间 3D Gaussian\n$\\Sigma$ : 3×3", fontsize=14, ha="center", color=BLUE)
    ax.text(*(view.p(corners[0]) + [0.4, -0.45]), "屏幕 2D 椭圆  $\\Sigma'$ : 2×2", fontsize=14, ha="center", color=NAVY)
    mid = view.p(0.68 * c) + [0.0, -0.3]
    ax.text(*mid, "投影：$J\\,W$", fontsize=13, ha="center", color="black")
    ax.autoscale_view()
    fig.savefig(OUT / "projection.png", dpi=220, bbox_inches="tight", transparent=True)
    plt.close(fig)


# ---------------------------------------------------------------- diagram: tiles
def fig_tiles():
    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    ax.set_aspect("equal")
    W, H, T = 8, 5, 1.0
    for i in range(W + 1):
        ax.plot([i, i], [0, H], color="#9AA8BD", lw=1.0)
    for j in range(H + 1):
        ax.plot([0, W], [j, j], color="#9AA8BD", lw=1.0)
    hl = [(2, 2), (3, 2), (2, 3), (3, 3)]
    for (i, j) in hl:
        ax.add_patch(Rectangle((i, j), T, T, fc="#FFE8A3", ec="#E0A800", lw=2, zorder=1))
    blobs = [((3.0, 3.05), 0.55, 0.30, 20, RED), ((6.5, 1.5), 0.2, 0.12, -40, GREEN),
             ((1.5, 0.5), 0.18, 0.14, 60, BLUE), ((5.5, 3.5), 0.22, 0.1, 10, ORANGE)]
    for (cx, cy), a, b, ang, col in blobs:
        th = np.radians(ang)
        R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
        cov = R @ np.diag([a**2, b**2]) @ R.T
        draw_blob(ax, (cx, cy), cov, col, nsig=2.0, layer_alpha=0.2, z=3, highlight=False)
    ax.text(2.95, 4.2, "跨 4 个 tile → 复制 4 个实例", fontsize=13, ha="center", color="#B8860B", fontweight="bold")
    ax.text(0.5, -0.45, "每个格子 = 16×16 像素的 tile", fontsize=12, color=NAVY, ha="left")
    ax.set_xlim(-0.1, W + 0.1)
    ax.set_ylim(-0.7, H + 0.6)
    ax.axis("off")
    fig.savefig(OUT / "tiles.png", dpi=220, bbox_inches="tight", transparent=True)
    plt.close(fig)


# ---------------------------------------------------------------- diagram: weights of the worked example
def fig_weights():
    alphas = [0.5, 0.4, 0.8]
    cols = [RED, GREEN, BLUE]
    T, ws = 1.0, []
    for a in alphas:
        ws.append(T * a)
        T *= 1 - a
    fig, ax = plt.subplots(figsize=(6.4, 1.6))
    left = 0
    for w, col, name in zip(ws + [T], cols + ["#D9D9D9"], ["G1", "G2", "G3", "背景"]):
        ax.barh(0, w, left=left, color=col, edgecolor="white", height=0.6)
        ax.text(left + w / 2, 0, f"{name}\n{w:.2f}", ha="center", va="center", fontsize=12,
                color="white" if name != "背景" else "black", fontweight="bold")
        left += w
    ax.set_xlim(0, 1)
    ax.axis("off")
    fig.savefig(OUT / "weights_bar.png", dpi=220, bbox_inches="tight", transparent=True)
    plt.close(fig)


# ---------------------------------------------------------------- dataset thumbnails / comparison grid
def copy_raster_figs():
    picks = {
        "ds_bicycle": "results2/bicycle/gt/DSC8824_s.png",
        "ds_garden": "results2/garden/gt/gt_001.png",
        "out_garden": "results2/garden/ours/DSC07964.png",
        "ds_room": "results2/room/gt/gt_0025_s.png",
        "ds_counter": "results2/counter/gt/DSCF6089_s.png",
        "ds_truck": "results2/truck/gt/000065_s.png",
        "ds_train": "results2/train/gt/gt_0008_s.png",
        "ds_playroom": "results2/playroom/gt/gt_014_s.png",
        "ds_drjohnson": "results2/drjohnson/gt/IMG_6366_s.png",
        "ficus": "figures/anisotropic/ficus.png",
        "aniso_real": "figures/anisotropic/real2.png",
        "limited_bw": "figures/ablations/images/30k/garden/limitedBW.png",
        "full_bw": "figures/ablations/images/30k/garden/full.png",
        "limit_mip": "results/limitations/color_009_s.png",
        "limit_ours": "results/limitations/00073_s.png",
        "extreme_mip": "figures/extremeviews/color_032_s.png",
        "extreme_ours": "figures/extremeviews/IMG_6589_s.png",
    }
    for name, rel in picks.items():
        Image.open(PAPER / rel).convert("RGB").save(OUT / f"{name}.png")


def comparison_grid():
    rows = [
        ("bicycle", ["gt/DSC8824_s.png", "ours/DSC8824_s.png", "mipnerf360/color_018_s.png",
                     "igp/out_DSC8824_s.jpg", "plenoxels/render_0018_s.png"]),
        ("garden", ["gt/gt_001.png", "ours/DSC07964.png", "mipnerf360/color_001.png",
                    "igp/out_DSC07964.JPG", "plenoxels/render_0001.png"]),
        ("room", ["gt/gt_0025_s.png", "ours/DSCF4867_s.png", "mipnerf360/color_025_s.png",
                  "igp/out_DSCF4867_s.jpg", "plenoxels/render_0025_s.png"]),
        ("truck", ["gt/000065_s.png", "ours/000065_s.png", "mipnerf360/color_008_s.png",
                   "igp/out_0008_s.png", "plenoxels/render_0008_s.png"]),
    ]
    cw, ch, gap = 520, 300, 8
    grid = Image.new("RGB", (5 * cw + 4 * gap, len(rows) * ch + (len(rows) - 1) * gap), "white")
    for r, (scene, files) in enumerate(rows):
        for c, f in enumerate(files):
            im = Image.open(PAPER / "results2" / scene / f).convert("RGB")
            scale = max(cw / im.width, ch / im.height)
            im = im.resize((int(im.width * scale + 0.5), int(im.height * scale + 0.5)), Image.LANCZOS)
            l, t = (im.width - cw) // 2, (im.height - ch) // 2
            grid.paste(im.crop((l, t, l + cw, t + ch)), (c * (cw + gap), r * (ch + gap)))
    grid.save(OUT / "comparison_grid.png")


if __name__ == "__main__":
    convert_pdfs()
    render_formulas()
    copy_raster_figs()
    comparison_grid()
    fig_pixel_blend_3d()
    fig_pixel_blend_screen()
    fig_ray_vs_splat()
    fig_quality_speed()
    fig_cov_decomp()
    fig_primitives()
    fig_gaussian_params()
    fig_projection()
    fig_tiles()
    fig_weights()
    print("assets ->", OUT)
