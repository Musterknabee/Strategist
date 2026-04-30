from __future__ import annotations

from pathlib import Path

from strategy_validator.cli.single_tenant_api_smoke import resolve_smoke_base_url, resolve_smoke_token


def test_api_smoke_resolves_token_from_env_file_without_shell_evaluation(tmp_path: Path, monkeypatch) -> None:
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

    assert resolve_smoke_token(env_file=env_file) == token


def test_api_smoke_prefers_environment_over_env_file(tmp_path: Path, monkeypatch) -> None:
    env_file = tmp_path / "deployment.env"
    env_file.write_text("STRATEGY_VALIDATOR_API_TOKEN=file-token-abcdefghijklmnopqrstuvwxyz\n", encoding="utf-8")
    monkeypatch.setenv("STRATEGY_VALIDATOR_API_TOKEN", "env-token-abcdefghijklmnopqrstuvwxyz")

    assert resolve_smoke_token(env_file=env_file) == "env-token-abcdefghijklmnopqrstuvwxyz"


def test_api_smoke_deprecated_token_argument_is_still_accepted(monkeypatch) -> None:
    monkeypatch.delenv("STRATEGY_VALIDATOR_API_TOKEN", raising=False)

    assert resolve_smoke_token(token="argv-token-abcdefghijklmnopqrstuvwxyz") == "argv-token-abcdefghijklmnopqrstuvwxyz"


def test_api_smoke_derives_base_url_from_env_file_host_port(tmp_path: Path, monkeypatch) -> None:
    env_file = tmp_path / "deployment.env"
    env_file.write_text("STRATEGY_VALIDATOR_HOST_PORT=18080\n", encoding="utf-8")
    monkeypatch.delenv("STRATEGY_VALIDATOR_BASE_URL", raising=False)
    monkeypatch.delenv("STRATEGY_VALIDATOR_HOST_PORT", raising=False)

    assert resolve_smoke_base_url(env_file=env_file) == "http://127.0.0.1:18080"


def test_api_smoke_base_url_overrides_host_port(tmp_path: Path, monkeypatch) -> None:
    env_file = tmp_path / "deployment.env"
    env_file.write_text(
        "STRATEGY_VALIDATOR_HOST_PORT=18080\nSTRATEGY_VALIDATOR_BASE_URL=http://127.0.0.1:19090/\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("STRATEGY_VALIDATOR_BASE_URL", raising=False)
    monkeypatch.delenv("STRATEGY_VALIDATOR_HOST_PORT", raising=False)

    assert resolve_smoke_base_url(env_file=env_file) == "http://127.0.0.1:19090"


def test_api_smoke_rejects_invalid_derived_host_port(tmp_path: Path, monkeypatch) -> None:
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
