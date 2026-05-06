# Strategy Validator & Forensic Analyst

Governed strategy validation, adjudication, and operator evidence control plane for a solo, single-tenant operator.

This repository is designed around evidence-backed research, append-only governance records, paper-only validation workflows, and production-safe operator readiness gates. It is not a live-trading bot and must not be treated as one unless future live execution authority is explicitly designed, governed, reviewed, and enabled.

## What this system does

Strategy Validator helps an operator move from strategy ideas to auditable research artifacts and governed decisions. The core system is organized around three planes:

1. **Decision kernel** — adjudication, realism checks, promotion decisions, and readiness gates.
2. **Evidence backbone** — append-only events, manifests, lineage, replay, and release evidence.
3. **Operator control plane** — trust posture, workflow, escalation, propagation, and automation surfaces.

The architectural direction is captured in `docs/ARCHITECTURE_ROADMAP.md`.

## Core principles

- **Single-tenant first**: built for one operator, not a multi-tenant SaaS surface.
- **Evidence before claims**: strategy results, readiness, releases, and provider posture should be backed by durable artifacts.
- **Append-only governance**: decision and state transitions are intended to be auditable rather than silently overwritten.
- **Paper-only research posture**: provider-backed and broker-like flows are research/simulation oriented unless explicitly governed otherwise.
- **Read-only advisory plane**: Oracle/advisory/intelligence modules may produce evidence and briefings, but must not gain ledger mutation or capital authority.
- **Fail-closed readiness**: missing proof should block higher-trust claims rather than degrade into optimistic defaults.

## Repository layout

```text
strategy_validator/        Python package: API, application services, validator, ledger, CLI, projections
strategy_validator/api/    FastAPI routes and HTTP surfaces
strategy_validator/cli/    Operator and research command-line entry points
strategy_validator/ledger/ Append-only ledger and persistence support
strategy_validator/validator/ Adjudication, oracle/advisory, and validation logic
strategy_validator/projections/ Read-plane projections for API/UI consumption
strategy_validator/migrations/ SQLite migrations
docs/                      Architecture, roadmap, and operational documentation
scripts/                   Local verification, packaging, and operational helper scripts
tests/                     Unit, integration, and constitutional test coverage
ui/                        Operator UI, when present in a checkout/branch
artifacts/                 Generated evidence and runtime artifacts; usually not source truth
```

## Requirements

- Python 3.11 or newer
- SQLite for local ledger-backed operation
- Node.js only when working on frontend/UI surfaces
- Optional provider credentials for explicit provider-backed research flows

The Python package metadata and console entry points are defined in `pyproject.toml`.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

Run the test suite:

```bash
pytest
```

Run local source/repository checks:

```bash
python scripts/repository_truth_check.py
python scripts/source_health.py
```

Run the API locally:

```bash
strategy-validator-api
```

Depending on local configuration, the API exposes health/readiness-style routes such as `/healthz`, `/livez`, `/readyz`, and strategy/readiness-specific endpoints.

## Common operator commands

The project exposes many console scripts. Frequently useful entry points include:

```bash
strategy-validator-migrate
strategy-validator-startup-check
strategy-validator-research-preflight
strategy-validator-single-tenant-preflight
strategy-validator-deployment-env-check
strategy-validator-single-tenant-api-smoke
strategy-validator-evidence-index
strategy-validator-operator-doctor
```

Research and paper-loop related commands include:

```bash
strategy-validator-provider-capabilities
strategy-validator-strategy-batch-run
strategy-validator-provider-paper-loop
strategy-validator-paper-research-replay-verify
strategy-validator-strategy-memory
strategy-validator-thesis
strategy-validator-shadow-book
strategy-validator-market-data-integrity
```

Use each command's `--help` output for the current argument contract.

## Configuration

Start from the sample deployment environment file when present:

```bash
cp deployment.env.sample deployment.env
```

Important production-style settings include:

- `STRATEGY_VALIDATOR_MODE=PRODUCTION` for production semantics.
- `STRATEGY_VALIDATOR_API_TOKEN` for protected mutation routes.
- Provider-specific environment variables only for explicit provider-backed commands.

The backend should remain bootable without optional provider keys. Missing optional provider credentials should produce unavailable/pending evidence rather than unsafe startup failure or fake success.

## Safety model

This repository intentionally separates authority:

- API routes should go through application surfaces.
- UI/frontend surfaces should consume API/read-plane projections rather than writing directly to persistence.
- Ledger mutation should stay centralized and append-only.
- Advisory/Oracle modules are read-only and evidence-producing.
- Readiness gates should block claims when required artifacts, credentials, signatures, or burn-in evidence are missing.

For personal research, keep provider/broker integrations in dry-run or paper-only mode unless a future governed live-execution design explicitly changes that boundary.

## Evidence and release posture

Generated evidence commonly lives under `artifacts/`. Release, deployment, provider, paper-loop, and readiness evidence should be treated as point-in-time records with enough metadata to support replay, audit, and trust assessment.

Useful evidence-oriented commands include:

```bash
strategy-validator-evidence-index
strategy-validator-single-tenant-evidence
strategy-validator-research-os-catalog
strategy-validator-research-os-drift
strategy-validator-research-os-release-readiness
```

## Development workflow

A practical local verification loop:

```bash
python -m compileall strategy_validator tests scripts
pytest
python scripts/repository_truth_check.py
python scripts/source_health.py
```

Before merging larger changes, also run the relevant migration, OpenAPI/UI facade snapshot, deployment, provider, or research-specific checks touched by the change.

## License

This project is marked as proprietary in package metadata. Do not assume open-source redistribution rights unless the repository owner adds an explicit license.
