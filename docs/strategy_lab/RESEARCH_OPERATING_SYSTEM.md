# Research operating system (read-plane)

This document is the **single high-level operator map** for research, paper tracking, lifecycle, promotion evidence, and portfolio simulation in this repository. For subsystem specifics, follow the links at the end—do not duplicate conflicting runbooks.

## What this is

An **evidence-first research workflow**: batch gauntlet runs, paper tracking, lifecycle assessment, human-review promotion packets, optional paper-broker configuration, daily paper manifests, robustness hints (CPCV), and portfolio allocation **simulation**. Everything is **paper / research posture** unless explicitly stated otherwise.

## What this is not

- **Not live trading** and **not a profitability guarantee**.
- **Not** automatic promotion to production strategies.
- **Not** a substitute for deployment approval or single-tenant API semantics (those remain unchanged).
- The Strategist Terminal frontend is **read-plane only** for these surfaces: it does not submit broker orders or mutate the ledger.

## End-to-end lifecycle (conceptual)

1. **Gauntlet / batch** — Run a multi-strategy batch (see [MULTI_STRATEGY_BATCH_RUNNER.md](./MULTI_STRATEGY_BATCH_RUNNER.md)); artifacts land under the strategy batch output root (often `artifacts/strategy_runs` or a demo root).
2. **Paper tracking** — Enroll candidates, append snapshots, evaluate scorecards (see [PAPER_TRACKING.md](./PAPER_TRACKING.md)).
3. **Lifecycle** — Derived state and blockers; synthetic paths stay non-promotable (see [CANDIDATE_LIFECYCLE.md](./CANDIDATE_LIFECYCLE.md)).
4. **Promotion review packet** — Evidence-only JSON for human review; never approves live (see [PROMOTION_REVIEW_PACKET.md](./PROMOTION_REVIEW_PACKET.md)).
5. **Paper broker / daily tracking** — Broker integration is **paper-only** and **key-optional** at API boot; daily runs write manifests (see [PAPER_BROKER_ALPACA.md](./PAPER_BROKER_ALPACA.md), [DAILY_PAPER_TRACKING.md](./DAILY_PAPER_TRACKING.md)).
6. **CPCV / robustness** — Per-strategy hints on the latest batch summary when present (see [CPCV_ROBUSTNESS.md](./CPCV_ROBUSTNESS.md)).
7. **Portfolio allocation** — Offline simulator from batch summary + run directory; **no orders** (see [PORTFOLIO_ALLOCATION.md](./PORTFOLIO_ALLOCATION.md)).
8. **Compute / GPU** — Optional acceleration; API and tests must not require GPU (see [COMPUTE_ACCELERATION.md](./COMPUTE_ACCELERATION.md)).

## Provider-backed paper loop

For the **fixture-first** provider snapshot → gauntlet → paper tracking → broker policy path, see [PROVIDER_BACKED_PAPER_LOOP.md](./PROVIDER_BACKED_PAPER_LOOP.md). Key manifest: `provider_paper_loop/latest/provider_paper_loop_manifest.json`.

## Canonical runtime evidence (Docker API + same artifact root)

The API reads **`STRATEGY_VALIDATOR_ARTIFACT_ROOT`** (default in sample deploy: `/var/lib/strategy-validator/artifacts`). Strategy batch output, paper tracking, and `strategy_data` default under that root unless you set explicit overrides.

**Inside the running API container** (paths align with the process):

```powershell
docker exec strategist-local-api strategy-validator-research-os-runtime-demo `
  --artifact-root /var/lib/strategy-validator/artifacts `
  --run-id runtime-demo `
  --allow-synthetic-demo `
  --skip-benchmark `
  --overwrite `
  --json
```

Or use `scripts/run_research_os_runtime_demo_in_container.ps1` from the repo.

- Writes `research_os_runtime/latest/runtime_demo_manifest.json` under the artifact root (`research_os_runtime_demo_manifest/v1`).
- `ok=true` means the pipeline machinery completed; individual gates may still be **BLOCKED**, **PENDING_KEY**, or **DO_NOT_PROMOTE** — those are honest outcomes, not API failures.

