# Next Single-Tenant Evidence Mount Contract Ledger

## Scope

Harden generated post-deploy evidence Docker fallback mounts so evidence collection cannot mutate deployment inputs.

## Finding

`commands/post-deploy-evidence.sh` mounted the generated bundle path at `/bundle` with read-write access inside fallback Docker CLI containers. The evidence collector writes only to `/evidence`; `/bundle`, `/repo`, and `/env` are input surfaces and should be immutable during evidence collection.

## Changes

- Changed generated `commands/post-deploy-evidence.sh` to mount `/bundle` read-only.
- Added `_verify_generated_evidence_mount_contract()` to reject regenerated/tampered bundles that make `/bundle`, `/repo`, or `/env` writable or make `/evidence` read-only.
- Added constitutional regression coverage that refreshes `manifest.json` after drifting the helper, proving the structural checker still blocks unsafe mount mutability.
- Updated deployment docs to describe read-only input mounts and read-write evidence output only.

## Production effect

Post-deploy evidence collection now follows a stricter evidence-input/evidence-output boundary: generated bundle, source/repo assets, and deployment env are read-only inputs; only the evidence directory is mutable output.
