"""ALNS parameter calibration -> data/calibration.csv.

Answers one question: which parameter values should the ALNS run with. It is not an
experiment and it tests no hypothesis about the results; those are answered later on the
measurement sources, with the parameters chosen here held fixed.

Follows Ropke & Pisinger's own tuning procedure (2006, section 4.3.2): start from a
working setting, let one parameter take several values while the rest stay fixed, keep the
winner, and move on to the next parameter *using the values found so far*. Sequential, not
independent - later parameters are tuned against earlier winners.

Three rules, each of which was got wrong on the first attempt:

  1. The tuning set is fixed for the whole run, or a later parameter's winner is not
     comparable to an earlier one's.
  2. Cells are chosen by structure, never by outcome. Picking sources because ALNS did
     badly on them tunes the parameters toward one regime and imports a result into the
     calibration.
  3. Within a cell the cheaper source is taken - a cost decision, not an outcome one, and
     R&P do the same ("the tuning instances must have a fairly limited size").

Budget limits: one seed where R&P use five, so only large effects clear the tie-break
variance, and eight tuning cells. Hence the decision rule - a default changes only on a
clear margin.
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

MIN_RELATIVE_GAIN = 0.02  # at one seed, less than this is not distinguishable from noise

# Budget per source. The first attempt used k=3 everywhere, which was worthless: at k=3
# the q bounds collapse to (1,1), so destroy removes one edge and repair puts one back,
# and from a fixed warm start every parameter setting walked to the same cut on 6 of 8
# cells - identical sigma to four decimals. Parameters cannot express a difference in a
# 1-swap. k=10 gives q in (1,4); k must stay below out(s), so small-out sources get the
# largest budget they can support. Kept in the results as a finding: at 1-swap budgets,
# ALNS parameter choice is irrelevant.
def tuning_k(out_degree: int) -> int:
    return min(10, out_degree - 1)

# Swept in this order, most-ours-first: a parameter R&P never had is a weaker inherited
# default than one they published a tuned value for.
SWEEP = [
    ("repair_p", [ALNS_REPAIR_P, 20, 60]),        # no R&P analogue at all
    ("max_hop_scope", [ALNS_MAX_HOP_SCOPE, 1]),   # ours; current value inherited untested
    ("q_max_frac", [ALNS_Q_MAX_FRAC, 0.7]),       # adapted from R&P's xi=0.4
    # Tested downward: cheaper, and fewer iterations previously scored better in-sample
    # and worse out-of-sample, which is the direction worth measuring.
    ("max_iter", [ALNS_MAX_ITER, 150]),
]


def tuning_cells(sample: pd.DataFrame) -> list:
    """One source per (out-degree band x reach class) cell, cheapest member of each."""
    calib = sample[sample.role == "calibration"]
    picks = calib.loc[calib.groupby("cell").sigma0_saa.idxmin()]
    return [(int(r.source), tuning_k(int(r.out_degree)), float(r.sigma0_saa), r.cell)
            for _, r in picks.sort_values("sigma0_saa").iterrows()]


def main():
    started = time.time()
    sample = pd.read_csv(DATA_DIR / "sample.csv")
    cells = tuning_cells(sample)

    per_pass = sum(predicted_seconds(s) for _, _, s, _ in cells)
    units = sum(sum(v / ALNS_MAX_ITER if name == "max_iter" else 1.0
                    for v in values[1:]) for name, values in SWEEP) + 1
    print(f"tuning set: {len(cells)} cells, one per (out-band x reach) cell")
    for source, k, sigma0, cell in cells:
        print(f"  {cell:<28} source {source:>5}  k={k:<3} sigma0 {sigma0:>6.1f}  "
              f"~{predicted_seconds(sigma0):>5.1f}s")
    print(f"\none pass over the set ~{per_pass:.0f}s; "
          f"{units:.1f} passes planned ~{per_pass * units:.0f}s "
          f"against a {CALIBRATION_BUDGET_SECONDS}s budget\n")

    bench = Workbench()
    print(f"workbench ready in {time.time() - started:.0f}s\n")

    rows, chosen = [], {}

    def evaluate(tag: str, params: dict, with_baselines: bool) -> float:
        """One pass over the tuning set; returns median R_mc, the deciding metric.

        Median, not mean: R is skewed across sources and a couple of saturated cells near
        R=0 would drag a mean around."""
        produced = []
        for source, k, _, _ in cells:
            if time.time() - started > CALIBRATION_BUDGET_SECONDS:
                print(f"    ! budget exhausted, stopping at source {source}")
                break
            ev_saa, ev_mc = bench.evaluators(source)
            produced += run_cell(bench.context(source), k, ev_saa, ev_mc,
                                 seeds=(ALNS_RUN_SEED,), alns_params=params,
                                 baselines=with_baselines, tag=tag)
        rows.extend(produced)
        alns = [r for r in produced if r["method"] == "alns"]
        return pd.Series([r["R_mc"] for r in alns]).median() if alns else float("nan")

    # The reference every sweep is measured against. Baselines run once, here: they do not
    # depend on ALNS parameters, so repeating them per setting would burn budget on
    # identical numbers.
    print("baseline setting (current config defaults)")
    t = time.time()
    reference = evaluate("default", {}, with_baselines=True)
    print(f"  median R_mc {reference:.4f}   {time.time() - t:.0f}s\n")

    for name, values in SWEEP:
        print(f"sweeping {name} (carrying {chosen or 'defaults'})")
        results = {values[0]: reference}
        for value in values[1:]:
            if time.time() - started > CALIBRATION_BUDGET_SECONDS:
                print("  ! budget exhausted, sweep stopped")
                break
            t = time.time()
            results[value] = evaluate(f"{name}={value}", {**chosen, name: value},
                                      with_baselines=False)
            print(f"  {name}={value:<6} median R_mc {results[value]:.4f}   "
                  f"{time.time() - t:.0f}s")

        best = max(results, key=lambda v: results[v])
        gain = (results[best] - reference) / max(abs(reference), 1e-9)
        if best != values[0] and gain > MIN_RELATIVE_GAIN:
            chosen[name] = best
            reference = results[best]
            print(f"  -> adopt {name}={best} ({gain:+.1%}), carried forward\n")
        else:
            print(f"  -> keep {name}={values[0]} "
                  f"(best alternative {gain:+.1%}, under the {MIN_RELATIVE_GAIN:.0%} "
                  f"margin needed at one seed)\n")

    frame = write_rows(rows, "calibration.csv")
    print(f"total {time.time() - started:.0f}s of {CALIBRATION_BUDGET_SECONDS}s\n")

    print("=" * 70)
    print("CALIBRATED DEFAULTS")
    if chosen:
        for name, value in chosen.items():
            print(f"  {name}: change to {value}")
        print("\n  Single seed, so confirm across seeds before editing config.py.")
    else:
        print("  No parameter cleared the margin - keep every current default.")

    alns = frame[frame.method == "alns"]
    print(f"\n  median SAA-MC gap {alns.saa_mc_gap.median():+.4f} "
          f"(positive = the cut looked better in-sample than it was)")
    return frame


if __name__ == "__main__":
    main()
