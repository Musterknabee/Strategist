# Evidence Bundle Index

## Purpose

`strategy-validator-evidence-index` builds a read-only local discovery index over known backend/ops evidence outputs under the governed artifact root.

This index helps operators find evidence without relying on memory or shell history.

## What It Discovers

Conventional artifact-root paths:

- `release_verification/latest/main-release-verification-pack.json`
- `release_verification/latest/main-release-verification-pack.md`
- `release_verification/latest/branch-cleanup-audit.json`
- `provider_paper_loop/latest/replay_manifest.json`
- `provider_paper_loop/latest/provider_evidence_manifest.json`
- `release_verification/latest/operator-doctor.json`
- `release_verification/latest/operator-doctor.md`
- `release_verification/latest/repo-handoff.zip`
- `release_verification/latest/repo-handoff.verify.json`
- `release_verification/latest/production-smoke-readiness.json`

## Command Usage

### Windows / PowerShell

```powershell
strategy-validator-evidence-index --json --artifact-root artifacts --output-path artifacts/evidence-index.json
```

### Linux / macOS

```bash
strategy-validator-evidence-index --json --artifact-root artifacts --output-path artifacts/evidence-index.json
```

Optional digest mode:

```bash
strategy-validator-evidence-index --json --artifact-root artifacts --include-digests
```

## Status Interpretation

- `exists=true` means the file is present at discovery time.
- `status` is discovery posture only (`OK` or `PENDING` by default).
- `verified_integrity=true` is only set when explicit verification evidence is discovered (for example a repository archive verification JSON report).
- Missing optional files remain `PENDING`; this does not fail the command by default.

## Safety Semantics

- Evidence discovery is not deployment approval.
- Evidence discovery is not operator signoff.
- Evidence discovery is not live trading authorization.
- Evidence discovery is not profitability evidence.
- Optional missing artifacts can remain `UNKNOWN`/`PENDING`.
- Digest presence is not strategy quality.

## Relationship To Verification

- Release verification pack (`main_release_verification_pack`) is a producer of evidence.
- Replay verification (`strategy-validator-paper-research-replay-verify`) validates replay digest chains.
- Repository archive verification (`verify_repo_archive.py`) validates archive membership/digests.
- Evidence index discovery does not run those workflows automatically.

## Artifact Root And Path Safety

- Discovery is constrained to the governed artifact root.
- Output JSON path must remain under artifact root or command returns non-zero with `ARTIFACT_OUTPUT_OUTSIDE_ROOT`.
- No network calls, no provider keys required, no ledger mutation.

## Cleanup

Generated local evidence index files should remain uncommitted:

```bash
rm -f artifacts/evidence-index.json
git status --short
```
