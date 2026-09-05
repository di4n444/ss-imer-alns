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
../.venv/bin/python hop_layers.py           # hop_layers.csv
../.venv/bin/python calibrate.py            # calibration.csv      (~13 min, not thesis content)
../.venv/bin/python measure.py              # results.csv   (~35 min)
../.venv/bin/python run_experiment.py       # CSV schema check
../.venv/bin/python smoke_test.py           # end-to-end, one source
```

```bash
cd ss-imer-alns/thesis

../.venv/bin/python figures.py              # conceptual figures -> ../figures/
../.venv/bin/python build_thesis.py         # -> "... - nacrt.docx" beside the original
```

```bash
cd ss-imer-alns/code
../.venv/bin/python make_result_figures.py  # chapter 7 figures -> ../figures/
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

Long runs enforce a wall-clock budget, so do not run the tests alongside one - the
measurement gets truncated rather than slowed.

---

## Status

**Phase 1 (architecture) — complete.** All modules written, three test suites passing.

**Phase 2 (experiment) — complete.** 100 cells in `data/results.csv`, produced by
`code/measure.py`. See REPORT §7a for what each tag holds and how the methods may
and may not be compared.

**Phase 3 (thesis) — chapters 1–7 written, 8 outstanding**, then the Zaključak and the two
abstracts. Chapter 7's findings are recorded in REPORT §7a, and chapter 8 argues from them.

### Done

- `config.py`, `create_graph.py`, `analyse_graph.py`, `heuristics.py`,
  `create_subgraphs.py`, `operators.py`, `source_context.py`, `evaluator.py`,
  `alns_optimizer.py`, `greedy_baseline.py`, `source_profile.py`, `sample_sources.py`,
  `run_experiment.py`, `calibrate.py`, `hop_layers.py`, `smoke_test.py`
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

### Phase 2 — done

- [x] Population sweep: all 28 measurement sources, one budget per out-degree band
- [x] Budget sweeps: two mid sources (k = 3…20) and one hub (k = 3…75)
- [x] Typical-budget cells at 20 / 35 / 50 % of each source's out-degree
- [x] Out-of-sample validation on every cell, with the SAA−MC gap recorded per row
- [x] Iteration probe (REPORT §7b) — the one result that changes the headline's hedging
- [x] Scaled re-run: 50 cells at `max_iter = min(100k, 2000)` → `data/results_scaled.csv`.
      A **chapter 7 result**, not a chapter 8 proposal — raising the budget globally was
      measured, and the gain was small on average and concentrated in the worst cells.
- [x] Improvement-share diagnostic on 5 cells → `data/iteration_probe.csv`

Not done, and chapter 8 material rather than gaps to fill before writing:

- [ ] Seed-to-seed spread. One RNG seed throughout, so tie-break variance is acknowledged
      and not measured. Do not imply otherwise in chapter 7.
- [ ] **Allocating iterations by need** — the successor to the scaled re-run, since that
      re-run is what rules out simply raising the constant (REPORT §7b, §8). Two-pass on
      the share/R combination, then the dynamic self-extending budget; the baseline spread
      is the cheap prior and the weakest of the three.
- [ ] The re-run selected by *loss against a baseline* rather than by cost. The scaled 50
      were the cheapest per stratum, so cheap ≈ converged, and "does more search rescue a
      struggling cell" still rests on the five probe cells.
- [ ] A σ-greedy baseline (REPORT §II.5).
- [ ] Do the greedy baselines reach the enumerated optimum on small sources (out ≤ 10)?
      Separates a weak *criterion* from a weak *search*.

### Next — Phase 3 (thesis)

Chapters, in the agreed structure:

- [x] Uvod
- [x] 1. Topologija i dinamika kompleksnih mreža
- [x] 2. Analiza mreže Bitcoin Alpha
- [x] 3. Formulacija problema SS-IMER
- [x] 4. Kriteriji odabira bridova
- [x] 5. Metode rješavanja
- [x] 6. Implementacija i eksperimentalni postav — 6.1 architecture, 6.2 frozen scenarios,
      6.3 source sample, 6.4 measures and protocol
- [x] 7. Rezultati i rasprava — written, four subsections, every number read from the CSVs
      at build time through `code/results_analysis.py`. Three figures
      (`fig7_1_saa_mc`, `fig7_2_k_sweep`, `fig7_3_scaled_gain`) from
      `code/make_result_figures.py`. The structure as agreed:
      - **7.1 Valjanost procjene** — the SAA−MC gap, median and spread, in both
        directions. First, because it says how much of any later difference is fitted to
        the frozen sample.
      - **7.2 Usporedba metoda** — tags `population`, `k-sweep`, `typical`; ALNS against
        each criterion individually (better/tied/worse and mean ΔR). The per-cell best
        baseline is an **oracle**, reported after the table and labelled a bound, never
        leading (REPORT §7a).
      - **7.3 Ovisnost o proračunu uklanjanja** — tag `k-sweep` only, R against k per
        source, the three sweeps never pooled.
      - **7.4 Utjecaj duljine pretrage** — `results_scaled.csv` paired per-cell against
        the same cells, the gradient by prior performance, and the four cells that got
        *worse*, which is 7.1's overfitting seen as a cost of search effort. State the
        selection bias before the result. Hands off to chapter 8.
