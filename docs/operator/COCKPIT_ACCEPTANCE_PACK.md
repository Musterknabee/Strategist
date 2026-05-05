# Operator Cockpit Acceptance Pack

The operator cockpit acceptance pack is the frontend/repository proof layer for the Strategist web cockpit. It is not a deployment approval and it is not an execution authorization.

It proves:

- all registered cockpit modes render through the switchboard,
- frontend read hooks align with the generated UI facade contract or explicit health/readiness probes,
- mutation hooks remain isolated to governed mutation surfaces,
- cockpit pane components do not directly fetch or import mutation clients,
- demo mode is opt-in, visibly synthetic, secret-free, and non-approving,
- command hints map to real console scripts or repository scripts and remain copy-only,
- production-sensitive hints carry warning text,
- evidence/release/first-run surfaces preserve no-approval and no-browser-execution language.

It does not prove:

- the backend is currently ready,
- deployment is approved,
- operator signoff is complete,
- broker/live trading is authorized,
- local CLI commands have been executed,
- artifact contents are current beyond the snapshots and read-plane payloads checked by the backend gates.

Run locally:

```powershell
cd ui/strategist-web
npm run acceptance
npm run certify
```

Repository proof commands that should remain green:

```powershell
python scripts/ui_facade_contract_snapshot.py --check --no-static-fallback
python scripts/openapi_contract_snapshot.py --check
python scripts/repository_truth_check.py
python scripts/source_health.py
```

Demo/offline mode remains explicitly opt-in with `NEXT_PUBLIC_STRATEGIST_DEMO_MODE=true`. Demo payloads are `DEMO_ONLY` and must never be used as readiness, deployment, signoff, or trading evidence.
