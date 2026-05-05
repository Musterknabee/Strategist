# Operator Ease-of-Use Commands

## Purpose

This runbook gives a solo single-tenant operator a clear, read-only command sequence for local diagnostics and evidence hygiene.

- No live trading.
- No broker orders.
- Local diagnostics are not production deployment approval.
- Local diagnostics are not operator signoff.
- No profitability claim.

## Quickstart

### PowerShell (Windows)

```powershell
cd <repo-root>
python scripts/setup_local_deployment.py --force
strategy-validator-operator-doctor --json --require-ready
```

### Bash (Linux/macOS)

```bash
cd <repo-root>
python scripts/setup_local_deployment.py --force
strategy-validator-operator-doctor --json --require-ready
```

## Operator Doctor

`strategy-validator-operator-doctor` is a read-only diagnostic command. It reports configured state, blockers, warnings, and deterministic next commands.

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

1. `strategy-validator-deployment-env-check deployment.env --require-valid --json`
2. `strategy-validator-migrate --json`
3. `strategy-validator-single-tenant-preflight --prepare --require-ready --json`
4. `strategy-validator-single-tenant-api-smoke --env-file deployment.env --token-source env-file --require-pass --json`
5. `python scripts/main_release_verification_pack.py --output-dir artifacts/release_verification/latest --json --require-pass`
6. `python scripts/branch_cleanup_audit.py --json --output-json-path artifacts/release_verification/latest/branch-cleanup-audit.json`

## PASS / WARN / FAIL meaning

- `PASS`: no blockers in local diagnostic scope.
- `WARN`: non-blocking issues remain (for example optional provider keys pending).
- `FAIL`: blocking setup or readiness issues detected.

## Windows/PowerShell notes

- `strategy-validator-single-tenant-preflight` reads process env. Load `deployment.env` into the current shell before preflight.
- Production-style `/var/...` paths map to the current drive on Windows when using local host processes.
- Use direct process exit codes for pytest; avoid `findstr` pass/fail inference.

## Evidence location

Default local evidence location:

- `artifacts/release_verification/latest/`

Use operator doctor plus release verification and branch audit outputs to keep post-merge evidence reproducible.