- [x] 8. Mogućnosti poboljšanja i budući rad — three subsections, each tied to a source
      rather than asserted: 8.1 allocation by need (stagnation criteria, `hoos2004`),
      8.2 the σ-greedy (`kimura2008`, and `leskovec2007` for why lazy greedy does *not*
      port without submodularity), 8.3 the estimate and the seeds (`kleywegt2002`,
      `mak1999`). Four references added to `bibliography.py`, all verified against the
      published record.
- [ ] Zaključak, Sažetak, Summary. The Zaključak is a chapter (`ch09_*.py`); **Sažetak and
      Summary are front matter and are filled in the original .docx**, not generated.
- [ ] The AI-usage statement, also in the original — the template requires the technologies,
      their versions, the purpose, and a note on the extent of your own intervention.
- [ ] **The trim, last.** Body is ~36 pages against a target of roughly 30.

All 16 figures exist: `fig1_1` ER/WS/BA, `fig1_2` live-edge, `fig2_1` degree distribution,
`fig2_2` probability distribution, `fig2_3` bow-tie, `fig2_4` source reach, `fig2_5`
out-degree composition, `fig3_base/near/choke` the choke-point sequence, `fig5_1` ALNS loop,
`fig5_2` hop layers, `fig6_1` pipeline, `fig7_1` SAA vs MC, `fig7_2` the k-sweeps, `fig7_3`
the scaled gain. Anything chapter 8 adds goes in `code/make_result_figures.py` if it reads
data and in `thesis/figures.py` if it does not — and is drawn at its printed width with
body-sized type, as `thesis/figures.py` explains, or the lettering is unreadable on A4.

**Structure is fixed and subsections are not to be added.** The agreed outline above is
what the chapters follow; the first draft grew extra subsections for design dilemmas and
they were removed. A dilemma worth mentioning gets a sentence inside the relevant section,
not a heading of its own. The thesis describes the architecture as it stands — it is not
a history of the project, which now lives in Part II of [REPORT.md](REPORT.md).

**Calibration is not in the thesis.** It was run, every default held, and a tuning step
that changed nothing is not a result. Recorded in REPORT.md Part II instead.

**Numbers and settings are read at build time, never retyped.** Chapters 2, 4 and 5 read
`data/*.csv`; chapters 3, 5 and 6 read `code/config.py` through `thesis/params.py`, so
every parameter value in the prose is the one the code actually runs with.

**Cross-references resolve themselves.** Headings carry `label=`, the text asks for
`t.sec("label")`, and `build_thesis.py` renders twice — once to discover the numbers,
once to substitute them — because a chapter may point forward (3.3 points at 5.2.4). The
build refuses to save if any reference is still unresolved. Equations, figures, tables and
listings work the same way via `t.ref`, `t.figref`, `t.tabref` and `t.coderef`. Do not
write a section number by hand.

**The faculty template is the authority on format.**
`Završni_rad_predložak_lipanj_2026.docx` settles questions of citation style, captions,
heading depth and the rest — check it rather than guessing. What it has already settled:

- Two citation styles are permitted and **one must be used consistently**; this thesis uses
  author–year, so every new source goes into `bibliography.py` and is cited by key.
- **Every figure and table must be referenced in the text, and the reference comes before
  the block appears** — it is the announcement, not an afterthought. Three chapters
  violated this and were fixed; if you add a figure, add its `t.figref` too.
- Captions: figures below (`Sl. 7.1`), tables above (`Tablica 7.1`), equations numbered at
  the right margin and referenced as "izraz (25)". `doc.py` already does all three.
- **Heading depth stops at three levels** (7.4.1); do not nest deeper.
- A `Skraćenice` chapter is optional and this thesis does not have one. Worth considering,
  given ALNS, SAA, MC, IC, SS-IMER and ICM all appear.

**Length.** The body now runs about 36 pages against a target of roughly 30. Chapters 1–6
were about 34 before 7 and 8 were written, so the two result chapters cost less than the
ten pages budgeted for them — but the trim is still owed, and it comes out of prose rather
than out of substance. It is deliberately the **last** step, after the Zaključak and the
abstracts, so that nothing is cut twice.

---

## When to start a new chat

At a phase boundary, once this file and `git log` describe the state — which is the point
of keeping them current. Good moments: after a chapter is written and committed, after a
measurement run completes, after a design decision is recorded in REPORT.md. Bad moments:
mid-debug, or with uncommitted work, because the reasoning then exists only in the
conversation.
