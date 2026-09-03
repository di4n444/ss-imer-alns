"""Figures for thesis Chapters 1-2, generated from analyse_graph.py's output and a
fresh Bitcoin Alpha build. Standalone (not part of the ALNS pipeline / PLAN.md Phase 3),
since these only depend on Phase 1's topology analysis and the thesis text needed them
now. Output: figures/*.png.
"""

import random

import igraph as ig
import matplotlib.pyplot as plt
import numpy as np
import powerlaw

from config import ER_NULL_MODEL_SEED, FIGURES_DIR
from create_graph import build_graph

plt.rcParams.update({"font.size": 11, "figure.dpi": 150, "savefig.bbox": "tight"})


def _draw_graph(ax, g: ig.Graph, layout, title, node_color="#3b6fa0"):
    coords = np.array(g.layout(layout).coords)
    degrees = np.array(g.degree())
    sizes = 15 + 8 * (degrees - degrees.min()) / max(1, (degrees.max() - degrees.min()))
    for e in g.es:
        x = [coords[e.source, 0], coords[e.target, 0]]
        y = [coords[e.source, 1], coords[e.target, 1]]
        ax.plot(x, y, color="#b0b0b0", linewidth=0.6, zorder=1)
    ax.scatter(coords[:, 0], coords[:, 1], s=sizes**1.15, color=node_color, zorder=2,
               edgecolors="white", linewidths=0.4)
    ax.set_title(title, fontsize=11)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


def figure_1_er_ws_ba():
    """Chapter 1: small synthetic ER / WS / BA networks, same N, illustrating the
    homogeneous-vs-clustered-vs-hub-heavy structural distinction."""
    n = 40
    random.seed(ER_NULL_MODEL_SEED)

    er = ig.Graph.Erdos_Renyi(n=n, m=80, directed=False)
    ws = ig.Graph.Watts_Strogatz(dim=1, size=n, nei=2, p=0.05)
    ba = ig.Graph.Barabasi(n=n, m=2)

    fig, axes = plt.subplots(1, 3, figsize=(11, 4))
    _draw_graph(axes[0], er, "circle", "Erdős–Rényi\n(homogena distribucija stupnjeva)")
    _draw_graph(axes[1], ws, "circle", "Watts–Strogatz\n(malog svijeta, bez hubova)")
    _draw_graph(axes[2], ba, "fr", "Barabási–Albert\n(bez skale, s hubovima)")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig1_1_er_ws_ba.png")
    plt.close(fig)


def figure_2_degree_distribution(g: ig.Graph):
    """Chapter 2: out-degree CCDF on log-log scale with the CSN power-law fit overlaid."""
    degrees = [d for d in g.outdegree() if d > 0]
    fit = powerlaw.Fit(degrees, discrete=True, verbose=False)

    fig, ax = plt.subplots(figsize=(6, 5))
    fit.plot_ccdf(ax=ax, color="#3b6fa0", marker="o", markersize=3, linewidth=0,
                  label="Bitcoin Alpha (izlazni stupanj)")
    fit.power_law.plot_ccdf(ax=ax, color="#c0392b", linestyle="--",
                             label=f"power-law fit (γ={fit.power_law.alpha:.2f}, "
                                   f"x_min={fit.power_law.xmin:.0f})")
    ax.set_xlabel("stupanj k")
    ax.set_ylabel("P(K ≥ k)")
    ax.set_title("Distribucija izlaznog stupnja (CCDF, log-log)")
    ax.legend(fontsize=9)
    fig.savefig(FIGURES_DIR / "fig2_1_degree_distribution.png")
    plt.close(fig)


def figure_3_probability_histogram(g: ig.Graph):
    """Chapter 2: bar chart of the 10 discrete transmission-probability levels."""
    probs = np.array(g.es["probability"])
    values, counts = np.unique(np.round(probs, 4), return_counts=True)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar([f"{v:.3f}" for v in values], counts, color="#3b6fa0")
    ax.set_yscale("log")
    ax.set_xlabel("vjerojatnost prijenosa p")
    ax.set_ylabel("broj bridova (log skala)")
    ax.set_title("Raspodjela vjerojatnosti prijenosa p po bridovima")
    plt.xticks(rotation=40, ha="right")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig2_2_probability_distribution.png")
    plt.close(fig)


