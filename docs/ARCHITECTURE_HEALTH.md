# Architecture Health

This document is produced by `scripts/architecture_health_report.py` and tracks the repository's current convergence pressure.

## What the report now tracks

- largest Python files by line count across the live `strategy_validator/*` surface
- package balance across application, API, CLI, governance, contracts, ledger, projections, validator, and the smaller research-chain packages
- tracked hotspot files that currently absorb too much change pressure
- whether the operator/governance shell is outgrowing the underbuilt proposer → tribunal → feature → PIT chain

## Current operating rule

New functionality should prefer:

1. bounded modules under `strategy_validator/application/` or `strategy_validator/control_plane/`
2. explicit contracts under `strategy_validator/contracts/`
3. projection-backed read models under `strategy_validator/projections/`
4. focused validator services or orchestration helpers instead of growth in the largest oracle files

Avoid growing these hotspots further without first splitting them:

- `strategy_validator/validator/oracle_briefing_pack_builders.py`
- `strategy_validator/validator/oracle_briefing_sections.py`
- `strategy_validator/validator/oracle_doctrine_evidence_semiannual.py`
- `strategy_validator/validator/oracle_doctrine_evidence_annual.py`
- `strategy_validator/validator/oracle_diagnostics_status_pack_builders.py`
- `strategy_validator/application/ui_views.py`
- `strategy_validator/application/ui_workboard_intelligence_policy.py`
- `strategy_validator/control_plane/governance_claim_foundations.py`
- `strategy_validator/control_plane/governance_plane_foundations.py`
- `strategy_validator/cli/oracle_strategy_domain_runners.py`

## Interpretation guidance

A pass is converging when:

- line count growth lands in bounded packages instead of the largest files
- CLI compatibility wrappers shrink rather than multiply
- operator actions materialize through projection helpers instead of direct ledger reads inside control-plane snapshots
- journal-backed queue items should carry explicit governed-merge state instead of generic pending-only semantics
- the underbuilt proposer / tribunal / feature-factory / data-spine chain gains one real end-to-end path

## Horizon A/B convergence update

The Horizon A/B patch tranche adds two hard repo-health controls:

- `syntax_health` in `scripts/architecture_health_report.py` now reports the high-gravity syntax sample status. The CI syntax gate now uses `scripts/source_health.py` so the first-pass check is side-effect free and does not create bytecode caches.
- CLI public-surface pressure is back within the configured architecture-health budget: two unreferenced queue transition compatibility wrappers were removed, bringing `cli_file_count` to 159 and restoring the current budget pass.

The same tranche also moves UI workboard assembly through `strategy_validator/application/ui_projection_surfaces.py`, so UI-facing workbench data carries an explicit `read_model_surface` marker instead of being assembled ad hoc by route handlers.


## Horizon C completion update

The Horizon C pass adds a strategic-readiness gate instead of pretending that
frontend productization, credentialed provider automation, multi-tenant scaling,
external workflow orchestration, or broad Oracle expansion are complete.

The controlling implementation is:

- `strategy_validator/application/strategic_horizon_readiness.py`
- `GET /readiness/strategic-horizon` in `strategy_validator/api/routes/readiness.py`
- explicit release-publication path rooting through
  `strategy_validator/application/release_publication_paths.resolve_release_publication_paths`

The rule is now mechanical: later strategic work is blocked/deferred unless the
repository contains concrete evidence for the prerequisite. This preserves the
control-plane architecture while avoiding roadmap inflation.

## Next-slice convergence update

The next tranche makes syntax and environment gates more deterministic for release
handoffs:

- `scripts/source_health.py` provides a side-effect-free AST syntax gate over the
  high-gravity source-health scope. It avoids `compileall` bytecode writes, so it
  cannot create `__pycache__` while proving the historically fragile modules still
  parse.
- `.github/workflows/ci.yml` and `strategy_validator/cli/release_candidate.py`
  now use `scripts/source_health.py` for the fast syntax gate.
- `scripts/environment_check.py` validates the declared Python/runtime dependency
  envelope using distribution metadata instead of importing heavy packages. The
  critical check is `pydantic>=2.6`, matching `pyproject.toml` and preventing the
  Pydantic-v1 false-negative runtime seen in local sandboxes.
- `scripts/architecture_health_report.py` consumes the same source-health gate and
  records the checked scope as high-gravity AST syntax health.

This intentionally does not replace the full test suite. It makes the first
failure mode cheaper and cleaner: invalid source or an incompatible dependency
environment should fail before long pytest or release-candidate execution.

