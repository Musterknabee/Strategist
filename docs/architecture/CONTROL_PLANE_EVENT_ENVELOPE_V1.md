# Control Plane Event Envelope v1

The control-plane event envelope is the canonical, transport-neutral identity wrapper for operator/control-plane outputs before they are rendered into JSON/Markdown artifacts.

## Purpose

Filesystem artifacts remain useful operator renderings, but they should not be the long-term source of truth. The envelope records:

- `event_type`
- `producer`
- `occurred_at_utc`
- optional actor, target, policy fingerprint, idempotency key, and evidence references
- canonical payload digest
- payload body

The digest is computed from canonical JSON and can be verified without ledger state.

## Current implementation

- Contract: `strategy_validator/contracts/control_plane_event_envelope.py`
- Rendering helper: `strategy_validator/control_plane/materialization.py`
- First sidecar event producer: `strategy_validator/control_plane/operator_decision_execution.py`

`operator_decision_execution` now emits:

- `ORACLE_OPERATOR_DECISION_EXECUTION.json`
- `ORACLE_OPERATOR_DECISION_EXECUTION.md`
- `ORACLE_OPERATOR_DECISION_EXECUTION.event.json`

The `.event.json` file is intentionally a sidecar in this slice. It does not yet mutate the ledger. The next convergence step is to make selected workflows event-first and treat JSON/Markdown artifacts as projections/renderings.


## Event-backed materialization primitive

`strategy_validator.control_plane.materialization.write_event_backed_json_markdown_artifacts`
is the first event-first rendering primitive. It builds a
`ControlPlaneEventEnvelope` from the canonical payload, writes the `.event.json`
sidecar, and then renders the JSON/Markdown operator artifacts through the same
shared materialization path used by legacy file-first workflows.

As of this slice, `strategy_validator/control_plane/operator_decision_execution.py`
uses the event-backed writer and emits:

- `ORACLE_OPERATOR_DECISION_EXECUTION.event.json`
- `ORACLE_OPERATOR_DECISION_EXECUTION.json`
- `ORACLE_OPERATOR_DECISION_EXECUTION.md`

The event sidecar is still filesystem-backed. It is the transition shape for a
future ledger-backed control-plane event stream; it is not yet a ledger commit.


## Slice 21: event journal bridge and sidecar replay

Control-plane event sidecars can now be replayed with `build_control_plane_event_sidecar_replay_report(...)` and materialized as a projection artifact with `write_control_plane_event_sidecar_replay_report(...)`. Event-backed materializers may opt in to durable operator journal recording via `append_to_operator_journal=True`; this writes the verified event envelope to `operator_action_events` as a `control-plane-event` action while preserving the `.event.json` sidecar as a filesystem rendering.

The production smoke script also accepts `--restore-drill-backup-path` plus `--restore-drill-database-path` for a verified restore drill that can be paired with readiness checks.

## Sidecar replay and journal reconciliation

The current transition state has two control-plane event surfaces:

1. `*.event.json` sidecars emitted next to derived JSON/Markdown artifacts.
2. Optional `control-plane-event` entries appended to the operator action journal.

Use the sidecar CLI to verify sidecars without requiring ledger access:

```bash
strategy-validator-control-plane-event-sidecars replay \
  --event-root docs/artifacts \
  --output-path scratch/control-plane-event-sidecar-replay.json \
  --fail-on-rejected \
  --json
```

Use reconciliation when a workflow also records envelopes into the operator action journal:

```bash
strategy-validator-control-plane-event-sidecars reconcile \
  --event-root docs/artifacts \
  --output-path scratch/control-plane-event-reconciliation.json \
  --fail-on-drift \
  --json
```

Reconciliation is intentionally stricter than replay. A verified sidecar without a matching journal event is reported as `SIDECAR_ONLY`; a journaled event without a sidecar is reported as `JOURNAL_ONLY`; payload digest disagreement is reported as `DIGEST_MISMATCH`. Until every control-plane workflow is ledger-backed, `SIDECAR_ONLY` can be expected for sidecar-only workflows.

## Operator action chain verification

Control-plane event sidecars can be reconciled against durable journal entries, but journal trust also depends on the append-only operator-action chain. The canonical operator check is:

```bash
strategy-validator-ledger-ops verify-operator-actions --database-path <ledger.sqlite3> --json
```

This validates `sequence_number`, `previous_event_hash`, and event hash recomputation for `operator_action_events`, including journaled `control-plane-event` rows created by event-backed materializers.

## Reconciliation chain verification

`strategy-validator-control-plane-event-sidecars reconcile --verify-operator-chain` verifies the `operator_action_events` hash chain as part of sidecar/journal reconciliation. A reconciliation report is only operationally clean when sidecar events match journaled `control-plane-event` entries and the underlying operator action journal chain is clean.

Use `--fail-on-drift` for CI/operator gates that should fail on `SIDECAR_ONLY`, `JOURNAL_ONLY`, `DIGEST_MISMATCH`, invalid sidecars, or chain-verification failure. Use `--verify-operator-chain` when the caller wants a distinct non-zero exit for chain integrity failure.

## Semantic submission contract split

Validator-ingress acceptance and final validator-submission contracts now live in `strategy_validator/contracts/semantic_validator_submission.py`. `strategy_validator/contracts/semantic.py` re-exports them as a compatibility facade; new code should import from the stage module directly.

### Control-plane event projection index

After replay/reconciliation, operators can build a compact projection index that joins every
`*.event.json` sidecar to its durable `control-plane-event` journal entry:

```bash
strategy-validator-control-plane-event-sidecars index \
  --event-root docs/artifacts \
  --output-path scratch/control-plane-event-index.json \
  --fail-on-drift \
  --json
```

The index emits `control_plane_event_projection_index/v1` with per-event status,
source count, payload digest, and `fully_indexed` state. Treat `SIDECAR_ONLY`,
`JOURNAL_ONLY`, `DIGEST_MISMATCH`, or an unclean operator journal chain as drift
until explicitly waived.

