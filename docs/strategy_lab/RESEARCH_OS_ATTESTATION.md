# Research OS Closure Verification and Operator Attestation

Research OS attestation is an evidence-only layer on top of the Research OS closure manifest. It verifies that the closure manifest still matches the artifacts it digest-linked, then records an operator acknowledgement or restricted signoff.

It does **not** approve deployment. It does **not** authorize live trading. It does **not** submit broker orders. It does **not** certify profitability.

## What it verifies

The verifier reads the latest closure manifest from:

```text
artifacts/research_os_closure/latest/research_os_closure_manifest.json
```

It checks:

- closure manifest `manifest_sha256`
- every artifact digest captured by the closure manifest
- whether digest-linked artifacts disappeared after closure
- whether digest-linked artifacts became unreadable
- whether known secret markers appear in closure or artifact JSON
- safety flags such as `no_live_trading`, `no_broker_orders`, and `deployment_approval_unchanged`

If a digest-linked artifact changes after closure, the verification status becomes `TAMPERED`.

## CLI

Verify latest closure evidence and write the latest verification artifact:

```bash
strategy-validator-research-os-attestation verify \
  --write \
  --overwrite \
  --json
```

Write an operator attestation:

```bash
strategy-validator-research-os-attestation attest \
  --operator-id local-operator \
  --decision ACCEPTED_WITH_RESTRICTIONS \
  --rationale "Paper-only evidence acknowledged; not deployment approval" \
  --constraint "No live trading" \
  --constraint "No broker orders" \
  --overwrite \
  --json
```

Available decisions:

- `ACKNOWLEDGED`
- `ACCEPTED_WITH_RESTRICTIONS`
- `REJECTED`
- `BLOCKED`

If verification is not `VERIFIED`, the attestation is forced to `BLOCKED`.

## Artifact layout

```text
artifacts/research_os_attestation/
  verifications/{verification_id}/closure_verification_result.json
  attestations/{attestation_id}/operator_attestation.json
  latest/closure_verification_result.json
  latest/operator_attestation.json
```

## API and cockpit

The API exposes:

```text
GET /ui/research-os/attestation/latest
```

The frontend cockpit exposes:

```text
/research-attestation
```

`/research-os` also summarizes the latest verification and attestation when present.

## Safety boundaries

- read-plane/evidence-plane only
- no live trading
- no broker orders
- no browser order controls
- no ledger writer authority
- no API tokens or provider secrets in artifacts/UI
- deployment approval semantics unchanged
