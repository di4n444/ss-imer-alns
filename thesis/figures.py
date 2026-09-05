"""Conceptual figures for the theory and method chapters.

These are diagrams, not measurements: nothing here reads a result. Node positions are
written out by hand rather than produced by a layout algorithm, so the same picture comes
out every time.

**Sizing.** A figure is placed into the document at `doc.figure`'s `width_cm` (14 cm by
default), so whatever Word has to shrink, it shrinks the lettering with it: a figure drawn
28 cm wide has its 9 pt labels rendered at 4.5 pt on paper. Every figure here is therefore
drawn at roughly its final printed width (`WIDTH_IN`) with body-sized type, so the scale
factor stays near 1 and the text stays readable on A4. Multi-panel comparisons are split
into separate figures rather than squeezed side by side, for the same reason.

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

# Printed width of a figure in the thesis, in inches: doc.figure places pictures at 14 cm.
# Drawing slightly wider than that leaves a little margin without shrinking the type much.
WIDTH_IN = 6.3

BODY = 11       # labels, node names, axis titles
SMALL = 9.5     # secondary annotations
TITLE = 11.5

plt.rcParams.update({
    "font.size": BODY,
    "axes.titlesize": TITLE,
    "axes.labelsize": BODY,
    "xtick.labelsize": SMALL,
    "ytick.labelsize": SMALL,
    "legend.fontsize": SMALL,
})


def _save(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return path


def _arrow(ax, start, end, colour=INK, style="-", width=1.4, shrink=13):
    ax.add_patch(FancyArrowPatch(
        start, end, arrowstyle="-|>", mutation_scale=13, linewidth=width,
        linestyle=style, color=colour, shrinkA=shrink, shrinkB=shrink,
        joinstyle="round", capstyle="round"))


def _node(ax, xy, label, filled=False, source=False, radius=0.19):
    face = FILL if filled else "white"
    edge = HIGHLIGHT if source else INK
    ax.add_patch(plt.Circle(xy, radius, facecolor=face, edgecolor=edge,
                            linewidth=2.0 if source else 1.3, zorder=3))
    ax.text(*xy, label, ha="center", va="center", zorder=4,
            fontsize=BODY, color=edge, fontweight="bold" if source else "normal")


# -- chapter 1 ---------------------------------------------------------------

def live_edge_figure(path):
    """How a stochastic cascade becomes a reachability count.

    Three panels on one small graph: the probabilities that label the edges, one
    realisation after the coin flips, and the set reachable from the source in it. Kept as
    one figure because the three panels are only meaningful next to each other, and it is
    drawn at its printed width so the panels are legible anyway."""
    pos = {
        "s": (0.0, 0.0), "a": (1.0, 0.75), "b": (1.0, -0.75),
        "c": (2.0, 0.75), "d": (2.0, -0.75), "e": (3.0, 0.0),
    }
    edges = [("s", "a", 0.9), ("s", "b", 0.3), ("a", "c", 0.8), ("b", "d", 0.7),
             ("c", "e", 0.6), ("d", "e", 0.5), ("a", "d", 0.4)]
    # One fixed realisation, chosen to show a blocked edge that still leaves a detour.
    live = {("s", "a"), ("a", "c"), ("c", "e"), ("a", "d")}
    reached = {"s", "a", "c", "e", "d"}

    titles = ["a) vjerojatnosti prijenosa", "b) jedna realizacija",
              "c) dohvatljivi skup"]
    fig, axes = plt.subplots(1, 3, figsize=(WIDTH_IN, WIDTH_IN * 0.40))

    for panel, ax in enumerate(axes):
        for u, w, p in edges:
            if panel == 0:
                _arrow(ax, pos[u], pos[w], width=1.1, shrink=9)
                mx, my = (pos[u][0] + pos[w][0]) / 2, (pos[u][1] + pos[w][1]) / 2
                ax.text(mx, my + 0.18, f"{p:.1f}".replace(".", ","), ha="center",
                        va="center", fontsize=7.5, color=INK,
                        bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.6})
            else:
                is_live = (u, w) in live
                _arrow(ax, pos[u], pos[w], width=1.4 if is_live else 0.8, shrink=9,
                       colour=INK if is_live else MUTED,
                       style="-" if is_live else (0, (2, 2)))

        for name, xy in pos.items():
            _node(ax, xy, name, filled=(panel == 2 and name in reached),
                  source=(name == "s"), radius=0.22)
            # the node label has to shrink with the panel, unlike a full-width figure
            ax.texts[-1].set_fontsize(8)

        ax.set_title(titles[panel], fontsize=8.5)
        ax.set_xlim(-0.42, 3.42)
        ax.set_ylim(-1.20, 1.20)
        ax.set_aspect("equal")
        ax.axis("off")

    return _save(fig, path)


# -- chapter 2 ---------------------------------------------------------------

def source_reach_figure(path, profile_csv):
    """How reach is distributed over the sources: a smooth continuum, not two groups."""
    import pandas as pd

    profile = pd.read_csv(profile_csv)
    usable = profile[profile.out_degree > 0]

    fig, ax = plt.subplots(figsize=(WIDTH_IN, WIDTH_IN * 0.58))
    ordered = usable.sigma0_saa.sort_values().to_numpy()
    share = [(i + 1) / len(ordered) for i in range(len(ordered))]
    ax.plot(ordered, share, color=INK, linewidth=2.0)
    ax.set_xscale("log")
    ax.set_xlabel("očekivani doseg $\\sigma_0$ (logaritamska skala)")
    ax.set_ylabel("kumulativni udio izvora")
    ax.grid(alpha=0.25, linewidth=0.7)
    ax.axvline(400, color=HIGHLIGHT, linestyle=(0, (4, 3)), linewidth=1.5)
    ax.text(440, 0.10, "zasićeni izvori", color=HIGHLIGHT, fontsize=SMALL)
    return _save(fig, path)


def source_outdegree_figure(path, profile_csv):
    """Out-degree against reach: most of the graph cannot serve as a source at all."""
    import pandas as pd

    profile = pd.read_csv(profile_csv)
    usable = profile[profile.out_degree > 0]

    fig, ax = plt.subplots(figsize=(WIDTH_IN, WIDTH_IN * 0.58))
    bands = [(1, 4), (4, 10), (10, 20), (20, 50), (50, 10 ** 9)]
    labels = ["1–3", "4–9", "10–19", "20–49", "50+"]
    low, high = [], []
    for lo, hi in bands:
        sel = (usable.out_degree >= lo) & (usable.out_degree < hi)
        high.append(int((sel & (usable.sigma0_saa >= 400)).sum()))
        low.append(int((sel & (usable.sigma0_saa < 400)).sum()))
    ax.bar(labels, low, color="#D8D8D8", edgecolor=INK, linewidth=0.9,
           label="$\\sigma_0 < 400$")
    ax.bar(labels, high, bottom=low, color=FILL, edgecolor=INK, linewidth=0.9,
           label="$\\sigma_0 \\geq 400$")
    ax.set_xlabel("izlazni stupanj izvora")
    ax.set_ylabel("broj čvorova")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.25, linewidth=0.7)
    ax.text(0, low[0] + high[0] + 55, "ne mogu biti izvor\nza k ≥ 3", ha="center",
            fontsize=SMALL, color=HIGHLIGHT)
    ax.set_ylim(0, max(a + b for a, b in zip(low, high)) * 1.30)
    return _save(fig, path)


# -- chapter 3 ---------------------------------------------------------------

CHOKE_POS = {
    "s": (0.0, 0.0), "a": (1.0, 0.7), "b": (1.0, -0.7), "c": (2.0, 0.0),
    "h": (2.9, 0.0), "d": (3.9, 0.62), "e": (3.9, 0.0), "f": (3.9, -0.62),
}
CHOKE_EDGES = [("s", "a"), ("s", "b"), ("a", "c"), ("b", "c"), ("c", "h"),
               ("h", "d"), ("h", "e"), ("h", "f")]

CHOKE_PANELS = {
    "base": (set(), set(CHOKE_POS)),
    "near": ({("s", "a")}, {"s", "b", "c", "h", "d", "e", "f"}),
    "choke": ({("c", "h")}, {"s", "a", "b", "c"}),
}


def choke_point_figure(path, panel):
    """One panel of the redundancy example, drawn on its own.

    `panel` is "base", "near" (one edge cut at the source) or "choke" (one edge cut where
    the two paths rejoin). Same budget, very different result: this is the
    non-submodularity of 3.3 and the reason the search may not stop at the source."""
    cut, reached = CHOKE_PANELS[panel]

    fig, ax = plt.subplots(figsize=(WIDTH_IN, WIDTH_IN * 0.50))
    for u, w in CHOKE_EDGES:
        is_cut = (u, w) in cut
        _arrow(ax, CHOKE_POS[u], CHOKE_POS[w],
               colour=HIGHLIGHT if is_cut else INK,
               style=(0, (3, 3)) if is_cut else "-",
               width=1.8 if is_cut else 1.4)
    for name, xy in CHOKE_POS.items():
        _node(ax, xy, name, filled=name in reached, source=(name == "s"))

    ax.add_patch(plt.Rectangle((3.60, -1.00), 0.60, 2.00, fill=False,
                               edgecolor=MUTED, linewidth=1.1,
                               linestyle=(0, (2, 2)), zorder=1))
    ax.text(3.90, 1.04, "gusto povezana regija", ha="center", va="bottom",
            fontsize=SMALL, color="#555555")
    ax.text(0.9, -1.22, f"doseg = {len(reached)}", ha="center", fontsize=BODY,
            color=HIGHLIGHT if cut else INK)

    ax.set_xlim(-0.4, 4.4)
    ax.set_ylim(-1.45, 1.35)
    ax.set_aspect("equal")
    ax.axis("off")
    return _save(fig, path)


# -- chapter 5 ---------------------------------------------------------------

def alns_loop_figure(path):
    """One ALNS iteration, and what the adaptive layer does around it.

    The picture has to carry that three choices are made independently per iteration -
    destroy operator, repair criterion, hop layer - and that all three are fed by the same
    reward, booked at the end of the iteration and turned into weights only at the end of
    a segment."""
    fig, ax = plt.subplots(figsize=(WIDTH_IN, WIDTH_IN * 0.62))

    def box(x, y, w, h, label, sub=None, fill="white"):
        ax.add_patch(plt.Rectangle((x - w / 2, y - h / 2), w, h, facecolor=fill,
                                   edgecolor=INK, linewidth=1.3, zorder=3))
        ax.text(x, y + (0.13 if sub else 0), label, ha="center", va="center",
                fontsize=BODY, zorder=4)
        if sub:
            ax.text(x, y - 0.30, sub, ha="center", va="center", fontsize=SMALL,
                    color="#555555", zorder=4)

    def line(points, colour=INK, style="-", width=1.3, arrow=True):
        """A routed polyline: straight segments, arrowhead only on the last."""
        for a, b in zip(points, points[1:]):
            last = b is points[-1]
            ax.annotate("", xy=b, xytext=a,
                        arrowprops={"arrowstyle": "-|>" if (arrow and last) else "-",
                                    "linewidth": width, "color": colour,
                                    "linestyle": style, "shrinkA": 0, "shrinkB": 0})

    xs = [1.15, 3.55, 5.95, 8.35]
    labels = ["razori\nq bridova", "popravi\nq bridova", "procijeni\ndoseg", "prihvati?"]
    for x, label in zip(xs, labels):
        box(x, 2.35, 1.95, 1.00, label)
    for x0, x1 in zip(xs, xs[1:]):
        line([(x0 + 0.99, 2.35), (x1 - 1.01, 2.35)])

    line([(8.35, 2.85), (8.35, 3.45), (1.15, 3.45), (1.15, 2.87)])
    ax.text(4.75, 3.58, "sljedeća iteracija", ha="center", fontsize=SMALL, color=INK)

    wheels = [("kotač\nrazaranja", "3 operatora"),
              ("kotač\npopravljanja", "6 kriterija"),
              ("kotač\nslojeva", "hop 0–3")]
    for x, (label, sub) in zip(xs, wheels):
        box(x, 0.50, 2.10, 1.00, label, sub, fill=FILL)
        line([(x - 0.34, 1.00), (x - 0.34, 1.83)], style=(0, (2, 2)), width=1.1)

    line([(8.35, 1.85), (8.35, 1.42), (1.15, 1.42)], colour=HIGHLIGHT, width=1.4,
         arrow=False)
    for x in xs[:3]:
        line([(x + 0.34, 1.42), (x + 0.34, 1.02)], colour=HIGHLIGHT, width=1.4)
    # below the bus rather than beside it: at this size the label would otherwise cross
    # the dashed selection arrow rising out of the third wheel
    ax.text(7.95, 1.20, "nagrada σ₁ / σ₂ / σ₃", ha="center", fontsize=SMALL,
            color=HIGHLIGHT)
    ax.text(9.72, 0.50, "na kraju\nsegmenta\ntežine se\nosvježe", ha="center",
            va="center", fontsize=SMALL, color=HIGHLIGHT)

    ax.set_xlim(-0.05, 10.6)
    ax.set_ylim(-0.10, 3.85)
    ax.axis("off")
    return _save(fig, path)


def hop_layers_figure(path):
    """Hop layers around the source, and the size problem that comes with them.

    Each layer is drawn visibly larger than the last, because that growth is the whole
    difficulty: the layers the scope wheel chooses between differ by orders of magnitude,
    so the same rank-biased draw does not mean the same thing in each."""
    import numpy as np

    fig, ax = plt.subplots(figsize=(WIDTH_IN, WIDTH_IN * 0.90))

    rings = [(1.0, "hop 0"), (1.9, "hop 1"), (2.8, "hop 2"), (3.7, "hop 3")]
    for radius, label in rings:
        ax.add_patch(plt.Circle((0, 0), radius, fill=False, edgecolor=MUTED,
                                linewidth=1.2, linestyle=(0, (3, 3)), zorder=1))
        ax.text(0, radius - 0.20, label, ha="center", fontsize=BODY, color="#444444",
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.5}, zorder=2)

    rng = np.random.default_rng(3)
    # Illustrative, not measured: the point is the growth rate, and the real ratio between
    # the innermost and outermost layer is far steeper than a drawing can hold.
    counts = [4, 14, 38, 74]
    for ring, (radius, _) in enumerate(rings):
        inner = 0.12 if ring == 0 else rings[ring - 1][0]
        angles = rng.uniform(0, 2 * np.pi, counts[ring])
        radii = rng.uniform(inner + 0.16, radius - 0.16, counts[ring])
        ax.scatter(radii * np.cos(angles), radii * np.sin(angles), s=16,
                   facecolor=FILL if ring == 0 else "white", edgecolor=INK,
                   linewidth=0.8, zorder=3)

    ax.add_patch(plt.Circle((0, 0), 0.20, facecolor=FILL, edgecolor=HIGHLIGHT,
                            linewidth=2.0, zorder=4))
    ax.text(0, 0, "s", ha="center", va="center", fontsize=BODY, color=HIGHLIGHT,
            fontweight="bold", zorder=5)

    ax.text(0, -4.30, "svaki sljedeći sloj sadrži red veličine više kandidata",
            ha="center", fontsize=BODY, color=HIGHLIGHT)

    ax.set_xlim(-4.0, 4.0)
    ax.set_ylim(-4.60, 3.95)
    ax.set_aspect("equal")
    ax.axis("off")
    return _save(fig, path)


# -- chapter 6 ---------------------------------------------------------------

def pipeline_figure(path):
    """What is computed once, what is computed per source, and what runs in the loop.

    The division is the design rule of the implementation, so the picture is organised by
    it rather than by module: above the dashed line is paid for once, below it on every
    iteration."""
    fig, ax = plt.subplots(figsize=(WIDTH_IN, WIDTH_IN * 0.72))

    def box(x, y, label, w=3.35, h=1.05, fill="white"):
        ax.add_patch(plt.Rectangle((x - w / 2, y - h / 2), w, h, facecolor=fill,
                                   edgecolor=INK, linewidth=1.3, zorder=3))
        ax.text(x, y, label, ha="center", va="center", fontsize=BODY, zorder=4)
        return (x, y, w, h)

    def link(a, b, side="h"):
        (xa, ya, wa, ha), (xb, yb, wb, hb) = a, b
        if side == "h":
            start, end = (xa + wa / 2, ya), (xb - wb / 2, yb)
        else:
            start, end = (xa, ya - ha / 2), (xb, yb + hb / 2)
        ax.annotate("", xy=end, xytext=start,
                    arrowprops={"arrowstyle": "-|>", "linewidth": 1.3, "color": INK,
                                "shrinkA": 1, "shrinkB": 1})

    raw = box(1.90, 5.05, "sirovi podaci\n(SNAP)")
    graph = box(5.35, 5.05, "graf G s\nvjerojatnostima")
    feats = box(9.20, 5.05, "globalna obilježja\nbridova")
    scen = box(5.35, 3.35, "zamrznute\nrealizacije")
    ctx = box(9.20, 3.35, "kontekst izvora")

    link(raw, graph)
    link(graph, feats)
    link(graph, scen, "v")
    link(feats, ctx, "v")

    ax.plot([0.0, 13.1], [2.42, 2.42], color=MUTED, linewidth=1.2,
            linestyle=(0, (4, 3)), zorder=1)
    ax.text(0.05, 2.56, "računa se jednom", fontsize=SMALL, color="#555555")
    ax.text(0.05, 2.10, "izvodi se u petlji", fontsize=SMALL, color=HIGHLIGHT)

    evaluate = box(3.10, 1.25, "procjena dosega", fill=FILL)
    methods = box(7.05, 1.25, "pohlepne metode\ni ALNS", fill=FILL)
    results = box(11.05, 1.25, "rezultati")

    link(evaluate, methods)
    link(methods, results)
    for start, end, head in (((7.05, 0.72), (7.05, 0.35), False),
                             ((7.05, 0.35), (3.10, 0.35), False),
                             ((3.10, 0.35), (3.10, 0.72), True)):
        ax.annotate("", xy=end, xytext=start,
                    arrowprops={"arrowstyle": "-|>" if head else "-",
                                "linewidth": 1.3, "color": HIGHLIGHT,
                                "shrinkA": 0, "shrinkB": 0})
    ax.text(5.05, 0.02, "svaki kandidatni rez", ha="center", fontsize=SMALL,
            color=HIGHLIGHT)

    for src, x in ((scen, 3.10), (ctx, 7.05)):
        ax.annotate("", xy=(x, 1.80), xytext=(src[0], src[1] - src[3] / 2),
                    arrowprops={"arrowstyle": "-|>", "linewidth": 1.1, "color": INK,
                                "linestyle": (0, (2, 2)), "shrinkA": 2, "shrinkB": 2})

    ax.set_xlim(0.0, 13.1)
    ax.set_ylim(-0.15, 5.75)
    ax.axis("off")
    return _save(fig, path)


if __name__ == "__main__":
    from pathlib import Path
    out = Path(__file__).resolve().parent.parent / "figures"
    out.mkdir(exist_ok=True)
    data = Path(__file__).resolve().parent.parent / "data"

    print("wrote", live_edge_figure(out / "fig1_2_live_edge.png"))
    print("wrote", source_reach_figure(out / "fig2_4_source_reach.png",
                                       data / "source_profile.csv"))
    print("wrote", source_outdegree_figure(out / "fig2_5_source_outdegree.png",
                                           data / "source_profile.csv"))
    for panel in ("base", "near", "choke"):
        print("wrote", choke_point_figure(out / f"fig3_{panel}_choke.png", panel))
    print("wrote", alns_loop_figure(out / "fig5_1_alns_loop.png"))
    print("wrote", hop_layers_figure(out / "fig5_2_hop_layers.png"))
    print("wrote", pipeline_figure(out / "fig6_1_pipeline.png"))
