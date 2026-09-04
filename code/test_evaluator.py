"""Regression tests for the objective function.

Everything the thesis reports rests on `Evaluator` computing sigma(s, G\\D) correctly,
and it is the one component written for speed rather than obviousness — a stamp array
instead of a visited set, a reused cut buffer, and a one-pass marginal computation
that skips work by reasoning about which edges *can* matter. Each of those is a place
a subtle error would silently change every number in the results chapter rather than
crash, so each is pinned here against an independent oracle.

Run directly: `python test_evaluator.py`
"""

import itertools
import random

import igraph as ig

import create_graph
import create_subgraphs
import heuristics
from evaluator import Evaluator
from source_context import build_source_context

ORACLE_SCENARIOS = 40
SOURCE_SNAP_ID = 1
K = 20
SEED = 7


def _fixture():
    g = create_graph.build_graph()
    source = g.vs["name"].index(SOURCE_SNAP_ID)
    scenarios = create_subgraphs.build_saa_scenarios(g)
    ctx = build_source_context(g, source, heuristics.load_global_features())
    cut = frozenset(random.Random(SEED).sample(ctx.edges_by_hop[0], K))
    return g, source, scenarios, ctx, cut


def test_matches_igraph_reachability(g, source, scenarios, ctx, cut):
    """Ground truth: rebuild each scenario as a real graph with the cut edges deleted
    and ask igraph for the reachable set. Independent of every optimisation we made."""
    cut_pairs = {ctx.endpoints[eid] for eid in cut}
    for index, adj in enumerate(scenarios[:ORACLE_SCENARIOS]):
        edges = [(u, v) for u in range(len(adj)) for v in adj[u] if (u, v) not in cut_pairs]
        oracle = len(ig.Graph(n=g.vcount(), edges=edges, directed=True)
                     .subcomponent(source, mode="out"))
        ours = Evaluator(g.vcount(), [adj], use_cache=False).evaluate_reach(
            source, cut, ctx.endpoints)
        assert ours == oracle, f"scenario {index}: ours={ours} igraph={oracle}"
    print(f"  reach matches igraph on {ORACLE_SCENARIOS} scenarios")


def test_marginals_match_naive(g, source, scenarios, ctx, cut):
    """The one-pass marginal computation must equal the naive |D|+1 sweeps it replaced."""
    evaluator = Evaluator(g.vcount(), scenarios)
    base, gains = evaluator.marginal_values(source, cut, ctx.endpoints)
    assert abs(base - evaluator.evaluate_reach(source, cut, ctx.endpoints)) < 1e-9
    for eid in itertools.islice(sorted(cut), 6):
        naive = evaluator.evaluate_reach(source, cut - {eid}, ctx.endpoints) - base
        assert abs(naive - gains[eid]) < 1e-9, f"edge {eid}: naive={naive} onepass={gains[eid]}"
    print("  one-pass marginals match the naive per-edge computation")


def test_cut_buffer_is_left_clean(g, source, scenarios, ctx, cut):
    """The cut mask is a reused buffer; a leaked entry would corrupt later evaluations
    silently rather than raising."""
    evaluator = Evaluator(g.vcount(), scenarios)
    evaluator.evaluate_reach(source, cut, ctx.endpoints)
    evaluator.marginal_values(source, cut, ctx.endpoints)
    assert all(entry is None for entry in evaluator._blocked), "cut buffer leaked state"
    print("  cut buffer is clean after both entry points")


