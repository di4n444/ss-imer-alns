"""When does the search stop improving? -> data/iteration_probe.csv

Evidence for one claim only: that whether 300 iterations is enough can be *observed* per
run rather than guessed in advance, which is the chapter 8 upgrade argued in REPORT §7b.

Deliberately a separate script that changes nothing in the search. `run_alns` already
returns a per-segment `trace` carrying the best reach so far; it is simply never written to
the results CSV. Reading it here needs no instrumentation in the optimizer, so the measured
runs stay exactly the runs the thesis reports.

Resolution is one segment (20 iterations), which is ample: the question is whether the
final improvement landed early or at the very end, not which iteration precisely.
"""

import pandas as pd

from alns_optimizer import run_alns
from config import ALNS_MAX_ITER, ALNS_RUN_SEED, DATA_DIR
from run_experiment import Workbench

# A spread of outcomes from the main run, so the measure is seen against cells that did
# well and cells that did badly - not a single regime.
CELLS = [(96, 10), (123, 20), (201, 10), (421, 3), (145, 15)]


def improvement_point(trace, max_iter, segment_length):
    """Iteration of the last segment that improved on everything before it, and that as a
    fraction of the run. Near 0: converged early. Near 1: still improving when cut off."""
    last = 0
    best = float("inf")
    for entry in trace:
        if entry["best_reach"] < best - 1e-12:
            best = entry["best_reach"]
            last = entry["segment"] * segment_length
    return last, last / max_iter


def main():
    bench = Workbench()
    results = pd.read_csv(DATA_DIR / "results.csv")
    rows = []

    for source, k in CELLS:
        # The SAA evaluator, since that is what the search optimises against; the
        # out-of-sample set plays no part in when the search stops improving.
        ev_saa, _ = bench.evaluators(source)
        outcome = run_alns(bench.context(source), k, ev_saa, ALNS_RUN_SEED)
        last, share = improvement_point(outcome["trace"], ALNS_MAX_ITER,
                                        outcome["params"]["segment_length"])
        stored = results[(results.source == source) & (results.k == k)
                         & (results.method == "alns")]
        rows.append({
            "source": source,
            "k": k,
            "last_improvement_iteration": last,
            "improvement_share": round(share, 3),
            "R_mc_at_300": round(float(stored.R_mc.iloc[0]), 4) if len(stored) else None,
        })
        print(f"source {source:>5} k={k:<3} last improvement at iteration {last:>3} "
              f"of {ALNS_MAX_ITER}  share {share:.2f}")

    frame = pd.DataFrame(rows)
    frame.to_csv(DATA_DIR / "iteration_probe.csv", index=False)
    print(f"\nwrote {len(frame)} rows to data/iteration_probe.csv")
    return frame


if __name__ == "__main__":
    main()
