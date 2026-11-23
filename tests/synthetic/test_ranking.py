from __future__ import annotations

import numpy as np

from gene_retrieval.evaluation.ranking import common_support, evaluate_rankings, paired_cluster_bootstrap, rank_complete_queries


def score(query: str, locus: str, gene: str, method: str, value: float) -> dict[str, object]:
    return {
        "query_id": query,
        "unified_locus_id": locus,
        "candidate_gene_id": gene,
        "method_id": method,
        "score": value,
        "eligibility_status": "ELIGIBLE",
        "abstention_reason": "",
    }


def test_ties_are_stable_and_multi_truth_uses_first_true_gene() -> None:
    rows = [
        score("Q1", "L1", "ENSG3", "A", 1.0),
        score("Q1", "L1", "ENSG1", "A", 1.0),
        score("Q1", "L1", "ENSG2", "A", 0.5),
    ]
    rankings, abstentions = rank_complete_queries(rows, {"Q1": {"ENSG1", "ENSG2", "ENSG3"}})
    assert rankings[("Q1", "A")] == ["ENSG1", "ENSG3", "ENSG2"]
    metrics = evaluate_rankings(
        rankings,
        abstentions,
        {"Q1": {"ENSG2", "ENSG3"}},
        {"Q1": "L1"},
    )[0]
    assert metrics.first_true_rank == 2
    assert metrics.reciprocal_rank == 0.5
    assert metrics.recall_at_1 == 0.0
    assert 0.0 < metrics.ndcg < 1.0


def test_incomplete_or_missing_candidate_score_abstains_whole_query() -> None:
    rows = [score("Q1", "L1", "G1", "A", 2.0)]
    rankings, abstentions = rank_complete_queries(rows, {"Q1": {"G1", "G2"}})
    assert not rankings
    assert abstentions[("Q1", "A")] == "INCOMPLETE_CANDIDATE_SUPPORT"

    rows = [
        score("Q1", "L1", "G1", "A", 2.0),
        {
            **score("Q1", "L1", "G2", "A", 0.0),
            "score": "",
            "eligibility_status": "MISSING_SCORE",
            "abstention_reason": "NO_SCORE",
        },
    ]
    rankings, abstentions = rank_complete_queries(rows, {"Q1": {"G1", "G2"}})
    assert not rankings
    assert abstentions[("Q1", "A")] == "NO_SCORE"


def test_common_support_has_explicit_strict_source_layer() -> None:
    rows = []
    for query, locus, truth in (("Q1", "L1", "G1"), ("Q2", "L2", "G2")):
        score_rows = [
            score(query, locus, "G1", "A", 2.0),
            score(query, locus, "G2", "A", 1.0),
            score(query, locus, "G1", "B", 1.0),
            score(query, locus, "G2", "B", 2.0),
        ]
        rankings, abstentions = rank_complete_queries(score_rows, {query: {"G1", "G2"}})
        rows.extend(evaluate_rankings(rankings, abstentions, {query: {truth}}, {query: locus}))
    assert len(common_support(rows, "A", "B")) == 2
    strict = common_support(rows, "A", "B", strict_queries={"Q2"})
    assert [row[0] for row in strict] == ["Q2"]


def test_cluster_bootstrap_is_deterministic_and_reports_loci() -> None:
    paired = [
        ("Q1", "L1", 1.0, 0.5),
        ("Q2", "L1", 0.5, 0.25),
        ("Q3", "L2", 0.25, 1.0),
    ]
    first = paired_cluster_bootstrap(paired, n_replicates=200, seed=20260919)
    second = paired_cluster_bootstrap(paired, n_replicates=200, seed=20260919)
    assert first["n_loci"] == 2
    assert first["n_queries"] == 3
    assert first["ci_type"] == "BIAS_CORRECTED_NOT_BCA"
    assert np.array_equal(first["replicates"], second["replicates"])
    assert first["delta_mrr"] == 0.0

