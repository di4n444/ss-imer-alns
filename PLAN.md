# PLAN — internal tracker

Three phases, in order: **architecture → experiment → figures**. Do not start Phase 2
until Phase 1 smoke tests pass; do not start Phase 3 until Phase 2's CSVs are frozen.
Check items off as we go. This file is process state, not a design doc — rationale for
decisions belongs in [REPORT.md](REPORT.md).

Timebox: 2 days total for build + thesis writing, so each phase should be built to "correct
and minimal," not "extensible for problems we don't have."

---

## Phase 1 — Architecture

Design patterns in play: **Strategy** for edge-scoring heuristics (one interface, six
interchangeable implementations, consumed identically by baselines and ALNS repair);
**two independent families** for destroy vs. repair (never share one heuristic across
both); single **config module** as the only place literals/seeds live.

- [x] **`config.py`** — grows incrementally as later modules need constants, not authored
      up front (see chat history). Has dataset path + duplicate-edge policy so far.
- [x] **`create_graph.py`** — load `data/soc-sign-bitcoinalpha.csv`, drop `RATING <= 0`,
      resolve duplicate edges (keep latest by time), map `RATING → p` via sigmoid, build
      the igraph directed graph with an explicit sorted vertex order + a structural
      `verify_vertex_alignment` guard (REPORT.md §8a, not `Graph.TupleList`). Smoke-tested:
      reproduces PILOT_TESTS.md §12 numbers exactly (REPORT.md §5).
      **Caught and fixed a real bug**: the skeleton's `code/operator.py` shadowed
      Python's stdlib `operator` module and broke every import; renamed to `operators.py`.
- [x] **`analyse_graph.py`** — both jobs done, output written to CSV
      (`data/topology_summary.csv`, `data/edge_features.csv`):
  - Topology chapter numbers, smoke-tested against pilot's known numbers (REPORT.md §5)
    — exact match on path length/clustering vs. ER, spectral threshold, bow-tie, k-core,
    assortativity, Granovetter bridges; Louvain close but not identical (expected,
    stochastic algorithm); **power-law γ/xmin doesn't match pilot's number and is
    flagged unresolved in REPORT.md §5 — trusting this run's principled CSN fit.**
  - Global features (degree-sum, Granovetter bridge, index-aligned spectral score) and
    a per-source function (`source_features`) giving hop-distance + source-rooted
    betweenness from a single shared BFS pass — not yet called by anything downstream,
    that happens when `create_subgraphs.py`/`operators.py` need it.
