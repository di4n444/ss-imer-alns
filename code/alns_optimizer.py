"""ALNS main loop: roulette-wheel operator selection, R&P's (2006) adaptive weight
update, simulated-annealing acceptance, and the hop-scope mechanism.

Faithful to R&P for everything they specify (REPORT.md §6a): independent roulette
wheels per operator family (eq. 20), the sigma1/sigma2/sigma3 score system with its
"only reward unvisited solutions" rule, the segment-end weight update
w' = w(1-r) + r*(score/count), and SA acceptance with a start temperature calibrated
from the initial solution.

Three deliberate departures, all documented in REPORT.md §6a and §12:
  - the cooling rate is derived from *our* iteration budget rather than copying R&P's
    c=0.99975, which only makes sense against their 25000-iteration runs;
  - the hop scope is our own addition — R&P have no notion of a restricted candidate
    neighbourhood — implemented as a *third weight book* over hop layers rather than an
    expanding horizon, because the horizon version was measured to wreck the search
    (REPORT.md §12);
  - Delta = 0 is accepted but scores nothing, which is what a strict reading of R&P's
    three sigma cases already implies (PILOT_TESTS.md §18's bug, fixed by construction).
"""

import math
import random

from config import (
    ALNS_FINAL_TEMP_FRACTION,
    ALNS_MAX_HOP_SCOPE,
    ALNS_MAX_ITER,
    ALNS_Q_MAX_FRAC,
    ALNS_Q_MIN_FRAC,
    ALNS_REACTION_FACTOR,
    ALNS_REPAIR_P,
    ALNS_SEGMENT_LENGTH,
    ALNS_SIGMA1,
    ALNS_SIGMA2,
    ALNS_SIGMA3,
    ALNS_START_TEMP_CONTROL,
)
from heuristics import HEURISTICS
from operators import DESTROY_OPERATORS, DESTROY_REGISTRY, repair


def _roulette_select(weights: dict, rng: random.Random):
    """R&P eq. 20: P(select j) = w_j / sum(w_i)."""
    threshold = rng.random() * sum(weights.values())
    cumulative = 0.0
    for name, weight in weights.items():
        cumulative += weight
        if cumulative >= threshold:
            return name
    return next(reversed(weights))  # floating-point guard


def _updated_weights(weights: dict, scores: dict, counts: dict, r: float) -> dict:
    """R&P §3.4: w_{i,j+1} = w_ij(1-r) + r*(pi_i/theta_i). An operator never selected
    this segment (theta_i = 0) keeps its weight — an edge case R&P leave unstated."""
    return {
        name: weight * (1 - r) + r * (scores[name] / counts[name]) if counts[name] else weight
        for name, weight in weights.items()
    }


def _zeroed(names) -> dict:
    return {name: 0 for name in names}


