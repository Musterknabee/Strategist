# Frontend operator console (`ui/strategist-web`)

The Next.js app under `ui/strategist-web` is the **operator read-plane console**. It consumes the same `/ui/*` routes documented by `GET /ui/facade`. It does **not** write to the ledger or SQLite; all writes remain on backend command routes.

## Readiness status (intentional)

- **`frontend_readiness_claimed`** in backend inventory remains **`false`** until product and evidence gates define a passing bar (see below). **Frontend production readiness is NOT_CLAIMED** until then; passing lint/build/smoke does not change that by itself.
- **Backend single-tenant deployment approval** is independent: a passing backend evidence pack does not certify the UI.

## Configuration (no client secrets)

| Variable | Where | Purpose |
|----------|-------|---------|
| `NEXT_PUBLIC_STRATEGIST_API_BASE_URL` | Browser / Next build | Public HTTP(S) origin of the API (e.g. `https://ops.example.com` or `http://127.0.0.1:8000`). **Never** put API tokens or `STRATEGY_VALIDATOR_API_TOKEN` in `NEXT_PUBLIC_*`. |
| `STRATEGY_VALIDATOR_UI_CORS_ORIGINS` | API process | Optional comma-separated browser origins allowed for **GET / HEAD / OPTIONS** on `/ui/*` when the UI is served from a different origin than the API (typical local dev). Unset = no extra CORS (fail-closed). |
| `STRATEGIST_SMOKE_API_BASE_URL` | Smoke / verify scripts | Optional; base URL for `npm run smoke` or `scripts/verify_frontend.py --smoke-api-base`. |

### `GET /ui/facade` frontend fields (authority stays on the API)

| Field | Meaning |
|-------|---------|
| `frontend_package_present` / `frontend_package_detected_by_backend` | **True** only if the API process can see `ui/strategist-web/package.json` or `package-lock.json` under its working directory (full repo checkout). **False** in typical **API-only containers** (e.g. Docker image with only `strategy_validator/`) even when Next.js runs separately — **expected**, not a browser error. |
| `frontend_runtime_reachable` | Always **`null`** from the API (the server does not observe your browser). |
| `frontend_operator_console_hint` | Short operator copy clarifying the above. |
| `frontend_readiness_claimed` | Stays **`false`** until formal product/evidence gates say otherwise. |
| `read_plane_only` | **`true`**: this console uses unauthenticated read-plane routes only for this tranche. |

Copy `ui/strategist-web/.env.example` to `.env.local` for local development.

## Ports (typical local)

| Service | Port | URL example |
|---------|------|-------------|
| Strategy Validator API | **8000** | `http://127.0.0.1:8000` |
| strategist-web (Next dev) | **3000** | `http://127.0.0.1:3000` |

## Terminal keyboard shortcuts (operator cockpit)

The UI is a **read-plane terminal**: navigation and refresh only; **no API token in the browser**; **no mutations** from these shortcuts.

