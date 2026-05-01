from __future__ import annotations

import json
import io
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from strategy_validator.cli import single_tenant_api_smoke as smoke
from strategy_validator.cli.single_tenant_api_smoke import (
    _ERROR_TOKEN_SOURCE_ENV_FILE_REQUIRES_ENV_FILE,
    resolve_smoke_base_url,
    resolve_smoke_token,
)


def test_api_smoke_resolves_token_from_env_file_without_shell_evaluation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    token = "abcdefghijklmnopqrstuvwxyz1234567890TOKEN"
    env_file = tmp_path / "deployment.env"
    env_file.write_text(
        "\n".join(
            [
                "# comments are ignored",
                "export STRATEGY_VALIDATOR_API_TOKEN='" + token + "' # inline comment",
                "UNRELATED=$(echo should-not-run)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("STRATEGY_VALIDATOR_API_TOKEN", raising=False)

    resolution = resolve_smoke_token(env_file=env_file)
    assert resolution.token == token
    assert resolution.warnings == ()


def test_api_smoke_prefers_environment_over_env_file_in_auto_mode_when_values_match(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When env and file agree, auto mode uses env first without mismatch diagnostics."""
    shared = "shared-token-abcdefghijklmnopqrstuvwxyz"
    env_file = tmp_path / "deployment.env"
    env_file.write_text(f"STRATEGY_VALIDATOR_API_TOKEN={shared}\n", encoding="utf-8")
    monkeypatch.setenv("STRATEGY_VALIDATOR_API_TOKEN", shared)

    resolution = resolve_smoke_token(env_file=env_file, token_source="auto")
    assert resolution.token == shared
    assert resolution.warnings == ()


def test_api_smoke_auto_mode_env_precedence_when_env_and_file_differ(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_file = tmp_path / "deployment.env"
    env_file.write_text("STRATEGY_VALIDATOR_API_TOKEN=file-token-abcdefghijklmnopqrstuvwxyz\n", encoding="utf-8")
    monkeypatch.setenv("STRATEGY_VALIDATOR_API_TOKEN", "env-token-abcdefghijklmnopqrstuvwxyz")

    resolution = resolve_smoke_token(env_file=env_file, token_source="auto")
    assert resolution.token == "env-token-abcdefghijklmnopqrstuvwxyz"
    assert len(resolution.warnings) == 1


def test_api_smoke_auto_mode_emits_mismatch_warning_with_fingerprints_not_raw_secrets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_file = tmp_path / "deployment.env"
    env_file.write_text("STRATEGY_VALIDATOR_API_TOKEN=distinct-file-LEAK_MARKER_FILE\n", encoding="utf-8")
    monkeypatch.setenv("STRATEGY_VALIDATOR_API_TOKEN", "distinct-env-LEAK_MARKER_ENV")

    resolution = resolve_smoke_token(env_file=env_file, token_source="auto")
    assert resolution.token == "distinct-env-LEAK_MARKER_ENV"
    assert len(resolution.warnings) == 1
    w = resolution.warnings[0]
    assert "LEAK_MARKER" not in w
    assert "env_sha256_prefix=" in w and "file_sha256_prefix=" in w
    assert "distinct-env" not in w and "distinct-file" not in w


def test_api_smoke_token_source_env_forces_process_env_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / "deployment.env"
    env_file.write_text("STRATEGY_VALIDATOR_API_TOKEN=file-only-should-not-be-used\n", encoding="utf-8")
    monkeypatch.setenv("STRATEGY_VALIDATOR_API_TOKEN", "env-forced-token")

    resolution = resolve_smoke_token(env_file=env_file, token_source="env")
    assert resolution.token == "env-forced-token"
    assert resolution.warnings == ()


def test_api_smoke_token_source_env_missing_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / "deployment.env"
    env_file.write_text("STRATEGY_VALIDATOR_API_TOKEN=file-fallback-not-used\n", encoding="utf-8")
    monkeypatch.delenv("STRATEGY_VALIDATOR_API_TOKEN", raising=False)

    with pytest.raises(ValueError, match="token-source env"):
        resolve_smoke_token(env_file=env_file, token_source="env")


def test_api_smoke_token_source_env_file_forces_file_ignores_stale_process_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_file = tmp_path / "deployment.env"
    env_file.write_text("STRATEGY_VALIDATOR_API_TOKEN=from-file-align-with-docker\n", encoding="utf-8")
    monkeypatch.setenv("STRATEGY_VALIDATOR_API_TOKEN", "stale-shell-env-NEVER_USE_THIS")

    resolution = resolve_smoke_token(env_file=env_file, token_source="env-file")
    assert resolution.token == "from-file-align-with-docker"
    assert resolution.warnings == ()


def test_api_smoke_token_source_env_file_requires_env_file_path() -> None:
    with pytest.raises(ValueError) as excinfo:
        resolve_smoke_token(env_file=None, token_source="env-file")
    assert str(excinfo.value).startswith(_ERROR_TOKEN_SOURCE_ENV_FILE_REQUIRES_ENV_FILE)


def test_api_smoke_token_source_env_file_requires_nonempty_env_file_path() -> None:
    with pytest.raises(ValueError) as excinfo:
        resolve_smoke_token(env_file="", token_source="env-file")
    assert str(excinfo.value).startswith(_ERROR_TOKEN_SOURCE_ENV_FILE_REQUIRES_ENV_FILE)


def test_api_smoke_deprecated_token_argument_is_still_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("STRATEGY_VALIDATOR_API_TOKEN", raising=False)

    resolution = resolve_smoke_token(token="argv-token-abcdefghijklmnopqrstuvwxyz")
    assert resolution.token == "argv-token-abcdefghijklmnopqrstuvwxyz"
    assert resolution.warnings == ()


def test_api_smoke_deprecated_token_wins_over_token_source_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / "deployment.env"
    env_file.write_text("STRATEGY_VALIDATOR_API_TOKEN=file-token\n", encoding="utf-8")
    monkeypatch.setenv("STRATEGY_VALIDATOR_API_TOKEN", "env-token")

    resolution = resolve_smoke_token(token="argv-wins", env_file=env_file, token_source="env-file")
    assert resolution.token == "argv-wins"


def test_api_smoke_token_env_var_custom_name(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / "deployment.env"
    env_file.write_text("MY_CUSTOM_TOKEN=custom-from-file\n", encoding="utf-8")
    monkeypatch.delenv("MY_CUSTOM_TOKEN", raising=False)

    resolution = resolve_smoke_token(env_file=env_file, token_source="env-file", token_env_var="MY_CUSTOM_TOKEN")
    assert resolution.token == "custom-from-file"


def test_main_json_includes_error_code_when_env_file_required_but_missing() -> None:
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = smoke.main(
            [
                "--token-source",
                "env-file",
                "--base-url",
                "http://127.0.0.1:1",
                "--wait-seconds",
                "0",
            ]
        )
    payload = json.loads(buf.getvalue())
    assert payload["error_code"] == _ERROR_TOKEN_SOURCE_ENV_FILE_REQUIRES_ENV_FILE
    assert payload["ok"] is False
    assert code == 0

    buf2 = io.StringIO()
    with redirect_stdout(buf2):
        code_fail = smoke.main(
            [
                "--token-source",
                "env-file",
                "--base-url",
                "http://127.0.0.1:1",
                "--require-pass",
            ]
        )
    assert code_fail == 2


def test_main_auto_mismatch_stderr_has_no_raw_token_material(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    env_file = tmp_path / "deployment.env"
    env_file.write_text("STRATEGY_VALIDATOR_API_TOKEN=supersecretfileZZZ\n", encoding="utf-8")
    monkeypatch.setenv("STRATEGY_VALIDATOR_API_TOKEN", "supersecretenvYYY")

    buf = io.StringIO()
    with redirect_stdout(buf):
        smoke.main(
            [
                "--base-url",
                "http://127.0.0.1:1",
                "--env-file",
                str(env_file),
                "--wait-seconds",
                "0",
                "--timeout",
                "0.01",
            ]
        )
    captured = capsys.readouterr()
    combined = captured.err + captured.out + buf.getvalue()
    assert "supersecretfile" not in combined
    assert "supersecretenv" not in combined
    assert "ZZZ" not in combined and "YYY" not in combined
    assert "env_sha256_prefix=" in captured.err


def test_api_smoke_derives_base_url_from_env_file_host_port(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / "deployment.env"
    env_file.write_text("STRATEGY_VALIDATOR_HOST_PORT=18080\n", encoding="utf-8")
    monkeypatch.delenv("STRATEGY_VALIDATOR_BASE_URL", raising=False)
    monkeypatch.delenv("STRATEGY_VALIDATOR_HOST_PORT", raising=False)

    assert resolve_smoke_base_url(env_file=env_file) == "http://127.0.0.1:18080"


def test_api_smoke_base_url_overrides_host_port(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / "deployment.env"
    env_file.write_text(
        "STRATEGY_VALIDATOR_HOST_PORT=18080\nSTRATEGY_VALIDATOR_BASE_URL=http://127.0.0.1:19090/\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("STRATEGY_VALIDATOR_BASE_URL", raising=False)
    monkeypatch.delenv("STRATEGY_VALIDATOR_HOST_PORT", raising=False)

    assert resolve_smoke_base_url(env_file=env_file) == "http://127.0.0.1:19090"


def test_api_smoke_rejects_invalid_derived_host_port(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / "deployment.env"
    env_file.write_text("STRATEGY_VALIDATOR_HOST_PORT=99999\n", encoding="utf-8")
    monkeypatch.delenv("STRATEGY_VALIDATOR_BASE_URL", raising=False)
    monkeypatch.delenv("STRATEGY_VALIDATOR_HOST_PORT", raising=False)

    try:
        resolve_smoke_base_url(env_file=env_file)
    except ValueError as exc:
        assert "between 1 and 65535" in str(exc)
    else:  # pragma: no cover - assertion clarity
        raise AssertionError("expected invalid host port to fail")
