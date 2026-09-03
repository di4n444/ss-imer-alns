"""Strategy layer: six edge-scoring heuristics, consumed identically by greedy
baselines and ALNS operators (REPORT.md §2). Scores are precomputed lookups only —
no graph traversal here (REPORT.md §8). Also the shared selection mechanism used by
both callers: deterministic top-k for baselines, R&P's rank-biased y^p sampling
(with a tie-shuffle pre-step) for ALNS operators (REPORT.md §3, §7a).
"""

import random

import pandas as pd

from config import DATA_DIR

HEURISTICS = ["random", "probability", "degree", "bridge", "betweenness", "spectral"]


def load_global_features() -> pd.DataFrame:
    """Static, source-independent features computed once by analyse_graph.py."""
    df = pd.read_csv(DATA_DIR / "edge_features.csv")
    return df.set_index("edge_id")


def endpoints_lookup(features: pd.DataFrame) -> dict:
    """edge_id -> (source, target), for the deterministic baseline tie-break."""
    return {eid: (row.source, row.target) for eid, row in features.iterrows()}


def active_pool(edges_by_hop: dict, max_hop: int, exclude: set = None) -> list:
    """Union of edges_by_hop[0..max_hop] (analyse_graph.py's per-source feature),
    optionally minus `exclude` (typically the current D). This is what turns the
    ALNS loop's `active_max_hop` state into an actual candidate list — used by
    `operators.py`'s repair (exclude=D) and `greedy_baseline.py` (max_hop=0, no
    exclude needed since baselines don't grow a set)."""
    pool = [eid for h in range(max_hop + 1) for eid in edges_by_hop.get(h, [])]
    if exclude:
        pool = [eid for eid in pool if eid not in exclude]
    return pool


def build_edge_meta(features: pd.DataFrame, hop_of_node: dict) -> dict:
    """edge_id -> {source, target, probability, hop}, assembled from the global
    features table plus one source's hop-distance feature. `hop` is the tail node's
    hop level (None if unreachable from this source) — used by `destroy_related`'s
    relatedness measure in operators.py."""
    return {
        eid: {
            "source": row.source,
            "target": row.target,
            "probability": row.probability,
            "hop": hop_of_node.get(row.source),
        }
        for eid, row in features.iterrows()
    }


def edge_scores(heuristic: str, features: pd.DataFrame, edge_ids, source_features=None,
                 rng: random.Random = None) -> dict:
    """{edge_id: score} for `heuristic`, restricted to `edge_ids`. Higher = more
    preferred (both for "greedy picks this" and "operator biases toward this")."""
    edge_ids = list(edge_ids)
    if heuristic == "random":
        r = rng or random.Random()
        return {eid: r.random() for eid in edge_ids}
    if heuristic == "probability":
        col = features["probability"]
    elif heuristic == "degree":
        col = features["degree_sum"]
    elif heuristic == "bridge":
        col = features["is_local_bridge"].astype(float)
    elif heuristic == "spectral":
        col = features["spectral_score"]
    elif heuristic == "betweenness":
        if source_features is None:
            raise ValueError("betweenness heuristic requires source_features")
        bc = source_features["betweenness"]
        return {eid: bc.get(eid, 0.0) for eid in edge_ids}
    else:
        raise ValueError(f"unknown heuristic: {heuristic}")
    return {eid: float(col.loc[eid]) for eid in edge_ids}


def rank(edge_ids, scores: dict, endpoints: dict, rng: random.Random = None) -> list:
    """Sort edge_ids by (score desc, then u asc/v asc if rng is None — deterministic
    baseline rule — else shuffled first, so Python's stable sort preserves random
    order within tied-score groups — the ALNS operator sampler). REPORT.md §3/§7a."""
    ids = list(edge_ids)
    if rng is None:
        return sorted(ids, key=lambda e: (-scores[e], endpoints[e][0], endpoints[e][1]))
    rng.shuffle(ids)
    return sorted(ids, key=lambda e: -scores[e])


def pick_biased(ranked_ids: list, rng: random.Random, p: float):
    """Rospke & Pisinger (2006) Algorithm 2/3: draw y~Uniform[0,1), return
    ranked_ids[floor(y**p * len(ranked_ids))]. Larger p -> more greedy (biased toward
    the top of the ranking); p -> 0 approaches uniform random choice. REPORT.md §6a."""
    y = rng.random()
    idx = min(int((y**p) * len(ranked_ids)), len(ranked_ids) - 1)
    return ranked_ids[idx]


def select_q(edge_ids, scores: dict, endpoints: dict, q: int, rng: random.Random,
             p: float) -> list:
    """Iteratively pick q edges via the rank-biased mechanism above, one at a time
    (matching R&P's Algorithms 2/3 loop structure) — used by ALNS destroy/repair."""
    remaining = list(edge_ids)
    chosen = []
    for _ in range(q):
        if not remaining:
            break
        ranked = rank(remaining, scores, endpoints, rng=rng)
        pick = pick_biased(ranked, rng, p)
        chosen.append(pick)
        remaining.remove(pick)
    return chosen


def topk(edge_ids, scores: dict, endpoints: dict, k: int, rng: random.Random = None) -> list:
    """Batch top-k: deterministic for baselines (rng=None), tie-shuffled otherwise."""
    return rank(edge_ids, scores, endpoints, rng=rng)[:k]


def tie_group_sizes(edge_ids, scores: dict) -> list:
    """Diagnostic: sizes of groups sharing an identical score, for REPORT.md §3's
    tie-frequency reporting requirement. Not wired into the hot path — call
    separately when logging."""
    from collections import Counter

    counts = Counter(scores[e] for e in edge_ids)
    return sorted(counts.values(), reverse=True)
