"""Schema validation for candidate, truth, and method-score tables.

This module validates interfaces only. It does not join evaluation truth or compute
scientific outcomes.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Any, Iterable, Mapping


class ContractError(ValueError):
    """Raised when a table violates a candidate, truth or score contract."""


class CollisionClass(str, Enum):
    INDEPENDENT = "INDEPENDENT"
    POTENTIAL_OVERLAP = "POTENTIAL_OVERLAP"
    SAME_SOURCE = "SAME_SOURCE"
    DIRECT_COLLISION = "DIRECT_COLLISION"
    UNKNOWN = "UNKNOWN"


STRICT_ELIGIBLE_COLLISIONS = {CollisionClass.INDEPENDENT.value}
ALLOWED_UNIT_TYPES = {"VARIANT", "CRE"}
ALLOWED_SCORE_STATES = {
    "ELIGIBLE",
    "MISSING_SCORE",
    "OUT_OF_MODEL_SCOPE",
    "CONTRACT_INCOMPATIBLE",
    "ABSTAIN",
}

CANDIDATE_REQUIRED = {
    "dataset_id",
    "query_id",
    "unified_locus_id",
    "unit_type",
    "chromosome",
    "start_1based",
    "end_1based",
    "candidate_gene_id",
    "candidate_set_size",
    "genome_build",
    "provenance_id",
}

TRUTH_REQUIRED = {
    "dataset_id",
    "query_id",
    "truth_gene_id",
    "truth_type",
    "truth_source_id",
    "source_collision_class",
    "provenance_id",
}

SCORE_REQUIRED = {
    "dataset_id",
    "query_id",
    "candidate_gene_id",
    "method_id",
    "score",
    "score_direction",
    "eligibility_status",
    "abstention_reason",
    "provenance_id",
}

FORBIDDEN_PRETRUTH_FIELDS = {
    "truth_gene_id",
    "is_truth",
    "label",
    "outcome",
    "reciprocal_rank",
    "mrr",
    "recall_at_1",
    "ndcg",
}


@dataclass(frozen=True)
class ValidationSummary:
    rows: int
    queries: int
    loci: int | None = None


def _missing(row: Mapping[str, Any], required: set[str]) -> list[str]:
    return sorted(field for field in required if field not in row)


def _nonempty(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def _as_int(value: Any, field: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ContractError(f"{field} must be an integer: {value!r}") from exc
    return parsed


def _assert_no_forbidden_fields(rows: list[Mapping[str, Any]], table_name: str) -> None:
    for index, row in enumerate(rows, start=1):
        overlap = FORBIDDEN_PRETRUTH_FIELDS.intersection(row)
        if overlap:
            raise ContractError(
                f"{table_name} row {index} contains truth/outcome fields before truth access: "
                f"{sorted(overlap)}"
            )


def validate_candidate_rows(rows: Iterable[Mapping[str, Any]]) -> ValidationSummary:
    records = list(rows)
    if not records:
        raise ContractError("candidate table is empty")
    _assert_no_forbidden_fields(records, "candidate table")

    pair_keys: list[tuple[str, str]] = []
    query_sizes: dict[str, int] = {}
    query_loci: dict[str, str] = {}
    for index, row in enumerate(records, start=1):
        missing = _missing(row, CANDIDATE_REQUIRED)
        if missing:
            raise ContractError(f"candidate row {index} missing fields: {missing}")
        if str(row["genome_build"]) != "GRCh38":
            raise ContractError(f"candidate row {index} must use GRCh38")
        if str(row["unit_type"]) not in ALLOWED_UNIT_TYPES:
            raise ContractError(f"candidate row {index} has invalid unit_type")
        if not str(row["chromosome"]).startswith("chr"):
            raise ContractError(f"candidate row {index} chromosome must use chr prefix")
        start = _as_int(row["start_1based"], "start_1based")
        end = _as_int(row["end_1based"], "end_1based")
        size = _as_int(row["candidate_set_size"], "candidate_set_size")
        if start < 1 or end < start or size < 1:
            raise ContractError(f"candidate row {index} has invalid coordinates or size")
        for field in ("dataset_id", "query_id", "unified_locus_id", "candidate_gene_id", "provenance_id"):
            if not _nonempty(row[field]):
                raise ContractError(f"candidate row {index} has empty {field}")
        query_id = str(row["query_id"])
        pair_keys.append((query_id, str(row["candidate_gene_id"])))
        query_sizes.setdefault(query_id, size)
        query_loci.setdefault(query_id, str(row["unified_locus_id"]))
        if query_sizes[query_id] != size:
            raise ContractError(f"query {query_id} has inconsistent candidate_set_size")
        if query_loci[query_id] != str(row["unified_locus_id"]):
            raise ContractError(f"query {query_id} spans multiple loci")
        if str(row["unit_type"]) == "VARIANT":
            if start != end:
                raise ContractError(f"variant query {query_id} must have start=end")
            for allele_field in ("ref_allele", "alt_allele"):
                allele = str(row.get(allele_field, "")).upper()
                if not allele or any(base not in "ACGT" for base in allele):
                    raise ContractError(f"variant query {query_id} has invalid {allele_field}")

    duplicates = [key for key, count in Counter(pair_keys).items() if count > 1]
    if duplicates:
        raise ContractError(f"duplicate query/gene candidate pairs: {duplicates[:3]}")
    observed = Counter(query for query, _ in pair_keys)
    for query_id, declared in query_sizes.items():
        if observed[query_id] != declared:
            raise ContractError(
                f"query {query_id} declares {declared} candidates but has {observed[query_id]} rows"
            )
    return ValidationSummary(len(records), len(query_sizes), len(set(query_loci.values())))


def validate_truth_rows(rows: Iterable[Mapping[str, Any]]) -> ValidationSummary:
    records = list(rows)
    if not records:
        raise ContractError("truth table is empty")
    keys: set[tuple[str, str, str]] = set()
    for index, row in enumerate(records, start=1):
        missing = _missing(row, TRUTH_REQUIRED)
        if missing:
            raise ContractError(f"truth row {index} missing fields: {missing}")
        for field in ("dataset_id", "query_id", "truth_gene_id", "truth_type", "truth_source_id", "provenance_id"):
            if not _nonempty(row[field]):
                raise ContractError(f"truth row {index} has empty {field}")
        collision = str(row["source_collision_class"])
        if collision not in {item.value for item in CollisionClass}:
            raise ContractError(f"truth row {index} has invalid source collision class")
        key = (str(row["query_id"]), str(row["truth_gene_id"]), str(row["truth_source_id"]))
        if key in keys:
            raise ContractError(f"duplicate truth relation: {key}")
        keys.add(key)
    return ValidationSummary(len(records), len({str(row["query_id"]) for row in records}))


def validate_score_rows(rows: Iterable[Mapping[str, Any]]) -> ValidationSummary:
    records = list(rows)
    if not records:
        raise ContractError("score table is empty")
    _assert_no_forbidden_fields(records, "score table")
    keys: set[tuple[str, str, str]] = set()
    for index, row in enumerate(records, start=1):
        missing = _missing(row, SCORE_REQUIRED)
        if missing:
            raise ContractError(f"score row {index} missing fields: {missing}")
        if str(row["score_direction"]) != "HIGHER_IS_BETTER":
            raise ContractError(f"score row {index} must use HIGHER_IS_BETTER")
        status = str(row["eligibility_status"])
        if status not in ALLOWED_SCORE_STATES:
            raise ContractError(f"score row {index} has invalid eligibility_status")
        score = row["score"]
        if status == "ELIGIBLE":
            try:
                parsed = float(score)
            except (TypeError, ValueError) as exc:
                raise ContractError(f"eligible score row {index} is non-numeric") from exc
            if not isfinite(parsed):
                raise ContractError(f"eligible score row {index} is non-finite")
            if _nonempty(row["abstention_reason"]):
                raise ContractError(f"eligible score row {index} cannot have abstention_reason")
        else:
            if _nonempty(score):
                raise ContractError(f"ineligible score row {index} must have empty score")
            if not _nonempty(row["abstention_reason"]):
                raise ContractError(f"ineligible score row {index} needs abstention_reason")
        key = (str(row["query_id"]), str(row["candidate_gene_id"]), str(row["method_id"]))
        if key in keys:
            raise ContractError(f"duplicate method score: {key}")
        keys.add(key)
    return ValidationSummary(len(records), len({str(row["query_id"]) for row in records}))
