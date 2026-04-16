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
