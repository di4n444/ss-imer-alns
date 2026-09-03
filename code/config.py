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
