# Plan, clean short version

A fresh rewrite of the thesis body. Nothing is carried over from the 57pg or 66pg drafts
as text; only the **infrastructure** (build system, figures, data) is reused. The Uvod is
kept verbatim as you supplied it.

---

## 0. Style rules for the whole document

These bind every chapter. They are the difference between this version and the last three.

1. **No em dash.** Use a comma, a colon, or a full stop.
2. **Narrative, not catalogue.** Each section tells one thing and says why it matters for
   the goal of the thesis: cutting a source off from the network. If a paragraph does not
   serve that goal, it comes out.
3. **Explain on examples.** Every abstract idea gets a concrete instance first. The
   live-edge model is explained by walking through the six node graph in `Sl. 1.2`, not by
   defining a probability space.
4. **Student tone.** Plain sentences, first person plural where natural ("u ovom radu
   promatramo"), no inflated academic register, no hedging stacked on hedging.
5. **The report is raw material, not a source to copy.** `REPORT.md` holds far more than
   the thesis needs. A fact goes in only if the argument would be incomplete without it.
6. **Target: 8 000 words for the whole document, hard maximum.** That leaves roughly
   6 500 words of body prose once captions, tables, bibliography and front matter are
   counted. Page count follows from that and is not itself a target.
7. **Figures must be readable and used properly.** Each one is referenced in the text
   before it appears, and the text says what to look at in it. Width is set per figure so
   nothing is shrunk below legibility.

---

## 1. What gets reused, what gets rewritten

**Reused unchanged** — this is the "easiest way", and it is also what kills the
hallucination class:

| file | what it gives us |
|---|---|
| `thesis/doc.py` | headings, figure/table/listing numbering, captions, cross-references, template styles (TNR 12pt, 1.5 spacing) |
| `thesis/omml.py` | real Word equation objects, numbered `(n)` against the right margin |
| `thesis/bibliography.py` | citations written as `{kempe2003}` → "(Kempe i sur., 2003)"; bibliography auto-sorted |
| `thesis/build_thesis.py` | two-pass build so forward section references resolve |
| `code/results_analysis.py` | the grouping rules for `results.csv` (which tags may be pooled, what counts as a tie) |
| `figures/*.png` | all 16 figures, unchanged |
| `data/*.csv` | every number |

**Rewritten from scratch:** `ch01…ch08` → new `ch01…ch07`. This is where all the bad text,
the padding and the unreadable sentences live.

**Two mechanical guarantees worth stating, because they are why this restart is worth doing:**

1. **No number is typed by hand.** Every figure in the prose is read from a CSV at build
   time. If a number is wrong, it is wrong in the measurement, not in the writing.
2. **No citation is typed by hand.** Chapters write a key; the name and year are
   substituted at build time and the bibliography is generated from the same table. The
   first draft of chapter 1 had 8 of 15 citations pointing at the wrong source — that
   cannot recur.

One fix needed: `build_thesis.py` currently points `SOURCE` at
`Optimizacija protoka informacije u grafovima.docx`, which no longer exists. It will point
at the 57pg file (used only as a shell for the title page, Sažetak, Summary, the table-of-
contents field and the AI statement — the entire body between *Uvod* and *Literatura* is
replaced).

---

## 2. Structure — 7 chapters instead of 8

Two merges, both justified by the Uvod's own sentence *"Središnji dio rada opisuje kriterije
za prepoznavanje ključnih bridova **i** metode pretraživanja prostora rješenja koje ih
koriste"* — it already describes criteria and methods as one central part:

- old **4. Kriteriji** + old **5. Metode** → new **4. Kriteriji i metode rješavanja**
- old **6. Implementacija** shrinks to a short **5. Eksperimentalni postav**
- sub-subsections (Heading 3) are dropped everywhere except where the ALNS operators
  genuinely need them — flatter document, fewer headings eating pages

```
Uvod                                     580 w   (verbatim, yours)
1. Teorijska podloga                     650 w   2 figures
2. Mreža Bitcoin Alpha                   850 w   5 figures, 1 table
3. Problem SS-IMER                       700 w   3 figures
4. Kriteriji i metode rješavanja       1 400 w   2 figures, 2 tables, 1 listing
5. Eksperimentalni postav                400 w   1 figure
6. Rezultati i rasprava                1 350 w   3 figures, 4 tables
7. Mogućnosti poboljšanja                450 w
Zaključak                                280 w
                                     ─────────
body prose                             6 660 w   16 figures, 7 tables, 1 listing
captions, tables, bibliography, front    1 340 w
                                     ─────────
document total                         8 000 w
```

---

## 3. Chapter by chapter

### Uvod — 580 w, unchanged
Your text, verbatim. Only change: the six citations get wired to keys
(`{albert2002}`, `{castiglioni2021}`, `{coro2021}`, `{sheldon2010}`,
`{kumar2016,kumar2018}`, `{ropke2006}`) so they render identically but can never drift.

### 1. Teorijska podloga — 700 w
The minimum theory needed to state the problem. No detail that is not used later.

- **1.1 Od slučajnih do kompleksnih mreža** (350 w) — ER as the null model, then the two
  things real networks have that it does not: short paths with high clustering
  (small-world) and hubs (heavy tail). Told as a story about *why* both matter for
  spreading, not as a taxonomy.
  → **Sl. 1.1** `fig1_1_er_ws_ba.png` · eq. *L ≈ ln N / ln ⟨k⟩*, eq. *P(k) ~ k^−γ*
  → `{erdos1960}` `{watts1998}` `{albert2002}` `{predavanja}`
- **1.2 Nezavisni kaskadni model** (250 w) — the coin-flip-per-edge rule, then the
  live-edge trick: flip every coin *in advance* and the stochastic cascade becomes plain
  reachability in a fixed subgraph. This is the single most important idea in the thesis
  and gets a worked example rather than a definition.
  → **Sl. 1.2** `fig1_2_live_edge.png` · eq. σ as expected reachable set
  → `{kempe2003}`
- **1.3 Epidemiološki prag** (100 w) — λc = 1/λmax in two sentences, used once, in 2.2, to
  say the network is far above threshold.
  → eq. *λc = 1/λmax* → `{castellano2010}` `{antulov2008}`

### 2. Mreža Bitcoin Alpha — 900 w
- **2.1 Podaci i vjerojatnost prijenosa** (250 w) — what the dataset is, why only positive
  ratings, the sigmoid, and the fact that p takes exactly **ten** values (which is what
  makes tie-breaking a real problem in 4.2).
  → **Sl. 2.1** `fig2_2_probability_distribution.png` · eq. sigmoid → `{kumar2016,kumar2018}`
- **2.2 Struktura mreže** (350 w) — everything measured, compressed into one table plus
  two figures and a short reading of them. Includes the honest power-law result (beats
  exponential, loses to truncated power law / lognormal — reported, not hidden).
  → **Tablica 2.1** *(new)* measured properties: N, M, ⟨L⟩ vs ER, clustering vs ER, γ,
  λmax vs λc, SCC/IN/OUT, k-core, share of local bridges
  → **Sl. 2.2** `fig2_1_degree_distribution.png`, **Sl. 2.3** `fig2_3_bowtie.png`
  → `{clauset2009}` `{watts1998}` `{granovetter1973}` `{castellano2010}`
- **2.3 Populacija izvora** (200 w) — reach is a smooth continuum, not two groups; and
  most nodes cannot be a source at all (411 with out-degree 0; only 1184 of 3683 support
  even k = 3). This is what forces the stratified sample in ch. 5.
  → **Sl. 2.4** `fig2_4_source_reach.png`, **Sl. 2.5** `fig2_5_source_outdegree.png`
- **2.4 Topologija osnovnog grafa ne razlikuje bridove** (150 w) — **the finding that
  explains almost everything later.** Phrased as: *the reachable set is the same set for
  almost every source*, namely the core plus everything downstream of it, 3618 nodes. Six
  sources reach three or four nodes, and nobody is in between.

  The point is not the number, it is the consequence: if every source has the same
  reachable set, then the base graph carries almost no information about which edge
  matters. A bottleneck **can** appear once the coins are flipped, because a realization is
  a sparse random subgraph and a node there may hang on a single surviving edge. But that
  bottleneck belongs to that one draw, not to the network, so no criterion computed from
  the base graph can see it. Probability is the only one of our six that says anything
  about whether an edge is present in a realization at all.

  This is the spine of the results chapter: it explains in advance why the five topological
  criteria underperform, why `probability` wins, why the hop layers find no downstream
  choke point, and why σ is small and smooth while raw reachability is a constant. It also
  hands chapter 7 its strongest future-work item.

  *Currently buried in the REPORT and stated late. Moving it to ch. 2 is the single biggest
  structural improvement over the old drafts.*

### 3. Problem SS-IMER — 750 w
- **3.1 Definicija** (300 w) — IMER from Castiglioni, the exact-budget variant from Kimura,
  and the SS- prefix stated plainly as *our own name, not an established one*.
  → eq. σ(s, G), eq. *D\* = argmin σ(s, G∖D)*, eq. *R(D) = 1 − σ(D)/σ₀*
  → `{castiglioni2021}` `{kimura2008}` `{kempe2003}`
- **3.2 Zašto je problem težak** (300 w) — three reasons, one paragraph each:
  (a) evaluating one candidate cut exactly is #P-complete `{valiant1979}`;
  (b) no constant-factor approximation exists `{castiglioni2021}`, Theorem 6;
  (c) **the interesting one**: σ is *not* submodular in the removed-edge set, so greedy's
  1 − 1/e guarantee does not transfer. Shown on the 8-node example rather than argued:
  cut at the source → 8 → 7; cut the shared choke point → 8 → 4. That is increasing
  returns, exactly what greedy cannot see, and it is the entire reason for using ALNS.
  → **Sl. 3.1/3.2/3.3** `fig3_base_choke` / `fig3_near_choke` / `fig3_choke_choke`
  → plus one sentence pointing back to 2.4: *this geometry motivates the method, but does
  not occur at scale in Bitcoin Alpha* — so the reader is not left expecting ch. 6 to find it
  → `{kempe2003}` `{tong2012}`
- **3.3 Procjena dosega** (150 w) — frozen realizations; SAA drives the search, an
  independent MC set is what gets reported; why that split is not optional.
  → eq. σ̂ → `{kleywegt2002}` `{kimura2008}`

### 4. Kriteriji i metode rješavanja — 1 550 w
- **4.1 Šest kriterija** (400 w) — the table does the work; prose is one or two sentences
  per criterion saying *what it believes about the network*. Includes the two checkable
  predictions made in advance: degree should underperform (Kimura found blocking
  high-degree links is not necessarily effective) and spectral optimises the wrong
  quantity by construction.
  → **Tablica 4.1** six criteria, what each measures, distinct values on Bitcoin Alpha
  → 2 equations only (degree sum, spectral *u(i)·v(j)*), the rest in prose
  → `{granovetter1973}` `{tong2012}` `{kimura2008}` `{leskovec2007}`
- **4.2 Izjednačene vrijednosti** (150 w) — `bridge` takes 2 distinct values over 22 650
  edges, `probability` 10. So the tie rule *is* the method for half the criteria.
  Deterministic for baselines (reproducible), random for ALNS (or there is nothing to
  search).
- **4.3 Pohlepne metode** (150 w) — score once, take the top k incident to s. Their role:
  not straw men but the honest fixed-criterion opponent.
- **4.4 ALNS — petlja i adaptivne težine** (400 w) — destroy-and-repair, three independent
  roulette wheels, the score system (reward only *new* solutions, reward *both* operators
  because you cannot tell which caused the success), SA acceptance with the start
  temperature derived from the initial solution.
  → **Sl. 4.1** `fig5_1_alns_loop.png` · **Kôd 4.1** the loop as pseudocode
  → eq. *P(j) = w_j / Σ w_i*, eq. weight update, eq. SA acceptance → `{ropke2006}`
- **4.5 Operatori razaranja i popravljanja** (250 w) — Shaw / worst / random removal, the
  *y^p* draw, and the mapping of R&P's four relatedness terms onto edges.
  → **Tablica 4.2** the four terms and our counterparts · eq. *y^p* draw
  → plus a short honest list of the departures from R&P (the hop wheel is ours; repair
  samples where theirs is deterministic; q bounds scaled to k; cooling from our own budget)
- **4.6 Slojevi udaljenosti od izvora** (200 w) — the level-2 mechanism: candidates grouped
  by BFS hop of the edge's tail, one layer per iteration chosen by its own wheel, capped at
  hop 3 because mean path length is 3.74. States up front the confound that layers differ
  in size by up to 1900:1, so the *weights* cannot answer the question — only whether deep
  edges reach the winning cut can.
  → **Sl. 4.2** `fig5_2_hop_layers.png`

### 5. Eksperimentalni postav — 450 w
One chapter, no subsections. The pipeline figure carries the architecture; prose covers
the stratified source sample (15 calibration + 28 measurement, disjoint by construction),
one row per (source, k, method), both σ's always recorded, and reproducibility as a
*measured* property (the scaled re-run accidentally repeated cells at identical settings
and every one reproduced to the last decimal).
→ **Sl. 5.1** `fig6_1_pipeline.png`

### 6. Rezultati i rasprava — 1 400 w
Ordered so each answer is readable in light of the previous one.
- **6.1 Valjanost procjene** (200 w) — the SAA−MC gap: median ≈ +0.016, and *this sets the
  floor below which no difference is decisive*. Said here, before any comparison.
  → **Sl. 6.1** `fig7_1_saa_mc.png`
- **6.2 Usporedba metoda** (450 w) — ALNS against each criterion separately, then the
  stratification, then the oracle bound. **Leads with the honest problem**: the pooled
  margin over `probability` (+0.016) is the same size as the estimation error — stated
  before a reader can notice it — and then makes the case from the evidence that survives:
  the 60/13/22 record, and +0.094 / +0.062 on mid-reach sources turning to −0.022 only on
  the saturated ones, which 6.4 shows are starving. Closes with the strongest supported
  claim: ALNS ties the hindsight oracle to within a thousandth.
  → **Tablica 6.1** per criterion (better/tied/worse, mean Δ) · **Tablica 6.2** by reach class
- **6.3 Ovisnost o ograničenju** (200 w) — R against k per source, not pooled. Includes the
  non-monotonic dip as a *self-diagnosing* search failure: optimal R cannot decrease in k,
  so a dip is a missed optimum with no ground truth needed to see it.
  → **Sl. 6.2** `fig7_2_k_sweep.png`
- **6.4 Duljina pretrage** (300 w) — the scaled re-run: 15 improved / 23 unchanged / 5
  worse, cost factor 3.7 for a mean +0.016, and the gain concentrated entirely in cells
  that were doing badly. Also the four cells that got *worse* — the same overfitting 6.1
  measures, seen from the other side. And the selection caveat: the 50 cells were chosen as
  cheapest-per-stratum, and cheap correlates with already-converged.
  → **Tablica 6.3** by prior band · **Sl. 6.3** `fig7_3_scaled_gain.png`
- **6.5 Udaljenost korisnih bridova od izvora** (250 w) — **the Uvod's second promise, kept.**
  81 of 95 winning cuts are entirely hop 0; 89.4 % of all cut edges are hop 0; cuts
  containing a deeper edge score −0.123. And the decisive part: when starved cells are given
  more iterations they *actively replace* deep edges with hop-0 ones and improve sharply.
  Conclusion stated exactly as narrowly as the evidence allows, with all three hedges
  (cap at hop 3, one seed, deep cells concentrated in a few hubs), and tied back to 2.4 —
  the mechanism did not fail, the network has nothing for it.
  → **Tablica 6.4** *(new)* the three cells at 300 iterations vs. lengthened, with hop mix

### 7. Mogućnosti poboljšanja i budući rad — 450 w
Four items, one short paragraph each, no subsections. The first is new and is the one the
thesis genuinely earns:

1. **Kriteriji izvedeni iz realizacija, a ne iz osnovnog grafa** (the strongest item).
   Chapter 2.4 shows the base graph cannot distinguish edges, and chapter 6 shows every
   criterion built on it underperforms. The natural conclusion is that the useful structure
   lives in the realizations themselves: how much of the graph survives one draw, whether a
   giant component survives, and above all whether an edge is a bottleneck *in the
   realizations* rather than in the base graph. A criterion of the form "in how many of the
   500 realizations does the cut of this edge disconnect something" would be exactly the
   thing our six criteria are blind to, and it is cheap because the realizations are
   already frozen and reused. **We never ran this analysis, and it is the most useful
   single thing a next version could add.** Stated plainly as a gap, not as a result.
2. **allocate search effort by need** — a global constant is the wrong instrument (measured:
   ×3.7 compute for +0.016); the improvement-share diagnostic paired with a low R is the
   cheap detector, and the dynamic version extends a run that is still paying. Plus
   non-monotonicity in k as a second, free detector.
3. **σ-greedy** — Kimura's own method, the stronger opponent this thesis does not have;
   with the reformulation that avoids his sample loss on heterogeneous p (eq.)
4. **multi-seed confirmation and deeper hop scope** — what currently rests on one seed

### Zaključak — 300 w
What was asked, what was found, what it cost, and what it does not establish.

---

## 4. Length

**Settled: 8 000 words for the document as a whole, hard maximum. Page count is whatever
follows.** At the template's ~305 words per page that lands near 40 pages once the 16
figures and 7 tables are placed. Figures are sized individually for legibility rather than
shrunk to save pages.

The arithmetic below is kept only so we can see what any later change costs.

### Reference arithmetic

The template is A4, Times New Roman 12 pt, 1.5 spacing ≈ **300–305 words per full page**
(calibrated against your own 66pg draft: 14 948 w + 16 figures + 5 tables = 66 pages).

| | pages |
|---|---|
| body prose, 7 080 w | 23.2 |
| 16 figures + captions | 5.5 |
| 7 tables + captions | 2.5 |
| ~14 numbered equations | 1.2 |
| headings and caption spacing | 1.5 |
| **numbered body (1. → Zaključak)** | **≈ 34** |
| front matter (title, blank, Sažetak, Summary, Sadržaj) | 5 |
| Literatura + AI statement | 2.5 |
| **total** | **≈ 41** |

**So "8 000 words *and* all 16 figures" does not fit in 30 pages — it lands around 45.**
The plan above is set at ~7 000 words of body prose, which comes to ~8 000 for the document
as a whole once captions, tables, bibliography and front matter are counted, and lands at
**≈ 40–41 pages**. That is the top of your range.

Levers if you want it shorter, in the order I'd pull them:
- **figures at 11–12 cm instead of 14 cm** — the conceptual ones (1.1, 3.1–3.3, 4.1, 5.1)
  do not need full width. Saves ≈ 1.5 pages, costs nothing.
- **cut ch. 7 to a single page** (−200 w) and ch. 1 to 550 w (−150 w). Saves ≈ 1 page.
- **drop the three-panel choke-point example to two panels** — but I'd argue against it:
  the third panel *is* the non-submodularity argument, and it is the one place where the
  reason for choosing ALNS becomes visible rather than asserted.
- a hard 35 pages would mean ≈ 5 800 words, which starts costing explanation rather than padding.

**→ Decision needed: ~41 pages as planned, or shall I pull the first two levers and aim at 38?**

---

## 5. Things outside the body that still need doing

1. **Sažetak and Summary are still the template's placeholder text** ("Sažetak opisuje
   sadržaj rada, prepričan u stotinjak riječi"). Both need writing, ~100 words each plus
   keywords. I can draft them last, from the finished text.
2. **The AI usage statement is still placeholder.** The faculty template asks for the tools,
   versions, purpose, the extent of your own intervention, and *observed limitations or
   hallucinations*. Given the history of these drafts you have an unusually concrete and
   honest answer available. I can draft it; you must be the one to check and sign it.
3. **Four cited works have no PDF in the folder**: Valiant (1979), Kleywegt i sur. (2002),
   Clauset i sur. (2009), Leskovec i sur. (2007). Each carries a load-bearing claim
   (#P-completeness, SAA, the power-law fitting method, cost-effective outbreak detection).
   Either get the PDFs so the claims are checkable, or I re-route the claim through a source
   you do have.
4. **Four PDFs in the folder are not cited anywhere**: `Efficient Influence Maximization`,
   `gen-threshold-icdm11`, `srds03-virus`, `Antulov_ZS3V_2011-poster`. Tell me if any of
   them should earn a place — otherwise they stay out.

---

## 6. How we'll write it

Chapter by chapter, in order, each one built and shown to you as a `.docx` before moving on
— so a wrong tone or a wrong level of detail is caught at chapter 1 rather than at chapter 7.
Every chapter is a Python module that reads its numbers from `data/`, so the final document
is reproducible with one command and cannot drift from the measurement.
