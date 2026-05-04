# Next slice ledger: paper retention signoff verification

## Slice

Added an independent read-only verifier for the paper evidence-chain retention signoff certificate.

## Scope

- Verifies the retention signoff artifact digest.
- Recomputes and verifies the embedded operator signoff statement digest.
- Recomputes and verifies the referenced retention-verification artifact digest.
- Checks signoff/source status, trust banners, retention entry counts, missing counts, and digest mismatch counts.
- Surfaces the verification result in the paper-execution cockpit, daily operator-run summary, CLI, and frontend payload/types.

## Authority boundary

This slice is read-only. It does not copy retained files, submit broker orders, mutate the ledger, promote strategies, or grant execution authority.

## CLI

```bash
strategy-validator-paper-broker verify-evidence-bundle-retention-signoff
```

Optional explicit source:

```bash
strategy-validator-paper-broker verify-evidence-bundle-retention-signoff \
  --retention-signoff-artifact artifacts/paper_broker/<tracking_id>/paper_execution_evidence_bundle_retention_signoff.json
```

## Validation

Targeted validation performed with plugin autoload disabled:

- `tests/application/test_paper_execution_evidence_bundle_retention_signoff_verification.py`
- `tests/cli/test_paper_broker_verify_evidence_bundle_retention_signoff.py`
- surrounding retention/signoff app and CLI regressions
- broader paper evidence-chain app regressions
- paper-broker CLI wildcard regressions
- cockpit and daily operator-run regressions
