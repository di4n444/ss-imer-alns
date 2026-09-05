"""Orchestration: one CSV row per (source, k, method) run.

The schema rule comes from a bug this project has
already paid for once: `best_peer_mc = min([alns_mc, *baselines])` put ALNS into the pool
it was being judged against, so the column could never show ALNS losing — it read equal to
ALNS on 25 of 40 rows while ALNS was strictly best on only 11. So: **one row per method,
never a column that pools a method with its own competitors.** "Best fixed baseline" and
"oracle" are `groupby` operations performed after measurement, not columns written during
it.

Each row also carries every resolved ALNS parameter, so a calibration variant is identifiable from the row alone
and can never be mistaken for a default run.

Both sigmas are always recorded. SAA is what the search optimised; MC is what gets
reported. They have been measured disagreeing — a cut that wins in-sample and
loses out-of-sample — so writing only one of them would hide the overfitting rather than
measure it.
"""

import time

import pandas as pd

import create_graph
import create_subgraphs
import heuristics
from alns_optimizer import run_alns
from config import DATA_DIR
from evaluator import Evaluator
from greedy_baseline import run_greedy
from heuristics import HEURISTICS
from source_context import build_source_context


def _row(result, ctx, k, sigma0_saa, sigma0_mc, elapsed, tag) -> dict:
    saa, mc = result["best_reach_saa"], result["best_reach_mc"]
    row = {
        "tag": tag,
        "source": ctx.source,
        "out_degree": ctx.out_degree,
        "k": k,
        "method": result["method"],
        "seed": result.get("seed"),
        "sigma0_saa": sigma0_saa,
        "sigma0_mc": sigma0_mc,
        "sigma_saa": saa,
        "sigma_mc": mc,
        "R_saa": 1 - saa / sigma0_saa,
        "R_mc": 1 - mc / sigma0_mc,
        # SAA minus MC on the same cut: positive means the cut looked better in-sample
        # than it turned out to be: overfitting to the in-sample scenarios.
        "saa_mc_gap": (1 - saa / sigma0_saa) - (1 - mc / sigma0_mc),
        "cut_size": len(result["best_cut"]),
        "hop_mix": repr(dict(sorted(result["hop_mix"].items()))),
        "stop_reason": result["stop_reason"],
        "seconds": round(elapsed, 2),
    }
    for key in ("iterations_done", "last_improvement", "improvement_share",
                "evaluations", "scope_weights", "repair_weights",
                "destroy_weights", "best_hits_by_heuristic", "best_hits_by_hop",
                "best_hits_by_scope", "scope_selected", "neutral_moves", "fallback_used",
                "layer_sizes", "q_bounds",
                # baseline-side diagnostics: how large the tied group at the cutoff was,
                # and how it split, which is where the tie-break rule rather than the
                # criterion decided the cut
                "candidates", "tie_split_at_cutoff", "tie_group_sizes"):
        if key in result:
            row[key] = repr(result[key]) if isinstance(result[key], (dict, tuple, list)) \
                else result[key]
    row.update({f"param_{name}": value
                for name, value in result.get("params", {}).items()})
    return row


def run_cell(ctx, k: int, ev_saa, ev_mc, *, seeds=(7,), alns_params=None,
             baselines=True, tag="") -> list:
    """Every method on one (source, k), as a list of rows.

    One evaluator per scenario set is reused across every method and budget — safe since
    the cache is keyed by (source, cut) — because building the scenario sets is the
    expensive part, not evaluating against them.

    Deterministic baselines are computed once regardless of how many ALNS seeds are run
; only `random` and ALNS vary with the seed.
    """
    endpoints = ctx.endpoints
    sigma0_saa = ev_saa.evaluate_reach(ctx.source, frozenset(), endpoints)
    sigma0_mc = ev_mc.evaluate_reach(ctx.source, frozenset(), endpoints)
    rows = []

    if baselines:
        for name in HEURISTICS:
            # `random` is the one baseline whose result depends on the seed, so it is the
            # only one run per seed.
            for seed in (seeds if name == "random" else seeds[:1]):
                started = time.time()
                result = run_greedy(ctx, name, k, ev_saa, seed=seed)
                result["best_reach_mc"] = ev_mc.evaluate_reach(
                    ctx.source, result["best_cut"], endpoints)
                rows.append(_row(result, ctx, k, sigma0_saa, sigma0_mc,
                                 time.time() - started, tag))

    for seed in seeds:
        started = time.time()
        result = run_alns(ctx, k, ev_saa, seed, **(alns_params or {}))
        result["method"], result["seed"] = "alns", seed
        result["best_reach_mc"] = ev_mc.evaluate_reach(
            ctx.source, result["best_cut"], endpoints)
        rows.append(_row(result, ctx, k, sigma0_saa, sigma0_mc,
                         time.time() - started, tag))
    return rows


class Workbench:
    """Graph, scenario sets and per-source contexts, built once and reused.

    Setup dominates a short run (two scenario sets and a SourceContext per source), so
    every driver shares this rather than rebuilding. Contexts are cached per source since
    a source appears at several budgets.
    """

    def __init__(self):
        self.g = create_graph.build_graph()
        self.saa = create_subgraphs.build_saa_scenarios(self.g)
        self.mc = create_subgraphs.build_mc_scenarios(self.g)
        self.features = heuristics.load_global_features()
        self._contexts, self._evaluators = {}, {}

    def context(self, source: int):
        if source not in self._contexts:
            self._contexts[source] = build_source_context(self.g, source, self.features)
        return self._contexts[source]

    def evaluators(self, source: int):
        """One SAA and one MC evaluator per source. Separate objects by construction, so
        the search can never be handed the out-of-sample set."""
        if source not in self._evaluators:
            self._evaluators[source] = (Evaluator(self.g.vcount(), self.saa),
                                        Evaluator(self.g.vcount(), self.mc))
        return self._evaluators[source]


def write_rows(rows: list, filename: str) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    frame.to_csv(DATA_DIR / filename, index=False)
    print(f"wrote {len(frame)} rows to data/{filename}")
    return frame


if __name__ == "__main__":
    # Schema check: one source/k, every method,
    # confirming the row schema is complete and stable before any real sweep uses it.
    bench = Workbench()
    sample = pd.read_csv(DATA_DIR / "sample.csv")
    probe = sample[sample.role == "calibration"].nsmallest(1, "sigma0_saa").iloc[0]
    ctx = bench.context(int(probe.source))
    ev_saa, ev_mc = bench.evaluators(int(probe.source))

    rows = run_cell(ctx, 3, ev_saa, ev_mc, seeds=(7,), tag="schema-check")
    frame = write_rows(rows, "schema_check.csv")
    print(f"\nsource {probe.source} (out={ctx.out_degree}, sigma0={probe.sigma0_saa:.1f}), k=3")
    print(frame[["method", "sigma_saa", "sigma_mc", "R_mc", "cut_size", "hop_mix",
                 "stop_reason"]].to_string(index=False))
    missing = [c for c in frame.columns if frame[c].isna().all()]
    print(f"\n{len(frame.columns)} columns; all-empty: {missing or 'none'}")
