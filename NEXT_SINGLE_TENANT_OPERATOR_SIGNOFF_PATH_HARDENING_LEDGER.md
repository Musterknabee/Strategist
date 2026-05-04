# Next Slice: Operator Signoff Path-Integrity Hardening

## Scope

Hardened the late-stage deployment signoff generator so release approval evidence is not read from or written through symlinked filesystem paths.

## Changed files

- `scripts/generate_operator_deployment_signoff.py`
- `tests/constitutional/test_generate_operator_deployment_signoff.py`

## Behavior

`generate_operator_deployment_signoff.py` now rejects unsafe paths before reading evidence manifests or writing `operator_signoff.json`:

- `SIGNOFF_EVIDENCE_DIR_IS_SYMLINK`
- `SIGNOFF_EVIDENCE_DIR_PARENT_IS_SYMLINK`
- `SIGNOFF_EVIDENCE_MANIFEST_IS_SYMLINK`
- `SIGNOFF_EVIDENCE_MANIFEST_PARENT_IS_SYMLINK`
- `SIGNOFF_PROVIDER_EVIDENCE_MANIFEST_IS_SYMLINK`
- `SIGNOFF_PROVIDER_EVIDENCE_MANIFEST_PARENT_IS_SYMLINK`
- `SIGNOFF_OUTPUT_IS_SYMLINK`
- `SIGNOFF_OUTPUT_PARENT_IS_SYMLINK`

Failures emit `operator_deployment_signoff_path_error/v1` and exit non-zero without writing the signoff artifact.

## Validation

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/constitutional/test_generate_operator_deployment_signoff.py tests/constitutional/test_deployment_readiness_tier.py tests/constitutional/test_runtime_ledger_path_integrity.py tests/constitutional/test_ledger_ops_cli.py`
- `python scripts/source_health.py --json`
- `python scripts/repository_truth_check.py --json`
- `python -m compileall -q strategy_validator scripts tests`
- `python scripts/verify_repo_archive.py <archive> --repo-root . --json`
