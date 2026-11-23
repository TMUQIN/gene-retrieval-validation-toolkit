# Configurable evaluation authorization

`require_formal_authorization()` is an optional application-level opt-in check. An application can bind a random token to a receipt and require an explicit environment setting before evaluation. The helper does not run automatically inside ranking, authenticate a user, enforce an operating-system boundary or grant data rights.

All configuration is caller-supplied:

```python
from pathlib import Path
from gene_retrieval.evaluation.authorization import require_formal_authorization

receipt = require_formal_authorization(
    Path("."),
    authorization_filename="consent/approval.txt",
    receipt_filename="metadata/approval.json",
    environment_variable="EVALUATION_OPT_IN",
    authorization_scope="APPROVED_EVALUATION",
)
```

This call fails until its explicitly configured inputs and opt-in exist. There are no default filenames, environment variable or scope. Filenames are relative to the existing workspace. Absolute paths, parent traversal, identical token/receipt paths and paths traversing symlinks or junctions are rejected. Configuration should come from a trusted application; these checks are not a substitute for access controls against concurrent hostile filesystem changes.

The receipt is a JSON object containing `authorization_token_sha256` (a 64-character SHA-256 hexadecimal digest) and `authorization_scope` (an exact match to the requested scope). The helper hashes the nonempty stripped token and compares digests with `hmac.compare_digest`. The configured environment variable must equal `YES`. Missing files, unreadable/invalid text, invalid JSON/object structure, invalid digest, token mismatch, incorrect scope or missing/incorrect opt-in raise `AuthorizationError`.

`generate_authorization_token()` generates a random token. Store plaintext only in the designated authorization file; keep it out of receipts and provenance metadata. The helper returns the validated receipt without adding the plaintext token. Synthetic tests use artificial tokens and receipts only.
