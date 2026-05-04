# Next single-tenant evidence hardening ledger

## Scope

This slice tightens the backend-only single-tenant deployment evidence pack.

## Changes

- `strategy_validator/cli/single_tenant_deployment_evidence.py` now rejects symlinked evidence report paths instead of hashing through filesystem indirection.
- Optional frontend checkpoint evidence now accepts the real `single_tenant_frontend_readiness/v1` schema as context, but fails closed if that checkpoint claims frontend readiness.
- The top-level single-tenant evidence report still keeps `frontend_readiness_claimed=false`; frontend readiness remains outside the backend-only deployment go/no-go path.
- Added regression tests covering:
  - symlinked deployment report rejection,
  - claimed frontend readiness rejection,
  - non-claiming frontend checkpoint context acceptance.

## Why

The evidence pack is the final operator handoff record. It should record direct JSON reports, not symlink targets that can redirect evidence collection to mutable or unexpected locations. It also must not let an optional frontend checkpoint smuggle a frontend-readiness claim into a backend-only deployment record.

## Validation

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/constitutional/test_single_tenant_deployment_evidence.py`
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/constitutional/test_single_tenant_deployment_bundle.py tests/constitutional/test_single_tenant_deployment_acceptance.py tests/constitutional/test_single_tenant_deployment_env_check.py tests/constitutional/test_single_tenant_deployment_evidence.py tests/constitutional/test_single_tenant_api_smoke_token_sources.py tests/constitutional/test_single_tenant_api_smoke_script.py tests/constitutional/test_single_tenant_deployment_preflight.py`
- `python scripts/source_health.py`
- `python scripts/repository_truth_check.py`
