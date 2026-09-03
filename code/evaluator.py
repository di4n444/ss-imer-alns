"""Masked-BFS reach evaluation over a frozen scenario set, given a candidate cut D.
Does not generate scenarios (create_subgraphs.py). One function, `evaluate_reach`,
used for both SAA (in-sample, inside the ALNS search loop) and OOS (out-of-sample,
final validation only) — the separation between the two is structural: which
scenario array a caller passes in and holds a reference to (REPORT.md §1/§7), not
two copies of this logic. The ALNS loop must only ever be given `saa_scenarios`;
final validation must only ever be given `mc_scenarios` — never both.

Optional `cache` reuses the same dict the ALNS loop already needs for R&P's
visited-solution tracking (only reward unvisited solutions, REPORT.md §6a) — so a
revisited D is a dict lookup instead of a repeat 500-scenario BFS sweep. Passing no
cache still works (plain compute), so this stays testable on its own.
"""

import collections


def _bfs_reach(source: int, base_adj: list, occupied_mask, D: frozenset) -> int:
    """Reach from `source` using only edges that are occupied in this scenario AND
    not in D. Never mutates `base_adj` or `occupied_mask`."""
    seen = {source}
    queue = collections.deque([source])
    while queue:
        v = queue.popleft()
        for w, eid in base_adj[v]:
            if not occupied_mask[eid] or eid in D:
                continue
            if w not in seen:
                seen.add(w)
                queue.append(w)
    return len(seen)


def evaluate_reach(source: int, D, base_adj: list, scenarios, cache: dict = None) -> float:
    """Mean reach across `scenarios` (boolean occupancy array, shape (n, M)).

    `cache`, if given, is keyed by frozenset(D) -> fitness. Caller owns the dict (and
    must use a separate one per scenario set — a SAA-evaluated D and an
    MC-evaluated D are different numbers, never share a cache between the two).
    """
    D = D if isinstance(D, frozenset) else frozenset(D)
    if cache is not None and D in cache:
        return cache[D]
    value = sum(_bfs_reach(source, base_adj, mask, D) for mask in scenarios) / len(scenarios)
    if cache is not None:
        cache[D] = value
    return value
