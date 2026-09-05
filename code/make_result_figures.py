"""Figures for thesis Chapter 7, generated from data/results.csv and
data/results_scaled.csv. Standalone, like make_topology_figures.py: it reads finished
measurements and draws them, and takes part in no pipeline.

Sizing follows thesis/figures.py rather than this file's older sibling: every figure is
drawn at its printed width (WIDTH_IN) with body-sized type, because doc.figure places
pictures at 14 cm and Word shrinks the lettering along with anything drawn wider.

Output: figures/fig7_*.png.
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from config import DATA_DIR, FIGURES_DIR
from results_analysis import (BANDS, MAIN_TAGS, comparison_table, load_results,
                              paired_scaled, prior_band)

# Printed width in inches; doc.figure places pictures at 14 cm.
WIDTH_IN = 6.3
BODY = 11
SMALL = 9.5

INK = "#222222"
MUTED = "#BBBBBB"
HIGHLIGHT = "#C0392B"
ACCENT = "#3b6fa0"

plt.rcParams.update({
    "font.size": BODY,
    "axes.titlesize": 11.5,
    "axes.labelsize": BODY,
    "xtick.labelsize": SMALL,
    "ytick.labelsize": SMALL,
    "legend.fontsize": SMALL,
    "figure.dpi": 150,
    "savefig.bbox": "tight",
})


def _save(fig, name):
    path = FIGURES_DIR / name
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)
    print("wrote", path)
    return path


def figure_saa_mc(results):
    """7.1: the in-sample estimate against the out-of-sample one, per ALNS cell.

    A point below the diagonal was optimistic in sample. The diagonal carries the whole
    argument, so it is drawn first and the points sit on top of it."""
    alns = results[(results.method == "alns") & results.tag.isin(MAIN_TAGS)]
    alns = alns.drop_duplicates(subset=["source", "k"])

    fig, ax = plt.subplots(figsize=(WIDTH_IN, WIDTH_IN * 0.72))
    ax.plot([0, 1], [0, 1], color=MUTED, linewidth=1.2, zorder=1)
    ax.scatter(alns.R_saa, alns.R_mc, s=26, facecolor=ACCENT, edgecolor="white",
               linewidth=0.5, alpha=0.85, zorder=3)

    worst = alns.loc[alns.saa_mc_gap.idxmax()]
    ax.annotate(f"izvor {int(worst.source)}, $k$ = {int(worst.k)}:\n"
                f"najveći zabilježeni raskorak",
                xy=(worst.R_saa, worst.R_mc), xytext=(0.06, 0.70),
                fontsize=SMALL, color=HIGHLIGHT, ha="left", va="center",
                arrowprops={"arrowstyle": "-", "color": HIGHLIGHT, "linewidth": 1.0,
                            "shrinkA": 4, "shrinkB": 6})

    ax.text(0.62, 0.30, "precijenjeno\nna uzorku", fontsize=SMALL, color=INK,
            ha="center", va="center")
    ax.set_xlabel("$R$ na zamrznutom uzorku (SAA)")
    ax.set_ylabel("$R$ na neovisnom uzorku (MC)")
    ax.set_xlim(-0.03, 1.03)
    ax.set_ylim(-0.03, 1.03)
    ax.set_aspect("equal")
    ax.grid(True, linewidth=0.4, color="#E8E8E8")
    ax.set_axisbelow(True)
    return _save(fig, "fig7_1_saa_mc.png")


def figure_k_sweep(results):
    """7.2/7.3: R against k, one panel per swept source.

    Stacked rather than side by side: the panels keep the full printed width, so the type
    stays at its drawn size. The three are deliberately not pooled - the same k is a
    different fraction of each source's fan-out, which is what the top axis shows."""
    sweep = results[results.tag == "k-sweep"]
    sources = sorted(sweep.source.unique())

    series = [("alns", "ALNS", HIGHLIGHT, "o", 2.0),
              ("greedy_probability", "vjerojatnost", ACCENT, "s", 1.4),
              ("greedy_degree", "stupanj", "#7a9a3f", "^", 1.1),
              ("greedy_betweenness", "međupoloženost", "#8d6e9e", "v", 1.1),
              ("greedy_spectral", "spektralni", "#c98b2e", "D", 1.1),
              ("greedy_bridge", "most", "#7f7f7f", "P", 1.1),
              ("greedy_random", "slučajno", MUTED, "x", 1.1)]

    fig, axes = plt.subplots(len(sources), 1, figsize=(WIDTH_IN, 2.45 * len(sources)))
    for ax, src in zip(axes, sources):
        grp = sweep[sweep.source == src]
        out = int(grp.out_degree.iloc[0])
        wide = grp.pivot_table(index="k", columns="method", values="R_mc")
        for method, label, colour, marker, width in series:
            ax.plot(wide.index, wide[method], label=label, color=colour,
                    marker=marker, markersize=4.0, linewidth=width,
                    zorder=3 if method == "alns" else 2)
        ax.set_title(f"izvor {src}, izlazni stupanj {out}", fontsize=BODY)
        ax.set_ylabel("$R$ (MC)")
        ax.set_ylim(-0.04, 1.04)
        # Tick the budgets that were actually measured: a tick at k = 7,5 invites reading
        # a value off a curve at a budget no run ever used.
        ax.set_xticks(list(wide.index))
        ax.grid(True, linewidth=0.4, color="#E8E8E8")
        ax.set_axisbelow(True)

        top = ax.secondary_xaxis("top", functions=(lambda v, o=out: v / o,
                                                   lambda v, o=out: v * o))
        top.set_xlabel("$k\\,/\\,\\mathrm{out}(s)$", fontsize=SMALL)
        top.tick_params(labelsize=SMALL)

    axes[-1].set_xlabel("proračun $k$")
    axes[0].legend(loc="upper left", ncol=2, frameon=False, fontsize=SMALL)
    return _save(fig, "fig7_2_k_sweep.png")


