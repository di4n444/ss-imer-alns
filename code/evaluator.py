"""Reach evaluation over a frozen scenario set, given a candidate cut D.

Does not generate scenarios (create_subgraphs.py). One `Evaluator` is bound to exactly
one scenario set for its whole life — that object *is* the SAA/OOS boundary
(REPORT.md §1/§7): the ALNS loop only ever holds an SAA-bound evaluator, final
validation only ever an MC-bound one, so the search objective can never accidentally
be computed against out-of-sample data.

This is the hot path — profiling put ~92% of a run inside `_mark_reach` — so four
implementation choices are deliberate, each measured or inherited from a prior lesson:

1. The cut is applied through a reusable list indexed by node id, not a dict keyed by
   tail. D touches at most k tails but a traversal probes every node it pops (~135M
   probes per run), and a list index skips the hashing a dict lookup pays.
2. Visited-marking uses a reusable stamp array rather than a fresh `set()` per
   traversal: no per-call allocation, no hashing, and no O(N) reset — just bump an
   integer (PILOT_TESTS.md §24).
3. `edge_id` never appears in the traversal at all. Bitcoin Alpha has no multi-edges
   (deduplicated at load, config.DUPLICATE_EDGE_POLICY), so (tail, head) identifies an
   edge and only the k-element cut needs translating per call.
4. `marginal_values` computes all |D| marginal contributions in ONE pass per scenario
   rather than |D|+1 full sweeps — measured at 1.0x the cost of a single evaluation
   instead of 21x for k=20, and verified to match the naive computation exactly.
"""


