# Toolkit scope

The package offers in-memory table validators and ranking metrics, streamed reference helpers, configurable evaluation opt-in and checksum generation. There is no training, model inference or biological-data download workflow. Ranking accepts caller-provided values and does not verify their scientific provenance or automatically invoke authorization.

The two candidate dictionaries serve different purposes and remain separate: `candidate_universe.schema.tsv` describes a variant-oriented provenance table; `candidate_geometry.schema.tsv` describes a query/interval interchange table. The truth and source-overlap dictionaries describe separate interfaces. Dictionary requirements can exceed the constraints enforced in Python. Synthetic fixture tables use their own small demonstration formats, not a claim of complete schema conformance.

Only the runtime package, packaging configuration, schemas, synthetic tests/fixtures, README/public documentation, minimal environment information, current clean-room evidence and current public file manifest belong in the public candidate. Migration records, original-path crosswalks, historical evidence and internal rights/decision records are retained separately. They are not runtime inputs or members of the public ZIP.

The public file manifest uses current archive-relative paths only. It excludes itself from hashing to avoid self-reference. Its own bytes are included in the outer ZIP and covered by the external final checksum record. A successful synthetic run supports the tested snapshot/environment only; it does not establish scientific validity, full manuscript reproduction, cross-platform support or redistribution rights.
