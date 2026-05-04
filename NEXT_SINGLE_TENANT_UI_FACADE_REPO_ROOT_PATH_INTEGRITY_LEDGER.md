# Next Slice Ledger: UI Facade Repo-Root Path-Integrity Hardening

## Objective

Close the UI facade snapshot bypass where `--output` was guarded, but `--repo-root` could still be resolved through a symlink before route discovery and public facade inventory generation.

## Changes

- Hardened `scripts/ui_facade_contract_snapshot.py` with `_validate_repo_root()`.
- Reused `scripts._path_integrity.safe_input_dir()` so caller-provided repo roots preserve symlink visibility.
- Applied repo-root validation to both CLI execution and programmatic `build_ui_facade_contract_snapshot()` calls.
- Added regression coverage in `tests/constitutional/test_ui_facade_contract_snapshot_path_integrity.py`.

## New Fail-Closed Codes

- `UI_FACADE_REPO_ROOT_IS_SYMLINK`
- `UI_FACADE_REPO_ROOT_PARENT_IS_SYMLINK`

## Operator Impact

The UI public facade snapshot can no longer be checked or regenerated against a repository root reached through filesystem indirection.
