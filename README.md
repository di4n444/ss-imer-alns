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
2. **How far from the source** the edges worth removing actually are. The intuition is to
   cut edges leaving `s` directly, but when several independent hop0 edges all feed the
   same well-connected region, a budget `k` smaller than that fan-out cannot close them
   all — and if those paths converge on a shared choke point a few hops downstream,
   cutting that one edge is far cheaper (REPORT.md §8c). ALNS's candidate pool is
   organized into hop layers (BFS distance of an edge's tail from `s`) and repair draws
   from **one layer per iteration, chosen by its own roulette wheel** alongside the
   destroy and repair wheels — an explicit, logged, adaptive mechanism, not a byproduct
   of unrestricted search. An earlier expanding-horizon version of this was measured to
   wreck the search and was removed (REPORT.md §12). Baselines below stay fixed at hop0.

   The question this asks is *"do edges beyond hop0 ever reach the winning cut?"*, not
   *"which layer scores best"* — the layers differ in size by up to 1,900:1, so the
   learned weights alone cannot answer the latter (REPORT.md §14.2).

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
  greedy_baseline.py    hop0-only baselines, one per heuristic
  source_profile.py     per-source reach/out-degree profile for the whole graph
  sample_sources.py     the one stratified source sample (calibration | measurement)
  run_experiment.py     orchestration -> one CSV row per (source, k, method)
  calibrate.py          R&P one-at-a-time parameter tuning -> CSV
  smoke_test.py         end-to-end pipeline check with timings
  test_evaluator.py     regression tests for the objective function
  make_topology_figures.py  Chapter 1-2 figures, generated from the CSVs
  test_evaluator.py     objective pinned against an igraph oracle
  test_features.py      spectral index alignment, three independent ways
  test_scenarios.py     scenario reproducibility, independence, immutability
thesis/
  omml.py               native Word equations (OMML) with proper math formatting
  doc.py                document assembly against the faculty template's rules
  bibliography.py       citation keys -> author-year, and the bibliography itself
  figures.py            conceptual diagrams for the theory and method chapters
  ch01_*.py, ch02_*.py  chapter text, numbers read from data/ at build time
  build_thesis.py       writes the chapters into the .docx
data/                   raw dataset + generated topology/feature/sample/result CSVs
figures/                generated only from CSVs or from figures.py
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
