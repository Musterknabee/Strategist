from __future__ import annotations

import json
import socket
from pathlib import Path

from strategy_validator.application.paper_research_replay import (
    build_replay_manifest,
    config_fingerprint_from_env,
    verify_replay_manifest,
)


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_replay_manifest_verify_ok(tmp_path: Path) -> None:
    repo_root = tmp_path
    inp = _write(tmp_path / "inputs" / "sample.json", '{"ok":true}')
    out = _write(tmp_path / "outputs" / "summary.json", '{"done":true}')
    manifest = build_replay_manifest(
        repo_root=repo_root,
        artifact_id="unit-replay-ok",
        command="strategy-validator-provider-paper-loop",
        command_args_redacted=("--artifact-root", "artifacts/test"),
        provider_id="demo_provider",
        provider_name="Demo Provider",
        provider_mode="OFFLINE_REPLAY",
        provider_key_required=False,
        provider_key_present=False,
        trust_banner="SYNTHETIC_FIXTURE_RESEARCH_ONLY",
        license_usage_caveat="fixture_research_only",
        source_label="tests/fixtures/provider_snapshots",
        config_fingerprint=config_fingerprint_from_env({}),
        input_paths=(("provider_samples_manifest", inp),),
        output_paths=(("batch_summary", out),),
    )
    replay_path = _write(tmp_path / "artifacts" / "provider_paper_loop" / "latest" / "replay_manifest.json", manifest.model_dump_json())
    result = verify_replay_manifest(replay_path, repo_root=repo_root)
    assert result.ok is True
    assert result.missing_artifact_count == 0
    assert result.digest_mismatch_count == 0


def test_replay_manifest_verify_missing_file(tmp_path: Path) -> None:
    repo_root = tmp_path
    inp = _write(tmp_path / "inputs" / "sample.json", '{"ok":true}')
    out = _write(tmp_path / "outputs" / "summary.json", '{"done":true}')
    manifest = build_replay_manifest(
        repo_root=repo_root,
        artifact_id="unit-replay-missing",
        command="strategy-validator-provider-paper-loop",
        command_args_redacted=(),
        provider_id="demo_provider",
        provider_name="Demo Provider",
        provider_mode="OFFLINE_REPLAY",
        provider_key_required=False,
        provider_key_present=False,
        trust_banner="SYNTHETIC_FIXTURE_RESEARCH_ONLY",
        license_usage_caveat="fixture_research_only",
        source_label="tests/fixtures/provider_snapshots",
        config_fingerprint=config_fingerprint_from_env({}),
        input_paths=(("provider_samples_manifest", inp),),
        output_paths=(("batch_summary", out),),
    )
    replay_path = tmp_path / "replay_manifest.json"
    replay_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2), encoding="utf-8")
    out.unlink()
    result = verify_replay_manifest(replay_path, repo_root=repo_root)
    assert result.ok is False
    assert result.missing_artifact_count == 1
    assert result.digest_mismatch_count == 0


def test_replay_manifest_verify_digest_mismatch_and_no_network(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    repo_root = tmp_path
    inp = _write(tmp_path / "inputs" / "sample.json", '{"ok":true}')
    out = _write(tmp_path / "outputs" / "summary.json", '{"done":true}')
    manifest = build_replay_manifest(
        repo_root=repo_root,
        artifact_id="unit-replay-mismatch",
        command="strategy-validator-provider-paper-loop",
        command_args_redacted=(),
        provider_id="demo_provider",
        provider_name="Demo Provider",
        provider_mode="OFFLINE_REPLAY",
        provider_key_required=False,
        provider_key_present=False,
        trust_banner="SYNTHETIC_FIXTURE_RESEARCH_ONLY",
        license_usage_caveat="fixture_research_only",
        source_label="tests/fixtures/provider_snapshots",
        config_fingerprint=config_fingerprint_from_env({}),
        input_paths=(("provider_samples_manifest", inp),),
        output_paths=(("batch_summary", out),),
    )
    replay_path = tmp_path / "replay_manifest.json"
    replay_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2), encoding="utf-8")
    out.write_text('{"done":false}', encoding="utf-8")

    def _fail_network(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("verify_replay_manifest must not use network")

    monkeypatch.setattr(socket, "create_connection", _fail_network)
    result = verify_replay_manifest(replay_path, repo_root=repo_root)
    assert result.ok is False
    assert result.digest_mismatch_count == 1
