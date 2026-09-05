"""The measurement run -> data/results.csv.

Two experiments, both on the measurement sources only (the preparation sources are never
touched here):

  A. **Population sweep.** Every measurement source once, at the budget its out-degree can
     support. Answers the Level-1 question - can adaptive search beat a fixed topological
     criterion - across the whole sampled population rather than on hand-picked instances.

  B. **Budget sweep.** Three sources, several budgets each, to show how the picture changes
     with k. Sources are chosen by *structure* (which cell they sit in) and, within a cell,
     by cost - never by how well any method did on them, which would import a result into
     the design.

Both are fixed here, in advance, and stated in the thesis before any number is reported.

**Rows are written after every cell.** A run that is stopped early - and this one has a
wall-clock budget - still leaves every completed cell on disk. Nothing is held until the
end, because the one thing worse than a short experiment is an hour of compute with no
output.
"""

import sys
import time

import pandas as pd

from config import (ALNS_MAX_ITER, ALNS_RUN_SEED, DATA_DIR,
                    SAMPLE_OUT_DEGREE_BANDS)
from run_experiment import Workbench, run_cell

# Wall-clock cap. The driver checks it between cells and stops cleanly rather than
# overrunning; whatever finished is already written.
BUDGET_SECONDS = 55 * 60

# Experiment A: the budget each out-degree band is run at. k stays clear of out(s) in every
# band, so no cell collapses into the trivial isolated case, and the budget scales with what
# the source can actually support.
BUDGET_BY_BAND = {(4, 10): 3, (10, 20): 5, (20, 50): 10, (50, 10 ** 9): 20}

# Experiment B: same out-degree band at two very different reach levels, plus the hub band.
# Everything about these three is decided by the cell they belong to.
SWEEP_CELLS = ["out[20,50) low-reach", "out[20,50) saturated", "out[50,+) saturated"]
SWEEP_BUDGETS = (3, 5, 10, 15, 20)


def budget_for(out_degree: int) -> int:
    for (lo, hi), k in BUDGET_BY_BAND.items():
        if lo <= out_degree < hi:
            return k
    raise ValueError(f"no budget defined for out-degree {out_degree}")


def sweep_sources(sample: pd.DataFrame) -> list:
    """One source per sweep cell: the second-cheapest member, so the sweep is affordable
    without being the extreme case of its cell. A cost rule, not an outcome rule."""
    chosen = []
    for cell in SWEEP_CELLS:
        members = sample[sample.cell == cell].sort_values("sigma0_saa")
        if members.empty:
            print(f"  ! no measurement source in {cell}, skipping")
            continue
        chosen.append(members.iloc[min(1, len(members) - 1)])
    return chosen


def plan(sample: pd.DataFrame) -> list:
    """Every (source, k, tag) to run, cheapest first.

    Cheapest first for a practical reason: if the budget runs out, what is missing is the
    expensive tail rather than an arbitrary slice, and the cells that did finish still
    cover every cell of the sample."""
    cells = [(int(r.source), budget_for(int(r.out_degree)), float(r.predicted_seconds),
              "population")
             for _, r in sample.iterrows()]

    for row in sweep_sources(sample):
        for k in SWEEP_BUDGETS:
            if k < int(row.out_degree):   # k >= out(s) is the trivial isolated case
                cells.append((int(row.source), k, float(row.predicted_seconds), "k-sweep"))

    return sorted(cells, key=lambda c: c[2])


