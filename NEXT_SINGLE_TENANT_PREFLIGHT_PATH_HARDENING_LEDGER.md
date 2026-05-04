# Next Slice Ledger: Single-Tenant Preflight Durable Path Hardening

## Slice

Harden the single-tenant deployment preflight so it rejects symlinked durable paths before it creates, migrates, verifies, backs up, or restores mutable deployment storage.

## Why

Earlier slices hardened the deployment env file, generated bundle, acceptance gate, and evidence pack against symlink indirection. The remaining preflight gap was durable runtime paths: `database_path`, `backup_dir`, `artifact_root`, and `restore_drill_path` were canonicalized with `Path.resolve()`, which follows symlinks before the gate can reason about the operator-provided path.

For single-tenant deployment readiness, those paths are write targets. Accepting a symlinked final path or parent directory can redirect ledger creation, backup generation, restore drills, and artifact writes outside the reviewed deployment envelope.

## Implementation

- Reused `absolute_path_preserving_symlink()` in `strategy_validator/cli/single_tenant_preflight.py`.
- Added durable path integrity checks that inspect the final path and existing parent components without resolving symlinks.
- Added `preparation.path_integrity` to the preflight payload.
- Added the boolean check `deployment_paths_not_symlinked`.
- Fail closed before mutation when durable path integrity fails:
  - no migration
  - no directory preparation
  - no backup/restore drill
  - no ledger or operator-action verification writes
- Preserved the backend-only preflight shape and final `BLOCK_DEPLOYMENT_AND_FIX_PREFLIGHT` recommendation.

## Tests

Added regression tests in `tests/constitutional/test_single_tenant_deployment_preflight.py`:

- rejects a symlinked ledger database path before migration
- rejects a symlinked restore-drill destination before backup/restore execution

## Validation

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/constitutional/test_single_tenant_deployment_bundle.py \
  tests/constitutional/test_single_tenant_deployment_acceptance.py \
  tests/constitutional/test_single_tenant_deployment_env_check.py \
  tests/constitutional/test_single_tenant_deployment_evidence.py \
  tests/constitutional/test_single_tenant_api_smoke_token_sources.py \
  tests/constitutional/test_single_tenant_api_smoke_script.py \
  tests/constitutional/test_single_tenant_deployment_preflight.py
```

Result: `38 passed`.

Also passed:

```bash
python scripts/source_health.py
python scripts/repository_truth_check.py
python scripts/verify_repo_archive.py /mnt/data/Strategist-main-next-slices-preflight-path-hardening.zip --repo-root . --json
```

Archive verification status: `PASS`.
