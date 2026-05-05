from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.cli.evidence_bundle_index import main


def test_json_output_emits_valid_payload(tmp_path: Path, capsys, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    code = main(["--json", "--artifact-root", "artifacts"])
    captured = capsys.readouterr()
    assert code == 0
    payload = json.loads(captured.out)
    assert payload["schema_version"] == "evidence_bundle_index/v1"
    assert isinstance(payload["entries"], list)


def test_missing_optional_artifacts_do_not_fail(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    code = main(["--artifact-root", "artifacts"])
    assert code == 0


def test_include_digests_emits_sha256(tmp_path: Path, capsys, monkeypatch) -> None:
    release_root = tmp_path / "artifacts" / "release_verification" / "latest"
    release_root.mkdir(parents=True)
    (release_root / "main-release-verification-pack.md").write_text("report", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    code = main(["--json", "--artifact-root", "artifacts", "--include-digests"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    markdown = next(item for item in payload["entries"] if item["kind"] == "release_verification_markdown")
    assert isinstance(markdown["sha256"], str)


def test_unsafe_output_path_exits_non_zero(tmp_path: Path, capsys, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    outside = tmp_path.parent / "outside-index.json"
    code = main(["--artifact-root", "artifacts", "--output-path", str(outside)])
    captured = capsys.readouterr()
    assert code == 2
    assert "ARTIFACT_OUTPUT_OUTSIDE_ROOT" in captured.err


def test_output_redacts_secret_like_environment_values(tmp_path: Path, capsys, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("STRATEGY_VALIDATOR_API_TOKEN", "SUPERSECRET_TOKEN_VALUE")
    code = main(["--json", "--artifact-root", "artifacts"])
    raw = capsys.readouterr().out
    assert code == 0
    assert "SUPERSECRET_TOKEN_VALUE" not in raw