def main(pilot: bool = False):
    started = time.time()
    sample = pd.read_csv(DATA_DIR / "sample.csv")
    measurement = sample[sample.role == "measurement"]

    cells = plan(measurement)
    if pilot:
        cells = cells[:2]

    predicted = sum(c[2] for c in cells)
    print(f"{len(cells)} cells over {measurement.source.nunique()} measurement sources")
    print(f"  {sum(1 for c in cells if c[3] == 'population')} population, "
          f"{sum(1 for c in cells if c[3] == 'k-sweep')} k-sweep")
    print(f"  ~{predicted:.0f}s of ALNS predicted, plus baselines; "
          f"budget {BUDGET_SECONDS}s\n")

    bench = Workbench()
    print(f"workbench ready in {time.time() - started:.0f}s\n")

    filename = "pilot.csv" if pilot else "results.csv"
    rows = []
    for n, (source, k, _, tag) in enumerate(cells, start=1):
        if time.time() - started > BUDGET_SECONDS:
            print(f"\n! budget reached, stopping with {n - 1} of {len(cells)} cells done")
            break

        cell_started = time.time()
        ev_saa, ev_mc = bench.evaluators(source)
        # Kept separately rather than sliced back off `rows`: a fixed-width window over the
        # accumulated list reaches into the previous cell the moment the row count per cell
        # is not what the window assumed, and then the progress line reports the wrong run.
        produced = run_cell(bench.context(source), k, ev_saa, ev_mc,
                            seeds=(ALNS_RUN_SEED,), tag=tag)
        rows += produced

        # Rewritten in full after every cell rather than appended: the greedy and ALNS rows
        # carry different keys, and letting pandas align them each time is safer than
        # trusting a fixed header. At a few hundred rows the cost is nothing.
        pd.DataFrame(rows).to_csv(DATA_DIR / filename, index=False)

        alns = [r for r in produced if r["method"] == "alns"][0]
        # R is a reduction, so better is larger - this is a max, not a min
        best_greedy = max((r["R_mc"] for r in produced
                           if r["method"].startswith("greedy")), default=float("nan"))
        elapsed = time.time() - started
        print(f"[{n:>3}/{len(cells)}] {tag:<10} source {source:>5} k={k:<3} "
              f"R_mc alns {alns['R_mc']:+.3f} vs best greedy {best_greedy:+.3f}  "
              f"{time.time() - cell_started:>5.1f}s  (total {elapsed / 60:.1f} min)")

    frame = pd.DataFrame(rows)
    print(f"\nwrote {len(frame)} rows to data/{filename} "
          f"in {(time.time() - started) / 60:.1f} min")
    return frame


# ---------------------------------------------------------------- stage 2 ----
#
# Experiment C: iteration probe. Two cells where ALNS lost to a baseline - so a better cut
# demonstrably exists and is reachable - run again with more iterations and nothing else
# changed. Cells whose ceiling is low for reasons other than search (a hub at a budget far
# too small to contain it) cannot answer this question and are not used.
PROBES = [(96, 10, 500), (123, 20, 1000)]

# Experiment D: extend the hub budget sweep until k is a real fraction of the fan-out.
# Source 13 has out-degree 92 and was only swept to k=20, i.e. never past a fifth of its
# out-edges; these carry it to four fifths.
HUB_SWEEP = (13, (30, 45, 60, 75))

# Experiment E: fill out the picture with one cell per source at budgets that are a
# sensible share of what that source can spend, rather than a fixed k that means something
# different on every source.
TYPICAL_SHARES = (0.20, 0.35, 0.50)
TARGET_CELLS = 100


def typical_cells(sample, already, room):
    """Cells at a budget proportional to the source's out-degree, cheapest first."""
    candidates = []
    for _, row in sample.iterrows():
        out_degree = int(row.out_degree)
        for share in TYPICAL_SHARES:
            k = max(3, round(share * out_degree))
            if k < out_degree and (int(row.source), k) not in already:
                already.add((int(row.source), k))
                candidates.append((int(row.source), k, float(row.predicted_seconds),
                                   "typical"))
    return sorted(candidates, key=lambda c: c[2])[:room]


def final():
    """Everything still owed for the results chapter, written after every cell."""
    started = time.time()
    frame = pd.read_csv(DATA_DIR / "results.csv")
    sample = pd.read_csv(DATA_DIR / "sample.csv")
    measurement = sample[sample.role == "measurement"]
    already = set(zip(frame.source, frame.k))

    done = frame.groupby(["source", "k", "tag"]).ngroups
    hub_cells = [(HUB_SWEEP[0], k, "k-sweep") for k in HUB_SWEEP[1]]
    room = TARGET_CELLS - done - len(PROBES) - len(hub_cells)
    fill = typical_cells(measurement, already | {(s, k) for s, k, _ in hub_cells}, room)

    print(f"{done} cells already; adding {len(PROBES)} probes, {len(hub_cells)} hub-sweep, "
          f"{len(fill)} typical -> {done + len(PROBES) + len(hub_cells) + len(fill)}")

    bench = Workbench()
    print(f"workbench ready in {time.time() - started:.0f}s\n")

    def store(new):
        nonlocal frame
        frame = pd.concat([frame, pd.DataFrame(new)], ignore_index=True)
        frame.to_csv(DATA_DIR / "results.csv", index=False)

    for source, k, iterations in PROBES:
        before = frame[(frame.source == source) & (frame.k == k)
                       & (frame.method == "alns")].R_mc.iloc[0]
        ev_saa, ev_mc = bench.evaluators(source)
        produced = run_cell(bench.context(source), k, ev_saa, ev_mc,
                            seeds=(ALNS_RUN_SEED,), baselines=False,
                            alns_params={"max_iter": iterations}, tag=f"probe{iterations}")
        store(produced)
        print(f"probe  source {source:>5} k={k:<3} {iterations:>5} iter: "
              f"R_mc {before:+.3f} -> {produced[0]['R_mc']:+.3f}")

    queue = [(s, k, 0.0, tag) for s, k, tag in hub_cells] + fill
    for n, (source, k, _, tag) in enumerate(queue, start=1):
        if time.time() - started > BUDGET_SECONDS:
            print(f"\n! budget reached at {n - 1} of {len(queue)}")
            break
        cell_started = time.time()
        ev_saa, ev_mc = bench.evaluators(source)
        produced = run_cell(bench.context(source), k, ev_saa, ev_mc,
                            seeds=(ALNS_RUN_SEED,), tag=tag)
        store(produced)
        alns = [r for r in produced if r["method"] == "alns"][0]
        best = max(r["R_mc"] for r in produced if r["method"].startswith("greedy"))
        print(f"[{n:>3}/{len(queue)}] {tag:<8} source {source:>5} k={k:<3} "
              f"alns {alns['R_mc']:+.3f} vs best {best:+.3f}  "
              f"{time.time() - cell_started:>5.1f}s (total {(time.time()-started)/60:.1f}m)")

    print(f"\nresults.csv: {len(frame)} rows, "
          f"{frame.groupby(['source','k','tag']).ngroups} cells, "
          f"{(time.time() - started) / 60:.1f} min")
    return frame


