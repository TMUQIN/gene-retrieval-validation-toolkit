# v0.1.0 synthetic clean-room validation

**PASS — 56/56 cases, 0 failures, 0 skips.** This fresh execution tested `gene-retrieval-toolkit==0.1.0` with import namespace `gene_retrieval`. All nine inherited regression functions passed; the remaining 47 cases also passed. `TEST_CASES.tsv` identifies every current test case. `CLEANROOM_TEST_RESULTS.tsv` contains 87 PASS execution/check records, including the 56 cases; these are not 87 independent unit tests.

## Source and environment

- Input code/data source: the independently reviewed 55-member `PUBLIC_RELEASE_CANDIDATE.zip`.
- Input ZIP SHA256: `72004613b4ab2892b46a4c82d23b5c5c0221eb8a4e1a243102ac855c68385f9c`.
- Three license files were supplied separately and copied unchanged. No old Git history or original research workspace was used.
- SHA256 of `VALIDATED_INPUT_SHA256.tsv`: `118a03ee5eefdfe72529dabfc37c0b958524f8124b4252bbdc5fbaa1eb251bc4`.
- All 35 execution inputs, including the supplied licenses, remained unchanged in the source and copied snapshot after execution. The source folder was subsequently placed at its final standalone location without changing file bytes.
- Windows 11 AMD64 / CPython 3.12.10; NumPy 2.5.5; pytest 9.2.0. Separate setup tools: pip 25.0.1, setuptools 80.9.0 and wheel 0.45.1. All installed distributions are listed in `ENVIRONMENT_METADATA.txt` and `run_summary.json`.

A new external virtual environment was created. The stdlib phase ran before NumPy/pytest installation and imported contracts, reference, authorization and manifest helpers. It checked artificial FASTA, empty candidate rejection and absent authorization. After setup, a non-editable package install was imported from fresh site-packages with no source-path injection. Pip check reported no broken requirements. All eight installed runtime Python files match the source SHA256 values.

## Tests

The inherited nine cover candidate/truth/score contracts, stable ties and multi-truth metrics, incomplete-score abstention, independent-source support, seeded locus bootstrap and fail-closed authorization. Package import/version checks now expect 0.1.0. Authorization uses explicit caller-selected filenames, workspace, environment variable and scope, with rejection cases for invalid paths/configuration, malformed/non-object receipts, invalid digests/tokens, unreadable text and absent/incorrect opt-in. Link rejection is implemented/reviewed but actual link creation is not exercised; no link case was skipped.

Reference checks use only short literal gzip FASTA, cross-line segments and missing/truncated requests. Normalization/identifier tests explicitly preserve the existing behavior: callers must validate REF/build/coordinates; the formatter does not perform that validation. Runtime scientific code, all five schema/design files and both fixture TSVs remain byte-identical to the reviewed input.

The two fixtures contain 12 artificial candidate rows and six artificial truth rows across four queries. Exact headers, IDs, probability constants and referential links are checked. A toy-distance case negates literal distances to exercise generic ranking; it is not a complete distance-only pipeline or biological finding. Manifest checks cover self-exclusion, exclusions, explicit installed-package root and containment; its separate isolated CLI invocation also passed.

## Boundary and limits

Workers use isolated UTF-8 Python, disabled bytecode/plugin autoload and a minimal environment. Python audit hooks restrict file access and reject socket/subprocess events. Each worker's three intentional synthetic probes were rejected before operation, with no unexpected boundary attempts. Setup and the separate reviewed stdlib manifest CLI are outside those hooks. The setup-only temporary-directory ACL workaround is not carried into tests.

Only dependency preparation used PyPI. No real biological/OA/patient/controlled data, AlphaGenome-derived outputs, model artifacts or model/data API was accessed. Setup log copies redact machine-specific paths. Python-level hooks are not OS/container isolation or complete native syscall tracing.

Scoped MIT / CC BY 4.0 notices are supplied in `LICENSE`, `LICENSE-CC-BY-4.0.txt` and `LICENSES.md`; third-party dependency terms remain separate. Tests do not verify ownership or grant additional rights. No full-manuscript, cross-platform, minimum-version or scientific-validity claim follows. No repository, commit, tag, Release, DOI or Zenodo record was created. The exact release inventory is in `PUBLIC_RELEASE_FILE_MANIFEST.tsv`; external final manifests/checksums accompany the release ZIP.
