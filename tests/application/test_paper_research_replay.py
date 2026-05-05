from __future__ import annotations

import json
import socket
from pathlib import Path
import pytest

from strategy_validator.application.paper_research_replay import (
    build_replay_manifest,
    config_fingerprint_from_env,
    latest_replay_verification_summary,
    redact_command_args,
    verify_replay_manifest,
)
from strategy_validator.contracts.artifact_replay import PaperResearchReplayManifest, ReplayArtifactEntry


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
    assert any(item.startswith("MISSING_ARTIFACT:") for item in result.blockers)


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


def test_replay_manifest_verify_path_traversal_fails(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text('{"x":1}', encoding="utf-8")
    manifest = PaperResearchReplayManifest(
        artifact_id="unsafe-traversal",
        generated_at_utc="2026-05-01T00:00:00Z",
        command="x",
        input_artifacts=(ReplayArtifactEntry(kind="input", path="../outside.json", sha256="a" * 64),),
    )
    replay = root / "replay_manifest.json"
    replay.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    result = verify_replay_manifest(replay, repo_root=root)
    assert result.ok is False
    assert any(item.startswith("PATH_OUTSIDE_ROOT:") for item in result.blockers)


def test_replay_manifest_verify_absolute_path_rejected_by_default(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    artifact = root / "inputs" / "ok.json"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text('{"ok":true}', encoding="utf-8")
    manifest = PaperResearchReplayManifest(
        artifact_id="abs-path",
        generated_at_utc="2026-05-01T00:00:00Z",
        command="x",
        input_artifacts=(ReplayArtifactEntry(kind="input", path=str(artifact), sha256="b" * 64),),
    )
    replay = root / "replay_manifest.json"
    replay.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    result = verify_replay_manifest(replay, repo_root=root)
    assert result.ok is False
    assert any(item.startswith("UNSAFE_PATH:") for item in result.blockers)


def test_replay_manifest_verify_symlink_escape_fails(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    target = tmp_path / "outside.json"
    target.write_text('{"secret":"x"}', encoding="utf-8")
    link = root / "inputs" / "escape.json"
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        link.symlink_to(target)
    except (NotImplementedError, OSError):
        pytest.skip("symlink creation unavailable on this platform")
    manifest = PaperResearchReplayManifest(
        artifact_id="symlink-escape",
        generated_at_utc="2026-05-01T00:00:00Z",
        command="x",
        input_artifacts=(ReplayArtifactEntry(kind="input", path="inputs/escape.json", sha256="c" * 64),),
    )
    replay = root / "replay_manifest.json"
    replay.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    result = verify_replay_manifest(replay, repo_root=root)
    assert result.ok is False
    assert any(item.startswith("SYMLINK_OUTSIDE_ROOT:") for item in result.blockers)


def test_missing_latest_manifest_returns_unknown_pending(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.chdir(tmp_path)
    payload = latest_replay_verification_summary(repo_root=tmp_path)
    assert payload["status"] == "UNKNOWN"
    assert "REPLAY_MANIFEST_NOT_FOUND" in payload["warnings"]
    assert "PENDING_REPLAY_EVIDENCE" in payload["warnings"]


def test_latest_manifest_discovery_uses_env_artifact_root(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    artifact_root = tmp_path / "custom-artifacts"
    inp = artifact_root / "input.json"
    out = artifact_root / "output.json"
    inp.parent.mkdir(parents=True, exist_ok=True)
    inp.write_text('{"in":1}', encoding="utf-8")
    out.write_text('{"out":1}', encoding="utf-8")
    replay = build_replay_manifest(
        repo_root=tmp_path,
        artifact_id="env-discovery",
        command="cmd",
        command_args_redacted=(),
        provider_id="p",
        provider_name="p",
        provider_mode="OFFLINE_REPLAY",
        provider_key_required=False,
        provider_key_present=False,
        trust_banner="t",
        license_usage_caveat="l",
        source_label="s",
        config_fingerprint=config_fingerprint_from_env({}),
        input_paths=(("input", inp),),
        output_paths=(("output", out),),
    )
    replay_path = artifact_root / "provider_paper_loop" / "latest" / "replay_manifest.json"
    replay_path.parent.mkdir(parents=True, exist_ok=True)
    replay_path.write_text(replay.model_dump_json(indent=2), encoding="utf-8")
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(artifact_root))
    payload = latest_replay_verification_summary(repo_root=tmp_path)
    assert payload["status"] in {"OK", "DEGRADED"}
    assert payload["replay_manifest_path"] == replay_path.as_posix()


def test_no_hard_coded_windows_manifest_fallback() -> None:
    source = Path("strategy_validator/application/paper_research_replay.py").read_text(encoding="utf-8")
    assert "C:/var/lib/strategy-validator/artifacts/provider_paper_loop/latest/replay_manifest.json" not in source


def test_redaction_separated_and_equals_syntax() -> None:
    secret = "SUPER_SECRET_VALUE_123"
    args = (
        "--token",
        secret,
        "--api-key=value1",
        "--normal",
        "ok",
        "api_token=value2",
        "--Bearer",
        "abc",
    )
    got = redact_command_args(args)
    joined = " ".join(got)
    assert secret not in joined
    assert "--token" in got
    assert "--api-key=<redacted>" in got
    assert "api_token=<redacted>" in got
    assert "--normal" in got and "ok" in got


def test_contract_rejects_invalid_digest_and_flags() -> None:
    with pytest.raises(ValueError):
        ReplayArtifactEntry(kind="in", path="a", sha256="xyz")
    with pytest.raises(ValueError):
        ReplayArtifactEntry(kind="", path="a", sha256="a" * 64)
    with pytest.raises(ValueError):
        ReplayArtifactEntry(kind="in", path="", sha256="a" * 64)
    normalized = ReplayArtifactEntry(kind="in", path="a", sha256="A" * 64)
    assert normalized.sha256 == "a" * 64
    with pytest.raises(ValueError):
        PaperResearchReplayManifest(
            artifact_id="bad-flags",
            generated_at_utc="2026-05-01T00:00:00",
            command="x",
            replayable_offline=False,
        )
    with pytest.raises(ValueError):
        PaperResearchReplayManifest(
            artifact_id="bad-paper-only",
            generated_at_utc="2026-05-01T00:00:00Z",
            command="x",
            paper_only=False,
        )
    with pytest.raises(ValueError):
        PaperResearchReplayManifest(
            artifact_id="bad-live-block",
            generated_at_utc="2026-05-01T00:00:00Z",
            command="x",
            live_trading_blocked=False,
        )
