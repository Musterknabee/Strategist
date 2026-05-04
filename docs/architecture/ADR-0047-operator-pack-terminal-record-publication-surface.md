# ADR-0047: Operator Pack Terminal Record Publication Surface

## Status
Accepted

## Context
Terminal archive and retention posture now exists, but the platform still stops at archive/retain governance. Operators and downstream consumers need a reusable publication/read-model that expresses whether a terminal record should be published, indexed, or simply retained open.

## Decision
Introduce `strategy_validator.control_plane.operator_pack_terminal_record` as the shared terminal-record publication surface above terminal archive plus the shared operator-pack registry.

## Consequences
- briefing/status/incident pack markdown consume one shared terminal-record section
- CLI gains `oracle-operator-pack-terminal-record`
- terminal retention posture now converges into reusable publication/index-update state instead of remaining only archive governance
