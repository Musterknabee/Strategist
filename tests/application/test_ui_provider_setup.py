from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from strategy_validator.application.ui_provider_setup import build_ui_provider_setup_payload


def test_provider_setup_payload_is_secret_safe_and_actionable(tmp_path, monkeypatch) -> None:
    manifest = tmp_path / "provider_samples.json"
    manifest.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "provider_id": "bls",
                        "classified_status": "OK",
                        "http_status": 200,
                        "retrieved_at_utc": "2026-05-02T10:00:00+00:00",
                        "sha256": "a" * 64,
                    },
                    {
                        "provider_id": "tiingo",
                        "classified_status": "PENDING_KEY",
                        "retrieved_at_utc": "2026-05-02T10:00:00+00:00",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("STRATEGY_VALIDATOR_PROVIDER_SAMPLES_MANIFEST", str(manifest))
    monkeypatch.setenv("TIINGO_API_KEY", "CHANGEME")
    payload = build_ui_provider_setup_payload(
        repo_root=tmp_path,
        env={
            "STRATEGY_VALIDATOR_PROVIDER_SAMPLES_MANIFEST": str(manifest),
            "TIINGO_API_KEY": "CHANGEME",
            "STRATEGY_VALIDATOR_PROVIDER_FRESHNESS_MAX_AGE_SECONDS": "86400",
        },
        generated_at_utc=datetime(2026, 5, 2, 10, 30, tzinfo=timezone.utc),
    )

    assert payload["schema_version"] == "ui_provider_setup_console/v1"
    assert payload["read_plane_only"] is True
    assert payload["no_network_calls"] is True
    assert payload["no_secret_values"] is True
    assert "CHANGEME" not in json.dumps(payload)
    assert payload["summary"]["provider_count"] >= 2

    by_id = {row["provider_id"]: row for row in payload["entries"]}
    assert by_id["bls"]["freshness_class"] == "FRESH"
    assert by_id["bls"]["readiness_tier"] == "READY"
    assert by_id["tiingo"]["setup_status"] == "MISSING_OPTIONAL_SECRET"
    assert "TIINGO_API_KEY" in by_id["tiingo"]["expected_env_vars"]


def test_provider_setup_marks_stale_samples(tmp_path) -> None:
    manifest = tmp_path / "provider_samples.json"
    old = datetime(2026, 5, 1, tzinfo=timezone.utc)
    manifest.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "provider_id": "bls",
                        "classified_status": "OK",
                        "http_status": 200,
                        "retrieved_at_utc": old.isoformat(),
                        "sha256": "b" * 64,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    payload = build_ui_provider_setup_payload(
        repo_root=tmp_path,
        env={
            "STRATEGY_VALIDATOR_PROVIDER_SAMPLES_MANIFEST": str(manifest),
            "STRATEGY_VALIDATOR_PROVIDER_FRESHNESS_MAX_AGE_SECONDS": "60",
        },
        generated_at_utc=old + timedelta(hours=2),
    )

    bls = next(row for row in payload["entries"] if row["provider_id"] == "bls")
    assert bls["freshness_class"] == "STALE"
    assert bls["readiness_tier"] == "STALE"
    assert bls["freshness_age_seconds"] >= 7200
