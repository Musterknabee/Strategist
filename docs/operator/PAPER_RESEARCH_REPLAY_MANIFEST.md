# Paper research replay manifest

`paper_research_replay_manifest/v1` is the offline integrity contract for provider-backed paper research artifacts.

## Purpose

The replay manifest answers:

- what inputs produced the artifact,
- what outputs were emitted,
- what command generated the run (redacted),
- what code/config fingerprint was used,
- whether the run is paper-only and live-blocked,
- whether all artifacts can be replay-verified offline by digest.

Replay verification checks artifact integrity only. It does not claim strategy quality, profitability, production readiness, deployment approval, or operator signoff.

## Schema highlights

- `schema_version`
- `artifact_id`, `artifact_kind`, `generated_at_utc`
- `command`, `command_args_redacted`
- `git_commit`, `code_fingerprint`, `config_fingerprint`
- `provider_id`, `provider_name`, `provider_mode`
- `provider_key_required`, `provider_key_present` (never raw keys)
- `trust_banner`, `license_usage_caveat`, `source_label`
- `input_artifacts[]` (`kind`, `path`, `sha256`)
- `output_artifacts[]` (`kind`, `path`, `sha256`)
- `replayable_offline=true`, `paper_only=true`, `live_trading_blocked=true`
- `warnings[]`, `blockers[]`

## Verification command

```powershell
strategy-validator-paper-research-replay-verify --replay-manifest artifacts/provider_paper_loop/latest/replay_manifest.json --json
```

Expected behavior:

- no provider network calls,
- no provider key requirement,
- no ledger mutation,
- returns non-zero on missing files or digest mismatch.

## What replay verifies

- presence of declared input/output artifacts,
- byte-level SHA256 digest match against manifest entries.

## What replay does not verify

- alpha validity or profitability,
- data licensing legal sufficiency beyond recorded caveats,
- production readiness or deployment approval,
- live-trading safety authorization.
