# Strategic dead-zone quarantine

This repo must not expand these surfaces until their prerequisite checks pass.

| Surface | Status | Required prerequisite | Enforcement hook |
|---|---|---|---|
| Frontend operator UI | Deferred | Stable projection-backed workboard API, scoped auth context, OpenAPI snapshot | `strategy_validator.application.strategic_horizon_readiness` |
| Workflow engine integration | Deferred | Idempotent operator journal, deterministic projection replay, restore drill gate | `strategy_validator.application.strategic_horizon_readiness` |
| Multi-tenant operation | Deferred | Principal/scoped auth, tenant isolation model, database strategy | `strategy_validator.application.strategic_horizon_readiness` |
| Oracle/advisory expansion | Quarantined | Event-sourced advisory outputs and read-only authority tests | `tests/constitutional` and projection registry |
| Additional provider integrations | Quarantined | Provider URL policy, credential burn-in, production smoke gate | `strategy_validator.core.provider_url_policy` |