## Repository truth-gate update

The next slice adds `scripts/repository_truth_check.py` as a side-effect-free
configuration integrity gate. It validates that:

- console-script entrypoints declared in `pyproject.toml` map to real modules and
  callable functions
- pytest paths referenced by `.github/workflows/ci.yml` exist on disk
- the optional `ui/strategist-web` workflow remains guarded by package-lock
  presence while the frontend tree is absent
- SQLite migration files and `EXPECTED_SCHEMA_VERSION` remain synchronized
- the Dockerfile keeps production mode and a non-root runtime user

`strategy-validator-release-candidate assess` and the CI syntax-health job now run
this gate before deeper tests. This is intentionally distinct from
`environment_check.py`: repository truth validates files/configuration without
requiring runtime dependencies.

`source_health.py` keeps its default scope high-gravity for deterministic CI and
release assessment. Broader local diagnostics can be run with:

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/source_health.py --repo-owned
```

The high-gravity default is deliberate: in constrained sandboxes, repeatedly AST
parsing the entire tree in one process can hang after hundreds of files even when
package-sliced parsing succeeds. The release gate therefore protects the known
fragile source seams while the repository-truth gate catches stale config drift.

## Repository hygiene hardening update

The follow-on convergence slice closes a practical release-handoff gap: repository
health tooling must not create the transient files that the hygiene gate forbids.

Changes now enforced:

- `scripts/architecture_health_report.py` sets `sys.dont_write_bytecode = True`
  before importing local modules, so architecture-health reporting remains
  side-effect free even when callers forget `PYTHONDONTWRITEBYTECODE=1`.
- `strategy_validator/cli/release_candidate.py` defaults every subprocess spawned
  by assessment to `PYTHONDONTWRITEBYTECODE=1`; release checks should not leave
  `__pycache__` behind.
- `strategy-validator-release-candidate cleanup` removes `__pycache__/`
  directories, not only the contained `.pyc` files.
- `.gitignore` now mirrors the repository hygiene policy for Python caches,
  runtime databases, generated release artifacts, and frontend caches.
- `scripts/repository_truth_check.py` validates `.gitignore` and `.dockerignore`
  hygiene patterns in addition to CI paths, console-script entrypoints,
  migrations, and Docker runtime posture.

This keeps the release-candidate chain honest: source-health, repository-truth,
architecture-health, and cleanup are all expected to be safe to run from a clean
source archive without polluting the next hygiene check.

## Command-policy and repo-truth hardening update

This tranche closes two remaining drift seams in the post-horizon health gates:

- `strategy_validator/application/ui_command_actions.py` now routes the public
  `build_ui_operator_command_receipt_payload(...)` helper through the same
  command-policy shape checks used by `execute_ui_operator_command(...)`. The
  direct compatibility helper can no longer journal targetless operator commands
  or replay an idempotency key against a different target payload.
- `scripts/source_health.py` now reports `source_health/v2` and fails when an
  explicitly requested root or high-gravity file is missing. This prevents a
  deleted fragile module from being silently skipped by the syntax gate.
- `scripts/repository_truth_check.py` now verifies that all default
  source-health roots exist, release-candidate assessment includes the
  environment/source/repository gates, and SQLite migrations record each schema
  version through the expected version.
- `scripts/environment_check.py` now derives runtime dependency requirements
  directly from `[project].dependencies` in `pyproject.toml` instead of carrying
  a separate hardcoded dependency list. The check therefore fails when the local
  environment drifts from packaging metadata, not only when a manually curated
  subset is wrong.

The practical result is a stronger first-line repo truth chain:

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/source_health.py
python scripts/repository_truth_check.py
python scripts/environment_check.py --include-extra dev
```

Use the base `python scripts/environment_check.py` form only for minimal-package
smoke checks that intentionally do not require pytest/import-linter. These gates
remain cheap and side-effect free; they still do not replace the full
pytest/import-linter/release-candidate chain.

## Dev dependency and archive-manifest truth update

The next convergence slice tightens the gap between packaging metadata, CI jobs,
and release-candidate assessment:

- `scripts/environment_check.py` now reports `environment_check/v3` and supports
  `--include-extra dev`. CI jobs that run pytest/import-linter-backed validation
  and `strategy-validator-release-candidate assess` now validate both runtime
  dependencies and the `[project.optional-dependencies].dev` group from
  `pyproject.toml`.