# Experiment F: the same instances searched longer. max_iter is fixed at 300 regardless of
# k or fan-out, and two probes showed that starves the larger budgets badly. The rule is
# linear in k, since k is what sets the size of the solution being assembled, and capped so
# the deepest budget of the hub sweep stays affordable. No stagnation rule is added: R&P
# stop on a fixed iteration count and nothing else, and inventing an early exit here would
# also truncate the cooling schedule, which is derived from max_iter.
RERUN_ITERATIONS = lambda k: min(100 * k, 2000)
RERUN_CELLS = 50


def rerun_cells(results, sample):
    """Half the cells, chosen so no two are the same scenario twice.

    One cell per (stratum, budget) pair - keeping the cheapest - which is what drops the
    near-duplicates: four sources from the same band at the same k answer the same question
    four times. Selection is entirely structural; nothing looks at how any method scored."""
    cells = (results[results.method == "alns"][["source", "k", "tag"]]
             .drop_duplicates()
             .merge(sample[["source", "cell"]].drop_duplicates(), on="source"))
    cells = cells[~cells.tag.astype(str).str.startswith("probe")]
    seconds = results[results.method == "alns"].groupby(["source", "k"]).seconds.first()
    cells["seconds"] = cells.set_index(["source", "k"]).index.map(seconds)

    unique = (cells.sort_values("seconds")
                   .drop_duplicates(subset=["cell", "k"], keep="first"))
    return unique.nsmallest(RERUN_CELLS, "seconds")


def rerun():
    started = time.time()
    results = pd.read_csv(DATA_DIR / "results.csv")
    sample = pd.read_csv(DATA_DIR / "sample.csv")
    chosen = rerun_cells(results, sample)

    predicted = sum(row.seconds * RERUN_ITERATIONS(int(row.k)) / ALNS_MAX_ITER
                    for _, row in chosen.iterrows())
    print(f"{len(chosen)} cells, ~{predicted / 60:.0f} min predicted "
          f"(was {chosen.seconds.sum() / 60:.1f} min at {ALNS_MAX_ITER})")

    bench = Workbench()
    rows = []
    for n, (_, row) in enumerate(chosen.iterrows(), start=1):
        source, k = int(row.source), int(row.k)
        iterations = RERUN_ITERATIONS(k)
        cell_started = time.time()
        ev_saa, ev_mc = bench.evaluators(source)
        produced = run_cell(bench.context(source), k, ev_saa, ev_mc,
                            seeds=(ALNS_RUN_SEED,), baselines=False,
                            alns_params={"max_iter": iterations}, tag="scaled")
        rows += produced
        pd.DataFrame(rows).to_csv(DATA_DIR / "results_scaled.csv", index=False)
        before = results[(results.source == source) & (results.k == k)
                         & (results.method == "alns")].R_mc.iloc[0]
        print(f"[{n:>2}/{len(chosen)}] source {source:>5} k={k:<3} {iterations:>4} iter: "
              f"{before:+.3f} -> {produced[0]['R_mc']:+.3f}  "
              f"{time.time() - cell_started:>5.1f}s (total {(time.time()-started)/60:.1f}m)")

    print(f"\nwrote {len(rows)} rows to data/results_scaled.csv, "
          f"{(time.time() - started) / 60:.1f} min")


if __name__ == "__main__":
    if "--rerun" in sys.argv:
        rerun()
    elif "--final" in sys.argv:
        final()
    else:
        main(pilot="--pilot" in sys.argv)
