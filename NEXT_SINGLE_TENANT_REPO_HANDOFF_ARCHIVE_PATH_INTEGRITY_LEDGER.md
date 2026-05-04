# Next Slice: Repo Handoff Archive Path-Integrity Hardening

## Objective

Close the remaining path-integrity gap in the repository handoff tooling itself. The clean ZIP generator and verifier are part of the operator handoff chain, so they must not write or verify archives through symlinked filesystem paths.

## Changed files

- `scripts/package_repo.py`
- `scripts/verify_repo_archive.py`
- `tests/constitutional/test_repo_archive_path_integrity.py`

## Behavior added

### Package generation

`build_clean_repo_zip()` now rejects archive output paths that are:

- symlinks
- under symlinked parent directories
- existing non-regular filesystem objects

The package tool also avoids using `Path.resolve()` on the caller-provided archive output path before validation, preserving symlink visibility.

### Archive verification

`verify_clean_repo_archive()` now rejects archive inputs that are:

- symlinks
- under symlinked parent directories
- existing non-regular filesystem objects

Path-integrity failures are returned as structured verification failures instead of hashing/opening through the unsafe path.

## New structured failure names

- `archive_path_integrity`
- `archive_regular_file`

## Validation

Focused tests:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/constitutional/test_repo_archive_path_integrity.py \
  tests/constitutional/test_provider_operator_path_integrity.py \
  tests/constitutional/test_generate_operator_deployment_signoff.py \
  tests/constitutional/test_deployment_readiness_tier.py
```

Repository checks:

```bash
python scripts/source_health.py --json
python scripts/repository_truth_check.py --json
python -m compileall -q strategy_validator scripts tests
python scripts/verify_repo_archive.py <archive> --repo-root . --json
```
