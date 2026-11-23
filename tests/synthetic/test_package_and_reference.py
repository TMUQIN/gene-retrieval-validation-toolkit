"""Additional tests use literal sequences and artificial variant identifiers only."""
import gzip
import importlib
from importlib.metadata import version
from gene_retrieval.harmonization import reference_utils as ref
import pytest

@pytest.mark.parametrize("module", ["evaluation.authorization", "evaluation.build_manifest", "evaluation.ranking", "harmonization.contracts", "harmonization.reference_utils"])
def test_qualified_package_imports(module):
    assert importlib.import_module("gene_retrieval." + module).__package__.startswith("gene_retrieval.")
    assert version("gene-retrieval-toolkit") == "0.1.0"

def test_reference_streams_artificial_fasta(synthetic_workspace):
    fasta = synthetic_workspace / "artificial.fa.gz"
    with gzip.open(fasta, "wt", encoding="ascii") as handle:
        handle.write(">chr1 artificial\nACGT\nACGT\nAA\n>chr2\nTTCC\nGG\n")
    segments = ref.read_reference_segments(fasta, {"chr1": {1: 4, 3: 5, 8: 3, 10: 2}, "chr2": {3: 4}, "chrX": {1: 1}})
    assert segments == {("chr1", 1): "ACGT", ("chr1", 3): "GTACG", ("chr1", 8): "TAA", ("chr2", 3): "CCGG"}

def test_variant_helpers_and_normalization():
    assert ref.reverse_complement("acgtA") == "TACGT"
    assert ref.supported_allele("ac") and not ref.supported_allele("N")
    assert ref.parse_source_variant_id("chr1_5_A_C_synthetic")["position_1based"] == 5
    assert ref.parse_source_variant_id("chr1_0_A_C") is None
    assert ref.canonical_variant_id("chr1", 5, "a", "c") == "chr1:5:A:C"
    assert ref.normalize_variant("chr1", 5, "AC", "AT", lambda _: "G") == ("chr1", 6, "C", "T")
    assert ref.normalize_variant("chr1", 4, "AA", "A", lambda _: "A") == ("chr1", 1, "AA", "A")
    with pytest.raises(ValueError):
        ref.normalize_variant("chr1", 1, "N", "A", lambda _: "A")


def test_normalization_does_not_validate_ref_or_build():
    # An artificial reference has A at this coordinate, but the supplied REF is C.
    # Callers must detect that mismatch before normalization; SNPs need no callback.
    artificial_reference = "ACGT"
    supplied_ref = "C"
    assert supplied_ref != artificial_reference[0]
    def previous_base_not_needed(_):
        raise AssertionError("SNP normalization should not request a preceding base")
    assert ref.normalize_variant("chr1", 1, supplied_ref, "G", previous_base_not_needed) == ("chr1", 1, "C", "G")
    assert ref.canonical_variant_id("artificial_contig", 0, "n", "?") == "artificial_contig:0:N:?"
