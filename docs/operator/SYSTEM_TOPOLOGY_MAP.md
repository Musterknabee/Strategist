# System topology / dependency map

## Purpose

The **System topology / dependency map** cockpit section is a read-only operator and developer view that ties together only what the repository already declares:

- **Frontend panes → hooks → HTTP endpoints** (curated in `ui/strategist-web/lib/operator/system-topology-model.ts`, aligned with `CockpitPageShell` data sources).
- **UI facade routes → payload schemas → optional builder hints** (from `ui/strategist-web/lib/contracts/ui-facade-routes.json`, which must match `docs/api/ui-public-facade.snapshot.json` via CI).
- **CLI commands → expected evidence → cockpit pane names** (from `ui/strategist-web/lib/operator/local-ops-command-registry.json`).
- **CI scripts → stated invariants** (curated list of known gates such as `scripts/repository_truth_check.py` — not an exhaustive live CI parser).
- **Authority boundaries** (file paths and summaries only; no live enforcement claims from the browser).

Anything not present in those sources is shown as **UNKNOWN**, **PENDING**, or **DEGRADED**, not invented.

## How mapping works

1. **Contract routes** — Each `GET`/`HEAD`/`OPTIONS`/`POST` row in `ui-facade-routes.json` becomes a single grouped node per `path` with `kind` and `auth_required` driving **read-plane vs mutation** and **export vs metadata** safety classes.
2. **Pane wiring** — Each home-cockpit pane lists the hooks and endpoints the shell uses for that surface. Endpoints that are **not** in the UI facade contract (for example `/healthz`, `/readyz`, `/readiness/deployment`) are labeled as probes or **UNKNOWN** relative to the facade contract, not as fabricated API routes.
3. **Builder hints** — Only `payload_schema` keys that are explicitly listed in `PAYLOAD_SCHEMA_BUILDER_HINT` get an `APPLICATION_BUILDER` node. Other schemas have **no** builder node (not a claim that no builder exists).
4. **CLI / evidence** — Registry rows drive `CLI_COMMAND`, `EVIDENCE_ARTIFACT`, and `DOC` nodes. `cockpitPane` strings are mapped to topology `pane_key` values via `REGISTRY_COCKPIT_COMPONENT_TO_PANE_KEY`.
5. **Degraded panes** — When a pane’s backing queries fail in the shell, the topology marks that pane **DEGRADED** and shows a **non-diagnostic** “inspect next” hint (which endpoint or artifact to check). It does **not** assert root cause.

## No browser execution

The topology UI **never** runs shell commands, package scripts, or Python. Command strings shown elsewhere in the cockpit remain **copy-only** hints from the registry; this pane does not add execution.

## Authority boundaries (conceptual)

- **Append-only / centralized ledger** — Server-side modules under `strategy_validator/ledger/` enforce storage discipline; the browser does not write SQLite or artifacts.
- **Mutation routes** — `POST /ui/commands/{action}` and other mutation rows in the facade contract require bearer auth when the deployment is token-protected; posture is summarized via `GET /ui/runtime` elsewhere in the cockpit, not re-executed here.
- **Read-plane UI** — JSON projections are built through bounded application surfaces (`api_ui_surfaces`); the topology only names files/schemas that are already documented or hinted in-repo.

## Related files

- Topology model: `ui/strategist-web/lib/operator/system-topology-model.ts`
- Topology UI: `ui/strategist-web/components/cockpit/SystemTopologyPane.tsx`
- Operator command registry: `ui/strategist-web/lib/operator/local-ops-command-registry.json`
- UI facade contract: `ui/strategist-web/lib/contracts/ui-facade-routes.json`
