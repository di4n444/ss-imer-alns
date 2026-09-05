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


def choke_point_figure(path):
    """Why removing edges one at a time can miss the answer.

    The smallest graph on which the effect is visible: two independent gateways out of the
    source that rejoin at a single downstream edge. Cutting either gateway alone leaves the
    reach untouched, so a method that scores edges individually sees nothing worth taking —
    while one cut further out does the whole job. This is the non-submodularity argued in
    3.3 and the motivation for searching beyond the source's own edges (5.2.4)."""
    pos = {
        "s": (0.0, 0.0), "a": (1.0, 0.7), "b": (1.0, -0.7), "c": (2.0, 0.0),
        "h": (2.9, 0.0), "d": (3.9, 0.62), "e": (3.9, 0.0), "f": (3.9, -0.62),
    }
    edges = [("s", "a"), ("s", "b"), ("a", "c"), ("b", "c"), ("c", "h"),
             ("h", "d"), ("h", "e"), ("h", "f")]

    panels = [
        ("a) izvorna mreža", set(), set(pos)),
        ("b) uklonjen jedan brid uz izvor (k = 1)", {("s", "a")},
         {"s", "b", "c", "h", "d", "e", "f"}),
        ("c) uklonjen brid u uskom grlu (k = 1)", {("c", "h")},
         {"s", "a", "b", "c"}),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.6))
    for ax, (title, cut, reached) in zip(axes, panels):
        for u, w in edges:
            is_cut = (u, w) in cut
            _arrow(ax, pos[u], pos[w],
                   colour=HIGHLIGHT if is_cut else INK,
                   style=(0, (3, 3)) if is_cut else "-",
                   width=1.4 if is_cut else 1.2)
        for name, xy in pos.items():
            _node(ax, xy, name, filled=name in reached, source=(name == "s"))

        ax.add_patch(plt.Rectangle((3.62, -1.0), 0.56, 2.0, fill=False,
                                   edgecolor=MUTED, linewidth=0.9,
                                   linestyle=(0, (2, 2)), zorder=1))
        ax.text(3.90, 1.06, "gusto povezana\nregija", ha="center", va="bottom",
                fontsize=7.5, color="#666666")
        ax.text(1.9, -1.35, f"doseg = {len(reached)}", ha="center", fontsize=8.5,
                color=HIGHLIGHT if cut else INK)

        ax.set_title(title, **FONT)
        ax.set_xlim(-0.45, 4.45)
        ax.set_ylim(-1.6, 1.5)
        ax.set_aspect("equal")
        ax.axis("off")

    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path


