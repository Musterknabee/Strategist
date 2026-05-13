# Repository truth certification failure — investigation and repair

## Scope

This note addresses **Research-and-Paper-Discovery** certification reporting **`failed_step: repository_truth`** in `artifacts/local_certify/latest/local_certify_report.json`, without weakening **repository truth**, skipping gates, or adding product/live authority.

## Canonical failure slice (archived report)

The preserved artifact tree was moved to:

`artifacts/local_certify/latest_failed_repository_truth_20260513T090923Z/`

### Exact failing repository_truth invariants

From the **`repository_truth`** step in `local_certify_report.json` (`exit_code: 1`), **`stdout_tail`** showed substring gates failing under the **`release_candidate_*`** family, including (representative list):

| Check id | Failure detail (from stdout_tail) |
| --- | --- |
| `release_candidate_environment_gate_present` | assessment does not include `scripts/environment_check.py` |
| `release_candidate_source_health_gate_present` | assessment does not include `scripts/source_health.py` |
| `release_candidate_repository_truth_gate_present` | assessment does not include `scripts/repository_truth_check.py` |
| `release_candidate_migration_truth_gate_present` | assessment does not include `scripts/migration_truth_check.py` |
| `release_candidate_environment_gate_includes_dev_extra` | must validate dev dependencies required by pytest/import-linter checks |
| `release_candidate_environment_gate_precedes_pytest` | must run environment gate before pytest-backed checks |
| `release_candidate_migration_truth_precedes_environment_gate` | must run migration truth before dependency-heavy environment gates |
| `release_candidate_assessment_verifies_bundle_first` | must verify bundle membership before readiness checks |
| `release_candidate_assessment_records_bundle_verify` | must record bundle verification in schema 2 assessment output |
| *(additional)* | cleanup/archive fallback/bundle-verify structural gates tied to the same concatenated source corpus |

### certify_run.log

Review `artifacts/local_certify/latest_failed_repository_truth_20260513T090923Z/certify_run.log` alongside `local_certify_report.json` for the full transcript.

## Root cause classification

**Primary:** **CI/local parity and workflow drift around CLI decomposition** — `scripts/repository_truth_check.py` evaluates release-candidate contracts via `_concat_tracked_sources(...)` over:

- `strategy_validator/cli/release_candidate.py`
- `strategy_validator/cli/release_candidate_assessment.py`
- `strategy_validator/cli/release_candidate_bundle.py`
- `strategy_validator/cli/release_candidate_cleanup.py`
- `strategy_validator/cli/release_candidate_common.py`

If that corpus does not contain the required literals (gate scripts, ordering markers such as `run_check("migration-truth"` before `run_check("environment-check"`, bundle-verify/schema markers, cleanup helpers), **`repository_truth_check.py` exits non-zero**, which surfaces as **`failed_step: repository_truth`** in `local_certify`.

On **2026-05-13**, rerunning `python scripts/repository_truth_check.py` against **current** workspace sources showed **all** `release_candidate_*` gates **PASS** — meaning the saved **`FAIL`** report reflected **stale or superseded tree state** relative to the repository files now on disk (notably post-decomposition parity).

**Secondary observation:** The archived **`local_certify_report.json`** embeds **later** timestamps (for example shard proofs) **after** an earlier **`repository_truth`** failure timestamp — treat **`failed_step`** plus embedded summaries carefully when diagnosing mixed-run artifact folders.

## Before / after — gate scripts only

| Command | Before (archived failing report context) | After (repair verification pass) |
| --- | --- | --- |
| `python scripts/repository_truth_check.py` | FAIL at repository_truth step (embedded report) | **PASS** (exit code 0) |
| `python scripts/migration_truth_check.py` | (not re-blocking repository_truth once restored) | **PASS** |
| `python scripts/package_repo.py --check` | N/A for repository_truth root slice | **PASS** |
| `python scripts/public_surface_dashboard.py --json` | N/A for repository_truth root slice | **`"ok": true`** |

