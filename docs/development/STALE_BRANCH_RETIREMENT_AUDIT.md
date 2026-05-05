# Stale Branch Retirement Audit

- Date (UTC): 2026-05-05
- Main SHA: `05e3b64`
- Audit scope: local and remote non-main branches visible from `origin/main`

## Disclaimers

- Audit only.
- No branch deletion performed.
- No production deployment approval.
- No operator signoff.
- No live trading implication.

## Classification Meanings

- `KEEP_MAIN`: always retain `main`.
- `OPEN_PR_DO_NOT_DELETE`: branch has an open pull request.
- `MERGED_SAFE_TO_DELETE`: proven merged into `origin/main` and no open PR.
- `SUPERSEDED_NEEDS_OPERATOR_CONFIRMATION`: branch appears functionally replaced by a newer branch/PR, but requires explicit operator confirmation before deletion.
- `STALE_NEEDS_MANUAL_REVIEW`: branch not merged and no open PR; requires human review.
- `NO_COMMON_ANCESTOR_DO_NOT_DELETE`: branch history diverges with no merge-base against `origin/main`.
- `UNKNOWN_DO_NOT_DELETE`: insufficient confidence from local/remote evidence.

## Branch Audit Table

| Branch | Latest commit | Ahead/behind vs main | Common ancestor | Open PR | Classification | Recommended action | Safe delete command | Rationale |
|---|---|---:|---|---|---|---|---|---|
| `main` | `05e3b64` | n/a | yes | n/a | `KEEP_MAIN` | Keep | none | Main branch is never deletable. |
| `origin/codex/run-release-verification-lanes` | `7748bdd` | unknown (no merge-base) | no | no | `NO_COMMON_ANCESTOR_DO_NOT_DELETE` | Do not delete | none | No merge-base with `origin/main`; classify as isolated history. |
| `origin/release/convergence-pass` | `95a8269` | unknown (no merge-base) | no | no | `NO_COMMON_ANCESTOR_DO_NOT_DELETE` | Do not delete | none | No merge-base with `origin/main`; requires manual historical context. |
| `origin/release/convergence-pass-2` | `5a4e961` | unknown (no merge-base) | no | no | `NO_COMMON_ANCESTOR_DO_NOT_DELETE` | Do not delete | none | No merge-base with `origin/main`; do not automate retirement. |
| `origin/ops/main-release-verification-evidence-pack` | `cbb1ea7` | ahead 1 / behind 0 | yes | no | `SUPERSEDED_NEEDS_OPERATOR_CONFIRMATION` | Manual review; likely retire after confirming PR #11 merge is authoritative | local only: `git branch -d ops/main-release-verification-evidence-pack` (if local branch is merged and not needed) | Content was merged to main as squash commit `05e3b64`, but head SHA differs due to squash strategy; treat as superseded, not auto-safe. |
| `origin/ops/operator-ease-of-use-command-pack` | `06e99e2` | ahead 1 / behind 0 | yes | yes (PR #14) | `OPEN_PR_DO_NOT_DELETE` | Keep until PR closes | none | Active review branch with open PR. |
| `origin/ui/operator-cockpit-productization-pass` | `70e7ff1` | ahead 2 / behind 0 | yes | yes (PR #12) | `OPEN_PR_DO_NOT_DELETE` | Keep until PR closes | none | Active UI/cockpit PR branch. |
| `origin/ui/demo-mode-and-cockpit-acceptance-pack` | `aa85cee` | ahead 1 / behind 0 | yes | yes (PR #13) | `OPEN_PR_DO_NOT_DELETE` | Keep until PR closes | none | Active demo/acceptance PR branch. |

## Additional Local Branch Notes

These local-only branches were present and should be retired only after manual confirmation:

- `fix/post-merge-pr-queue-stabilization`: `MERGED_SAFE_TO_DELETE` (local suggestion only).
- `integration-main`: `MERGED_SAFE_TO_DELETE` (local suggestion only).
- `local-baseline`: `NO_COMMON_ANCESTOR_DO_NOT_DELETE`.
- `ops/stale-branch-retirement-audit`: current working branch for this audit.
- `ui/operator-cockpit-productization-pass-worktree`: `STALE_NEEDS_MANUAL_REVIEW` (not tracked as remote open-PR branch).

## Safe Deletion Policy

- Never delete `main`.
- Never delete branches with open PRs.
- Never delete branches with no common ancestor with `origin/main`.
- Never delete unknown classification branches.
- For squash-merged branches, require explicit supersession confirmation before deletion.
- Prefer local branch cleanup first; remote branch deletion is always manual and explicit.

## Operator Review Commands

```bash
git fetch origin --prune
gh pr list --state open
python scripts/branch_cleanup_audit.py --json
git branch -r --merged origin/main
git branch -r --no-merged origin/main
git merge-base origin/main origin/<branch>
git log --oneline origin/main..origin/<branch> --max-count=20
git diff --stat origin/main...origin/<branch>
```

## Local Deletion Commands (Only When Safe)

Run only after confirming branch is merged and has no open PR:

```bash
git branch -d fix/post-merge-pr-queue-stabilization
git branch -d integration-main
```

## Remote Deletion Commands (Manual Suggestion Only)

Do not run automatically. Run only after explicit operator confirmation:

```bash
git push origin --delete <branch>
```

Use this only for branches that are closed, superseded/merged, have a common ancestor with `origin/main`, and have no open PR.
