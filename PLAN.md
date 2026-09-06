# PLAN — operational state

What is done, what is next, and how to run things. Rationale lives in
[REPORT.md](REPORT.md); this file is process state only.

**Read this first when starting a new chat.** Together with `git log` it is the complete
handoff — no earlier conversation needs to be reconstructed.

---

## Where this stands (2026-09-06) — the next job is a restructure, not a chapter

All eight chapters are written and the document builds, but a review on 2026-09-05/06 found
that **the thesis does not deliver what its own introduction promises**, and that the three
strongest results in the project are not in the text. The next session's job is to rewrite
around the two hypotheses, not to add material.

**The Uvod states two research questions.** Level 1: can adaptive search beat a fixed
topological criterion. Level 2: how far from the source do the edges worth removing lie.
Chapter 7 answers Level 1 and **never returns to Level 2**. That is an unkept promise an
examiner finds by reading the Uvod against chapter 7.

**Three findings exist, are measured, and are not in the thesis.** All three are written up
in [REPORT.md](REPORT.md) §7a, in the order they should be read:

1. **No choke point exists on this graph.** 2069 of 2075 multi-out-edge sources reach
   *exactly* 3618 nodes (= SCC + OUT, both already in 2.3); the best single hop-0 cut removes
   a median of 1 node, the best downstream choke anywhere removes 5. Fig 3.1–3.2 are true,
   fig 3.3 does not occur at scale. **This is the explanatory spine the thesis lacks** — it
   accounts for the Level-2 result, for why the probability criterion dominates, and for why
   σ₀ is small while raw reach is constant.
2. **The Level-2 answer is negative and well-supported.** Starved searches given more
   iterations converge to *pure hop 0* (source 96: 6 deep edges → 0, R 0.008 → 0.169; source
   123: 8 → 0, R 0.009 → 0.487). Cells that shed deep edges gained +0.107 against +0.009 for
   those that did not. The searches did not fail to explore deep layers — they explored and
   rejected them.
3. **The headline margin sits on the noise floor.** ALNS beats `probability` by +0.016; the
   median SAA−MC gap is +0.0159. 7.2 has been rewritten to say so and rest the claim on the
   win/loss record and the stratification instead.

**Still not done, and now worth more than when it was filed as future work:** the
scenario-subgraph analysis (REPORT §8). Comparing the live-edge realizations to the base
graph — edge retention, whether the giant SCC survives one percolation draw — is the missing
*empirical* link for finding 1. The base graph's "everything reaches everything" is a
property of the base graph only; the cascade travels the percolated graph. `create_subgraphs.
generate_scenarios` is deterministic from a seed, so this is a short script writing one CSV.

**The document is ~36 pages against a target of ~30**, so the restructure has to cut while it
adds. Measured section weights and a ranked trim list are below under **Length**.

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
- [x] 8. Mogućnosti poboljšanja i budući rad — four subsections: 8.1 allocation by need,
      8.2 competing versus complementary criteria (the probability/hop-distance argument),
      8.3 the σ-greedy (`kimura2008`, `leskovec2007`), 8.4 the estimate, seeds and the
      single-graph limitation (`kleywegt2002`).
- [x] 7.2 rewritten so the +0.016 margin is scaled against the +0.0159 noise floor, and the
      dominance of the probability criterion is explained rather than just reported.

### The restructure — what the next session actually has to do

- [ ] **Put finding 1 into chapter 2.** The reachability result (2069/2075 sources reach
      exactly SCC + OUT = 3618; best single cut removes 1 node) is a topology measurement and
      belongs beside the bow-tie section that already reports both numbers. Everything else
      then references it.
- [ ] **Write the Level-2 answer.** Either a 7.5 or folded into 7.4. The finding is negative
      and well-supported: deeper edges are a symptom of a search in trouble, and the searches
      that improved discarded them. Hedge with `ALNS_MAX_HOP_SCOPE = 3`, one seed, and the
      concentration in a few hub sources.
- [ ] **Re-point chapter 3.** Fig 3.1–3.3 stay as conceptual illustrations of why greedy
      fails on redundancy — that argument does not need the geometry to be common — but the
      text must not leave a reader expecting the search to find choke points that do not
      exist here.
- [ ] **Say in chapter 8 that the hop-scope wheel is a candidate for removal**, not tuning,
      and that a graph with a sparser core is how you would tell whether the idea or the
      instance was wrong.
- [ ] **Scenario-subgraph analysis** — the missing empirical link for finding 1. Short script,
      one CSV.
- [ ] Zaključak, Sažetak, Summary. The Zaključak is a chapter (`ch09_*.py`); **Sažetak and
      Summary are front matter and are filled in the original .docx**, not generated.
- [ ] The AI-usage statement, also in the original — the template requires the technologies,
      their versions, the purpose, and a note on the extent of your own intervention.
- [ ] **The trim.** See **Length** below for measured weights and a ranked list.

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

**Every citation was checked against the paper itself** (2026-09-05). Six of the then 24
entries had wrong metadata, three of them conflations of two different papers, so do not
add a source from memory — open it. The substantive claims held up; the three that did not
are recorded in the git history. The list is now 20, each carrying a claim nothing else
covers, and the rule going forward is: cite the paper you actually read, and prefer a
source already on the shelf over a stronger one you have not opened.

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

**Length — measured, not guessed.** 13 700 words of prose ≈ 34 pages, plus 16 figures and
4 tables; the built document is ~36. Target ~30. Weights as of 2026-09-06:

| chapter | words | % | | chapter | words | % |
|---|---:|---:|---|---|---:|---:|
| **5 Metode** | **2 451** | **18** | | 6 Implementacija | 1 372 | 10 |
| 7 Rezultati | 2 019 | 15 | | 8 Poboljšanja | 1 283 | 10 |
| 2 Bitcoin Alpha | 1 524 | 11 | | 1 Topologija | 1 244 | 9 |
| 4 Kriteriji | 1 443 | 11 | | Uvod | 647 | 5 |
| 3 Formulacija | 1 439 | 11 | | | | |

Ranked by value, largest first:

1. **Chapter 5 restates Røpke & Pisinger** — the roulette wheel, the three score increments,
   the weight-update formula and SA acceptance are all in the cited paper. Cut to what is
   needed to follow *our* adaptations. `Arhitektura i adaptivne težine` (592 w) and
   `Kriterij prihvaćanja` (355 w) are the dense spots; **keep** `Slojevi udaljenosti`
   (433 w), which is the one mechanism with no R&P counterpart. **−400 to −600.**
2. **Chapter 1** is textbook ER/WS/BA before the problem is stated. Keep equations and the
   one-line consequence of each, cut the narration. **−300.** Check with the mentor first.
3. **Chapter 6 `Arhitektura implementacije`** (527 w) is caching detail. **−150.**
4. Sentence-level tightening for the rest.

Three duplications were already removed on 2026-09-06 (the Uvod arguing ch3's choke-point
case, 5.1 restating 4.7's tie-breaking, the milder-intervention claim in both Uvod and 3.1).
The rule that found them: **the introduction may assert, a chapter argues** — repeat
conclusions, never arguments. The roadmap paragraph is not repetition and stays.

**Do not cut:** 2.6 (carries the population fix ch7 depends on), 7.1 (sets the threshold 7.2
now leans on), 7.4's selection caveat.

---

## When to start a new chat

At a phase boundary, once this file and `git log` describe the state — which is the point
of keeping them current. Good moments: after a chapter is written and committed, after a
measurement run completes, after a design decision is recorded in REPORT.md. Bad moments:
mid-debug, or with uncommitted work, because the reasoning then exists only in the
conversation.
