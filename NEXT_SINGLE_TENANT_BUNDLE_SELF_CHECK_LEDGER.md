# Next single-tenant bundle self-check ledger

## Scope

This slice closes a deployment-readiness gap in the single-tenant bundle generator itself.

## Changes

- `strategy_validator/cli/single_tenant_deployment_bundle.py` now runs the generated bundle through the same structural verifier before returning a successful generation report.
- Generation now fails closed when generated templates drift, even if the emitted manifest digests match the drifted files.
- `manifest.json` is rewritten with the final `ok` value and structural errors after self-verification, so operators do not receive a misleading green manifest from a bad generator.
- Added a regression test that monkeypatches the generated systemd template to widen the host bind from loopback to `0.0.0.0`; generation now reports failure and records the drift in `manifest.json`.
- Fixed the env-check regression test fixture to chmod the secret-bearing test env file to `0600`, matching the production env-file permission policy.

## Why

Prior bundle verification caught tampered or drifted generated artifacts when `strategy-validator-single-tenant-bundle --check` was run. The generation path itself could still emit an `ok=true` report if the generator template had drifted before manifest creation. That was too optimistic for a fail-closed deployment handoff.

## Validation

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/constitutional/test_single_tenant_deployment_bundle.py tests/constitutional/test_single_tenant_deployment_acceptance.py tests/constitutional/test_single_tenant_deployment_env_check.py`
- `python scripts/source_health.py`
- `python scripts/repository_truth_check.py`
