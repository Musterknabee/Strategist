from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone
from pathlib import Path

from strategy_validator.cli.oracle_temporal_runners import cmd_extract_temporal_semantic_batch
from strategy_validator.contracts.oracle_temporal import TemporalSemanticExtractionBatchRequest, TemporalSourceRecord
from strategy_validator.core.config import AppConfig, NvidiaNimConnectorSettings
from strategy_validator.validator.oracle_temporal_extraction import extract_temporal_semantic_batch
from strategy_validator.validator.providers.factory import build_nvidia_nim_semantic_provider


def _request() -> TemporalSemanticExtractionBatchRequest:
    return TemporalSemanticExtractionBatchRequest(
        provider_kind="NVIDIA_NIM",
        provider_id="nim-test",
        model_name="minimaxai/minimax-m2.7",
        batch_start_date=date(2026, 1, 5),
        batch_end_date=date(2026, 1, 6),
        days=[
            {
                "point_in_time_date": "2026-01-05",
                "trading_session_id": "XNYS-2026-01-05",
                "allowed_prefix_digest_sha256": "abc123",
                "source_records": [
                    {
                        "source_id": "news-1",
                        "source_timestamp_utc": "2026-01-05T12:00:00Z",
                        "source_kind": "NEWS",
                        "text": "Fed commentary balanced, two hawkish notes, one dovish note.",
                    }
                ],
            },
            {
                "point_in_time_date": "2026-01-06",
                "trading_session_id": "XNYS-2026-01-06",
                "allowed_prefix_digest_sha256": "def456",
                "source_records": [
                    {
                        "source_id": "news-2",
                        "source_timestamp_utc": "2026-01-06T14:00:00Z",
                        "source_kind": "NEWS",
                        "text": "Geopolitical tensions rose and narrative contradiction count increased.",
                    }
                ],
            },
        ],
    )


def test_extract_temporal_semantic_batch_writes_artifacts_and_manifests(tmp_path: Path) -> None:
    cfg = AppConfig(semantic_nvidia_nim_connector=NvidiaNimConnectorSettings(enabled=True, provider_id="nim-test"))
    provider = build_nvidia_nim_semantic_provider(cfg)
    assert provider is not None

    def _fake_complete(*, system_prompt, user_prompt, temperature=0.0, response_model=None):
        payload = json.loads(user_prompt)
        source = payload["current_day"]["source_records"][0]
        response = {
            "semantic_raw": {
                "hawkish_document_ratio": 0.4,
                "dovish_document_ratio": 0.2,
                "geopolitical_headline_share": 0.3,
                "contradiction_count": 1,
                "belief_conflict_score": 0.25,
            },
            "citations": [{
                "source_id": source["source_id"],
                "source_timestamp_utc": source["source_timestamp_utc"],
                "source_kind": source["source_kind"],
                "exact_quote": source["text"],
            }],
            "advisory_notes": ["provider synthesized semantic ratios from supplied day-only records"],
        }
        raw = {"id": f"req-{payload['current_day']['point_in_time_date']}", "choices": [{"message": {"content": json.dumps(response)}}]}
        return provider._parse_completion_payload(raw, response_model=response_model)[0], {"raw_response": raw, "response_text": json.dumps(response), "vendor_request_id": raw["id"], "request_body": {"model": provider.model}}

    provider.complete_structured_json_with_metadata = _fake_complete  # type: ignore[assignment]
    manifest, artifact = extract_temporal_semantic_batch(_request(), provider=provider, artifact_root=tmp_path / "artifacts")

    assert len(manifest.days) == 2
    assert artifact.provider_id == "nim-test"
    assert (tmp_path / "artifacts" / "TEMPORAL_SEMANTIC_BATCH_MANIFEST.json").exists()
    assert (tmp_path / "artifacts" / "2026-01-05" / "NVIDIA_NIM_TEMPORAL_RESPONSE.json").exists()


def test_cli_extract_temporal_semantic_batch_emits_payload(tmp_path: Path, monkeypatch) -> None:
    request = _request()
    input_path = tmp_path / "request.json"
    input_path.write_text(json.dumps(request.model_dump(mode="json"), indent=2), encoding="utf-8")

    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text("""semantic_nvidia_nim_connector:
  enabled: true
  provider_id: nim-test
""", encoding="utf-8")

    from strategy_validator.validator.providers.nvidia_nim_semantic_provider import NvidiaNimTemporalSemanticProvider

    def _fake_complete(self, *, system_prompt, user_prompt, temperature=0.0, response_model=None):
        payload = json.loads(user_prompt)
        source = payload["current_day"]["source_records"][0]
        response = {
            "semantic_raw": {
                "hawkish_document_ratio": 0.5,
                "dovish_document_ratio": 0.1,
                "geopolitical_headline_share": 0.2,
                "contradiction_count": 0,
                "belief_conflict_score": 0.1,
            },
            "citations": [{
                "source_id": source["source_id"],
                "source_timestamp_utc": source["source_timestamp_utc"],
                "source_kind": source["source_kind"],
                "exact_quote": source["text"],
            }],
            "advisory_notes": [],
        }
        raw = {"id": "req-cli", "choices": [{"message": {"content": json.dumps(response)}}]}
        return self._parse_completion_payload(raw, response_model=response_model)[0], {"raw_response": raw, "response_text": json.dumps(response), "vendor_request_id": raw["id"], "request_body": {"model": self.model}}

    monkeypatch.setattr(NvidiaNimTemporalSemanticProvider, "complete_structured_json_with_metadata", _fake_complete, raising=True)

    out = tmp_path / "out.json"
    ns = type("NS", (), {
        "input": str(input_path),
        "config": str(cfg_path),
        "artifact_root": str(tmp_path / "artifacts"),
        "temperature": 0.0,
        "output": str(out),
    })
    assert cmd_extract_temporal_semantic_batch(ns) == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["temporal_semantic_batch"]["provider_id"] == "nim-test"
    assert payload["provider_artifact"]["provider_id"] == "nim-test"
