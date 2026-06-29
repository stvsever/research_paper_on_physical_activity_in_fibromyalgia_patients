"""Network drawing helpers (matplotlib) shared by the figure scripts.

Draws psychological networks in the qgraph idiom: nodes on a circle, edges colored by
sign (blue positive, red negative) and scaled by absolute weight. Directed (temporal)
networks use curved arrows and self-loops for autoregressive effects; undirected
(contemporaneous / between-person) networks use straight chords. Non-significant edges are
faded rather than removed, so the reader can see the full estimated structure.
"""
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Circle

import vizstyle as vs


def _circle_positions(nodes, radius=1.0):
    n = len(nodes)
    ang = np.linspace(np.pi / 2, np.pi / 2 + 2 * np.pi, n, endpoint=False)
    return {nd: (radius * np.cos(a), radius * np.sin(a)) for nd, a in zip(nodes, ang)}


def draw_network(ax, nodes, edges, directed=True, title="", node_radius=0.30,
                 max_lw=7.0, weight_ref=None, label_fontsize=10, sig_col="P",
                 sig_thresh=0.05, show_selfloops=True, min_draw=0.0, edge_color=None,
                 edge_cmap=None):
    """Draw a network on ``ax``.

    nodes : list of node keys (matched to vizstyle colors/labels).
    edges : list of dicts with keys from/to (or node1/node2), weight, and optionally P.
    """
    pos = _circle_positions(nodes)
    if weight_ref is None:
        weight_ref = max([abs(e["weight"]) for e in edges] + [1e-6])

    def lw(w):
        return 0.8 + max_lw * (abs(w) / weight_ref)

    # edges first (under nodes)
    for e in edges:
        a = e.get("from", e.get("node1"))
        b = e.get("to", e.get("node2"))
        w = e["weight"]
        if abs(w) < min_draw:
            continue
        sig = (e.get(sig_col, 0.0) <= sig_thresh) if sig_col in e else True
        if edge_cmap is not None:
            col = edge_cmap(min(abs(w) / weight_ref, 1.0))   # same hue, saturation by value
        elif edge_color is not None:
            col = edge_color
        else:
            col = vs.EDGE_POS if w >= 0 else vs.EDGE_NEG
        alpha = 0.95 if sig else 0.22
        if a == b:
            if not (directed and show_selfloops):
                continue
            _self_loop(ax, pos[a], node_radius, col, lw(w), alpha)
            continue
        x1, y1 = pos[a]
        x2, y2 = pos[b]
        # shorten to node edges
        dx, dy = x2 - x1, y2 - y1
        d = np.hypot(dx, dy)
        ux, uy = dx / d, dy / d
        sx, sy = x1 + ux * node_radius, y1 + uy * node_radius
        ex, ey = x2 - ux * node_radius, y2 - uy * node_radius
        if directed:
            rad = 0.18
            arrow = FancyArrowPatch(
                (sx, sy), (ex, ey), connectionstyle=f"arc3,rad={rad}",
                arrowstyle="-|>", mutation_scale=12 + lw(w) * 1.4,
                lw=lw(w), color=col, alpha=alpha, zorder=1,
                shrinkA=0, shrinkB=0)
            ax.add_patch(arrow)
        else:
            ax.plot([sx, ex], [sy, ey], color=col, lw=lw(w), alpha=alpha, zorder=1,
                    solid_capstyle="round")

    # nodes
    for nd in nodes:
        x, y = pos[nd]
        c = Circle((x, y), node_radius, facecolor=vs.node_color(nd),
                   edgecolor="white", lw=2.0, zorder=3)
        ax.add_patch(c)
        ax.text(x, y, vs.node_label(nd), ha="center", va="center",
                fontsize=label_fontsize, fontweight="bold", color="white", zorder=4)

    # Dynamic, symmetric limits so the outward self-loops always fit on the axes.
    loop_reach = max((node_radius * 1.9) if (directed and show_selfloops) else 0.0, 0.0)
    lim = 1.0 + node_radius + loop_reach + 0.12
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect("equal")
    ax.axis("off")
    if title:
        ax.set_title(title, pad=10)


def _self_loop(ax, center, node_radius, col, lw, alpha):
    """Draw an autoregressive self-loop as an outward arc with an arrowhead, fully
    outside the node and within the (expanded) axis limits."""
    x, y = center
    d = np.hypot(x, y) or 1.0
    ox, oy = x / d, y / d                      # outward radial unit vector
    px, py = -oy, ox                            # tangential unit vector
    loop_r = node_radius * 0.62
    # loop centre sits just outside the node, radially outward
    cx = x + ox * (node_radius + loop_r * 0.78)
    cy = y + oy * (node_radius + loop_r * 0.78)
    # draw the loop as an arc (open near the node so it reads as a loop)
    theta = np.linspace(-2.35, 2.35, 60)        # leave a small gap toward the node
    base = np.arctan2(cy - y, cx - x)           # orientation away from node
    ax_pts = cx + loop_r * np.cos(theta + base)
    ay_pts = cy + loop_r * np.sin(theta + base)
    ax.plot(ax_pts, ay_pts, color=col, lw=lw, alpha=alpha, zorder=1,
            solid_capstyle="round")
    # arrowhead at the end of the arc, pointing back toward the node
    ex, ey = ax_pts[-1], ay_pts[-1]
    ex2, ey2 = ax_pts[-3], ay_pts[-3]
    ax.add_patch(FancyArrowPatch((ex2, ey2), (ex, ey), arrowstyle="-|>",
                 mutation_scale=9 + lw * 1.2, color=col, alpha=alpha,
                 shrinkA=0, shrinkB=0, zorder=1))