def alns_loop_figure(path):
    """One ALNS iteration, and what the adaptive layer does around it.

    The point the picture has to carry is that three independent choices are made per
    iteration — which destroy operator, which repair criterion, which hop layer — and that
    all three are fed by the same reward, booked at the end of the iteration and turned
    into weights only at the end of a segment."""
    fig, ax = plt.subplots(figsize=(10.6, 4.8))

    def box(x, y, w, h, label, sub=None, fill="white"):
        ax.add_patch(plt.Rectangle((x - w / 2, y - h / 2), w, h, facecolor=fill,
                                   edgecolor=INK, linewidth=1.2, zorder=3))
        ax.text(x, y + (0.10 if sub else 0), label, ha="center", va="center",
                fontsize=8.5, zorder=4)
        if sub:
            ax.text(x, y - 0.26, sub, ha="center", va="center", fontsize=7,
                    color="#555555", zorder=4)

    def line(points, colour=INK, style="-", width=1.1, arrow=True):
        """A routed polyline: straight segments, with the arrowhead only on the last."""
        for a, b in zip(points, points[1:]):
            last = b is points[-1]
            ax.annotate("", xy=b, xytext=a,
                        arrowprops={"arrowstyle": "-|>" if (arrow and last) else "-",
                                    "linewidth": width, "color": colour,
                                    "linestyle": style, "shrinkA": 0, "shrinkB": 0})

    xs = [1.0, 3.4, 5.8, 8.2]
    labels = ["razori\nq bridova", "popravi\nq bridova", "procijeni\ndoseg", "prihvati?"]
    for x, label in zip(xs, labels):
        box(x, 2.30, 1.55, 0.90, label)
    for x0, x1 in zip(xs, xs[1:]):
        line([(x0 + 0.78, 2.30), (x1 - 0.80, 2.30)])

    # next iteration: routed above the row rather than across it
    line([(8.2, 2.75), (8.2, 3.30), (1.0, 3.30), (1.0, 2.77)])
    ax.text(4.6, 3.42, "sljedeća iteracija", ha="center", fontsize=8, color=INK)

    wheels = [("kotač\nrazaranja", "3 operatora"),
              ("kotač\npopravljanja", "6 kriterija"),
              ("kotač\nslojeva", "hop 0–3")]
    for x, (label, sub) in zip(xs, wheels):
        box(x, 0.45, 1.75, 0.90, label, sub, fill=FILL)
        # selection goes up on the left of each column, reward comes down on the right
        line([(x - 0.30, 0.90), (x - 0.30, 1.83)], style=(0, (2, 2)), width=1.0)

    # one reward bus, dropping into every wheel: R&P score all mechanisms involved equally
    line([(8.2, 1.85), (8.2, 1.45), (1.0, 1.45)], colour=HIGHLIGHT, width=1.2,
         arrow=False)
    for x in xs[:3]:
        line([(x + 0.30, 1.45), (x + 0.30, 0.92)], colour=HIGHLIGHT, width=1.2)
    ax.text(6.6, 1.58, "nagrada σ₁ / σ₂ / σ₃", ha="center", fontsize=8.5,
            color=HIGHLIGHT)
    ax.text(9.55, 0.45, "na kraju segmenta\ntežine se osvježe", ha="center",
            va="center", fontsize=7.5, color=HIGHLIGHT)

    ax.set_xlim(-0.1, 10.9)
    ax.set_ylim(-0.15, 3.70)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path


def hop_layers_figure(path):
    """Hop layers around the source, and the size problem that comes with them.

    Drawn with each layer visibly larger than the last, because that growth is the whole
    difficulty: the layers the scope wheel chooses between differ by orders of magnitude,
    so the same rank-biased draw does not mean the same thing in each."""
    import numpy as np

    fig, ax = plt.subplots(figsize=(7.4, 4.6))

    rings = [(1.0, "hop 0"), (1.9, "hop 1"), (2.8, "hop 2"), (3.7, "hop 3")]
    for radius, label in rings:
        ax.add_patch(plt.Circle((0, 0), radius, fill=False, edgecolor=MUTED,
                                linewidth=1.0, linestyle=(0, (3, 3)), zorder=1))
        ax.text(0, radius - 0.17, label, ha="center", fontsize=8, color="#555555",
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.0}, zorder=2)

    rng = np.random.default_rng(3)
    # Illustrative, not measured: the point is the growth rate, and the real ratio between
    # the innermost and outermost layer is far steeper than a drawing can hold.
    counts = [4, 14, 38, 74]
    for ring, (radius, _) in enumerate(rings):
        inner = 0.12 if ring == 0 else rings[ring - 1][0]
        angles = rng.uniform(0, 2 * np.pi, counts[ring])
        radii = rng.uniform(inner + 0.15, radius - 0.15, counts[ring])
        ax.scatter(radii * np.cos(angles), radii * np.sin(angles), s=9,
                   facecolor=FILL if ring == 0 else "white", edgecolor=INK,
                   linewidth=0.6, zorder=3)

    ax.add_patch(plt.Circle((0, 0), 0.17, facecolor=FILL, edgecolor=HIGHLIGHT,
                            linewidth=1.8, zorder=4))
    ax.text(0, 0, "s", ha="center", va="center", fontsize=9, color=HIGHLIGHT,
            fontweight="bold", zorder=5)

    ax.text(0, -4.35, "svaki sljedeći sloj sadrži red veličine više kandidata",
            ha="center", fontsize=8.5, color=HIGHLIGHT)

    ax.set_xlim(-4.1, 4.1)
    ax.set_ylim(-4.65, 4.0)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path


