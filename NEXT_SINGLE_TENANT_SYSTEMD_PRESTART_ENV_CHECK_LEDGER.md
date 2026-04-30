# Next single-tenant slice: systemd pre-start env validation

## Context

The generated Docker Compose path relies on the operator running the generated
acceptance/preflight commands before startup. The generated systemd unit had
lifecycle hardening and host-port parity, but the service itself did not run a
machine-readable deployment env validation step before Docker received the final
`-p 127.0.0.1:${STRATEGY_VALIDATOR_HOST_PORT}:8000` bind.

That left an operator footgun: a copied `/etc/strategy-validator/deployment.env`
with an empty or invalid host port, missing scopes, placeholder token, or invalid
container paths could fail later through Docker/systemd errors rather than
through the repo's explicit `single_tenant_deployment_env_check/v1` contract.

## Changes

- Added a non-ignored systemd `ExecStartPre=` validation container that runs:
  `strategy-validator-deployment-env-check /deployment-env/deployment.env --require-valid --json`.
- The validator container uses the same hardening posture where practical:
  read-only root filesystem, tmpfs `/tmp`, dropped capabilities, and
  `no-new-privileges`.
- The env directory is mounted read-only at `/deployment-env`.
- The validator runs as root inside the short-lived container so a recommended
  root-owned `0600` `/etc/strategy-validator/deployment.env` remains readable,
  while the long-lived API container still runs as the image's non-root user.
- Updated constitutional tests and deployment docs to lock this behavior.

## Validation intent

Systemd deployments now fail before long-lived API startup when the deployment
env file violates the same production contract used by bundle acceptance and
preflight.
