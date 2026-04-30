# Next Single-Tenant Bundle Tamper Evidence Ledger

## Scope

Continued the single-tenant production-readiness hardening after the secret-safe smoke slice. This tranche focused on making the generated target-host bundle auditable after it leaves the source checkout.

## Problem found

`strategy-validator-single-tenant-bundle --check` and the acceptance gate verified that generated helper files existed, but they did not verify that those files still matched the `manifest.json` SHA-256/size inventory. A copied bundle with a locally edited helper script could therefore pass existence-only acceptance.

## Changes

- Hardened `strategy_validator/cli/single_tenant_deployment_bundle.py`:
  - validates `manifest.generated_files` shape,
  - rejects unsafe manifest paths,
  - verifies generated-file size and SHA-256 digests against the manifest inventory,
  - requires all generated files except `manifest.json` to be present in the manifest digest inventory,
  - rejects `manifest.json` self-reference in `generated_files`,
  - verifies generated command helpers are executable,
  - rejects bundles whose manifest `ok` field is not true.
- Extended acceptance coverage so tampered bundles fail the go/no-go gate through `deployment_bundle_valid`.
- Updated deployment readiness docs to state that bundle verification is digest-backed, not existence-only.

## Validation

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/constitutional/test_single_tenant_deployment_bundle.py tests/constitutional/test_single_tenant_deployment_acceptance.py -q`: PASS, 8 tests.
- `python -m py_compile strategy_validator/cli/single_tenant_deployment_bundle.py tests/constitutional/test_single_tenant_deployment_bundle.py tests/constitutional/test_single_tenant_deployment_acceptance.py`: PASS.

## Boundary

This slice does not make the system multi-tenant or frontend-ready. It hardens the backend-only single-tenant deployment handoff and post-copy bundle verification path.
