# v0.1.0 dependency and input audit

AST-visible imports for every runtime/test module and validation driver are in `PYTHON_IMPORTS.tsv`. Embedded worker/setup scripts were reviewed separately. Ranking uses NumPy 2.5.5; the other runtime helpers use only the standard library. Pytest 9.2.0 is test-only. Pip/setuptools/wheel are separate setup tools. The broad historical package snapshot is neither used nor bundled.

Runtime source is byte-identical to the reviewed candidate. Contracts/ranking consume caller-provided records; authorization requires explicit workspace-relative files and opt-in settings; reference lookup reads only an explicitly selected gzip FASTA; manifest generation uses an explicit root and contained output. No runtime model/API client or fitted-model loader is introduced.

The package version metadata and its test expectation are updated to 0.1.0. The validation driver additionally hashes the three supplied license inputs. Its file-specific CC-BY-4.0 notice implements the supplied validation/** scope. These changes do not affect scientific algorithms, schema semantics or artificial fixtures.

REF/build validation remains the caller's responsibility before normalization. The identifier formatter only formats values. Tests use literal sequences, records and authorization receipts, plus two reviewed hand-specified TSVs. The dictionaries, Python-enforced constraints and toy fixture formats remain distinct.

The source code/data comes only from the reviewed ZIP; license notices come only from the supplied kit. No third-party dependency code, real reference data or model-derived output is vendored. Dependency licenses remain their own terms. Python audit hooks support the described cooperative test boundary, not complete native syscall tracing.
