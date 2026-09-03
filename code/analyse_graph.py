"""Topology characterization (thesis Ch. 2) and precomputed heuristic feature tables.

Two jobs, both write CSVs, nothing printed-only (PLAN.md Phase 1):

1. Topology numbers for the thesis: small-world/scale-free evidence vs. a directed ER
   null model, spectral epidemic threshold, bow-tie decomposition, k-core, Louvain
   (descriptive only — REPORT.md §2), assortativity.
2. Precomputed heuristic feature tables (REPORT.md §8): global, source-independent
   features (degree-sum, Granovetter local bridge, spectral edge score) computed once
   for the whole graph; per-source features (hop-distance-from-source, source-rooted
   betweenness) computed once per source and reused across every k/method/ALNS
   iteration for that source — never recomputed inside the ALNS loop.
"""

import collections
import random

import igraph as ig
import numpy as np
import pandas as pd
import powerlaw
import scipy.sparse.linalg as spla

from config import DATA_DIR, ER_NULL_MODEL_SEED, LOUVAIN_RESTART_SEEDS
from create_graph import build_graph


# --------------------------------------------------------------------------
# 1. Topology chapter numbers
# --------------------------------------------------------------------------


def small_world_stats(g: ig.Graph) -> dict:
    """Average path length, diameter, and clustering vs. a directed ER null model with
    the same N, M. One ER instance is reused for every comparison so "the ER null model"
    is a consistent single object, not a fresh random graph per statistic.

    `unconn=True` averages geodesics within components only (standard for real networks
    that aren't fully connected) — same convention applied to both g and the ER null so
    the comparison is fair.
    """
    n, m = g.vcount(), g.ecount()
    random.seed(ER_NULL_MODEL_SEED)
    er = ig.Graph.Erdos_Renyi(n=n, m=m, directed=True)
    return {
        "path_length": g.average_path_length(directed=True, unconn=True),
        "path_length_er": er.average_path_length(directed=True, unconn=True),
        "diameter": g.diameter(directed=True, unconn=True),
        "diameter_er": er.diameter(directed=True, unconn=True),
        "clustering": g.as_undirected(mode="collapse").transitivity_undirected(mode="zero"),
        "clustering_er": er.as_undirected(mode="collapse").transitivity_undirected(mode="zero"),
    }


def degree_heterogeneity(g: ig.Graph) -> dict:
    """kappa = <k^2>/<k>^2 on degrees k>0, in- and out- separately.

    PILOT_TESTS.md §13 flags kappa alone as NOT the epidemic threshold (that's
    spectral_threshold above) - this is reported only as a heterogeneity descriptor.
    """
    out_deg = np.array(g.outdegree())
    in_deg = np.array(g.indegree())
    in_nz = in_deg[in_deg > 0]
    return {
        "kappa_out": float((out_deg**2).mean() / out_deg.mean() ** 2),
        "kappa_in": float((in_nz**2).mean() / in_nz.mean() ** 2),
    }


def probability_stats(g: ig.Graph) -> dict:
    p = np.array(g.es["probability"])
    return {
        "p_mean": float(p.mean()),
        "p_median": float(np.median(p)),
        "p_std": float(p.std()),
        "p_min": float(p.min()),
        "p_max": float(p.max()),
    }


def bow_tie_full(g: ig.Graph) -> dict:
    """Full bow-tie decomposition relative to the giant SCC: IN (reaches SCC, not
    reachable from it), OUT (reachable from SCC, can't reach back), rest (tendrils,
    tubes, disconnected components - not split further, PLAN.md doesn't need that
    granularity)."""
    n = g.vcount()
    scc = g.connected_components(mode="strong")
    giant = set(max(scc, key=len))
    adj_out = g.get_adjlist(mode="out")
    adj_in = g.get_adjlist(mode="in")

    def bfs_multi(starts, adj):
        seen = set(starts)
        dq = collections.deque(starts)
        while dq:
            v = dq.popleft()
            for w in adj[v]:
                if w not in seen:
                    seen.add(w)
                    dq.append(w)
        return seen

    out_set = bfs_multi(giant, adj_out) - giant
    in_set = bfs_multi(giant, adj_in) - giant
    rest = set(range(n)) - giant - out_set - in_set
    return {
        "bowtie_scc": len(giant),
        "bowtie_in": len(in_set),
        "bowtie_out": len(out_set),
        "bowtie_rest": len(rest),
    }


def top_betweenness_sources(g: ig.Graph, top_n: int = 3) -> list:
    """Top-N nodes by full (all-pairs) directed betweenness centrality - candidate
    high-influence cascade sources for later experiments. Distinct from the per-source
    betweenness in `source_features` below (that one is restricted to a single source)."""
    bc = g.betweenness(directed=True)
    top_idx = sorted(range(g.vcount()), key=lambda i: -bc[i])[:top_n]
    return [{"snap_id": g.vs[i]["name"], "betweenness": bc[i]} for i in top_idx]


