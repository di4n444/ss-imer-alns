"""ALNS parameter calibration -> data/calibration.csv.

REPORT.md §10: the calibration *process* is thesis content, not an internal tuning step,
so this writes a CSV of everything tried rather than printing a conclusion. R&P calibrate
the same way (§4.3.2): start from a working setting, vary one parameter at a time over a
few values, keep what wins, move on.

**The budget is 30 minutes, and that shapes the design rather than just shrinking it.**
Runtime tracks sigma_0 (REPORT.md §11), so one saturated source costs ~25 low-reach ones
and the composition of the calibration cells decides everything. Two phases:

  Phase A tests one hypothesis with a mechanism behind it. ALNS lost to
  `greedy_probability` on large hop0 pools, and R&P's `L[y^p |L|]` draw picks expected
  rank |L|/(p+1) - so at repair_p=6 on a 486-edge hop0 it selects around rank 69 while the
  baseline takes ranks 1-20. If that is the cause, raising repair_p should close the gap
  *specifically on hub sources*. Expensive per run, so it is run only where the prediction
  applies.

  Phase B sweeps the remaining parameters one at a time on affordable cells, carrying
  Phase A's winner.

**Two limitations that follow from the budget and must be reported with any conclusion:**
single seed, so only large effects are distinguishable from tie-break variance
(REPORT.md §3); and the cells under-represent saturated sources relative to their ~16%
population share, Phase A being the deliberate exception. PILOT_TESTS.md §22's own
conclusion is the decision rule here: *"Ako razlike nisu jasne, ne dirati defaulte."*
"""

import time

import pandas as pd

from config import (
    ALNS_MAX_HOP_SCOPE,
    ALNS_MAX_ITER,
    ALNS_Q_MAX_FRAC,
    ALNS_REPAIR_P,
    ALNS_RUN_SEED,
    CALIBRATION_BUDGET_SECONDS,
    DATA_DIR,
)
from run_experiment import Workbench, run_cell, write_rows
from sample_sources import predicted_seconds

MIN_RELATIVE_GAIN = 0.02  # below this, a difference is noise at one seed - PILOT §22


def budgets_for(out_degree: int) -> list:
    """k must stay below out(s) or the instance is trivially isolated (REPORT.md §13).
    Two budgets per source: the small-budget regime everything can support, and a larger
    one where the source is wide enough, since PILOT_TESTS.md §25 warns that a single
    fixed k is a map of one budget rather than a result."""
    budgets = [3]
    if out_degree > 10:
        budgets.append(10)
    elif out_degree - 1 > 3:
        budgets.append(out_degree - 1)
    return budgets


def plan(sample: pd.DataFrame) -> tuple:
    """Choose Phase A and Phase B cells and cost them *before* running anything."""
    calib = sample[sample.role == "calibration"]
    hubs = calib.nlargest(2, "out_degree")
    phase_a = [(int(r.source), 20, float(r.sigma0_saa)) for _, r in hubs.iterrows()]

    affordable = calib[~calib.source.isin(hubs.source)].nsmallest(7, "predicted_seconds")
    phase_b = [(int(r.source), k, float(r.sigma0_saa))
               for _, r in affordable.iterrows()
               for k in budgets_for(int(r.out_degree))]
    return phase_a, phase_b


def cost(cells: list, settings: int = 1, iteration_scale: float = 1.0) -> float:
    return sum(predicted_seconds(s, int(300 * iteration_scale))
               for _, _, s in cells) * settings


