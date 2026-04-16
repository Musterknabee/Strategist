# ADR-0049: Operator Terminal Record Publication Materialization

## Status
Accepted

## Context
The terminal-record control-plane surface now classifies publication posture, but operators still need a durable artifact, manifest, and index that can be consumed independently of a live CLI call.

## Decision
Introduce `strategy_validator.projections.operator_terminal_record_service` and CLI command `oracle-operator-pack-terminal-record-publish` to materialize terminal-record JSON/markdown bundles plus a dedicated publication manifest and index.

## Consequences
- terminal-record posture becomes a durable artifact family rather than an ephemeral CLI-only report
- downstream operator tooling can discover published terminal records via a dedicated index
- source pack manifests remain linked through publication manifest lineage