- `scripts/repository_truth_check.py` was expanded to validate that
  CI/release-candidate dev validation uses the dev extra, that
  import-linter contracts point at modules that exist, and that ignored imports
  are well formed.
- `strategy_validator/cli/release_candidate.py` now filters no-git/source-archive
  manifest fallback discovery so generated `artifacts/`, scratch/debug files,
  and transient cache directories cannot be sealed into a release bundle merely
  because the source tree lacks `.git` metadata.

The fast release preflight for developer machines should now be:

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/source_health.py
python scripts/repository_truth_check.py
python scripts/environment_check.py --include-extra dev
PYTHONDONTWRITEBYTECODE=1 python -c "from strategy_validator.cli.hygiene_check import main; raise SystemExit(main([]))"
```

## Clean archive and release-assessment ordering update

This tranche adds a first-class clean handoff archive selector and closes a
release-assessment ordering gap:

- `scripts/package_repo.py` reports `clean_repo_archive/v1` and builds full-repo
  ZIP handoffs while excluding generated release artifacts, scratch/debug files,
  bytecode caches, local virtual environments, dependency folders, and build
  outputs. This gives operators a deterministic archive path instead of relying
  on ad hoc ZIP commands.
- `.github/workflows/ci.yml` runs `python scripts/package_repo.py --check` in the
  syntax/repository-truth lane, so archive-selection drift is caught before deep
  tests.
- `scripts/repository_truth_check.py` now reports `repository_truth_check/v3` and
  verifies that the clean archive tool filters generated directories, that CI
  runs the clean archive gate, and that release-candidate assessment executes the
  environment gate before pytest-backed checks.
- `strategy_validator/cli/release_candidate.py` no longer imports `pytest` before
  `scripts/environment_check.py --include-extra dev` can explain dependency
  drift. Missing or stale dev dependencies should fail at the explicit
  environment gate, not as an opaque import error.

A local archive dry run should now be part of the fast repo-health chain:

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/source_health.py
python scripts/repository_truth_check.py
python scripts/package_repo.py --check
python scripts/environment_check.py --include-extra dev
```

## Next-slices update: deterministic clean archive handoff

The repository health chain now treats clean full-repo handoff archives as a first-class
operator artifact, not an ad-hoc ZIP created outside the repo:

- `.github/workflows/ci.yml` runs both `python scripts/package_repo.py --check` and a
  clean archive build smoke into `$RUNNER_TEMP/strategy-validator-clean.zip`.
- `scripts/package_repo.py` now excludes local archive outputs such as `.zip`, `.tar`,
  `.gz`, and `.tgz`, so a previous handoff archive cannot be accidentally sealed into
  the next handoff.
- Clean archive entries are sorted and written with normalized ZIP metadata and fixed
  regular-file permissions; the report includes `archive_sha256` when an archive is
  actually written.
- `scripts/repository_truth_check.py` now reports `repository_truth_check/v4` and verifies
  that CI builds the archive, that the archive tool is deterministic/digesting, and that
  release-candidate no-git manifests exclude local archive outputs.

This keeps the fast syntax/repository-truth path dependency-light while making the handoff
artifact itself reproducible enough for operator comparison and CI smoke validation.

## Next-slices update: clean archive verification gate

The clean handoff archive path now has a verifier, not only a builder:

- `scripts/verify_repo_archive.py` reports `repo_archive_verify/v1` and compares a
  ZIP produced by `scripts/package_repo.py` against the current clean archive
  selection.
- The verifier checks entry membership, sorted ordering, fixed ZIP timestamps,
  normalized file modes, and per-entry source digests.
- `.github/workflows/ci.yml` now builds `$RUNNER_TEMP/strategy-validator-clean.zip`
  and immediately verifies it with `scripts/verify_repo_archive.py`.
- `scripts/repository_truth_check.py` now reports `repository_truth_check/v5` and
  verifies the archive verifier is present, covered by source-health, and wired
  into CI.

This closes the remaining handoff gap: CI no longer proves only that a clean ZIP
can be written; it also proves that the ZIP faithfully matches the checked-out
repository source/config/docs/tests set.

## Next-slices update: release bundle manifest closure

Release-candidate bundle verification now checks both file digests and manifest
membership:

- `strategy_validator/cli/release_candidate.py` emits bundle manifests with
  `schema: 2` and `content_sha256`, a normalized digest over each manifest
  entry's path, size, and file SHA-256.