class Evaluator:
    def __init__(self, n_nodes: int, scenarios: list, use_cache: bool = True):
        self.scenarios = scenarios
        self._seen = [0] * n_nodes        # visited stamps, main traversal
        self._seen_extra = [0] * n_nodes  # visited stamps, incremental probes
        self._blocked = [None] * n_nodes  # tail -> set(cut heads), reused across calls
        self._stamp = 0
        self._stamp_extra = 0
        self.cache: dict = {} if use_cache else None
        # Marginal values are a property of a cut, so they cache like reach does.
        self._marginal_cache: dict = {} if use_cache else None

    # -- cut masking ------------------------------------------------------

    def _apply_cut(self, D: frozenset, endpoints: dict) -> list:
        """Write D into the reusable `_blocked` buffer; returns the tails touched so
        they can be cleared again. Always pair with `_clear_cut` in a finally block —
        a stale entry would silently corrupt every later evaluation."""
        blocked = self._blocked
        touched = []
        for eid in D:
            u, v = endpoints[eid]
            heads = blocked[u]
            if heads is None:
                heads = blocked[u] = set()
                touched.append(u)
            heads.add(v)
        return touched

    def _clear_cut(self, touched: list) -> None:
        blocked = self._blocked
        for u in touched:
            blocked[u] = None

    # -- core traversal ---------------------------------------------------

    def _mark_reach(self, source: int, adj: list) -> tuple:
        """Traverse from `source` over one scenario's occupied-only adjacency, skipping
        (v, w) pairs in the currently applied cut. Leaves the reached set marked in
        `self._seen` with the returned stamp so callers can test membership in O(1).

        Order does not matter — we only need the size of the reachable set — so this
        uses a stack, avoiding deque overhead."""
        self._stamp += 1
        stamp = self._stamp
        seen = self._seen
        blocked = self._blocked
        seen[source] = stamp
        stack = [source]
        count = 1
        while stack:
            v = stack.pop()
            cut_here = blocked[v]
            if cut_here is None:
                # Overwhelmingly the common case: nothing out of this tail is cut, so
                # skip the per-edge membership test entirely.
                for w in adj[v]:
                    if seen[w] != stamp:
                        seen[w] = stamp
                        count += 1
                        stack.append(w)
            else:
                for w in adj[v]:
                    if seen[w] != stamp and w not in cut_here:
                        seen[w] = stamp
                        count += 1
                        stack.append(w)
        return stamp, count

    def _count_new_from(self, start: int, adj: list, stamp: int) -> int:
        """Nodes reachable from `start` that are not already marked with `stamp`,
        still respecting the applied cut. A second stamp array keeps the main reach
        marking intact for the next probe."""
        self._stamp_extra += 1
        s2 = self._stamp_extra
        seen, seen2, blocked = self._seen, self._seen_extra, self._blocked
        seen2[start] = s2
        stack = [start]
        count = 1
        while stack:
            v = stack.pop()
            cut_here = blocked[v]
            for w in adj[v]:
                if seen[w] == stamp or seen2[w] == s2:
                    continue
                if cut_here is not None and w in cut_here:
                    continue
                seen2[w] = s2
                count += 1
                stack.append(w)
        return count

    # -- public API -------------------------------------------------------

    def evaluate_reach(self, source: int, D, endpoints: dict) -> float:
        """Mean reach across this evaluator's bound scenario set."""
        D = D if isinstance(D, frozenset) else frozenset(D)
        cache = self.cache
        # Keyed by (source, cut), never the cut alone: reach is a property of both, and
        # one evaluator is deliberately reusable across sources (the scenario set is the
        # expensive thing to build). Keying on D alone silently returned the previous
        # source's answer - measured at sigma=41.10 for a source whose true sigma is
        # 643.63. Nothing crashes; the number is just wrong. Same bug class as
        # PILOT_TESTS.md §35 D5, one level down.
        key = (source, D)
        if cache is not None:
            hit = cache.get(key)
            if hit is not None:
                return hit

        touched = self._apply_cut(D, endpoints)
        try:
            mark = self._mark_reach  # hoisted: called once per scenario
            total = 0
            for adj in self.scenarios:
                total += mark(source, adj)[1]
        finally:
            self._clear_cut(touched)

        value = total / len(self.scenarios)
        if cache is not None:
            cache[key] = value
        return value

    def marginal_values(self, source: int, D, endpoints: dict) -> tuple:
        """(mean reach with all of D cut, {eid: mean reach gained if that one edge
        alone were restored}).

        Exact, in one pass per scenario rather than |D|+1 sweeps. For a scenario with
        reached set R (all of D cut) and an edge e=(u,v) in D, restoring e alone can
        only add nodes reached *through* e, so the gain is zero unless e survived
        percolation here, its tail u is in R, and its head v is not — and only then is
        any traversal done, exploring strictly new territory."""
        D = D if isinstance(D, frozenset) else frozenset(D)
        key = (source, D)  # see evaluate_reach: never key on the cut alone
        if self._marginal_cache is not None:
            hit = self._marginal_cache.get(key)
            if hit is not None:
                return hit

        pairs = [(eid, *endpoints[eid]) for eid in D]
        seen = self._seen
        gains = {eid: 0 for eid in D}
        base_total = 0

        touched = self._apply_cut(D, endpoints)
        try:
            mark, probe = self._mark_reach, self._count_new_from
            for adj in self.scenarios:
                stamp, count = mark(source, adj)
                base_total += count
                out_sets: dict = {}  # tail -> set(adj[tail]), built at most once each
                for eid, u, v in pairs:
                    if seen[u] != stamp or seen[v] == stamp:
                        continue  # tail unreachable, or head already covered
                    out = out_sets.get(u)
                    if out is None:
                        out = out_sets[u] = set(adj[u])
                    if v in out:  # else: this edge did not survive percolation here
                        gains[eid] += probe(v, adj, stamp)
        finally:
            self._clear_cut(touched)

        n = len(self.scenarios)
        result = (base_total / n, {eid: g / n for eid, g in gains.items()})
        if self.cache is not None:
            self.cache[key] = result[0]  # the base reach is exactly sigma(D)
            self._marginal_cache[key] = result
        return result
