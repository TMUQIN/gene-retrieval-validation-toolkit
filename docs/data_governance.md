# Data and permissions

All supplied TSV records and test sequences are artificial. The geometry fixture contains 12 candidates across four queries; the truth fixture contains six rows. Identifiers, variants, genes, distances, evidence categories, probability constants and disease-like labels are hand-specified test values. They are not measurements, estimates from real studies or biological findings.

Reference tests create short gzip FASTA files from literal A/C/G/T strings and remove their own scratch files. No real reference genome is included or downloaded. Candidate and truth interfaces remain separate. Interface validation does not certify scientific correctness, dataset origin, genome-build agreement or every requirement in a dictionary.

The candidate contains no real biological/patient/controlled-access data, AlphaGenome raw or derived outputs, fitted-model artifacts, score-fusion analyses, figures derived from those materials, API credentials or third-party research assets. The generic score interface does not grant permission to supply any particular score source.

Project-owned software and materials in this repository are distributed under the scoped MIT and CC BY 4.0 licenses specified in `LICENSES.md`. These licenses do not extend to third-party dependencies, upstream datasets, reference resources, or excluded research materials. Users are responsible for verifying the access rights and scientific suitability of any external data or reference resources supplied to the toolkit. Software test results do not independently establish data provenance or ownership.
