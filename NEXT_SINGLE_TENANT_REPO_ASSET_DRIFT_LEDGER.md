# Next single-tenant repo-asset drift hardening ledger

## Scope

This slice tightens the generated deployment handoff around source deployment asset drift. The bundle already carried `repo-assets.manifest.json`, but acceptance treated an existing source checkout as sufficient even when those files had changed after bundle generation.

## Changes

- `strategy_validator/cli/single_tenant_deployment_acceptance.py` now compares present source deployment assets against the bundle-recorded SHA-256 and size evidence.
- Missing source assets can still pass on a target host when `repo-assets.manifest.json` proves they existed at bundle generation.
- `strategy_validator/cli/single_tenant_deployment_bundle.py` now validates the repo-asset manifest structure during bundle checks, including unsafe paths, duplicate paths, invalid digest values, invalid sizes, and missing required asset records.
- Constitutional tests cover source-asset drift rejection and malformed repo-asset manifest rejection.

## Why

Single-tenant operators may copy a generated handoff bundle alongside a later or locally modified source checkout. Acceptance must distinguish:

1. no source checkout available, but bundle repo-asset evidence is present; from
2. a source checkout is available but no longer matches the evidence used to generate the deployment bundle.

The second case is now deployment-blocking.
