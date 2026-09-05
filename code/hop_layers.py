"""Candidate-pool size per hop layer, for the sampled sources -> data/hop_layers.csv.

The thesis states a bound on how deep the search looks (config.ALNS_MAX_HOP_SCOPE) and
has to justify it from the graph rather than assert it. Two facts decide the question and
both are measured here:

  * how fast a layer grows relative to the one before it, which is what makes the same
    rank-biased draw mean different things in different layers;
  * what share of the edges reachable from the source layers 0..MAX already cover, which
    is what says whether a deeper layer would add candidates at all.

One BFS per source, so this is cheap; it is a separate script only because it answers a
question about the search space rather than about the graph or about one source's reach.
"""

import pandas as pd

import analyse_graph
import create_graph
from config import ALNS_MAX_HOP_SCOPE, DATA_DIR


def layer_sizes(g, source: int) -> dict:
    """{hop: number of candidate edges in that layer} for one source."""
    features = analyse_graph.source_features(g, source)
    return {hop: len(edges) for hop, edges in features["edges_by_hop"].items()}


def main():
    g = create_graph.build_graph()
    sample = pd.read_csv(DATA_DIR / "sample.csv")

    rows = []
    for _, row in sample.iterrows():
        sizes = layer_sizes(g, int(row.source))
        reachable = sum(sizes.values())
        within = sum(n for hop, n in sizes.items() if hop <= ALNS_MAX_HOP_SCOPE)
        rows.append({
            "source": int(row.source),
            "role": row.role,
            "cell": row.cell,
            "out_degree": int(row.out_degree),
            "deepest_hop": max(sizes),
            "reachable_edges": reachable,
            "edges_within_max_scope": within,
            "share_within_max_scope": within / reachable if reachable else float("nan"),
            **{f"hop{hop}": sizes.get(hop, 0) for hop in range(ALNS_MAX_HOP_SCOPE + 2)},
        })

    frame = pd.DataFrame(rows).sort_values(["role", "source"]).reset_index(drop=True)
    frame.to_csv(DATA_DIR / "hop_layers.csv", index=False)
    print(f"wrote {len(frame)} rows to data/hop_layers.csv\n")

    share = frame.share_within_max_scope
    print(f"layers 0..{ALNS_MAX_HOP_SCOPE} cover {share.min():.4f}-{share.max():.4f} "
          f"of every source's reachable edges (median {share.median():.4f})")
    print(f"deepest layer that exists at all: {frame.deepest_hop.max()}")
    print("\nmedian layer size:")
    for hop in range(ALNS_MAX_HOP_SCOPE + 2):
        column = frame[f"hop{hop}"]
        print(f"  hop{hop}: median {column.median():>8.0f}   "
              f"range {column.min():>6}-{column.max():>6}")
    return frame


if __name__ == "__main__":
    main()
