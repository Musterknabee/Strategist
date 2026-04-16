# Architecture Health

This document is produced by `scripts/architecture_health_report.py` and tracks convergence pressure in the repository.

## Focus metrics

- Largest Python files by line count
- Package balance across application, kernel, evidence, governance, and ingress surfaces
- Hotspot tracking for known compression targets
- Presence of explicit application and API seams

## Current operating rule

New functionality should prefer:

1. `strategy_validator/application/`
2. bounded contract modules under `strategy_validator/contracts/`
3. domain services under `strategy_validator/validator/services/` or equivalent bounded packages

Avoid growing:

- `strategy_validator/contracts/oracle.py`
- `strategy_validator/cli/rollout_ops.py`
- `strategy_validator/cli/oracle_queue_commands.py`
- `strategy_validator/control_plane/__init__.py`
