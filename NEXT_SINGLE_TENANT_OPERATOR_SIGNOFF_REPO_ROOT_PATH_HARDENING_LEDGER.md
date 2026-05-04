# Next Slice Ledger: Operator Signoff Repo-Root Path Hardening

## Slice

Hardened `scripts/generate_operator_deployment_signoff.py` so `--repo-root` is validated without following symlinks before git metadata lookup or signoff artifact generation.

## Why

The signoff evidence/input/output paths were already guarded, but `--repo-root` still used `Path.resolve()` directly. That could hide a symlinked repository root when deriving git commit metadata for final operator approval evidence.

## Changes

- Reused the signoff script's symlink-preserving directory validator for `--repo-root`.
- Added fail-closed path errors before output materialization.
- Added constitutional regression coverage for:
  - symlinked `--repo-root`
  - repo root under a symlinked parent directory

## New error codes

- `SIGNOFF_REPO_ROOT_IS_SYMLINK`
- `SIGNOFF_REPO_ROOT_PARENT_IS_SYMLINK`
- `SIGNOFF_REPO_ROOT_NOT_DIRECTORY`

## Validation

Validated with the focused signoff path-integrity test suite, source health, repository truth check, compileall, and archive verification.
