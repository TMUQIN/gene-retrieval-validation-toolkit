# Reproducing the synthetic checks

Use Windows 11 AMD64 / CPython 3.12.10 for the tested configuration. Install `environment/requirements-minimal.txt`, install the package, then run:

```powershell
python -m pytest tests/synthetic --import-mode=importlib -p no:cacheprovider
```

The tests import the installed `gene_retrieval` package without source-path injection. They use literal synthetic rows, two artificial TSV fixtures, short artificial gzip FASTA and artificial authorization receipts. The nine inherited regression functions are identified by their current test paths in the final evidence; authorization calls now pass explicit generic settings. Additional cases exercise invalid paths/receipts, custom settings, missing opt-in and reference-helper limitations. No real data or external model/API is needed.

For a complete fresh-environment check, run the supplied driver with a new external directory:

```powershell
python -X utf8 -I -B validation/clean-room/current/run_cleanroom.py --work-dir "$env:TEMP/gene-retrieval-fresh-check"
```

That directory must not already exist. The driver copies only explicit current package/test/schema/documentation and supplied-license inputs, creates a virtual environment without system/user packages and runs standalone standard-library checks before installing NumPy/pytest. Setup bootstraps pip from CPython's bundled wheel, downloads pinned runtime/test/build dependencies from PyPI, and performs a non-editable local package installation. Network is used for package setup only. A temporary-directory ACL workaround applies to setup processes only on the tested host.

Test workers use isolated Python, disabled bytecode/plugin autoload, a minimal environment and Python audit hooks restricting file access and rejecting socket/subprocess events. Intentional synthetic event probes verify these rejection rules without making a network/process operation. The stdlib-only manifest CLI is additionally run as a separate isolated process. Audit hooks are Python-level instrumentation, not an OS/container sandbox or complete native syscall trace.

`FINAL_CLEANROOM_REPORT.md` records actual final outcomes. `VALIDATED_INPUT_SHA256.tsv` identifies all execution inputs; `SOURCE_SHA256_BEFORE_AFTER.tsv` checks both source and copied inputs. Evidence generated after execution is covered by `PUBLIC_RELEASE_FILE_MANIFEST.tsv` and the external final checksum record. Machine-specific setup paths are redacted from published log copies. The original Windows clean-room evidence identifies the pre-publication copy-edit snapshot through its input fingerprints. Only README, project metadata description, governance prose, and this reproducibility explanation were copy-edited afterward; no runtime code, tests, schemas, or fixtures changed. The current release inventory and external archive SHA256 identify the publication-facing snapshot. No old Git history is included.

Versions are tested pins, not lowest supported versions or a full lockfile. NumPy is the sole third-party runtime requirement; pytest is test-only. Setuptools/wheel are build tools. The full installed distribution list is recorded in current environment metadata. No full manuscript reproduction, cross-platform or publication-rights conclusion follows.
