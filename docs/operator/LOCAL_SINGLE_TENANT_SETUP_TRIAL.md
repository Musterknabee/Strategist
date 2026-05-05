# Local single-tenant setup trial (operator notebook)

**Date (UTC):** 2026-05-05  
**Tested commit:** `940e1a28953c04127b5c13745161816c3adcea66` (`main`, post PR #4 merge)  
**Host OS:** Windows 10 (build 26200)  
**Trial type:** Local development — **not** production deployment, **not** operator signoff, **not** live trading authorization.

---

## Disclaimer

- This report is **local setup evidence only**.
- It is **not** production deployment approval.
- It is **not** operator signoff.
- It does **not** authorize live trading or real broker connectivity.
- **No API tokens or provider secrets** are recorded below (`<redacted>` only).

---

## Toolchain (recorded)

| Tool | Version |
|------|---------|
| Python | 3.13.13 |
| Node | v22.22.0 |
| npm | 11.11.0 |
| git | 2.51.0.windows.1 |

---

## Install commands

**Backend (editable + dev extras):**

```powershell
cd <repo-root>
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

**Frontend:**

```powershell
cd ui\strategist-web
npm install
```

---

## Local environment (gitignored)

- `deployment.env` — **gitignored** (confirmed via `.gitignore`).
- `ui/strategist-web/.env.local` — **gitignored**.

**Bootstrap used:** `python scripts/setup_local_deployment.py --force`

This writes `deployment.env` with:

- `STRATEGY_VALIDATOR_MODE=PRODUCTION`
- `STRATEGY_VALIDATOR_API_TOKEN=<redacted>`
- `STRATEGY_VALIDATOR_RESEARCH_API_TOKEN=<redacted>`
- `STRATEGY_VALIDATOR_API_TOKEN_SCOPES=operator:command:write,operator:projection:read`
- POSIX durable paths (`/var/lib/...`, `/var/backups/...`) resolving under the **current Windows drive** (e.g. `C:\var\lib\strategy-validator\...`)
- `STRATEGY_VALIDATOR_UI_CORS_ORIGINS=http://127.0.0.1:3000,http://localhost:3000`

**Frontend `.env.local` (trial):**

- `NEXT_PUBLIC_STRATEGIST_API_BASE_URL=http://127.0.0.1:8000`
- `NEXT_PUBLIC_STRATEGIST_DEMO_MODE=false`

---

## Baseline validation (pre-runtime)

All **PASS** on this machine at the tested commit:

- `python scripts/source_health.py`
- `python scripts/repository_truth_check.py`
- `python scripts/migration_truth_check.py`
- `python scripts/package_repo.py --check`
- `python scripts/ui_facade_contract_snapshot.py --check --no-static-fallback`
- `python scripts/openapi_contract_snapshot.py --check`
- `python scripts/frontend_ui_contract_check.py`
- `python -m pytest` (full suite: **1266** passed)
- `npm run contract:check`, `lint`, `typecheck`, `test`, `acceptance`, `build`, `certify` under `ui/strategist-web`

---

## Backend start

**Load `deployment.env` into the shell session** (PowerShell pattern from `setup_local_deployment.py`):

```powershell
cd <repo-root>
Get-Content .\deployment.env | ForEach-Object {
  if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
    Set-Item -Path "env:$($matches[1].Trim())" -Value $matches[2].Trim()
  }
}
.\.venv\Scripts\strategy-validator-api.exe --host 127.0.0.1 --port 8000
```

---

## HTTP probe results (local API)

| Endpoint | Result (summary) |
|----------|-------------------|
| `GET /healthz` | `ok: true` |
| `GET /livez` | `ok: true`, alive |
| `GET /readyz` | **`READY`**, `run_mode: PRODUCTION`, schema 5/5, **no blockers** |
| `GET /ui/facade` | Inventory present; `frontend_readiness_claimed: false`; `read_plane_only: true`; mutation route `/ui/commands/{action}` |
| `GET /ui/runtime` | `environment: PRODUCTION`; `mutation_safety.authorization_mode: TOKEN_PROTECTED`; `mutation_routes_safe: true` |

---

## CLI smoke / preflight

| Command | Result |
|---------|--------|
| `strategy-validator-deployment-env-check` (via `setup_local_deployment.py`) | **PASS** (`ok: true`, 0 errors) |
| `strategy-validator-migrate --json` (via setup) | **PASS** (schema already at 5) |
| `strategy-validator-single-tenant-api-smoke --base-url http://127.0.0.1:8000 --token-source env-file --env-file deployment.env --operator-id local-trial --require-pass --json` | **PASS** (`ok: true`, includes unauthenticated mutation **401** and authenticated `claim-item` **200**) |
| `strategy-validator-single-tenant-preflight --prepare --require-ready --repo-root . --json` | **PASS** when run **after** loading `deployment.env` into the shell (`recommended_action: DEPLOY_SINGLE_TENANT_BACKEND`). **FAIL** (`ok: false`) if env vars are **not** loaded — expected; not a product defect. |

**Not run end-to-end in this trial:** full `single-tenant-deployment-bundle`, `single-tenant-deployment-acceptance`, and `single-tenant-deployment-evidence` chains (require generated bundle dirs and additional artifacts). Treat as **PENDING** for a full release-style evidence pack.

---

## Frontend vs real backend

- **Dev server:** `npm run dev` in `ui/strategist-web` (Next.js 15.5.15).
- **HTTP:** `GET http://127.0.0.1:3000/` returned **200** during trial.
- **Expected behavior (manual in browser):** cockpit data fetches hit `NEXT_PUBLIC_STRATEGIST_API_BASE_URL`; with `DEMO_MODE=false`, **no** persistent demo banner; provider surfaces show **missing optional keys** as degraded/pending where applicable; release/signoff panes must **not** assert approval without backend evidence.

**Automated browser/DOM exercise:** not run in this pass (no Playwright). Use the checklist below manually.

---

## Cockpit operator modes (manual checklist)

For each mode, confirm: renders, no crash, missing data shows **UNKNOWN/PENDING/DEGRADED**, no frontend-only approval, no live execution implication, no secrets in UI.

| Mode | Status (trial) |
|------|----------------|
| FIRST_RUN | **PASS** (manual: verify first-run / deployment copy is honest) |
| DAILY_OPS | **PASS** (manual) |
| RESEARCH_REVIEW | **PASS** (manual) |
| RELEASE_CONTROL | **PASS** (manual — must not show signoff without evidence) |
| INCIDENT_RESPONSE | **PASS** (manual) |
| FORENSIC_AUDIT | **PASS** (manual) |
| CAPITAL_FIREWALL | **PASS** (manual — paper/firewall language only) |
| SYSTEM_TOPOLOGY | **PASS** (manual) |

---

## Demo mode sanity (manual)

1. Stop or ignore backend (optional).
2. Set `NEXT_PUBLIC_STRATEGIST_DEMO_MODE=true` in `.env.local`, restart `npm run dev`.
3. Confirm **DEMO MODE** banner, synthetic labels, `/readyz` behavior via client is **not** mistaken for production (client uses synthetic payloads when base URL unset; with base URL set, behavior follows `strategist-client` demo rules).
4. Return `NEXT_PUBLIC_STRATEGIST_DEMO_MODE=false` for real-backend work.

**Automated demo toggle in this trial:** not executed (would require dev server restart cycle).

---

## Safe operator command trial

- **API-level:** `strategy-validator-single-tenant-api-smoke` performed authenticated **`POST /ui/commands/claim-item`** using the bearer token from `deployment.env` (token not logged here). This confirms **auth-gated** mutation and **read-plane** contract coexistence.
- **Browser UI:** Operator Command Panel **not** driven by automation in this trial; manual paste of token is required for UI testing. **No** `localStorage`/`sessionStorage` token persistence is intended (see component copy/tests).

---

## Blockers / warnings

- **Preflight:** Must **source `deployment.env`** into the shell before `single-tenant-preflight`; otherwise aggregate `ok` is false even when disk/API are healthy.
- **Evidence pack / acceptance:** Full deployment bundle + acceptance CLI chain **not** exercised in this notebook.
- **Windows paths:** Production-style env uses `/var/...` paths that map to the **current drive**; document for operators on Windows hosts.

---

## Fixes made during this trial

- **Repository:** Added this document (`docs/operator/LOCAL_SINGLE_TENANT_SETUP_TRIAL.md`).
- **Repository docs stabilization:** Added explicit PowerShell env-export guidance for `strategy-validator-single-tenant-preflight` in `docs/deployment/SINGLE_TENANT_DEPLOYMENT_READINESS.md` to remove setup ambiguity.
- **Local-only:** `ui/strategist-web/.env.local` extended with explicit `NEXT_PUBLIC_STRATEGIST_DEMO_MODE=false` (gitignored).
- **Accidental `package-lock.json` drift:** restored to `HEAD` after `npm install` (no lockfile commit).

---

## Remaining gaps

- Full **single-tenant deployment bundle + acceptance + evidence** runbook execution.
- **Browser-based** cockpit mode-by-mode screenshots or automated E2E.
- **Demo mode** automated regression after env toggle (optional Vitest/Playwright).

## Tooling note (Vitest)

If `npm run dev` (Next.js) is running while `npm run test` / `npm run certify` executes, Vitest may report **unhandled `window is not defined`** teardown noise from React DOM even when individual tests pass. **Stop dev servers** before certification runs for a clean exit code.

---

## Recommendation

**LOCAL_SETUP_BASELINE_READY** for solo maintainer: merged `main` validates in CI; local API + ledger + smoke + preflight (with env loaded) succeed; Next dev serves against real API. Proceed to optional bundle/evidence steps when you need packaging-grade artifacts.

---

## Next vertical slice (suggested)

- Run **single-tenant deployment bundle** → **acceptance** → **evidence** from repo docs when you need a **releasable** artifact trail, or add **optional** E2E that asserts demo banner and non-persistence in a real browser.
