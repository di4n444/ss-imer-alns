"""Load the Bitcoin Alpha trust network and build the directed IC graph.

Positive ratings only; each rating is mapped to an Independent Cascade
transmission probability via a sigmoid, p = 1 / (1 + exp(-(rating - 5))).
See PILOT_TESTS.md §12 and REPORT.md §1 for why this formula and this filter.

Vertex indexing: igraph.Graph.TupleList is intentionally not used (see
REPORT.md §8a) because it orders vertices by first-appearance in the edge
list, decoupled from any array built elsewhere. Instead vertices are added
in a single, explicit, sorted order, and every downstream consumer of a
numeric array (e.g. eigenvector components for the spectral heuristic) must
derive it from igraph's own index-ordered API (get_adjacency_sparse, etc.),
never rebuild a parallel array by hand.
"""

import math

import igraph as ig
import pandas as pd

from config import DUPLICATE_EDGE_POLICY, RAW_DATASET_COLUMNS, RAW_DATASET_PATH


def rating_to_probability(rating: float) -> float:
    """IC transmission probability from a Bitcoin Alpha rating (PILOT_TESTS.md §12)."""
    return 1.0 / (1.0 + math.exp(-(rating - 5.0)))


def load_ratings(path=RAW_DATASET_PATH) -> pd.DataFrame:
    """Read the raw CSV, keep positive ratings, resolve duplicate (source, target) edges."""
    df = pd.read_csv(path, header=None, names=RAW_DATASET_COLUMNS)
    df = df[df["rating"] > 0]

    if DUPLICATE_EDGE_POLICY != "latest":
        raise NotImplementedError(f"unknown DUPLICATE_EDGE_POLICY: {DUPLICATE_EDGE_POLICY!r}")
    df = (
        df.sort_values("time")
        .drop_duplicates(subset=["source", "target"], keep="last")
        .reset_index(drop=True)
    )
    return df


def verify_vertex_alignment(g: ig.Graph, node_ids: list) -> None:
    """Structural guard against the index-misalignment bug class (REPORT.md §4/§8a).

    Called every time the graph is constructed, not just once during testing.
    """
    if list(g.vs["name"]) != list(node_ids):
        raise AssertionError(
            "graph vertex order does not match the explicit node_ids list — "
            "never rebuild a parallel array independently of igraph's own index order."
        )


def build_graph(path=RAW_DATASET_PATH) -> ig.Graph:
    """Build the directed IC graph: nodes = users, edge attribute = transmission probability."""
    ratings = load_ratings(path)

    node_ids = sorted(set(ratings["source"]) | set(ratings["target"]))
    id_to_idx = {node_id: idx for idx, node_id in enumerate(node_ids)}

    g = ig.Graph(directed=True)
    g.add_vertices(len(node_ids))
    g.vs["name"] = node_ids
    verify_vertex_alignment(g, node_ids)

    edges = [(id_to_idx[s], id_to_idx[t]) for s, t in zip(ratings["source"], ratings["target"])]
    g.add_edges(edges)
    g.es["rating"] = ratings["rating"].tolist()
    g.es["probability"] = [rating_to_probability(r) for r in ratings["rating"]]

    return g


if __name__ == "__main__":
    g = build_graph()
    probs = g.es["probability"]
    sorted_p = sorted(probs)
    print(f"N = {g.vcount()}")
    print(f"M = {g.ecount()}")
    print(f"mean out-degree = {g.ecount() / g.vcount():.4f}")
    print(f"mean p = {sum(probs) / len(probs):.4f}")
    print(f"median p = {sorted_p[len(sorted_p) // 2]:.4f}")
