"""ALNS destroy and repair operators — two independently weighted families, never
sharing a heuristic between them (REPORT.md §4/§7a; PILOT_TESTS.md §32).

Destroy picks members of the current cut D to put back into the graph. Repair picks
new edges from the active hop-windowed pool to cut instead. Every destroy operator has
the same signature `(D, q, ctx, evaluator, rng) -> set`, so `DESTROY_REGISTRY` can
dispatch by name without kwargs plumbing — that uniformity is the point of the
Strategy pattern here.

Grounded in R&P (2006) §3.1: random removal, worst removal (Algorithm 3) and Shaw
"related" removal (Algorithm 2), with their tuned determinism exponents
(p_worst=3, p_Shaw=6 — see REPORT.md §6a).
"""

import random

from config import DESTROY_SHAW_P, DESTROY_WORST_P
from heuristics import biased_index, edge_scores, rank, select_q


def destroy_random(D: frozenset, q: int, ctx, evaluator, rng: random.Random) -> set:
    """R&P §3.1.2 — Shaw removal with p=1, implemented directly (as R&P do) since it
    needs no ranking at all. `sorted` first so the draw is reproducible regardless of
    set iteration order."""
    return set(rng.sample(sorted(D), min(q, len(D))))


def destroy_worst(D: frozenset, q: int, ctx, evaluator, rng: random.Random) -> set:
    """R&P Algorithm 3. "Worst" = the members of D contributing least to reducing
    reach, i.e. the cheapest to give back, freeing budget for repair to spend better.

    Marginal values come from `Evaluator.marginal_values`, which computes all |D| of
    them in one pass per scenario instead of |D|+1 full sweeps — without that this
    single operator dominated the entire runtime (REPORT.md §11)."""
    _, gains = evaluator.marginal_values(ctx.source, D, ctx.endpoints)
    scores = {eid: -gain for eid, gain in gains.items()}  # least valuable ranks first
    return set(select_q(D, scores, ctx.endpoints, q, rng, DESTROY_WORST_P))


def _relatedness(a: int, b: int, ctx) -> float:
    """R(i,j) in R&P §3.1.1 — lower means more related. Four terms, each normalised to
    roughly [0,1] against what this instance actually contains (R&P normalise their raw
    terms the same way rather than using absolute scales).

    Equal weights are an uncalibrated placeholder; R&P tuned theirs (φ,χ,ψ,ω)=(9,3,2,5)
    for PDPTW terms that have no counterpart here. Flagged for Phase 2 (REPORT.md §10)."""
    ua, va = ctx.endpoints[a]
    ub, vb = ctx.endpoints[b]
    same_tail = 0.0 if ua == ub else 1.0
    same_head = 0.0 if va == vb else 1.0
    hop_a, hop_b = ctx.hop_of_edge.get(a), ctx.hop_of_edge.get(b)
    if ctx.hop_span > 0 and hop_a is not None and hop_b is not None:
        hop_term = abs(hop_a - hop_b) / ctx.hop_span
    else:
        hop_term = 0.0
    prob_term = abs(ctx.probability[a] - ctx.probability[b])
    return same_tail + same_head + hop_term + prob_term


def destroy_related(D: frozenset, q: int, ctx, evaluator, rng: random.Random) -> set:
    """R&P Algorithm 2 (Shaw removal): seed with a random member of D, then repeatedly
    draw a member related to one already chosen. Relatedness is recomputed against the
    growing set each step — that dynamic re-ranking is what distinguishes Shaw removal
    from a static score, so it is kept rather than precomputed."""
    remaining = set(D)
    seed = rng.choice(sorted(remaining))
    chosen = [seed]
    remaining.discard(seed)

    while len(chosen) < q and remaining:
        reference = rng.choice(chosen)
        scores = {eid: -_relatedness(reference, eid, ctx) for eid in remaining}
        ranked = rank(remaining, scores, ctx.endpoints, rng=rng)
        pick = ranked[biased_index(len(ranked), rng, DESTROY_SHAW_P)]
        chosen.append(pick)
        remaining.discard(pick)
    return set(chosen)


DESTROY_REGISTRY = {
    "random": destroy_random,
    "worst": destroy_worst,
    "related": destroy_related,
}
DESTROY_OPERATORS = list(DESTROY_REGISTRY)


def repair(heuristic: str, pool: list, D: frozenset, q: int, ctx,
           rng: random.Random, p: float) -> set:
    """Fill D back up to k by cutting q new edges chosen from `pool` (the active
    hop-windowed candidates, already excluding D) under one of the six heuristics."""
    scores = edge_scores(heuristic, ctx, pool, rng=rng)
    return set(select_q(pool, scores, ctx.endpoints, q, rng, p))