## Legacy packaged demo (no network, no keys)

From the repository root:

```bash
python scripts/run_research_os_demo.py \
  --output-root artifacts/research_os_demo \
  --run-id research-os-demo \
  --overwrite \
  --skip-benchmark \
  --json
```

- Writes `artifacts/research_os_demo/latest/demo_manifest.json` and isolates demo paper/batch roots via environment for the run.
- Optional steps (`--skip-portfolio`, benchmark) can be skipped; missing GPU or provider keys should **degrade** with warnings, not crash the core path.

**Host-only runtime demo** (must use the same directory the API container mounts as `STRATEGY_VALIDATOR_ARTIFACT_ROOT`):

```powershell
python scripts/run_research_os_runtime_demo.py `
  --artifact-root <host-path-matching-docker-volume> `
  --run-id runtime-demo `
  --overwrite `
  --json
```

## Inspecting artifacts

- **Runtime demo manifest:** `<artifact_root>/research_os_runtime/latest/runtime_demo_manifest.json`
- **Legacy demo manifest:** `artifacts/research_os_demo/latest/demo_manifest.json`
- **Batch summaries:** `**/batch_summary.json` under the strategy batch output root
- **Paper tracking:** per-tracking directories under `STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT`
- **Daily runs:** `daily_runs/<date>/daily_run_manifest.json`
- **Provider snapshots:** `artifacts/strategy_data/*_manifest.json` when ingestion has been run

## Cockpit (read-plane API + frontend)

- **API:** `GET /ui/research-os/status` — consolidated payload `ui_research_os_status/v1`; missing artifacts yield **degraded** hints, not HTTP 500.
- **Facade:** route is listed on `GET /ui/facade`.
- **Frontend:** Strategist Terminal → **Research OS** (`/research-os`) shows the same payload (inspect / raw JSON drawer).

## Optional providers, broker, GPU

- **Providers:** Historical ingestion may require keys for real pulls; without keys, statuses should remain **PENDING** / **UNAVAILABLE**, not block API startup.
- **Paper broker:** Paper endpoints and env-gated policy; live trading is out of scope.
- **GPU:** Torch and devices are optional; probes and benchmarks should tolerate CPU-only environments.

## Safety boundaries (non-negotiable)

- Research and paper tooling **must not** import the ledger writer directly (see constitutional tests).
- Normal **pytest** must not call the live network.
- No secrets in public frontend config (`NEXT_PUBLIC_*` must not carry tokens).
- **Single-tenant deployment approval** semantics are not weakened by this document or the research OS surfaces.

## Known limitations

- Consolidated UI status is **hinting**: it scans latest artifacts on disk relative to the API process; in API-only containers without mounted artifact volumes, fields may show **degraded** even when a workstation has files locally.
- Promotion packets are **evidence for humans**; readiness flags are gates for review, not execution.
- Portfolio allocation and CPCV outputs depend on batch configuration and gates; **BLOCKED** or **DO_NOT_PROMOTE** outcomes are normal and informative.

## Next graduation steps (real world)

1. Wire durable artifact storage visible to the deployment that serves `/ui/research-os/status`.
2. Run the demo script in CI or a controlled agent with pinned fixtures.
3. Keep provider and broker keys out of the runtime image; inject at orchestration layer only where required.
4. Expand human review workflow outside the repo (ticketing, sign-off) — not in the read-plane UI.

## Related docs

- [PROVIDER_BACKED_PAPER_LOOP.md](./PROVIDER_BACKED_PAPER_LOOP.md)
- [MULTI_STRATEGY_BATCH_RUNNER.md](./MULTI_STRATEGY_BATCH_RUNNER.md)
- [PAPER_TRACKING.md](./PAPER_TRACKING.md)
- [CANDIDATE_LIFECYCLE.md](./CANDIDATE_LIFECYCLE.md)
- [PROMOTION_REVIEW_PACKET.md](./PROMOTION_REVIEW_PACKET.md)
- [PROVIDER_HISTORICAL_DATA.md](./PROVIDER_HISTORICAL_DATA.md)
- [PAPER_BROKER_ALPACA.md](./PAPER_BROKER_ALPACA.md)
- [DAILY_PAPER_TRACKING.md](./DAILY_PAPER_TRACKING.md)
- [COMPUTE_ACCELERATION.md](./COMPUTE_ACCELERATION.md)
- [CPCV_ROBUSTNESS.md](./CPCV_ROBUSTNESS.md)
- [PORTFOLIO_ALLOCATION.md](./PORTFOLIO_ALLOCATION.md)

