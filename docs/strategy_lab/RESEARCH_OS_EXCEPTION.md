# Research OS Governed Exceptions

Research OS governed exceptions are time-bounded, digest-linked operator annotations over the latest Research OS policy gate.

They are intentionally conservative:

- `WARN` policy gates can receive an `ACTIVE` exception with explicit constraints and expiry.
- `PASS` policy gates do not need an exception and produce `NOT_APPLICABLE`.
- `BLOCK` or `EMPTY` policy gates cannot be bypassed; exception records are rejected and preserve the blockers.

## Non-authority

A governed exception does **not**:

- approve deployment,
- enable live trading,
- submit broker orders,
- add browser order controls,
- certify profitability,
- mutate the ledger.

## CLI

```bash
strategy-validator-research-os-exception request \
  --exception-id daily-restricted-evidence-review \
  --operator-id local-operator \
  --rationale "Paper-only restricted evidence acknowledged; not deployment approval" \
  --ttl-hours 24 \
  --constraint "Resolve missing provider paper loop before release review" \
  --overwrite \
  --json
```

Read latest:

```bash
strategy-validator-research-os-exception latest --json
```

Demo:

```bash
python scripts/run_research_os_exception_demo.py --overwrite --json
```

## Artifact layout

```text
artifacts/research_os_exceptions/
  exceptions/{exception_id}/research_os_exception_record.json
  latest/research_os_exception_record.json
  latest/latest_ref.json
```

## Cockpit

Read-plane route:

```text
GET /ui/research-os/exceptions/latest
```

Frontend route:

```text
/research-exception
```

The page shows status, decision, source policy gate, expiry, constraints, covered warnings, residual warnings/blockers, and SHA-256 digests.
