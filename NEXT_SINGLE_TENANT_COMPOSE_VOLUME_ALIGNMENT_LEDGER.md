# Next Single-Tenant Compose Volume Alignment Ledger

## Slice objective

Prevent generated Docker Compose deployments from using Compose-prefixed volume names while generated one-shot helper containers use bare Docker volume names.

## Production risk found

Docker Compose normally prefixes named volumes with the Compose project name. The generated helper scripts use literal Docker volumes:

- `strategy-validator-ledger:/var/lib/strategy-validator`
- `strategy-validator-backups:/var/backups/strategy-validator`

Without explicit Compose `name:` fields, an operator who starts the API with Compose could run preflight, verification, backup, and restore helpers against a different empty ledger/backup volume from the running API container.

## Changes

- `strategy_validator/cli/single_tenant_deployment_bundle.py`
  - pinned generated Compose volume names to the `strategy-validator-ledger:/var/lib/strategy-validator` and `strategy-validator-backups:/var/backups/strategy-validator` volume bindings.
  - updated generated bundle README to document the volume-name invariant.
- `tests/constitutional/test_single_tenant_deployment_bundle.py`
  - added assertions that Compose declares explicit volume names and helper scripts use the same named volumes.
- `docs/deployment/SINGLE_TENANT_DEPLOYMENT_READINESS.md`
- `docs/deployment/BACKEND_CONTAINER_V1.md`
  - documented that these volume names are part of the handoff contract.

## Validation

- focused bundle tests
- py_compile for touched modules
- source health / repository truth / migration truth
- repo archive package + verification + unzip integrity
