# Next single-tenant slice: systemd lifecycle idempotence

## Objective

Close a target-host lifecycle footgun in the generated single-tenant systemd unit: first boot could abort before starting the API if stale-container cleanup returned a non-zero exit status when the container did not yet exist.

## Changes

- Updated `strategy_validator/cli/single_tenant_deployment_bundle.py` so generated `systemd/strategy-validator.service` uses:
  - `ExecStartPre=-/usr/bin/docker rm -f strategy-validator-api`
  - `ExecStop=-/usr/bin/docker stop strategy-validator-api`
- Added constitutional assertions that the generated unit keeps cleanup/stop idempotent while preserving a single loopback port binding and hardened Docker runtime flags.
- Updated deployment docs to call out the idempotent systemd lifecycle behavior.

## Why this matters

Systemd treats a failing `ExecStartPre` command as a failed service start unless the command is explicitly prefixed with `-`. `docker rm -f strategy-validator-api` returns non-zero when no such container exists, which is normal on first boot. The generated unit now ignores only cleanup/stop idempotence failures; the main `docker run` command still fails closed.

## Validation

- Focused single-tenant bundle tests with plugin autoload disabled.
- Static compile of changed Python files.
- Repository/package/archive verification gates.
