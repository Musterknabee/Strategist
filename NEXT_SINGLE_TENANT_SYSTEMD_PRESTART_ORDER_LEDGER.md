# Next Single-Tenant Systemd Pre-Start Order Ledger

## Slice

Harden the generated systemd service so deployment env validation happens before stale-container cleanup.

## Problem

The systemd template already ran a hardened `strategy-validator-deployment-env-check` container before launching the API, but the stale-container cleanup command ran first:

```ini
ExecStartPre=-/usr/bin/docker rm -f strategy-validator-api
ExecStartPre=/usr/bin/docker run ... strategy-validator-deployment-env-check ...
```

If `/etc/strategy-validator/deployment.env` was invalid, systemd could remove the existing API container and only then fail closed on validation. That makes invalid configuration a higher-availability event than necessary.

## Change

The generated unit now runs the validator first, then performs ignored stale-container cleanup, then starts the API container:

```ini
ExecStartPre=/usr/bin/docker run ... strategy-validator-deployment-env-check ...
ExecStartPre=-/usr/bin/docker rm -f strategy-validator-api
ExecStart=/usr/bin/docker run --rm --name strategy-validator-api ...
```

This preserves fail-closed validation while avoiding avoidable deletion of a currently present container when the env file is bad.

## Tests

Updated constitutional bundle tests assert the exact ordering:

1. deployment env validation
2. stale-container cleanup
3. API container start

## Scope

Single-tenant backend deployment only. This does not claim frontend, SaaS, or multi-tenant readiness.
