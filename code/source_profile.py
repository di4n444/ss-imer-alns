"""Per-source profile for the whole graph -> data/source_profile.csv.

The source sample is stratified by reach level and out-degree band, and the stratifying
variable must be *reach*, not centrality: topologically distinct nodes turned out to have identical cascade
reach to the decimal, because they land in the same live-edge SCC. So the sample cannot be
drawn until reach has actually been measured, and this measures it for every source rather
than for a probe, so the sample is drawn from the real distribution and the same table can
later justify each curated showcase pick.

Also recorded because they cost nothing on top of the same pass and each answers a
question the sample design has to face:
  - `out_degree`, the hop0 candidate-pool size, which is the second stratifying axis and
    also bounds k (k >= out_degree is the trivial isolated case);
  - `reachable`, the deterministic descendant count on the base graph, i.e. the ceiling
    sigma_0 could ever approach, which separates "small because it is cut off" from
    "small because its edges are weak";
  - `sigma0_saa`, the in-sample reach with nothing cut - the denominator of R = 1 -
    sigma/sigma_0, every run's baseline, and the thing ALNS runtime
    actually scales with, so it doubles as the cost model for the experiment matrix.

Deliberately *not* here: any ALNS or baseline result. This is a property of the graph, so
it is computed once and reused, never recomputed per experiment.
"""

import time

import igraph as ig
import pandas as pd

import create_graph
import create_subgraphs
from config import DATA_DIR, SAA_SCENARIO_COUNT
from evaluator import Evaluator


def profile_sources(g: ig.Graph, scenarios: list) -> pd.DataFrame:
    """One row per node. A single Evaluator is shared across every source — its cache is
    keyed by (source, cut), so this is safe, and the scenario set is the expensive thing
    that should not be rebuilt 3683 times."""
    endpoints = {e.index: (e.source, e.target) for e in g.es}
    evaluator = Evaluator(g.vcount(), scenarios)
    names = g.vs["name"]
    empty = frozenset()

    rows = []
    for v in range(g.vcount()):
        rows.append({
            "source": v,
            "snap_id": names[v],
            "out_degree": g.outdegree(v),
            "in_degree": g.indegree(v),
            "reachable": len(g.subcomponent(v, mode="out")),
            "sigma0_saa": evaluator.evaluate_reach(v, empty, endpoints),
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    started = time.time()
    g = create_graph.build_graph()
    scenarios = create_subgraphs.build_saa_scenarios(g)
    print(f"graph + {SAA_SCENARIO_COUNT} SAA scenarios: {time.time() - started:.1f}s")

    t = time.time()
    profile = profile_sources(g, scenarios)
    profile.to_csv(DATA_DIR / "source_profile.csv", index=False)
    print(f"profiled {len(profile)} sources in {time.time() - t:.0f}s "
          f"-> data/source_profile.csv\n")

    eligible = profile[profile.out_degree > 0]
    print(f"{len(profile) - len(eligible)} of {len(profile)} nodes have out-degree 0 "
          f"and cannot be sources at all\n")

    print("sigma0 distribution over eligible sources:")
    print(f"  {'decile':>8} {'sigma0':>10}")
    for q in range(0, 11):
        print(f"  {q * 10:>7}% {eligible.sigma0_saa.quantile(q / 10):>10.2f}")

    print("\nsigma0 by band (is reach bimodal?):")
    bands = [(1, 2), (2, 10), (10, 100), (100, 400), (400, 600), (600, 1e9)]
    for lo, hi in bands:
        n = ((eligible.sigma0_saa >= lo) & (eligible.sigma0_saa < hi)).sum()
        print(f"  sigma0 in [{lo:>5}, {hi:>5}): {n:>5} sources "
              f"({100 * n / len(eligible):>5.1f}%)")

    print("\nout-degree band x reach class (the candidate stratification):")
    saturated = eligible.sigma0_saa >= 400
    print(f"  {'out-degree':>12} {'n':>6} {'saturated':>11} {'low-reach':>11} "
          f"{'median sigma0':>14}")
    for lo, hi in [(1, 4), (4, 10), (10, 20), (20, 50), (50, 10000)]:
        sel = (eligible.out_degree >= lo) & (eligible.out_degree < hi)
        if not sel.any():
            continue
        print(f"  {f'[{lo},{hi})':>12} {sel.sum():>6} {(sel & saturated).sum():>11} "
              f"{(sel & ~saturated).sum():>11} "
              f"{eligible[sel].sigma0_saa.median():>14.2f}")

    print(f"\ntotal {time.time() - started:.0f}s")
