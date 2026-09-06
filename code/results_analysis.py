"""The grouping rules for the measurement, in one place.

Chapter 7 and the result figures both aggregate `data/results.csv`, and the rules that
govern the aggregation are not obvious enough to be restated in two files: which tags may
be pooled, which rows are duplicates, how close two scores must be to count as tied. A
second copy would drift, and the drift would show up as two different numbers for the same
claim in the same document.

So the rules live here and both callers import them. Nothing in this module reads a graph
or imports igraph: the thesis build must stay cheap, and it only ever wants numbers.

The rules themselves, and why:

- **Only `population`, `k-sweep` and `typical` may be compared.** The `probe*` rows hold
  ALNS at a different iteration budget with no baselines beside them, so pooling them with
  the main run would compare a method at one setting against opponents measured at
  another.
- **A (source, k) pair measured under two tags is one instance, not two.** Three pairs were
  drawn into both `population` and `k-sweep`; the pipeline is deterministic, so the second
  measurement reproduces the first exactly, and counting both would weight those instances
  twice.
- **`isolated` rows are excluded from every average** - they are solved in closed form, so
  every method scores identically. None of the measurement sources produced one, but the
  filter stays: it is a property of the protocol, not of this particular sample.
"""

import pandas as pd

MAIN_TAGS = ("population", "k-sweep", "typical")

CRITERIA = ("probability", "degree", "betweenness", "spectral", "bridge", "random")

# Two scores this close are one score. The evaluator is deterministic and the objective is
# a mean over a fixed scenario set, so a genuine tie is exact; the tolerance only absorbs
# float noise, and is far below any difference the thesis would report.
TIE_TOL = 1e-9

# How a cell was doing before its search was lengthened (§7.4). The edges are round rather
# than derived: they split the paired cells into three groups large enough to average.
BANDS = ((0.0, 0.3), (0.3, 0.6), (0.6, 1.01))

_BAND_LABELS = {0.0: "slab učinak (R < 0,3)",
                0.3: "osrednji učinak (0,3 ≤ R < 0,6)",
                0.6: "dobar učinak (R ≥ 0,6)"}


def prior_band(low):
    """The Croatian label for a band, defined once so the figure legend and the table in
    the text cannot disagree about where the boundaries lie."""
    return _BAND_LABELS[low]


def load_results(path):
    """Read the measurement and drop the rows no comparison may use."""
    results = pd.read_csv(path)
    return results[results.stop_reason != "isolated"]


def comparison_rows(results):
    """The rows the method comparison is entitled to use: main tags, one row per
    (source, k, method)."""
    main = results[results.tag.isin(MAIN_TAGS)]
    return main.drop_duplicates(subset=["source", "k", "method"])


def comparison_cells(results):
    """One row per instance, one column per method, holding out-of-sample R.

    Carries the two stratifying variables with it, since every average over these cells
    has to be split by at least one of them: the cells span three orders of magnitude in
    reach and budgets from 3 to 75, so a plain mean reports whichever regime happens to be
    the most numerous."""
    rows = comparison_rows(results)
    cells = rows.pivot_table(index=["source", "k", "out_degree"], columns="method",
                             values="R_mc").reset_index()
    cells["budget_share"] = cells.k / cells.out_degree

    reach = (rows[rows.method == "alns"].set_index(["source", "k"]).sigma0_mc)
    cells["sigma0"] = [reach.get((row.source, row.k)) for row in cells.itertuples()]
    return cells


def comparison_table(results):
    """ALNS against each criterion separately: the record and the mean difference.

    Deliberately per criterion. A per-cell maximum over the six is an oracle that picks
    the winner with hindsight for every instance, so it is a bound rather than an opponent
    and is reported by `oracle_summary` instead."""
    cells = comparison_cells(results)
    rows = []
    for criterion in CRITERIA:
        delta = cells["alns"] - cells[f"greedy_{criterion}"]
        rows.append({
            "criterion": criterion,
            "better": int((delta > TIE_TOL).sum()),
            "tied": int((delta.abs() <= TIE_TOL).sum()),
            "worse": int((delta < -TIE_TOL).sum()),
            "mean_delta": delta.mean(),
            "mean_R": cells[f"greedy_{criterion}"].mean(),
        })
    table = pd.DataFrame(rows).sort_values("mean_delta", ascending=False)
    return table.reset_index(drop=True)


