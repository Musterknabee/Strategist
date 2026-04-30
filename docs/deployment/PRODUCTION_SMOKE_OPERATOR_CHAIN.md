# Production smoke operator-chain extension

Run the backend production smoke path together with restore verification and operator-action chain/index checks:

```bash
python scripts/production_smoke_check.py \
  --base-url http://127.0.0.1:8000 \
  --restore-drill-backup-path /var/backups/strategy-validator/latest.sqlite3 \
  --restore-drill-database-path /tmp/strategy-validator-restore-drill.sqlite3

python -m strategy_validator.cli.ledger_ops verify-operator-actions \
  --database-path /var/lib/strategy-validator/ledger.sqlite3 \
  --json

python -m strategy_validator.cli.operator_action_event_index \
  --database-path /var/lib/strategy-validator/ledger.sqlite3 \
  --output-path scratch/operator-action-event-index.json \
  --json
```

## Operator-action event index

After chain verification, materialize the compact operator-action journal index:

```bash
strategy-validator-ledger-ops index-operator-actions \
  --database-path /var/lib/strategy-validator/ledger.sqlite3 \
  --output-path scratch/operator-action-event-index.json \
  --json
```

This artifact should be archived with the control-plane diagnostics bundle. It is intentionally derived from the ledger and can be regenerated from the same database snapshot.

## Markdown summary artifact

When running operator-chain production smoke diagnostics, also pass `--summary-markdown-output-path scratch/production-smoke-summary.md`. The summary is derived from the same JSON payload and should be uploaded beside the machine-readable artifacts.
