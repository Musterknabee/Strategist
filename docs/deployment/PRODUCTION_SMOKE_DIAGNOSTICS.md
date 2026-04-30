# Production smoke diagnostics

The production smoke diagnostics workflow is intentionally non-blocking while the backend runtime envelope is still converging. It collects JSON and Markdown artifacts that let an operator inspect readiness without treating every drift signal as a release blocker.

## Runtime smoke

```bash
python scripts/production_smoke_check.py \
  --verify-operator-action-chain \
  --operator-action-index-output-path scratch/operator-action-event-index.from-smoke.json \
  --summary-markdown-output-path scratch/production-smoke-summary.md \
  > scratch/production-smoke-readiness.json
```

This combines runtime readiness, optional operator-action chain verification, and optional operator-action index materialization into one `production_smoke_check_diagnostics/v1` payload.

## Deployment-tier smoke

```bash
python scripts/production_smoke_check.py \
  --deployment-tier \
  --repo-root . \
  --summary-markdown-output-path scratch/production-smoke-deployment-summary.md \
  > scratch/production-smoke-deployment-readiness.json
```

Use the Markdown summary as the human review surface and the JSON payloads as machine-readable evidence.

## Blocking policy

The CI workflow uses explicit `continue-on-error: true` for these artifact-only diagnostic steps and uploads artifacts. Promote it to a hard gate only after the deployment environment has stable token, ledger, restore, and operator-action journal fixtures.
