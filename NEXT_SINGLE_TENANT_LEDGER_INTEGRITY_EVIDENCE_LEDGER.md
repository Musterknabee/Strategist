# Next Single-Tenant Ledger Integrity Evidence Ledger

## Slice completed

This tranche hardens the target-host post-deploy ledger evidence path.

## Changes

- Added `ledger_ops_integrity_verify/v1` as a single combined JSON report for ledger schema/hash-chain verification plus operator action journal verification.
- Added `strategy-validator-ledger-ops verify-integrity` so generated deployment helpers no longer need to concatenate multiple JSON documents into one redirected file.
- Updated generated `commands/verify-ledger.sh` to emit one machine-readable JSON document.
- Extended deployment evidence acceptance to allow the combined integrity schema while preserving compatibility with the earlier `ledger_ops_verify/v1` schema.
- Added `backup_sha256` to ledger backup reports so backup artifacts have direct digest evidence in addition to report digests.
- Removed a duplicate generated Docker `--read-only` flag in `commands/acceptance.sh`.

## Why this matters

Before this slice, `commands/post-deploy-evidence.sh` redirected `commands/verify-ledger.sh` into `ledger-verify.json`, but `verify-ledger.sh` emitted two JSON objects: one for the ledger and one for operator actions. That made the evidence file invalid JSON and could block or corrupt final deployment evidence collection.

## Scope boundary

This remains a backend-only single-tenant deployment hardening step. It does not certify frontend or multi-tenant SaaS readiness.