def oracle_summary(results):
    """The per-cell best of the six criteria - an upper bound, not a method."""
    cells = comparison_cells(results)
    best = cells[[f"greedy_{c}" for c in CRITERIA]].max(axis=1)
    delta = cells["alns"] - best
    return {
        "cells": len(cells),
        "alns_mean_R": cells["alns"].mean(),
        "oracle_mean_R": best.mean(),
        "mean_delta": delta.mean(),
        "alns_at_least": int((delta >= -TIE_TOL).sum()),
    }


def stratified(results, by, edges, labels, against="greedy_probability"):
    """ALNS against one criterion inside each stratum of `by`."""
    cells = comparison_cells(results)
    cells = cells.assign(stratum=pd.cut(cells[by], edges, labels=labels))
    rows = []
    for stratum, grp in cells.groupby("stratum", observed=True):
        delta = grp["alns"] - grp[against]
        rows.append({
            "stratum": stratum,
            "cells": len(grp),
            "alns_mean_R": grp["alns"].mean(),
            "other_mean_R": grp[against].mean(),
            "mean_delta": delta.mean(),
            "better": int((delta > TIE_TOL).sum()),
            "worse": int((delta < -TIE_TOL).sum()),
        })
    return pd.DataFrame(rows)


def gap_summary(results):
    """The SAA-MC gap over the ALNS cells: how much of the searched-for gain survives on
    an independent sample."""
    rows = comparison_rows(results)
    alns = rows[rows.method == "alns"]
    gap = alns.saa_mc_gap
    baselines = {c: rows[rows.method == f"greedy_{c}"].saa_mc_gap.median()
                 for c in CRITERIA}
    return {
        "cells": len(gap),
        "median": gap.median(),
        "q1": gap.quantile(0.25),
        "q3": gap.quantile(0.75),
        "min": gap.min(),
        "max": gap.max(),
        "optimistic": int((gap > TIE_TOL).sum()),
        "pessimistic": int((gap < -TIE_TOL).sum()),
        "over_10": int((gap.abs() > 0.10).sum()),
        "baseline_medians": baselines,
        "worst_baseline_median": max(baselines.values()),
    }


def paired_scaled(results, scaled):
    """The lengthened search against the same cells at the original budget.

    Paired per cell, never two independent averages: the instances are identical, so the
    pairing removes all between-cell variation, which is the only reason a mean change of
    a few hundredths is readable at all."""
    base = comparison_rows(results)
    base = base[base.method == "alns"][
        ["source", "k", "out_degree", "R_mc", "param_max_iter", "seconds"]]
    paired = scaled.merge(base, on=["source", "k"], suffixes=("_scaled", "_base"))
    paired["delta"] = paired.R_mc_scaled - paired.R_mc_base
    paired["more_iterations"] = paired.param_max_iter_scaled > paired.param_max_iter_base
    return paired


def scaled_summary(results, scaled):
    """What the longer search bought, and what it cost."""
    paired = paired_scaled(results, scaled)
    more = paired[paired.more_iterations]
    unchanged = paired[~paired.more_iterations]

    bands = []
    for low, high in BANDS:
        grp = more[(more.R_mc_base >= low) & (more.R_mc_base < high)]
        bands.append({"band": prior_band(low), "cells": len(grp),
                      "mean_delta": grp.delta.mean(), "max_delta": grp.delta.max()})

    return {
        "paired": len(paired),
        "more": len(more),
        "budget_unchanged": len(unchanged),
        "reproduced_exactly": int((unchanged.delta.abs() < 1e-12).sum()),
        "improved": int((more.delta > TIE_TOL).sum()),
        "unchanged": int((more.delta.abs() <= TIE_TOL).sum()),
        "worse": int((more.delta < -TIE_TOL).sum()),
        "mean_delta": more.delta.mean(),
        "best_delta": more.delta.max(),
        "worst_delta": more.delta.min(),
        "bands": pd.DataFrame(bands),
        "seconds_scaled": paired.seconds_scaled.sum(),
        "seconds_base": paired.seconds_base.sum(),
        "cost_factor": paired.seconds_scaled.sum() / paired.seconds_base.sum(),
    }