def pipeline_figure(path):
    """What is computed once, what is computed per source, and what runs in the loop.

    The division is the whole design rule of the implementation, so the picture is
    organised by it rather than by module: everything above the dashed line is paid for
    once, everything below it is paid for on every iteration."""
    fig, ax = plt.subplots(figsize=(10.8, 5.0))

    def box(x, y, label, w=2.35, h=0.86, fill="white"):
        ax.add_patch(plt.Rectangle((x - w / 2, y - h / 2), w, h, facecolor=fill,
                                   edgecolor=INK, linewidth=1.2, zorder=3))
        ax.text(x, y, label, ha="center", va="center", fontsize=8.3, zorder=4)
        return (x, y, w, h)

    def link(a, b, side="h"):
        (xa, ya, wa, ha), (xb, yb, wb, hb) = a, b
        if side == "h":
            start, end = (xa + wa / 2, ya), (xb - wb / 2, yb)
        else:
            start, end = (xa, ya - ha / 2), (xb, yb + hb / 2)
        ax.annotate("", xy=end, xytext=start,
                    arrowprops={"arrowstyle": "-|>", "linewidth": 1.1, "color": INK,
                                "shrinkA": 1, "shrinkB": 1})

    raw = box(1.4, 4.15, "sirovi podaci\n(SNAP)")
    graph = box(4.3, 4.15, "graf G s\nvjerojatnostima")
    feats = box(7.5, 4.15, "globalna obilježja\nbridova")
    scen = box(4.3, 2.75, "zamrznute\nrealizacije (SAA, MC)")
    ctx = box(7.5, 2.75, "kontekst izvora\n(slojevi, međupoloženost)")

    link(raw, graph)
    link(graph, feats)
    link(graph, scen, "v")
    link(feats, ctx, "v")

    ax.plot([0.0, 10.9], [1.95, 1.95], color=MUTED, linewidth=1.0,
            linestyle=(0, (4, 3)), zorder=1)
    ax.text(0.05, 2.08, "računa se jednom", fontsize=7.5, color="#666666")
    ax.text(0.05, 1.68, "izvodi se u petlji", fontsize=7.5, color=HIGHLIGHT)

    evaluate = box(2.6, 1.05, "procjena dosega\n(obilazak realizacija)", fill=FILL)
    methods = box(5.9, 1.05, "pohlepne metode\ni ALNS", fill=FILL)
    results = box(9.1, 1.05, "rezultati\n(jedan redak po metodi)")

    link(evaluate, methods)
    link(methods, results)
    # the loop: methods ask the evaluator for a value and get one back
    # routed clear of both boxes as straight segments, so the return path reads as a loop
    # rather than as a line crossing the blocks it connects
    for start, end, head in (((5.9, 0.62), (5.9, 0.32), False),
                             ((5.9, 0.32), (2.6, 0.32), False),
                             ((2.6, 0.32), (2.6, 0.62), True)):
        ax.annotate("", xy=end, xytext=start,
                    arrowprops={"arrowstyle": "-|>" if head else "-",
                                "linewidth": 1.1, "color": HIGHLIGHT,
                                "shrinkA": 0, "shrinkB": 0})
    ax.text(4.25, 0.06, "svaki kandidatni rez", ha="center", fontsize=7.5,
            color=HIGHLIGHT)

    # what feeds the loop
    for src, x in ((scen, 2.6), (ctx, 5.9)):
        ax.annotate("", xy=(x, 1.50), xytext=(src[0], src[1] - src[3] / 2),
                    arrowprops={"arrowstyle": "-|>", "linewidth": 1.0, "color": INK,
                                "linestyle": (0, (2, 2)),
                                "connectionstyle": "arc3,rad=0.0",
                                "shrinkA": 2, "shrinkB": 2})

    ax.set_xlim(0.0, 10.9)
    ax.set_ylim(-0.15, 4.75)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path