def degree_power_law_fit(degrees: list, prefix: str) -> dict:
    """Clauset-Shalizi-Newman (2009) MLE fit + KS statistic, via the `powerlaw` package -
    NOT just kappa = <k^2>/<k>^2 (PILOT_TESTS.md §36 flags kappa alone as insufficient).

    Fitting alone isn't proof of scale-free structure either (REPORT.md §5): also run
    CSN's own recommended likelihood-ratio comparison against plausible alternative
    heavy-tailed distributions. R > 0 favors power law, R < 0 favors the alternative;
    p < 0.05 means the comparison itself is trustworthy (the sign of R is meaningful).
    """
    data = [d for d in degrees if d > 0]
    fit = powerlaw.Fit(data, discrete=True, verbose=False)
    result = {
        f"{prefix}_gamma": fit.power_law.alpha,
        f"{prefix}_xmin": fit.power_law.xmin,
        # fit.power_law.KS() is broken in powerlaw==2.0.0 (undefined free function
        # called internally); .D holds the same statistic, computed during the fit.
        f"{prefix}_ks": fit.power_law.D,
    }
    for alt in ["lognormal", "exponential", "truncated_power_law", "stretched_exponential"]:
        R, p = fit.distribution_compare("power_law", alt)
        result[f"{prefix}_R_vs_{alt}"] = R
        result[f"{prefix}_p_vs_{alt}"] = p
    return result


def spectral_threshold(g: ig.Graph) -> dict:
    """lambda_c = 1 / lambda_max(A) - Wang et al. 2003; Castellano & Pastor-Satorras 2010.

    Also reports lambda_max(P) (probability-weighted adjacency) per PILOT_TESTS.md §20 -
    NOT used interchangeably with lambda_max(A); the structural threshold is unweighted.
    """
    A = g.get_adjacency_sparse().asfptype()
    lam_a = float(abs(spla.eigs(A, k=1, which="LR", return_eigenvectors=False)[0]))
    P = g.get_adjacency_sparse(attribute="probability").asfptype()
    lam_p = float(abs(spla.eigs(P, k=1, which="LR", return_eigenvectors=False)[0]))
    return {"lambda_max_A": lam_a, "lambda_c": 1.0 / lam_a, "lambda_max_P": lam_p}


def bow_tie(g: ig.Graph) -> dict:
    scc = g.connected_components(mode="strong")
    wcc = g.connected_components(mode="weak")
    return {
        "scc_giant": max(len(c) for c in scc),
        "n_scc": len(scc),
        "wcc_giant": max(len(c) for c in wcc),
        "n_wcc": len(wcc),
    }


def k_core_stats(g: ig.Graph) -> dict:
    core = g.coreness(mode="all")
    max_core = max(core)
    return {"k_core_max": max_core, "n_in_max_core": sum(1 for c in core if c == max_core)}


def louvain_best_of_n(g: ig.Graph, seeds=LOUVAIN_RESTART_SEEDS) -> dict:
    """Best-of-N Louvain restarts (PILOT_TESTS.md §36) - Louvain is seed-sensitive.

    igraph delegates its RNG to Python's `random` module by default, so `random.seed`
    controls reproducibility here (verified against known pilot numbers).
    """
    gu = g.as_undirected(mode="collapse")
    results = []
    for seed in seeds:
        random.seed(seed)
        vc = gu.community_multilevel()
        results.append((len(vc), vc.modularity))
    best_n, best_q = max(results, key=lambda r: r[1])
    ns = [r[0] for r in results]
    qs = [r[1] for r in results]
    return {
        "louvain_best_n_communities": best_n,
        "louvain_best_modularity": best_q,
        "louvain_n_communities_min": min(ns),
        "louvain_n_communities_max": max(ns),
        "louvain_modularity_min": min(qs),
        "louvain_modularity_max": max(qs),
    }


def assortativity(g: ig.Graph) -> dict:
    return {"assortativity_degree": g.assortativity_degree(directed=True)}


# --------------------------------------------------------------------------
# 2a. Global, source-independent heuristic features (REPORT.md §8)
# --------------------------------------------------------------------------


def degree_sum_scores(g: ig.Graph) -> dict:
    """out(u) + out(v) on the base graph, per edge - REPORT.md §2."""
    out_deg = g.outdegree()
    return {e.index: out_deg[e.source] + out_deg[e.target] for e in g.es}


def granovetter_local_bridge_flags(g: ig.Graph) -> dict:
    """Edge is a local bridge if its endpoints share no common neighbor (Granovetter 1973,
    standard "no common friend" definition - REPORT.md §2)."""
    gu = g.as_undirected(mode="collapse")
    neighbor_sets = [set(gu.neighbors(v)) for v in range(gu.vcount())]
    return {
        e.index: len(neighbor_sets[e.source] & neighbor_sets[e.target]) == 0 for e in g.es
    }


