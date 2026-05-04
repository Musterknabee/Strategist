# Next Single-Tenant Provider Operator Path Hardening Ledger

## Scope

This slice hardens provider-facing operator scripts that ingest secret-bearing env files and produce evidence artifacts for deployment/signoff flows.

## Changed files

- `scripts/_path_integrity.py`
- `scripts/check_provider_keys.py`
- `scripts/retrieve_provider_samples.py`
- `scripts/provider_health_check.py`
- `scripts/build_provider_evidence_manifest.py`
- `scripts/normalize_provider_samples.py`
- `tests/constitutional/test_provider_operator_path_integrity.py`

## Security posture

Operator-supplied env, manifest, sample-directory, normalized-records, and output paths are now validated without following symlinks. Unsafe paths fail closed before secrets are read, provider samples are written, normalized observations are materialized, or provider evidence manifests are generated.

## Machine-readable failures

Representative error codes include:

- `CHECK_PROVIDER_KEYS_ENV_FILE_IS_SYMLINK`
- `RETRIEVE_PROVIDER_OUTPUT_DIR_IS_SYMLINK`
- `RETRIEVE_PROVIDER_ENV_FILE_PARENT_IS_SYMLINK`
- `PROVIDER_HEALTH_MANIFEST_IS_SYMLINK`
- `PROVIDER_EVIDENCE_OUTPUT_PARENT_IS_SYMLINK`
- `PROVIDER_EVIDENCE_NORMALIZED_IS_SYMLINK`
- `NORMALIZE_PROVIDER_SAMPLES_DIR_IS_SYMLINK`
- `NORMALIZE_PROVIDER_OUTPUT_IS_SYMLINK`

## Validation

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/constitutional/test_provider_operator_path_integrity.py tests/constitutional/test_provider_scripts.py tests/constitutional/test_generate_operator_deployment_signoff.py tests/constitutional/test_deployment_readiness_tier.py tests/constitutional/test_ledger_ops_cli.py tests/constitutional/test_runtime_ledger_path_integrity.py`
- `python scripts/source_health.py --json`
- `python scripts/repository_truth_check.py --json`
- `python -m compileall -q scripts tests/constitutional/test_provider_operator_path_integrity.py strategy_validator`
