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
  config.py             every path, seed and tunable constant, in one place
  create_graph.py       load the raw data, build the directed IC graph
  analyse_graph.py      topology characterisation (small-world, scale-free, spectral
                        threshold, bow-tie, k-core, Louvain, Granovetter bridges) and
                        the precomputed edge-feature tables
  source_context.py     SourceContext: everything precomputed once per source, plus a
                        structural guard that the feature table still matches the graph
  heuristics.py         the six edge-scoring strategies + the one selection mechanism
                        shared by baselines (deterministic) and ALNS (rank-biased)
  create_subgraphs.py   frozen live-edge scenarios: SAA in-sample + MC out-of-sample
  evaluator.py          reach evaluation; one Evaluator is bound to one scenario set,
                        which is what keeps SAA and OOS structurally separate
  operators.py          ALNS destroy + repair, two independently weighted families
  alns_optimizer.py     the ALNS loop: three adaptive weight books (destroy, repair,
                        hop scope), SA acceptance
  greedy_baseline.py    hop0-only baselines, one per heuristic          (not yet written)
  run_experiment.py     orchestration -> CSV                            (not yet written)
  smoke_test.py         end-to-end pipeline check with timings
  test_evaluator.py     regression tests for the objective function
  make_topology_figures.py  Chapter 1-2 figures, generated from the CSVs
data/                   raw dataset + generated topology/feature CSVs
figures/                generated only from CSVs
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
