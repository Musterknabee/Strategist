# Audit timeline & forensic diff (cockpit)

The **Audit trail & forensic diff** pane (`AuditForensicPane`, `data-testid="cockpit-audit-forensic"`) merges:

1. **`/ui/evidence-chain`** — `timeline.entries` (decision ledger + operator action journal), sorted by `created_at_utc`, plus stream fallbacks when the timeline array is empty.  
2. **Supplemental artifact markers** — latest timestamps from read-plane payloads already fetched by the home cockpit: `/ui/evidence`, Research OS (release readiness, handoff, signoff, review journal, export, drift), and `/ui/paper-execution/latest`.

## Rules

- **Read-plane only** — no ledger writes, no file writes, no shell execution.  
- **Chain semantics** follow backend `chained` and `issue_codes` only; the UI does not re-verify hashes.  
- **Forensic diffs** — pairwise tails for promotion ledger and operator journal **only when at least two events** of that family exist in the merged window; otherwise **NO_BASELINE**. Registry digest longitudinal diff is **NO_BASELINE** (APIs expose a single current snapshot).  
- **Filters** narrow the table; they do not change backend data.

Implementation: `ui/strategist-web/lib/operator/audit-timeline-model.ts`, `ui/strategist-web/components/cockpit/AuditForensicPane.tsx`.

## Related

- Evidence packet checklist: `docs/EVIDENCE_PACKET_RUNBOOK_VIEWER.md`  
- CLI / artifact mapping: `docs/LOCAL_OPS_COMMAND_CENTER.md`  
