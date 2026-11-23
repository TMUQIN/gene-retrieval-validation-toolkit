"""Ranking metrics and locus-cluster bootstrap for caller-supplied scores.

Callers manage data permissions and any required evaluation authorization.
These functions do not invoke the optional authorization helper automatically.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from math import log2
from statistics import NormalDist, mean
from typing import Any, Iterable, Mapping, Sequence

import numpy as np


@dataclass(frozen=True)
class QueryMetrics:
    query_id: str
    unified_locus_id: str
    method_id: str
    eligible: bool
    abstention_reason: str
    first_true_rank: int | None
    reciprocal_rank: float | None
    recall_at_1: float | None
    recall_at_5: float | None
    recall_at_10: float | None
    ndcg: float | None


def rank_complete_queries(
    score_rows: Iterable[Mapping[str, Any]],
    expected_candidates: Mapping[str, set[str]],
    *,
    expected_methods: Iterable[str] | None = None,
) -> tuple[dict[tuple[str, str], list[str]], dict[tuple[str, str], str]]:
    """Rank complete query/method score blocks with a frozen stable tie break."""
    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in score_rows:
        grouped[(str(row["query_id"]), str(row["method_id"]))].append(row)

    if expected_methods is None:
        keys = set(grouped)
    else:
        methods = {str(method) for method in expected_methods}
        keys = set(grouped) | {
            (str(query_id), method)
            for query_id in expected_candidates
            for method in methods
        }
    rankings: dict[tuple[str, str], list[str]] = {}
    abstentions: dict[tuple[str, str], str] = {}
    for key in sorted(keys):
        rows = grouped.get(key, [])
        query_id, _ = key
        expected = expected_candidates.get(query_id, set())
        if not rows:
            abstentions[key] = "MISSING_SCORE_BLOCK"
            continue
        observed = {str(row["candidate_gene_id"]) for row in rows}
        if not expected or observed != expected:
            abstentions[key] = "INCOMPLETE_CANDIDATE_SUPPORT"
            continue
        ineligible = [row for row in rows if str(row["eligibility_status"]) != "ELIGIBLE"]
        if ineligible:
            reasons = sorted({str(row["abstention_reason"]) for row in ineligible})
            abstentions[key] = ";".join(reasons) or "ABSTAIN"
            continue
        ordered = sorted(
            rows,
            key=lambda row: (-float(row["score"]), str(row["candidate_gene_id"])),
        )
        rankings[key] = [str(row["candidate_gene_id"]) for row in ordered]
    return rankings, abstentions


def _dcg(binary_relevance: Sequence[int]) -> float:
    return sum(rel / log2(rank + 1) for rank, rel in enumerate(binary_relevance, start=1))


def evaluate_rankings(
    rankings: Mapping[tuple[str, str], Sequence[str]],
    abstentions: Mapping[tuple[str, str], str],
    truth_by_query: Mapping[str, set[str]],
    locus_by_query: Mapping[str, str],
    *,
    coverage_only_queries: set[str] | None = None,
) -> list[QueryMetrics]:
    """Evaluate first-true-gene ranking with explicit multi-truth semantics."""
    keys = sorted(set(rankings) | set(abstentions))
    results: list[QueryMetrics] = []
    for query_id, method_id in keys:
        locus_id = locus_by_query[query_id]
        if (query_id, method_id) in abstentions:
            results.append(
                QueryMetrics(
                    query_id,
                    locus_id,
                    method_id,
                    False,
                    abstentions[(query_id, method_id)],
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                )
            )
            continue
        ranked = list(rankings[(query_id, method_id)])
        if coverage_only_queries and query_id in coverage_only_queries:
            results.append(
                QueryMetrics(
                    query_id,
                    locus_id,
                    method_id,
                    False,
                    "CANDIDATE_SET_SINGLETON_COVERAGE_ONLY",
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                )
            )
            continue
        truth = truth_by_query.get(query_id, set())
        true_ranks = [rank for rank, gene in enumerate(ranked, start=1) if gene in truth]
        if not true_ranks:
            results.append(
                QueryMetrics(
                    query_id,
                    locus_id,
                    method_id,
                    False,
                    "TRUTH_NOT_IN_CANDIDATE_UNIVERSE",
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                )
            )
            continue
        first = min(true_ranks)
        relevance = [1 if gene in truth else 0 for gene in ranked]
        # The ideal denominator contains every accepted truth relation, not
        # only truth genes recovered in the candidate ranking.  This keeps
        # multi-truth NDCG faithful to the frozen binary-relevance contract.
        ideal_relevant = min(len(truth), len(ranked))
        ideal = [1] * ideal_relevant + [0] * (len(ranked) - ideal_relevant)
        results.append(
            QueryMetrics(
                query_id,
                locus_id,
                method_id,
                True,
                "",
                first,
                1.0 / first,
                float(first <= 1),
                float(first <= 5),
                float(first <= 10),
                _dcg(relevance) / _dcg(ideal),
            )
        )
    return results


def common_support(
    rows: Iterable[QueryMetrics],
    method_a: str,
    method_b: str,
    strict_queries: set[str] | None = None,
) -> list[tuple[str, str, float, float]]:
    """Return paired query metrics on all or strictly independent common support."""
    by_key = {(row.query_id, row.method_id): row for row in rows}
    query_ids = sorted({row.query_id for row in rows})
    paired: list[tuple[str, str, float, float]] = []
    for query_id in query_ids:
        if strict_queries is not None and query_id not in strict_queries:
            continue
        a = by_key.get((query_id, method_a))
        b = by_key.get((query_id, method_b))
        if not a or not b or not a.eligible or not b.eligible:
            continue
        assert a.reciprocal_rank is not None and b.reciprocal_rank is not None
        if a.unified_locus_id != b.unified_locus_id:
            raise ValueError(f"locus mismatch for query {query_id}")
        paired.append((query_id, a.unified_locus_id, a.reciprocal_rank, b.reciprocal_rank))
    return paired


def _quantile(values: np.ndarray, probability: float) -> float:
    return float(np.quantile(values, probability, method="linear"))


def paired_cluster_bootstrap(
    paired_rows: Sequence[tuple[str, str, float, float]],
    *,
    n_replicates: int,
    seed: int,
    confidence: float = 0.95,
) -> dict[str, Any]:
    """Bias-corrected paired delta MRR CI with locus-level resampling."""
    if not paired_rows:
        raise ValueError("paired common support is empty")
    if n_replicates < 2:
        raise ValueError("n_replicates must be at least 2")
    by_locus: dict[str, list[float]] = defaultdict(list)
    for _, locus_id, method_a_rr, method_b_rr in paired_rows:
        by_locus[locus_id].append(float(method_a_rr) - float(method_b_rr))
    loci = sorted(by_locus)
    observed = mean(delta for deltas in by_locus.values() for delta in deltas)
    rng = np.random.default_rng(seed)
    replicates = np.empty(n_replicates, dtype=float)
    for index in range(n_replicates):
        sampled = rng.choice(loci, size=len(loci), replace=True)
        values = [delta for locus_id in sampled for delta in by_locus[str(locus_id)]]
        replicates[index] = float(np.mean(values))

    normal = NormalDist()
    lower_alpha = (1.0 - confidence) / 2.0
    upper_alpha = 1.0 - lower_alpha
    proportion_less = float(np.mean(replicates < observed))
    epsilon = 0.5 / n_replicates
    proportion_less = min(max(proportion_less, epsilon), 1.0 - epsilon)
    z0 = normal.inv_cdf(proportion_less)
    adjusted_lower = normal.cdf(2.0 * z0 + normal.inv_cdf(lower_alpha))
    adjusted_upper = normal.cdf(2.0 * z0 + normal.inv_cdf(upper_alpha))
    ci_low = _quantile(replicates, adjusted_lower)
    ci_high = _quantile(replicates, adjusted_upper)
    return {
        "delta_mrr": observed,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "confidence": confidence,
        "ci_type": "BIAS_CORRECTED_NOT_BCA",
        "n_replicates": n_replicates,
        "seed": seed,
        "n_queries": len(paired_rows),
        "n_loci": len(loci),
        "replicates": replicates,
    }