def run_alns(ctx, k: int, evaluator, seed: int, *, fixed_hop_scope: int = None) -> dict:
    """One ALNS search for a fixed (source, k).

    `ctx` is the SourceContext holding every precomputed per-source table; `evaluator`
    must be bound to the SAA scenario set, never the out-of-sample one (REPORT.md §7).

    `fixed_hop_scope` pins repair to a single hop layer instead of letting the scope
    wheel choose. That is the Level-2 ablation the thesis needs — hop0-only versus
    adaptive is how the claim gets tested rather than assumed (PLAN.md Phase 2).
    """
    rng = random.Random(seed)
    endpoints = ctx.endpoints

    # Candidate layers, capped (config.ALNS_MAX_HOP_SCOPE). Each layer's edge list is
    # static, so it is materialised once here and only the D-exclusion is per-iteration.
    if fixed_hop_scope is not None:
        scopes = [fixed_hop_scope]
    else:
        scopes = sorted(h for h in ctx.edges_by_hop if h <= ALNS_MAX_HOP_SCOPE)
    layer_edges = {h: list(ctx.edges_by_hop[h]) for h in scopes}
    fallback_edges = [eid for h in scopes for eid in layer_edges[h]]

    # Warm start: k random hop0 edges. Deliberately not heuristic-chosen — that would
    # hand the matching repair operator a built-in head start (PILOT_TESTS.md §32).
    #
    # k >= out_degree is not an error, just the trivial case: the budget can cut every
    # edge leaving the source, so the warm start does exactly that, isolating it. Any
    # remaining budget is topped up from the other layers to keep |D| = k, though those
    # edges are unreachable once the source is isolated (PILOT_TESTS.md §10).
    hop0 = ctx.edges_by_hop[0]
    if k >= len(hop0):
        current = set(hop0)
        spare = [e for h in scopes if h != 0 for e in layer_edges[h] if e not in current]
        current |= set(rng.sample(spare, min(k - len(current), len(spare))))
    else:
        current = set(rng.sample(hop0, k))

    current_reach = evaluator.evaluate_reach(ctx.source, current, endpoints)
    best, best_reach = set(current), current_reach

    temperature = ALNS_START_TEMP_CONTROL * current_reach / math.log(2)  # R&P §3.5
    cooling_rate = ALNS_FINAL_TEMP_FRACTION ** (1 / ALNS_MAX_ITER)

    destroy_weights = {name: 1.0 for name in DESTROY_OPERATORS}
    repair_weights = {name: 1.0 for name in HEURISTICS}
    scope_weights = {h: 1.0 for h in scopes}
    destroy_scores, destroy_counts = _zeroed(DESTROY_OPERATORS), _zeroed(DESTROY_OPERATORS)
    repair_scores, repair_counts = _zeroed(HEURISTICS), _zeroed(HEURISTICS)
    scope_scores, scope_counts = _zeroed(scopes), _zeroed(scopes)

    q_min = max(1, math.floor(ALNS_Q_MIN_FRAC * k))
    q_max = max(q_min, min(k - 1, math.floor(ALNS_Q_MAX_FRAC * k)))

    # sigma1 attribution. PILOT_TESTS.md §23 is explicit that final weights alone do NOT
    # license the claim "ALNS learns which criterion to use" — that needs per-heuristic
    # counts of who actually produced a new global best. Same for the scope wheel, which
    # is the Level-2 claim's evidence.
    best_hits_by_heuristic = _zeroed(HEURISTICS)
    best_hits_by_scope = _zeroed(scopes)
    best_hits_by_hop, neutral_moves = {}, _zeroed(HEURISTICS)
    trace = []

    # sigma >= 1 always (the source counts itself), so reach == 1 means the source is
    # fully cut off: the global optimum, provably, with nothing left to search for.
    stop_reason = "isolated" if best_reach <= 1.0 + 1e-9 else "max_iter"
    iteration = -1

    while stop_reason != "isolated" and iteration + 1 < ALNS_MAX_ITER:
        iteration += 1
        destroy_name = _roulette_select(destroy_weights, rng)
        repair_name = _roulette_select(repair_weights, rng)
        scope = _roulette_select(scope_weights, rng)

        released = DESTROY_REGISTRY[destroy_name](
            frozenset(current), rng.randint(q_min, q_max), ctx, evaluator, rng
        )
        partial = current - released
        wanted = len(released)

        # Repair draws from the chosen layer first; if that layer cannot supply enough
        # (small hop0, or most of it already cut) the remainder comes from the other
        # in-scope layers, so |D| = k always holds (PILOT_TESTS.md §10's fill rule).
        added = repair(repair_name, [e for e in layer_edges[scope] if e not in partial],
                        partial, wanted, ctx, rng, ALNS_REPAIR_P)
        if len(added) < wanted:
            spare = [e for e in fallback_edges if e not in partial and e not in added]
            added |= repair(repair_name, spare, partial | added, wanted - len(added),
                             ctx, rng, ALNS_REPAIR_P)
        candidate = partial | added

        # PILOT_TESTS.md B2: a short repair is a bug to surface, never a silent skip.
        assert len(candidate) == k or len(candidate) == len(current), (
            f"repair returned |D|={len(candidate)} != k={k} at hop scope {scope}"
        )

        already_visited = frozenset(candidate) in evaluator.cache
        candidate_reach = evaluator.evaluate_reach(ctx.source, candidate, endpoints)
        delta = candidate_reach - current_reach
        accepted = delta <= 0 or rng.random() < math.exp(-delta / temperature)

        is_new_best = candidate_reach < best_reach
        if is_new_best:
            reward = ALNS_SIGMA1
        elif already_visited:
            reward = 0
        elif candidate_reach < current_reach:
            reward = ALNS_SIGMA2
        elif candidate_reach > current_reach and accepted:
            reward = ALNS_SIGMA3
        else:
            reward = 0  # a tie is accepted but earns nothing
        if delta == 0:
            neutral_moves[repair_name] += 1

        for scores, counts, key in ((destroy_scores, destroy_counts, destroy_name),
                                     (repair_scores, repair_counts, repair_name),
                                     (scope_scores, scope_counts, scope)):
            scores[key] += reward
            counts[key] += 1

        if accepted:
            current, current_reach = candidate, candidate_reach
            if is_new_best:
                best, best_reach = set(candidate), candidate_reach
                best_hits_by_heuristic[repair_name] += 1
                best_hits_by_scope[scope] += 1
                for hop in {ctx.hop_of_edge[e] for e in added if e in ctx.hop_of_edge}:
                    best_hits_by_hop[hop] = best_hits_by_hop.get(hop, 0) + 1
                if best_reach <= 1.0 + 1e-9:
                    stop_reason = "isolated"  # provably optimal; stop rather than spin

        temperature *= cooling_rate

        if (iteration + 1) % ALNS_SEGMENT_LENGTH == 0:
            destroy_weights = _updated_weights(destroy_weights, destroy_scores,
                                                destroy_counts, ALNS_REACTION_FACTOR)
            repair_weights = _updated_weights(repair_weights, repair_scores,
                                               repair_counts, ALNS_REACTION_FACTOR)
            scope_weights = _updated_weights(scope_weights, scope_scores,
                                              scope_counts, ALNS_REACTION_FACTOR)
            trace.append({
                "segment": (iteration + 1) // ALNS_SEGMENT_LENGTH,
                "best_reach": best_reach,
                "destroy_weights": dict(destroy_weights),
                "repair_weights": dict(repair_weights),
                "scope_weights": dict(scope_weights),
            })
            destroy_scores, destroy_counts = _zeroed(DESTROY_OPERATORS), _zeroed(DESTROY_OPERATORS)
            repair_scores, repair_counts = _zeroed(HEURISTICS), _zeroed(HEURISTICS)
            scope_scores, scope_counts = _zeroed(scopes), _zeroed(scopes)

    # hop composition OF THE CUT, kept separate from the search-side hop statistics
    # above: PILOT_TESTS.md §23 warns explicitly not to conflate "which layer the search
    # visited" with "which layer the winning edges came from".
    hop_mix = {}
    for eid in best:
        hop = ctx.hop_of_edge.get(eid)
        hop_mix[hop] = hop_mix.get(hop, 0) + 1

    return {
        "best_cut": best,
        "best_reach_saa": best_reach,
        "stop_reason": stop_reason,
        "iterations_done": iteration + 1,
        "hop_mix": hop_mix,
        "scope_weights": scope_weights,
        "repair_weights": repair_weights,
        "destroy_weights": destroy_weights,
        "best_hits_by_heuristic": best_hits_by_heuristic,
        "best_hits_by_scope": best_hits_by_scope,
        "best_hits_by_hop": best_hits_by_hop,
        "neutral_moves": neutral_moves,
        "evaluations": len(evaluator.cache) if evaluator.cache is not None else None,
        "trace": trace,
    }