- [x] **`heuristics.py`** — the Strategy layer, consuming precomputed features only,
      never touching the graph directly. `edge_scores` for the six heuristics;
      `rank`/`pick_biased`/`select_q`/`topk` implement the shared selection mechanism
      (REPORT.md §3/§7a — R&P's y^p rank-biased sampling with a tie-shuffle pre-step,
      not a separate "shuffle only" mechanism). Two more helpers added once
      `operators.py` actually needed them (not guessed in advance): `active_pool`
      (turns `edges_by_hop` + the loop's `active_max_hop` into a candidate list) and
      `build_edge_meta` (per-edge source/target/probability/hop, for
      `destroy_related`'s relatedness measure). `tie_group_sizes` diagnostic not yet
      wired into a hot path — that's a Phase 2 measurement task.
- [x] **`create_subgraphs.py`** — builds frozen live-edge scenario subgraphs as boolean
      occupancy masks over edge ids (not rebuilt adjacency lists — reuses one shared
      base adjacency, REPORT.md §7), **not** hop-layer candidates. Two disjoint,
      separately seeded sets: in-sample (SAA, 500 scenarios) and out-of-sample (MC,
      2000 scenarios) — counts taken directly from the thesis's own Ch.4 text, not
      invented. Nothing downstream mutates these.
- [x] **`evaluator.py`** — one function, `evaluate_reach(source, D, base_adj,
      scenarios)`: masked BFS reach given a candidate cut `D`, over whatever scenario
      array is passed in. Does not generate scenarios (`create_subgraphs.py`). Used
      for both SAA (inside the ALNS loop) and OOS (final validation only) — no
      separate `oos_evaluator.py` file (removed: it was a 2-line re-export, no actual
      enforcement beyond what passing the right array already gives). The separation
      is structural — callers only ever hold a reference to one scenario set at a
      time — not a second file.
- [ ] **`greedy_baseline.py`** — one baseline per heuristic, hop0-only candidates
      (edges directly incident to `s`), deterministic `topk` path. No ALNS-specific
      logic here at all. This restriction is the whole point of the baseline — it's
      what ALNS is being compared against, see REPORT.md §7 on the Level-2 reframing.
- [x] **`operators.py`** — destroy (random / worst / related-Shaw) and repair (the six
      `heuristics.py` scorers) as two independently weighted families, drawing from
      whatever active hop-windowed candidate pool `alns_optimizer.py` exposes via
      `heuristics.active_pool` (operators don't own or compute the horizon themselves
      — REPORT.md §7). `destroy_worst` and `destroy_related` grounded directly in R&P
      (2006) §3.1 (re-read before writing, not from memory) — see REPORT.md §6a for
      their actual tuned parameter vector (σ1=33, σ2=9, σ3=13, r=0.1, w=0.05,
      c=0.99975, p_worst=3, p_Shaw=6 — starting points, not invented). Shaw-relatedness
      weighting (shared tail/head/hop/probability, equal-weighted) is a genuinely
      uncalibrated placeholder, flagged for Phase 2. `destroy_worst` and the main loop
      share `evaluator.py`'s optional cache (keyed by `frozenset(D)`) — doubles as
      R&P's required visited-solution tracking and a real memoization win.
- [ ] **`alns_optimizer.py`** — adaptive weight update (σ1/σ2/σ3 reward, Δ=0 accepted but
      rewarded 0, tracked separately as `neutral_moves`), SA acceptance with geometric
      cooling, and hop-horizon state: `active_max_hop` starts at hop0∪hop1, expands per
      segment when the outer layer's average reward is positive, using the precomputed
      hop-distance feature to build each segment's active pool. Because this is a real
      adaptive-learning claim (not just a descriptive stat), log per segment:
      `active_max_hop`, per-layer/per-heuristic weights, `best_hits` by hop — and
      implement (or explicitly justify skipping) a **contraction** rule, since pilot's
      expansion-only horizon was flagged as unvalidated (REPORT.md §6/§10, pilot §33).
      Explicit `stop_reason` ∈ {max_iter, stagnation, isolated/hard-error}.
- [ ] **`run_experiment.py`** — config-driven orchestration; one CSV row per
      (source, k, method) run; never a column that puts ALNS in its own comparison pool.
- [ ] **Smoke tests** (small, run before Phase 2 starts):
  - [ ] Reproduce topology numbers once and freeze them into REPORT.md §5.
  - [ ] One source/k run per method family, confirm CSV schema is complete and stable.
  - [ ] Confirm `k ≥ out(s)` behaves as the decided hard error (REPORT.md §4).
  - [ ] Confirm spectral score index alignment (REPORT.md §4/§6) — check against a
        hand-computable small case if possible.
  - [ ] Confirm frozen scenarios are byte-for-byte reproducible given a seed, and that
        no code path ever mutates them (REPORT.md §7).

## Phase 2 — Experiment design & execution

- [ ] Decide source sample: stratify by reach level (low/mid/high) and/or out-degree
      band; disjoint calibration set vs. measurement/showcase set.
- [ ] **Calibrate ALNS defaults on the calibration set, immediately after Phase 1 smoke
      tests pass, before any measurement/showcase run.** Document the process itself
      (values tried, selection metric, final defaults, RNG sensitivity) into REPORT.md
      §10 — this is thesis methodology content, not just internal tuning.
- [ ] Curate showcase (source, k) pairs — and, where more revealing, other-parameter
      showcases (segment length, ρ, q bounds) — each picked for a specific phenomenon,
      with the reason documented (REPORT.md §9). Not a uniform sources×k grid.
- [ ] Design and run the dedicated k-sweep figure's experiment: fixed representative
      source(s), k varied across a chosen range.
- [ ] Run the curated showcase matrix → raw per-run CSV, tagged with which
      showcase/purpose each row belongs to.
- [ ] Tie-frequency + tie-break-variance measurement pass (REPORT.md §3): log tie-group
      sizes per heuristic per selection event; run a small fixed number of ALNS seeds per
      (source, k) and record the σ/R spread across seeds. Document, do not average away.
- [ ] OOS validation pass on best cuts found.

## Chapter 1-2 figures (out of phase order — done early, thesis needed them now)

- [x] `code/make_topology_figures.py` → `figures/`: ER/WS/BA comparison (Ch1),
      out-degree CCDF with power-law fit (Ch2 — visually shows the tail falling below
      the fit, supporting the truncated-power-law finding in REPORT.md §5), probability
      distribution bar chart (Ch2), bow-tie diagram drawn as an actual three-lobe
      IN→SCC→OUT shape with directional arrows (not just a bar) — sized with a minimum-
      radius floor since SCC's 86.7% dominance would otherwise shrink IN/periphery to
      invisible dots; exact counts always labeled regardless of drawn size.

## Phase 3 — Figures & report

- [ ] Decide the figure list against the thesis chapter outline (topology chapter figures;
      results chapter figures) before generating anything.
- [ ] Generate every figure from CSV only — no figure computed inline during a run.
- [ ] Fill in REPORT.md §5 numbers and any remaining thesis-writing notes.

---

## Status

Currently: pre-Phase-1, architecture design agreed, not yet implemented.
