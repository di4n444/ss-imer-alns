"""Greedy baselines: one per heuristic, hop0 only, deterministic.

These are the reference point ALNS is measured against, and the hop0 restriction is the
whole point of them (README "Problem"; REPORT.md §7, §8c). A baseline may only cut edges
leaving `s` directly. Widening its pool does not make it a better opponent — the pilot
measured hop0∪hop1 greedy at mean R≈0.02 against hop0's 0.48, because a fixed score on a
wider pool picks high-`p` edges further out that never actually close the source
(PILOT_TESTS.md §23: source 718, hop0 `p` gives sigma=48, hop0∪hop1 `p` gives sigma=642).
"Should you have looked past the source's own edges?" is therefore an ALNS question, and
local quarantine is the honest null model to ask it against.

Selection here is deliberately stripped of everything ALNS-specific: no `y^p` draw, no
tie shuffle, no acceptance criterion, no iteration. `rank(..., rng=None)` sorts by
(score desc, u asc, v asc), so one (source, k, heuristic) has exactly one answer forever
(REPORT.md §3, §7a). The one exception is `random`, whose *scores* come from a seeded
RNG: it is the only baseline that varies across seeds and so the only one to average over
them (PILOT_TESTS.md §31).

Because the other five are deterministic, orchestration must compute them once per
(source, k) and reuse them across ALNS seeds rather than recomputing per seed
(PILOT_TESTS.md §19).

Not implemented here, deliberately: a sigma-greedy that picks by measured marginal reach
reduction rather than by a topological score. That is Kimura et al. (2008)'s own proposed
method — the six below are the heuristics *he* used as baselines — so it is the stronger
opponent and belongs in the comparison eventually (REPORT.md §15). Deferred, not
forgotten.
"""

import random

from heuristics import HEURISTICS, edge_scores, tie_group_sizes, topk


def _select(ctx, heuristic: str, k: int, rng: random.Random):
    """Score the hop0 pool once and take the top k. Returns the working parts so the
    caller can report on the ranking as well as use it — `random`'s scores cannot simply
    be recomputed for reporting, since drawing them again advances the RNG."""
    pool = list(ctx.edges_by_hop.get(0, []))
    scores = edge_scores(heuristic, ctx, pool, rng=rng)
    ranked = topk(pool, scores, ctx.endpoints, k, rng=None)
    return set(ranked), pool, scores, ranked


def greedy_cut(ctx, heuristic: str, k: int, rng: random.Random = None) -> set:
    """The k hop0 edges `heuristic` ranks highest. Fewer than k only when the source has
    fewer than k out-edges, which is the trivial isolated case — see `run_greedy`."""
    return _select(ctx, heuristic, k, rng)[0]


def run_greedy(ctx, heuristic: str, k: int, evaluator, seed: int = None) -> dict:
    """One baseline run, shaped like `run_alns`'s result so orchestration can write one
    CSV row per method without special-casing (REPORT.md §9, PILOT_TESTS.md §28: one row
    per method, never a column that pools ALNS with the methods it is judged against).

    `seed` is used only by the `random` heuristic and ignored by the other five, which is
    itself the reason `random` is the only baseline averaged across seeds.

    k > out(s) is the trivial case, consistently with REPORT.md §13: the cut is all of
    hop0, the source is isolated, sigma = 1 and that is provably optimal. Unlike ALNS this
    does *not* top the cut up to exactly k from deeper layers — a hop0 baseline has no
    deeper layers by definition — so `cut_size` can be below k. Both methods reach
    sigma = 1 there, so the comparison stays fair; `stop_reason` marks the rows so they
    can be excluded from averages they would otherwise flatter equally.
    """
    if heuristic not in HEURISTICS:
        raise ValueError(f"unknown heuristic: {heuristic}; expected one of {HEURISTICS}")
    rng = random.Random(seed) if heuristic == "random" else None

    cut, pool, scores, ranked = _select(ctx, heuristic, k, rng)
    reach = evaluator.evaluate_reach(ctx.source, cut, ctx.endpoints)

    # REPORT.md §3.1 wants tie frequency reported as a structural fact about each
    # heuristic's candidate pool, and specifically the tie *at the cutoff* — the group
    # straddling rank k, where the deterministic (u, v) rule silently decides which tied
    # edges make the cut and which do not. `tie_split` is (taken, left behind) within
    # that group: a second number > 0 means the rule, not the heuristic, chose.
    if ranked and len(ranked) < len(pool):
        cutoff = scores[ranked[-1]]
        tied = [e for e in pool if scores[e] == cutoff]
        taken = sum(1 for e in tied if e in cut)
        tie_split = (taken, len(tied) - taken)
    else:
        tie_split = (0, 0)

    return {
        "method": f"greedy_{heuristic}",
        "heuristic": heuristic,
        "seed": seed if heuristic == "random" else None,
        "best_cut": cut,
        "cut_size": len(cut),
        "best_reach_saa": reach,
        # sigma >= 1 always, so reach == 1 means the source was cut off completely.
        "stop_reason": "isolated" if reach <= 1.0 + 1e-9 else "topk",
        "hop_mix": {0: len(cut)} if cut else {},
        "candidates": len(pool),
        "tie_split_at_cutoff": tie_split,
        "tie_group_sizes": tie_group_sizes(pool, scores),
    }


if __name__ == "__main__":
    import create_graph
    import create_subgraphs
    import heuristics as _h
    from config import ALNS_RUN_SEED
    from evaluator import Evaluator
    from source_context import build_source_context

    SOURCE_SNAP_ID, K = 1, 20

    g = create_graph.build_graph()
    source = g.vs["name"].index(SOURCE_SNAP_ID)
    ctx = build_source_context(g, source, _h.load_global_features())
    evaluator = Evaluator(g.vcount(), create_subgraphs.build_saa_scenarios(g))
    uncut = evaluator.evaluate_reach(source, frozenset(), ctx.endpoints)

    print(f"source {SOURCE_SNAP_ID} (internal {source}), out-degree {ctx.out_degree}, "
          f"k={K}, sigma_0={uncut:.2f}\n")
    print(f"{'baseline':>22} {'sigma':>9} {'R':>7}  {'tie at cutoff':>14}")
    for name in HEURISTICS:
        r = run_greedy(ctx, name, K, evaluator, seed=ALNS_RUN_SEED)
        taken, left = r["tie_split_at_cutoff"]
        tie = f"{taken}+{left} tied" if left else "-"
        print(f"{r['method']:>22} {r['best_reach_saa']:>9.2f} "
              f"{1 - r['best_reach_saa'] / uncut:>7.3f}  {tie:>14}")
