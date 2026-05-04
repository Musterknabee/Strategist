# Research data spine — operator runbook

This spine connects optional provider samples to PIT-aware evidence and Oracle advisory context. Backend startup does **not** require provider keys.

## Flow

1. **Samples** — `python scripts/retrieve_provider_samples.py` (`--public-only` and/or `--configured-keyed-only --env-file deployment.env`). Writes a manifest under `artifacts/provider_samples/` (gitignored by default).
2. **Health** — `python scripts/provider_health_check.py --env-file deployment.env --json` (optional manifest via `STRATEGY_VALIDATOR_PROVIDER_SAMPLES_MANIFEST` or `--manifest`).
3. **Normalize** — `python scripts/normalize_provider_samples.py --manifest artifacts/provider_samples/manifest.json -o artifacts/provider_samples/normalized.json --json`.
4. **Evidence manifest** — `python scripts/build_provider_evidence_manifest.py --samples artifacts/provider_samples/manifest.json --normalized artifacts/provider_samples/normalized.json --output artifacts/provider_samples/evidence_manifest.json --env-file deployment.env --json`.
5. **Oracle advisory** — `strategy_validator.oracle.provider_ingestion` reads the evidence manifest and produces **advisory-only** summaries (no ledger mutation, no promotion authority).

## API / UI read-plane

- `GET /readiness/health` — runtime readiness; includes compact `provider_research_spine` summary.
- `GET /readiness/provider-health` — full provider health snapshot (JSON).
- `GET /ui/provider-health` — same snapshot for operator UI surfaces.
- `GET /ui/facade` — lists `/ui/provider-health`.

## Rules

- Never commit API keys or echo raw secrets in logs or manifests.
- Freemium providers default to research-only; they do not silently become live promotion authority.
- Alpaca: paper by default; live execution requires explicit personal approval env (see deployment env samples).
