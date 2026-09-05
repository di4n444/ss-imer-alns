"""Conceptual figures for the theory and method chapters.

These are diagrams, not measurements: nothing here reads a result. Node positions are
written out by hand rather than produced by a layout algorithm, so the same picture comes
out every time and the panels of a multi-part figure stay aligned with each other.

Figures derived from data live with the analysis code instead; only explanatory drawings
belong here.
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

INK = "#222222"
MUTED = "#BBBBBB"
HIGHLIGHT = "#C0392B"
FILL = "#F2C9C2"
FONT = {"fontsize": 9}


def _arrow(ax, start, end, colour=INK, style="-", width=1.2, shrink=11):
    ax.add_patch(FancyArrowPatch(
        start, end, arrowstyle="-|>", mutation_scale=11, linewidth=width,
        linestyle=style, color=colour, shrinkA=shrink, shrinkB=shrink,
        joinstyle="round", capstyle="round"))


def _node(ax, xy, label, filled=False, source=False):
    face = FILL if filled else "white"
    edge = HIGHLIGHT if source else INK
    ax.add_patch(plt.Circle(xy, 0.16, facecolor=face, edgecolor=edge,
                            linewidth=1.8 if source else 1.1, zorder=3))
    ax.text(*xy, label, ha="center", va="center", zorder=4,
            fontsize=9, color=edge, fontweight="bold" if source else "normal")


def live_edge_figure(path):
    """How a stochastic cascade becomes a reachability count.

    Three panels on one small graph: the probabilities that label the edges, one
    realisation after the coin flips, and the set reachable from the source in it. This is
    the single conceptual step the whole estimation procedure rests on, so it is drawn
    once and referred back to."""
    pos = {
        "s": (0.0, 0.0), "a": (1.0, 0.75), "b": (1.0, -0.75),
        "c": (2.0, 0.75), "d": (2.0, -0.75), "e": (3.0, 0.0),
    }
    edges = [("s", "a", 0.9), ("s", "b", 0.3), ("a", "c", 0.8), ("b", "d", 0.7),
             ("c", "e", 0.6), ("d", "e", 0.5), ("a", "d", 0.4)]
    # One fixed realisation, chosen to show a blocked edge that still leaves a detour.
    live = {("s", "a"), ("a", "c"), ("c", "e"), ("a", "d")}
    reached = {"s", "a", "c", "e", "d"}

    titles = ["a) graf s vjerojatnostima prijenosa",
              "b) jedna live-edge realizacija",
              "c) skup dohvatljiv iz izvora"]
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.4))

    for panel, ax in enumerate(axes):
        for u, w, p in edges:
            is_live = (u, w) in live
            if panel == 0:
                _arrow(ax, pos[u], pos[w])
                mx, my = (pos[u][0] + pos[w][0]) / 2, (pos[u][1] + pos[w][1]) / 2
                ax.text(mx, my + 0.14, f"{p:.1f}", ha="center", va="center",
                        fontsize=8, color=INK,
                        bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.8})
            else:
                _arrow(ax, pos[u], pos[w],
                       colour=INK if is_live else MUTED,
                       style="-" if is_live else (0, (3, 3)),
                       width=1.6 if is_live else 0.9)

        for name, xy in pos.items():
            _node(ax, xy, name, filled=(panel == 2 and name in reached),
                  source=(name == "s"))

        ax.set_title(titles[panel], **FONT)
        ax.set_xlim(-0.45, 3.45)
        ax.set_ylim(-1.3, 1.3)
        ax.set_aspect("equal")
        ax.axis("off")

    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path


if __name__ == "__main__":
    from pathlib import Path
    out = Path(__file__).resolve().parent.parent / "figures"
    out.mkdir(exist_ok=True)
    print("wrote", live_edge_figure(out / "fig1_2_live_edge.png"))
