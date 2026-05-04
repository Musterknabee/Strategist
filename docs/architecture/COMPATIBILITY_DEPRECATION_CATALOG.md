# Compatibility deprecation catalog

This catalog turns compatibility wrappers into owned, shrinkable debt instead of
permanent public surface. New compatibility entrypoints must not be added unless
an owner, replacement, and removal condition are recorded here.

## Current governed surfaces

| Surface | Owner | Replacement / canonical path | Removal condition | Current action |
|---|---|---|---|---|
| `strategy_validator.application.__init__` lazy export map | Application plane | Import directly from the concrete application module | All internal imports use concrete modules and external users have one release cycle notice | Freeze growth; remove dead exports in small batches |
| `strategy_validator.cli` compatibility modules | Operator tooling | Narrow command modules registered through `pyproject.toml` entrypoints | CLI smoke tests prove canonical commands cover prior behavior | Freeze growth; catalog wrappers before deletion |
| `strategy_validator.api.routes.research` re-export imports | API transport | Bounded routers such as `research_release.py`, `research_handoff.py`, and `research_submission.py` | Source-string route tests migrate to router-level/API tests | Continue extracting route groups; preserve external paths |

## Rules

1. Compatibility files may forward calls, but must not accumulate new behavior.
2. New compatibility entries require a test proving the canonical replacement.
3. Removal must be one bounded PR per wrapper group.
4. Public API path preservation is allowed; implementation-file preservation is not.
5. Budget tests should ratchet downward after each extraction/removal.


## Removed compatibility wrappers

| Removed surface | Canonical replacement | Removal slice |
|---|---|---|
| `strategy_validator.cli.oracle_pack_compat_configs` | `strategy_validator.cli.oracle_pack_command_configs` | Horizon A CLI surface ratchet #1 |
