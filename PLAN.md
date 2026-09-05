# PLAN — operational state

What is done, what is next, and how to run things. Rationale lives in
[REPORT.md](REPORT.md); this file is process state only.

**Read this first when starting a new chat.** Together with `git log` it is the complete
handoff — no earlier conversation needs to be reconstructed.

---

## The one rule about numbers

**Every number that reaches the thesis comes from `data/*.csv` produced by the code in
this repository.** Nothing is retyped from a conversation, and nothing is taken from
[PILOT_TESTS.md](PILOT_TESTS.md), whose measurements come from a deleted, pre-git
implementation. That file is kept for its *decisions*, not its figures — see the warning
at the top of it.

The git history is exactly the current architecture: the previous implementation was never
committed, and no experiment was run until the code had been reviewed and its objective
pinned by tests. So anything reachable from `git log` is trustworthy provenance.

---

## Commands

Each script imports its siblings, so it must be run from its own directory.

```bash
cd ss-imer-alns/code

# tests — objective, spectral alignment, frozen scenarios
../.venv/bin/python test_evaluator.py
../.venv/bin/python test_features.py
../.venv/bin/python test_scenarios.py

# pipeline stages (each writes to ../data/)
../.venv/bin/python analyse_graph.py        # topology_summary.csv, edge_features.csv
../.venv/bin/python source_profile.py       # source_profile.csv   (~2 min)
../.venv/bin/python sample_sources.py       # sample.csv
../.venv/bin/python calibrate.py            # calibration.csv      (~13 min)
../.venv/bin/python run_experiment.py       # CSV schema check
../.venv/bin/python smoke_test.py           # end-to-end, one source
```

```bash
cd ss-imer-alns/thesis

../.venv/bin/python figures.py              # conceptual figures -> ../figures/
../.venv/bin/python build_thesis.py         # -> "... - nacrt.docx" beside the original
```

### Which file to edit

`build_thesis.py` **reads** `Optimizacija protoka informacije u grafovima.docx` and
**writes** `Optimizacija protoka informacije u grafovima - nacrt.docx`. The original is
never modified.

The nacrt is regenerated from scratch on every build, so:

- **Chapter text** is edited in `thesis/ch0*.py`, never in the nacrt — an edit there is
  lost on the next build.
- **Front and back matter** (title page, Sažetak, Summary, the table-of-contents field,
  the AI-usage statement) is carried over from the original untouched, so fill those in
  **in the original** and they flow into every future build.
- The bibliography is regenerated from `thesis/bibliography.py`.
- Once the text is final and the build is retired, the nacrt can be edited directly in
  Word like any document.

Tests and the calibration compete for CPU; do not run them at the same time, since the
calibration enforces a wall-clock budget and would truncate.

---

## Status

**Phase 1 (architecture) — complete.** All modules written, three test suites passing.

**Phase 2 (experiment) — calibration done, measurement not started.**

**Phase 3 (thesis) — chapters 1–6 written.** Everything up to the results chapter is
drafted; 7 waits on the measurement runs.

### Done

- `config.py`, `create_graph.py`, `analyse_graph.py`, `heuristics.py`,
  `create_subgraphs.py`, `operators.py`, `source_context.py`, `evaluator.py`,
  `alns_optimizer.py`, `greedy_baseline.py`, `source_profile.py`, `sample_sources.py`,
  `run_experiment.py`, `calibrate.py`, `smoke_test.py`
- Tests: `test_evaluator.py` (objective vs. igraph oracle, one-pass marginals,
  monotonicity, buffer cleanliness, cache correctness across sources, sampler bias),
  `test_features.py` (spectral index alignment, three ways), `test_scenarios.py`
  (reproducibility, SAA/MC independence, immutability under a full search)
- Source sample drawn: 15 calibration + 28 measurement, disjoint, one seed
- **ALNS parameters calibrated and locked**: every default stands; `max_iter=300` is
  positively supported rather than merely retained
- Thesis generator: native Word equations, author-year citations, style-based heading
  numbering, alphabetical bibliography, template styles for lists, tables and code
  listings, and two-pass section cross-referencing

### Next — Phase 2

- [ ] Curate showcase (source, k) pairs, each chosen for a specific phenomenon, with the
      reason recorded. Not a uniform grid.
- [ ] Dedicated k-sweep experiment: a few representative sources, k varied.
- [ ] Run the measurement matrix → per-run CSV tagged by showcase/purpose.
      Budget: one ALNS run over all 28 measurement sources is ~990 s, so a full sweep at
      3 budgets × 3 seeds is roughly 2.5 h.
- [ ] Tie-frequency and tie-break-variance pass: tie-group sizes per criterion, and the
      σ/R spread across a few seeds. Report the spread, do not average it away.
- [ ] Do the greedy baselines also reach the enumerated optimum on small sources
      (out ≤ 10)? Separates a weak *criterion* from a weak *search*.
- [ ] Out-of-sample validation of the best cuts found.

### Next — Phase 3 (thesis)

Chapters, in the agreed structure:

- [x] Uvod
- [x] 1. Topologija i dinamika kompleksnih mreža
- [x] 2. Analiza mreže Bitcoin Alpha
- [x] 3. Formulacija problema SS-IMER
- [x] 4. Kriteriji odabira bridova
- [x] 5. Metode rješavanja — 5.2 ended up with eight subsections rather than five: the
      hop-layer mechanism needed three (the layers, why a wheel rather than a horizon,
      and what the learned weights do *not* license), and the departures from R&P are
      tabulated in 5.2.8 rather than scattered.
- [x] 6. Implementacija i eksperimentalni postav
- [ ] 7. Rezultati i rasprava — after the measurement runs
- [ ] 8. Mogućnosti poboljšanja i budući rad. Already promised by the text: the σ-greedy
      of REPORT §15.3 is named in 5.1 as the next step, so it has to appear here.
- [ ] Zaključak, Sažetak, Summary

All figures for chapters 1–6 exist: `fig1_1` ER/WS/BA, `fig1_2` live-edge, `fig2_1`
degree distribution, `fig2_2` probability distribution, `fig2_3` bow-tie, `fig2_4` source
population, `fig3_1` choke point, `fig5_1` ALNS loop, `fig5_2` hop layers, `fig6_1`
pipeline.

**Numbers and settings are read at build time, never retyped.** Chapters 2, 4, 5 and 6
read `data/*.csv`; chapters 5 and 6 read `code/config.py` through `thesis/params.py`, so
every parameter value in the prose is the one the code actually runs with. Chapter 6.4
recomputes the calibration verdict from `data/calibration.csv` rather than quoting it.

**Cross-references resolve themselves.** Headings carry `label=`, the text asks for
`t.sec("label")`, and `build_thesis.py` renders twice — once to discover the numbers,
once to substitute them — because a chapter may point forward (3.3 points at 5.2.4). The
build refuses to save if any reference is still unresolved. Equations, figures, tables and
listings work the same way via `t.ref`, `t.figref`, `t.tabref` and `t.coderef`. Do not
write a section number by hand.

**Where calibration is written up: §6.4, as method, not as a result.** It describes R&P's
one-at-a-time procedure, the tuning set, the decision rule and the chosen values, and
states the two limitations (single seed, eight tuning cells). Per-setting scores are not
reported there — they are in `data/calibration.csv` if ever needed.

---

## When to start a new chat

At a phase boundary, once this file and `git log` describe the state — which is the point
of keeping them current. Good moments: after a chapter is written and committed, after a
measurement run completes, after a design decision is recorded in REPORT.md. Bad moments:
mid-debug, or with uncommitted work, because the reasoning then exists only in the
conversation.
