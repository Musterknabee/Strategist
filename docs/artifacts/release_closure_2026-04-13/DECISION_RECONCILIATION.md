# Decision Reconciliation

## Machine Facts
- **Verification Status**: `INCOMPLETE`
- **Machine Decision**: `BLOCK_AND_INVESTIGATE`
- **Primary Classification**: `EVIDENCE_INTEGRITY_FAILURE`
- **Secondary Classifications**: `DATA_QUALITY_DEGRADATION, POLICY_MISMATCH`
- **Governed Exception Eligible**: `False`

## Canonical Boundary
- Signoff conclusions must be derived from the verified closure snapshot and its referenced review artifact.
- Non-canonical or stale artifact chains must not be used to reinterpret the current release stance.

## Why this stance follows
- Canonical closure evidence is not fully verified; release conclusions cannot be promoted from narrative evidence.
- Closure snapshot is incomplete because referenced rollout artifacts are missing.

## Operator next step
- Repair the canonical evidence chain and regenerate the closure snapshot.
- Re-run closure snapshot verification before updating signoff documents.

## Missing artifacts
- pilot_followup_alpaca_long.jsonl
- pilot_followup_alpaca_off_hours.jsonl
- pilot_followup_alpaca_sym_QQQ.jsonl
