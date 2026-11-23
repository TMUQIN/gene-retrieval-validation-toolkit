"""The two legacy fixture formats are distinct from the contract interchange schema."""
import csv
from collections import Counter
from pathlib import Path
from gene_retrieval.evaluation.ranking import rank_complete_queries, evaluate_rankings

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "synthetic"

def load(name):
    with (FIXTURES / name).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = list(reader)
        assert all(None not in row and all(value is not None for value in row.values()) for row in rows)
        return reader.fieldnames, rows

def test_artificial_geometry_format_and_content():
    fields, rows = load("candidate_geometry.tsv")
    assert fields == ["query_id", "unified_locus_id", "variant", "candidate_gene_id", "distance_to_tss_bp", "candidate_order_key", "candidate_present"]
    assert len(rows) == 12
    assert Counter(row["query_id"] for row in rows) == {f"q{i}": 3 for i in range(1, 5)}
    assert len({(r["query_id"], r["candidate_gene_id"]) for r in rows}) == 12
    assert {r["variant"] for r in rows} == {f"sv{i}" for i in range(1, 5)}
    assert all(r["candidate_present"] == "1" and r["candidate_order_key"] == r["candidate_gene_id"] for r in rows)
    for query in {r["query_id"] for r in rows}:
        assert [int(r["distance_to_tss_bp"]) for r in rows if r["query_id"] == query] == [10, 20, 30]

def test_artificial_truth_format_and_links():
    fields, truth = load("truth_panel.tsv")
    _, geometry = load("candidate_geometry.tsv")
    assert fields == ["query_id", "unified_locus_id", "trait", "variant", "gene", "evidence_type", "evidence_tier", "PIP", "coloc_probability", "tissue", "source", "genome_build", "allele_info", "independence_status", "conflict_group", "accepted_flag"]
    assert len(truth) == 6
    assert Counter(r["query_id"] for r in truth) == {"q1": 1, "q2": 2, "q3": 2, "q4": 1}
    candidates = {(r["query_id"], r["unified_locus_id"], r["variant"], r["candidate_gene_id"]) for r in geometry}
    assert all((r["query_id"], r["unified_locus_id"], r["variant"], r["gene"]) in candidates for r in truth)
    assert all(r["trait"] == "SYNTHETIC_OA" and r["tissue"] == "SYN_CARTILAGE" and r["genome_build"] == "SYN_BUILD" and r["source"].startswith("SYN_SRC_") and r["allele_info"] == "SYN_REF>SYN_ALT" and r["accepted_flag"] == "1" for r in truth)
    assert [(r["PIP"], r["coloc_probability"]) for r in truth] == [("NA", "NA"), ("NA", "NA"), ("NA", "NA"), ("0.80", "0.90"), ("0.60", "0.85"), ("NA", "NA")]

def test_artificial_distance_ranking_example():
    _, geometry = load("candidate_geometry.tsv")
    _, truth = load("truth_panel.tsv")
    candidates, truths, loci = {}, {}, {}
    for row in geometry:
        candidates.setdefault(row["query_id"], set()).add(row["candidate_gene_id"])
        loci[row["query_id"]] = row["unified_locus_id"]
    for row in truth:
        truths.setdefault(row["query_id"], set()).add(row["gene"])
    scores = [{**r, "method_id": "SYNTHETIC_DISTANCE", "score": -int(r["distance_to_tss_bp"]), "eligibility_status": "ELIGIBLE", "abstention_reason": ""} for r in geometry]
    ranks, abstentions = rank_complete_queries(scores, candidates)
    metrics = evaluate_rankings(ranks, abstentions, truths, loci)
    assert not abstentions and len(metrics) == 4
    assert all(m.first_true_rank == 1 and m.reciprocal_rank == 1.0 for m in metrics)
