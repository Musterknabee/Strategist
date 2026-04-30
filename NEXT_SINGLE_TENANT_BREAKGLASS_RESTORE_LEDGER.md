# Next single-tenant hardening slice — break-glass restore safety

## Scope

This slice hardens the single-tenant rollback path without changing the backend authority model or claiming frontend / multi-tenant readiness.

## Changes

- `strategy_validator/cli/ledger_ops.py`
  - Added `ledger_ops_pre_restore_backup/v1` evidence for overwrite restores.
  - `restore_ledger_database(..., allow_overwrite=True)` now preserves the displaced destination ledger before replacement.
  - Restore reports now include `restored_sha256` and pre-restore backup path/size/SHA-256.
  - CLI adds `--pre-restore-backup-dir` for durable operator-controlled preservation.

- `strategy_validator/cli/single_tenant_deployment_bundle.py`
  - Fixed duplicate systemd port binding line.
  - Hardened generated `commands/restore-ledger.sh` with `STRATEGY_VALIDATOR_CONFIRM_API_STOPPED=YES` and `STRATEGY_VALIDATOR_PRE_RESTORE_BACKUP_DIR`.
  - Generated restore helper passes `--pre-restore-backup-dir` into `strategy-validator-ledger-ops restore`.

- `docs/deployment/*`
  - Documented break-glass restore semantics and pre-restore backup evidence.

- `tests/constitutional/*`
  - Added/updated coverage for restore preservation and generated bundle restore-script posture.

## Validation performed in sandbox

- `scripts/source_health.py --json`: PASS
- `scripts/repository_truth_check.py --json`: PASS
- `scripts/migration_truth_check.py --json`: PASS
- Generated a single-tenant bundle and verified restore helper/systemd content statically.
- `scripts/package_repo.py --output ... --json`: PASS
- `scripts/verify_repo_archive.py ... --json`: PASS
- `unzip -t`: PASS

## Environment limitation

Full pytest execution is blocked in this sandbox because the environment has Pydantic v1, while the repository requires Pydantic v2 (`model_validator`). The changes were kept compatible with the existing project contract and validated through static repo gates plus targeted generated-artifact checks.
