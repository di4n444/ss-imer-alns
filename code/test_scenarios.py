"""Regression tests for the frozen live-edge scenario sets.

PLAN.md Phase 1 lists these as smoke tests that must pass before Phase 2, and REPORT.md §7
states the property they defend: the SAA and MC sets are generated once and are immutable
afterwards, so evaluation always works on a mask, never on the scenario objects.

Both failure modes are silent. If generation is not reproducible from its seed, no run can
be compared with any other run — PILOT_TESTS.md §8 ("ne uspoređivati runove na različitim
in-sample scenarijima") and §24 ("promjena SAA/MC seeda invalidira sve σ"). If any code
path mutates a scenario, every sigma after that point is wrong and nothing raises. Neither
would be caught by the objective tests in test_evaluator.py, which check a single
evaluation against an oracle rather than the state shared across thousands of them.

Run directly: `python test_scenarios.py`
"""

import create_graph
import create_subgraphs
import heuristics
from alns_optimizer import run_alns
from config import (
    ALNS_RUN_SEED,
    MC_SCENARIO_COUNT,
    MC_SCENARIO_SEED,
    SAA_SCENARIO_COUNT,
    SAA_SCENARIO_SEED,
)
from evaluator import Evaluator
from greedy_baseline import run_greedy
from heuristics import HEURISTICS
from source_context import build_source_context

SOURCE = 774  # out-degree 6, sigma_0 ~ 41: cheap enough to run the whole search twice
K = 3


def _fingerprint(scenarios: list) -> list:
    """One hash per scenario, sensitive to adjacency *order* as well as content — the
    claim being defended is byte-for-byte reproducibility, not set equality. Built one
    scenario at a time so this never holds a second copy of the whole set."""
    return [hash(tuple(map(tuple, adj))) for adj in scenarios]


def test_generation_is_reproducible_from_its_seed(g, scenarios, ctx, evaluator):
    """Same seed, same scenarios, exactly. Without this, no two runs in the thesis are
    comparable and no result is reproducible from config.py alone."""
    again = create_subgraphs.generate_scenarios(g, SAA_SCENARIO_COUNT, SAA_SCENARIO_SEED)
    assert _fingerprint(again) == _fingerprint(scenarios), (
        "regenerating with the same seed produced different scenarios"
    )
    assert len(scenarios) == SAA_SCENARIO_COUNT
    print(f"  {SAA_SCENARIO_COUNT} SAA scenarios reproduce exactly from seed "
          f"{SAA_SCENARIO_SEED}")


def test_saa_and_mc_are_independent_draws(g, scenarios, ctx, evaluator):
    """The out-of-sample set has to be genuinely out of sample. A shared seed would make
    OOS validation measure nothing while looking like it passed (REPORT.md §7)."""
    assert SAA_SCENARIO_SEED != MC_SCENARIO_SEED, "SAA and MC share a seed"
    mc_head = create_subgraphs.generate_scenarios(g, 20, MC_SCENARIO_SEED)
    overlap = set(_fingerprint(mc_head)) & set(_fingerprint(scenarios))
    assert not overlap, f"{len(overlap)} MC scenarios are identical to SAA scenarios"
    print(f"  MC (seed {MC_SCENARIO_SEED}, n={MC_SCENARIO_COUNT}) shares no realization "
          f"with SAA (seed {SAA_SCENARIO_SEED})")


def test_a_full_search_does_not_mutate_the_scenarios(g, scenarios, ctx, evaluator):
    """The real guard. Run everything that touches the scenario set — every baseline, a
    complete ALNS search, and the marginal-value path that writes into the shared cut
    buffer — then check the scenarios are bit-identical. `Evaluator` applies the cut to a
    reusable `_blocked` list rather than to the adjacency, and this is what says so."""
    before = _fingerprint(scenarios)

    for name in HEURISTICS:
        run_greedy(ctx, name, K, evaluator, seed=ALNS_RUN_SEED)
    evaluator.marginal_values(ctx.source, frozenset(ctx.edges_by_hop[0][:K]), ctx.endpoints)
    run_alns(ctx, K, evaluator, ALNS_RUN_SEED)

    assert _fingerprint(scenarios) == before, "a scenario was mutated during the search"
    assert all(entry is None for entry in evaluator._blocked), "cut buffer leaked state"
    print(f"  {len(scenarios)} scenarios unchanged after 6 baselines + a full ALNS run")


def test_a_full_search_does_not_mutate_the_source_context(g, scenarios, ctx, evaluator):
    """SourceContext is frozen, but frozen only stops attribute rebinding — its dicts and
    lists stay mutable, and every operator reads them on every iteration. The candidate
    layers are the ones at risk, since `run_alns` filters them per iteration."""
    before = ({h: list(edges) for h, edges in ctx.edges_by_hop.items()},
              dict(ctx.hop_of_edge), dict(ctx.probability))
    run_alns(ctx, K, evaluator, ALNS_RUN_SEED + 1)
    after = ({h: list(edges) for h, edges in ctx.edges_by_hop.items()},
             dict(ctx.hop_of_edge), dict(ctx.probability))
    assert before == after, "the search mutated a shared per-source table"
    print("  edges_by_hop / hop_of_edge / probability unchanged after a search")


if __name__ == "__main__":
    print("frozen scenario tests")
    graph = create_graph.build_graph()
    saa = create_subgraphs.build_saa_scenarios(graph)
    context = build_source_context(graph, SOURCE, heuristics.load_global_features())
    ev = Evaluator(graph.vcount(), saa)
    for test in (test_generation_is_reproducible_from_its_seed,
                 test_saa_and_mc_are_independent_draws,
                 test_a_full_search_does_not_mutate_the_scenarios,
                 test_a_full_search_does_not_mutate_the_source_context):
        test(graph, saa, context, ev)
    print("all passed")
