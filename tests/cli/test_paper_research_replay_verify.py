from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.paper_research_replay import build_replay_manifest, config_fingerprint_from_env
from strategy_validator.cli.paper_research_replay_verify import main


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_replay_verify_cli_passes_when_digests_match(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    repo_root = tmp_path
    inp = _write(tmp_path / "inputs" / "source.json", '{"k":"v"}')
    out = _write(tmp_path / "outputs" / "result.json", '{"done":true}')
    replay = build_replay_manifest(
        repo_root=repo_root,
        artifact_id="cli-ok",
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
        input_paths=(("input", inp),),
        output_paths=(("output", out),),
    )
    replay_path = tmp_path / "replay_manifest.json"
    replay_path.write_text(json.dumps(replay.model_dump(mode="json"), indent=2), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert main(["--replay-manifest", str(replay_path), "--json"]) == 0


def test_replay_verify_cli_fails_on_missing_artifact(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    repo_root = tmp_path
    inp = _write(tmp_path / "inputs" / "source.json", '{"k":"v"}')
    out = _write(tmp_path / "outputs" / "result.json", '{"done":true}')
    replay = build_replay_manifest(
        repo_root=repo_root,
        artifact_id="cli-missing",
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
        input_paths=(("input", inp),),
        output_paths=(("output", out),),
    )
    replay_path = tmp_path / "replay_manifest.json"
    replay_path.write_text(json.dumps(replay.model_dump(mode="json"), indent=2), encoding="utf-8")
    out.unlink()
    monkeypatch.chdir(tmp_path)
    assert main(["--replay-manifest", str(replay_path)]) == 1
