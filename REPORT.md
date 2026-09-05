# REPORT — thesis-facing working document

The single source of truth for what goes into the thesis: decisions and why, and pointers
to the CSV that holds each number. It is raw material for the text, not the text.

**Provenance rule.** Numbers live in `data/*.csv`, produced by the code in this repository,
and are never retyped here or into the thesis by hand. Chapter 2 of the thesis reads its
figures from those CSVs at build time for exactly that reason. Nothing from
[PILOT_TESTS.md](PILOT_TESTS.md) is a measurement of this system — see the warning at the
top of that file.

Written in English for precision; translated when drafting the Croatian chapters.

**On the numbering.** Sections are in the order they were written, which is why the
sequence runs 1–5, 6a–9a, then 6–18. The code no longer cites section numbers, so
renumbering would now be safe — but every internal cross-reference would have to be
remapped at the same time, and a pointer that silently resolves to the wrong section is
worse than an ugly sequence. The index below is grouped logically instead.

---

## Index

**Problem and scope**
- [§1 What SS-IMER is and isn't](#1-problem-scope--what-ss-imer-is-and-isnt)
- [§8c Level-2 hypothesis, corrected framing](#8c-level-2-hypothesis--corrected-framing-supersedes-the-original-phrasing)
- [§15 What the baseline set should be](#15-what-the-baseline-set-should-be--read-from-kimura-castiglioni-and-tong)

**The data**
- [§9a Duplicate edges in the raw data](#9a-duplicate-edges-in-the-raw-data)
- [§5 Numbers — which CSV holds what](#5-numbers)
- [§18 The source population](#18-the-source-population--measured-and-it-changed-the-sampling-design)

**Method decisions**
- [§2 Heuristic portfolio](#2-heuristic-portfolio--whats-in-it-and-why)
- [§3 Tie-breaking policy](#3-tie-breaking-policy--must-be-documented-in-the-thesis-not-fixed)
- [§6a ALNS core mechanism, verbatim from R&P](#6a-alns-core-mechanism--verbatim-from-røpke--pisinger-2006)
- [§7a Where our portfolio doesn't map onto R&P](#7a-where-our-heuristic-portfolio-doesnt-map-cleanly-onto-rp--decided)
- [§14 R&P fidelity audit, term by term](#14-rp-fidelity-audit--read-from-the-paper-term-by-term)
- [§12 The hop-horizon mechanism was broken](#12-the-hop-horizon-mechanism-was-broken-and-how-we-found-out--thesis-relevant)
- [§13 k ≥ out(s) is the trivial case](#13-k--outs-is-the-trivial-case-not-an-error)
- [§16 Two settled scope decisions](#16-two-settled-scope-decisions)

**Implementation**
- [§8a Graph library and the alignment guard](#8a-graph-library--igraph-with-a-structural-not-one-off-alignment-guard)
- [§8b Heuristics use full-graph metrics only](#8b-heuristics-use-full-graph-metrics-never-saamc-scenario-derived-metrics--why)
- [§8 Precomputation](#8-precomputation--saa-fitness-is-the-only-expense-thats-allowed-to-be-expensive)
- [§7 Scenario architecture](#7-scenario-architecture-and-candidate-space--corrections-supersedes-earlier-draft-of-6)
- [§11 Runtime cost model](#11-runtime--cost-model-what-was-fixed-and-what-it-cost-us-to-learn)
- [§4 Known bugs not to reintroduce](#4-known-bugs-from-the-pilot-phase--do-not-reintroduce)
- [§17 Phase 1 smoke tests](#17-phase-1-smoke-tests--the-two-that-could-have-invalidated-a-calibration)

**Experiment**
- [§9 Experiment design](#9-experiment-design--curated-showcases-not-one-uniform-matrix)
- [§10 Calibration is itself thesis content](#10-alns-parameter-calibration--is-itself-thesis-content)

**Superseded, kept for the record**
- [§6 Open items](#6-open-items-to-confirm-beforewhile-coding) — both resolved; the hop
  horizon it discusses was removed in §12

---

## 1. Problem scope — what SS-IMER is and isn't

- SS-IMER = Single-Source Influence Minimization by Edge Removal. Fixed source `s`,
  budget `k`, remove `D ⊆ E`, `|D| = k`, minimize `σ(s, G\D)` under Independent Cascade.
- **Precision needed vs. Kimura et al. (2008):** Kimura's contamination minimization
  objective is `c(G) = (1/|V|) Σ_v σ(v; G)` — averaged over *every node as a potential
  source*, estimated via bond percolation / SCC decomposition. SS-IMER fixes one known
  source and estimates σ via per-scenario BFS reachability on frozen live-edge samples.
  **State this explicitly in the thesis as "we adapt Kimura's link-blocking formulation to
  a single fixed source," not as a direct instance of his problem** — the objective and the
  estimation method both differ.
- Castiglioni et al. (2021) is cited correctly as-is: hardness/inapproximability paper for
  election manipulation (seeding + edge removal/addition budgets), used for domain
  motivation and hardness argument only — not a source of an algorithm or a submodularity
  result we inherit.
- Khalil et al. (2014) supermodularity result is for **Linear Threshold**, not IC — usable
  only as a motivating analogy for "synergy across multiple edges," never as a theorem
  covering our IC objective.

## 2. Heuristic portfolio — what's in it and why

| Heuristic | Role | Notes |
|---|---|---|
| Random | baseline + operator | control |
| Transmission probability `p` | baseline + operator | strongest single fixed heuristic in pilot data (mean R≈0.48, orthogonal to degree: Spearman 0.03–0.08) |
| Degree sum (out(u)+out(v) on base graph) | baseline + operator | weak on this dataset — most out-edges are low-probability |
| Granovetter local bridge (`is_local_bridge`: edge whose endpoints share no common neighbor) | baseline + operator | strongest validated effect size: mean p bridge/non-bridge 0.086/0.116, Cliff δ=−0.118, p=1.4e-60, on 32.1% of edges |
| Betweenness (Brandes, source-rooted) | baseline + operator | stays mostly local to hop0 in practice |
| Spectral (leading eigenvector `u_i·v_j`) | baseline + operator | requires index alignment to graph's internal vertex order — see §6 |

**Louvain communities are descriptive only, not a heuristic.** Community-detection-based
"inter-community edge" as an operator/baseline heuristic was tested and found near-null
once measured correctly (mean p inter/intra 0.102/0.108, Cliff δ≈+0.002, practically null) —
the earlier apparent signal was an artifact of comparing against one arbitrary,
seed-sensitive partition (Q swings 21–31 communities without a fixed seed). Louvain still
belongs in the topology chapter as a mesoscale-structure figure (community count,
modularity Q, and optionally how Q rises as the graph is thresholded on edge probability).

## 3. Tie-breaking policy — must be documented in the thesis, not "fixed"

Several heuristics have very low cardinality (bridge is binary; probability takes exactly
10 distinct values from the rating→sigmoid mapping), so most candidate-edge rankings
contain large tied groups.

- **Baseline selection is a deterministic rule**: sort by `(score desc, u asc, v asc)`,
  same input → same output always, for reproducible method comparison.
- **ALNS operator selection is a sampler**: ties are broken by drawing uniformly at random
  (seeded RNG) among tied candidates. A deterministic tie-break in the operator would
  collapse heuristics like `bridge`/`probability` into producing the exact same single cut
  every run, eliminating the exploration ALNS is supposed to provide.
- **Decision: we do not try to cancel out this randomness by averaging over many ALNS
  seeds.** We run a small, fixed number of seeds and treat the resulting variance as a
  property of the method to report, not noise to average away.
- **Must appear in the thesis (methodology + results/discussion):**
  1. **Tie frequency**: for each heuristic, how often candidate rankings contain ties, and
     how large the tied groups typically are (e.g. distribution of tie-group size at the
     point where the k-th/q-th edge is selected). This is a property of the heuristic
     itself and should be reported once as a structural fact about the candidate pool.
  2. **Impact of tie-break randomness on outcomes**: how much the final σ/R varies across
     independent ALNS seeds for the same (source, k, heuristic mix), specifically
     attributable to which tied candidate got picked, not to the search trajectory in
     general. Report this as a variance/spread, with the explicit framing that it is
     documented as a characteristic of the method rather than eliminated.
- Implementation note (drives architecture): one shared `topk(edges, score, k, rng=None)`
  function — `rng=None` for the deterministic baseline path, `rng=<seeded Random>` for the
  operator path — so the two policies can never silently drift apart.

## 4. Known bugs from the pilot phase — do not reintroduce

(Full detail lives in [PILOT_TESTS.md](PILOT_TESTS.md); this is the short list to check against during code review.)

- Index misalignment between igraph vertex names (original SNAP IDs) and CSR/adjacency
  order — must permute any Perron/eigenvector score onto `graph.vs` index before use.
- Rewarding a zero-improvement (Δ=0) move as if it were a real improvement.
- Comparing ALNS against a "best peer" pool that includes ALNS itself.
- Sharing one heuristic/score between destroy and repair — they are two independent
  operator families with independent weights.
- MinCut used as a peer method in comparison tables — it sees the whole graph and is not a
  fair peer; report separately if used at all.
- Un-seeded Louvain / un-seeded global `random` module.
- `k ≥ out(s)` — **resolved: not an error, just the trivial case** (see §13). The pilot
  flip-flopped on this (§10 said isolate, §19 said hard error); §10 was right.

## 5. Numbers

All numbers live in CSVs under `data/` or `results/` (once produced), never retyped by hand
into this file. This section just indexes what CSV holds what, once they exist.

- Topology properties (N, M, path length, clustering, assortativity, degree-distribution
  exponent γ + KS statistic, spectral threshold, bow-tie sizes, k-core, Louvain Q) → TBD CSV
- **Confirmed via `create_graph.py` (reproduces PILOT_TESTS.md §12 exactly)**: N = 3683,
  M = 22650, mean out-degree = 6.1499, mean p = 0.1063, median p = 0.0180.
- **`analyse_graph.py` output (`data/topology_summary.csv`, `data/edge_features.csv`),
  cross-checked against PILOT_TESTS.md where a prior number exists:**

  | quantity | this run | pilot notes | match |
  |---|---|---|---|
  | path length (directed, within-component) | 3.7395 | 3.7395 | exact |
  | path length, ER null | 4.7337 | 4.7237 | close (ER is stochastic) |
  | clustering (undirected transitivity) | 0.0760 | 0.0760 | exact |
  | clustering, ER null | 0.0035 | 0.0030 | close (ER is stochastic) |
  | λmax(A), λc = 1/λmax(A) | 38.9545, 0.02567 | 38.95, 0.0257 | exact |
  | λmax(P) | 7.6311 | 7.63 | exact |
  | SCC giant / count | 3192 / 477 | 3192 (86.7%) | exact |
  | WCC giant / count | 3670 / 7 | 3670 | exact |
  | k-core max, nodes in it | 32, 73 | 32, 73 | exact |
  | assortativity r | −0.15458 | −0.1546 | exact |
  | Granovetter local bridges | 7266 (32.1%) | 7266 (32.1%) | exact |
  | Louvain best-of-20 | 26 comm., Q=0.4907, range 21–30 comm. / Q 0.460–0.4907 | 31, Q=0.491 (best-of-20) | same ballpark, not identical — expected for a stochastic algorithm across different library/RNG-stream versions |
  | **out-degree power-law γ, xmin, KS** | **2.148, xmin=8, KS=0.038** | **γ_out=2.81, xmin=41, KS≈0.058** | **mismatch — see below** |

  **Power-law fit discrepancy, unresolved**: computed via the `powerlaw` package's
  Clauset–Shalizi–Newman (2009) MLE with automatic xmin selection (the standard,
  citable method — not just κ, per PILOT_TESTS.md §36's own warning). Tried in-degree,
  out-degree, and a forced `xmin=1` variant; none reproduce pilot's γ≈2.8/xmin=41. Since
  every *other* number above matches pilot's notes exactly (same graph, same
  construction), this looks like a difference in the old pilot code's fitting procedure
  itself, not a data problem — and PILOT_TESTS.md's own framing already warned some pilot
  numbers "could be wrong or hallucinated." **Trusting this run's number** (principled,
  reproducible, standard method) over the pilot figure unless told otherwise.
  **Known bug worked around**: `powerlaw==2.0.0`'s `fit.power_law.KS()` calls an
  undefined name internally; `fit.power_law.D` holds the same statistic and works.

  **Did we prove scale-free structure? Nuanced yes, with the honest caveat stated.**
  Cross-checked against Albert & Barabási (2002) directly: their definition (p.63) is
  simply "degree distribution follows a power law P(k)~k^-γ" and their own Table II
  reports real-network exponents mostly in the 2–3 range (Internet domain-level
  γ=2.1–2.2, WWW γ≈2.1–2.7) — our γ_out=2.148, γ_in=1.853 sit squarely in that band, but
  their 2002 methodology is essentially eyeballing log-log straight lines, which predates
  Clauset–Shalizi–Newman (2009)'s rigorous test that `powerlaw` implements.
  Ran CSN's own recommended step — comparing the power-law fit against plausible
  alternative heavy-tailed distributions via likelihood-ratio test
  (`fit.distribution_compare`), not just fitting alone:
  - power law **beats exponential** decisively (out: R=102.8, p=8e-5; in: R=695.8,
    p=3e-20) — confirms a genuine heavy tail, not memoryless/random-graph-like degrees.
  - power law **loses to truncated power law, lognormal, and stretched exponential**
    (all R<0, all p<0.05, both in- and out-degree) — a pure, unbounded power law is
    **not** the best-fitting model; a power law with a finite-size cutoff fits better.
  **Honest thesis claim**: the degree distribution is heavy-tailed and its exponent is
  consistent with the scale-free literature's typical range, but a rigorous test rejects
  a *pure* power law in favor of a truncated one — report it as "heavy-tailed,
  scale-free-like with a finite-size cutoff," not an unqualified "scale-free network."
  This is the more defensible, modern claim (a strength, not a weakness, of doing the
  CSN test at all — most informal "scale-free" claims in older literature skip it).
- Per-run experiment results (method, source, k, IS/OOS σ, stop_reason, hop_mix,
  final_max_hop, best_hits per heuristic/hop, neutral_moves per heuristic) → TBD CSV
- Tie-frequency and tie-break-variance measurements (§3) → TBD CSV

## 6a. ALNS core mechanism — verbatim from Røpke & Pisinger (2006)

Pulled directly from the PDF (not from memory/pilot paraphrase), since "true R&P method"
was an explicit requirement. Section numbers below refer to the R&P paper.

**Roulette wheel operator selection (§3.3, eq. 20).** With `k` operators of weight
`w_i`, operator `j` is selected with probability `w_j / Σ_i w_i`. Removal (destroy) and
insertion (repair) operators are selected **independently** — this is exactly our
"two independent families" decision, confirmed as R&P's own design, not an addition.

**Score system (§3.4).** Search is divided into segments (R&P use 100 iterations/segment;
pilot used 20 — a calibration choice, see §10). Each heuristic's score resets to 0 at the
start of a segment and is increased by exactly one of:
- `σ1` — the move produced a new global-best solution.
- `σ2` — the move produced a solution *not previously visited* and better than the
  current solution.
- `σ3` — the move produced a solution *not previously visited*, worse than the current
  solution, but accepted by the SA criterion.
**Both** the destroy heuristic and the repair heuristic used in that iteration get the
same score increment (can't attribute success to one alone) — added to each one's own
family's tally, not a shared score.
**Important detail not in pilot notes**: R&P only reward *unvisited* solutions — they
hash every solution (assignment) and skip the reward if it's been seen before, even if it
would otherwise qualify for σ2/σ3. For us, "solution" = the cut `D`; hashing
`frozenset(D)` and keeping a visited-set for the run is cheap (max_iter is O(100s–1000s))
and is required for literal fidelity. **Decided: implemented**, for literal R&P fidelity.
Note: neither σ2 nor σ3 covers an exact tie (Δ=0 vs. current solution) — R&P's own
categories imply a Δ=0 move scores 0 by omission, which is exactly the pilot's own
Δ=0-accepted-reward-0 rule (§18 of PILOT_TESTS). Not a pilot workaround — it's what a
strict reading of R&P already implies.

**Weight update, end of segment j (§3.4):**
```
w_{i,j+1} = w_{i,j} · (1 − r) + r · (π_i / θ_i)
```
`π_i` = total score accumulated by heuristic `i` in segment `j`; `θ_i` = number of times
heuristic `i` was selected in segment `j`; `r` ∈ [0,1] is the reaction factor (r=0 →
weights never adapt; r=1 → last segment's score fully determines next weight). First
segment: all heuristics weighted equally. **Edge case not addressed in the paper**: if
`θ_i = 0` (heuristic never selected in the segment), division by zero — practical fix is
`w_{i,j+1} = w_{i,j}` (unchanged) when `θ_i = 0`.

**SA acceptance criterion (§3.5).** Accept `s'` given current `s` with probability
`exp(-(f(s') - f(s)) / T)`; always accept if `f(s') ≤ f(s)`. Temperature decays every
iteration: `T = T · c`, `0 < c < 1`. **Start temperature** is calibrated from the initial
solution, not set directly: choose `T_start` such that a solution `w`% worse than the
initial cost `z'` is accepted with probability 0.5 — i.e.
```
T_start = (w · z') / ln(2)
```
(derived from `0.5 = exp(-(w·z')/T_start)`). `w` is the "start temperature control
parameter." **This directly fills in the thesis draft's unfinished formula** ("Početna
temperatura SA skalira se iz početnog SAA dosega: ___") — cite this derivation there.

**Destroy-operator randomized selection (§3.1, Algorithms 2–3).** Both Shaw (related)
removal and Worst removal rank a candidate list `L` by their respective score, draw
`y ~ Uniform[0,1)`, and pick `L[⌊y^p · |L|⌋]` — larger `p` biases the pick toward the top
of the ranking (more greedy), `p → 0` approaches uniform random choice over `L`. Random
removal is literally Shaw removal with `p = 1` (implemented separately for speed, per
R&P). This confirms pilot's own `floor(y**p * n)` mechanism (§32 of PILOT_TESTS) was
already a faithful port of this exact technique.

**R&P's own tuned parameter vector (§4.3.1-4.3.2)**, found by re-reading the paper before
writing `operators.py`/`alns_optimizer.py` rather than guessing: after their own
trial-and-error + one-parameter-at-a-time tuning process, R&P report
`(φ,χ,ψ,ω,p,p_worst,w,c,σ1,σ2,σ3,r,η,ξ) = (9,3,2,5,6,3,0.05,0.99975,33,9,13,0.1,0.025,0.4)`.
Relevant to us directly: **σ1=33, σ2=9, σ3=13** (this is where pilot's inherited numbers
actually came from — not arbitrary, confirmed against the primary source now), **r=0.1**
(reaction factor), **w=0.05** (start-temperature control parameter), **c=0.99975**
(cooling rate per iteration), **p_worst=3, p_Shaw=6** (destroy determinism exponents —
also matches pilot's `floor(y**p*n)` notes exactly). Stopping criterion: 25000 LNS
iterations, chosen for a time/quality tradeoff on their (much larger) VRP instances —
not directly transferable to us, see below. These are **starting points to recalibrate
on our own problem** (PLAN.md Phase 2), not final values — but grounded starting points,
not invented ones.

**q-bounds — literal R&P formula does not scale to our k, kept pilot's adapted version
deliberately, not by oversight.** R&P define ρ (their q) as a random integer with
`4 ≤ ρ ≤ min(100, ξ·n)`, where n is the instance's total request count (in the
hundreds for their VRP instances). Applied literally to us — where `n` would be `k`,
since D is a fixed-size solution the same way their route-assignment is — the fixed
lower bound of 4 **breaks for small k** (e.g. k=3 in the canonical smoke case from
PILOT_TESTS §16: 4 ≤ q is impossible when |D|=3). Kept the pilot's scaled version
instead: `q_min = max(1, floor(0.1k))`, `q_max = min(k-1, floor(0.4k))` — proportional
to k rather than a fixed floor, always leaves at least one element of D fixed
(`q_max < k`), always changes at least one (`q_min ≥ 1`). This is a justified departure
from literal R&P, not an unexamined inheritance — R&P's own formula is undefined for
problem sizes as small as ours.

**Explicitly not ported**: the noise term added to insertion costs (§3.6) — it's defined
in terms of the PDPTW's continuous distance matrix (`maxN = η · max_{i,j} d_ij`) and has
no direct analog for discrete edge-selection heuristics; not needed here.

## 7a. Where our heuristic portfolio doesn't map cleanly onto R&P — decided

R&P's insertion (repair) heuristics are themselves deterministic, greedy procedures
operating on continuous real-valued costs (distances/times), where exact ties are
essentially impossible — so literal R&P repair applies **deterministic** top-q selection
within whichever heuristic the roulette wheel picked; randomness only enters at the
destroy side, via the `y^p` mechanism above.

Our repair heuristics are not all like that — `bridge` is binary and `probability` takes
exactly 10 values (§3 of this report), so most of the candidate ranking is tied. A
literal transplant of R&P's deterministic repair selection would make those two
heuristics collapse to the exact same single result every run — this isn't a flaw in
R&P's method, it's a mismatch between their continuous-cost domain and our discrete one.

**Proposed reconciliation** (replaces the earlier, simpler "shuffle within ties" idea):
use R&P's own `y^p` rank-biased selection mechanism for **repair as well as destroy**,
but build the ranked list `L` with a two-stage order — sort by `(score desc, then a
random shuffle within exactly-tied score groups, seeded per call)` — and *then* apply
`⌊y^p·|L|⌋`. This keeps R&P's actual mechanism (and its determinism-vs-exploration knob
`p`) intact and faithful, while fixing the tie-collapse problem with the minimum change:
a pre-shuffle only within tied bands, not a departure from R&P's selection rule itself.
`p` can differ per heuristic/operator if calibration shows that's useful. Baselines
(`greedy_baseline.py`) stay fully deterministic — no `y^p`, no shuffle, that's what makes
them a fixed reference point.

## 8a. Graph library — igraph, with a structural (not one-off) alignment guard

**Decision: igraph**, not networkx. Reasoning: the actual per-iteration hot loop (SAA
evaluation, called thousands of times) doesn't use either library's traversal machinery —
per pilot's own finding, a hand-rolled BFS over plain Python adjacency lists beat both
(~2.3× over the old approach), so it's built once from the frozen scenario and masked `D`,
independent of which library builds the base graph. That neutralizes most of the speed
argument for the hot loop, but **not** for the one-time per-source precomputation
(betweenness, eigenvectors, Louvain) — igraph's C backend is genuinely faster there, and
the user has direct working fluency with it.

Pilot's index-alignment bug class (§4 of this report, §18/§26 of PILOT_TESTS) was
specifically about `Graph.TupleList` silently ordering vertices by first-appearance,
decoupled from any array/CSR ordering built independently elsewhere. **We do not use
`Graph.TupleList`.** `create_graph.py` instead: (1) collects the sorted unique node-ID
list once, (2) adds exactly that many vertices with `name` set to that list in that exact
order, (3) builds an explicit `id_to_idx` dict for all edge insertion, and (4) any matrix
representation needed later (spectral heuristic) is derived via igraph's own
`get_adjacency_sparse()`, never a separately-rebuilt array.
**Structural guard, not a one-off smoke test**: `verify_vertex_alignment(g, node_ids)` is
called every time the graph is constructed (not just once during Phase 1 testing) and
raises immediately if `list(g.vs["name"]) != node_ids`. This converts "a bug we know how
to avoid" into "the code refuses to run if it's ever violated."

## 8b. Heuristics use full-graph metrics, never SAA/MC scenario-derived metrics — why

User's own reasoning, confirmed correct and already how the architecture is built (§8):
scoring candidate edges using a metric derived from the SAA or MC frozen scenarios
themselves (e.g. "how often does this edge appear in a scenario where the source's reach
is large") would let the *same* sampling noise leak into both the optimization objective
(SAA fitness) and the candidate-selection heuristic — compounding overfitting risk rather
than the two being independent checks on each other. All six heuristics (random,
probability, degree-sum, Granovetter bridge, betweenness-from-source, spectral) are
computed once from the **base graph** in `analyse_graph.py`, before any scenario is
generated, and never touch a scenario subgraph. `probability` uses the edge's own fixed
IC parameter, not a scenario-realized outcome. This is the academically defensible
position and should be stated explicitly in the methodology (thesis section 4.2 or a new
short subsection before it): heuristics operate on stable structural facts about G;
**only** the fitness function operates on frozen scenarios, and even there, in-sample
(search) and out-of-sample (reported result) are kept structurally separate (§7).

**Where scenario-subgraph analysis itself belongs — decided.** Current thesis structure
(unchanged, confirmed): 1 Topologija, 2 Analiza Bitcoin Alpha, 3 Formulacija SS-IMER,
4 Heuristike za odabir bridova, 5 Metodologija ALNS (5.1 Arhitektura, 5.2 Operatori,
**5.3 Fitness funkcija**), 6 Greedy metoda za usporedbu, 7 Rezultati i rasprava.
§5.3 gets only a brief methodological mention of why SAA is used (avoiding the
scenario-derived-heuristic overfitting risk, §8b above) — not the empirical comparison
itself. The full SAA **and** MC vs. full-graph comparison (edge retention, density,
whether giant-component structure survives a single percolation draw) live **together**
as the first subsection of Chapter 7, "Evaluacija rezultata" — validating the measurement
methodology before the actual ALNS-vs-baseline findings that follow it. Deferred until
`create_subgraphs.py` is built — not urgent, but flagged so it isn't forgotten (PLAN.md
Phase 1).

## 8c. Level-2 hypothesis — corrected framing (supersedes the original phrasing)

Original framing ("edges directly out of `s` sometimes lead to dead ends, so the real
bottleneck can be several hops away") doesn't hold up: if the danger routes through
exactly **one** hop0 edge and the rest are dead ends, that's still a hop0-solvable
problem — a hop0-only greedy method (or even exhaustive enumeration, since out(s) is
usually small) can identify and cut that single edge. That scenario isn't evidence for
needing to search beyond hop0 at all.

**Corrected scenario**: the real case for going beyond hop0 is **redundancy**, not
distance per se. When `s` has *multiple* hop0 edges that all lead (independently) toward
the same dangerous, well-connected region, no single hop0 removal suffices — under a
limited budget k smaller than that redundant fan-out, hop0-only methods can't close all
the parallel gateways. If those redundant paths **converge** onto a narrower shared
choke point one or more hops downstream (e.g. several hop0 neighbors all feed into the
same hub via a small number of shared uplink edges), removing that shared downstream
choke point is far more budget-efficient than trying to sever every redundant hop0 path
individually. This is structurally a min-cut argument: sometimes the narrowest s–(danger)
cut just isn't at the edges touching `s`.

This isn't new speculation — it matches a real prior observation in PILOT_TESTS.md §23:
source 2765, k=3 was the "canonical choke case," where a cut at hop≥1 (uplink edges into
a mega-hub) beat hop0 quarantine. That's exactly this pattern, not "hop0 is all dead
ends." Use this framing (redundant convergent paths + a downstream choke point) as the
motivating example in the Introduction and in the Level-2 discussion, replacing the
"dead end" framing.

## 9a. Duplicate edges in the raw data

Bitcoin Alpha's raw CSV has no header (`SOURCE,TARGET,RATING,TIME`) and can contain more
than one rating for the same ordered pair over time (users re-rating each other). SS-IMER
needs one probability per directed edge. **Default: keep the most recent rating by
`TIME`** (most current trust assessment) — configurable, flagged in §6.

## 6. Open items to confirm before/while coding

- Spectral score index-alignment (§4) needs a concrete, tested implementation early, since
  it silently produces garbage otherwise (pilot: Spearman(Tong, Δλmax) 0.15 → 0.969 after
  the fix).
- **Resolved (was a misunderstanding, not a scope cut):** the hop-horizon windowing
  mechanism is kept — Level 2 stays a real, explicit adaptive-learning claim (ALNS learns
  how far from `s` to search, not just what it finds is described post-hoc). What changed
  is only *where the mechanism lives in the code* — see §7. Because this is a real claim
  (not just a descriptive statistic), it inherits pilot §33's requirement in full: no
  claim of "ALNS learns search depth" is allowed into the thesis without the per-segment
  trace to back it (active_max_hop, per-layer/per-heuristic weights, best_hits by hop),
  and with an explicit **closing** rule for the horizon (pilot's version only ever
  expanded, never contracted — decide and implement a contraction rule this time, or
  explicitly justify why expansion-only is acceptable).
  **Superseded by §12**: the horizon is gone entirely, replaced by the hop-scope roulette
  wheel, which gives contraction for free (a layer that stops paying is down-weighted).
  The per-segment trace requirement stands and is met. The Level-2 claim itself is
  narrowed by §14.2 — "does hop>0 reach the winning cut", not "ALNS learns search depth".

## 7. Scenario architecture and candidate space — corrections (supersedes earlier draft of §6)

- **`create_subgraphs.py` builds frozen live-edge realizations (scenario subgraphs),
  not hop-layer candidate pools.** A scenario is a bond-percolation-style realization:
  each edge is independently kept with probability `p` (its IC transmission
  probability), producing an unweighted subgraph. Two disjoint, separately seeded sets
  are generated once and then treated as immutable: an in-sample (SAA) set and an
  out-of-sample (Monte Carlo) set. Nothing downstream is allowed to mutate them —
  evaluation always works on a copy/mask, never on the frozen scenario objects directly.
- **`evaluator.py` has one function, `evaluate_reach`** — given a candidate
  cut `D`, a scenario array, and the shared base adjacency, computes mean reach via
  masked BFS from `s`. It does not generate scenarios. Used for **both** SAA (inside
  the ALNS loop) and OOS (final validation only) by passing a different scenario
  array — **no separate `oos_evaluator.py` file** (removed after a second look: it was
  a 2-line re-export with no actual enforcement beyond what correctly passing the
  right array already gives — the file split was indirection the safety property
  didn't need). The SAA/OOS separation is structural in the sense that matters: only
  the orchestration code (not yet written) holds a reference to `mc_scenarios`, and
  the ALNS loop is only ever constructed with `saa_scenarios` — never both.
- **Hop-layer candidate windowing is kept, but it isn't a standalone script.**
  *(The `active_max_hop` mechanism described in this bullet was removed — see §12. Hop
  layers are still per-source precomputed features and still live in the optimizer's own
  state, but repair draws from one layer per iteration chosen by a roulette wheel, not
  from an expanding window. The rest of the bullet stands.)*
  Hop-distance-from-source is a precomputed, per-source feature (`analyse_graph.py`,
  §8) — an edge's layer = BFS distance of its tail from `s`. The *state* that changes
  during search (`active_max_hop`, starting at hop0∪hop1, expanding per segment when
  the outer layer's average reward is positive) belongs to `alns_optimizer.py`, since
  it's ALNS's own search state, not a graph property. `operators.py`'s destroy/repair
  operators simply receive whatever the current active pool is (precomputed hop feature
  filtered by the optimizer's current `active_max_hop`) — they don't own or compute the
  horizon themselves. `greedy_baseline.py` never varies this: hop0 only, always.

## 8. Precomputation — SAA fitness is the only expense that's allowed to be expensive

Rule of thumb: **anything computable from the static graph must be computed once and
cached, never recomputed inside an ALNS iteration.** ALNS runs many thousands of
evaluations; SAA fitness (BFS over frozen scenarios) is the one unavoidable per-iteration
cost. Heuristic scoring must never add graph traversal or recomputation on top of that.

Two tiers of precomputed features, both produced by `analyse_graph.py`:

- **Global, source-independent** (computed once for the whole graph, cached/persisted):
  transmission probability `p` (given), degree-sum score, Granovetter local-bridge flag,
  spectral leading-eigenvector components (index-aligned per §4/§6 above).
- **Per-source** (computed once per source at the start of that source's experiment run,
  cached and reused across every `k`, every method, and every ALNS iteration for that
  source — never recomputed per iteration): source-rooted betweenness, hop-distance from
  `s`, and the set of edges reachable from `s` (defines the candidate pool).

`heuristics.py`'s scoring "strategies" should therefore be lookups into these precomputed
tables, not functions that touch the graph — `topk(edges, scores: dict, k, rng=None)`
takes a precomputed score mapping, not a callable.

## 9. Experiment design — curated showcases, not one uniform matrix

Neither a single fixed `k` nor `k` purely scaled to `out(s)` is the right default across
all experiments — decided against both as a blanket policy. Instead:

- **One dedicated k-sweep figure**: fix a small number of representative sources, vary
  `k` across a deliberately chosen range, show how ALNS's advantage over hop0 baselines
  changes with budget. This is a specific, narrow experiment, not the general protocol.
- **A curated set of showcase (source, k) pairs**, chosen to demonstrate specific
  phenomena rather than to cover the space uniformly — same spirit as the pilot's
  canonical pairs (choke points beyond hop0, hub sources where hop0 is hard to beat,
  small-out sources where the cut space is enumerable and SAA-vs-MC regret can be
  measured exactly, etc.). Pick sources for what they reveal, document why each one was
  picked.
- **Other ALNS parameters (segment length, ρ, q bounds, cooling schedule) are also fair
  game as a showcase axis**, not just k/out-degree, when they're the more interesting
  variable for a given phenomenon.
- This affects the CSV schema: results need enough metadata per row (source, k, method,
  and *which showcase/purpose it belongs to*) to reconstruct why each run was included,
  not just raw numbers.

## 10. ALNS parameter calibration — is itself thesis content

Once the architecture (Phase 1) is implemented, calibrate ALNS's parameters
(`max_iter`, `segment_length`, `ρ`, `q_min`/`q_max`, cooling schedule, horizon expansion
threshold) on a calibration set disjoint from the measurement/showcase sources — this was
already planned. What's new: **document the calibration process itself as methodology
content for the thesis**, not just as an internal tuning step:
- what parameter values/ranges were tried,
- what metric decided the final choice (and on which disjoint calibration sources),
- the final chosen defaults,
- and, per §3's tie-break-randomness principle, whether the calibration conclusions were
  stable or sensitive to the tie-break RNG seed.
This becomes its own short methodology subsection — pilot's own calibration (§22) was
later invalidated by unrelated bugs (§28/§32), so this time the calibration run must
happen only after the architecture fixes in §1–§8 are in place and verified by the Phase 1
smoke tests.

## 11. Runtime — cost model, what was fixed, and what it cost us to learn

Runtime matters here for a practical reason: every calibration and showcase run in
Phase 2 pays this cost, so a 4x difference decides whether the experiment matrix fits
in the time available.

**Cost model (measured, not estimated).** One ALNS run costs roughly

    sweeps x scenarios x per-BFS-time,   sweeps ~ max_iter + (#worst-destroy calls)

with `per-BFS-time` scaling with the source's reach sigma_0, not its out-degree. At
500 SAA scenarios one sweep is ~155 ms for a sigma_0 ~ 643 source. Measured
end-to-end, k=5, 300 iterations:

| source | out-degree | sigma_0 | ALNS runtime |
|---|---|---|---|
| 3616 | 9 | 74 | 9.4 s |
| 774 | 6 | 41 | 9.8 s |
| 0 (hub) | 486 | 644 | 65.9 s |
| 253 | 22 | 644 | 64.3 s (was **750 s**, see below) |

So **low-reach sources are cheap and high-reach sources dominate the budget** — worth
knowing when choosing the showcase sample (§9), since a sample skewed toward large
sigma_0 costs several times more for the same number of runs.

**Four fixes took a k=20 run from ~270 s (and a 750 s pathological case) to ~65 s.**
Each was found by profiling rather than guessed:

1. **Marginal values in one pass instead of |D|+1 sweeps.** `destroy_worst` needs
   sigma(D\{e}) for every e in D. Naively that is |D|+1 full sweeps and it alone was
   ~237 s of a ~270 s run — exactly what PILOT_TESTS.md §34 predicted. It is not
   needed: for a scenario with reached set R, restoring one edge (u,v) can only add
   nodes reached *through* it, so the gain is provably zero unless the edge survived
   percolation, u is in R and v is not. Only that last case does any traversal, and it
   explores strictly new territory. Measured at **1.0x one evaluation instead of 21x**
   for k=20, and verified exact against the naive version (test_evaluator.py).
2. **The cut mask is a reused list indexed by node id, not a dict keyed by tail.** A
   traversal probes every node it pops (~135 M probes per run) but D touches at most k
   tails, so this trades hashing for an array index on the hottest line in the codebase.
3. **`select_q` ranks once instead of per pick.** Its callers score statically, so
   re-sorting the pool between picks cost O(q · n log n) for no behavioural gain.
   Relatedly, tie-shuffling now uses a random sort key rather than `random.shuffle`
   (profiled at 4% of total runtime on its own). R&P's Shaw removal genuinely must
   re-rank each step — that one kept its dynamic loop.
4. **The hop-windowed pool is cached per horizon level.** This is what caused the
   750 s outlier; see below.

**The 750 s outlier was a symptom, not just a slow path — flag for the Level-2
hypothesis.** Source 253 has only 22 hop0 edges. With so few, the horizon-expansion
rule ("grow if the frontier layer earned positive average reward this segment") fires
almost every segment, so `active_max_hop` climbs and the candidate pool grows toward
the entire reachable edge set (~20k edges), which was then being rebuilt, scored,
filtered and sorted *every iteration*. Caching the pool per horizon fixed the runtime
(750 s -> 64 s), but the underlying behaviour is still that **the horizon runs away on
sources with a small hop0**. That is a research problem, not only a performance one:
PILOT_TESTS.md §23 found the winning cut was pure hop0 in 31/40 cases, so a horizon
that expands to hop 5-6 mostly dilutes the search across candidates that never win.
PILOT_TESTS.md §33 already flagged this rule as unvalidated and demanding both a
stricter expansion criterion and a contraction mechanism. **Open decision** (PLAN.md
Phase 1) — the options are a stricter rule (require a sigma1 hit, not any positive
reward), adding contraction, or a hard cap; whichever is chosen has to be measured,
not assumed, because it *is* the Level-2 mechanism.

**Correctness is pinned, not assumed.** The evaluator is the one component written for
speed over obviousness, so `code/test_evaluator.py` checks it against an independent
oracle: each scenario is rebuilt as a real igraph graph with the cut edges deleted and
`subcomponent(mode="out")` gives ground truth. It also pins the one-pass marginals
against the naive computation, monotonicity in the cut, that the reused cut buffer is
left clean, and that caching never changes an answer. This started as a discrepancy
(643.50 vs 643.096 between two versions) that turned out to come from since-deleted
code — the lesson kept was the test, not the number.

## 12. The hop-horizon mechanism was broken, and how we found out — thesis-relevant

This is the most important methodological finding so far, and it belongs in the
methodology chapter, not just in a commit message: **the original Level-2 mechanism (an
expanding hop horizon) actively destroyed the search**, and replacing it with a third
adaptive weight book fixed it. Both the diagnosis and the fix are reportable.

### How the failure was detected

Small sources make the search space enumerable. For a source with out-degree 9 and
k=4 there are only C(9,4)=126 hop0 cuts, so *all* of them can be evaluated against the
same SAA objective ALNS optimises, giving an exact ground-truth optimum. This measures
**search quality specifically** — it is deliberately separate from the SAA-vs-true-sigma
question, which is what out-of-sample validation is for.

Against that ground truth the horizon version was far from optimal — gaps of 25-495%
on spaces of 70-210 cuts that 300 iterations should nearly brute-force. Holding the
horizon fixed instead was decisive:

| horizon setting | exactly optimal | mean gap | worst gap |
|---|---|---|---|
| hop0 only, fixed | **8/8** | 0.0% | 0.0% |
| hop0 U hop1, fixed | 5/8 | 18.1% | 84.9% |
| adaptive horizon (original) | 1/8 | 154.6% | 494.6% |

So the operators, adaptive weights, SA acceptance and evaluator were all sound; the
horizon policy alone was responsible.

### Why it failed — two distinct defects

1. **The expansion predicate was vacuous.** sigma1/sigma2/sigma3 are positive and every
   other outcome scores 0, so rewards are non-negative *by construction*. "Expand if the
   frontier layer's average reward > 0" therefore reduces to "expand if any reward ever
   occurred", which is almost always true. The horizon ratcheted open every segment and,
   having no contraction rule, never closed. PILOT_TESTS.md §33 observed the same
   behaviour without identifying this as the cause.
2. **Flattening layers into one pool dilutes the search.** Once the horizon reaches
   hop 5-6 the candidate pool approaches the whole reachable edge set (~20k edges), so
   the handful of hop0 edges that actually close off the source are drowned out. This is
   exactly PILOT_TESTS.md §23's independent finding that wide pools pick high-p hop1
   edges which do not close the source (source 718: hop0 p gives sigma=48, hop0-1 p
   gives sigma=642). It also caused a 750s runtime outlier (REPORT.md §11).

### The replacement: hop scope as a third roulette wheel

Repair now draws from **one hop layer per iteration**, chosen by its own roulette wheel
alongside the destroy and repair wheels, updated by the same R&P rule. If the chosen
layer cannot supply enough candidates the remainder comes from the other in-scope
layers, so |D| = k always holds.

Why this is the better mechanism, and better *for the thesis*:
- It makes Level-2 a genuine adaptive-learning claim — per-layer weights, logged every
  segment — rather than a one-way ratchet that cannot express "this layer is not worth
  visiting".
- It cannot run away: a layer that stops paying is simply down-weighted, which gives
  contraction for free (the thing PILOT_TESTS.md §33 said was missing).
- hop0 stays competitive instead of being diluted.
- It matches the architecture that survived the pilot's own A/D testing (§10: a separate
  roulette for hop-scope and for heuristic).

**Layers start equally weighted.** Seeding a prior (the pilot used hop0=2, hop1=8) would
prejudge precisely what Level-2 is asking, so ALNS starts uniform and has to learn.
Layers deeper than hop3 are excluded outright, justified by PILOT_TESTS.md §23 finding
no winning cut ever used hop>=4; revisit in calibration.

**Result: 4/4 exactly optimal on the enumerable sources**, and in every case the learned
scope weight was highest for hop0.

**Correction (see §14.2): that last observation does not license the claim it was
originally written to support.** The layers being compared differ in size by up to three
orders of magnitude (hop0 = 4–486 edges, hop2 = 4,780–13,765 on the same sources), so a
higher learned weight for hop0 partly measures that hop0 is easier to search, not only
that its edges are better. The scope weights stay a legitimate *diagnostic*; they are
not on their own evidence that "the mechanism recovers where the useful edges are".

### Caveat for the write-up

These numbers come from a handful of small sources and a single seed, run to diagnose a
bug — they are **not** the experiment. The measured protocol (proper source sample,
budgets, baselines, seeds, OOS validation) still has to produce the reported figures.
What is established here is a design decision and its justification.


## 13. k >= out(s) is the trivial case, not an error

Settled: when the budget can cut every edge leaving the source, that is not a
misconfiguration to reject — it is an instance whose optimum is known in closed form.
The warm start cuts all of hop0, which isolates the source, so sigma = 1 (the source
still counts itself) and that is provably the global minimum: no cut can do better,
because sigma >= 1 always. Any leftover budget is topped up from other layers to keep
|D| = k, though those edges are unreachable once the source is isolated.

The search then stops immediately with `stop_reason="isolated"` rather than spending
300 iterations rediscovering an optimum it already holds. Measured on a source with
out-degree 6: k=6 and k=8 both return sigma=1.000 in 0 iterations, while k=3 runs
normally.

This restores PILOT_TESTS.md §10's original position ("take all hop0, k_eff = |hop0|,
do not raise ValueError; ALNS may stop when spread ~ 1") against §19's later reversal
to a hard error. §10 was right: raising would have forced every experiment driver to
special-case a situation the algorithm can simply handle, and would have thrown away a
legitimate data point (the budget at which a source becomes fully containable is itself
worth reporting).

Reporting note: `stop_reason` distinguishes these runs, so trivially-solved instances
can be excluded from averages where they would otherwise flatter every method equally.

## 14. R&P fidelity audit — read from the paper, term by term

Prompted by a code review that found `destroy_related` degenerate. Everything below was
checked against the PDF itself, not against pilot paraphrase.

### 14.1 Shaw relatedness is R&P eq. (17), and we were missing a quarter of it

R&P's relatedness measure, verbatim (§3.1.1, eq. 17):

```
R(i,j) = φ·( d_A(i)A(j) + d_B(i)B(j) )                    location
       + χ·( |T_A(i) − T_A(j)| + |T_B(i) − T_B(j)| )      time
       + ψ·|l_i − l_j|                                    load
       + ω·( 1 − |K_i ∩ K_j| / min{|K_i|,|K_j|} )         servable set
```

with each raw term scaled to [0,1] so that `0 ≤ R ≤ 2(φ+χ)+ψ+ω`, and their §4.3.2 tuned
vector giving **(φ, χ, ψ, ω) = (9, 3, 2, 5)**.

A "request" for SS-IMER is an edge `e = (u,v)`; its two locations A/B are the tail and
the head. The mapping:

| R&P term | weight | our counterpart | was it there? |
|---|---|---|---|
| φ location | 9 | co-location of tails / of heads (0 if shared, else 1 — our nodes carry no metric, so R&P's normalised distance degenerates to an indicator) | yes |
| χ time | 3 | BFS hop from `s` of each endpoint — under IC the earliest step a node can be reached *is* its hop, so hop distance is our time coordinate | tail only; head half was missing |
| ψ load | 2 | the edge's transmission probability | yes |
| ω servable set | 5 | overlap of the *territory* each edge feeds — the head's bounded descendant set, compared with R&P's own min-normalised overlap coefficient (not Jaccard: min-normalisation makes a small set contained in a large one count as fully related, which is the intended semantics) | **missing entirely** |

**Why this mattered.** Within one hop layer every tail is `s`, so the φ and χ terms are
constant by construction — correctly, those edges do start in the same place at the same
time. With ω absent, relatedness reduced to `|p_a − p_b|` alone, and `p` takes only ten
discrete values with 60.75% of edges at 0.018 (PILOT_TESTS.md §30). Measured on 20-edge
hop0 cuts, 190 pairs: **2 distinct relatedness values on the out-degree-486 hub, 4 on
source 253.** `destroy_related` was `destroy_random` with extra steps, in the regime that
dominates the results.

**After restoring ω** (and the head half of χ): 29 and 161 distinct values on the same
two sources. Cost: 0.23 s to build the territory table (once per graph, mean |T| = 213
nodes at depth 2) and ~0.25 s per run for the relatedness evaluations.

Restoring the fourth term is also what makes **R&P's tuned (9,3,2,5) usable**. Equal
weights were not a calibration choice, they were a symptom: with one term missing there
was nothing for their vector to weight. Recalibration on our own instances stays a
Phase 2 item (§10), but the starting point is now theirs, not a placeholder.

Measured effect on search quality, source 1 / k=20 / seed 7, everything else identical:
SAA σ **626.57 → 602.98** (2.6% → 6.2% below the warm start), new-global-best hits 7 → 28,
runtime unchanged at ~46 s. One instance, one seed — a sanity check, not a result.

### 14.2 Hop-layer size is a confound the mechanism cannot remove

Measured candidate-pool sizes per layer:

| source | out(s) | hop0 | hop1 | hop2 | hop3 |
|---|---|---|---|---|---|
| 718 | 4 | 4 | 301 | 7,567 | 12,601 |
| 3616 | 9 | 9 | 350 | 6,073 | 12,120 |
| 253 | 22 | 22 | 6,403 | 6,403 | 13,298 |
| 1 | 186 | 186 | 6,343 | 13,647 | 2,148 |
| 0 (hub) | 486 | 486 | 4,863 | 13,765 | 3,159 |

R&P's `L[⌊y^p·|L|⌋]` draw picks expected rank `|L|/(p+1)`. At p=6 that is rank ~1 out of
a 9-edge hop0 and rank ~1,966 out of a 13,765-edge hop2. R&P tuned a single `p` against
instances of a single size (50 requests); our `|L|` varies by three orders of magnitude
across the layers the scope wheel is choosing between, so one `p` cannot mean the same
thing in each. **This is not fixable by weighting** — the layer sizes are a property of
the graph.

**Consequence for what the thesis may claim.** The Level-2 question is *"do edges beyond
hop0 ever end up in the winning cut?"*, not *"which layer scores best?"*. Evidence for it
is `hop_mix` (composition of the best cut) and `best_hits_by_hop` (which layer supplied
the edges that produced a new global best) — not `scope_weights`. The confound is
asymmetric and works in our favour:

- a **positive** finding (hop>0 edges in winning cuts) is *strengthened* by it — they were
  found despite a search disadvantage of up to 1,900:1;
- a **negative** finding cannot distinguish "deeper edges are not useful" from "deeper
  layers are too large to search", and must be hedged accordingly.

Every run now records `layer_sizes` and `scope_selected` alongside the weights, so the
weights can always be read against pool size and selection frequency rather than alone.

### 14.3 Scope reward attribution follows R&P's own rule

If repair cannot fill from the chosen layer it falls back to the others. The reward was
being booked to the *chosen* scope regardless of where the edges came from. Fixed: a
layer is credited only for edges it actually supplied, and when several layers
contribute, **each gets the full increment** — which is R&P §3.4 verbatim: *"The scores
for both heuristics are updated by the same amount as we can not tell whether it was the
removal or the insertion that was the reason for the 'success'."* Splitting the reward
proportionally would be our own invention and would additionally assume σ is divisible
across the edges of a cut, which is precisely the non-submodularity the thesis argues
against (§1, thesis §3.3).

The fallback provably cannot fire under the current configuration — `|hop0| > k` in every
non-isolated run and `partial` holds only `k − q` edges, so the chosen layer always has at
least `|hop0| − k + q > q` candidates left — and `fallback_used` measured 0 on every layer
across the runs done so far. So this change is currently a no-op; it converts a guarantee
that depended on an algebraic argument into one that holds structurally.

### 14.4 Remaining deliberate departures from R&P

Stated here so the thesis can list them honestly rather than claiming unqualified fidelity:

1. **Worst removal ranks once.** R&P Algorithm 3 rebuilds and re-sorts `L` inside the
   removal loop, since removing one request changes `cost(i,s)` for the rest. We compute
   all marginals once and draw `q` picks from that single ranking. Doing it literally
   costs one full marginal pass per pick (~155 ms), i.e. roughly +2 minutes per run at
   q=8 over ~100 worst-removal calls. Shaw removal *does* re-rank per step, because there
   it costs only dict lookups and is the operator's defining feature.
2. **Cooling rate** derived from our iteration budget, not their c=0.99975 (§6a).
3. **q bounds** proportional to k, since their `4 ≤ ρ` is undefined for our budgets (§6a).
4. **The hop-scope wheel** has no R&P counterpart at all — they have exactly two families
   (§3.3). Ours is a third, scored by their rule but not their idea.
5. **Repair uses the `y^p` sampler**, where R&P's insertion heuristics are deterministic —
   forced by our discrete, heavily-tied scores (§7a).
6. **The noise term (§3.6) is not ported** — it is defined against a continuous distance
   matrix and has no analogue here (§6a).

### 14.5 Reading the paper

`pdftotext`/poppler is not installed on this machine, which is why an earlier attempt to
quote eq. (17) failed. `pypdf` extracts it fine and is installed outside the project
(not in `requirements.txt`, not in `.venv`) since it is a reading tool, not a dependency.

## 15. What the baseline set should be — read from Kimura, Castiglioni and Tong

### 15.1 Kimura's "proposed method" is a sigma-greedy; our six are his *baselines*

Read from the PDF directly. Kimura et al. (2008)'s algorithm for contamination
minimization is:

```
4. for i = 0 to k−1 do
5.    Choose a link e* ∈ E_i minimizing c(G_i(e)),  (e ∈ E_i)
6.    D_{i+1} ← D_i ∪ {e*}
```

Step 5 is *inside* the loop and evaluates on `G_i`, the graph with everything blocked so
far already removed — so it is a **sequential greedy over the measured objective, with
re-evaluation at every step**, not a one-shot top-k by score.

His comparison methods are, verbatim: *"two heuristics based on the well-studied notions
of betweenness and out-degree… as well as the crude baseline of blocking links at
random."* He beats them decisively — 41% vs 30% contamination reduction against
betweenness, and roughly 100x more effective than out-degree and random.

**Consequence for Chapter 6.** Our six topological baselines are (a superset of) the set
Kimura published as the *weak* methods. The method he actually proposed — the one a
reader of this literature expects to see — is currently absent from our comparison. This
does not invalidate the six; they answer "can ALNS beat a fixed topological criterion?",
which is our Level-1 question and is worth answering. But the thesis should say plainly
that the comparison set is heuristic baselines, and it should not imply that beating them
is beating the state of the art. Chapter 3.3 additionally argues that step-by-step greedy
methods "mogu zakazati u hvatanju sinergije više bridova" — an argument about a
sigma-greedy that we do not run, so as written it is cited rather than demonstrated.

Two details worth carrying into the text:

- **Kimura's betweenness baseline recalculates.** He uses Newman–Girvan: remove the
  highest-betweenness link, recompute all scores, repeat. Ours is one-shot top-k on a
  static, source-rooted score. Defensible (REPORT.md §8 forbids recomputation in the
  loop, and source-rooted betweenness is the right notion for a fixed source), but state
  it as a difference rather than leave it looking like an oversight.
- **His conclusion independently backs our degree finding**: *"unlike the task of removing
  nodes, the strategy of blocking links between nodes with high out-degrees is not
  necessarily effective for our problem."* PILOT_TESTS.md §23/§25 found the same thing on
  Bitcoin Alpha empirically; now it has a citation behind it rather than standing alone.

### 15.2 Castiglioni has no experiments at all

Checked: the paper is purely theoretical and closes with *"theoretical and experimental
analysis of the problems on realistic networks would be of extreme interest"* — i.e. they
ran none. There is no baseline to inherit and no experimental protocol to match. §1's
framing (hardness result and domain motivation only) is correct as written.

**Tong et al. (2012)** optimise the leading eigenvalue, not sigma, so their baselines are
eigenvalue-driven and do not transfer. Already how §1 treats them.

### 15.3 Kimura's efficiency trick does not survive our probability distribution

His eq. (6) estimates `c(G_i(e))` as the average of φ over only those sampled scenarios in
which `e` was **unoccupied** — exact under edge independence, one pass, no per-candidate
re-simulation. That is what makes his greedy affordable.

It does not port to Bitcoin Alpha. The estimator's effective sample size is
`(1 − p_e)·M`. Kimura used a single uniform propagation probability (p = 0.2 on the blog
network, 0.03 on Wikipedia), so every candidate kept 80–97% of the sample. Our `p` spans
ten values up to 0.993 (PILOT_TESTS.md §30), where the estimator retains **~3.5 of 500
scenarios** — and high-`p` edges are precisely the ones most worth cutting. Porting his
method to a heterogeneous-`p` network is a genuine finding, not just an implementation
detail, and belongs in the text if the sigma-greedy is built.

The fix keeps his insight without the sample loss: blocking `e` changes a scenario only if
`e` was occupied in it, so

```
sigma(D ∪ {e}) = (1/M)[ Σ_{m: e absent} reach_m(D) + Σ_{m: e present} reach_m(D ∪ {e}) ]
```

The first sum is free from a single base pass; only the second needs recomputation, on a
`p_e` fraction of scenarios. Exact, full sample. Estimated cost hop0-only: ~5 s for a
small source (out=9, k=5), ~2.7 min for the out-degree-486 hub at k=20, against ~25 min
naive. Being deterministic, it would be computed once per (source, k) and reused across
ALNS seeds (PILOT_TESTS.md §19).

**Decision: deferred, not dropped.** The six heuristic baselines go first, since they are
what the Level-1 question needs. The sigma-greedy is the stronger opponent and the one
that makes §3.3's argument empirical; it goes in before the results chapter is written.

## 16. Two settled scope decisions

- **No `fixed_hop_scope` ablation.** A winning cut will in general contain at least one
  hop0 edge, so a hop0-only-versus-hop2-only comparison is not where this thesis's
  evidence lies; the Level-2 question is answered by `hop_mix` and `best_hits_by_hop` on
  the adaptive runs (§14.2). `fixed_hop_scope=` stays in `run_alns` as a diagnostic knob
  but is not part of the experiment matrix. This also retires the open question about the
  ablation's warm start being drawn from hop0 regardless of the pinned layer.
- **`ALNS_MAX_HOP_SCOPE = 3` is a calibration parameter, not a finding.** It currently
  rests on PILOT_TESTS.md §23's "no winning cut ever used hop>=4", which is exactly the
  class of inherited pilot number this project has agreed not to trust. It must be
  re-derived on the calibration set (§10) rather than carried forward.

## 17. Phase 1 smoke tests — the two that could have invalidated a calibration

Both were still unchecked on PLAN.md's Phase 1 list, and both defend properties whose
failure is silent. PILOT_TESTS.md §22 → §32 is this project's own precedent: a calibration
run before the defects were found, and invalidated by them afterwards.

### 17.1 Spectral index alignment — verified, and the weak result is genuine

`code/test_features.py`. Three independent angles, because "it looks aligned" is what the
pilot bug also looked like:

1. **Invariance to vertex insertion order.** The graph is rebuilt with vertices added in a
   shuffled order, so every internal index changes while the named edges do not; scores
   per *named* edge must be unchanged. Worst relative gap **4.5e-15**. This is the pilot's
   bug class stated as a property rather than as a number — it does not depend on knowing
   the right answer.
2. **The pilot's own diagnostic, reproduced.** Tong et al. (2012) derive `u_i·v_j` as a
   first-order estimate of the drop in λmax from removing edge (i,j), so the score must
   rank-correlate with the drop *actually measured* by deleting the edge and recomputing.
   Over 180 edges stratified across the score range: **Spearman 0.965**, against
   PILOT_TESTS.md §18's 0.15 when the eigenvector was indexed by name order and 0.969 once
   aligned.
3. **CSV vs. fresh computation.** `verify_feature_alignment` checks the CSV's endpoints
   line up with the graph, but cannot check that the *values* came from this graph — a
   stale CSV with correct endpoints passes it. Worst relative gap **2.3e-14**.

**Consequence beyond the test.** PILOT_TESTS.md §26 forbids citing any spectral number
from a run made before alignment was confirmed. That restriction is now lifted, and it
settles an ambiguity in the first ALNS-vs-baseline comparison: `spectral` scored a mean
R_mc of 0.189 there, barely above `random`'s 0.218 — with alignment verified, that is a
**genuine property of the heuristic on this dataset**, not a misalignment artifact. It can
be reported as a finding rather than held back as a suspect number.

### 17.2 Frozen scenarios — reproducible, independent, and never mutated

`code/test_scenarios.py`. Four checks, all passing:

- 500 SAA scenarios reproduce **byte-for-byte** from seed 42 (adjacency order included,
  not just set equality). Without this no two runs in the thesis are comparable —
  PILOT_TESTS.md §8 and §24.
- SAA (seed 42) and MC (seed 999) share **no realization**, so out-of-sample validation is
  genuinely out of sample (REPORT.md §7).
- Running all six baselines, the marginal-value path, and a complete ALNS search leaves
  every scenario **bit-identical**, and the evaluator's reusable cut buffer clean. This is
  what says the cut is applied to a mask rather than to the frozen adjacency.
- The search does not mutate `SourceContext`'s shared tables either. `@dataclass(frozen=True)`
  only prevents attribute rebinding; the dicts and lists inside stay mutable and every
  operator reads them every iteration.

Phase 1's remaining unchecked item is the CSV schema check, which belongs with
`run_experiment.py` rather than before it.

## 18. The source population — measured, and it changed the sampling design

`code/source_profile.py` → `data/source_profile.csv`: out-degree, in-degree, deterministic
reachability and SAA σ₀ for all 3683 nodes, 120 s for the whole graph. PLAN.md Phase 2
cannot draw a sample before this exists, because PILOT_TESTS.md §1 requires stratifying on
**reach**, not centrality — topologically distinct nodes there turned out to share a
cascade reach to the decimal, since they land in the same live-edge SCC.

### 18.1 Reach is a smooth heavy-tailed continuum, not bimodal

We expected two modes (a saturated class near σ₀ ≈ 643 and everything else), on the
strength of five hand-picked sources and PILOT_TESTS.md §20. Measured deciles over the
3272 sources with out-degree ≥ 1:

| decile | 0% | 10% | 20% | 30% | 40% | 50% | 60% | 70% | 80% | 90% | 100% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| σ₀ | 1.0 | 4.6 | 10.0 | 14.0 | 22.5 | 35.8 | 66.0 | 127.8 | 323.3 | 598.3 | 653.2 |

**46.6% of eligible sources sit between σ₀ 10 and 100**, and only ~16% are saturated at
400+. PILOT §20's "~17% saturated" was right; the claim that the rest forms a second mode
was not. So "low / mid / high reach" is a real three-way split, just not the one assumed.

**This invalidates the informal ALNS-vs-baseline comparison run before the profile
existed** (8 cells, 3 of 5 sources saturated — 60% against a population rate of 16%). Its
"3 better / 3 same / 2 worse" is not a population estimate, and both ALNS losses fell in
the over-represented saturated regime. Do not carry that headline forward.

### 18.2 Most of the graph cannot be a source at all

- **411 of 3683 nodes have out-degree 0.** No out-edges, σ = 1 with an empty cut. Handled
  as the isolated case rather than crashed (REPORT.md §13), but they are not instances.
- **A further 2088 have out-degree 1–3.** Since `k ≥ out(s)` is the trivial isolated case,
  these cannot support even k = 3.

So the usable population for the smallest budget studied is **1184 sources, 32% of the
graph** — dropping to 500 for k = 10 and 230 for k = 20. That bound belongs in the thesis:
it constrains what "a randomly chosen source" can mean on this dataset, and it is a
property of Bitcoin Alpha's degree distribution (§5's heavy tail), not of our method.

### 18.3 Out-degree × reach, and why both axes are needed

| out-degree | sources | low-reach | saturated | median σ₀ | supports |
|---|---|---|---|---|---|
| [1,4) | 2088 | 1975 | 113 | 16.4 | k ≤ 2 only |
| [4,10) | 684 | 588 | 96 | 90.6 | k=3 |
| [10,20) | 270 | 158 | 112 | 344.2 | k=3, 10 |
| [20,50) | 155 | 33 | 122 | 599.4 | k=3, 10, 20 |
| [50,∞) | 75 | 1 | 74 | 643.6 | all |

Out-degree predicts reach strongly but not deterministically — 5% of the smallest band is
saturated against 99% of the largest — which is exactly why stratifying on one axis alone
would be wrong. Two consequences:

- **At the top the axes collapse**: out-degree ≥ 50 is 99% saturated, so "hub" and
  "saturated" are nearly the same stratum there, and the out ≥ 50 low-reach cell has
  exactly **one** member in the entire graph and cannot be sampled.
- **The off-diagonal cells are the interesting ones for Level 2**: the 96 sources with
  out ∈ [4,10) and 112 with out ∈ [10,20) that are nonetheless saturated have few gateways
  feeding the giant component. That is the redundant-fan-out geometry §8c describes, and
  where hop0-only quarantine should struggle most.

### 18.4 The sample

`code/sample_sources.py` → `data/sample.csv`, drawn once under `SOURCE_SAMPLE_SEED`,
calibration taken first and measurement from the remainder so the two are disjoint by
construction rather than by discipline (PILOT_TESTS.md §35 B7, which exists because the
pilot audit found three samples in circulation). 7 viable cells × (2 calibration + 4
measurement) = **15 calibration + 28 measurement sources**.

Each row carries `predicted_seconds` from §11's cost model, so an experiment plan can be
costed before it is run rather than discovered to have overrun. One ALNS run over the full
measurement set is ~992 s; over the calibration set ~496 s. That is the number that makes
a 30-minute calibration a design constraint rather than a detail (§19).
