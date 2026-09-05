# REPORT — thesis-facing working document

The single source of truth for what goes into the thesis: decisions and why, and pointers
to the CSV that holds each number. It is raw material for the text, not the text.

**Provenance rule.** Numbers live in `data/*.csv`, produced by the code in this repository,
and are never retyped here or into the thesis by hand. The thesis chapters read their
figures from those CSVs at build time for exactly that reason. Nothing from
[PILOT_TESTS.md](PILOT_TESTS.md) is a measurement of this system — see the warning at the
top of that file.

Written in English for precision; translated when drafting the Croatian chapters.

**How this file is organised.** Part I is the settled content the thesis draws on — the
final architecture and the claims it supports, with nothing about how we got there.
Part II is what a future coding session needs to know: the bugs this codebase has already
paid for, the lessons that shaped the design, and the work that is deliberately not done.
Part II is *not* thesis material. If something in Part II starts mattering to the argument,
promote it to Part I first.

---

# Part I — thesis content

## 1. Problem scope

- **SS-IMER** = Single-Source Influence Minimization by Edge Removal. Fixed source `s`,
  budget `k`, remove `D ⊆ E` with `|D| = k`, minimize `σ(s, G\D)` under Independent
  Cascade.
- The `SS-` prefix and the exact-cardinality budget are **this thesis's own**, not an
  established name. Say so explicitly (the Uvod does).
- **Castiglioni et al. (2021)** define IMER as their Definition 4: general seed set `S`,
  budget `|E'| ≤ B`, maximize the drop `χ(S,E) − χ(S,E\E')`. Their **Theorem 6** is the
  hardness result the thesis uses: for any constant ρ there is no polynomial-time
  ρ-approximation to IMER with finite budget unless P = NP. They ran no experiments, so
  there is no protocol or baseline to inherit from them.
- **Kimura et al. (2008)** is the nearest algorithmic ancestor. His objective is
  `c(G) = (1/|V|) Σ_v σ(v; G)` — averaged over *every node as a source* — and his budget
  is exact (`|D| = k`), which is where our exact budget comes from. State the adaptation
  explicitly: single fixed source, not a direct instance of his problem.
- **Kempe et al. (2003)** supplies the IC model, the live-edge equivalence, NP-hardness of
  influence maximization (Theorem 2.4), and the submodularity that licenses the greedy
  `1 − 1/e` guarantee **over seed sets**. They also state that computing σ exactly is an
  open question and estimate it by simulation.
- **Valiant (1979)**: two-terminal network reliability is #P-complete. Since
  `σ(s,G) = Σ_w Pr[w reachable from s]`, each term is exactly that problem, so evaluating
  one candidate cut exactly is intractable. This is the cleanest statement of why the
  objective must be estimated.
