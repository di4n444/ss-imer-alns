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
