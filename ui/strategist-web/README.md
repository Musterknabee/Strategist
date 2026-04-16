# Strategist Web

Institutional operator UI scaffold for Strategist.

## Current slice

This scaffold now includes:

- App Router-based shell
- bounded BFF routes under `app/api/ui/*`
- Control Plane, Validator, Tribunal, and Evidence routes
- policy-aware shell state and blindness-safe navigation
- command receipt and review packet shell lanes
- review packet export/inspection flows
- URL-backed deep-link context for receipts and review packets
- Vitest scaffolding for shell/governance components
- root/route loading and error boundaries for safer local execution

## Environment

Copy the example file and adjust as needed:

```bash
npm run bootstrap:env
```

Available variables:

- `STRATEGIST_BACKEND_BASE_URL` — base URL of the Python/FastAPI service exposing the `/ui/*` routes
- `STRATEGIST_BACKEND_TIMEOUT_MS` — optional timeout for the Next.js BFF → backend hop
- `STRATEGIST_FORCE_MOCKS` — (dev-only) force the shell to stay on local mock payloads even if a backend URL is configured

When `STRATEGIST_FORCE_MOCKS=true`, the shell stays on explicit local mock payloads for frontend-only work.
Without that flag, production-facing dashboard routes now fail closed when the backend is unavailable instead of presenting silent mock state as operational truth.
In production (`NODE_ENV=production`), the web shell is strict-backend by default and will fail closed if the backend is unavailable or misconfigured.

## Local development

```bash
npm install
npm run dev
```

Open the app at `http://localhost:3000`.

## Local validation

```bash
npm run check
npm run build
# or
npm run validate
```

Recommended hardening sequence:

1. `npm run bootstrap:env`
2. `npm install`
3. `npm run doctor`
4. `npm run dev`
5. `npm run smoke`
6. `npm run check`
7. `npm run build`
8. fix the first TypeScript/JSX/runtime breaks before adding more UI breadth

## Notes

This sandbox pass wired the frontend structure and tests, but it did **not** execute:

- `npm install`
- `npm run test`
- `npm run build`

So the web surface is scaffolded and iteratively hardened, but still needs a real local frontend execution pass.


## Runtime diagnostics

A local bring-up page is available at `/settings/runtime`. It reflects the current frontend server fetch posture (backend base URL, timeout, and explicit mock-mode posture) and gives a minimal checklist for first-run validation.

A second page is available at `/settings/preflight`. It runs a lightweight server-side probe against representative BFF payloads (`runtime`, `workboard`, `burn-in`) and summarizes what the web shell currently sees before you attempt a full `check`/`build` pass.


## Diagnostics routes

- `/settings` — diagnostics overview
- `/settings/runtime` — normalized env/runtime diagnostics
- `/settings/preflight` — representative BFF preflight checks


## Doctor command

Run `npm run doctor` to print the normalized local env posture, effective backend/mock mode, and the recommended next steps before a full check/build pass.


## Additional local commands

- `npm run bootstrap:env` — create `.env.local` from `.env.example` if needed
- `npm run doctor` — print normalized local env posture and next steps
- `npm run smoke` — probe representative local BFF routes after the dev server is running


## Diagnostics export

- `npm run export:diagnostics` — fetch the aggregated diagnostics snapshot and write `artifacts/frontend-diagnostics.snapshot.json`
- `/settings/export` — browser view of the same aggregated diagnostics posture
- `/api/ui/diagnostics/export` — raw JSON export surface


The diagnostics export script also appends a compact history entry to `artifacts/frontend-diagnostics.history.jsonl` so repeated local bring-up runs leave a small review trail.


## Diagnostics history

Repeated `npm run export:diagnostics` runs append compact entries to `artifacts/frontend-diagnostics.history.jsonl`.
Use `npm run prune:diagnostics` to trim that history to the most recent runs.
The shell also exposes this history at `/settings/history` and `/api/ui/diagnostics/history`.


Additional local diagnostics maintenance:

- `npm run reset:diagnostics` removes the local diagnostics snapshot and history files when you want a clean restart of the trail.
- `/settings/latest` shows only the most recent diagnostics export when the full history page is more than you need.


## Extra diagnostics helpers

- `npm run summarize:diagnostics` prints a compact aggregate summary of local diagnostics history.
- `/settings/summary` shows aggregate counts and latest posture from recent diagnostics exports.


## Additional diagnostics ergonomics

- Use `/settings/quick-actions` when you want copy/paste-friendly local command blocks grouped by bootstrap, verification, and diagnostics maintenance.
- Use `/api/ui/diagnostics/quick-actions` if you want the grouped quick-action payload as JSON.


## Diagnostics runbook

- `/settings/runbook` — combined workflow sequences for first-run bring-up, verify-before-build, and diagnostics maintenance
- `/api/ui/diagnostics/runbook` — raw JSON for the same workflow groups


Additional diagnostics surfaces:
- `/api/ui/diagnostics/index` for combined manifest + summary + latest posture + recommended validation sequence
- `/settings` now includes a copyable end-to-end validation block for local bring-up


## Diagnostics compare

- `/settings/compare` compares the latest diagnostics export against the aggregate summary derived from local history.
- `/api/ui/diagnostics/compare` exposes the same comparison as JSON.

- `/settings/status-board` combines latest posture, aggregate summary, trends, compare alignment, and a recurring maintenance loop in one operational view.
- `/api/ui/diagnostics/status-board` exposes the same combined status board as JSON for local review/automation.

- `/settings/recommendations` — prioritized diagnostics next steps derived from latest posture and recent history
- `/api/ui/diagnostics/recommendations` — JSON recommendations payload for the diagnostics center
- `npm run recommend:diagnostics` — print prioritized local next steps from diagnostics history


- `/settings/action-queue`
- `/api/ui/diagnostics/action-queue`

- `/settings/escalation-matrix`
- `/api/ui/diagnostics/escalation-matrix`

- `/settings/incident-playbook`
- `/api/ui/diagnostics/incident-playbook`

- `/settings/recovery-scorecard`
- `/api/ui/diagnostics/recovery-scorecard`

- `/settings/readiness-gate` — go / no-go diagnostics view before a fuller local validation pass.
- `/api/ui/diagnostics/readiness-gate` — JSON payload for latest posture, blockers, recovery readiness, and proceed sequence.

- `/settings/decision-log` — audit-style proceed / conditional / hold / stabilize log derived from readiness, recovery, and action-queue posture.
- `/api/ui/diagnostics/decision-log` — JSON decision-log payload for the diagnostics center.


Diagnostics additions:
- `/settings/handoff-packet`
- `/api/ui/diagnostics/handoff-packet`

- `/settings/checkpoint-register`
- `/api/ui/diagnostics/checkpoint-register`

- `/settings/certification-manifest`
- `/api/ui/diagnostics/certification-manifest`

- `/settings/release-candidate-dossier`
- `/api/ui/diagnostics/release-candidate-dossier`