- `strategy-validator-release-candidate verify-bundle` now fails when the
  current source selection contains files that are missing from the manifest,
  when manifest paths are stale, when duplicate/malformed paths are present, or
  when the normalized content digest no longer matches.
- `scripts/repository_truth_check.py` now reports `repository_truth_check/v6`
  and verifies that release-candidate manifests include the content digest and
  that bundle verification compares manifest membership against the current
  source selection.

This closes a release-evidence gap: a manifest that omitted a current source
file can no longer verify successfully merely because all listed files still
match their hashes.

## Next-slices update: SQLite migration truth gate

The fast repository-health lane now validates the SQLite migration chain without
opening or mutating the operator's real ledger file:

- `scripts/migration_truth_check.py` reports `migration_truth_check/v1` and runs
  all SQL migrations twice against an in-memory SQLite database.
- The gate verifies that the first and second application both land on
  `EXPECTED_SCHEMA_VERSION`, that the migration chain is idempotent, and that
  required ledger/operator-action tables and indexes exist.
- `.github/workflows/ci.yml` runs the migration truth gate in the dependency-light
  syntax/repository-truth lane.
- `strategy-validator-release-candidate assess` runs migration truth before the
  dependency-heavy environment/pytest checks, so schema drift is reported as a
  direct release-gate failure.
- `scripts/repository_truth_check.py` now reports `repository_truth_check/v7` and
  verifies that the migration truth gate is present, source-health-covered, and
  wired into CI and release-candidate assessment.

This separates schema-chain truth from runtime ledger smoke: the container smoke
still proves the packaged CLI can initialize a ledger path, while migration truth
proves the migration files themselves are complete and idempotent.

## Next-slices update: assessment bundle gate and migration contract depth

The release and schema gates now verify the next layer of evidence integrity:

- `strategy-validator-release-candidate assess` runs bundle verification before
  source, repository, migration, environment, hygiene, or pytest-backed checks.
  Assessment output is now `schema: 2` and records `bundle-verify` as the first
  check, so a stale or incomplete `bundle-manifest.json` blocks the candidate at
  the release-assessment boundary instead of depending on a separate operator
  command.
- `scripts/migration_truth_check.py` now reports `migration_truth_check/v2`. It
  still applies all SQLite migrations twice to an in-memory database, but now
  also verifies the required column contracts and proves the durable operator
  action idempotency unique index rejects duplicate non-empty idempotency keys.
- `scripts/repository_truth_check.py` now reports `repository_truth_check/v8` and
  verifies the release-assessment bundle gate plus the deeper migration-truth
  column/idempotency checks.

This closes two practical gaps: assessment can no longer pass without first
checking the generated bundle membership, and migration truth no longer stops at
"table/index names exist" when the operator journal depends on specific columns
and idempotency uniqueness semantics.

## Next-slices update: archive/runtime-state hygiene closure

This tranche tightens the clean handoff path and release fallback manifest around
runtime-state leakage and deterministic verification:

- `scripts/package_repo.py` now prunes excluded directories during traversal
  instead of walking generated trees and filtering them afterward. This keeps the
  dry-run/build gate fast even when a source archive contains large local
  artifacts.
- Clean repo archives now exclude runtime state suffixes in addition to prior
  archive outputs: `.sqlite`, `.sqlite3`, `.db`, `.db-wal`, `.db-shm`, `.log`,
  and `.jsonl`.
- `scripts/verify_repo_archive.py` now verifies ZIP compression mode as well as
  entry order, fixed timestamps, normalized permissions, exact membership, and
  per-entry digests.
- `strategy_validator/cli/release_candidate.py` now applies the same runtime
  suffix filtering to the no-git/source-archive manifest fallback.
- `scripts/repository_truth_check.py` now reports `repository_truth_check/v9`
  and verifies pruned archive traversal, runtime-state filtering, compression
  verification, and release fallback filtering.

The intended operator invariant is now: a full-repo handoff ZIP contains source,
configs, tests, docs, scripts, and workflows only; it must not contain prior
handoff archives, generated release packets, scratch output, bytecode caches,
local databases, ledger WAL/SHM files, logs, or JSONL event streams.

## Next-slices update: archive self-inclusion guard

This tranche closes a smaller but important clean-handoff edge case: archive
outputs written inside the repository with a non-excluded suffix could become
eligible for the next clean archive or verification pass.

- `scripts/package_repo.py` now reports `clean_repo_archive/v2` and rejects
  output paths under the repo root that would be included in future clean
  archive selections. Operators should write handoff archives outside the repo
  or use an explicitly excluded archive suffix such as `.zip`.
