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
    edges_by_hop: dict   # hop -> [eid]
    hop_span: float      # max-min observed hop, for normalising relatedness


def verify_feature_alignment(g, features) -> None:
    """Structural guard, the counterpart to create_graph.verify_vertex_alignment: the
    feature table is keyed by `edge_id` and must line up with the graph's own edge
    indexing, row for row. Cheap enough (one pass over M edges) to run every time
    rather than trusting that whoever regenerated the CSV used the same graph."""
    if len(features) != g.ecount():
        raise AssertionError(
            f"edge_features.csv has {len(features)} rows but the graph has "
            f"{g.ecount()} edges - regenerate it with analyse_graph.py."
        )
    names = g.vs["name"]
    for e in g.es:
        row = features.loc[e.index]
        if row.source != names[e.source] or row.target != names[e.target]:
            raise AssertionError(
                f"edge_features.csv row {e.index} is ({row.source}->{row.target}) but "
                f"the graph's edge {e.index} is "
                f"({names[e.source]}->{names[e.target]}) - stale CSV, regenerate it."
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
        edges_by_hop=sf["edges_by_hop"],
        hop_span=hop_span,
    )
