"""Single source of truth for paths, seeds, and tunable constants.

Nothing outside this file should hardcode a literal that could plausibly need to
change or be looked up while reading results.
This file grows as later modules need new constants; it is not meant to be
complete up front.
"""

from pathlib import Path

# --- paths -------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
FIGURES_DIR = PROJECT_ROOT / "figures"

RAW_DATASET_PATH = DATA_DIR / "soc-sign-bitcoinalpha.csv"

# --- data cleaning -------------------------------------------------------

# Bitcoin Alpha's raw CSV has no header: SOURCE, TARGET, RATING, TIME.
RAW_DATASET_COLUMNS = ["source", "target", "rating", "time"]

# A (source, target) pair can be rated more than once over time. One edge,
# one probability is required for SS-IMER, so duplicates must be resolved.
# "latest" keeps the row with the largest `time` value.
DUPLICATE_EDGE_POLICY = "latest"  # one of: "latest"

# --- analyse_graph.py ----------------------------------------------------

# igraph delegates its RNG to Python's `random` module by default, so seeding this
# before a stochastic call (Erdos-Renyi null model, Louvain) makes it reproducible.
ER_NULL_MODEL_SEED = 1
LOUVAIN_RESTART_SEEDS = range(1, 21)  # best-of-20

# --- create_subgraphs.py (frozen live-edge scenarios) --------------------

SAA_SCENARIO_COUNT = 500  # thesis Ch.4 "Fitness funkcija" text, already decided
SAA_SCENARIO_SEED = 42
MC_SCENARIO_COUNT = 2000  # thesis Ch.4: "2000 neovisnih MC scenarija" for OOS validation
MC_SCENARIO_SEED = 999  # must differ from SAA_SCENARIO_SEED - in-sample/OOS independence

# --- operators.py: destroy-side determinism exponents (R&P 2006 tuned vector, §4.3.2 -
# their (p, p_worst) = (6, 3); starting points, to recalibrate on our problem later) --

DESTROY_WORST_P = 3
DESTROY_SHAW_P = 6

# Shaw relatedness weights, R&P eq. (17). Their §4.3.2 tuned vector gives
# (phi, chi, psi, omega) = (9, 3, 2, 5), read from the paper directly. These are usable
# as-is only because every one of R&P's four terms has a counterpart in our formulation
# (operators._relatedness documents the mapping term by term); when a term was missing
# the weights had to be equal-and-meaningless instead. Still starting points to
# recalibrate, but grounded ones.
SHAW_PHI = 9    # location: are the two edges attached to the same tail / same head
SHAW_CHI = 3    # time: how far into the cascade each endpoint is reached (BFS hop)
SHAW_PSI = 2    # load: transmission probability carried by the edge
SHAW_OMEGA = 5  # servable set: overlap of the territory each edge feeds

# Depth of the "territory" set standing in for R&P's vehicle set K_i. Bounded for the
# same reason K_i is bounded: on a graph whose SCC holds 86.7% of nodes, the unbounded
# descendant set is nearly everything for nearly everyone, and every pair would look
# identical. Measured: depth 2 gives mean |T| = 213 nodes.
TERRITORY_DEPTH = 2

# --- alns_optimizer.py: R&P (2006) tuned vector, section 4.3.2 — starting -------
# points to recalibrate on our own problem, not final values.     -

ALNS_SIGMA1 = 33  # new global best
ALNS_SIGMA2 = 9   # better than current, unvisited
ALNS_SIGMA3 = 13  # worse but accepted, unvisited
ALNS_REACTION_FACTOR = 0.1   # r in w_{i,j+1} = w_ij*(1-r) + r*(score/count)
ALNS_START_TEMP_CONTROL = 0.05  # w: solution w% worse than initial accepted w.p. 0.5