- `scripts/repository_truth_check.py` now reports `repository_truth_check/v10`
  and verifies the self-inclusion guard as part of repository truth.
- `strategy_validator/cli/release_candidate.py` cleanup no longer lists the same
  cache root twice, keeping cleanup evidence stable and easier to audit.

The clean archive path is now protected against both classes of generated-state
leakage: accidental prior archives/runtime files in the source tree, and newly
created archive outputs that would otherwise become future source members.

## Next-slices update: release manifest header verification

This tranche tightens release-bundle evidence semantics beyond membership and
per-file digests:

- `strategy_validator/cli/release_candidate.py` now treats bundle manifest header
  drift as a verification failure. `verify-bundle` validates `schema == 2`,
  `entry_count == len(entries)`, and `content_sha256` shape before accepting a
  candidate manifest.
- `bundle-verify.json` now reports `manifest_error_count`, `manifest_errors`,
  `manifest_schema`, and `declared_entry_count` so operators can distinguish
  file-level digest drift from malformed release evidence metadata.
- `scripts/repository_truth_check.py` now reports `repository_truth_check/v11`
  and verifies that release-bundle verification checks manifest header fields,
  not only source membership and path digests.

The release invariant is now: a candidate can only pass bundle verification when
its manifest header, manifest membership, normalized membership digest, and every
listed source-file digest agree with the current source tree.

## Next-slices update: malformed manifest digest-entry handling

The release-bundle verifier now fails closed with structured evidence when a
manifest entry cannot participate in `content_sha256` recomputation.  In
particular, malformed `size_bytes`, non-hexadecimal entry hashes, invalid paths,
or other digest-entry defects are reported in `bundle-verify.json` via
`malformed` and `manifest_errors` instead of surfacing as uncaught exceptions.

`strategy_validator/cli/release_candidate.py` now canonicalizes manifest digest
entries through a strict normalizer before recomputing the bundle content digest.
`tests/constitutional/test_repo_hygiene_and_release_cleanup.py` covers malformed
size and hash cases.  `scripts/repository_truth_check.py` now reports
`repository_truth_check/v12` and verifies that this malformed-digest-entry path
exists.  `scripts/package_repo.py` also had a duplicate CLI target assignment
removed; repository truth now checks that the clean archive CLI formats its target
exactly once.

## Next-slices update: malformed manifest container handling

Release bundle verification now treats malformed manifest containers as structured
release blockers instead of verifier crashes. `strategy-validator-release-candidate
verify-bundle` writes `bundle-verify.json` with `ok: false` and manifest errors
when `bundle-manifest.json` is invalid JSON, is not a JSON object, or has an
`entries` value that is not a list.

This extends the prior digest-entry hardening: malformed manifest *headers*,
malformed digest entries, and malformed manifest containers now all fail through
machine-readable release evidence. `scripts/repository_truth_check.py` now
reports `repository_truth_check/v13` and includes
`release_candidate_bundle_verify_handles_malformed_manifest_container` so this
behavior remains part of the dependency-light repository truth gate.

## Next-slices update: non-regular manifest path handling

Release bundle verification now treats manifest entries that resolve to
non-regular paths as controlled release-evidence failures. If a manifest entry
points at a directory or an unreadable path, `strategy-validator-release-candidate
verify-bundle` records the defect in `bundle-verify.json` under `malformed`
instead of attempting to hash the path and crashing.

`scripts/repository_truth_check.py` now reports `repository_truth_check/v14` and
includes `release_candidate_bundle_verify_handles_non_regular_manifest_paths` so
this edge-case hardening remains part of the dependency-light repository truth
gate.

## Next-slices update: release candidate path containment

Release-candidate artifact directories are now protected against path traversal
and accidental nested path writes. `strategy_validator/cli/release_candidate.py`
validates candidate identifiers with a bounded character allowlist before using
an identifier as an artifact path segment. Candidate ids may contain letters,
digits, dots, underscores, and dashes; path separators, empty ids, `.` and `..`
are rejected.

`scripts/repository_truth_check.py` now reports `repository_truth_check/v15` and
includes `release_candidate_rejects_path_traversal_candidate_ids` so candidate-id
path containment remains part of the dependency-light repository truth gate.

## Next-slices update: symlink-safe release and archive evidence