def figure_scaled_gain(results, scaled):
    """7.4: the paired change from a longer search, against how the cell was doing.

    One point per cell that actually received more iterations. The gradient is the
    result; the points below zero are the overfitting that comes with it."""
    paired = paired_scaled(results, scaled)
    more = paired[paired.more_iterations]

    fig, ax = plt.subplots(figsize=(WIDTH_IN, WIDTH_IN * 0.62))
    ax.axhline(0, color=MUTED, linewidth=1.2, zorder=1)
    for (low, high), colour in zip(BANDS, (HIGHLIGHT, "#c98b2e", ACCENT)):
        band = more[(more.R_mc_base >= low) & (more.R_mc_base < high)]
        ax.scatter(band.R_mc_base, band.delta, s=30, facecolor=colour,
                   edgecolor="white", linewidth=0.5, zorder=3,
                   label=f"{prior_band(low)}  (n = {len(band)}, "
                         f"prosjek {band.delta.mean():+.3f})".replace(".", ","))

    ax.set_xlabel("$R$ (MC) prije produljenja pretrage")
    ax.set_ylabel("promjena $R$ (MC)")
    ax.set_xlim(-0.03, 1.03)
    ax.legend(loc="upper right", frameon=False, fontsize=SMALL)
    ax.grid(True, linewidth=0.4, color="#E8E8E8")
    ax.set_axisbelow(True)
    return _save(fig, "fig7_3_scaled_gain.png")


if __name__ == "__main__":
    FIGURES_DIR.mkdir(exist_ok=True)
    results = load_results(DATA_DIR / "results.csv")
    scaled = pd.read_csv(DATA_DIR / "results_scaled.csv")

    figure_saa_mc(results)
    figure_k_sweep(results)
    figure_scaled_gain(results, scaled)

    print("\ncomparison table, for reference:")
    print(comparison_table(results).to_string(index=False))