def _deep_edges(hop_mix):
    """How many edges of a cut lie beyond hop 0. `hop_mix` is stored as a dict literal."""
    import ast
    mix = ast.literal_eval(hop_mix) if isinstance(hop_mix, str) else (hop_mix or {})
    return sum(count for hop, count in mix.items() if int(hop) > 0)


def hop_summary(results):
    """The Level-2 question: do edges beyond hop 0 reach the winning cut?

    Deliberately not read off the learned layer weights. Layers differ in size by up to
    three orders of magnitude and a smaller layer is easier to search, so a high weight on
    hop 0 partly measures that ease rather than that hop 0 is where the good edges are.
    What the cut actually contains carries no such confound."""
    rows = comparison_rows(results)
    alns = rows[rows.method == "alns"]
    deep = alns.hop_mix.map(_deep_edges)

    by_hop, total = {}, 0
    for mix in alns.hop_mix:
        import ast
        parsed = ast.literal_eval(mix) if isinstance(mix, str) else (mix or {})
        for hop, count in parsed.items():
            by_hop[int(hop)] = by_hop.get(int(hop), 0) + count
            total += count

    cells = comparison_cells(results).set_index(["source", "k"])
    best = cells[[f"greedy_{c}" for c in CRITERIA]].max(axis=1)
    margin = (cells["alns"] - best)
    per_cell = [margin.get((row.source, row.k)) for row in alns.itertuples()]

    pure = [m for m, d in zip(per_cell, deep) if d == 0]
    mixed = [m for m, d in zip(per_cell, deep) if d > 0]
    return {
        "cells": len(alns),
        "pure_hop0": int((deep == 0).sum()),
        "with_deep": int((deep > 0).sum()),
        "edge_share": {hop: count / total for hop, count in sorted(by_hop.items())},
        "mean_margin_pure": sum(pure) / len(pure) if pure else float("nan"),
        "mean_margin_deep": sum(mixed) / len(mixed) if mixed else float("nan"),
    }


def deep_shedding(results, scaled):
    """Cells whose lengthened search replaced every deep edge with a hop-0 one.

    This is the decisive part of the Level-2 answer. A search that merely fails to find
    good deep edges cannot distinguish "deeper edges are useless" from "deeper layers are
    too big to search"; a search that had those edges and discarded them on reconsideration
    was not short of exploration, it judged them worse."""
    paired = paired_scaled(results, scaled)
    paired = paired[paired.more_iterations]

    base = comparison_rows(results)
    base = base[base.method == "alns"].set_index(["source", "k"]).hop_mix

    rows = []
    for row in paired.itertuples():
        before = _deep_edges(base.get((row.source, row.k), "{}"))
        rows.append({"source": row.source, "k": row.k,
                     "deep_before": before, "deep_after": _deep_edges(row.hop_mix),
                     "R_before": row.R_mc_base, "R_after": row.R_mc_scaled,
                     "delta": row.delta})
    table = pd.DataFrame(rows)
    shed = table[(table.deep_before > 0) & (table.deep_after == 0)]
    rest = table.drop(shed.index)
    return {
        "shed": shed.sort_values("delta", ascending=False),
        "mean_delta_shed": shed.delta.mean(),
        "mean_delta_rest": rest.delta.mean(),
        "n_rest": len(rest),
    }


def runtime_summary(results):
    """Totals over the `seconds` column.

    Summed, never read per row: `_row` rounds to two decimals, so a greedy run faster than
    10 ms is stored as 0.00. Each missing value is under 0.005 s, so the sum stays accurate
    to well under a second while the individual rows are useless."""
    rows = comparison_rows(results)
    alns = rows[rows.method == "alns"].seconds.sum()
    baselines = rows[rows.method != "alns"].seconds.sum()
    return {
        "alns_seconds": alns,
        "baselines_seconds": baselines,
        "baselines_share": baselines / alns,
        "one_baseline_share": baselines / len(CRITERIA) / alns,
    }