def spectral_edge_scores(g: ig.Graph) -> dict:
    """Tong et al. 2012, Algorithm 1: score(i,j) = u(i)*v(j).

    u = leading LEFT eigenvector of A (A^T's leading right eigenvector), v = leading
    RIGHT eigenvector of A, both sign-corrected via Perron-Frobenius. Verbatim from the
    paper - see REPORT.md §6a. Uses igraph's own get_adjacency_sparse so vertex order is
    guaranteed aligned to g.vs index (REPORT.md §8a) - never a separately rebuilt array.
    """
    A = g.get_adjacency_sparse().asfptype()
    _, vecs_r = spla.eigs(A, k=1, which="LR")
    v = np.real(vecs_r[:, 0])
    _, vecs_l = spla.eigs(A.T, k=1, which="LR")
    u = np.real(vecs_l[:, 0])

    # Perron-Frobenius: the leading eigenvector of a non-negative matrix can be chosen
    # non-negative. Flip sign if the solver returned the negated version.
    if u.sum() < 0:
        u = -u
    if v.sum() < 0:
        v = -v

    return {e.index: float(u[e.source] * v[e.target]) for e in g.es}


# --------------------------------------------------------------------------
# 2b. Per-source heuristic features - computed once per source, cached and reused
# --------------------------------------------------------------------------


def source_features(g: ig.Graph, source: int) -> dict:
    """Single BFS from `source` gives hop-distance for free; a reverse accumulation pass
    over the same BFS gives source-rooted edge betweenness (Brandes 2001, restricted to
    one start node - "Brandesov score na najkraćim putevima koji pocinju u izvoru",
    REPORT.md §2). Both are per-source static facts: compute once, reuse across every
    k/method/ALNS iteration for that source - never recompute inside the ALNS loop.

    Returns hop_of_node, betweenness (per edge id), and edges_by_hop (candidate pool
    buckets, REPORT.md §7): edge (u,v) belongs to layer hop_of_node[u]. hop_of_node is
    computed on the base graph, not recomputed as the cut changes.
    """
    n = g.vcount()
    out_adj = [g.incident(v, mode="out") for v in range(n)]  # edge ids per vertex

    dist = [-1] * n
    sigma = [0] * n
    dist[source] = 0
    sigma[source] = 1
    order = []
    queue = [source]
    qi = 0
    predecessors = [[] for _ in range(n)]
    while qi < len(queue):
        v = queue[qi]
        qi += 1
        order.append(v)
        for eid in out_adj[v]:
            w = g.es[eid].target
            if dist[w] == -1:
                dist[w] = dist[v] + 1
                queue.append(w)
            if dist[w] == dist[v] + 1:
                sigma[w] += sigma[v]
                predecessors[w].append((v, eid))

    delta = [0.0] * n
    betweenness = {}
    for v in reversed(order):
        for p, eid in predecessors[v]:
            contrib = (sigma[p] / sigma[v]) * (1 + delta[v])
            betweenness[eid] = betweenness.get(eid, 0.0) + contrib
            delta[p] += contrib

    hop_of_node = {v: dist[v] for v in range(n) if dist[v] != -1}
    edges_by_hop: dict = {}
    for e in g.es:
        if e.source in hop_of_node:
            edges_by_hop.setdefault(hop_of_node[e.source], []).append(e.index)

    return {"hop_of_node": hop_of_node, "betweenness": betweenness, "edges_by_hop": edges_by_hop}


# --------------------------------------------------------------------------
# CLI entry point
# --------------------------------------------------------------------------

if __name__ == "__main__":
    g = build_graph()

    topology = {}
    topology.update(small_world_stats(g))
    topology.update(degree_power_law_fit(g.outdegree(), "out"))
    topology.update(degree_power_law_fit(g.indegree(), "in"))
    topology.update(spectral_threshold(g))
    topology.update(bow_tie(g))
    topology.update(bow_tie_full(g))
    topology.update(k_core_stats(g))
    topology.update(louvain_best_of_n(g))
    topology.update(assortativity(g))
    topology.update(degree_heterogeneity(g))
    topology.update(probability_stats(g))
    topology["n"] = g.vcount()
    topology["m"] = g.ecount()

    pd.DataFrame([topology]).to_csv(DATA_DIR / "topology_summary.csv", index=False)
    for k, v in topology.items():
        print(f"{k}: {v}")

    top_sources = top_betweenness_sources(g)
    pd.DataFrame(top_sources).to_csv(DATA_DIR / "top_betweenness_sources.csv", index=False)
    print("\ntop betweenness sources:", top_sources)

    degree_sum = degree_sum_scores(g)
    bridge = granovetter_local_bridge_flags(g)
    spectral = spectral_edge_scores(g)
    edge_rows = [
        {
            "edge_id": e.index,
            "source": g.vs[e.source]["name"],
            "target": g.vs[e.target]["name"],
            "probability": e["probability"],
            "degree_sum": degree_sum[e.index],
            "is_local_bridge": bridge[e.index],
            "spectral_score": spectral[e.index],
        }
        for e in g.es
    ]
    pd.DataFrame(edge_rows).to_csv(DATA_DIR / "edge_features.csv", index=False)
    print(f"\nwrote {len(edge_rows)} rows to edge_features.csv")
    print(f"local bridges: {sum(bridge.values())} ({100 * sum(bridge.values()) / len(bridge):.1f}%)")
