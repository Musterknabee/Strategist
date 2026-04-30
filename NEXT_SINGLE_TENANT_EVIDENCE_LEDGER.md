# Next single-tenant deployment evidence slice

Implemented a backend-only single-tenant deployment evidence pack.

## Added

- `strategy_validator/cli/single_tenant_deployment_evidence.py`
- console script `strategy-validator-single-tenant-evidence`
- deployment bundle helper `commands/post-deploy-evidence.sh`
- constitutional tests in `tests/constitutional/test_single_tenant_deployment_evidence.py`
- CI gate that builds a non-final evidence manifest from env, bundle, and acceptance reports
- repository truth/source health coverage

## Scope

This remains single-tenant backend-only deployment readiness. It does not add a frontend, multi-tenant auth, SaaS hosting, or workflow engine.

## Evidence model

The evidence CLI emits `single_tenant_deployment_evidence/v1` and records schema versions, file sizes, and SHA-256 hashes for deployment reports. Final evidence mode requires preflight, API smoke, ledger verification, and backup reports.
