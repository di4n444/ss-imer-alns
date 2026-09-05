"""ALNS main loop: roulette-wheel operator selection, R&P's (2006) adaptive weight
update, simulated-annealing acceptance, and the hop-scope mechanism.

Faithful to R&P for everything they specify: independent roulette
wheels per operator family (eq. 20), the sigma1/sigma2/sigma3 score system with its
"only reward unvisited solutions" rule, the segment-end weight update
w' = w(1-r) + r*(score/count), and SA acceptance with a start temperature calibrated
from the initial solution.

Three deliberate departures:
  - the cooling rate is derived from *our* iteration budget rather than copying R&P's
    c=0.99975, which only makes sense against their 25000-iteration runs;
  - the hop scope is our own addition — R&P have no notion of a restricted candidate
    neighbourhood — implemented as a *third weight book* over hop layers rather than an
    expanding horizon, because the horizon version was measured to wreck the search
. It is scored by R&P's own attribution rule (§3.4: every mechanism
    involved in a success gets the same increment, because you cannot tell which one
    caused it), applied to the layers that actually supplied the new edges;
  - Delta = 0 is accepted but scores nothing, which is what a strict reading of R&P's
    three sigma cases already implies.
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


def run_alns(ctx, k: int, evaluator, seed: int, *, fixed_hop_scope: int = None,
             max_iter: int = ALNS_MAX_ITER,
             segment_length: int = ALNS_SEGMENT_LENGTH,
             repair_p: float = ALNS_REPAIR_P,
             q_min_frac: float = ALNS_Q_MIN_FRAC,
             q_max_frac: float = ALNS_Q_MAX_FRAC,
             reaction_factor: float = ALNS_REACTION_FACTOR,
             max_hop_scope: int = ALNS_MAX_HOP_SCOPE) -> dict:
    """One ALNS search for a fixed (source, k).

    `ctx` is the SourceContext holding every precomputed per-source table; `evaluator`
    must be bound to the SAA scenario set, never the out-of-sample one.

    `fixed_hop_scope` pins repair to a single hop layer instead of letting the scope
    wheel choose. Kept as a diagnostic knob; not part of the experiment matrix
