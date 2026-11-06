"""matplotlib helpers for self-drawn diagrams: Gaussian blobs, pseudo-3D blocks, cameras, arrows.

Diagram conventions: ax.axis("off"), equal aspect, transparent background, CJK labels 13-17 pt,
same color for the same concept on every slide (see design.md).
"""
from __future__ import annotations

import numpy as np
from matplotlib.patches import Ellipse, FancyArrowPatch, FancyBboxPatch, Polygon

from . import assets  # noqa: F401  (configures fonts)

NAVY = "#1F3A5F"
EDGE = "#5C677D"
BUILD = "#B0B7C3"   # neutral object (e.g. the running-example building)
WIN = "#E7EEF6"
VIS = "#2A9D8F"     # kept / visible / good
OCC = "#E63946"     # removed / occluded / bad
IDLE = "#C8CDD6"    # unselected / inactive
BLUE = "#3A86FF"
TEAL = "#2A9D8F"
ORANGE = "#F4A261"
GREY = "#8D99AE"


class View:
    """Orthographic view for pseudo-3D drawings with plain 2D patches."""

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


def ellipse_params(cov2):
    w, V = np.linalg.eigh(cov2)
    angle = np.degrees(np.arctan2(V[1, 1], V[0, 1]))
    return np.sqrt(np.maximum(w[1], 1e-12)), np.sqrt(np.maximum(w[0], 1e-12)), angle


def cov_wh(w, h, ang_deg):
    """2D covariance of an ellipse with full width w, height h, rotated ang_deg."""
    th = np.radians(ang_deg)
    R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
    return R @ np.diag([(w / 2) ** 2, (h / 2) ** 2]) @ R.T


def draw_blob(ax, c2, cov2, color, nsig=2.0, levels=8, layer_alpha=0.16, z=2, edge=True, highlight=True):
    """Gaussian splat: stacked translucent ellipses plus an optional soft highlight."""
    a, b, ang = ellipse_params(cov2)
    for k in range(levels):
        s = nsig * (1 - k / levels)
        ax.add_patch(Ellipse(c2, 2 * s * a, 2 * s * b, angle=ang, fc=color, ec="none", alpha=layer_alpha, zorder=z))
    if edge:
        ax.add_patch(Ellipse(c2, 2 * nsig * a, 2 * nsig * b, angle=ang, fc="none", ec=color, lw=1.4, alpha=0.9, zorder=z))
    if highlight:
        off = np.array([-0.35 * a * np.cos(np.radians(ang)), 0.35 * b]) * 0.8
        ax.add_patch(Ellipse(np.asarray(c2) + off, 0.7 * a, 0.45 * b, angle=ang, fc="white", ec="none", alpha=0.35, zorder=z))


def arrow(ax, p0, p1, color=NAVY, lw=1.6, style="-|>", ms=14, z=6, ls="-"):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=ms, color=color, lw=lw, zorder=z, linestyle=ls))


def shade(hexcolor, f):
    r, g, b = [int(hexcolor[i:i + 2], 16) for i in (1, 3, 5)]
    r, g, b = [max(0, min(255, int(c * f))) for c in (r, g, b)]
    return f"#{r:02X}{g:02X}{b:02X}"


def face(ax, view, pts, fc, ec=EDGE, lw=0.7, alpha=1, z=3):
    ax.add_patch(Polygon(view.p(pts), closed=True, fc=fc, ec=ec, lw=lw, alpha=alpha, zorder=z))


def windows_on(ax, view, origin, u, v, rows, cols, color=WIN, z=4, inset=0.22):
    o = np.asarray(origin, float)
    u, v = np.asarray(u, float), np.asarray(v, float)
    for i in range(cols):
        for j in range(rows):
            a0, a1 = (i + inset) / cols, (i + 1 - inset) / cols
            b0, b1 = (j + 0.28) / rows, (j + 1 - 0.22) / rows
            pts = [o + a0 * u + b0 * v, o + a1 * u + b0 * v, o + a1 * u + b1 * v, o + a0 * u + b1 * v]
            face(ax, view, pts, color, ec="none", lw=0, z=z)


