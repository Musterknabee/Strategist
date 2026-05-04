# ADR-0011: Operator pack materialization service

## Status
Accepted

## Context
Oracle status-pack, incident-pack, and briefing-pack assembly had started to converge on a shared projection read plane, but the final bundle materialization path still lived inside validator modules. That mixed runtime discovery, report semantics, bundle writes, artifact copying, and pack layout in the same validator-oriented files.

## Decision
Introduce a typed operator-pack materialization service under `strategy_validator.projections.operator_pack_service` backed by generic bundle-writing primitives in `strategy_validator.projections.operator_materialization`.

The service owns the bundle layout and write semantics for:
- status packs
- incident packs
- briefing packs

Validator modules keep compatibility wrappers, but the actual materialization logic now lives in the projections/read-plane package family.

## Consequences
- pack bundle writes are now reusable platform services rather than validator-local helpers
- incident artifact copying is centralized and test-locked
- future operator surfaces can consume the same bundle writer without reimplementing JSON/Markdown/HTML and artifact-copy logic
- validator remains focused on report construction while the operator read/materialization plane owns bundle emission