# R&P's own segment length (100) and iteration budget (25000) are tuned for VRP
# instances with hundreds of requests; ours has a far smaller search space and a
# more expensive per-iteration cost (SAA evaluation), so both need independent
# starting points, not literal transplants - pilot's own SS-IMER-specific defaults,
# not R&P's, and explicitly flagged for Phase 2 recalibration.
ALNS_MAX_ITER = 300
ALNS_SEGMENT_LENGTH = 20

# Cooling rate c is NOT copied from R&P's c=0.99975: that value only makes sense
# relative to their 25000-iteration budget (0.99975^25000 ~ 0.002, most of the
# cooling). Applied to our much shorter runs it would barely cool at all
# (0.99975^300 ~ 0.93). Instead we derive c from our own max_iter, targeting a
# standard final-temperature fraction of the start temperature (textbook SA
# practice, not R&P-specific) - see alns_optimizer.py.
ALNS_FINAL_TEMP_FRACTION = 0.01

# q bounds: R&P's literal formula (4 <= q <= min(100, xi*n), xi=0.4) breaks for our
# much smaller k. Kept the
# pilot's k-proportional version instead - a justified departure, not an oversight.
ALNS_Q_MIN_FRAC = 0.1
ALNS_Q_MAX_FRAC = 0.4

# Repair's rank-biased selection exponent has no R&P analog at all (their insertion
# heuristics are deterministic; ours cannot be, since our scores tie heavily). Entirely
# our own choice, not sourced from the paper; starting near Shaw's p as a reasonable
# "mostly greedy, still explores tied groups" default.
ALNS_REPAIR_P = 6

ALNS_RUN_SEED = 7  # per-run RNG seed; experiments vary this deliberately

# Hop scope: repair draws from ONE hop layer per iteration, chosen by its own roulette
# wheel alongside the destroy and repair wheels. Layers start equally
# weighted so ALNS *learns* which distance pays — that learning is the Level-2 claim,
# so seeding it with a prior would be assuming the answer.
#
# Layers deeper than this are excluded outright: pilot runs found no winning
# cut ever used hop>=4 (hop0 in 31/40 cases, then 9/6/4 at hops 1/2/3). Keeping them in
# only spends iterations on candidates that never win. Revisit in calibration.
ALNS_MAX_HOP_SCOPE = 3

# --- source sampling -------------
#
# B7's rule, learned the hard way: ONE sample, ONE seed, calibration disjoint from
# measurement. The pilot audit found three different source samples in circulation and
# could no longer say which numbers came from which. data/sample.csv is the only sample.

SOURCE_SAMPLE_SEED = 20260904

# A source needs out(s) > k or the instance is the trivial isolated case,
# so out-degree < 4 cannot support the smallest budget we study. That excludes 2088 of
# 3272 eligible nodes - a fact about the graph that belongs in the thesis, not a
# convenience filter.
SAMPLE_MIN_OUT_DEGREE = 4

# Stratification axes, measured rather than assumed (data/source_profile.csv):
# reach is a smooth heavy-tailed continuum, not the bimodal split we expected, and
# out-degree predicts it strongly but not deterministically - which is exactly why both
# axes are needed. Stratify on reach, never on centrality alone.
SAMPLE_OUT_DEGREE_BANDS = [(4, 10), (10, 20), (20, 50), (50, 10**9)]
SAMPLE_SATURATED_SIGMA0 = 400.0  # above this a source reaches the giant live-edge component

SAMPLE_CALIBRATION_PER_CELL = 2
SAMPLE_MEASUREMENT_PER_CELL = 4

# --- calibration ---
#
# Hard wall-clock budget. Runtime scales with sigma_0, so a calibration
# set's cost is decided by its reach composition, not its size: one saturated source costs
# ~25 low-reach ones. The driver costs its plan against this before running anything.
CALIBRATION_BUDGET_SECONDS = 1800

# Measured fit to (sigma_0, seconds) = (41, 2), (74, 3.5), (643, 55) at 300 iterations.
CALIBRATION_COST_PER_SIGMA0 = 0.088
CALIBRATION_COST_INTERCEPT = -1.6