def building_iso(ax, view, x, y, z, sx, sy, sz, color=BUILD, rows=4, cols=3, zorder=3, windows=True, win=WIN):
    """Axis-aligned block seen from the -x, -y quadrant."""
    face(ax, view, [(x, y, z), (x, y + sy, z), (x, y + sy, z + sz), (x, y, z + sz)], shade(color, 0.86), z=zorder)
    face(ax, view, [(x, y, z), (x + sx, y, z), (x + sx, y, z + sz), (x, y, z + sz)], color, z=zorder)
    face(ax, view, [(x, y, z + sz), (x + sx, y, z + sz), (x + sx, y + sy, z + sz), (x, y + sy, z + sz)],
         shade(color, 1.14), z=zorder)
    if windows and rows and cols:
        windows_on(ax, view, (x, y, z), (sx, 0, 0), (0, 0, sz), rows, cols, color=win, z=zorder + 0.2)


def camera_iso(ax, view, pos, scale=0.28, z=6):
    x, y, z0 = pos
    s = scale
    face(ax, view, [(x, y, z0), (x + s, y, z0), (x + s, y, z0 + 0.62 * s), (x, y, z0 + 0.62 * s)], NAVY, ec=NAVY, z=z)
    face(ax, view, [(x, y, z0), (x, y + 0.7 * s, z0), (x, y + 0.7 * s, z0 + 0.62 * s), (x, y, z0 + 0.62 * s)],
         shade(NAVY, 0.75), ec=NAVY, z=z)
    face(ax, view, [(x, y, z0 + 0.62 * s), (x + s, y, z0 + 0.62 * s), (x + s, y + 0.7 * s, z0 + 0.62 * s),
                    (x, y + 0.7 * s, z0 + 0.62 * s)], shade(NAVY, 1.3), ec=NAVY, z=z)
    face(ax, view, [
        (x + 0.2 * s, y, z0 + 0.16 * s), (x + 0.8 * s, y, z0 + 0.16 * s),
        (x + 0.95 * s, y - 0.28 * s, z0 + 0.08 * s), (x + 0.05 * s, y - 0.28 * s, z0 + 0.08 * s),
    ], shade(NAVY, 1.15), ec=NAVY, z=z)


def camera_2d(ax, x, y, label=None, w=0.62, h=0.42, color=NAVY, label_dy=0.42, size=13, facing="right"):
    """Flat camera glyph (body + lens) for top / side views."""
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06", fc=color, ec=color, zorder=5))
    if facing == "right":
        lens = [[x + w, y + 0.24 * h], [x + w + 0.33, y - 0.05 * h], [x + w + 0.33, y + 1.05 * h], [x + w, y + 0.76 * h]]
    else:
        lens = [[x, y + 0.24 * h], [x - 0.33, y - 0.05 * h], [x - 0.33, y + 1.05 * h], [x, y + 0.76 * h]]
    ax.add_patch(Polygon(lens, fc=color, zorder=5))
    if label:
        ax.text(x + w / 2, y - label_dy, label, fontsize=size, color=color, ha="center")


def panel(ax, title=None, size=15, color=NAVY):
    ax.set_aspect("equal")
    ax.axis("off")
    if title:
        ax.set_title(title, fontsize=size, color=color, fontweight="bold", pad=4)


def round_box(ax, x, y, w, h, text=None, fc="#F3F6FA", ec="#C9D3E3", color=NAVY, size=13, bold=False, z=3):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec=ec, lw=1.0, zorder=z))
    if text:
        ax.text(x + w / 2, y + h / 2, text, fontsize=size, color=color, ha="center", va="center",
                fontweight="bold" if bold else "normal", zorder=z + 1)
