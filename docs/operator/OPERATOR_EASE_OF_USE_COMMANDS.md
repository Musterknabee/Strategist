# Operator Ease-of-Use Commands

## Purpose

This runbook is the canonical single-tenant operator sequence for local diagnostics and backend evidence hygiene.

- No live trading.
- No broker orders.
- Local diagnostics are not production deployment approval.
- Local diagnostics are not operator signoff.
- No profitability claim.
- Missing provider keys can remain `PENDING`/`WARN` depending on the command; they are not universally fatal.
- Explicit provider sample retrieval for a keyed provider without key setup returns blocked/non-zero so missing setup is not silently reported as success.

## Canonical operator sequence

Use this order and then branch into detailed runbooks:

1. Clone/install (`python -m pip install -e ".[dev]"`; optional UI handled separately).
2. Configure env (`deployment.env` from `deployment.env.sample`).
3. Check env (`strategy-validator-deployment-env-check deployment.env --require-valid --json`).
4. Migrate (`strategy-validator-migrate --json`).
5. Preflight (`strategy-validator-single-tenant-preflight --prepare --require-ready --json`).
6. Start API (`strategy-validator-api --host 127.0.0.1 --port 8000` or Docker flow).
7. Optional API smoke (`strategy-validator-single-tenant-api-smoke --env-file deployment.env --token-source env-file --require-pass --json`).
8. Operator doctor (`strategy-validator-operator-doctor --json --require-ready`).
9. Release verification pack (`python scripts/main_release_verification_pack.py ...`).
10. Branch cleanup audit (`python scripts/branch_cleanup_audit.py ...`).
11. Inspect paper replay evidence (`strategy-validator-paper-research-replay-verify ...`).
12. UI/cockpit runbooks are separate and do not replace backend gates.

For detailed deployment packaging, acceptance, and final evidence: `docs/deployment/SINGLE_TENANT_DEPLOYMENT_READINESS.md`.
For local setup trial notes: `docs/operator/LOCAL_SINGLE_TENANT_SETUP_TRIAL.md`.
For replay integrity semantics: `docs/operator/PAPER_RESEARCH_REPLAY_MANIFEST.md`.

## Quickstart

### PowerShell (Windows)

```powershell
cd <repo-root>
python scripts/setup_local_deployment.py --force
strategy-validator-deployment-env-check deployment.env --require-valid --json
strategy-validator-single-tenant-preflight --prepare --require-ready --repo-root . --json
strategy-validator-operator-doctor --json --require-ready
```

### Bash (Linux/macOS)

```bash
cd <repo-root>
python scripts/setup_local_deployment.py --force
strategy-validator-deployment-env-check deployment.env --require-valid --json
strategy-validator-single-tenant-preflight --prepare --require-ready --json
strategy-validator-operator-doctor --json --require-ready
```

## Operator doctor details

`strategy-validator-operator-doctor` is read-only and reports configured state, blockers, warnings, deterministic next commands, and a readiness summary that reuses backend readiness application payloads (runtime, deployment, strategic horizon) instead of re-implementing those gates independently.

## Operator command table

| Command | Purpose | Mode | Requires token? | Writes artifacts? | Safety notes |
|---|---|---|---|---|---|
| `strategy-validator-operator-doctor` | Local backend diagnostics + next steps | Read-only | No | Optional (`--summary-markdown-output-path`) | No live trading, no signoff authority |
| `strategy-validator-deployment-env-check` | Validate `deployment.env` contract | Read-only | No | No | Fail-closed linting; not deployment approval |
| `strategy-validator-migrate` | Apply governed sqlite schema migrations | Mutation-capable | No | No | Schema authority only; not release approval |
| `strategy-validator-single-tenant-preflight` | Readiness/preflight with optional prepare | Mutation-capable | No | Optional summaries | Backend readiness only; no profitability claim |
| `strategy-validator-single-tenant-api-smoke` | HTTP smoke for health/readiness/auth boundaries | Read-only | Optional (for authenticated checks) | Optional reports | Smoke evidence only; not operator signoff |
| `strategy-validator-paper-research-replay-verify` | Offline replay digest verification | Read-only | No | No | Integrity only; no live authorization |

### JSON output

