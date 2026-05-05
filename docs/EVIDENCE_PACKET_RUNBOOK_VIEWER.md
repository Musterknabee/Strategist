# Evidence packet & runbook viewer (cockpit)

The **Evidence packet & runbook checklist** pane on the home cockpit (`EvidenceRunbookPane`, `data-testid="cockpit-evidence-runbook"`) is a **read-plane presentation layer** only. It normalizes existing GET responses:

- `/ui/evidence` — dashboard registry, deployment cockpit fields, `registry_table` rows  
- `/ui/evidence-chain` — ledger / operator-action chain summary  
- `/ui/operator-actions` — projection index counts and chain health  
- `/ui/research-os/release-readiness/latest`, `/handoff/latest`, `/handoff-signoff/latest`, `/review-journal/latest`  
- `/ui/research-os/export/latest` — portable export manifest presence  

## Semantics

1. **No deployment or release approval** is implied by the checklist or by copied markdown.  
2. **Operator signoff** still requires **backend evidence** (disk manifests, CLI-built artifacts, ledger projections) — not UI state alone.  
3. **Copy markdown** uses the browser clipboard only: **no file writes**, **no shell execution**.  
4. **UNKNOWN / MISSING / STALE** rows mean incomplete or degraded read models — treat as **review-required**, not PASS.

Implementation: `ui/strategist-web/lib/operator/evidence-packet-model.ts` and `ui/strategist-web/components/cockpit/EvidenceRunbookPane.tsx`. Command provenance for rows that map to the local-ops registry uses `ui/strategist-web/lib/operator/local-ops-command-registry.json` (see `docs/LOCAL_OPS_COMMAND_CENTER.md`).

## Related docs

- `docs/AUDIT_TIMELINE_FORENSIC_COCKPIT.md` — chronological audit timeline + forensic diff pane  
- `docs/LOCAL_OPS_COMMAND_CENTER.md` — CLI ↔ evidence ↔ cockpit mapping  
- `docs/deployment/SINGLE_TENANT_DEPLOYMENT_READINESS.md` — deployment evidence flow  
- `docs/OPERATOR_RUNBOOK.md` — operator posture and procedures  
