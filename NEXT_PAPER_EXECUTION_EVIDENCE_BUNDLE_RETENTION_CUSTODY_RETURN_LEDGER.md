# Next Slice Ledger — Paper Evidence Bundle Retention Custody Return

## Slice

`retention custody return + independent return verification`

## Chain extension

```text
retention custody archive verification
→ custody retrieval
→ custody retrieval verification
→ custody return
→ custody return verification
```

## Feature value

After a retained archive is retrieved for operator review, the repository can now produce a read-only custody return record proving the evidence was returned to its declared custody location, then independently verify that return artifact and statement digest.

## Files added

- `strategy_validator/application/paper_execution_evidence_bundle_retention_custody_return.py`
- `strategy_validator/application/paper_execution_evidence_bundle_retention_custody_return_verification.py`
- `tests/application/test_paper_execution_evidence_bundle_retention_custody_return.py`
- `tests/cli/test_paper_broker_retention_custody_return.py`

## Files wired

- `strategy_validator/contracts/paper_execution.py`
- `strategy_validator/contracts/daily_operator_run.py`
- `strategy_validator/application/paper_execution_cockpit.py`
- `strategy_validator/application/daily_operator_run_projection.py`
- `strategy_validator/cli/paper_broker.py`
- `ui/strategist-web/app/paper-execution/page.tsx`

## CLI

```bash
strategy-validator-paper-broker return-evidence-bundle-retention-custody-retrieval
strategy-validator-paper-broker verify-evidence-bundle-retention-custody-return
```

## Validation

```bash
python -m compileall -q strategy_validator
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  tests/application/test_paper_execution_evidence_bundle_retention_custody_return.py \
  tests/cli/test_paper_broker_retention_custody_return.py \
  tests/application/test_paper_execution_evidence_bundle_retention_custody_retrieval.py \
  tests/cli/test_paper_broker_retention_custody_retrieval.py \
  tests/application/test_paper_execution_cockpit.py \
  tests/application/test_daily_operator_run_projection.py
```

Result: `13 passed`.
