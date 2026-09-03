"""Phase 1 smoke test (PLAN.md): run the whole pipeline end to end on one real
(source, k) and check the wiring, not the science. Reports timings so the runtime
budget stays visible — the target is one (source, k, seed) run in well under a minute.
"""

import random
import time

import create_graph
import create_subgraphs
import heuristics
from alns_optimizer import run_alns
from config import ALNS_RUN_SEED
from evaluator import Evaluator
from source_context import build_source_context

SOURCE_SNAP_ID = 1
K = 20


def main():
    started = time.time()
    g = create_graph.build_graph()
    source = g.vs["name"].index(SOURCE_SNAP_ID)

    scenarios = create_subgraphs.build_saa_scenarios(g)
    features = heuristics.load_global_features()
    ctx = build_source_context(g, source, features)
    evaluator = Evaluator(g.vcount(), scenarios)
    print(f"setup: {time.time() - started:.1f}s "
          f"(source={SOURCE_SNAP_ID} out_degree={ctx.out_degree} k={K}, "
          f"{len(scenarios)} SAA scenarios, hop0={len(ctx.edges_by_hop[0])} edges)")

    warm_start = set(random.Random(ALNS_RUN_SEED).sample(ctx.edges_by_hop[0], K))
    warm_reach = evaluator.evaluate_reach(source, warm_start, ctx.endpoints)

    t0 = time.time()
    result = run_alns(ctx, K, evaluator, ALNS_RUN_SEED)
    elapsed = time.time() - t0

    reduction = 100 * (warm_reach - result["best_reach_saa"]) / warm_reach
    print(f"\nALNS: {elapsed:.1f}s, {result['stop_reason']}, "
          f"{result['evaluations']} distinct cuts evaluated")
    print(f"  warm start reach : {warm_reach:.2f}")
    print(f"  best reach (SAA) : {result['best_reach_saa']:.2f}  ({reduction:.1f}% lower)")
    print(f"  scope weights    : { {h: round(w, 2) for h, w in sorted(result['scope_weights'].items())} }")
    print(f"  best hits by hop : {result['best_hits_by_hop']}")
    final = result["trace"][-1]
    print(f"  repair weights   : { {k: round(v, 2) for k, v in final['repair_weights'].items()} }")
    print(f"  destroy weights  : { {k: round(v, 2) for k, v in final['destroy_weights'].items()} }")

    assert result["best_reach_saa"] <= warm_reach, "ALNS returned worse than its warm start"
    assert len(result["best_cut"]) == K, "best cut is not exactly k edges"
    print("\nOK: pipeline runs end to end and improves on the warm start.")


if __name__ == "__main__":
    main()
