"""Frozen live-edge (bond percolation) scenario sets: SAA in-sample + Monte Carlo
out-of-sample. Generated once per graph, immutable afterwards (REPORT.md §7).

Each scenario is a boolean occupancy mask over edge ids (numpy array), not a rebuilt
adjacency structure — evaluation reuses one shared base adjacency list
(`build_base_adjacency`) and checks occupancy + the candidate cut D during BFS
(fitness_evaluator.py). Nothing downstream mutates these arrays.
"""

import numpy as np

from config import MC_SCENARIO_COUNT, MC_SCENARIO_SEED, SAA_SCENARIO_COUNT, SAA_SCENARIO_SEED


def build_base_adjacency(g) -> list:
    """adj[u] = [(v, edge_id), ...] for all edges, indexed by igraph vertex id."""
    adj = [[] for _ in range(g.vcount())]
    for e in g.es:
        adj[e.source].append((e.target, e.index))
    return adj


def generate_scenarios(g, n_scenarios: int, seed: int) -> np.ndarray:
    """n_scenarios boolean occupancy masks (shape (n_scenarios, M)); each edge kept
    independently with probability equal to its own transmission probability."""
    rng = np.random.default_rng(seed)
    probs = np.array(g.es["probability"])
    draws = rng.random((n_scenarios, len(probs)))
    return draws < probs


def build_saa_scenarios(g) -> np.ndarray:
    return generate_scenarios(g, SAA_SCENARIO_COUNT, SAA_SCENARIO_SEED)


def build_mc_scenarios(g) -> np.ndarray:
    return generate_scenarios(g, MC_SCENARIO_COUNT, MC_SCENARIO_SEED)