def figure_4_bowtie(g: ig.Graph):
    """Chapter 2: literal bow-tie shape - IN and OUT as triangular wings pointing into
    the SCC circle (like a real bow tie: |>o<|), periphery as a small satellite circle.

    Sized by sqrt(count) (area proportional to size, standard convention) with only a
    small minimum-size floor - Bitcoin Alpha's SCC is so dominant (86.7%) that a fully
    proportional drawing would make IN/periphery invisible, but the floor here is small
    enough that the size difference between IN (1.3%) and OUT (11.6%) still reads
    clearly. Exact counts are always labeled regardless of drawn size.
    """
    import collections

    import matplotlib.patches as mpatches

    scc = g.connected_components(mode="strong")
    giant = set(max(scc, key=len))
    adj_out = g.get_adjlist(mode="out")
    adj_in = g.get_adjlist(mode="in")

    def bfs_multi(starts, adj):
        seen = set(starts)
        dq = collections.deque(starts)
        while dq:
            v = dq.popleft()
            for w in adj[v]:
                if w not in seen:
                    seen.add(w)
                    dq.append(w)
        return seen

    out_set = bfs_multi(giant, adj_out) - giant
    in_set = bfs_multi(giant, adj_in) - giant
    n = g.vcount()
    rest = n - len(giant) - len(out_set) - len(in_set)

    sizes = {"IN": len(in_set), "SCC": len(giant), "OUT": len(out_set), "periferija": rest}
    max_r = 1.7
    min_r = 0.12 * max_r  # small floor: keeps tiny slices visible without flattening the scale
    max_size = max(sizes.values())

    def radius(count):
        return min_r + (max_r - min_r) * (count / max_size) ** 0.5

    r_in, r_scc, r_out, r_rest = (radius(sizes[k]) for k in ["IN", "SCC", "OUT", "periferija"])

    fig, ax = plt.subplots(figsize=(9, 5))
    gap = 0.25
    x_scc = 0.0

    # IN wing: triangle apex touching SCC's left edge, base (wide side) further left.
    in_len = 2.1 * r_in
    x_in_apex = x_scc - r_scc - gap
    x_in_base = x_in_apex - in_len
    in_triangle = [(x_in_apex, 0), (x_in_base, r_in), (x_in_base, -r_in)]

    # OUT wing: mirrored - apex touching SCC's right edge, base further right.
    out_len = 2.1 * r_out
    x_out_apex = x_scc + r_scc + gap
    x_out_base = x_out_apex + out_len
    out_triangle = [(x_out_apex, 0), (x_out_base, r_out), (x_out_base, -r_out)]

    ax.add_patch(mpatches.Polygon(in_triangle, closed=True, color="#f2c14e",
                                   ec="white", lw=1.5, zorder=2))
    ax.add_patch(mpatches.Circle((x_scc, 0), r_scc, color="#3b6fa0",
                                  ec="white", lw=1.5, zorder=3))
    ax.add_patch(mpatches.Polygon(out_triangle, closed=True, color="#5fa8d3",
                                   ec="white", lw=1.5, zorder=2))

    y_rest = -(r_scc + r_rest + 0.8)
    ax.add_patch(mpatches.Circle((0, y_rest), r_rest, color="#b0b0b0",
                                  ec="white", lw=1.5, zorder=2))

    labels = [
        ((x_in_base + x_in_apex) / 2, 0, "IN", sizes["IN"], "black"),
        (x_scc, 0, "SCC\n(jezgra)", sizes["SCC"], "white"),
        ((x_out_apex + x_out_base) / 2, 0, "OUT", sizes["OUT"], "black"),
        (0, y_rest, "periferija", sizes["periferija"], "black"),
    ]
    for x, y, label, count, text_color in labels:
        pct = 100 * count / n
        ax.text(x, y, f"{label}\n{count} ({pct:.1f}%)", ha="center", va="center",
                fontsize=9, color=text_color, zorder=4)

    ax.set_xlim(x_in_base - 0.5, x_out_base + 0.5)
    ax.set_ylim(y_rest - r_rest - 0.5, max(r_scc, r_in, r_out) + 0.6)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Bow-Tie struktura mreže Bitcoin Alpha")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig2_3_bowtie.png")
    plt.close(fig)


if __name__ == "__main__":
    FIGURES_DIR.mkdir(exist_ok=True)
    figure_1_er_ws_ba()
    g = build_graph()
    figure_2_degree_distribution(g)
    figure_3_probability_histogram(g)
    figure_4_bowtie(g)
    print("wrote figures to", FIGURES_DIR)
