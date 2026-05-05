# Cockpit Demo Mode and Acceptance Coverage

The strategist web demo mode is an opt-in frontend preview for the operator cockpit. It is enabled with `NEXT_PUBLIC_STRATEGIST_DEMO_MODE=true` and uses synthetic read-plane payloads only.

Demo mode is not production. It is not deployment approval, not operator signoff, not live trading authorization, and not profitability evidence. Synthetic rows prove that the UI can render the cockpit surfaces without a backend; they do not prove backend readiness, provider credentials, evidence quality, strategy quality, or broker execution capability.

## How To Read Demo Data

- Treat every demo payload as `DEMO_ONLY` and synthetic.
- Missing or unavailable values remain `UNKNOWN`, `PENDING`, `DEGRADED`, or `NO_PAPER_DATA`.
- Synthetic provider entries do not mean provider keys exist.
- Evidence and replay demo fields only exercise integrity displays; they do not claim strategy quality.
- Command-capable cockpit modes still require the existing token-gated backend paths outside demo mode.

## Acceptance Coverage

The frontend acceptance pack covers:

- Operator Home default rendering and advanced cockpit reveal.
- Candidate Workbench empty, degraded, filtered, and candidate-review states.
- Advanced Cockpit mode switches for Research Review, Forensic Audit, Capital Firewall, and Release Control.
- Safety boundaries for no live trading, no broker orders, no deployment approval, no operator signoff, and no profitability claim.
- Forbidden authority language checks for cockpit acceptance surfaces.

## Commands

Run these before treating a UI demo or acceptance change as review-ready:

```bash
npm run contract:check
npm run test
npm run acceptance
npm run certify
```

`npm run certify` is the full frontend gate. If it fails, fix the failing surface or report the exact failure; do not convert unknown or degraded data into success to make the demo look cleaner.
