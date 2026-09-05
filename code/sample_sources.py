"""Draw the one source sample -> data/sample.csv.

The rule this file exists to enforce: **one sample, one seed,
calibration disjoint from measurement**. The pilot audit found three different samples in
circulation and could no longer say which reported number came from which. So there is
exactly one function here, it is seeded from config, and it writes one file.

Stratification is on (out-degree band x reach class), both measured from
data/source_profile.csv rather than assumed:

  - Reach is required as a stratifying variable, because topologically
    distinct nodes turned out to have identical cascade reach - they land in the same
    live-edge SCC. Centrality alone is not a proxy for it.
  - Out-degree is kept as the second axis because it *is* the hop0 candidate pool, so it
    decides both what k can be studied and how hard the search is, and
    because it predicts reach strongly but not deterministically: 5% of out<4 sources are
    saturated, against 99% of out>=50 ones. The off-diagonal cells - few edges out of s,
    but they reach the giant component - are exactly the redundant-fan-out geometry the
    Level-2 question is about.

Sources with out-degree < 4 are excluded: k >= out(s) is the trivial isolated case
, so they cannot support even the smallest budget studied. That is 2088 of
3272 eligible nodes, which is a finding to report rather than a filter to hide.

`predicted_seconds` is carried per source so an experiment plan can be costed *before* it
is run - runtime tracks sigma_0, not source count, so a set's cost is
decided by its reach composition.
"""

import pandas as pd

from config import (
    CALIBRATION_COST_INTERCEPT,
    CALIBRATION_COST_PER_SIGMA0,
    DATA_DIR,
    SAMPLE_CALIBRATION_PER_CELL,
    SAMPLE_MEASUREMENT_PER_CELL,
    SAMPLE_MIN_OUT_DEGREE,
    SAMPLE_OUT_DEGREE_BANDS,
    SAMPLE_SATURATED_SIGMA0,
    SOURCE_SAMPLE_SEED,
)


def predicted_seconds(sigma0: float, iterations: int = 300) -> float:
    """Estimated ALNS runtime. Linear in sigma_0 and in the
    iteration budget. Used only for planning; drivers measure the real thing."""
    per_300 = max(1.0, CALIBRATION_COST_PER_SIGMA0 * sigma0 + CALIBRATION_COST_INTERCEPT)
    return per_300 * iterations / 300


def _cell(row) -> str:
    for lo, hi in SAMPLE_OUT_DEGREE_BANDS:
        if lo <= row.out_degree < hi:
            band = f"out[{lo},{hi if hi < 10**9 else '+'})"
            break
    else:
        return None
    reach = "saturated" if row.sigma0_saa >= SAMPLE_SATURATED_SIGMA0 else "low-reach"
    return f"{band} {reach}"


def draw_sample(profile: pd.DataFrame) -> pd.DataFrame:
    """Stratified draw, calibration first then measurement from what is left, so the two
    can never overlap by construction rather than by discipline."""
    eligible = profile[profile.out_degree >= SAMPLE_MIN_OUT_DEGREE].copy()
    eligible["cell"] = eligible.apply(_cell, axis=1)
    eligible = eligible[eligible.cell.notna()]

    rows = []
    for cell, members in sorted(eligible.groupby("cell"), key=lambda kv: kv[0]):
        wanted = SAMPLE_CALIBRATION_PER_CELL + SAMPLE_MEASUREMENT_PER_CELL
        if len(members) < wanted:
            # Too thin to sample both roles: report it rather than silently short-drawing.
            print(f"  ! {cell}: only {len(members)} sources, need {wanted} - "
                  f"taking calibration first, measurement gets the remainder")
        drawn = members.sample(n=min(wanted, len(members)),
                               random_state=SOURCE_SAMPLE_SEED)
        for i, (_, row) in enumerate(drawn.iterrows()):
            rows.append({
                "source": int(row.source),
                "snap_id": int(row.snap_id),
                "role": "calibration" if i < SAMPLE_CALIBRATION_PER_CELL else "measurement",
                "cell": cell,
                "out_degree": int(row.out_degree),
                "sigma0_saa": float(row.sigma0_saa),
                "reachable": int(row.reachable),
                "predicted_seconds": round(predicted_seconds(row.sigma0_saa), 1),
            })
    return pd.DataFrame(rows).sort_values(["role", "cell", "source"]).reset_index(drop=True)


if __name__ == "__main__":
    profile = pd.read_csv(DATA_DIR / "source_profile.csv")
    print(f"source_profile.csv: {len(profile)} nodes, "
          f"{(profile.out_degree >= SAMPLE_MIN_OUT_DEGREE).sum()} with out-degree "
          f">= {SAMPLE_MIN_OUT_DEGREE}\n")

    sample = draw_sample(profile)
    sample.to_csv(DATA_DIR / "sample.csv", index=False)
    print(f"\nwrote {len(sample)} sources to data/sample.csv "
          f"(seed {SOURCE_SAMPLE_SEED})\n")

    for role in ("calibration", "measurement"):
        part = sample[sample.role == role]
        print(f"{role}: {len(part)} sources, "
              f"{part.predicted_seconds.sum():.0f}s for one ALNS run each")
        for cell, members in part.groupby("cell"):
            ids = ", ".join(str(s) for s in members.source)
            print(f"  {cell:<28} {ids:<24} "
                  f"sigma0 {members.sigma0_saa.min():>6.1f}-{members.sigma0_saa.max():>6.1f}"
                  f"  ~{members.predicted_seconds.sum():>5.0f}s")
        print()

    overlap = set(sample[sample.role == "calibration"].source) & \
        set(sample[sample.role == "measurement"].source)
    assert not overlap, f"calibration and measurement overlap: {overlap}"
    print("calibration and measurement sets are disjoint")