- **Tong et al. (2012)** optimise the leading eigenvalue, not σ, so their method does not
  transfer. Used for two things only: the edge score `u(i)·v(j)` (their Algorithm 1, with
  Lemma 3's first-order justification), and their own remark that the effect of removing a
  *set* of edges is not the sum of the individual effects.

### 1.1 Why greedy has no guarantee here

The `1 − 1/e` result rests on σ being monotone and submodular **as a function of the seed
set**. As a function of the **removed-edge set** it is not: with two redundant gateways
out of `s` into the same region, removing either alone changes almost nothing and removing
both changes a great deal, so the second edge's contribution is *larger* on the larger set.
That is increasing returns, the opposite of what greedy needs.

This is the argument for using a method that changes several edges at once, and it is
illustrated in the thesis on the smallest graph where it is visible (fig 3.1): at `k = 1`,
cutting at the source gives 8 → 7 while cutting the shared downstream choke point gives
8 → 4.

## 2. The dataset

Bitcoin Alpha, SNAP, introduced by Kumar et al. (2016, 2018). Positive-rated edges only;
a negative rating expresses distrust and cannot be assumed to carry a cascade the same way.
Rating → probability by the sigmoid in thesis 2.1. Duplicate (source, target) pairs are
resolved by keeping the most recent rating (`config.DUPLICATE_EDGE_POLICY`).

All measured properties are in `data/topology_summary.csv` and `data/edge_features.csv`
and are read into chapter 2 at build time. The ones that carry argumentative weight later:

- **The transmission probability takes exactly ten values**, because it is derived from an
  integer rating, with the lowest covering ~61% of edges. This is what makes tie-breaking
  a real design question rather than a detail (thesis 4.7).
- **The degree distribution is heavy-tailed with a finite cutoff, not scale-free without
  qualification.** The power-law fit (Clauset, Shalizi & Newman method) beats an
  exponential decisively but loses to the truncated power law, lognormal and stretched
  exponential. Report the honest version — it is a strength that the comparison was run.
- **The network is deep in the supercritical regime** (λmax of the probability-weighted
  matrix ≫ 1), so a cascade from a well-connected source will not die out on its own. The
  problem is therefore *separating the source from the core*, not slowing the network down
  — which is also why the objective is reach from one source and not the spectral radius.
- **Mean shortest path 3.74**, which is what justifies bounding the search at hop 3.
- **Granovetter local bridges are 32.1% of edges.** Louvain communities are descriptive
  only and never a criterion: the partition varies run to run, so a criterion built on one
  arbitrary partition would not be reproducible.

### 2.1 The source population (`data/source_profile.csv`)

Measured for all 3683 nodes. Two facts constrain what the experiment can even ask:

- **Reach is a smooth heavy-tailed continuum, not bimodal.** Deciles run 1.0, 4.6, 10.0,
  14.0, 22.5, 35.8, 66.0, 127.8, 323.3, 598.3. About 47% of eligible sources sit between
  σ₀ 10 and 100; ~16% are saturated at 400+.
- **Most of the graph cannot be a source at all.** 411 nodes have out-degree 0 and a
  further 2088 have 1–3, and since `k ≥ out(s)` is the trivial isolated case, only 1184 of
  3683 can support even `k = 3` — dropping to 500 for `k = 10` and 230 for `k = 20`. That
  bound is a property of the degree distribution and belongs in the thesis.

Out-degree predicts reach strongly but not deterministically (5% of the smallest band is
saturated against 99% of the largest), which is why the sample stratifies on **both** axes.
The off-diagonal cells — few out-edges but saturated reach — are the redundant-fan-out
geometry §1.1 describes, and where hop0-only quarantine should struggle most.

## 3. The six criteria

| Criterion | What it measures | Level |
|---|---|---|
| Random | nothing (control) | per call |
| Transmission probability `p` | reliability of the channel | global |
| Degree sum `out(u)+out(v)` | proximity to hubs | global |
| Granovetter local bridge | absence of a detour (endpoints share no neighbour) | global |
| Betweenness from the source | share of shortest paths out of `s` | per source |
| Spectral `u(i)·v(j)` | contribution to the spectral radius | global |

Distinct values over 22 650 edges: spectral 20 480, degree sum 407, probability 10,
bridge 2. That spread is the quantitative statement of the tie problem.

**Criteria never read the sampled realizations.** They are computed from the base graph
only. If a criterion were derived from the same realizations that define the objective,
the same sampling noise would enter both the objective and the candidate choice, and they
would stop being independent checks on each other.

**Two expectations worth stating before the results.** Kimura found that blocking links
between high-out-degree nodes is *not* necessarily effective, so the degree criterion is
expected to underperform — a checkable prediction, not a hedge. And the spectral criterion
optimises the wrong quantity by construction (λmax governs the whole network's threshold,
not reach from one source), so it is included as a structurally motivated candidate whose
usefulness here is an empirical question.

### 3.1 Tie-breaking is a policy, not a fix

Two rules, deliberately different:

- **Baselines are a deterministic rule**: sort by `(score desc, u asc, v asc)`, so one
  (source, k, criterion) has exactly one answer forever, which is what makes the method
  comparison reproducible.
- **ALNS operators are a sampler**: ties broken uniformly at random from the run's seeded
  RNG. A deterministic tie-break there would make `bridge` and `probability` return the
  identical cut every run, leaving nothing to search.

One shared `rank(edges, scores, endpoints, rng=None)` implements both, so the two paths
cannot silently drift apart.

**Report, do not average away.** Tie-group size at the cutoff (split into taken and left
behind) is recorded per baseline run; the σ/R spread across ALNS seeds is reported as a
property of the method.

## 4. ALNS, and where it departs from Røpke & Pisinger

Everything below was read from the paper, not from paraphrase.

**Roulette-wheel selection (§3.3, eq. 20).** `P(j) = w_j / Σ w_i`. Removal and insertion
operators are selected **independently** — R&P's own design, not our addition.

**Score system (§3.4).** Segments; scores reset to 0 at the start of each. A heuristic's
score rises by exactly one of σ1 (new global best), σ2 (better than current, unvisited),
σ3 (worse than current but accepted, unvisited). **Only unvisited solutions are rewarded**
— they hash every solution; we hash `frozenset(D)` per run. **Both** the destroy and the
repair heuristic get the same increment, because you cannot tell which caused the success.
A Δ=0 move scores nothing: it fits none of the three cases.

**Weight update (§3.4).** `w_{i,j+1} = w_{i,j}(1−r) + r·(π_i/θ_i)`. If `θ_i = 0` the
weight is unchanged — an edge case the paper leaves unstated.

**SA acceptance (§3.5).** Accept if Δ ≤ 0, else with probability `exp(−Δ/T)`; `T = T·c`
each iteration. Start temperature is derived from the initial solution rather than set:
`T_start = w·z' / ln 2`, so a solution `w`% worse than the initial is accepted with
probability 0.5. This matters here because reach varies by three orders of magnitude
across sources, so one fixed temperature would be wrong for almost every source.

**Destroy operators (§3.1, Algorithms 2–3).** Shaw (related) and Worst removal rank a list
`L` and pick `L[⌊y^p·|L|⌋]` with `y ~ U[0,1)`; larger `p` is greedier, `p → 1` approaches
uniform. Random removal is Shaw with `p = 1`, implemented separately as R&P do.

**Shaw relatedness is their eq. (17)**, four terms each scaled to [0,1], with their tuned
(φ, χ, ψ, ω) = (9, 3, 2, 5). The mapping onto SS-IMER, where a "request" is an edge and
its two locations are the tail and the head:

| R&P term | weight | our counterpart |
|---|---|---|
| φ location | 9 | do the two edges share a tail / a head |
| χ time | 3 | BFS hop of each endpoint from `s` — under IC the earliest a node can be reached *is* its hop |
| ψ load | 2 | the edge's transmission probability |
| ω servable set | 5 | overlap of the bounded downstream territory each edge feeds, by R&P's own min-normalised overlap coefficient |

The ω term is what makes the measure work at all here: within one hop layer every tail is
`s` and every head is one step away, so φ and χ are constant by construction, and without
ω relatedness collapses to `|p_a − p_b|` over ten discrete values. Territory is bounded at
depth 2 for the same reason R&P bound `K_i`: on a graph whose SCC holds 86.7% of nodes the
unbounded descendant set is nearly everything for nearly everyone, and every pair would
look identical.

**Repair** is one operator per criterion, using the same `y^p` draw.

### 4.1 Deliberate departures — list these honestly, do not claim unqualified fidelity

1. **The hop-scope wheel has no R&P counterpart at all.** They have exactly two operator
   families; ours is a third, scored by their rule but not their idea.
2. **Repair uses the `y^p` sampler**, where R&P's insertion heuristics are deterministic.
   Forced by our discrete, heavily-tied scores: a literal transplant would make `bridge`
   and `probability` return one fixed cut. The ranking is shuffled *within tied bands only*
   before the draw, which keeps their selection rule intact.
3. **q bounds proportional to k**: `q_min = max(1, ⌊0.1k⌋)`, `q_max = min(k−1, ⌊0.4k⌋)`.
   R&P's literal `4 ≤ ρ` is undefined for budgets as small as ours.
4. **Cooling rate derived from our own iteration budget**, not their c = 0.99975, which
   only makes sense against their 25 000 iterations (at 300 it would barely cool).
5. **Worst removal ranks once** where Algorithm 3 re-sorts inside the removal loop. A cost
   decision: doing it literally costs one full marginal pass per pick. Shaw removal *does*
   re-rank each step, because there it is the operator's defining feature and costs only
   dict lookups.
6. **The noise term (§3.6) is not ported** — defined against a continuous distance matrix,
   with no analogue here.

### 4.2 Hop layers

An edge belongs to layer `h` if its tail is `h` BFS steps from `s`. Layer 0 is exactly the
baselines' candidate set. Repair draws from **one layer per iteration**, chosen by a third
roulette wheel updated by R&P's rule; if that layer cannot supply enough, the remainder
comes from the others so `|D| = k` always holds. A layer is credited only for edges it
actually supplied, and when several contribute, **each gets the full increment** — R&P's
own rule for an unattributable success. Splitting it proportionally would assume σ is
divisible across a cut's edges, which is precisely the non-submodularity of §1.1.

**Layers start equally weighted**, because how far from the source it pays to look is the
question being asked, and seeding a prior would assume the answer.

**Depth is capped at 3.** Justification for the thesis, in one or two sentences: the mean
shortest path is 3.74, so by hop 3 the pool already holds most of what is reachable from
the source, while each deeper layer multiplies the candidate set without adding edges that
could plausibly close the source off. (`data/hop_layers.csv` has the per-source layer sizes
if a number is ever wanted.)

**What the learned weights may and may not support.** Layer sizes differ by up to three
orders of magnitude, and the `y^p` draw picks expected rank `|L|/(p+1)`, so one `p` does
not mean the same thing in a 10-edge layer and a 10 000-edge one. A higher learned weight
for hop0 therefore partly measures that hop0 is *easier to search*. The Level-2 question is
consequently **"do edges beyond hop0 reach the winning cut?"**, answered by `hop_mix` and
`best_hits_by_hop`, not by `scope_weights`. The confound is asymmetric and works in our
favour: a positive finding is *strengthened* by it (found despite a search disadvantage),
while a negative finding cannot distinguish "deeper edges are useless" from "deeper layers
are too big to search" and must be hedged.

## 5. Estimating reach

σ is estimated on **frozen** live-edge realizations: draw the sample once, then score every
candidate cut against that same sample. Two consequences, both load-bearing:

- the objective becomes **deterministic**, so a difference between two cuts reflects their
  quality rather than sampling noise — without which the search could not compare two close
  solutions at all;
- the optimum found is the optimum **of the sample**, so it must be validated on an
  independent one.

Hence two disjoint sets: SAA (500, seed 42) drives the search; MC (2000, seed 999) is used
only for the reported result. Kimura's bond-percolation estimator is the same idea and is
the citation for it.

Verified properties (`code/test_scenarios.py`): byte-for-byte reproducible from the seed,
adjacency order included; the two sets share no realization; a full run leaves every
realization bit-identical.

## 6. Experiment design and protocol

**The sample** (`data/sample.csv`, `code/sample_sources.py`): stratified on
(out-degree band × reach class), drawn once under one seed, calibration taken first and
measurement from the remainder so the two are disjoint **by construction**. 15 calibration
+ 28 measurement sources. Each row carries `predicted_seconds`, so a plan can be costed
before it is run — runtime tracks σ₀, not source count, and one saturated source costs
about twenty-five low-reach ones.

**Not one uniform matrix.** A dedicated k-sweep on a few representative sources, plus a
curated set of (source, k) showcases each chosen to demonstrate a specific phenomenon, with
the reason recorded per row.

**One row per (source, k, method).** Never a column that pools a method with its own
competitors — "best baseline" and "oracle" are `groupby` operations performed after
measurement, not columns written during it. Every resolved ALNS parameter travels with the
row, so a variant is identifiable from the row alone.

**Both σ's always recorded**, plus their gap. SAA is what the search optimised, MC is what
gets reported, and they have been measured disagreeing; writing only one would hide
overfitting rather than measure it.

**`stop_reason` marks trivially-solved instances** (`k ≥ out(s)`, source isolated, σ = 1,
provably optimal) so they can be excluded from averages they would otherwise flatter
equally.

**Deterministic baselines are computed once** per (source, k) and reused across ALNS seeds;
only `random` and ALNS vary with the seed.

## 7. What the comparison does and does not establish

Our six baselines are (a superset of) the heuristics **Kimura published as his weak
comparison methods** — betweenness, out-degree, random. The method he actually *proposed*
is a sequential greedy over the measured objective with re-evaluation at each step, and it
is not in our comparison. So the thesis answers *"can adaptive search beat a fixed
topological criterion?"* and must not imply it beats the state of the art. Say this plainly.

Two further honest notes:

- **Kimura's betweenness baseline recalculates** after each removal (Newman–Girvan style);
  ours is one-shot top-k on a static, source-rooted score. Defensible — recomputation
  inside the loop is forbidden by the cost model — but state it as a difference.
- **His efficiency trick does not port.** He estimates `c(G_i(e))` by averaging over only
  those scenarios where `e` was unoccupied, which keeps 80–97% of his sample at a uniform
  p = 0.2/0.03. Our `p` reaches 0.993, where that estimator retains ~3.4 of 500 scenarios —
  and high-`p` edges are precisely the ones worth cutting. Porting his method to a
  heterogeneous-`p` network is a genuine finding, not an implementation detail.

## 8. Deliberately not done — material for chapter 8

- **A σ-greedy baseline** (Kimura's own proposed method), which is the stronger opponent
  and the one that would make §1.1's argument empirical rather than cited. The exact
  reformulation that avoids his sample loss is derived in §II.5 below.
- **Scenario-subgraph analysis**: how SAA and MC realizations compare to the full graph
  (edge retention, density, whether giant-component structure survives one percolation
  draw). Belongs at the head of the results chapter as methodology validation.
- **Parameter calibration is not thesis content.** It was run (`data/calibration.csv`),
  every default held, and nothing changed — so it is a tuning step, not a result, and is
  left out of the text. Details in §II.6.
- **Multi-seed confirmation** of anything currently resting on one seed.

---

# Part II — history and working notes

Not thesis material. This is what a future session needs so the same ground is not
re-covered, and so the bugs below are not reintroduced.

## II.1 Bugs this codebase has already paid for

Each was real, each is fixed, and each is now defended by a test or a structural guard.

- **Index misalignment** between igraph's internal vertex order and any separately built
  array. This is the bug class that produces a plausible wrong number with no exception.
  Guarded structurally: `verify_vertex_alignment` runs on every graph construction and
  `verify_feature_alignment` on every feature load, both raising immediately.
  `code/test_features.py` additionally rebuilds the graph with vertices inserted in
  shuffled order and requires per-*named*-edge scores to be unchanged.
- **A source-blind evaluator cache.** `evaluate_reach` was keyed on the cut alone, but
  reach is a function of the source too, so one evaluator reused across sources returned
  the previous source's answer — a 15× error with a plausible-looking value. Now keyed on
  `(source, cut)`, with a regression test running a shared evaluator against per-source
  ones. No published result was affected, but it would have fired the moment
  `run_experiment.py` reused an evaluator, which is the obvious optimisation.
- **`destroy_related` was `destroy_random` with extra steps.** Three of R&P's four
  relatedness terms were implemented; the missing ω is the only one that varies inside a
  hop layer. Measured on 20-edge hop0 cuts, 190 pairs: 2 distinct relatedness values on the
  out-degree-486 hub. After restoring ω and the head half of χ: 29 and 161. This is why
  R&P's tuned (9,3,2,5) is usable — equal weights had been a symptom of the missing term,
  not a choice.
- **`ctx.edges_by_hop[0]` raised KeyError** for out-degree-0 sources (411 of 3683).
- **R&P's visited-set aliased `evaluator.cache`**, which raised TypeError on a cacheless
  evaluator and would have leaked one run's visited solutions into the next.
- Do not reintroduce: rewarding a Δ=0 move as an improvement; comparing ALNS against a
  "best peer" pool containing ALNS itself; sharing one heuristic between destroy and
  repair; un-seeded RNG anywhere.

## II.2 The hop-horizon failure

The first version of the Level-2 mechanism was an expanding horizon: start at hop0∪hop1,
widen whenever the frontier layer's average reward exceeded zero. It actively destroyed the
search, and the diagnosis is worth keeping because the failure mode is subtle.

**The expansion predicate was vacuous.** σ1/σ2/σ3 are positive and every other outcome
scores 0, so rewards are non-negative *by construction*; "expand if average reward > 0"
reduces to "expand if any reward ever occurred", which is nearly always true. The horizon
ratcheted open every segment and, with no contraction rule, never closed. Flattening the
layers into one pool then diluted the search — once the horizon reached hop 5–6 the pool
approached the whole reachable edge set and the handful of hop0 edges that actually close
the source were drowned out. It also caused a 750 s runtime outlier.

Measured against enumerable ground truth on small sources (one seed, a diagnostic and not
an experiment): hop0-only fixed was exactly optimal 8/8, hop0∪hop1 fixed 5/8, the adaptive
horizon 1/8 with a mean gap of 155%. So the operators, weights, acceptance and evaluator
were all sound and the horizon policy alone was responsible.

The replacement — one layer per iteration chosen by its own wheel — cannot run away, since
a layer that stops paying is simply down-weighted, which gives contraction for free.

## II.3 Runtime and the cost model

One ALNS run costs roughly `sweeps × scenarios × per-BFS-time`, where per-BFS-time scales
with the source's **reach**, not its out-degree. Low-reach sources are cheap and saturated
ones dominate any budget.

Four fixes took a k=20 run from ~270 s (and a 750 s pathological case) to ~65 s, each found
by profiling rather than guessed:

1. **One-pass marginal values.** `destroy_worst` needs σ(D\{e}) for every e in D; naively
   that is |D|+1 sweeps and was ~237 s of a ~270 s run. Restoring one edge can only add
   nodes reached *through* it, so the gain is provably zero unless the edge survived
   percolation, its tail is reached and its head is not. Measured at 1.0× one evaluation
   instead of 21× at k=20, and verified exact against the naive version.
2. **The cut mask is a reused list indexed by node id**, not a dict keyed by tail: a
   traversal probes every node it pops (~135M probes per run) while D touches at most k
   tails.
3. **`select_q` ranks once** instead of per pick; tie-shuffling uses a random sort key
   rather than `random.shuffle`, which profiled at 4% of total runtime on its own.
4. **The candidate pool is cached per layer** rather than rebuilt, scored, filtered and
   sorted every iteration.

Rule of thumb that follows: **anything computable from the static graph is computed once
and cached, never inside an ALNS iteration.** SAA fitness is the one unavoidable
per-iteration cost.

## II.4 Test coverage, and what each test defends

- `test_evaluator.py` — the evaluator against an independent igraph oracle (each scenario
  rebuilt as a real graph, cut edges deleted, `subcomponent(mode="out")` as ground truth);
  one-pass marginals against the naive computation; monotonicity in the cut; the reusable
  cut buffer left clean; caching never changing an answer.
- `test_features.py` — spectral index alignment three ways: invariance to vertex insertion
  order (worst relative gap 4.5e-15), rank correlation with the measured λmax drop
  (Spearman 0.965 over 180 edges), and CSV against fresh computation (2.3e-14).
- `test_scenarios.py` — reproducibility, SAA/MC independence, and immutability of both the
  frozen scenarios and `SourceContext`'s shared tables under a full search.

Note that `@dataclass(frozen=True)` prevents attribute rebinding only; the dicts inside
stay mutable, which is why immutability is tested rather than assumed.

## II.5 The σ-greedy, if it ever gets built

Kimura's eq. (6) does not port (Part I §7). The fix keeps his insight without the sample
loss: blocking `e` changes a scenario only if `e` was occupied in it, so

```
σ(D ∪ {e}) = (1/M)[ Σ_{m: e absent} reach_m(D) + Σ_{m: e present} reach_m(D ∪ {e}) ]
```

The first sum is free from a single base pass; only the second needs recomputation, on a
`p_e` fraction of scenarios. Exact, full sample. Estimated ~5 s for a small source
(out=9, k=5) and ~2.7 min for the out-degree-486 hub at k=20, against ~25 min naive. Being
deterministic, it would be computed once per (source, k) and reused across seeds.

## II.6 The calibration that changed nothing

Run once against a 30-minute wall-clock budget, following R&P's own one-at-a-time
procedure on the calibration sources, one per cell, cheapest member — chosen by structure
and cost, never by outcome.

**The first attempt was worthless and the reason is instructive.** It used k=3 everywhere,
where the q bounds collapse to (1,1): destroy removes one edge and repair returns one, so
from a fixed warm start every parameter setting walked to the same cut on 6 of 8 cells,
identical to four decimals. Parameters cannot express a difference in a 1-swap. Kept as a
finding in `data/calibration_k3.csv`; the tuning budget became `k = min(10, out(s)−1)`.

The rerun is in `data/calibration.csv`. Judged on **paired per-cell change**, not the
median level, which was pinned by two frozen middle cells:

```
repair_p=20       +0.0014
repair_p=60       -0.0000
max_hop_scope=1   +0.0011
q_max_frac=0.7    +0.0025
max_iter=150      -0.0114   <- clearly worse, one cell losing 0.073
```

So every default stands, and `max_iter=300` is positively supported rather than merely
un-refuted. Single seed and eight cells, so only large effects are distinguishable — which
is why the decision rule was "change nothing without a clear margin", and why this is a
tuning step rather than a result.

`ALNS_MAX_HOP_SCOPE = 3` was inherited rather than derived and the sweep did not overturn
it; the thesis justifies it structurally instead (Part I §4.2).

## II.7 Settled scope decisions

- **No `fixed_hop_scope` ablation.** A winning cut will in general contain a hop0 edge, so
  hop0-only versus hop2-only is not where the evidence lies; `hop_mix` and
  `best_hits_by_hop` answer the Level-2 question on the adaptive runs. The knob stays in
  `run_alns` as a diagnostic.
- **igraph, not networkx.** The per-iteration hot loop uses neither (a hand-rolled BFS over
  plain Python adjacency beat both), but igraph's C backend genuinely wins on the one-time
  per-source precomputation.
- **Louvain is descriptive only** — tested as a criterion and found near-null once measured
  correctly; the earlier apparent signal was an artifact of one arbitrary partition.

## II.8 Reading the papers

`pdftotext`/poppler is not installed on this machine. `pypdf` works and is installed in
`.venv` as a reading tool — deliberately **not** in `requirements.txt`, since it is not a
dependency of anything the project runs.
