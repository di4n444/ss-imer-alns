# REPORT — thesis-facing working document

This file is the single source of truth for everything that needs to end up in the thesis
text: decisions made and why, numbers (pointer to the CSV that holds them, never retyped
here), and things that must not be forgotten when writing. It is not the thesis — it is the
raw material for it. Written in English for precision; translate into Croatian when drafting
the actual chapters.

Update this file continuously as we work, not at the end.

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
- `k ≥ out(s)` — decided as a **hard error**, not silent isolation (this reverses an
  earlier pilot note; confirm this is still the intended behavior before the first
  experiment run touches a hub source).

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

## 7. Scenario architecture and candidate space — corrections (supersedes earlier draft of §6)

- **`create_subgraphs.py` builds frozen live-edge realizations (scenario subgraphs),
  not hop-layer candidate pools.** A scenario is a bond-percolation-style realization:
  each edge is independently kept with probability `p` (its IC transmission
  probability), producing an unweighted subgraph. Two disjoint, separately seeded sets
  are generated once and then treated as immutable: an in-sample (SAA) set and an
  out-of-sample (Monte Carlo) set. Nothing downstream is allowed to mutate them —
  evaluation always works on a copy/mask, never on the frozen scenario objects directly.
- **`fitness_evaluator.py` only evaluates SAA** — given a candidate cut `D` and the
  frozen in-sample scenario set, compute mean reach via masked BFS from `s`. It does not
  generate scenarios.
- **A separate module evaluates out-of-sample Monte Carlo** — new file
  `oos_evaluator.py`, used only for final/best-cut validation after optimization, never
  inside the ALNS loop. Keeps "search objective" (SAA) and "reported result" (OOS)
  structurally separate so there's no risk of accidentally optimizing against OOS data.
- **Hop-layer candidate windowing is kept, but it isn't a standalone script.**
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