| Shortcut | Action |
|----------|--------|
| **Ctrl+K** / **⌘K** | Open command palette |
| **/** | Open palette (when focus is not in an input / textarea / contenteditable) |
| **G** then **O** | Go to Overview (`/`) |
| **G** then **W** | Workboard |
| **G** then **R** | Readiness |
| **G** then **E** | Evidence |
| **G** then **L** | Ledger |
| **G** then **P** | Providers |
| **G** then **T** | Runtime |
| **R** | **Route-scoped refresh**: invalidates only the TanStack queries used by the current page (e.g. `/ledger` → operator-actions only). Command bar **Refresh** matches **R**. |
| **Palette** | **“Refresh current route queries”** — same as **R**. **“Refresh all read-plane queries (full)”** — invalidates every `strategist` query (use after backend-wide changes). |
| **?** | Shortcut help |
| **Esc** | Close palette, help, or inspector |

Chord timing: second key must arrive within ~1s after **G**. Shortcuts are suppressed while typing in form fields.

**Live smoke:** If the API is not running, skip smoke and record **NOT_RUN** (do not treat as a failed gate). When the API is up on port 8000:

`cd ui/strategist-web && npm run smoke -- --api-base-url http://127.0.0.1:8000 --json`

## Local development

1. Start the API in production mode with valid `deployment.env` (temp paths are fine for smoke). Default API URL in dev is **`http://127.0.0.1:8000`**.
2. If the UI runs on another origin (Next on **port 3000**), set on the API host:
   `STRATEGY_VALIDATOR_UI_CORS_ORIGINS=http://127.0.0.1:3000,http://localhost:3000`
3. From repo root:

   ```bash
   cd ui/strategist-web
   npm ci
   npm run dev
   ```

4. Open **http://127.0.0.1:3000** (or **http://localhost:3000**) and go to **`/workboard`**. The page loads `/ui/facade` and `/ui/workboard` via TanStack Query from the API base in `NEXT_PUBLIC_STRATEGIST_API_BASE_URL` (or the development default `http://127.0.0.1:8000`).

### Frontend read-plane smoke (does **not** claim readiness)

After `npm run build`, you can verify the API is reachable from Node using the same base URL the UI would use:

```bash
cd ui/strategist-web
npm run smoke -- --api-base-url http://127.0.0.1:8000 --json
# equivalent: node scripts/smoke-frontend.mjs --api-base-url http://127.0.0.1:8000 --json
```

- Exits **non-zero** if `/ui/facade` or `/ui/workboard` is unreachable or the JSON shape is wrong.
- Emits `schema_version: strategist_frontend_smoke/v1` and a disclaimer that this is **not** a production frontend readiness claim.
- **No browser token**; optional `next_build_present` if `.next/BUILD_ID` exists.

`npm run smoke` runs `scripts/smoke-frontend.mjs`. `scripts/smoke-ui.mjs` remains a backward-compatible entry that calls the same checker.

## `npm audit`

`npm audit` may still list **moderate/high** findings tied to **devDependencies** (for example Vitest’s Vite/esbuild chain, or transitive `glob` inside `eslint-config-next`). **Next.js** is pinned to the current **14.2.x** security line; clearing every advisory often requires **major** bumps (e.g. Vitest 4, Next 16) and should be a deliberate upgrade PR, not a blind `npm audit fix --force`.

## Production

- Set **`NEXT_PUBLIC_STRATEGIST_API_BASE_URL`** at build time to the operator-visible API URL.
- Prefer **same-site** deployment (reverse proxy serves UI and API under one host) to minimize CORS exposure; only enable **`STRATEGY_VALIDATOR_UI_CORS_ORIGINS`** when split origins are required.
- Run **`npm run build`** (or CI `strategist-web` job) before shipping static/server output.

## Verification

| Command | Purpose |
|---------|---------|
| `npm run lint` / `typecheck` / `test` / `build` | Standard gates |
| `npm run smoke` / `node scripts/smoke-frontend.mjs --api-base-url http://127.0.0.1:8000 --json` | Read-plane reachability + JSON shape; not a readiness claim |
| `STRATEGIST_SMOKE_API_BASE_URL=http://127.0.0.1:8000 npm run smoke` | Same as above using env for base URL |
| `python scripts/verify_frontend.py --json` | Lint, typecheck, test, build |
| `python scripts/verify_frontend.py --smoke-api-base http://127.0.0.1:8000 --json` | Above + smoke |
| `python scripts/ci_local_verify.py --include-frontend --json` | Backend gates, then frontend verify (set `STRATEGIST_SMOKE_API_BASE_URL` if you want smoke in that run) |

On **Windows**, do not pipe pytest through `findstr` to detect failures (`findstr` exits 1 when no lines match, which can mark a green suite as failed). Use pytest’s exit code or `ci_local_verify.py`; see [WINDOWS_PYTEST_VERIFICATION.md](../development/WINDOWS_PYTEST_VERIFICATION.md).

## Future `frontend_readiness_claimed` bar (not automatic)

A future release may set **`frontend_readiness_claimed`** only when all of the following are true and recorded in evidence:

- Lint, typecheck, unit tests, and production build pass.
- Frontend smoke passes against a **known-good** API instance.
- No secrets in client bundles or `NEXT_PUBLIC_*`.
- At least one real operator screen renders honest loading/degraded/error states from live `/ui/*` data.

Until then, the backend continues to report **`frontend_readiness_claimed: false`**.
