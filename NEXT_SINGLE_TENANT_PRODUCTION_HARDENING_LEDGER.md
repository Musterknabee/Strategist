# Next single-tenant production hardening ledger

## Scope

Continuation slice for the backend-only single-tenant deployment handoff. This pass is intentionally bounded to production safety and operator portability, not frontend readiness or multi-tenant SaaS conversion.

## Slice 1 — explicit production mutation scopes

### Problem

Production scope enforcement could drift because some runtime paths interpreted an empty `STRATEGY_VALIDATOR_API_TOKEN_SCOPES` as the default required scope set. That is acceptable for local/non-production ergonomics but unsafe for production because the deployment env contract requires explicit operator scopes.

### Changes

- `strategy_validator/api/auth.py`
  - production runtime status now parses token scopes with `default_when_empty=False`.
  - `require_mutation_auth()` now refuses production mutation requests when the configured token is placeholder-like or required scopes are missing, even if the API is started outside `strategy-validator-api`.
  - authenticated mutation contexts now use the already-validated production scope tuple.
- `strategy_validator/validator/readiness.py`
  - production readiness no longer grants implicit scopes when the scope env var is missing.
- `strategy_validator/cli/single_tenant_preflight.py`
  - production preflight no longer grants implicit scopes when the scope env var is missing.
- `tests/constitutional/test_single_tenant_runtime_token_policy.py`
  - added source-level constitutional coverage for the no-implicit-production-scope rule.

## Slice 2 — lightweight probe registry import

### Problem

The API probe registry eagerly imported runtime readiness through the application readiness module. Liveness/health probe registration should stay lightweight; only `/readyz` needs the heavier readiness graph.

### Changes

- `strategy_validator/api/probes.py`
  - replaced eager readiness import with a lazy `perform_readiness_check()` wrapper used only by `/readyz`.
- `strategy_validator/api/app.py`
  - kept factory wiring stable and aligned with the existing registry seam assertion.
- `tests/constitutional/test_api_probe_registry_seam.py`
  - added coverage that probe registration does not eagerly import runtime readiness.

## Slice 3 — target-host bundle acceptance without source checkout

### Problem

The generated bundle's post-deploy evidence flow could run acceptance from the bundle directory and accidentally treat `.` as the source repo root. On a real single-tenant host this can fail or verify the wrong directory because the source checkout may not exist beside the generated bundle.

### Changes

- `strategy_validator/cli/single_tenant_deployment_bundle.py`
  - added `repo-assets.manifest.json` to every deployment bundle.
  - the manifest records required source deployment asset paths, SHA-256 digests, sizes, and missing asset count.
  - bundle verification now validates the repo-asset manifest schema and rejects bundles generated with missing required source assets.
- `strategy_validator/cli/single_tenant_deployment_acceptance.py`
  - acceptance can now satisfy repo-asset checks from the bundle repo-asset manifest when the source checkout is absent.
  - bundle file checks now require `repo-assets.manifest.json`.
- `tests/constitutional/test_single_tenant_deployment_bundle.py`
  - asserts the repo-asset manifest is generated and complete.
- `tests/constitutional/test_single_tenant_deployment_acceptance.py`
  - asserts acceptance can pass on a target host without a source checkout by relying on the bundle repo-asset manifest.

## Validation

Passed focused tests:

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest \
  tests/constitutional/test_single_tenant_deployment_bundle.py \
  tests/constitutional/test_single_tenant_deployment_acceptance.py \
  tests/constitutional/test_single_tenant_deployment_evidence.py \
  tests/constitutional/test_single_tenant_runtime_token_policy.py \
  tests/constitutional/test_single_tenant_deployment_env_check.py -q

15 passed
```

Passed repository gates:

```text
python scripts/source_health.py --json
python scripts/repository_truth_check.py --json
python scripts/migration_truth_check.py --json
```

All reported `PASS`.

## Remaining boundary

This is still a backend-only single-tenant deployment envelope. It does not certify `ui/strategist-web`, multi-tenant isolation, public SaaS posture, or external secret-manager integration.
