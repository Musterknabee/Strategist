# Provider-backed paper research loop smoke

**Date (UTC):** 2026-05-05  
**Branch tested:** `smoke/provider-backed-paper-research-loop`  
**Baseline commit:** `940e1a28953c04127b5c13745161816c3adcea66`  

## Scope

Run the smallest safe provider-backed paper-research smoke on local single-tenant setup:

- provider capabilities and public provider sampling,
- provider health + evidence manifest generation,
- fixture-first provider paper loop (paper-only),
- backend `/ui/*` visibility checks,
- frontend dev connectivity check.

No live broker orders were submitted. No live trading authority was enabled.

## Provider key posture

- Optional provider keys were **not required** for backend boot.
- Public/no-key providers were used for network sampling (`--public-only`).
- Broker/live credentials were not committed and not printed.
- Paper broker status remained `PENDING_KEY`.

## Commands run

```powershell
# capabilities
strategy-validator-provider-capabilities --json > artifacts/provider_smoke/provider_capabilities.json

# public provider samples + manifest
python scripts/retrieve_provider_samples.py --public-only --manifest-json --output-dir artifacts/provider_smoke/samples --max-samples 5

# normalized observations
python scripts/normalize_provider_samples.py --manifest artifacts/provider_smoke/samples/manifest.json --output artifacts/provider_smoke/normalized_observations.json --json

# provider evidence manifest
python scripts/build_provider_evidence_manifest.py --samples artifacts/provider_smoke/samples/manifest.json --normalized artifacts/provider_smoke/normalized_observations.json --output artifacts/provider_smoke/provider_evidence_manifest.json --env-file deployment.env --json

# provider health snapshot artifact
python scripts/provider_health_check.py --env-file deployment.env --manifest artifacts/provider_smoke/samples/manifest.json --json > artifacts/provider_smoke/provider_health_snapshot.json

# paper-only provider loop (fixture-first, no network for broker)
strategy-validator-provider-paper-loop --artifact-root C:\var\lib\strategy-validator\artifacts --run-id provider-smoke-live-ui-20260505 --env-file deployment.env --overwrite --json
```

## Providers sampled (public/no-key path)

- `sec_edgar`
- `world_bank_open_data`
- `ecb`
- `eurostat`
- `oecd`

All sampled as `classified_status=OK` in this run.

## Artifacts generated

- `artifacts/provider_smoke/provider_capabilities.json`
- `artifacts/provider_smoke/samples/manifest.json`
- `artifacts/provider_smoke/normalized_observations.json`
- `artifacts/provider_smoke/provider_evidence_manifest.json`
- `artifacts/provider_smoke/provider_health_snapshot.json`
- `C:\var\lib\strategy-validator\artifacts/provider_paper_loop/latest/provider_paper_loop_manifest.json`

SHA256 (this run):

- `samples/manifest.json` = `4d1bcbaa6c8d4421f4e1b9496814b61365d69b6da63799d0864371a8b0c60dfa`
- `normalized_observations.json` = `a6fb8827381c93e5a033b183b086ed3cee7f9908b6b47faa4aee39db8de50f79`
- `provider_evidence_manifest.json` = `aee0e0f408be9367533309be0c909ed558062609e9f28eff3a5103b65beef99a`
- `provider_health_snapshot.json` = `3158d4df2963dab7bd65d8ae408f780dfc12dfc1739fc088d21f429579959351`
- `provider_paper_loop_manifest.json` = `d778f688d5305068e8354e65c3304d57c412b28433ca55793d15c19bc06d7c6e`

## Backend route checks (`127.0.0.1:8000`)

- `/healthz`: healthy
- `/readyz`: `READY`, token-protected mutations, no readiness blockers
- `/ui/runtime`: production runtime, mutation safety intact
- `/ui/provider-setup`: provider setup payload available; action-required entries surfaced for missing optional keyed providers
- `/ui/provider-health`: sample manifest detected (`sample_manifest_present=true`), digest prefix present, classified OK count reflects sampled providers
- `/ui/evidence` and `/ui/evidence-chain`: no fake approval/signoff
- `/ui/strategy-batches/latest`: latest run points to provider-smoke run id
- `/ui/paper-tracking/latest`: latest tracking object present with paper-tracking lifecycle data
- `/ui/paper-execution`: read-plane payload present; no live authority implied

## Frontend cockpit check (`127.0.0.1:3000`)

- `NEXT_PUBLIC_STRATEGIST_API_BASE_URL=http://127.0.0.1:8000`
- `NEXT_PUBLIC_STRATEGIST_DEMO_MODE=false`
- Dev server reachable (HTTP 200).
- Demo banner not present in homepage response when demo mode disabled.
- Existing safety constraints remain:
  - no browser shell execution path,
  - no token persistence in `localStorage`/`sessionStorage`,
  - no frontend-only deployment/signoff claims.

## Gap fixed in this slice

- `provider_samples_manifest/v1` lacked top-level `generated_at_utc`.
- Added timestamp emission in `scripts/retrieve_provider_samples.py`.
- Added regression test:
  - `tests/api/test_retrieve_provider_samples_manifest_metadata.py`

## Blockers / warnings

- Backtest forensic latest route remained empty for this minimal smoke; this run intentionally exercised provider sample + paper tracking path with fixture-first provider snapshot loop.
- This is an integration smoke; it is not a deployment acceptance packet.

## Safety disclaimer

- This smoke is **paper/research-only evidence**.
- It is **not** production deployment approval.
- It is **not** operator signoff.
- It does **not** grant live trading authority.
