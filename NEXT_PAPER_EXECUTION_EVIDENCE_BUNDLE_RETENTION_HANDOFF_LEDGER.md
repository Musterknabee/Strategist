# Next slice ledger: paper retention handoff capsule and verification

## Slice
Added a terminal, read-only handoff capsule and independent verifier for the paper evidence-chain retention signoff.

## Scope
- Writes a final custody-transfer handoff artifact only from a verified retention signoff.
- Recomputes and stores a custodian handoff statement digest.
- Independently verifies the handoff artifact digest, handoff statement digest, and referenced signoff-verification artifact digest.
- Surfaces handoff and handoff-verification status in the cockpit payload, daily operator-run summary, CLI, and frontend console.
- Preserves the paper-only/read-only authority boundary.

## Authority boundary
This slice is read-only. It does not copy retained files, submit broker orders, mutate any ledger, promote strategies, or grant execution authority.

## CLI
```bash
strategy-validator-paper-broker handoff-evidence-bundle-retention
strategy-validator-paper-broker verify-evidence-bundle-retention-handoff
```

Optional explicit sources:

```bash
strategy-validator-paper-broker handoff-evidence-bundle-retention \
  --retention-signoff-verification-artifact artifacts/paper_broker/<tracking_id>/paper_execution_evidence_bundle_retention_signoff_verification.json \
  --custodian-id archive-vault \
  --handoff-note "custody transfer approved"

strategy-validator-paper-broker verify-evidence-bundle-retention-handoff \
  --retention-handoff-artifact artifacts/paper_broker/<tracking_id>/paper_execution_evidence_bundle_retention_handoff.json
```

## Validation
- `python -m compileall strategy_validator`
- targeted app/CLI tests for retention handoff and handoff verification
- regression tests for retention signoff verification
- cockpit and daily operator-run regressions

## Frontend
The paper execution terminal console now includes:
- `Evidence-chain retention handoff`
- `Evidence-chain retention handoff verification`

Both panes remain read-plane only and only display artifact state, trust banners, hash checks, counts, blockers, and warnings.
