# Next Single-Tenant Slice: Compose Runtime Contract Guardrails

## Problem

The generated bundle already pinned Docker Compose volume names so Compose-managed API containers and ad-hoc helper containers use the same durable ledger and backup volumes. However, bundle verification mostly treated the Compose file as a digest-tracked text artifact. If a generated manifest was refreshed from a drifted Compose file, structural mistakes such as duplicate `name:` entries, missing pinned volume names, or a widened host bind could pass until target-host runtime.

## Change

Added a generated Compose runtime-contract verifier in `strategy_validator/cli/single_tenant_deployment_bundle.py`. Bundle checks now require exactly one service ledger volume binding, one service backup volume binding, one pinned ledger volume name, one pinned backup volume name, and the loopback host-port binding `127.0.0.1:${STRATEGY_VALIDATOR_HOST_PORT:-8000}:8000`.

## Tests

Updated `tests/constitutional/test_single_tenant_deployment_bundle.py` to prove the checker rejects drifted Compose volume-name declarations and widened/non-aligned host-port binds even when the manifest digest inventory has been refreshed.
