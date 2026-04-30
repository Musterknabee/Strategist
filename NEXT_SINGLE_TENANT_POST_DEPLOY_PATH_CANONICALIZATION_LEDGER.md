# Next Single-Tenant Post-Deploy Path Canonicalization Ledger

## Slice objective

Make the generated post-deploy evidence collector robust when an operator supplies custom relative bundle, repo-root, env-file, or evidence-output paths.

## Problem found

`commands/post-deploy-evidence.sh` canonicalized the deployment env file but still used caller-relative values for `STRATEGY_VALIDATOR_BUNDLE_DIR`, `STRATEGY_VALIDATOR_REPO_ROOT`, and `STRATEGY_VALIDATOR_EVIDENCE_DIR` in host-side CLI calls and output redirections. Docker fallback mounts already used canonical host paths, so local CLI and Docker fallback execution could reason about different host locations under relative overrides.

## Changes made

- Canonicalized and exported `STRATEGY_VALIDATOR_BUNDLE_DIR` inside the generated evidence collector.
- Canonicalized and exported `STRATEGY_VALIDATOR_REPO_ROOT` inside the generated evidence collector.
- Canonicalized and exported `STRATEGY_VALIDATOR_EVIDENCE_DIR` inside the generated evidence collector.
- Added a bundle structural verifier that rejects generated post-deploy evidence helpers if those canonicalization/export lines are removed, even if `manifest.json` is regenerated from the drifted helper.
- Removed a duplicate `BUNDLE_DIR` assignment in `commands/preflight.sh` generation.
- Updated deployment docs to state that post-deploy evidence paths are canonicalized before local or Docker fallback execution.

## Validation intent

The single-tenant bundle check should now fail closed on caller-relative post-deploy evidence path drift, preserving alignment between generated bundle validation, acceptance, final evidence output, and Docker fallback mounts.
