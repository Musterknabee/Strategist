# Candidate lifecycle (paper / research)

**Scope:** Research and paper tracking only. **No live trading.** **No profitability guarantee.** Evidence artifacts are advisory; the orchestrator/ledger remains authoritative for deployment decisions.

## States

Lifecycle states are defined in `strategy_validator/contracts/candidate_lifecycle.py` and assessed into `artifacts/paper_tracking/{tracking_id}/lifecycle_assessment.json`.

## CLI

- `strategy-validator-paper-track assess --tracking-id <id> --json`
- `strategy-validator-paper-track list --json`

## Read-plane / UI

- `GET /ui/paper-tracking/latest` and `GET /ui/paper-tracking/{tracking_id}` include lifecycle fields when assessments exist.
- Strategist Terminal **Paper tracking** page shows the lifecycle rail and disclaimers (promotion review is **not** live approval).

## Limitations

Synthetic/demo candidates cannot reach `PROMOTION_REVIEW_READY`. Duplicative portfolio signals add governance blockers unless explicitly excepted elsewhere.

## Next graduation step

Human promotion review and deployment evidence reruns remain outside this artifact path.
