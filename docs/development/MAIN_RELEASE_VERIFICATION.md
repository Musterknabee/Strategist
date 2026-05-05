# Main Release Verification

## Purpose

This runbook defines a reproducible local evidence pack for validating `main` after PR queue merges and auditing stale branches safely for a single-tenant operator workflow.

This process is local verification evidence only.

## What this process does

- Runs required repository and contract gates.
- Runs required targeted pytest suites.
- Optionally runs full pytest and frontend certification.
- Produces machine-readable JSON evidence and Markdown summary.
- Produces a branch cleanup audit report with safe classifications.
- Never deletes branches automatically.

## What this process does not claim

- Not production deployment approval.
- Not operator signoff.
- Not live trading authorization.
- Not profitability evidence.

## Commands

Run the main evidence pack:

```powershell
python scripts/main_release_verification_pack.py `
  --output-dir artifacts/release_verification/latest `
  --json `
  --summary-markdown-output-path artifacts/release_verification/latest/main-release-verification-pack.md `
  --require-pass
```

Optional flags:

- `--no-frontend` skips `npm run certify`.
- `--no-pytest-full` skips full `python -m pytest -q`.

Run the branch cleanup audit:

```powershell
python scripts/branch_cleanup_audit.py `
  --json `
  --output-json-path artifacts/release_verification/latest/branch-cleanup-audit.json `
  --output-markdown-path artifacts/release_verification/latest/branch-cleanup-audit.md
```

Optional full-repo handoff archive steps are documented in:

- `docs/development/REPOSITORY_ARCHIVE_REPRODUCIBILITY.md`

## PASS and FAIL interpretation

- `PASS` means all required gates passed.
- `FAIL` means one or more required gates failed.
- With `--require-pass`, the evidence pack exits non-zero on required gate failure.

## Branch cleanup audit policy

Classifications:

- `KEEP_MAIN`
- `OPEN_PR_DO_NOT_DELETE`
- `MERGED_SAFE_TO_DELETE`
- `STALE_NEEDS_MANUAL_REVIEW`
- `NO_COMMON_ANCESTOR_DO_NOT_DELETE`
- `UNKNOWN_DO_NOT_DELETE`

Safe deletion policy:

- Never delete `main`.
- Never delete branches with open PRs.
- Never auto-delete remote branches.
- Only run suggested local delete commands after manual review.

## Windows notes

- Use direct process exit codes for pytest; do not infer pass/fail via `findstr`.
- `npm run certify` may fail noisily if a dev server is running in parallel; stop dev servers before verification.