Release and handoff evidence now explicitly reject symbolic links. Clean repo
archives exclude symlinks during source selection, and release-candidate manifest
generation refuses to seal tracked symlink paths. Bundle verification also treats
manifest entries that resolve to symlinks as structured malformed release
evidence rather than hashing the symlink target.

This closes a subtle evidence-integrity gap: a symlink can point outside the
repository or change target semantics independently from the path shown in the
manifest. `scripts/repository_truth_check.py` now reports
`repository_truth_check/v16` and verifies both clean-archive symlink exclusion
and release-candidate symlink rejection.

## Next-slice update: canonical release manifest paths

Release-candidate bundle verification now rejects non-canonical manifest path aliases before hashing source content. Manifest entries must be repo-relative POSIX paths exactly as generated by `Path.as_posix()`; aliases such as `./file`, duplicate slashes, `a/./b`, backslashes, absolute paths, and traversal segments are controlled release-evidence failures. This keeps manifest membership, `content_sha256`, and current source selection tied to one canonical identity per file.

## Next-slice update: sorted release manifest entries

Release-candidate manifests now use canonical sorted path order as part of the
release-evidence contract. `strategy-validator-release-candidate generate` emits
entries sorted lexicographically by canonical repo-relative POSIX path, and
`verify-bundle` treats unsorted manifest entries as a structured manifest error.
This keeps human review, manifest diffs, and `content_sha256` evidence stable
rather than allowing semantically equivalent but reordered release packets.

`scripts/repository_truth_check.py` now reports `repository_truth_check/v18` and
includes `release_candidate_bundle_manifest_entries_are_sorted` so sorted release
manifest evidence remains covered by the dependency-light repository truth gate.

## Next-slices update: readonly diagnostics and app-factory contract

Ledger and operator-action diagnostics now use readonly inspection paths for
verification/indexing instead of bootstrapping the storage they inspect.
`strategy_validator/ledger/operator_actions.py` exposes readonly event readers
and chain verification helpers; `strategy_validator/cli/ledger_ops.py` uses
readonly ledger hash-chain verification and readonly operator journal checks for
`verify`, `verify-operator-actions`, and `index-operator-actions`.

The API now exposes a real `create_app()` factory in `strategy_validator/api/app.py`,
and `scripts/openapi_contract_snapshot.py` imports that factory directly. This
keeps OpenAPI snapshot generation tied to the same route/security wiring as the
module-level ASGI app. `scripts/repository_truth_check.py` now reports
`repository_truth_check/v21` and verifies the app-factory/OpenAPI and readonly
ledger diagnostics contracts.

## Next-slices update: provider env override hardening

Provider URL policy validation now also covers environment overrides assigned
after Pydantic model construction. `strategy_validator/core/config.py` validates
operator-supplied provider base URLs and URL templates before assignment and
records invalid values in `runtime_policy.invalid_environment_overrides` while
retaining the previous safe value. This closes the bypass where direct env
assignment could avoid the field validators defined on provider connector models.

## Next-slices update: request body and operator-principal hardening

The API security envelope now enforces the configured body-size cap against actual streamed request bodies for write methods, not only declared `Content-Length` headers. Mutation auth also validates operator principal headers so malformed or unsafe principal identifiers fail closed before they can enter receipts or operator-action lineage.

## Next-slices update: OpenAPI gate and projection lineage

The API now exposes a `create_app()` factory while preserving the module-level ASGI `app`. OpenAPI snapshot generation is wired to the factory and the main CI validation job. Operator-action projection entries now carry authorization principal lineage so UI/read-plane consumers can explain who initiated a command without inspecting raw journal payloads.

## Next-set hardening update

The continuation pass adds three additional enforcement seams:

- **Scoped mutation authority:** `strategy_validator/api/auth.py` now records role and scopes on `UiMutationAuthContext`; `strategy_validator/application/ui_command_policy.py` requires `operator:command:write` for UI operator mutations.
- **Transport diagnostics:** `strategy_validator/api/security.py` emits/propagates `x-request-id` and supports optional in-process mutation rate limiting via `STRATEGY_VALIDATOR_API_MUTATION_RATE_LIMIT_PER_MINUTE`.
- **Operator event read plane:** `strategy_validator/application/operator_action_projection.py` exposes operator-action projection reads through the application layer, and `strategy_validator/api/routes/ui_routes_detail_runtime.py` publishes `/ui/operator-actions` without direct API-to-projection coupling.

These are still single-tenant safeguards. They do not make the system multi-tenant or internet-exposed SaaS-ready.
