import json
from pathlib import Path

from strategy_validator.cli.operator_doctor import (
    build_operator_doctor_report,
    main,
    write_markdown,
)


def _write_env(path: Path, *, token: str = "abcdefghijklmnopqrstuvwxyz1234567890") -> None:
    path.write_text(
        "\n".join(
            [
                "STRATEGY_VALIDATOR_MODE=PRODUCTION",
                f"STRATEGY_VALIDATOR_API_TOKEN={token}",
                "STRATEGY_VALIDATOR_API_TOKEN_SCOPES=operator:command:write,operator:projection:read",
                "STRATEGY_VALIDATOR_LEDGER_DB_PATH=/var/lib/strategy-validator/ledger.sqlite3",
                "STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR=/var/backups/strategy-validator",
                "STRATEGY_VALIDATOR_ARTIFACT_ROOT=/var/lib/strategy-validator/artifacts",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_json_report_shape_and_disclaimers(tmp_path: Path) -> None:
    env = tmp_path / "deployment.env"
    _write_env(env)
    payload = build_operator_doctor_report(repo_root=tmp_path, env_file=env)
    assert payload["schema_version"] == "operator_doctor/v1"
    assert payload["status"] in {"PASS", "WARN", "FAIL", "UNKNOWN"}
    assert "not production deployment approval" in " ".join(item.lower() for item in payload["disclaimers"])
    assert "no live trading authorization" in " ".join(item.lower() for item in payload["disclaimers"])


def test_missing_env_file_has_guidance(tmp_path: Path) -> None:
    payload = build_operator_doctor_report(repo_root=tmp_path, env_file=tmp_path / "missing.env")
    assert payload["status"] == "FAIL"
    assert any("setup_local_deployment.py" in cmd for cmd in payload["next_recommended_commands"])


def test_placeholder_token_is_not_ready(tmp_path: Path) -> None:
    env = tmp_path / "deployment.env"
    _write_env(env, token="CHANGEME")
    payload = build_operator_doctor_report(repo_root=tmp_path, env_file=env)
    assert payload["ok"] is False
    assert payload["deployment_env_status"]["status"] == "FAIL"
    assert any("deployment env check failed" in item.lower() for item in payload["blockers"])


def test_missing_provider_keys_warn_not_fatal(tmp_path: Path) -> None:
    env = tmp_path / "deployment.env"
    _write_env(env)
    payload = build_operator_doctor_report(repo_root=tmp_path, env_file=env)
    assert payload["provider_key_posture"]["status"] == "PENDING_KEY"
    assert any("optional provider keys" in item.lower() for item in payload["warnings"])


def test_raw_token_redacted_from_json_and_markdown(tmp_path: Path) -> None:
    env = tmp_path / "deployment.env"
    secret = "SUPERSECRET_TOKEN_VALUE_1234567890"
    _write_env(env, token=secret)
    payload = build_operator_doctor_report(repo_root=tmp_path, env_file=env, token=secret, token_source="explicit")
    encoded = json.dumps(payload, sort_keys=True)
    assert secret not in encoded
    markdown_path = tmp_path / "doctor.md"
    write_markdown(markdown_path, payload)
    assert secret not in markdown_path.read_text(encoding="utf-8")


def test_next_commands_deterministic(tmp_path: Path) -> None:
    payload_a = build_operator_doctor_report(repo_root=tmp_path, env_file=tmp_path / "missing.env")
    payload_b = build_operator_doctor_report(repo_root=tmp_path, env_file=tmp_path / "missing.env")
    assert payload_a["next_recommended_commands"] == payload_b["next_recommended_commands"]


def test_require_ready_returns_non_zero_when_blocked(tmp_path: Path, capsys) -> None:
    code = main(
        [
            "--repo-root",
            str(tmp_path),
            "--env-file",
            str(tmp_path / "missing.env"),
            "--json",
            "--require-ready",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert code == 2
    assert payload["ok"] is False
