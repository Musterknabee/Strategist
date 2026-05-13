# Phase profile validation proof chain repair

## Executive summary

Research-and-Paper-Discovery phase certification was exiting **1** at `research_paper_discovery_profile_validation` with nested failures on `local_certify_report` verification, closure, and evidence bundle. Investigation showed these were **cascading** from an earlier integrity break, not independent gate regressions.

## Root blocker

**Pytest subprocess tests overwrote canonical phase artifacts while a full `--certify-research-paper-discovery` run was still in progress.**

Specifically, these tests invoked `python scripts/local_certify.py --certify-research-paper-discovery --skip-frontend ...` against the real repo and wrote to default paths under `artifacts/local_certify/latest/` (notably `research_paper_discovery_profile_plan.json` and related files). Those tests run inside the same pytest process tree as the long phase certification (pytest execution shards). The subprocess replaced the **on-disk** profile plan (and other artifacts) with a **FAIL** `skip_frontend` plan after the parent run had already embedded the **PASS** plan summary and SHA256 in `local_certify_report.json`.

At end-of-run, `verify_local_certify_report` correctly enforced:

- `LOCAL_CERTIFY_RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_SHA256_MISMATCH` (embedded summary vs current file),
- `LOCAL_CERTIFY_RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_CURRENT_VALIDATION_FAILED` (re-validating the tampered-on-disk plan),
- `LOCAL_CERTIFY_REPORT_UNEXPECTED_STEPS:frontend_preflight` because `_expected_local_certify_step_names` omitted the `frontend_preflight` step that the phase profile records.

**First root failure in the chain:** cross-talk from subprocess tests mutating canonical artifacts (`research_paper_discovery_profile_plan.json` and neighbors), not closure or bundle logic in isolation.

## Downstream blockers (cascades)

Once `local_certify_report_verification` was **FAIL**, the phase profile intentionally appended:

- `RESEARCH_PAPER_DISCOVERY_PROFILE_LOCAL_CERTIFY_REPORT_VERIFICATION_NOT_PASSING:FAIL`
- `RESEARCH_PAPER_DISCOVERY_PROFILE_CLOSURE_NOT_PASSING:FAIL`
- `RESEARCH_PAPER_DISCOVERY_PROFILE_EVIDENCE_BUNDLE_NOT_PASSING:FAIL`

and the phase run report echoed the same dependency via `RESEARCH_PAPER_DISCOVERY_PHASE_RUN_*` codes. Treating closure or bundle as separate root causes would be incorrect.

## Fixes implemented

1. **Artifact path isolation for subprocess tests**  
   Added optional CLI overrides and a restoring context manager in `scripts/local_certify.py`:

   - `--local-certify-report-output`
   - `--frontend-preflight-report-output`
   - `--python-core-report-output`

   The main certify path runs under `_temporary_certify_artifact_paths(args)` so overrides apply for the subprocess lifetime and restore module globals on exit (safe for in-process test callers).

2. **Expected step manifest for the discovery profile**  
   `_expected_local_certify_step_names` now prefixes `frontend_preflight` when `certification_profile == RESEARCH_AND_PAPER_DISCOVERY`, matching the actual step list emitted for that profile.

3. **Final certificate index path consistency**  
   `write_final_research_paper_discovery_certification_index` is invoked with `output_path=args.final_phase_certificate_index_output`, and JSON stdout reports `final_phase_certificate_index_path` from the same argument (supports isolated runs).

4. **Regression tests**  
   - `tests/scripts/test_local_certify_plan_matches_ci_validate.py`: subprocess tests now pass isolated paths under `tmp_path`.  
   - `tests/scripts/test_local_certify_phase_profile_proof_chain.py`: proves expected step ordering, context manager restoration, phase run blocker codes for nested verification failure, and absence of false closure/bundle failures when nested proofs pass.

## Files changed

| File | Change |
| --- | --- |
| `scripts/local_certify.py` | `contextlib` import; `_temporary_certify_artifact_paths`; expected-step fix; `with` wrapper; new CLI flags; final index output wiring |
| `tests/scripts/test_local_certify_plan_matches_ci_validate.py` | Isolated paths for three subprocess-based discovery tests |
| `tests/scripts/test_local_certify_phase_profile_proof_chain.py` | New regression coverage |

## Commands run (repair validation)

- `python -m compileall -q strategy_validator tests scripts`
- `python scripts/source_health.py`
- `python scripts/repository_truth_check.py`
- `python scripts/migration_truth_check.py`
- `python scripts/package_repo.py --check`
- `python scripts/public_surface_dashboard.py --json`
- `python scripts/local_certify.py --verify-final-phase-certificate docs/audits/final_research_paper_discovery_certification.md --json` (see status below)
- `python -m pytest tests/scripts/test_local_certify_plan_matches_ci_validate.py::test_research_paper_discovery_profile_fails_fast_on_frontend_preflight_skip tests/scripts/test_local_certify_plan_matches_ci_validate.py::test_research_paper_discovery_profile_plan_only_blocks_skip_frontend tests/scripts/test_local_certify_plan_matches_ci_validate.py::test_research_paper_discovery_phase_run_report_records_full_profile_blocker tests/scripts/test_local_certify_phase_profile_proof_chain.py -q`

## Before / after status

| Check | Before | After (code + tests) |
| --- | --- | --- |
| Root cause | Canonical artifacts mutated mid-flight by pytest subprocess | Subprocess tests write under `tmp_path` only |
| `LOCAL_CERTIFY_REPORT_UNEXPECTED_STEPS:frontend_preflight` | Could fire on valid phase reports | `frontend_preflight` included in expected steps for the profile |
| Stale workspace `artifacts/local_certify/latest/*` | May still reflect old failed runs | **Re-run** full `--certify-research-paper-discovery` to refresh; verify-final and verify-report depend on fresh artifacts |

## Frontend proof

The defect was **not** “frontend certify failed in CI”; real frontend proof in the captured failing run was **PASS**. The shared `frontend_preflight_report.json` on disk could show **FAIL** after a stray `--skip-frontend` subprocess; isolation prevents that class of corruption. A full green phase run still requires `npm ci` / `npm run certify` under `ui/strategist-web` as documented in the final certificate.

## Final certificate verification

`python scripts/local_certify.py --verify-final-phase-certificate docs/audits/final_research_paper_discovery_certification.md --json` was executed in the workspace **before** a fresh full phase re-run. It reported **FAIL** because several canonical verification sidecars were missing or stale (for example `research_paper_discovery_closure_report_verification.json`), and some embedded artifact statuses were **FAIL** from the prior corrupted artifact set. The markdown certificate already contains the required phrase **PAPER_EVIDENCE_PASSED is not LIVE_READY** (and related assertions); `missing_assertion_phrases` was empty in the verifier output.

**After a successful full** `python scripts/local_certify.py --certify-research-paper-discovery --json`, re-run the verify-report / verify-phase-* / verify-final chain so indexes and sidecars align with disk.

## No-live-authority and paper/live firewall

No changes introduced live broker authority. Phase closure and final index semantics remain **read-plane / evidence-only**. The verifier output continued to report `no_live_authority_assertion: true`, `paper_live_firewall_assertion: true`, and `not_autonomous_live_trading_assertion: true` where those fields were evaluated.

## Branch

`repair/phase-profile-validation-proof-chain`
