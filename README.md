# SS-IMER-ALNS

Single-Source Influence Minimization by Edge Removal, solved with an Adaptive Large
Neighborhood Search (ALNS) metaheuristic, evaluated on the Bitcoin Alpha trust network.

Bachelor's thesis project ("Optimizacija protoka informacije u grafovima").

## Problem

Given a directed graph `G = (V, E)` with an Independent Cascade diffusion model, a fixed
source node `s`, and a budget `k`, find a set of edges `D ⊆ E`, `|D| = k`, whose removal
minimizes the expected cascade reach `σ(s, G\D)`.

The core research question is whether ALNS's adaptive learning helps at two levels:

1. **Which topological heuristic** (edge probability, degree, Granovetter local bridge,
   betweenness, spectral score, random) best estimates which edges to remove, learned via
   adaptive operator weights rather than fixed a priori.
2. **How far from the source** the edges worth removing actually are — most cascades are
   choked off closest to `s`, but the real bottleneck can sit several hops away when local
   edges lead to dead ends. ALNS's candidate pool is organized into hop layers (BFS
   distance of an edge's tail from `s`), starting at hop0∪hop1 and expanding outward
   during the search based on measured reward — an explicit, logged, adaptive mechanism,
   not just a byproduct of unrestricted search. Baselines below stay fixed at hop0.

ALNS is compared against greedy baselines that use the *same* heuristic-scoring logic but
are restricted to edges directly incident to `s` (hop0) — isolating search breadth and
adaptivity as the only variables between ALNS and each baseline.

## Data

[Bitcoin Alpha](https://snap.stanford.edu/data/soc-sign-bitcoinalpha.html) signed trust
network (Kumar et al., 2016, ICDM; Kumar et al., 2018, WSDM), via SNAP. Positive ratings
only; rating mapped to an IC transmission probability via a sigmoid.

## Project structure

```
code/
  config.py            single source of parameters, seeds, and constants
  create_graph.py      load + build the directed IC graph from raw data
  analyse_graph.py     topology characterization (small-world, scale-free, spectral
                        threshold, bow-tie, k-core, Louvain, Granovetter bridges, ...)
                        AND precomputed heuristic feature tables (global + per-source)
  heuristics.py         edge-scoring strategies (Strategy pattern, precomputed-lookup
                        only) + shared, tie-break-aware top-k selection used by both
                        baselines and ALNS
  create_subgraphs.py   frozen live-edge scenario subgraphs (SAA in-sample + Monte
                        Carlo out-of-sample), generated once, immutable afterwards
  evaluator.py          masked-BFS reach evaluation; one function used for both SAA
                        (inside the ALNS loop) and OOS (final validation only),
                        never both at once — see README's structure notes in REPORT.md
  greedy_baseline.py     hop0-only baselines, one per heuristic
  operators.py             ALNS destroy/repair operators (two independent families),
                        operating on the hop-windowed active candidate pool
  alns_optimizer.py       ALNS main loop: adaptive weights, SA acceptance, hop-horizon
                        state and expansion (owns active_max_hop)
  run_experiment.py       experiment orchestration → CSV output
data/                     raw dataset + generated scenario/topology CSVs
figures/                   generated only from CSVs in data/ or results/
```

`PILOT_TESTS.md` documents lessons (including bugs to avoid) from an earlier, discarded
implementation — kept as a reference, not as code.

## Status / process

See [PLAN.md](PLAN.md) for the current phase and task checklist (architecture →
experiment → figures), and [REPORT.md](REPORT.md) for the running log of decisions,
numbers, and everything that needs to make it into the thesis text.

## Reproducibility

All experiment numbers live in CSV files; figures are generated from those CSVs only.
Every stochastic step (scenario sampling, Louvain, source sampling, ALNS runs) is seeded
via `config.py`.
