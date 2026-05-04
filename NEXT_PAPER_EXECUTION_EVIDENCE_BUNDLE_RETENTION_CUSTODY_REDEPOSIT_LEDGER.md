# Next Slice Ledger — Paper Execution Evidence Bundle Retention Custody Redeposit

## Feature

Adds a read-only retention custody redeposit layer after verified custody return.

The chain extension is:

```text
custody retrieval
→ custody retrieval verification
→ custody return
→ custody return verification
→ custody redeposit
→ custody redeposit verification
```

## Authority boundary

- Paper trading only.
- No live trading authority.
- No browser order authority.
- No broker/network calls.
- No file-copy side effect; the artifact records a redeposit certificate and verifier only.
- No validator ledger mutation.

## Implemented surfaces

- Application artifact writer:
  - `strategy_validator/application/paper_execution_evidence_bundle_retention_custody_redeposit.py`
- Independent verifier:
  - `strategy_validator/application/paper_execution_evidence_bundle_retention_custody_redeposit_verification.py`
- CLI commands:
  - `strategy-validator-paper-broker redeposit-evidence-bundle-retention-custody-return`
  - `strategy-validator-paper-broker verify-evidence-bundle-retention-custody-redeposit`
- Contracts:
  - `PaperExecutionEvidenceBundleRetentionCustodyRedepositArtifact`
  - `PaperExecutionEvidenceBundleRetentionCustodyRedepositView`
  - `PaperExecutionEvidenceBundleRetentionCustodyRedepositVerificationArtifact`
  - `PaperExecutionEvidenceBundleRetentionCustodyRedepositVerificationView`
- Read planes:
  - paper execution cockpit summary/payload
  - daily operator run summary/recommended action path
- Frontend:
  - paper execution cockpit panels for return/redeposit/redeposit verification
- Tests:
  - app happy path, missing-source block, tamper detection
  - CLI round trip and help registration

## Validation

```bash
python -m compileall -q strategy_validator tests
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  tests/application/test_paper_execution_evidence_bundle_retention_custody_return.py \
  tests/cli/test_paper_broker_retention_custody_return.py \
  tests/application/test_paper_execution_evidence_bundle_retention_custody_redeposit.py \
  tests/cli/test_paper_broker_retention_custody_redeposit.py \
  tests/application/test_paper_execution_cockpit.py \
  tests/application/test_daily_operator_run_projection.py
```

Result: `13 passed`.
