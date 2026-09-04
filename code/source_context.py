"""Everything precomputed once for one source, consumed by heuristics, operators and
the ALNS loop.

This is the Parameter Object for the whole search: without it `run_alns` and every
operator need 8-9 loose arguments threaded through them. Built once per source, then
read-only.

All lookups are plain dicts, deliberately: the previous version scored candidates
straight off a pandas DataFrame with `.loc[eid]` per edge, which costs microseconds
*per element* and runs on pools of hundreds of edges every iteration. Flattening the
feature table into dicts once per source turns that into an O(1) hash lookup
(REPORT.md §8 — precompute once, never recompute in the loop).
"""

from dataclasses import dataclass

import numpy as np

import analyse_graph


@dataclass(frozen=True)
class SourceContext:
    source: int
    out_degree: int
    endpoints: dict      # eid -> (u, v)
    probability: dict    # eid -> transmission probability
    degree_sum: dict     # eid -> out(u) + out(v) on the base graph
    is_bridge: dict      # eid -> 1.0 if Granovetter local bridge else 0.0
    spectral: dict       # eid -> Tong's u(i)*v(j)
    betweenness: dict    # eid -> source-rooted Brandes score (0.0 if off every path)
    hop_of_edge: dict    # eid -> hop level of the edge's tail (reachable edges only)
    hop_of_node: dict    # node -> BFS hop from the source (R&P eq.17's time coordinate)
    edges_by_hop: dict   # hop -> [eid]
    hop_span: float      # max-min observed hop, for normalising relatedness
    territory: list      # node -> bounded descendant set (R&P eq.17's servable set K_i)


def verify_feature_alignment(g, features) -> None:
    """Structural guard, the counterpart to create_graph.verify_vertex_alignment: the
    feature table is keyed by `edge_id` and must line up with the graph's own edge
    indexing, row for row. Cheap enough (one pass over M edges) to run every time
    rather than trusting that whoever regenerated the CSV used the same graph.

    Vectorised deliberately: the obvious `features.loc[e.index]` per edge measured 2.3 s
    per source and was ~90% of the cost of building a SourceContext — the exact
    pandas-indexing-in-a-loop pattern REPORT.md §8 forbids in the hot path, which had no
    business being here either."""
    if len(features) != g.ecount():
        raise AssertionError(
            f"edge_features.csv has {len(features)} rows but the graph has "
            f"{g.ecount()} edges - regenerate it with analyse_graph.py."
        )
    rows = features.reindex(range(g.ecount()))
    if rows["source"].isna().any():
        missing = int(rows["source"].isna().to_numpy().argmax())
        raise AssertionError(
            f"edge_features.csv has no row for edge_id {missing} - its edge_id column "
            f"does not cover 0..{g.ecount() - 1}, regenerate it with analyse_graph.py."
        )
    names = g.vs["name"]
    edgelist = g.get_edgelist()
    expected_u = np.fromiter((names[u] for u, _ in edgelist), np.int64, len(edgelist))
    expected_v = np.fromiter((names[v] for _, v in edgelist), np.int64, len(edgelist))
    mismatch = ((rows["source"].to_numpy() != expected_u)
                | (rows["target"].to_numpy() != expected_v))
    if mismatch.any():
        i = int(mismatch.argmax())
        raise AssertionError(
            f"edge_features.csv row {i} is "
            f"({rows['source'].iloc[i]}->{rows['target'].iloc[i]}) but the graph's edge "
            f"{i} is ({expected_u[i]}->{expected_v[i]}) - stale CSV, regenerate it."
        )


def build_source_context(g, source: int, features) -> SourceContext:
    """One BFS-derived feature pass (analyse_graph.source_features) plus a flattening
    of the global feature table into dict lookups.

    Endpoints come from the graph (internal igraph vertex indices), NOT from
    edge_features.csv, whose `source`/`target` columns hold original SNAP user IDs for
    human-readable reporting. Scenarios, `hop_of_node` and the evaluator's stamp array
    are all indexed by internal vertex index, so mixing the two namespaces is exactly
    the index-misalignment bug class REPORT.md §4/§8a exists to prevent. Alignment on
    `edge_id` is safe: the CSV is written from `e.index` in analyse_graph.py.
    """
    verify_feature_alignment(g, features)

    sf = analyse_graph.source_features(g, source)
    hop_of_node = sf["hop_of_node"]

    endpoints = {e.index: (e.source, e.target) for e in g.es}
    hop_of_edge = {}
    for eid, (u, _v) in endpoints.items():
        hop = hop_of_node.get(u)
        if hop is not None:
            hop_of_edge[eid] = hop

    probability = features["probability"].to_dict()
    degree_sum = features["degree_sum"].to_dict()
    is_bridge = {eid: float(flag) for eid, flag in features["is_local_bridge"].items()}
    spectral = features["spectral_score"].to_dict()

    hops = hop_of_edge.values()
    hop_span = float(max(hops) - min(hops)) if hops else 0.0

    return SourceContext(
        source=source,
        out_degree=g.outdegree(source),
        endpoints=endpoints,
        probability=probability,
        degree_sum=degree_sum,
        is_bridge=is_bridge,
        spectral=spectral,
        betweenness=sf["betweenness"],
        hop_of_edge=hop_of_edge,
        hop_of_node=hop_of_node,
        edges_by_hop=sf["edges_by_hop"],
        hop_span=hop_span,
        # Source-independent, so rebuilding it per source is redundant work — but it
        # measures 0.23 s against ~45 s for one ALNS run, and keeping SourceContext
        # self-constructing is worth more than saving that. Hoist it to the caller only
        # if the source sample ever gets large enough for it to matter.
        territory=analyse_graph.node_territories(g),
    )
