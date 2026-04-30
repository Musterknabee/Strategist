# Next single-tenant host security hardening ledger

## Scope

Continues the single-tenant backend production-readiness path without claiming frontend, SaaS, or multi-tenant readiness.

## Implemented slices

### 1. Bundle command path portability

Generated target-host helper scripts now self-locate the bundle root and default `STRATEGY_VALIDATOR_ENV_FILE` to `${BUNDLE_DIR}/deployment.env`:

- `commands/preflight.sh`
- `commands/verify-ledger.sh`
- `commands/backup-ledger.sh`
- `commands/restore-ledger.sh`

This closes the risk where an operator running a helper from another working directory could accidentally use the wrong `deployment.env`.

### 2. Docker least-privilege defaults

Generated Docker Compose, systemd, and Docker-backed helper commands now include hardened container flags:

- read-only root filesystem,
- tmpfs `/tmp`,
- dropped Linux capabilities,
- `no-new-privileges`.

The image still runs as the non-root `strategy-validator` user; these flags reduce blast radius on the single-tenant host.

### 3. Secret-bearing env file permission gate

`strategy-validator-deployment-env-check` now rejects real POSIX `deployment.env` files that are group/world readable. Placeholder/template files continue to be rejected by token policy, while real secret-bearing env files require private 0600-style permissions.

### 4. Acceptance coverage tightened

The deployment acceptance gate now explicitly checks `commands/acceptance.sh` as a required generated bundle file, in addition to relying on the bundle checker.

## Tests run

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  tests/constitutional/test_single_tenant_deployment_env_check.py \
  tests/constitutional/test_single_tenant_deployment_bundle.py \
  tests/constitutional/test_single_tenant_deployment_acceptance.py \
  tests/constitutional/test_backend_container_envelope.py

13 passed
```

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  tests/constitutional/test_single_tenant_deployment_preflight.py \
  tests/constitutional/test_single_tenant_deployment_evidence.py \
  tests/constitutional/test_single_tenant_api_smoke_script.py \
  tests/constitutional/test_single_tenant_runtime_token_policy.py

13 passed
```

Additional repository checks:

```text
source_health: PASS
repository_truth_check: PASS
migration_truth_check: PASS
```

## Realistic caveat

This pass hardens host-side single-tenant deployment mechanics. Full runtime API exercise still belongs in the intended Python 3.11 + Pydantic v2 environment with a built Docker image and real mounted volumes.
