"""Strategy layer: the six edge-scoring heuristics, plus the one selection mechanism
shared by greedy baselines and ALNS operators.

Scores are O(1) dict lookups into `SourceContext`'s precomputed tables — no graph
traversal and no pandas indexing in the hot path.

Selection has exactly two modes, and they must never drift apart:
  - baselines are a deterministic *rule*   -> `topk(..., rng=None)`
  - ALNS operators are a *sampler*         -> `select_q(..., rng=<seeded Random>)`
The sampler is R&P (2006) Algorithm 2/3's y^p rank-biased draw, on a ranking whose
tied groups have been shuffled first — the tie-shuffle is our addition, because
several of our heuristics are heavily tied (bridge is binary, probability takes 10
values) where R&P's continuous VRP costs essentially never tie.
"""

import random

import pandas as pd

from config import DATA_DIR

HEURISTICS = ["random", "probability", "degree", "bridge", "betweenness", "spectral"]

# heuristic name -> the SourceContext table it reads. "random" is special-cased.
_SCORE_TABLE = {
    "probability": "probability",
    "degree": "degree_sum",
    "bridge": "is_bridge",
    "betweenness": "betweenness",
    "spectral": "spectral",
}


def load_global_features() -> pd.DataFrame:
    """Static, source-independent edge features computed once by analyse_graph.py."""
    return pd.read_csv(DATA_DIR / "edge_features.csv").set_index("edge_id")


def edge_scores(heuristic: str, ctx, edge_ids, rng: random.Random = None) -> dict:
    """{edge_id: score} for `heuristic` over `edge_ids`. Higher = more preferred,
    uniformly for every heuristic, so callers never need to know the direction."""
    if heuristic == "random":
        # No fall back to the global `random` module: every stochastic step must come
        # from the run's own seeded Random so runs stay independently reproducible
        #.
        if rng is None:
            raise ValueError("the 'random' heuristic needs the run's seeded rng")
        return {eid: rng.random() for eid in edge_ids}
    try:
        table = getattr(ctx, _SCORE_TABLE[heuristic])
    except KeyError:
        raise ValueError(f"unknown heuristic: {heuristic}") from None
    return {eid: table.get(eid, 0.0) for eid in edge_ids}


def rank(edge_ids, scores: dict, endpoints: dict, rng: random.Random = None) -> list:
    """Order candidates best-first.

    `rng=None` is the deterministic baseline rule: score desc, then (u, v) ascending.
    With an rng, a random second key breaks ties uniformly — equivalent to shuffling
    before a stable sort, but one pass instead of two, and `random()` is far cheaper
    than the `_randbelow` draws `random.shuffle` needs (profiling put that shuffle at
    4% of total runtime, on pools of thousands once the hop horizon widens)."""
    if rng is None:
        return sorted(edge_ids, key=lambda e: (-scores[e], endpoints[e][0], endpoints[e][1]))
    draw = rng.random
    return sorted(edge_ids, key=lambda e: (-scores[e], draw()))


def biased_index(n: int, rng: random.Random, p: float) -> int:
    """R&P (2006) Algorithms 2/3: draw y~U[0,1), take index floor(y**p * n). Larger p
    biases harder toward the top of the ranking; p=1 is a uniform draw. Single home
    for the formula — both selection paths use it."""
    return min(int((rng.random() ** p) * n), n - 1)


def select_q(edge_ids, scores: dict, endpoints: dict, q: int, rng: random.Random,
             p: float) -> list:
    """Pick q edges by repeated rank-biased draws from one ranking.

    The ranking is built once, not per pick. Every caller here scores *statically*
    (repair heuristics; worst-removal marginal values), so the order between picks
    only ever loses the item just taken — re-sorting the whole pool each time cost
    O(q · n log n) for no behavioural gain, and the pool reaches thousands of edges
    once the hop horizon widens. R&P's Shaw removal genuinely must re-rank, because
    its relatedness is measured against the growing chosen set; that one keeps its own
    dynamic loop in operators.py."""
    ranked = rank(edge_ids, scores, endpoints, rng=rng)
    return [ranked.pop(biased_index(len(ranked), rng, p))
            for _ in range(min(q, len(ranked)))]


def topk(edge_ids, scores: dict, endpoints: dict, k: int, rng: random.Random = None) -> list:
    """Batch top-k: the deterministic baseline path when rng is None."""
    return rank(edge_ids, scores, endpoints, rng=rng)[:k]


def tie_group_sizes(edge_ids, scores: dict) -> list:
    """Diagnostic for tie-frequency reporting: sizes of
    groups sharing an identical score, largest first. Called from measurement code,
    never from the hot path."""
    from collections import Counter

    return sorted(Counter(scores[e] for e in edge_ids).values(), reverse=True)
