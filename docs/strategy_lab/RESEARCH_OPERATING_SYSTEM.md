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

## Canonical local demo (no network, no keys)

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

## Inspecting artifacts

- **Demo manifest:** `artifacts/research_os_demo/latest/demo_manifest.json`
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