def main():
    started = time.time()
    sample = pd.read_csv(DATA_DIR / "sample.csv")
    phase_a, phase_b = plan(sample)

    repair_values = [ALNS_REPAIR_P, 20, 60]
    variants = {
        "default": {},
        "max_iter=600": {"max_iter": 600},
        "q_max_frac=0.7": {"q_max_frac": 0.7},
        "max_hop_scope=1": {"max_hop_scope": 1},
    }
    predicted = (cost(phase_a, len(repair_values))
                 + cost(phase_b, len(variants) - 1) + cost(phase_b, 1, 2.0))
    print(f"plan: phase A {len(phase_a)} cells x {len(repair_values)} repair_p values, "
          f"phase B {len(phase_b)} cells x {len(variants)} variants")
    print(f"predicted {predicted:.0f}s against a {CALIBRATION_BUDGET_SECONDS}s budget\n")

    bench = Workbench()
    print(f"workbench ready in {time.time() - started:.0f}s\n")
    rows = []

    def spend(cells, tag, params, with_baselines):
        for source, k, _ in cells:
            if time.time() - started > CALIBRATION_BUDGET_SECONDS:
                print(f"  ! budget exhausted, stopping before source {source} k={k}")
                return False
            ev_saa, ev_mc = bench.evaluators(source)
            rows.extend(run_cell(bench.context(source), k, ev_saa, ev_mc,
                                 seeds=(ALNS_RUN_SEED,), alns_params=params,
                                 baselines=with_baselines, tag=tag))
        return True

    print("PHASE A - does repair_p explain the hub losses?")
    for i, p in enumerate(repair_values):
        t = time.time()
        # Baselines only once per cell: they do not depend on ALNS parameters.
        if not spend(phase_a, f"A repair_p={p}", {"repair_p": p}, with_baselines=(i == 0)):
            break
        print(f"  repair_p={p:<3} {time.time() - t:.0f}s")

    frame = pd.DataFrame(rows)
    best_p = ALNS_REPAIR_P
    if not frame.empty:
        alns = frame[(frame.method == "alns") & frame.tag.str.startswith("A ")]
        if not alns.empty:
            by_p = alns.groupby("tag").R_mc.median().sort_values(ascending=False)
            print(f"\n  median R_mc by setting: "
                  + ", ".join(f"{t.split('=')[1]}:{v:.4f}" for t, v in by_p.items()))
            winner = float(by_p.iloc[0])
            default = float(by_p.get(f"A repair_p={ALNS_REPAIR_P}", winner))
            gain = (winner - default) / max(abs(default), 1e-9)
            if gain > MIN_RELATIVE_GAIN:
                best_p = int(by_p.index[0].split("=")[1])
                print(f"  -> repair_p={best_p} ({gain:+.1%} vs default); carried into phase B")
            else:
                print(f"  -> no clear winner ({gain:+.1%} <= {MIN_RELATIVE_GAIN:.0%}); "
                      f"keeping repair_p={ALNS_REPAIR_P} (PILOT_TESTS.md §22)")

    print(f"\nPHASE B - one parameter at a time, repair_p={best_p}")
    for name, override in variants.items():
        t = time.time()
        params = {"repair_p": best_p, **override}
        if not spend(phase_b, f"B {name}", params, with_baselines=(name == "default")):
            break
        print(f"  {name:<18} {time.time() - t:.0f}s")

    frame = write_rows(rows, "calibration.csv")
    print(f"\ntotal {time.time() - started:.0f}s "
          f"(budget {CALIBRATION_BUDGET_SECONDS}s)\n")
    report(frame, best_p)


def report(frame: pd.DataFrame, best_p: int) -> None:
    """Median across cells, never mean: R and sigma are skewed and a few saturated hubs
    with R near zero would drag a mean around (PILOT_TESTS.md §23/§37)."""
    alns = frame[frame.method == "alns"]

    print("PHASE A - ALNS vs the best baseline on hub cells")
    a = alns[alns.tag.str.startswith("A ")]
    if not a.empty:
        base = frame[(frame.tag.str.startswith("A ")) & (frame.method != "alns")]
        for (source, k), cell in a.groupby(["source", "k"]):
            best = base[(base.source == source) & (base.k == k)].R_mc.max()
            line = "  ".join(f"{r.tag.split('=')[1]:>3}:{r.R_mc:.4f}"
                             for _, r in cell.sort_values("tag").iterrows())
            print(f"  source {source:>5} k={k:<3} best baseline {best:.4f}  |  ALNS {line}")

    print("\nPHASE B - median R_mc across cells, one parameter at a time")
    b = alns[alns.tag.str.startswith("B ")]
    if b.empty:
        return
    stats = b.groupby("tag").agg(median_R_mc=("R_mc", "median"),
                                 median_gap=("saa_mc_gap", "median"),
                                 cells=("R_mc", "size"), seconds=("seconds", "sum"))
    baseline = stats.loc["B default", "median_R_mc"] if "B default" in stats.index else None
    print(f"  {'variant':<20} {'median R_mc':>12} {'vs default':>11} "
          f"{'median SAA-MC':>14} {'cells':>6} {'sec':>7}")
    for tag, r in stats.sort_values("median_R_mc", ascending=False).iterrows():
        delta = "" if baseline is None else f"{(r.median_R_mc - baseline) / max(abs(baseline), 1e-9):+.1%}"
        print(f"  {tag[2:]:<20} {r.median_R_mc:>12.4f} {delta:>11} "
              f"{r.median_gap:>14.4f} {r.cells:>6.0f} {r.seconds:>7.0f}")

    if baseline is not None:
        winner = stats.median_R_mc.idxmax()
        gain = (stats.median_R_mc.max() - baseline) / max(abs(baseline), 1e-9)
        print(f"\n  decision rule (PILOT_TESTS.md §22): change a default only on a clear "
              f"margin (> {MIN_RELATIVE_GAIN:.0%} at one seed).")
        if gain > MIN_RELATIVE_GAIN and winner != "B default":
            print(f"  -> {winner[2:]} wins by {gain:+.1%}. Confirm across seeds before adopting.")
        else:
            print(f"  -> best variant is {winner[2:]} at {gain:+.1%}: not a clear margin, "
                  f"keep current defaults (max_iter={ALNS_MAX_ITER}, "
                  f"q_max_frac={ALNS_Q_MAX_FRAC}, max_hop_scope={ALNS_MAX_HOP_SCOPE}, "
                  f"repair_p={best_p}).")


if __name__ == "__main__":
    main()
