# Licensing

This repository uses a **scoped, dual-license arrangement**. Do not assume that one license applies to every file.

## MIT License — software

The MIT License in the repository-root `LICENSE` applies to:
- `src/**`
- Python test code under `tests/**/*.py`
- `pyproject.toml`
- repository-owned software configuration and build scripts, where present

Copyright notice: `Copyright (c) 2026 Gene Retrieval Toolkit contributors`.

## CC BY 4.0 — documentation, schemas and synthetic materials

The notice in `LICENSE-CC-BY-4.0.txt` applies to:
- `README.md`
- `docs/**`
- `schemas/**`
- `tests/fixtures/**`
- `validation/**`
- `environment/**`
- repository-owned explanatory Markdown, TSV manifests, and clean-room reports

Attribution: `Gene Retrieval Toolkit contributors (2026), Gene Retrieval Validation Toolkit`.

## Exclusions

Neither license grants rights to:
- third-party software or dependencies (their own licenses apply);
- third-party reference data or annotations not included in this repository;
- AlphaGenome outputs or derivatives;
- F1 training artifacts, RNA-derived scores/ranks, or rank-fusion materials;
- patient-level or controlled-access data;
- third-party images or other materials not included in the release candidate.

If a file contains a separate copyright or license notice, that notice takes precedence for the relevant material. Do not remove upstream notices.

## Version

The first public release is planned as `0.1.0` / Git tag `v0.1.0`. This is an initial public release, not a claim of a mature 1.0 API. The package metadata, README and release tag must all use the same version.

## Citation

A version-specific Zenodo DOI will be added after the GitHub release has been archived. Until then, cite the GitHub repository URL and release tag; do not invent a DOI.