def test_cutting_more_never_increases_reach(g, source, scenarios, ctx, cut):
    """Monotonicity: removing edges can only shrink reachability. Cheap invariant that
    would catch a masking error the oracle test might miss on its sampled scenarios."""
    evaluator = Evaluator(g.vcount(), scenarios)
    uncut = evaluator.evaluate_reach(source, frozenset(), ctx.endpoints)
    full = evaluator.evaluate_reach(source, cut, ctx.endpoints)
    subset = evaluator.evaluate_reach(source, frozenset(sorted(cut)[:K // 2]), ctx.endpoints)
    assert full <= subset <= uncut, f"not monotone: {full} !<= {subset} !<= {uncut}"
    print(f"  monotone in the cut: {full:.2f} <= {subset:.2f} <= {uncut:.2f}")


def test_cache_does_not_change_answers(g, source, scenarios, ctx, cut):
    cached = Evaluator(g.vcount(), scenarios, use_cache=True)
    uncached = Evaluator(g.vcount(), scenarios, use_cache=False)
    first = cached.evaluate_reach(source, cut, ctx.endpoints)
    assert first == cached.evaluate_reach(source, cut, ctx.endpoints)  # cache hit path
    assert first == uncached.evaluate_reach(source, cut, ctx.endpoints)
    print("  cached and uncached evaluators agree")


def test_cache_does_not_confuse_sources(g, source, scenarios, ctx, cut):
    """One evaluator, many sources — the shape run_experiment.py wants, since the
    scenario set is the expensive thing to build and the source is the cheap loop
    variable. Reach depends on both the source and the cut, so a cache keyed on the cut
    alone hands back the previous source's answer: measured at 41.10 for a source whose
    true reach is 643.63. It raises nothing and looks entirely plausible."""
    shared = Evaluator(g.vcount(), scenarios)
    for other in (774, 253, 3616):
        warm = shared.evaluate_reach(other, frozenset(), ctx.endpoints)
        cold = Evaluator(g.vcount(), scenarios).evaluate_reach(
            other, frozenset(), ctx.endpoints)
        assert warm == cold, (
            f"source {other}: shared evaluator gave {warm:.2f}, fresh one {cold:.2f} — "
            f"the cache is keyed on the cut without the source"
        )
        _, gains = shared.marginal_values(other, cut, ctx.endpoints)
        _, fresh_gains = Evaluator(g.vcount(), scenarios).marginal_values(
            other, cut, ctx.endpoints)
        assert gains == fresh_gains, f"source {other}: marginal cache collides too"
    print("  one evaluator across several sources agrees with per-source evaluators")


def test_scenario_sampler_matches_declared_probabilities(g, source, scenarios, ctx, cut):
    """PILOT_TESTS.md §36: check the realised edge-occupancy frequency across scenarios
    against each edge's declared probability. If the sampler drifts, every sigma in the
    thesis is wrong and nothing else would notice — this is the cheapest possible guard
    against that."""
    n = len(scenarios)
    occurrences = {}
    for adj in scenarios:
        for u, heads in enumerate(adj):
            for v in heads:
                occurrences[(u, v)] = occurrences.get((u, v), 0) + 1
    drift = []
    for eid, (u, v) in ctx.endpoints.items():
        drift.append(occurrences.get((u, v), 0) / n - ctx.probability[eid])
    mean_drift = sum(drift) / len(drift)
    worst = max(abs(d) for d in drift)
    # Mean drift is the sensitive statistic: per-edge noise is ~1/sqrt(n) by construction,
    # but a systematic bias would show up in the mean.
    assert abs(mean_drift) < 5e-3, f"sampler bias: mean realised-declared = {mean_drift:.2e}"
    print(f"  sampler unbiased: mean drift {mean_drift:+.2e}, worst edge {worst:.3f} "
          f"(per-edge noise ~{1/n**0.5:.3f} at n={n})")


if __name__ == "__main__":
    fixture = _fixture()
    print("evaluator regression tests")
    for test in (test_matches_igraph_reachability, test_marginals_match_naive,
                 test_cut_buffer_is_left_clean, test_cutting_more_never_increases_reach,
                 test_cache_does_not_change_answers,
                 test_cache_does_not_confuse_sources,
                 test_scenario_sampler_matches_declared_probabilities):
        test(*fixture)
    print("all passed")
