# Frontend UI facade contract (snapshot → generated artifact → hooks)

This repository treats **`docs/api/ui-public-facade.snapshot.json`** as the authoritative inventory of public UI routes (path, HTTP method, `kind`, `auth_required`, `payload_schema`). It is produced and checked by:

```bash
python scripts/ui_facade_contract_snapshot.py --check --no-static-fallback
```

That gate also refreshes **`ui/strategist-web/lib/contracts/ui-facade-routes.json`** when snapshots are regenerated.

## Generated frontend mirror

After the backend snapshot changes, regenerate the TypeScript-facing contract (JSON + thin loader) from the same snapshot:

```bash
python scripts/generate_frontend_ui_facade_contract.py
```

Outputs:

| Artifact | Role |
|----------|------|
| `ui/strategist-web/lib/generated/ui-facade-contract.json` | Stable JSON: `schema_version`, `source_snapshot_schema_version`, `source_schema_version`, `read_plane_only`, `mutation_route`, `route_count`, `routes_sha256`, `routes[]` |
| `ui/strategist-web/lib/generated/ui-facade-contract.ts` | Imports the JSON and exports `uiFacadeContract` / `listUiFacadeRoutes()` |

Do not hand-edit generated files; fix drift at the snapshot, then re-run the generator.

## Hook / drift validation

**`scripts/frontend_ui_contract_check.py`** verifies:

1. `ui-facade-contract.json` matches the canonical payload derived from the snapshot (no stale committed contract).
2. `lib/contracts/ui-facade-routes.json` still matches the snapshot digest (`routes_sha256`, `route_count`).
3. Literal HTTP paths in **`ui/strategist-web/hooks/*.ts`** (excluding `*.test.ts`) used with `strategistGetJson`, `strategistPostJson`, `strategistProbeGetJson`, or `useReadPlaneJsonQuery` exist in the facade (with `{param}` template matching). Allowlisted non-facade reads: `/`, `/healthz`, `/livez`, `/readyz`, and `/readiness/*`.
4. POST usages map to facade **mutation** routes with **`auth_required`: true**.
5. Read-plane GET usages do not resolve to mutation routes.

Run from repository root:

```bash
python scripts/frontend_ui_contract_check.py
```

It is wired into **`npm run contract:check`** and therefore **`npm run certify`** / **`npm run validate`** inside `ui/strategist-web`. CI runs the same script after the UI facade snapshot gate.

## Proof of alignment

- **Backend**: `docs/api/ui-public-facade.snapshot.json` (`routes_sha256`, `schema_version`).
- **Frontend routes contract test**: `ui/strategist-web/lib/contracts/ui-facade-routes.contract.test.ts` (Vitest, digest vs snapshot).
- **Generated contract tests**: `ui/strategist-web/lib/generated/ui-facade-contract.test.ts`.
- **Python**: `tests/api/test_frontend_ui_contract_check.py` (path matching + script exit code).

If a hook introduces a path not in the snapshot, **`contract:check`** fails until the backend exposes the route and the snapshot (and generated files) are updated.
