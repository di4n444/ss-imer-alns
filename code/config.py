"""Single source of truth for paths, seeds, and tunable constants.

Nothing outside this file should hardcode a literal that could plausibly need to
change or be looked up while reading results — see REPORT.md and PLAN.md for why.
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
# See REPORT.md §9a. "latest" keeps the row with the largest `time` value.
DUPLICATE_EDGE_POLICY = "latest"  # one of: "latest"

# --- analyse_graph.py ----------------------------------------------------

# igraph delegates its RNG to Python's `random` module by default, so seeding this
# before a stochastic call (Erdos-Renyi null model, Louvain) makes it reproducible.
ER_NULL_MODEL_SEED = 1
LOUVAIN_RESTART_SEEDS = range(1, 21)  # best-of-20, PILOT_TESTS.md §36

# --- create_subgraphs.py (frozen live-edge scenarios, REPORT.md §7) ------

SAA_SCENARIO_COUNT = 500  # thesis Ch.4 "Fitness funkcija" text, already decided
SAA_SCENARIO_SEED = 42
MC_SCENARIO_COUNT = 2000  # thesis Ch.4: "2000 neovisnih MC scenarija" for OOS validation
MC_SCENARIO_SEED = 999  # must differ from SAA_SCENARIO_SEED - in-sample/OOS independence

# --- operators.py: destroy-side determinism exponents (R&P 2006 tuned vector, §4.3.2 -
# their (p, p_worst) = (6, 3); starting points, to recalibrate on our problem later) --

DESTROY_WORST_P = 3
DESTROY_SHAW_P = 6

# --- alns_optimizer.py: R&P (2006) tuned vector (§4.3.2), REPORT.md §6a — starting -
# points to recalibrate on our own problem (PLAN.md Phase 2), not final values.     -

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
# much smaller k (REPORT.md §6a - a fixed floor of 4 can exceed k itself). Kept the
# pilot's k-proportional version instead - a justified departure, not an oversight.
ALNS_Q_MIN_FRAC = 0.1
ALNS_Q_MAX_FRAC = 0.4

# Repair's rank-biased selection exponent has no R&P analog at all (their insertion
# heuristics are deterministic - REPORT.md §7a explains why ours can't be). Entirely
# our own choice, not sourced from the paper; starting near Shaw's p as a reasonable
# "mostly greedy, still explores tied groups" default.
ALNS_REPAIR_P = 6

ALNS_RUN_SEED = 7  # per-run RNG seed; experiments vary this deliberately (REPORT.md §3)

# Hop scope: repair draws from ONE hop layer per iteration, chosen by its own roulette
# wheel alongside the destroy and repair wheels (REPORT.md §12). Layers start equally
# weighted so ALNS *learns* which distance pays — that learning is the Level-2 claim,
# so seeding it with a prior would be assuming the answer.
#
# Layers deeper than this are excluded outright: PILOT_TESTS.md §23 found no winning
# cut ever used hop>=4 (hop0 in 31/40 cases, then 9/6/4 at hops 1/2/3). Keeping them in
# only spends iterations on candidates that never win. Revisit in calibration.
ALNS_MAX_HOP_SCOPE = 3
