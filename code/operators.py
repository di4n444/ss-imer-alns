"""ALNS destroy and repair operators — two independently weighted families, never
sharing a heuristic between them.

Destroy picks members of the current cut D to put back into the graph. Repair picks
new edges from the active hop-windowed pool to cut instead. Every destroy operator has
the same signature `(D, q, ctx, evaluator, rng) -> set`, so `DESTROY_REGISTRY` can
dispatch by name without kwargs plumbing — that uniformity is the point of the
Strategy pattern here.

Grounded in R&P (2006) §3.1: random removal, worst removal (Algorithm 3) and Shaw
"related" removal (Algorithm 2), with their tuned determinism exponents
(p_worst=3, p_Shaw=6 —), and Shaw relatedness as their eq. (17)
mapped term by term onto SS-IMER.

Fidelity, stated precisely because "true R&P" is a requirement of this thesis:
  - Shaw removal follows Algorithm 2 exactly, including the re-ranking against the
    growing chosen set that is the operator's defining feature;
  - random removal is Algorithm 3.1.2 (Shaw with p=1, implemented separately as R&P do);
  - worst removal follows Algorithm 3 except that it ranks once instead of rebuilding L
    per pick — a cost-driven departure, documented on the function itself.
"""

import random

from config import (
    DESTROY_SHAW_P,
    DESTROY_WORST_P,
    SHAW_CHI,
    SHAW_OMEGA,
    SHAW_PHI,
    SHAW_PSI,
)
from heuristics import biased_index, edge_scores, rank, select_q


def destroy_random(D: frozenset, q: int, ctx, evaluator, rng: random.Random) -> set:
    """R&P §3.1.2 — Shaw removal with p=1, implemented directly (as R&P do) since it
    needs no ranking at all. `sorted` first so the draw is reproducible regardless of
    set iteration order."""
    return set(rng.sample(sorted(D), min(q, len(D))))


def destroy_worst(D: frozenset, q: int, ctx, evaluator, rng: random.Random) -> set:
    """R&P Algorithm 3, with one documented departure. "Worst" = the members of D
    contributing least to reducing reach, i.e. the cheapest to give back, freeing budget
    for repair to spend better.

    Marginal values come from `Evaluator.marginal_values`, which computes all |D| of
    them in one pass per scenario instead of |D|+1 full sweeps — without that this
    single operator dominated the entire runtime.

    **Departure**: R&P rebuild and re-sort L *inside* the removal loop (Algorithm 3
    line 3), because removing one request changes cost(i,s) for the rest. We rank once
    and draw q picks from that single ranking. Doing it literally would cost one full
    marginal pass per pick — measured at ~155 ms each, so up to q=8 picks over ~100
    worst-removal calls in a 300-iteration run, roughly +2 minutes per run. Shaw removal
    below *does* re-rank each step, because there the re-ranking is the operator's whole
    point and it costs only dict lookups."""
    _, gains = evaluator.marginal_values(ctx.source, D, ctx.endpoints)
    scores = {eid: -gain for eid, gain in gains.items()}  # least valuable ranks first
    return set(select_q(D, scores, ctx.endpoints, q, rng, DESTROY_WORST_P))


def _relatedness(a: int, b: int, ctx) -> float:
    """R(i,j), R&P eq. (17), mapped onto SS-IMER. Lower means more related.

    R&P (PDPTW):
        R(i,j) = phi*( d_A(i)A(j) + d_B(i)B(j) )                      location
               + chi*( |T_A(i)-T_A(j)| + |T_B(i)-T_B(j)| )            time
               + psi*|l_i - l_j|                                      load
               + omega*( 1 - |K_i & K_j| / min(|K_i|,|K_j|) )         servable set

    A "request" here is an edge e=(u,v); its two locations A/B are the tail and the head.

    - phi   R&P use normalised road distance between the two pickups and between the two
            deliveries. Our nodes carry no coordinates, but the graph is itself a metric
            space, so the number of hops between two nodes stands in for it
            (analyse_graph.node_distances), normalised by the largest distance in the
            graph. Within one hop layer every tail is the source, so the tail half is
            0 there by construction - correctly, those edges do start in the same place -
            and the term's variation comes from how far apart the two *heads* sit.
    - chi   R&P's T_i is when location i is visited. Under IC the earliest a node can be
            reached is its BFS hop from s, so hop distance *is* our time coordinate.
            Both endpoints enter, matching their sum over pickup and delivery.
    - psi   R&P compare capacity demand; our edge's "load" is the transmission
            probability it carries. Already in [0,1].
    - omega R&P's K_i is the set of vehicles that can serve request i, and they compare
            it by overlap coefficient — min-normalised, not Jaccard, so a small set
            contained in a large one counts as fully related. Our analogue is the
            territory the cascade enters through the edge, i.e. the head's bounded
            descendant set (analyse_graph.node_territories). Two cut edges are related
            when they guard the same downstream ground.

    Each raw term is scaled to [0,1] before weighting, as R&P require ("d_ij, T_x and
    l_i are normalized such that 0 <= R(i,j) <= 2(phi+chi)+psi+omega").

    This term-by-term correspondence is what lets us use R&P's own tuned
    (phi,chi,psi,omega) = (9,3,2,5) rather than equal weights. It also fixes a measured
    degeneracy: with the omega term missing, every pair of hop0 edges scored identically
    on three of the four terms, leaving relatedness a function of |p_a - p_b| alone —
    2 distinct values across 190 pairs on the out-degree-486 hub, i.e. `destroy_related`
    was `destroy_random` with extra steps."""
    ua, va = ctx.endpoints[a]
    ub, vb = ctx.endpoints[b]
    hop, span = ctx.hop_of_node, ctx.hop_span

    distance, longest = ctx.distance, ctx.distance_max
    location = (distance[ua][ub] + distance[va][vb]) / longest if longest else 0.0
    if span > 0:
        time = (abs(hop[ua] - hop[ub]) + abs(hop[va] - hop[vb])) / span
    else:
        time = 0.0
    load = abs(ctx.probability[a] - ctx.probability[b])

    ta, tb = ctx.territory[va], ctx.territory[vb]
    if ta and tb:
        servable = 1.0 - len(ta & tb) / min(len(ta), len(tb))
    else:  # two dead ends are interchangeable; one dead end and one live edge are not
        servable = 0.0 if not ta and not tb else 1.0

    return SHAW_PHI * location + SHAW_CHI * time + SHAW_PSI * load + SHAW_OMEGA * servable


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


def repair(heuristic: str, pool: list, q: int, ctx, rng: random.Random, p: float) -> set:
    """Fill the cut back up to k by choosing q new edges from `pool` under one of the six
    heuristics. `pool` is the active hop-windowed candidate list with the current partial
    cut already excluded — the exclusion belongs to the caller, which is why this takes no
    `D` argument (it previously did, and never read it)."""
    scores = edge_scores(heuristic, ctx, pool, rng=rng)
    return set(select_q(pool, scores, ctx.endpoints, q, rng, p))
