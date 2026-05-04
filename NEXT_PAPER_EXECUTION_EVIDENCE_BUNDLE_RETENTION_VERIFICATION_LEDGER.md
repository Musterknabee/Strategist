# Next Slice Ledger — Paper Evidence-Chain Retention Verification

## Scope

Added a read-only verifier for paper evidence-chain retention receipts.

## Guarantees

- Recomputes retention receipt artifact digest.
- Recomputes retention index digest.
- Rechecks every retained artifact file digest and file size.
- Does not copy retained files.
- Does not submit orders.
- Does not mutate the adjudication ledger.
- Surfaces verification state through CLI, paper cockpit, daily operator summary, and frontend types/page.

## Entry Points

- Application: `strategy_validator/application/paper_execution_evidence_bundle_retention_verification.py`
- CLI: `strategy-validator-paper-broker verify-evidence-bundle-retention`
- Tests:
  - `tests/application/test_paper_execution_evidence_bundle_retention_verification.py`
  - `tests/cli/test_paper_broker_verify_evidence_bundle_retention.py`

## Status Semantics

- `PASS`: receipt hash, index, and retained file entries still match.
- `FAIL`: receipt, index, missing files, file digest, or size checks failed.
- `UNKNOWN`: no usable source receipt was available.