## Related research-memory layers

- [Strategy Memory and Candidate Graveyard](STRATEGY_MEMORY_AND_GRAVEYARD.md)

## Related research-memory layers

- [Strategy Thesis and Falsification Manifest](STRATEGY_THESIS_AND_FALSIFICATION.md)


## Added paper-governance layers

- [Shadow Book](SHADOW_BOOK.md): paper-only portfolio simulator with simulated fills, risk flags, drawdown, and read-plane cockpit visibility. No broker orders.
- [Market Data Integrity](MARKET_DATA_INTEGRITY.md): deterministic checks for stale bars, missing trading days, split-like jumps, survivorship warnings, and adjustment-status caveats.


## Research OS Closure

The closure manifest digest-links the latest Research OS evidence artifacts and exposes a read-plane cockpit page. See [RESEARCH_OS_CLOSURE.md](RESEARCH_OS_CLOSURE.md).

- [Research OS Attestation](RESEARCH_OS_ATTESTATION.md)


## Research OS Briefing

The Research OS briefing pack summarizes closure, attestation, provider-paper-loop, paper broker, strategy memory, thesis, shadow-book, and runtime evidence into one read-plane operator report. See [Research OS Briefing](RESEARCH_OS_BRIEFING.md).


## Research OS Export Bundle

Portable offline evidence handoff is documented in [RESEARCH_OS_EXPORT.md](RESEARCH_OS_EXPORT.md). It packages closure, attestation, briefing, and paper-research artifacts into a digest-linked bundle without granting live trading authority.

- [Research OS Operator Run](RESEARCH_OS_OPERATOR_RUN.md) — sequences closure, verification, attestation, briefing, and export into one daily run manifest.

- [Research OS Evidence Catalog](RESEARCH_OS_EVIDENCE_CATALOG.md) — read-plane artifact inventory with SHA-256 digests and category/status hints.


## Evidence drift

The Research OS evidence drift report compares evidence catalogs and shows added, removed, changed, and unchanged artifacts without executing research or granting trading authority. See [Research OS Evidence Drift](RESEARCH_OS_EVIDENCE_DRIFT.md).


## Research OS Policy Gate

The policy gate turns closure, attestation, briefing, export, operator-run, catalog, and drift evidence into a PASS/WARN/BLOCK operator-review posture. See `docs/strategy_lab/RESEARCH_OS_POLICY_GATE.md`.

- [Research OS Governed Exceptions](RESEARCH_OS_EXCEPTION.md) — time-bounded constrained annotations for WARN-level evidence.


## Research OS Remediation

See [RESEARCH_OS_REMEDIATION.md](RESEARCH_OS_REMEDIATION.md) for the read-plane action queue that turns policy-gate, exception, catalog, and drift evidence into prioritized remediation work.


## Release-readiness review

See [RESEARCH_OS_RELEASE_READINESS.md](RESEARCH_OS_RELEASE_READINESS.md) for the read-plane single-tenant release review posture. This is not deployment approval and does not enable live trading or broker orders.


## Research OS handoff

The single-tenant handoff pack summarizes release-readiness, policy-gate, exception, remediation, export, catalog, and operator-run evidence into one final operator handoff artifact. See [RESEARCH_OS_HANDOFF.md](RESEARCH_OS_HANDOFF.md). It is not deployment approval and does not authorize live trading or broker orders.

- [Research OS Handoff Verification and Reviewer Signoff](RESEARCH_OS_HANDOFF_SIGNOFF.md)


## Review Journal

The review journal summarizes Research OS review decisions and source artifact digests without mutating the canonical validator ledger. See [RESEARCH_OS_REVIEW_JOURNAL.md](RESEARCH_OS_REVIEW_JOURNAL.md).
