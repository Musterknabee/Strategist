# Next Single-Tenant Restore Backup Path Contract Ledger

## Scope

This slice hardens the generated single-tenant break-glass restore helper so it cannot accidentally restore from a host-local path or write pre-restore evidence outside the mounted backup volume.

## Changes

- `commands/restore-ledger.sh` now defines `BACKUP_ROOT=/var/backups/strategy-validator`.
- `STRATEGY_VALIDATOR_LEDGER_BACKUP_PATH` must be a container-visible `.sqlite3` path under that backup root.
- `STRATEGY_VALIDATOR_PRE_RESTORE_BACKUP_DIR` must be the backup root or a child directory under it.
- Bundle verification now rejects regenerated/tampered restore helpers that drop these guards even when `manifest.json` is refreshed.
- Deployment docs now spell out that rollback paths are container-visible backup-volume paths, not arbitrary host paths.

## Operator invariant

A restore is break-glass only and must use the same named backup volume that the generated API/helper containers mount at `/var/backups/strategy-validator`.
