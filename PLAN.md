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
- [x] **`heuristics.py`** — the Strategy layer, reading only precomputed tables.
      `edge_scores` for the six heuristics (plain dict lookups — the earlier pandas
      `.loc`-per-edge version was microseconds *per candidate* on pools of thousands);
      `rank`/`biased_index`/`select_q`/`topk` are the one shared selection mechanism
      (REPORT.md §3/§7a). Candidate lists per hop layer are materialised in
      `run_alns` itself, since they are search state, not a heuristic concern.
      `tie_group_sizes` diagnostic is written but not yet wired into a run — that is a
      Phase 2 measurement task.
- [x] **`create_subgraphs.py`** — frozen live-edge scenarios as plain-Python adjacency
      lists (`list[list[int]]`, targets only, occupancy baked in at generation time so
      the BFS never re-checks it — PILOT_TESTS.md §24). numpy still does the vectorised
      coin flips; only the structure the hot loop consumes is plain Python. Two
      disjoint, separately seeded sets: SAA (500) and MC (2000), counts taken from the
      thesis's own Ch.4 text. Nothing downstream mutates these.
- [x] **`greedy_baseline.py`** — one baseline per heuristic, hop0-only candidates
      (edges directly incident to `s`), deterministic `topk` path. No ALNS-specific
      logic here at all. This restriction is the whole point of the baseline — it's
      what ALNS is being compared against, see REPORT.md §7 on the Level-2 reframing.
      Returns a `run_alns`-shaped dict so orchestration writes one CSV row per method
      without special-casing, plus the tie diagnostics REPORT.md §3 asks for — the
      tied group straddling rank k, where the deterministic (u, v) rule rather than the
      heuristic decides. Already earning its keep: `bridge` at source 1 / k=20 takes 20
      edges out of a 240-edge tied group.
      **A sigma-greedy is deliberately not here** — that is Kimura's own proposed method
      and the stronger opponent, deferred with its cost analysis in REPORT.md §15.
- [x] **`operators.py`** — destroy (random / worst / related-Shaw) and repair (the six
      scorers) as two independently weighted families with one uniform signature each,
      dispatched through `DESTROY_REGISTRY` instead of kwargs plumbing. Grounded in
      R&P §3.1 with their tuned exponents (p_worst=3, p_Shaw=6). `destroy_worst` uses
      `Evaluator.marginal_values`, which was the single biggest performance fix in the
      project (REPORT.md §11). Shaw relatedness weighting stays an uncalibrated
      placeholder, flagged for Phase 2.
- [x] **`source_context.py`** *(new)* — `SourceContext`, the Parameter Object holding
      everything precomputed once per source. Without it `run_alns` and every operator
      need 8-9 loose arguments. Also `verify_feature_alignment`, the counterpart to
      `create_graph.verify_vertex_alignment`: it caught a real bug where endpoints were
      being read as SNAP IDs from the CSV while scenarios and the stamp array are
      indexed by internal igraph vertex index (REPORT.md §4/§8a's bug class, live).
- [x] **`evaluator.py`** — `Evaluator` class (state that must persist across thousands
      of calls: stamp arrays, reused cut buffer, fitness and marginal caches). Bound to
      one scenario set for its lifetime, which is what makes the SAA/OOS boundary
      structural. See REPORT.md §11 for the cost model and the four optimisations.
- [x] **`test_evaluator.py`** *(new)* — regression tests pinning the objective function
      against an independent igraph oracle, plus one-pass marginals vs naive,
      monotonicity, buffer cleanliness and cache transparency.
- [x] **`alns_optimizer.py`** — roulette-wheel selection over *three* weight books
      (destroy, repair, hop scope), R&P's σ1/σ2/σ3 scoring with the "only reward
      unvisited solutions" rule, segment-end weight update, SA acceptance with a
      calibrated start temperature. Δ=0 is accepted but scores nothing, counted as
      `neutral_moves` (PILOT_TESTS.md §18's bug, fixed by construction). Logs both
      weight books plus `scope_weights` and `best_reach` per segment.
      **The expanding hop horizon was removed**: measured at 1/8 optimal with gaps up
      to 495% on enumerable instances, versus 8/8 optimal with the horizon held at
      hop0. Replaced by the hop-scope roulette wheel — 4/4 optimal, and it learns that
      hop0 pays most rather than being told. Full diagnosis in REPORT.md §12.
      `fixed_hop_scope=` pins a single layer. **Decided: this is not part of the
      experiment matrix** — a winning cut generally contains at least one hop0 edge, so
      hop0-only-vs-hop2-only is not where the evidence lies; Level 2 is answered by
      `hop_mix` / `best_hits_by_hop` on the adaptive runs (REPORT.md §16). Kept as a
      diagnostic knob.
- [x] **`run_experiment.py`** — config-driven orchestration; one CSV row per
      (source, k, method) run; never a column that puts ALNS in its own comparison pool.
      `run_cell` is the shared core used by both the calibration driver and the eventual
      measurement sweep; `Workbench` builds the graph, both scenario sets and the
      per-source contexts once. Every row carries both σ's, their gap, and every resolved
      ALNS parameter (PILOT_TESTS.md §37). To vary a parameter is to pass an override to
      `run_alns`, never to take a different code path.
- [ ] **Smoke tests** (small, run before Phase 2 starts):
  - [ ] Reproduce topology numbers once and freeze them into REPORT.md §5.
  - [x] One source/k run per method family, confirm CSV schema is complete and stable —
        `run_experiment.py`'s `__main__`. 38 columns, all populated except
        `param_fixed_hop_scope`, which is correctly empty since that knob is out of the
        matrix (REPORT.md §16).
  - [x] `k ≥ out(s)` handled as the trivial isolated case, not an error: warm start
        cuts all of hop0, sigma=1, `stop_reason="isolated"`, 0 iterations (REPORT.md §13).
  - [x] Confirm spectral score index alignment (REPORT.md §4/§6) — `test_features.py`,
        three angles: invariance to vertex insertion order, Spearman against the
        *measured* drop in λmax, and CSV-vs-fresh-computation. **Passes: 0.965** against
        the pilot's 0.969-aligned / 0.15-misaligned (REPORT.md §17).
  - [x] Confirm frozen scenarios are byte-for-byte reproducible given a seed, and that
        no code path ever mutates them (REPORT.md §7) — `test_scenarios.py`, which also
        checks SAA/MC independence and that the search leaves SourceContext's shared
        tables untouched. All pass.

## Phase 2 — Experiment design & execution

- [x] Decide source sample: stratify by reach level (low/mid/high) and/or out-degree
      band; disjoint calibration set vs. measurement/showcase set.
      `source_profile.py` measures reach for every node first — the population turned out
      **not** to be bimodal, so the design changed (REPORT.md §18). `sample_sources.py`
      then draws 15 calibration + 28 measurement sources over 7 (out-degree × reach)
      cells into `data/sample.csv`, one seed, disjoint by construction. Also established:
      only 1184 of 3683 nodes can support k=3 at all, and the out≥50 low-reach cell has
      exactly one member in the whole graph.
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
- [ ] **Do the greedy baselines also find the enumerated optimum?** On sources small
      enough to brute-force (out-degree ≤ 10 ⇒ C(out,k) ≤ ~200 hop0 cuts), compare each
      hop0 baseline against the exhaustive optimum, the same way ALNS was checked in
      REPORT.md §12. This says whether a baseline's weakness is the *heuristic* or the
      *search* — and if a simple deterministic rule already hits the optimum on small
      instances, that bounds what ALNS can claim there. Not to be run until the ALNS
      side is settled.
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