```bash
strategy-validator-operator-doctor --json
```

### Markdown summary output

```bash
strategy-validator-operator-doctor \
  --json \
  --summary-markdown-output-path artifacts/release_verification/latest/operator-doctor.md
```

### Optional API smoke

API smoke is opt-in and never runs unless requested:

```bash
strategy-validator-operator-doctor \
  --include-api-smoke \
  --env-file deployment.env \
  --token-source env-file \
  --json
```

## Recommended command sequence

Use canonical paths so evidence stays predictable:

1. `strategy-validator-deployment-env-check deployment.env --require-valid --json`
2. `strategy-validator-migrate --json`
3. `strategy-validator-single-tenant-preflight --prepare --require-ready --json`
4. `strategy-validator-single-tenant-api-smoke --env-file deployment.env --token-source env-file --require-pass --json` (optional but recommended before command mutations)
5. `strategy-validator-operator-doctor --json --require-ready --summary-markdown-output-path artifacts/release_verification/latest/operator-doctor.md`
6. `python scripts/main_release_verification_pack.py --output-dir artifacts/release_verification/latest --json --require-pass`
7. `python scripts/branch_cleanup_audit.py --json --output-json-path artifacts/release_verification/latest/branch-cleanup-audit.json --output-markdown-path artifacts/release_verification/latest/branch-cleanup-audit.md`
8. `strategy-validator-paper-research-replay-verify --replay-manifest artifacts/provider_paper_loop/latest/replay_manifest.json --json`

The release verification pack status is evidence only:

- `PASS`/`FAIL` describe local gate outcomes.
- It does not grant deployment approval or operator signoff.
- Use `--require-pass` when you need non-zero exit on failed required steps.

## PASS / WARN / FAIL meaning

- `PASS`: required readiness signals map to `OK` in the doctor scope.
- `WARN`: unresolved `WARN`/`PENDING`/`UNKNOWN`/`OPTIONAL_NOT_CONFIGURED` signals remain (for example optional provider keys pending).
- `FAIL`: required signals include `BLOCKED`/`DEGRADED`/`NOT_CONFIGURED`; this is still diagnostic and not deployment approval authority.

Canonical readiness labels surfaced in doctor JSON and markdown summary include: `OK`, `WARN`, `BLOCKED`, `DEGRADED`, `UNKNOWN`, `PENDING`, `NOT_CONFIGURED`, and `OPTIONAL_NOT_CONFIGURED`.

Backend readiness APIs may additionally expose canonical status labels:

- `OK`, `WARN`, `BLOCKED`, `DEGRADED`, `UNKNOWN`, `PENDING`, `NOT_CONFIGURED`, `OPTIONAL_NOT_CONFIGURED`.
- `UNKNOWN`/`PENDING`/`DEGRADED`/`BLOCKED` are never silently interpreted as `OK`.
- Optional provider/frontend claim setup may remain `OPTIONAL_NOT_CONFIGURED` without globally failing unrelated local diagnostics.

Provider/evidence status cues:

- `OPTIONAL_NOT_CONFIGURED` or `PENDING_KEY` means local diagnostics can continue but provider-backed intent is not fully configured.
- `UNKNOWN` means evidence is missing/not yet produced, not pass.
- `DEGRADED` means evidence exists but verification/provider quality checks failed.
- Replay digest mismatches are degraded evidence and must be remediated before relying on that replay chain.

## Windows/PowerShell notes

- `strategy-validator-single-tenant-preflight` reads process env. Load `deployment.env` into the current shell before preflight.
- Production-style `/var/...` paths map to the current drive on Windows when using local host processes.
- Use direct process exit codes for pytest; avoid `findstr` pass/fail inference.
- PowerShell command continuations in this repo use backticks (`` ` ``); Bash uses `\`.

## Linux/macOS notes

- Keep `deployment.env` private (`chmod 600 deployment.env`) before env checks.
- Use `--token-source env-file` with API smoke when container/API token source is the env file to avoid shell-token drift.

## Evidence location

Primary local evidence location:

- `artifacts/release_verification/latest/`

Deployment bundle and deployment evidence live separately under `scratch/`:

- `scratch/single-tenant-deployment-bundle/`
- `scratch/single-tenant-deployment-evidence/`
