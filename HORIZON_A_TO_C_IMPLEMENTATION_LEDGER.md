# Horizon A-C implementation ledger

This archive contains a bounded implementation pass across the Horizon A-C roadmap.

## Implemented

### Runtime/readiness hardening
- Added non-mutating SQLite inspection helpers in `strategy_validator/ledger/_append_only.py`:
  - `_connect_readonly()`
  - `read_events_readonly()`
  - `inspect_schema_version_info_readonly()`
- Updated `strategy_validator/validator/readiness.py` so runtime readiness uses read-only schema inspection.
- Updated deployment readiness so missing ledgers are reported without being created and hash-chain checks use `verify_hash_chain_readonly()` only when a DB exists.
- Added deployment artifact-root checks through `STRATEGY_VALIDATOR_ARTIFACT_ROOT`.

### Ledger/hash-chain read boundary
- Added `verify_hash_chain(..., readonly=False)` and `verify_hash_chain_readonly()` in `strategy_validator/ledger/reader/__init__.py`.

### API hardening
- Added `strategy_validator/api/security.py` with an ASGI security envelope:
  - request-size rejection using `STRATEGY_VALIDATOR_API_MAX_REQUEST_BYTES`
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: no-referrer`
  - `Cross-Origin-Opener-Policy: same-origin`
  - `Cache-Control: no-store`
- Installed the middleware in `strategy_validator/api/app.py`.

### Adjudication commit semantics
- Updated `strategy_validator/validator/orchestrator/__init__.py` so adjudication stages mutations on a deep copy and mutates the caller object only after `commit_state_transition()` succeeds.

### PIT/data-spine correctness
- Fixed timezone-aware decision timestamps in `strategy_validator/data_spine/universe/governance.py` to convert to UTC rather than stripping and relocalizing offsets.

### Packaging/docs truth
- Added console scripts in `pyproject.toml`:
  - `strategy-validator-startup-check`
  - `strategy-validator-research-preflight`
- Extended `scripts/repository_truth_check.py` to verify documented console commands and documented test paths.
- Added missing documented integration/hygiene tests.

### Application public surface control
- Collapsed `strategy_validator/application/__init__.py` into a thin lazy facade importing the canonical `_EXPORT_MAP` from `strategy_validator/application/_exports.py`.
- Added application export budget reporting to `scripts/architecture_health_report.py`.

### Container/operator artifact contract
- Added `STRATEGY_VALIDATOR_ARTIFACT_ROOT=/var/lib/strategy-validator/artifacts` to `Dockerfile`.
- Created the container artifact root directory during image build.
- Updated `docs/deployment/BACKEND_CONTAINER_V1.md` and container tests.

### Release assessment honesty
- Updated `strategy_validator/cli/release_candidate.py` to record explicit frontend status when frontend validation is skipped or `ui/strategist-web` is absent.

## Added tests
- `tests/api/test_security_envelope.py`
- `tests/constitutional/test_architecture_health_application_budget.py`
- `tests/constitutional/test_application_public_surface_budget.py` updated for canonical `_exports.py`
- `tests/constitutional/test_orchestrator_staged_commit_source.py`
- `tests/constitutional/test_pit_universe_timezone.py`
- `tests/constitutional/test_readiness_readonly_schema_inspection.py`
- `tests/constitutional/test_release_candidate_frontend_status.py`
- `tests/constitutional/test_repo_hygiene_and_release_cleanup.py`
- `tests/integration/__init__.py`
- `tests/integration/test_telemetry_metrics_file_e2e.py`

## Verification performed in sandbox
- Manual AST parsing of the high-gravity source-health roots: PASS.
- `run_repository_truth_check(repo_root='.')`: PASS, 73 checks.
- `run_migration_truth_check(repo_root='.')`: PASS, 0 failures.

## Verification not fully completed in sandbox
- Full pytest was not run because the sandbox Python environment did not provide the repository runtime/dev dependency set reliably.
- The source-health CLI printed PASS on the high-gravity set, but the sandbox Python process exhibited shutdown/timeout oddities after script execution. Manual high-gravity AST parsing completed successfully.
