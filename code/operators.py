"""ALNS destroy/repair operators — two independently weighted families
(REPORT.md §4/§7a, pilot's own §32 lesson: never share one heuristic between them).

Destroy operates on the current cut D (which edges to un-remove, i.e. put back into
the graph). Repair operates on the active candidate pool (which new edges to remove).
Both use heuristics.py's rank-biased selection mechanism, not a deterministic pick —
REPORT.md §3/§7a explains why (several heuristics are heavily tied).
"""

import random

from config import DESTROY_SHAW_P, DESTROY_WORST_P
from evaluator import evaluate_reach
from heuristics import edge_scores, rank, select_q

DESTROY_OPERATORS = ["random", "worst", "related"]


def destroy_random(D: frozenset, rng: random.Random, q: int, **_kwargs) -> set:
    """R&P §3.1.2: "the special case of Shaw removal with p=1" - implemented directly
    for speed, per R&P's own note, rather than routing through the biased selector."""
    return set(rng.sample(sorted(D), min(q, len(D))))


def destroy_worst(D: frozenset, rng: random.Random, q: int, source: int, base_adj: list,
                   saa_scenarios, endpoints: dict, p: float = DESTROY_WORST_P,
                   cache: dict = None, **_kwargs) -> set:
    """R&P Algorithm 3: 'worst' = current D members contributing least to reducing
    reach (lowest marginal value = cheapest to un-remove without hurting fitness).
    Costs up to |D| SAA evaluations (PILOT_TESTS.md §34) - D is small, so this is
    affordable, but it is the one destroy operator that touches the evaluator. Shares
    the ALNS loop's evaluation cache (evaluator.py) - a `D - {eid}` here can coincide
    with a solution visited elsewhere in the search, saving a repeat BFS sweep.
    """
    f_full = evaluate_reach(source, D, base_adj, saa_scenarios, cache=cache)
    scores = {}
    for eid in D:
        f_without = evaluate_reach(source, D - {eid}, base_adj, saa_scenarios, cache=cache)
        marginal_value = f_without - f_full  # how much reach grows back if un-removed
        scores[eid] = -marginal_value  # higher score = lower marginal value = "worst"
    return set(select_q(D, scores, endpoints, q, rng, p))


def _normalized_relatedness(ref_meta: dict, other_meta: dict, hop_span: float) -> float:
    """R(i,j): lower = more related. Same convention as R&P §3.1.1 - each raw term
    normalized to roughly [0,1] relative to what's actually observed in this pool
    (R&P: 'scaling d_ij, T_x and l_i such that they only take on values from [0,1]'),
    not a fixed constant we can't justify. Equal weights on all four terms - genuinely
    uncalibrated placeholder, flagged for Phase 2 calibration (REPORT.md §6a/§10).
    """
    same_tail = 0.0 if ref_meta["source"] == other_meta["source"] else 1.0
    same_head = 0.0 if ref_meta["target"] == other_meta["target"] else 1.0
    hop_term = 0.0
    if hop_span > 0 and ref_meta["hop"] is not None and other_meta["hop"] is not None:
        hop_term = abs(ref_meta["hop"] - other_meta["hop"]) / hop_span
    p_term = abs(ref_meta["probability"] - other_meta["probability"])
    return same_tail + same_head + hop_term + p_term


def destroy_related(D: frozenset, rng: random.Random, q: int, edge_meta: dict,
                     p: float = DESTROY_SHAW_P, **_kwargs) -> set:
    """R&P Algorithm 2 (Shaw removal): start from a random D member, then repeatedly
    pick a member of D whose relatedness to the *last-added* member is used to build
    the ranking - relatedness is recomputed each step, matching R&P's actual loop
    structure (not a static one-shot score)."""
    remaining = set(D)
    seed = rng.choice(sorted(remaining))
    chosen = [seed]
    remaining.discard(seed)

    hops = [m["hop"] for m in edge_meta.values() if m["hop"] is not None]
    hop_span = (max(hops) - min(hops)) if hops else 0.0
    endpoints = {eid: (m["source"], m["target"]) for eid, m in edge_meta.items()}

    while len(chosen) < q and remaining:
        ref_meta = edge_meta[rng.choice(chosen)]
        scores = {
            eid: -_normalized_relatedness(ref_meta, edge_meta[eid], hop_span)
            for eid in remaining
        }  # negate: lower R = more related = higher score = more likely to be picked
        ranked = rank(remaining, scores, endpoints=endpoints, rng=rng)
        pick = ranked[min(int((rng.random() ** p) * len(ranked)), len(ranked) - 1)]
        chosen.append(pick)
        remaining.discard(pick)
    return set(chosen)


def destroy(name: str, D: frozenset, rng: random.Random, q: int, **kwargs) -> set:
    if name == "random":
        return destroy_random(D, rng, q, **kwargs)
    if name == "worst":
        return destroy_worst(D, rng, q, **kwargs)
    if name == "related":
        return destroy_related(D, rng, q, **kwargs)
    raise ValueError(f"unknown destroy operator: {name}")


def repair(heuristic: str, candidate_pool, D: frozenset, rng: random.Random, q: int,
           p: float, features, endpoints: dict, source_features=None) -> set:
    """One of the six heuristics (REPORT.md §2) picks q edges to add to D, from the
    active hop-windowed pool minus D, via the same rank-biased mechanism as destroy."""
    candidates = [e for e in candidate_pool if e not in D]
    scores = edge_scores(heuristic, features, candidates, source_features=source_features, rng=rng)
    return set(select_q(candidates, scores, endpoints, q, rng, p))
