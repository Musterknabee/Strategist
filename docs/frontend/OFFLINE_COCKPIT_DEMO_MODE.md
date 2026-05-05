# Offline Cockpit Demo Mode

The Strategist web cockpit can render a synthetic read-plane preview when the backend is absent.

Enable it explicitly:

```powershell
$env:NEXT_PUBLIC_STRATEGIST_DEMO_MODE="true"
npm run dev
```

Demo mode is frontend-only and opt-in. It is not a production default and it does not create, approve, sign, execute, or persist anything.

Safety boundaries:

- Every demo payload is marked `demo_only: true` and carries `DEMO_DATA_NOT_REAL`.
- `/readyz` remains non-ready in demo mode.
- Mutation requests are refused before any network call.
- The persistent banner states: no real backend evidence, no deployment approval, no live execution, synthetic data only.
- Demo payloads avoid provider keys, private tokens, broker account numbers, and realistic secret material.

Covered preview surfaces include `/ui/facade`, `/healthz`, `/readyz`, `/ui/runtime`, `/ui/evidence`, `/ui/evidence-chain`, `/ui/operator-actions`, `/ui/workboard`, `/ui/provider-health`, `/ui/provider-setup`, `/ui/paper-execution`, Research OS latest views, strategy batch/thesis/memory/graveyard latest views, and backtest forensics.

Use demo mode to inspect cockpit layout and contract coverage. Use a real backend and real evidence for readiness, deployment review, signoff, ledger verification, or paper/live execution decisions.
