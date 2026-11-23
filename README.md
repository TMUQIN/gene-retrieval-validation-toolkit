# Gene Retrieval Validation Toolkit

Version **0.1.0** provides reusable Python utilities for gene-retrieval evaluation, table validation, ranking metrics and streamed reference-sequence lookup. The repository contains artificial examples and synthetic tests; it does not distribute real biological data or model outputs.

## Included functions

- Candidate, truth and generic score table validation, including explicit missingness and candidate completeness checks.
- Stable ranking, retrieval metrics, common-support comparisons and a seeded locus-cluster bootstrap for caller-supplied scores.
- A configurable receipt-bound authorization helper with an explicit process opt-in.
- Streamed gzip FASTA segment lookup, allele/identifier helpers and the existing variant trimming/left-shift procedure.
- A workspace-contained, self-excluding SHA-256 manifest utility.

Ranking does not generate a complete distance-only analysis pipeline. Callers supply their own values and are responsible for data permissions, scientific assumptions and any required authorization.

## Installation and synthetic tests

The tested environment is Windows 11 AMD64 / CPython 3.12.10. Create a new virtual environment, activate it, then run from this checkout:

```powershell
python -m pip install -r environment/requirements-minimal.txt
python -m pip install .
python -m pytest tests/synthetic --import-mode=importlib -p no:cacheprovider
```

NumPy 2.5.5 is the ranking runtime dependency; pytest 9.2.0 runs the tests. Other runtime utilities use the Python standard library. Packaging also uses the build tools declared in `pyproject.toml`. Exact installed versions and the final test count are recorded in `FINAL_CLEANROOM_REPORT.md` and `validation/clean-room/current/ENVIRONMENT_METADATA.txt`. These are tested versions, not minimum supported versions or a full transitive lock. No cross-platform support claim is made.

```python
from gene_retrieval.harmonization.contracts import validate_candidate_rows
from gene_retrieval.evaluation.ranking import rank_complete_queries
from gene_retrieval.harmonization.reference_utils import read_reference_segments
```

For checksums, an installed package needs an explicit workspace:

```powershell
python -m gene_retrieval.evaluation.build_manifest --root . --output SHA256SUMS.tsv
```

## Scope and limitations

`src/gene_retrieval/` contains the runtime package; `schemas/` contains separate candidate dictionaries, a truth dictionary, source-overlap definitions and split design notes. `tests/fixtures/synthetic/` contains two hand-specified tables with artificial identifiers, distances, labels and probability constants. Their small example formats are distinct from the interchange contracts. No reference genome is bundled or downloaded.

The authorization helper requires caller-selected workspace, authorization filename, receipt filename, environment variable and scope. It has no implicit project settings and does not replace OS access controls or grant data rights. See [authorization configuration](docs/authorization.md).

`normalize_variant()` does not verify the input REF against a reference sequence. Callers must validate REF, coordinates and build before normalization. Its callback supplies preceding bases for the existing indel shift rule. `canonical_variant_id()` only formats an identifier and does not validate genome build or alleles.

This is not a full reproduction of the AlphaGenome–OA manuscript. The package contains no AlphaGenome-derived outputs, fitted models, real OA/patient data, controlled-access data or third-party research figures. Successful synthetic tests do not establish scientific validity for arbitrary inputs or grant rights to third-party data.

See [scope](docs/repository_scope.md), [data governance](docs/data_governance.md) and [reproducibility](docs/reproducibility.md). `PUBLIC_RELEASE_FILE_MANIFEST.tsv` lists current public-relative paths and file hashes; it contains no original private source paths. Current evidence is included separately from historical/internal records.

Project-owned materials are distributed under the scoped licenses listed below. For software verification, see the included clean-room evidence and its documented environment and scope.

## License

This toolkit uses scoped licenses:

- **Software code:** MIT License — see [`LICENSE`](LICENSE).
- **Documentation, schemas, synthetic fixtures, and validation materials:** CC BY 4.0 — see [`LICENSE-CC-BY-4.0.txt`](LICENSE-CC-BY-4.0.txt) and [`LICENSES.md`](LICENSES.md).

Third-party dependencies, upstream reference resources, and any material excluded from this repository retain their own terms. No AlphaGenome-derived outputs, F1 artifacts, patient-level data, or controlled-access data are included.
