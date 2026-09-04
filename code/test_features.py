"""Regression tests for the spectral heuristic's index alignment.

PLAN.md Phase 1 lists this as a smoke test that must pass before Phase 2. It gets its own
file because the failure mode is uniquely nasty: the spectral score is the one feature
computed from a matrix rather than read off the graph, so a vertex-ordering mistake
produces plausible-looking numbers that are simply attached to the wrong edges. PILOT
§18 measured exactly that — Spearman(score, actual drop in lambda_max) was 0.15 before
the fix and 0.969 after — and PILOT §26 forbids citing any spectral number from a run
made before alignment was checked. Nothing crashes when this is wrong; one baseline and
one repair operator just quietly become noise.

Three independent angles, because "it looks aligned" is what the pilot bug also looked
like: the score must not depend on the order vertices happen to be added in, it must
actually predict what Tong's derivation says it predicts, and the CSV the pipeline reads
must still agree with a fresh computation from the graph.

Run directly: `python test_features.py`
"""

import random

import igraph as ig
import numpy as np
import scipy.sparse.linalg as spla
from scipy.stats import spearmanr

import analyse_graph
import create_graph
import heuristics

PERTURBATION_SAMPLE = 60  # edges per stratum for the eigenvalue-drop test
SEED = 7


def _leading_eigenvalue(g: ig.Graph, drop_edge: int = None) -> float:
    A = g.get_adjacency_sparse().asfptype()
    if drop_edge is not None:
        u, v = g.es[drop_edge].source, g.es[drop_edge].target
        A = A.tolil()
        A[u, v] = 0.0
        A = A.tocsr()
    return float(np.real(spla.eigs(A, k=1, which="LR", return_eigenvectors=False)[0]))


def test_score_is_independent_of_vertex_insertion_order(g, scores):
    """The structural test. Rebuild the same graph with vertices added in a different
    order, so every internal index changes while the named edges do not. A score keyed
    to the vertex *index* survives that; a score accidentally keyed to name order, or to
    a separately-built array, does not.

    This is the pilot's bug class stated as a property rather than as a number: it does
    not depend on knowing what the right answer is."""
    names = g.vs["name"]
    shuffled = list(names)
    random.Random(SEED).shuffle(shuffled)

    other = ig.Graph(directed=True)
    other.add_vertices(len(shuffled))
    other.vs["name"] = shuffled
    index_of = {name: i for i, name in enumerate(shuffled)}
    other.add_edges([(index_of[names[e.source]], index_of[names[e.target]]) for e in g.es])

    other_scores = analyse_graph.spectral_edge_scores(other)
    # Compare per named edge, which is the only identity the two graphs share.
    ours = {(names[e.source], names[e.target]): scores[e.index] for e in g.es}
    theirs = {(shuffled[e.source], shuffled[e.target]): other_scores[e.index]
              for e in other.es}
    assert set(ours) == set(theirs), "the two builds do not contain the same edges"

    keys = sorted(ours)
    a = np.array([ours[k] for k in keys])
    b = np.array([theirs[k] for k in keys])
    # Eigenvector scale is whatever the solver returns, so compare shape, not magnitude.
    ratio = b.sum() / a.sum()
    worst = float(np.max(np.abs(a * ratio - b)) / max(b.max(), 1e-12))
    assert worst < 1e-6, f"scores disagree across vertex orderings, worst rel. gap {worst:.2e}"
    print(f"  invariant to vertex insertion order (worst relative gap {worst:.1e})")


def test_score_predicts_the_eigenvalue_drop(g, scores):
    """The pilot's own diagnostic, reproduced. Tong et al. (2012) derive u_i*v_j as a
    first-order estimate of how much removing edge (i,j) lowers lambda_max, so the score
    must rank-correlate with the drop actually measured by deleting the edge and
    recomputing. Stratified over the score range rather than sampled uniformly, since a
    uniform sample of this graph is almost entirely near-zero scores and would measure
    nothing."""
    ranked = sorted(scores, key=scores.get, reverse=True)
    rng = random.Random(SEED)
    sample = (ranked[:PERTURBATION_SAMPLE]
              + rng.sample(ranked[PERTURBATION_SAMPLE:-PERTURBATION_SAMPLE],
                           PERTURBATION_SAMPLE)
              + ranked[-PERTURBATION_SAMPLE:])

    base = _leading_eigenvalue(g)
    drops = [base - _leading_eigenvalue(g, eid) for eid in sample]
    rho = spearmanr([scores[eid] for eid in sample], drops).statistic
    assert rho > 0.9, (
        f"Spearman(spectral score, measured drop in lambda_max) = {rho:.3f}; "
        f"PILOT_TESTS.md §18 saw 0.15 when the eigenvector was indexed by name order "
        f"and 0.969 once aligned. Anything low here means the score is on the wrong edges."
    )
    print(f"  predicts the lambda_max drop it claims to: Spearman {rho:.3f} "
          f"over {len(sample)} edges (pilot: 0.15 misaligned, 0.969 aligned)")


def test_csv_still_matches_a_fresh_computation(g, scores):
    """verify_feature_alignment checks that the CSV's endpoints line up with the graph.
    It cannot check that the *values* were computed from this graph — a stale CSV with
    correct endpoints would pass it. This closes that gap for the one column where a
    wrong value is invisible."""
    stored = heuristics.load_global_features()["spectral_score"]
    fresh = np.array([scores[eid] for eid in stored.index])
    stored = stored.to_numpy()
    ratio = stored.sum() / fresh.sum()
    worst = float(np.max(np.abs(fresh * ratio - stored)) / max(abs(stored).max(), 1e-12))
    assert worst < 1e-6, (
        f"edge_features.csv's spectral_score disagrees with a fresh computation "
        f"(worst relative gap {worst:.2e}) - regenerate it with analyse_graph.py."
    )
    print(f"  edge_features.csv matches a fresh computation (worst gap {worst:.1e})")


if __name__ == "__main__":
    print("spectral alignment tests")
    graph = create_graph.build_graph()
    edge_scores = analyse_graph.spectral_edge_scores(graph)
    for test in (test_score_is_independent_of_vertex_insertion_order,
                 test_score_predicts_the_eigenvalue_drop,
                 test_csv_still_matches_a_fresh_computation):
        test(graph, edge_scores)
    print("all passed")