.

    Every tunable parameter is a keyword argument defaulting to its config value, so a
    calibration variant is an *override* rather than a separate code path, and the
    resolved values come back in the result under `params` to be written into the same
    CSV row as the numbers they produced. Nothing may reach into
    config to change behaviour behind the caller's back.
    """
    rng = random.Random(seed)
    endpoints = ctx.endpoints

    # Candidate layers, capped at `max_hop_scope`. Each layer's edge list is
    # static, so it is materialised once here and only the D-exclusion is per-iteration.
    if fixed_hop_scope is not None:
        if fixed_hop_scope not in ctx.edges_by_hop:
            raise ValueError(
                f"source {ctx.source} has no hop{fixed_hop_scope} layer to pin repair to; "
                f"available layers: {sorted(ctx.edges_by_hop)}"
            )
        scopes = [fixed_hop_scope]
    else:
        scopes = sorted(h for h in ctx.edges_by_hop if h <= max_hop_scope)
    layer_edges = {h: list(ctx.edges_by_hop[h]) for h in scopes}
    fallback_edges = [eid for h in scopes for eid in layer_edges[h]]

    # Warm start: k random hop0 edges. Deliberately not heuristic-chosen — that would
    # hand the matching repair operator a built-in head start.
    #
    # k >= out_degree is not an error, just the trivial case: the budget can cut every
    # edge leaving the source, so the warm start does exactly that, isolating it. Any
    # remaining budget is topped up from the other layers to keep |D| = k, though those
    # edges are unreachable once the source is isolated.
    #
    # A source with out-degree 0 (411 of Bitcoin Alpha's 3683 nodes) has no hop0 layer at
    # all: sigma = 1 with an empty cut, so it is the isolated case too, handled rather
    # than crashed. Such sources still do not belong in a measurement sample.
    hop0 = ctx.edges_by_hop.get(0, [])
    if k >= len(hop0):
        current = set(hop0)
        spare = [e for h in scopes if h != 0 for e in layer_edges[h] if e not in current]
        current |= set(rng.sample(spare, min(k - len(current), len(spare))))
    else:
        current = set(rng.sample(hop0, k))

    current_reach = evaluator.evaluate_reach(ctx.source, current, endpoints)
    best, best_reach = set(current), current_reach

    # R&P's "only reward unvisited solutions" rule needs the set of solutions *this run*
    # has seen. Deliberately not `evaluator.cache`: that is per-evaluator, so reusing one
    # evaluator across k values or seeds (which run_experiment.py will want to do, since
    # the scenario set is the expensive thing to build) would leak one run's visited
    # solutions into the next run's rewards and make `evaluations` cumulative rather than
    # per-run. It also raised TypeError outright on a use_cache=False evaluator.
    visited = {frozenset(current)}

    temperature = ALNS_START_TEMP_CONTROL * current_reach / math.log(2)  # R&P §3.5
    cooling_rate = ALNS_FINAL_TEMP_FRACTION ** (1 / max_iter)

    destroy_weights = {name: 1.0 for name in DESTROY_OPERATORS}
    repair_weights = {name: 1.0 for name in HEURISTICS}
    scope_weights = {h: 1.0 for h in scopes}
    destroy_scores, destroy_counts = _zeroed(DESTROY_OPERATORS), _zeroed(DESTROY_OPERATORS)
    repair_scores, repair_counts = _zeroed(HEURISTICS), _zeroed(HEURISTICS)
    scope_scores, scope_counts = _zeroed(scopes), _zeroed(scopes)

    # At k=1 these collapse to q = 1 = |D|: destroy empties the cut and repair rebuilds it
    # from nothing, so the search degenerates to a memoryless random restart with no
    # neighbourhood structure at all. k=2 and k=3 give q=1, a 1-swap. Both are correct, but neither is "adaptive" in any strong
    # sense, so results at those budgets must be read with that in mind — hence q_min/q_max
    # are returned with the run rather than left implicit.
    q_min = max(1, math.floor(q_min_frac * k))
    q_max = max(q_min, min(k - 1, math.floor(q_max_frac * k)))

    # sigma1 attribution. Final weights alone do NOT
    # license the claim "ALNS learns which criterion to use" — that needs per-heuristic
    # counts of who actually produced a new global best. Same for the scope wheel, which
    # is the Level-2 claim's evidence.
    best_hits_by_heuristic = _zeroed(HEURISTICS)
    # `best_hits_by_scope` stays a *selection* statistic (which layer the wheel picked
    # when a new best landed); `best_hits_by_hop` is the *origin* statistic (which layer
    # the winning edges came from). They coincide whenever repair is served entirely by
    # the chosen layer, and the two questions must
    # not be conflated, so both are kept. `scope_selected` is the denominator for
    # reading either against how often the wheel actually chose that layer.
    best_hits_by_scope = _zeroed(scopes)
    scope_selected = _zeroed(scopes)
    # Iterations where the chosen layer could not supply q candidates and the remainder
    # came from other layers. The scope *score* follows the edges' actual origin, so the
    # learning is unaffected — but `best_hits_by_scope` still keys on the selected layer,
    # so a non-zero count here means that one statistic is mixing layers and only
    # `best_hits_by_hop` should be read as Level-2 evidence. Counted rather than assumed
    # away: the algebra says it can never fire (|hop0| > k in every non-isolated run, and
    # `partial` holds only k-q edges, so the chosen layer always has at least
    # |hop0|-k+q > q candidates left), but that is an argument, not a measurement.
    fallback_used = _zeroed(scopes)
    best_hits_by_hop, neutral_moves = {}, _zeroed(HEURISTICS)
    trace = []

    # sigma >= 1 always (the source counts itself), so reach == 1 means the source is
    # fully cut off: the global optimum, provably, with nothing left to search for.
    stop_reason = "isolated" if best_reach <= 1.0 + 1e-9 else "max_iter"
    iteration = -1

    while stop_reason != "isolated" and iteration + 1 < max_iter:
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
        # in-scope layers, so |D| = k always holds.
        added = repair(repair_name, [e for e in layer_edges[scope] if e not in partial],
                        wanted, ctx, rng, repair_p)
        if len(added) < wanted:
            spare = [e for e in fallback_edges if e not in partial and e not in added]
            added |= repair(repair_name, spare, wanted - len(added), ctx, rng, repair_p)
            fallback_used[scope] += 1
        candidate = partial | added

        # A short repair is a bug to surface, never a silent skip.
        # |current| is invariably k inside this loop (the k >= |hop0| branch is isolated
        # and never enters it), so this is the full guard, not a weakened one.
        assert len(candidate) == k, (
            f"repair returned |D|={len(candidate)} != k={k} at hop scope {scope}"
        )

        candidate_key = frozenset(candidate)
        already_visited = candidate_key in visited
        candidate_reach = evaluator.evaluate_reach(ctx.source, candidate, endpoints)
        visited.add(candidate_key)
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

        # The scope wheel is scored by where the new edges actually CAME FROM, not by
        # which layer was selected — a layer only earns credit for edges it supplied.
        # When repair spans layers, every contributing layer gets the full reward, which
        # is R&P's own rule for an unattributable success: "The scores for both
        # heuristics are updated by the same amount as we can not tell whether it was the
        # removal or the insertion that was the reason for the 'success'" (§3.4). Splitting
        # the reward proportionally would be our invention, and would additionally assume
        # sigma is divisible across the edges of a cut — exactly the non-submodularity the
        # thesis argues against.
        origins = {ctx.hop_of_edge[e] for e in added}
        for scores, counts, keys in ((destroy_scores, destroy_counts, (destroy_name,)),
                                      (repair_scores, repair_counts, (repair_name,)),
                                      (scope_scores, scope_counts, origins)):
            for key in keys:
                scores[key] += reward
                counts[key] += 1
        scope_selected[scope] += 1

        if accepted:
            current, current_reach = candidate, candidate_reach
            if is_new_best:
                best, best_reach = set(candidate), candidate_reach
                best_hits_by_heuristic[repair_name] += 1
                best_hits_by_scope[scope] += 1
                for hop in {ctx.hop_of_edge[e] for e in added}:
                    best_hits_by_hop[hop] = best_hits_by_hop.get(hop, 0) + 1
                if best_reach <= 1.0 + 1e-9:
                    stop_reason = "isolated"  # provably optimal; stop rather than spin

        temperature *= cooling_rate

        if (iteration + 1) % segment_length == 0:
            destroy_weights = _updated_weights(destroy_weights, destroy_scores,
                                                destroy_counts, reaction_factor)
            repair_weights = _updated_weights(repair_weights, repair_scores,
                                               repair_counts, reaction_factor)
            scope_weights = _updated_weights(scope_weights, scope_scores,
                                              scope_counts, reaction_factor)
            trace.append({
                "segment": (iteration + 1) // segment_length,
                "best_reach": best_reach,
                "destroy_weights": dict(destroy_weights),
                "repair_weights": dict(repair_weights),
                "scope_weights": dict(scope_weights),
            })
            destroy_scores, destroy_counts = _zeroed(DESTROY_OPERATORS), _zeroed(DESTROY_OPERATORS)
            repair_scores, repair_counts = _zeroed(HEURISTICS), _zeroed(HEURISTICS)
            scope_scores, scope_counts = _zeroed(scopes), _zeroed(scopes)

    # hop composition OF THE CUT, kept separate from the search-side hop statistics
    # above: do not conflate "which layer the search
    # visited" with "which layer the winning edges came from".
    # Every candidate edge comes from `edges_by_hop`, whose domain is exactly
    # `hop_of_edge`'s, so a direct lookup is correct and a KeyError here would be a real
    # invariant violation worth raising rather than a None column worth hiding.
    hop_mix = {}
    for eid in best:
        hop = ctx.hop_of_edge[eid]
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
        "scope_selected": scope_selected,
        "neutral_moves": neutral_moves,
        "fallback_used": fallback_used,
        "layer_sizes": {h: len(layer_edges[h]) for h in scopes},
        "q_bounds": (q_min, q_max),
        "evaluations": len(visited),
        "trace": trace,
        # Every resolved parameter travels with the numbers it produced, so a CSV row is
        # self-describing and a variant can never be confused with a default
        #.
        "params": {
            "max_iter": max_iter,
            "segment_length": segment_length,
            "repair_p": repair_p,
            "q_min_frac": q_min_frac,
            "q_max_frac": q_max_frac,
            "reaction_factor": reaction_factor,
            "max_hop_scope": max_hop_scope,
            "fixed_hop_scope": fixed_hop_scope,
        },
    }
