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
- [ ] **`analyse_graph.py`** — two jobs, both write to CSV, nothing printed-only:
  - Topology chapter numbers: N, M, mean/median/std p; path length + clustering vs.
    directed ER null model; degree distribution power-law fit (Clauset–Shalizi–Newman
    MLE + KS, not just κ); spectral threshold `λc = 1/λmax`; bow-tie decomposition;
    k-core; Louvain (seeded, best-of-N restarts, report best + range) — descriptive
    only, see REPORT.md §2; assortativity.
  - Precomputed heuristic feature tables (REPORT.md §8) — global (degree-sum,
    Granovetter local-bridge flag, index-aligned spectral eigenvector components) and,
    per source, on demand at the start of that source's run (betweenness-from-source,
    hop-distance-from-source, reachable-from-`s` edge set). Cache per-source results —
    computed once, reused across every k/method/ALNS iteration for that source.
- [ ] **`heuristics.py`** — the Strategy layer, consuming precomputed features only,
      never touching the graph directly. One score table per heuristic (random,
      probability, degree, bridge, betweenness, spectral). Shared
      `topk(edges, scores: dict, k, rng=None)`:
      `rng=None` → deterministic `(score desc, u asc, v asc)`;
      `rng=<Random>` → shuffle within tied score groups first. This is the one function
      both `greedy_baseline.py` and `operators.py` call — see REPORT.md §3.
      Also compute and log tie-group-size stats here (feeds REPORT.md §3/§5).
- [ ] **`create_subgraphs.py`** — builds frozen live-edge scenario subgraphs (bond
      percolation: each edge kept independently with probability `p`), **not** hop-layer
      candidates (see REPORT.md §7). Produces two disjoint, separately seeded, immutable
      sets: in-sample (SAA) and out-of-sample (Monte Carlo). Nothing downstream mutates
      these — always operate on a copy/mask.
- [ ] **`fitness_evaluator.py`** — SAA evaluation only: given a candidate cut `D` and the
      frozen in-sample scenarios, compute mean reach via masked directed BFS from `s`
      over a **copy**. Does not generate scenarios (that's `create_subgraphs.py`) and
      does not touch the out-of-sample set.
- [ ] **`oos_evaluator.py`** *(new file)* — out-of-sample Monte Carlo evaluation of final/
      best cuts only, using the frozen OOS scenario set. Never called from inside the
      ALNS loop — keeps the search objective (SAA) and the reported result (OOS)
      structurally separate.
- [ ] **`greedy_baseline.py`** — one baseline per heuristic, hop0-only candidates
      (edges directly incident to `s`), deterministic `topk` path. No ALNS-specific
      logic here at all. This restriction is the whole point of the baseline — it's
      what ALNS is being compared against, see REPORT.md §7 on the Level-2 reframing.
- [ ] **`operators.py`** — destroy operators (random / worst-by-SAA-cost / related-Shaw)
      and repair operators (the six `heuristics.py` scorers) as two independently
      weighted families, drawing from whatever active hop-windowed candidate pool
      `alns_optimizer.py` currently exposes (operators don't own or compute the horizon
      themselves — see REPORT.md §7). Repair uses the seeded-random `topk` path.
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

## Phase 3 — Figures & report

- [ ] Decide the figure list against the thesis chapter outline (topology chapter figures;
      results chapter figures) before generating anything.
- [ ] Generate every figure from CSV only — no figure computed inline during a run.
- [ ] Fill in REPORT.md §5 numbers and any remaining thesis-writing notes.

---

## Status

Currently: pre-Phase-1, architecture design agreed, not yet implemented.