def source_population_figure(path, profile_csv):
    """What the source population actually looks like.

    Two facts the sampling design turns on: reach is a smooth heavy-tailed continuum
    rather than two separated groups, and most nodes cannot serve as a source at all
    because a budget must stay below the out-degree."""
    import pandas as pd

    profile = pd.read_csv(profile_csv)
    usable = profile[profile.out_degree > 0]

    fig, (left, right) = plt.subplots(1, 2, figsize=(11.0, 3.8))

    ordered = usable.sigma0_saa.sort_values().to_numpy()
    share = [(i + 1) / len(ordered) for i in range(len(ordered))]
    left.plot(ordered, share, color=INK, linewidth=1.6)
    left.set_xscale("log")
    left.set_xlabel("očekivani doseg $\\sigma_0$ (logaritamska skala)", fontsize=9)
    left.set_ylabel("kumulativni udio izvora", fontsize=9)
    left.set_title("a) raspodjela dosega po izvorima", **FONT)
    left.grid(alpha=0.25, linewidth=0.6)
    left.axvline(400, color=HIGHLIGHT, linestyle=(0, (4, 3)), linewidth=1.2)
    left.text(430, 0.12, "zasićeni izvori", color=HIGHLIGHT, fontsize=8)

    bands = [(1, 4), (4, 10), (10, 20), (20, 50), (50, 10 ** 9)]
    labels = ["1–3", "4–9", "10–19", "20–49", "50+"]
    low, high = [], []
    for lo, hi in bands:
        sel = (usable.out_degree >= lo) & (usable.out_degree < hi)
        high.append(int((sel & (usable.sigma0_saa >= 400)).sum()))
        low.append(int((sel & (usable.sigma0_saa < 400)).sum()))
    right.bar(labels, low, color="#D8D8D8", edgecolor=INK, linewidth=0.7,
              label="$\\sigma_0 < 400$")
    right.bar(labels, high, bottom=low, color=FILL, edgecolor=INK, linewidth=0.7,
              label="$\\sigma_0 \\geq 400$")
    right.set_xlabel("izlazni stupanj izvora", fontsize=9)
    right.set_ylabel("broj čvorova", fontsize=9)
    right.set_title("b) izlazni stupanj i doseg", **FONT)
    right.legend(fontsize=8, frameon=False)
    right.grid(axis="y", alpha=0.25, linewidth=0.6)
    # the first band cannot support the smallest budget studied
    right.text(0, low[0] + high[0] + 40, "ne mogu biti izvor\nza k ≥ 3", ha="center",
               fontsize=8, color=HIGHLIGHT)
    right.set_ylim(0, max(a + b for a, b in zip(low, high)) * 1.28)

    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path


if __name__ == "__main__":
    from pathlib import Path
    out = Path(__file__).resolve().parent.parent / "figures"
    out.mkdir(exist_ok=True)
    data = Path(__file__).resolve().parent.parent / "data"
    print("wrote", live_edge_figure(out / "fig1_2_live_edge.png"))
    print("wrote", source_population_figure(out / "fig2_4_source_population.png",
                                            data / "source_profile.csv"))
    print("wrote", choke_point_figure(out / "fig3_1_choke_point.png"))
    print("wrote", alns_loop_figure(out / "fig5_1_alns_loop.png"))
    print("wrote", hop_layers_figure(out / "fig5_2_hop_layers.png"))
    print("wrote", pipeline_figure(out / "fig6_1_pipeline.png"))
