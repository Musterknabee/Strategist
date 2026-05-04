# Promotion review packet

**Scope:** Human-review evidence only. **Does not approve live trading.** **No ledger mutation.**

## Artifact

`artifacts/paper_tracking/{tracking_id}/promotion_review_packet.json` produced when eligible.

## CLI

- `strategy-validator-paper-track promotion-packet --tracking-id <id> --json`

## Read-plane / UI

Summary fields are merged into paper tracking payloads. Strategist Terminal surfaces packet indicators on the Paper and Strategy Lab views where linked.

## Limitations

`READY_FOR_HUMAN_REVIEW` requires lifecycle `PROMOTION_REVIEW_READY`. Synthetic paths always `DO_NOT_PROMOTE`.

## Next graduation step

Formal human review and any deployment workflow remain manual and governed outside research tooling.
