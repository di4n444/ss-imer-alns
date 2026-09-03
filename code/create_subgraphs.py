"""Frozen live-edge (bond percolation) scenario sets: SAA in-sample + Monte Carlo
out-of-sample. Generated once per graph, immutable afterwards (REPORT.md §7).

Each scenario is a plain Python adjacency list, `list[list[int]]` indexed by node id,
giving only the *targets* reachable via an occupied edge — the coin-flip occupancy
decision is baked in once at generation time, not re-checked per BFS step. This
mirrors PILOT_TESTS.md §24's own measured lesson (~2.3x over a numpy-mask version):
numpy array indexing inside a tight Python BFS loop is slower than plain Python
lists/sets due to per-element boxing. Vectorized numpy is still used for the actual
random draws (that part benefits from it); only the structure consumed by the BFS
hot loop (evaluator.py) is plain Python.
"""

import numpy as np

from config import MC_SCENARIO_COUNT, MC_SCENARIO_SEED, SAA_SCENARIO_COUNT, SAA_SCENARIO_SEED


def generate_scenarios(g, n_scenarios: int, seed: int) -> list:
    """n_scenarios plain-Python adjacency lists (occupied edges only)."""
    rng = np.random.default_rng(seed)
    probs = np.array(g.es["probability"])
    sources = np.array([e.source for e in g.es])
    targets = np.array([e.target for e in g.es])
    n = g.vcount()

    draws = rng.random((n_scenarios, len(probs)))
    occupied = draws < probs  # (n_scenarios, M) boolean - vectorized generation

    scenarios = []
    for i in range(n_scenarios):
        mask = occupied[i]
        adj = [[] for _ in range(n)]
        for u, v in zip(sources[mask].tolist(), targets[mask].tolist()):
            adj[u].append(v)
        scenarios.append(adj)
    return scenarios


def build_saa_scenarios(g) -> list:
    return generate_scenarios(g, SAA_SCENARIO_COUNT, SAA_SCENARIO_SEED)


def build_mc_scenarios(g) -> list:
    return generate_scenarios(g, MC_SCENARIO_COUNT, MC_SCENARIO_SEED)
