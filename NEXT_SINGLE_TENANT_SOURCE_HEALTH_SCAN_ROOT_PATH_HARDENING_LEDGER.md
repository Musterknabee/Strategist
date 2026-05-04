# Next Slice: Source Health Scan-Root Path Hardening

## Summary

Hardened `scripts/source_health.py` so explicit scan roots are treated as repository-relative security boundaries instead of being normalized through `Path.resolve()`. The source-health gate now rejects symlinked scan roots, scan roots under symlinked parent directories, absolute scan roots, and parent-traversal roots before parsing any files.

This closes a gap where `--repo-root` was protected, but individual source-health roots could still silently follow filesystem indirection or escape the reviewed repository envelope.

## Changed files

- `scripts/source_health.py`
- `tests/constitutional/test_source_health_scan_root_path_integrity.py`

## New fail-closed codes

- `SOURCE_HEALTH_SCAN_ROOT_IS_SYMLINK`
- `SOURCE_HEALTH_SCAN_ROOT_PARENT_IS_SYMLINK`
- `SOURCE_HEALTH_SCAN_ROOT_ABSOLUTE`
- `SOURCE_HEALTH_SCAN_ROOT_PARENT_TRAVERSAL`

## Validation

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/constitutional/test_source_health_scan_root_path_integrity.py`
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/constitutional/test_source_health_scan_root_path_integrity.py tests/constitutional/test_ci_gate_repo_root_path_integrity.py tests/constitutional/test_ui_public_facade_snapshot_assets.py`
- `python scripts/source_health.py --json`
- `python scripts/source_health.py --repo-owned --json`
- `python scripts/repository_truth_check.py --json`
- `python scripts/migration_truth_check.py --json`
- `python -m compileall -q strategy_validator scripts tests`
