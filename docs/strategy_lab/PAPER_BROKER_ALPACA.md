# Paper broker (Alpaca) — evidence only

**Scope:** Optional Alpaca **paper** endpoint integration. **No live trading.** **No browser order buttons.** `PERSONAL_LIVE_APPROVED` must remain false for governed deployments.

## Policy

- `ALPACA_TRADING_MODE` must be `paper`.
- Base URL must be a paper host (e.g. `https://paper-api.alpaca.markets`).
- CLI-only submission behind `--confirm-paper`.

## CLI

```bash
strategy-validator-paper-broker status --env-file deployment.env --json
strategy-validator-paper-broker status --env-file deployment.env --output-root artifacts/paper_broker --json
# Optional: authenticated account probe when policy is PAPER_READY (trusted host only):
strategy-validator-paper-broker status --env-file deployment.env --output-root artifacts/paper_broker --allow-network --json
strategy-validator-paper-broker positions --env-file deployment.env --json
strategy-validator-paper-broker dry-run-order --tracking-id <id> --json
strategy-validator-paper-broker submit-paper-order --tracking-id <id> --confirm-paper --env-file deployment.env --json
```

Artifacts:

- `artifacts/paper_broker/latest/paper_broker_status.json` — policy + optional redacted account summary (from `status --output-root`).
- `artifacts/paper_broker/{tracking_id}/paper_order_submission.json` — CLI paper order evidence (redacted fields only).

## Read-plane / UI

`GET /ui/paper-broker/status` returns **env-derived policy** (no authenticated broker calls from FastAPI). Paper tracking page shows the policy strip.

## Limitations

Paper fills are evidence, not authority. Does not imply live readiness.

## Next graduation step

Keep all authenticated broker traffic on trusted hosts via CLI; never expose API secrets to the browser.
