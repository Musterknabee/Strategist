# Next Slice Ledger — CI Gate Repo-Root Path-Integrity Hardening

## Slice

Hardened fast CI/release gate scripts so an explicit `--repo-root` cannot be supplied through filesystem indirection.

## Files changed

- `scripts/source_health.py`
- `scripts/repository_truth_check.py`
- `scripts/environment_check.py`
- `tests/constitutional/test_ci_gate_repo_root_path_integrity.py`

## New fail-closed behavior

The scripts now preserve caller-provided path visibility and reject symlinked repository roots before scanning source, reading `pyproject.toml`, or evaluating environment metadata.

Representative structured codes:

- `SOURCE_HEALTH_REPO_ROOT_IS_SYMLINK`
- `REPOSITORY_TRUTH_REPO_ROOT_IS_SYMLINK`
- `ENVIRONMENT_CHECK_REPO_ROOT_IS_SYMLINK`

## Validation intent

This closes a CI/release-gate bypass where the snapshot/archive tooling had repo-root path guards, but the foundational health/truth/environment gates still resolved explicit repo roots through symlinks.
