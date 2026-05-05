# Local operator command center

This document is the human-facing map for **copy-only CLI hints** shown in the Strategist operator cockpit (`ui/strategist-web`). The browser **never** executes shell commands; it only displays strings from `ui/strategist-web/lib/operator/local-ops-command-registry.json`, which is enforced by `python scripts/repository_truth_check.py` (`local_ops_command_registry_mapped`).

## Safety classes

| Class | Meaning |
| --- | --- |
| `READ_ONLY` | Local checks that should not mutate deployment artifacts (verify, dry-run style). |
| `LOCAL_OPERATOR_ACTION` | Mutates local ledger, artifacts, or evidence directories — run only with intent and backups where appropriate. |
| `PRODUCTION_SENSITIVE` | Targets real env files or live API bases; may require tokens or production readiness outside the UI. Never paste secrets into the cockpit. |
| `AUTH_REQUIRED` | Governed **mutation plane** actions (e.g. workboard commands) use `POST /ui/commands/{action}` with operator headers and an explicit mutation token — not bash strings in this registry. |

## Command → evidence → cockpit → gate

| Operator intent | Console / script | Evidence / artifact | Cockpit / API | CI / truth |
| --- | --- | --- | --- | --- |
| Release candidate | `strategy-validator-release-candidate` | `artifacts/release_candidate/` | Release control pane; `/ui/evidence` | `repository_truth_check.py`; clean-archive jobs in CI |
| Clean archive plan | `python scripts/package_repo.py --check` | JSON selection plan | Release control pane | CI `package_repo.py --check` |
| Verify ZIP | `python scripts/verify_repo_archive.py` | `repo_archive_verify/v1` | Release control; `/ui/evidence` | CI verify step; `source_health.py` |
| Single-tenant acceptance | `strategy-validator-single-tenant-acceptance` | `single_tenant_deployment_acceptance/v1` | First-run + release panes; `/ui/evidence` | `repository_truth_check.py` |
| API smoke | `strategy-validator-single-tenant-api-smoke` | `single_tenant_api_http_smoke/v1` | First-run + release panes | `repository_truth_check.py` |
| Deployment evidence | `strategy-validator-single-tenant-evidence` | `single_tenant_deployment_evidence/v1` | First-run, provider readiness, release panes; `GET /ui/evidence` | `repository_truth_check.py` |
| Env validation | `strategy-validator-deployment-env-check` | `single_tenant_deployment_env_check/v1` | First-run wizard | `deployment.env.sample` hygiene in truth checks where wired |
| Migrate | `strategy-validator-migrate` | SQLite schema version | First-run wizard | `migration_truth_check.py`; CI |
| Preflight | `strategy-validator-single-tenant-preflight` | `single_tenant_deployment_preflight/v1` | First-run wizard | `repository_truth_check.py` |
| Research OS release readiness | `strategy-validator-research-os-release-readiness` | Artifacts under `artifacts/` | Release control; `GET /ui/research-os/release-readiness/latest` | `repository_truth_check.py` |
| Research OS handoff | `strategy-validator-research-os-handoff` | Handoff bundle | Release control; `GET /ui/research-os/handoff/latest` | `repository_truth_check.py` |
| Handoff verify / signoff | `strategy-validator-research-os-handoff-signoff` | Verification + signoff JSON | Release control; `GET /ui/research-os/handoff-signoff/latest` | `repository_truth_check.py` |
| Review journal | `strategy-validator-research-os-review-journal` | Journal artifact | Release control; `GET /ui/research-os/review-journal/latest` | `repository_truth_check.py` |

## Deeper runbooks

- Single-tenant flow: `docs/deployment/SINGLE_TENANT_DEPLOYMENT_READINESS.md`
- Research OS: `docs/strategy_lab/RESEARCH_OS_RELEASE_READINESS.md`, `RESEARCH_OS_HANDOFF.md`, `RESEARCH_OS_HANDOFF_SIGNOFF.md`, `RESEARCH_OS_REVIEW_JOURNAL.md`
- Operator posture: `docs/OPERATOR_RUNBOOK.md`

## Cockpit evidence packet viewer

Structured checklist (artifact presence, digests, blockers) from read-plane GETs only: **`docs/EVIDENCE_PACKET_RUNBOOK_VIEWER.md`**.

## Auditing

1. Every `strategy-validator-*` primary entry in the JSON registry must exist under `[project.scripts]` in `pyproject.toml`.
2. Every `python scripts/*.py` reference must exist on disk.
3. Every `docPath` must exist (this file satisfies entries that point here).
4. `PRODUCTION_SENSITIVE` rows must carry a non-empty `productionWarning`.
5. Command text must not embed token/secret patterns (enforced by `repository_truth_check.py`).

## Console script names (packaged)

The following names appear in cockpit hints and **must** remain in sync with `pyproject.toml`:

- `strategy-validator-release-candidate`
- `strategy-validator-single-tenant-evidence`
- `strategy-validator-single-tenant-acceptance`
- `strategy-validator-single-tenant-api-smoke`
- `strategy-validator-deployment-env-check`
- `strategy-validator-migrate`
- `strategy-validator-single-tenant-preflight`
- `strategy-validator-research-os-release-readiness`
- `strategy-validator-research-os-handoff`
- `strategy-validator-research-os-handoff-signoff`
- `strategy-validator-research-os-review-journal`
