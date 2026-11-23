from __future__ import annotations

import pytest

from gene_retrieval.harmonization.contracts import ContractError, validate_candidate_rows, validate_score_rows, validate_truth_rows


def candidate_rows() -> list[dict[str, object]]:
    base = {
        "dataset_id": "SYNTHETIC",
        "query_id": "Q1",
        "unified_locus_id": "L1",
        "unit_type": "VARIANT",
        "chromosome": "chr1",
        "start_1based": 100,
        "end_1based": 100,
        "ref_allele": "A",
        "alt_allele": "G",
        "candidate_set_size": 2,
        "genome_build": "GRCh38",
        "provenance_id": "SYNTHETIC_V1",
    }
    return [
        {**base, "candidate_gene_id": "ENSG000001"},
        {**base, "candidate_gene_id": "ENSG000002"},
    ]


def test_candidate_contract_accepts_grch38_complete_set() -> None:
    summary = validate_candidate_rows(candidate_rows())
    assert summary.rows == 2
    assert summary.queries == 1
    assert summary.loci == 1


def test_candidate_contract_rejects_truth_contact_and_size_mismatch() -> None:
    rows = candidate_rows()
    rows[1]["is_truth"] = True
    with pytest.raises(ContractError, match="row 2.*truth/outcome"):
        validate_candidate_rows(rows)
    rows = candidate_rows()[:-1]
    with pytest.raises(ContractError, match="declares 2 candidates"):
        validate_candidate_rows(rows)


def test_truth_contract_accepts_multiple_true_genes() -> None:
    rows = [
        {
            "dataset_id": "SYNTHETIC",
            "query_id": "Q1",
            "truth_gene_id": gene,
            "truth_type": "CRE_GENE_PERTURBATION",
            "truth_source_id": "SYNTHETIC_SOURCE",
            "source_collision_class": "INDEPENDENT",
            "provenance_id": "SYNTHETIC_V1",
        }
        for gene in ("ENSG000001", "ENSG000002")
    ]
    assert validate_truth_rows(rows).rows == 2


def test_score_contract_keeps_missingness_out_of_numeric_scores() -> None:
    eligible = {
        "dataset_id": "SYNTHETIC",
        "query_id": "Q1",
        "candidate_gene_id": "ENSG000001",
        "method_id": "SYNTHETIC_DISTANCE",
        "score": -10.0,
        "score_direction": "HIGHER_IS_BETTER",
        "eligibility_status": "ELIGIBLE",
        "abstention_reason": "",
        "provenance_id": "SYNTHETIC_V1",
    }
    missing = {
        **eligible,
        "candidate_gene_id": "ENSG000002",
        "score": "",
        "eligibility_status": "MISSING_SCORE",
        "abstention_reason": "NO_RELEASED_SCORE",
    }
    assert validate_score_rows([eligible, missing]).rows == 2
    missing["score"] = 0.0
    with pytest.raises(ContractError, match="must have empty score"):
        validate_score_rows([eligible, missing])
