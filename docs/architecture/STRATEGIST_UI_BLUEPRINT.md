# Strategist Web UI Blueprint

## Goal

Establish a governed web control surface for Strategist that:

- reads only from projection-shaped read planes
- sends writes only through backend command routes or application facades
- enforces Tribunal blindness at route, payload, and component boundaries
- keeps evidence provenance visible throughout the operator experience

## Architectural laws

1. **Read law** — the UI reads from `/ui/*` read-plane routes or the Next.js BFF only.
2. **Write law** — the UI never writes to the database; it submits commands to backend mutation routes only.
3. **Blindness law** — Tribunal routes are never hydrated with Validator-only quantitative payloads.
4. **Evidence law** — critical UI cards expose verification state, freshness, and provenance.
5. **Fallback law** — stale or missing projections render visible degraded states.

## Delivery slices

### Slice 1 — contracts and shell
- Bounded Next.js app under `ui/strategist-web` (workboard read-plane slice; see `docs/deployment/FRONTEND_OPERATOR_CONSOLE.md`)
- Add stable backend UI read-plane routes under `strategy_validator/api/routes/ui.py`
- Add workboard and burn-in feature folders
- Add projection polling with TanStack Query and a domain-boundary provider

### Slice 2 — operator pack flows
- Pack preview drawer
- Queue filters and search
- Projection freshness overlays
- Timeline and evidence tabs for a pack detail route

### Slice 3 — validator diagnostics
- Expanded CPCV / calibration / realism panels
- provider-path diagnostics
- artifact provenance drill-down

### Slice 4 — tribunal and evidence planes
- blindness-safe tribunal routes
- doctrine memory panels
- evidence backbone explorer
- lineage / as-of join inspection

### Slice 5 — governed commands
- claim / renew / acknowledge / reroute actions
- command receipts and projection invalidation
- audit-visible operator actions

## Frontend structure

```text
ui/strategist-web
├── app
│   ├── (console)
│   │   ├── workboard
│   │   ├── validator/burn-in
│   │   ├── tribunal
│   │   └── evidence
│   └── api/ui
├── components
│   ├── providers
│   └── ui
├── features
│   ├── control-plane
│   ├── validator
│   └── shared
├── lib
│   ├── contracts
│   ├── mocks
│   ├── server
│   └── utils
└── public
```

## Backend alignment

The UI routes added in this slice are intentionally thin:

- `/ui/workboard` → `strategy_validator.application.ui_views.build_ui_workboard_payload`
- `/ui/burnin` → `strategy_validator.application.ui_views.build_ui_burnin_payload`

This keeps the frontend bound to stable read-plane contracts instead of internal module composition.

## Backend facade contract snapshot

The backend publishes and snapshots the public UI facade; the `ui/strategist-web`
package binds to this contract at runtime:

- Runtime metadata endpoint: `/ui/facade`
- Machine-readable snapshot: `docs/api/ui-public-facade.snapshot.json`
- Snapshot generator/checker: `scripts/ui_facade_contract_snapshot.py`
- CI gate: `python scripts/ui_facade_contract_snapshot.py --check --no-static-fallback`

The snapshot is intentionally backend-owned. It lets the future frontend bind to
stable `/ui/*` route metadata without creating a premature UI package or reading
internal backend modules directly.