## Full `local_certify` / verify-chain status (operator machine)

`local_certify` only writes `artifacts/local_certify/latest/local_certify_report.json` at **end of run** (after all planned steps and validation). **Long foreground runs** in this environment were **truncated** before that final write, leaving `artifacts/local_certify/latest/` without a fresh `local_certify_report.json`. That is **not** a repository_truth regression — repeat certification **locally** until the process completes (~18–25 minutes typical):

```powershell
python scripts/local_certify.py --certify-research-paper-discovery --json
python -c "import json; print(json.load(open('artifacts/local_certify/latest/local_certify_report.json'))['status'])"
```

Then run the verify chain from `docs/audits/final_research_paper_discovery_certification.md` (steps 10 in the mission checklist).

**Sanity:** Verifying the **archived** failing report with `--verify-report` produced **exit code 1** (nonzero), confirming `local_certify.py --verify-report` surfaces failure correctly when invoked directly from Python.

## Commands executed during repair verification

```powershell
python -m compileall -q strategy_validator tests scripts
python scripts/source_health.py
python scripts/repository_truth_check.py
python scripts/migration_truth_check.py
python scripts/package_repo.py --check
python scripts/public_surface_dashboard.py --json
git status --short
```

Full certification was **re-run** after archiving stale artifacts:

```powershell
python scripts/local_certify.py --certify-research-paper-discovery --json
```

Follow-on verification (when `artifacts/local_certify/latest/local_certify_report.json` reports **`status: PASS`**):

```powershell
python scripts/local_certify.py --verify-report artifacts/local_certify/latest/local_certify_report.json --json
python scripts/local_certify.py --verify-phase-profile-plan artifacts/local_certify/latest/research_paper_discovery_profile_plan.json --json
python scripts/local_certify.py --verify-phase-run-report artifacts/local_certify/latest/research_paper_discovery_phase_run_report.json --json
python scripts/local_certify.py --verify-phase-closure-report artifacts/local_certify/latest/research_paper_discovery_closure_report.json --json
python scripts/local_certify.py --verify-phase-evidence-bundle artifacts/local_certify/latest/research_paper_discovery_evidence_bundle.json --json
python scripts/local_certify.py --verify-final-phase-certificate docs/audits/final_research_paper_discovery_certification.md --json
```

## Repository files changed for repository_truth repair

**None.** Current HEAD already satisfies `_concat_tracked_sources` release-candidate substring gates and **`repository_truth_check.py`** exits **0**. Operational repair steps were **archive stale `latest/`**, **rerun gates**, and **rerun certification**.

## Terminal runner / Python exit code masking

`scripts/local_certify.py` returns **`failed.exit_code or 1`** when `failed is not None`, and **`1`** when research-paper-discovery phase validation blockers exist — **Python exits non-zero on FAIL**.

If **PowerShell** shows **`exit_code: 0`** despite **`status: FAIL`** in the JSON report, common causes are:

- piping (`|`) without preserving **`$LASTEXITCODE`**
- running **`cmd /c`** wrappers that swallow codes
- **`Start-Process`** without `-Wait` / `-PassThru` exit code inspection

**Recommended PowerShell pattern:**

```powershell
python scripts/local_certify.py --certify-research-paper-discovery --json
if (-not $?) { exit $LASTEXITCODE }
```

## No-live-authority and paper/live firewall

No certification logic, broker surfaces, or tokens were changed as part of repository_truth repair. Repository truth edits were **not** applied beyond documenting parity and refreshing artifacts.

The archived failing report still carries embedded **`certification_profile_contract`** assertions (`paper_pass_live_authority_firewall_required`, `read_plane_only_required`) unchanged — repair did **not** relax those constraints.

## Paper/live firewall confirmation

This repair note does not alter paper/live boundaries or trading posture; it documents **repository_truth** parity with **release-candidate decomposition** sources only.
