# Next Slice: Repo Root Archive Path-Integrity Hardening

## Status

Implemented and validated.

## Problem

The clean repository handoff tooling already rejected symlinked archive input and output paths, but the caller-provided `--repo-root` could still be canonicalized with `Path.resolve()`. That allowed packaging or archive verification to operate on a symlinked repository root while reporting the resolved target, hiding filesystem indirection in the handoff evidence layer.

## Changes

- Added repo-root path-integrity validation to `scripts/package_repo.py`.
- Reused that validation in `scripts/verify_repo_archive.py`.
- Rejected symlinked repository roots and repository roots beneath symlinked parent directories before source selection, hashing, or ZIP verification.
- Preserved structured verification behavior by returning `repo_root_path_integrity` failures from archive verification.
- Added regression coverage in `tests/constitutional/test_repo_archive_path_integrity.py`.

## Validation

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/constitutional/test_repo_archive_path_integrity.py tests/constitutional/test_ui_facade_contract_snapshot_path_integrity.py tests/constitutional/test_frontend_readiness_claim_path_integrity.py`
- `python scripts/source_health.py --json`
- `python scripts/repository_truth_check.py --json`
- `python -m compileall -q scripts/package_repo.py scripts/verify_repo_archive.py tests/constitutional/test_repo_archive_path_integrity.py`
