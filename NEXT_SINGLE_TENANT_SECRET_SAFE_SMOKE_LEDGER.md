# Next Single-Tenant Secret-Safe Smoke Hardening Ledger

## Scope

This tranche continues the backend-only single-tenant production hardening work. It focuses on target-host operator safety for API smoke verification and bundle handling.

## Changes

### Secret-safe API smoke token sourcing

- `strategy_validator/cli/single_tenant_api_smoke.py`
  - Added standalone env-file parsing that does not shell-evaluate `deployment.env`.
  - Added `resolve_smoke_token(...)` with source precedence:
    1. deprecated explicit `--token` compatibility path,
    2. `--token-env-var` / environment variable,
    3. `--env-file` deployment env file.
  - Made `--token` optional and documented it as a compatibility-only path because bearer tokens in argv can appear in process listings and shell history.
  - Emits a machine-readable failed smoke report if no token source is available.

### Generated bundle smoke command

- `strategy_validator/cli/single_tenant_deployment_bundle.py`
  - `commands/api-smoke.sh` now self-locates the bundle root and defaults `STRATEGY_VALIDATOR_ENV_FILE` to `${BUNDLE_DIR}/deployment.env`.
  - It passes `--token-env-var` and `--env-file` instead of `--token <secret>`.
  - `commands/post-deploy-evidence.sh` no longer requires `STRATEGY_VALIDATOR_API_TOKEN` in the shell; the smoke helper can read it from the private env file.

### Bundle-local commit guardrails

- Generated bundles now include `.gitignore` to block accidental commits of:
  - `deployment.env`,
  - local `.env` files,
  - `evidence/`,
  - SQLite ledger files,
  - backup/pre-restore directories.

### Acceptance and documentation

- `strategy_validator/cli/single_tenant_deployment_acceptance.py`
  - Treats bundle `.gitignore` as a required generated handoff file.
- `docs/deployment/SINGLE_TENANT_DEPLOYMENT_READINESS.md`
  - Updated API smoke usage to prefer `--env-file deployment.env`.
  - Documented that `--token` is compatibility-only.
  - Documented the bundle-local `.gitignore` guardrail.

## Tests / validation

Focused tests run with plugin autoload disabled in the sandbox:

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/constitutional/test_single_tenant_api_smoke_token_sources.py \
  tests/constitutional/test_single_tenant_deployment_bundle.py \
  tests/constitutional/test_single_tenant_deployment_acceptance.py \
  tests/constitutional/test_single_tenant_deployment_evidence.py
```

Result:

```text
12 passed
```

Repository gates run:

```text
source_health: PASS
repository_truth_check: PASS
migration_truth_check: PASS
verify_repo_archive: PASS
unzip integrity: PASS
```

## Boundary

This remains a backend-only single-tenant hardening slice. It does not claim multi-tenant SaaS readiness or frontend readiness.
