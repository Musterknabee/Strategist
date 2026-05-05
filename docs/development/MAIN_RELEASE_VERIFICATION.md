# Main Release Verification

## Purpose

This runbook defines a reproducible local evidence pack for validating `main` after PR queue merges and auditing stale branches safely for a single-tenant operator workflow.

This process is local verification evidence only.
Use `docs/operator/OPERATOR_EASE_OF_USE_COMMANDS.md` as the canonical end-to-end sequence (setup -> env check -> migrate -> preflight -> smoke -> doctor -> verification pack -> branch audit -> replay verification).

Evidence output path governance:

- Default output root is `${STRATEGY_VALIDATOR_ARTIFACT_ROOT}/release_verification/latest`.
- If `STRATEGY_VALIDATOR_ARTIFACT_ROOT` is unset, fallback is `<repo>/artifacts`.
- `--output-dir` and branch-audit output paths must stay under artifact root; outside paths are rejected.

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
- Not a declaration that optional provider keys are mandatory for every diagnostic lane.

The operator doctor consumes release-verification and branch-audit presence as readiness hints only. Missing hints should surface as `PENDING` guidance and follow-up commands, not as deployment approval or rejection authority.

## Commands

Run the main evidence pack:

```powershell
python scripts/main_release_verification_pack.py `
  --output-dir release_verification/latest `
  --json `
  --summary-markdown-output-path main-release-verification-pack.md `
  --no-frontend `
  --no-pytest-full `
  --require-pass
```

Optional flags:

- `--no-frontend` skips `npm run certify`.
- `--no-pytest-full` skips full `python -m pytest -q`.
- `--summary-markdown-output-path` must stay under `--output-dir`; paths outside are rejected.
- `--output-dir` should normally remain `artifacts/release_verification/latest` for stable local evidence paths.

Run the branch cleanup audit:

```powershell
python scripts/branch_cleanup_audit.py `
  --json `
  --output-json-path release_verification/latest/branch-cleanup-audit.json `
  --output-markdown-path release_verification/latest/branch-cleanup-audit.md
```

Optional full-repo handoff archive steps are documented in:

- `docs/development/REPOSITORY_ARCHIVE_REPRODUCIBILITY.md`

## Related integrity check (paper replay evidence)

When provider paper artifacts are present, run replay verification separately:

```powershell
strategy-validator-paper-research-replay-verify `
  --replay-manifest artifacts/provider_paper_loop/latest/replay_manifest.json `
  --json
```

Replay verification is offline integrity only; it is not release approval, signoff, or profitability evidence.

## PASS and FAIL interpretation

- `PASS` means all required gates passed.
- `FAIL` means one or more required gates failed; evidence files are still produced for diagnosis.
- With `--require-pass`, the evidence pack exits non-zero on required gate failure.
- Without `--require-pass`, exit code can remain zero while JSON/Markdown status stays `FAIL`.

Release verification evidence is one readiness input, not approval authority:

- It does not imply production deployment approval.
- It does not imply operator signoff.
- It does not imply live-trading authorization or profitability.
- Missing/degraded replay/provider evidence must stay non-OK (`UNKNOWN`/`PENDING`/`DEGRADED`/`BLOCKED`) in readiness interpretation.

## Evidence pack schema highlights

The JSON evidence includes:

- `schema_version`, `generated_at_utc`, `repo_root`
- `git_head_sha`, `git_branch`, `dirty_tree_status`
- `status`, `failed_step`, `warnings`, `blockers`, `disclaimers`
- `command_results[]` with `name`, `command` (redacted), `cwd`, `exit_code`, `status`, `duration_seconds`, `stdout_tail`, `stderr_tail`

Redaction covers environment snapshots, command arguments, and output tails for token/key/secret/password/bearer patterns.

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
- Relative output paths are resolved under artifact root on Windows and Linux/macOS alike.

## Linux/macOS notes

- Keep `deployment.env` permission-restricted when used in the same session (`chmod 600 deployment.env`).
- Use explicit `--token-source env-file` for API smoke if the API was started from `deployment.env`.

## Evidence cleanup

Generated local evidence should stay local and uncommitted:

```bash
git status --short
rm -rf artifacts/release_verification/latest
```
