# Branch consolidation audit

**Repository:** `Musterknabee/Strategist`  
**Branch:** `chore/consolidate-branches-to-main`  
**Base:** `origin/main` @ `98981d2a3eef26c977638f8c19d91fa3cffcc536`  
**Date:** 2026-05-14

## Executive summary

This consolidation branch **does not** wholesale-merge every remote branch. It applies **low-risk, verifiable** deltas on top of current `main`, records audit evidence, and documents why larger branches (especially `repair/phase-profile-validation-proof-chain` tip and PR #32 snapshot commit) were **not** merged as-is.

### Integrated on this branch

| Source | Method | Notes |
|--------|--------|------|
| `docs/add-top-level-readme` | Cherry-pick | Top-level `README.md`. |
| `feature/evidence-index-markdown-summary` | Cherry-pick | `evidence_bundle_index_markdown.py`. |
| PR #32 audit (second commit only) | Doc import | `full_system_test_setup_and_readiness_audit.md` — **not** the snapshot commit that reintroduced `NEXT_*` ledgers. |
| `main` hygiene | Code fix | Added `research_integrity_validator_handoff_ingress_certificate.py` and wired import in `research_integrity_validator_handoff.py` so ingress certificate checksum helpers are defined (fixes latent `NameError` on `main`). |
| Pytest | Config | `addopts` includes `--import-mode=importlib` plus plugin disables to fix duplicate test module basename collection. |

### Explicitly not merged (and why)

| Item | Reason |
|------|--------|
| `repair/phase-profile-validation-proof-chain` (full series) | Tip commit thins `release_candidate.py` to import `release_candidate_assessment` / `bundle` / `cleanup` modules that **were not present** in the same commit series on the remote; cherry-picking produced a broken tree (`repository_truth_check` mass FAIL, missing imports). **Do not merge that branch until the repair series is self-consistent on GitHub.** |
| PR #32 first commit (`snapshot: pre-audit working tree state`) | Reintroduces `NEXT_SEMANTIC_VALIDATOR_HANDOFF_*` ledger spam and huge generated deltas — excluded per consolidation brief. |
| `hardening/evidence-bundle-index-and-discovery` | Already landed on `main` via prior merge (#27); cherry-pick was empty. |
| `ui/cockpit-operability-recovery-one-shot` | Already absorbed on `main` (#30); cherry-pick was empty. |
| `release/convergence-pass`, `release/convergence-pass-2`, `codex/run-release-verification-lanes` | **No common ancestor** with `main` — orphan/archive only. |

## Safety invariants

- No live trading, broker orders, wallet integration, or production deployment approval.
- No fake readiness; missing evidence stays UNKNOWN/PENDING/DEGRADED/BLOCKED.
- No secrets, real tokens, or local runtime artifacts committed.

## Remote branch table (vs `origin/main`)

| Branch | Ahead | Behind | Merge-base | Classification |
|--------|------:|-------:|------------|------------------|
| `audit/full-system-test-setup-and-readiness` | 2 | 0 | `98981d2` | Manual — snapshot excluded; audit doc copied |
| `docs/add-top-level-readme` | 1 | 18 | (diverged) | Cherry-picked |
| `ui/cockpit-operability-recovery-one-shot` | 1 | 3 | `85c7fa1` | Already in main |
| `hardening/production-placeholder-token-fail-closed` | 0 | 0 | `98981d2` | Safe delete candidate |
| `strategist-updated` | 0 | 0 | `98981d2` | Safe delete candidate |
| `feature/research-os-review-journal-acceptance-gate` | 0 | 0 | `98981d2` | Safe delete candidate |
| `feature/evidence-index-markdown-summary` | 1 | 0 | `98981d2` | Cherry-picked |
| `hardening/evidence-bundle-index-and-discovery` | 2 | 3 | `85c7fa1` | Already in main |
| `repair/phase-profile-validation-proof-chain` | 13 | 0 | `98981d2` | **Blocked** until split modules ship with thin `release_candidate` |
| `ui/cockpit-polish-after-ops-cleanup` | 1 | 1 | `daa5b9f` | Duplicate review vs #29/#30 |
| `ui/demo-mode-and-cockpit-acceptance-pack` | 3 | 15 | `b6293ab` | Stale — cherry-pick only if needed |
| `release/convergence-pass` | 7 | 41 | **NONE** | Orphan — do not merge |
| `release/convergence-pass-2` | 12 | 41 | **NONE** | Orphan — do not merge |
| `codex/run-release-verification-lanes` | 1 | 41 | **NONE** | Orphan — do not merge |

## Validation commands (run on this branch)

Backend (minimum):

```powershell
python -m compileall -q strategy_validator tests scripts
python scripts/source_health.py
python scripts/repository_truth_check.py
python scripts/migration_truth_check.py
python scripts/package_repo.py --check
python -m pytest --collect-only -q
```

Full matrix (when time permits — same as operator brief):

- `python scripts/openapi_contract_snapshot.py --check`
- `python scripts/ui_facade_contract_snapshot.py --check --no-static-fallback`
- `python scripts/frontend_ui_contract_check.py`
- `python -m pytest -q`
- `cd ui/strategist-web; npm ci; npm run contract:check; npm run lint; npm run typecheck; npm run test; npm run acceptance; npm run build; npm run certify`

## PR body checklist

- [ ] List branches integrated vs skipped (see tables above).
- [ ] Paste PASS/FAIL for validation commands.
- [ ] Note repair branch blocker for follow-up PR.
- [ ] Restate safety invariants (no live trading, no broker, no wallet, no fake readiness).

## Remote cleanup recommendations (manual only)

| Branch | Action after PR merge / confirmation |
|--------|-------------------------------------|
| `hardening/production-placeholder-token-fail-closed` | Delete remote |
| `strategist-updated` | Delete remote |
| `feature/research-os-review-journal-acceptance-gate` | Delete remote |
| Orphan branches | Archive names only; do not merge |

## Validation log (2026-05-14)

| Command | Result |
|---------|--------|
| `python -m compileall -q strategy_validator tests scripts` | PASS |
| `python scripts/source_health.py` | PASS |
| `python scripts/repository_truth_check.py` | PASS |
| `python scripts/migration_truth_check.py` | PASS |
| `python scripts/package_repo.py --check` | PASS |
| `python -m pytest --collect-only -q` | PASS (1341 tests collected) |

OpenAPI/UI facade snapshot scripts, full `pytest -q`, and `npm run certify` were not executed in this consolidation session; run them before treating the branch as CI-equivalent.
