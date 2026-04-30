# Architecture Convergence Roadmap

## Controlling direction

The repository is converging toward three authoritative planes:

1. **Decision kernel** — adjudication, realism, promotion, readiness.
2. **Evidence backbone** — append-only events, manifests, lineage, replay.
3. **Operator control plane** — trust posture, workflow, escalation, propagation, automation.

## Immediate rules

- New canonical truth must flow through the evidence backbone.
- Legacy review, doctrine, and memory lanes are migration surfaces, not expansion targets.
- New operator workflow logic should land in `strategy_validator/control_plane/` rather than expanding `validator/` or the CLI monolith.

## First implementation slices

- Restore nominal attestation trust baseline.
- Fix ledger transition correctness and cover the transition table with tests.
- Create the first control-plane namespace to support gradual extraction.
- Decompose the CLI and contract monoliths in bounded follow-on slices.


## Horizon C controlled strategic gate

Horizon C is intentionally not a broad expansion license. The repository now exposes
`strategy_validator.application.strategic_horizon_readiness` and the API route
`GET /readiness/strategic-horizon` as the controlling gate for later strategic moves.

The gate keeps the following moves blocked/deferred unless there is concrete repository
or runtime evidence:

- frontend operator UI productization requires an actual `ui/strategist-web` package and
  CI typecheck/test/build evidence; backend projection seams alone are not a frontend.
- live-provider automation requires a credentialed burn-in marker proving live credentials,
  no snapshot fallback, and freshness validation. Existing pilot artifacts remain
  insufficient unless they satisfy that marker.
- multi-tenant/horizontal scaling remains `DO_NOT_BUILD` while the append-only ledger is
  single-tenant/operator-scoped.
- workflow-engine integration remains deferred until idempotent event replay and workflow
  authority boundaries are explicit.
- Oracle/advisory expansion may continue only as read-only/evidence-producing work; it
  must not gain ledger mutation authority.

This makes Horizon C a readiness-controlled phase rather than an aspirational roadmap.
