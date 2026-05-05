# Branch Deletion Audit

- Generated at: `2026-05-05T15:23Z` (local audit session)
- Main SHA: `85c7fa1`
- Scope: remote non-main branch stewardship + safe cleanup
- Safety notice: branch audit only; no production deployment approval, no operator signoff, no live-trading implication, no profitability claim.

## Open PRs At Audit Time

- PR #27 `hardening/evidence-bundle-index-and-discovery` -> `main` (open)

## Classification Table

| Branch | Classification | Rationale |
|---|---|---|
| `main` | `KEEP_MAIN` | Main is never deleted. |
| `hardening/evidence-bundle-index-and-discovery` | `OPEN_PR_DO_NOT_DELETE` | Open PR #27 exists. |
| `ui/demo-mode-and-cockpit-acceptance-pack` | `UI_OWNED_DO_NOT_DELETE` | UI/Codex-owned branch; PR #13 is merged but operator did not explicitly approve deletion in this run. |
| `hardening/artifact-root-governance` | `SUPERSEDED_SAFE_TO_DELETE` | PR #21 merged into `main`; no open PR; branch purpose already squashed/merged. |
| `hardening/replay-verifier-portability-and-redaction` | `SUPERSEDED_SAFE_TO_DELETE` | PR #16 merged into `main`; no open PR; superseded by merged main history. |
| `ops/main-release-verification-evidence-pack` | `SUPERSEDED_SAFE_TO_DELETE` | PR #11 merged into `main`; no open PR. |
| `ops/operator-ease-of-use-command-pack` | `SUPERSEDED_SAFE_TO_DELETE` | PR #14 merged into `main`; no open PR. |
| `ops/stale-branch-retirement-audit` | `SUPERSEDED_SAFE_TO_DELETE` | PR #15 merged into `main`; no open PR. |
| `codex/run-release-verification-lanes` | `NO_COMMON_ANCESTOR_DO_NOT_DELETE` | No common ancestor with `origin/main`; unsafe to delete automatically. |
| `release/convergence-pass` | `NO_COMMON_ANCESTOR_DO_NOT_DELETE` | No common ancestor with `origin/main`; keep for manual review. |
| `release/convergence-pass-2` | `NO_COMMON_ANCESTOR_DO_NOT_DELETE` | No common ancestor with `origin/main`; keep for manual review. |

## Deletion Actions Executed

Deleted remote branches (safe/superseded only):

- `hardening/artifact-root-governance`
- `hardening/replay-verifier-portability-and-redaction`
- `ops/main-release-verification-evidence-pack`
- `ops/operator-ease-of-use-command-pack`
- `ops/stale-branch-retirement-audit`

Exact command executed:

```bash
git push origin --delete hardening/artifact-root-governance hardening/replay-verifier-portability-and-redaction ops/main-release-verification-evidence-pack ops/operator-ease-of-use-command-pack ops/stale-branch-retirement-audit
```

## Not Deleted

- `main` (policy)
- `hardening/evidence-bundle-index-and-discovery` (open PR)
- `ui/demo-mode-and-cockpit-acceptance-pack` (UI-owned + no explicit operator delete confirmation in this run)
- `codex/run-release-verification-lanes` (no common ancestor)
- `release/convergence-pass` (no common ancestor)
- `release/convergence-pass-2` (no common ancestor)

## Safety Policy Applied

- Never delete `main`.
- Never delete open-PR branches.
- Never delete UI-owned branch without explicit operator confirmation.
- Never delete no-common-ancestor branches.
- Never infer safety from naming alone; require merged/superseded PR evidence and no open PR.
- No PR closure automation, no force-push, no history rewrite.
