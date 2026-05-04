from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_module(name: str, relative: str) -> object:
    path = REPO_ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def check_provider_keys_mod():
    return _load_module("_check_provider_keys", "scripts/check_provider_keys.py")


@pytest.fixture
def retrieve_provider_samples_mod():
    return _load_module("_retrieve_provider_samples", "scripts/retrieve_provider_samples.py")


def test_check_provider_keys_redacts_values(check_provider_keys_mod, tmp_path: Path) -> None:
    secret = "super-secret-token-not-in-output-12345"
    env_file = tmp_path / "deployment.env"
    env_file.write_text(f"FRED_API_KEY={secret}\nALPACA_TRADING_MODE=paper\n", encoding="utf-8")
    report = check_provider_keys_mod.build_report(env_file=env_file)
    dumped = json.dumps(report)
    assert secret not in dumped
    fred = next(p for p in report["providers"] if p["provider_id"] == "fred")
    assert fred["configured"] is True
    assert fred.get("secret_sha256_prefix")
    assert len(fred["secret_sha256_prefix"]) == 16


def test_check_provider_keys_blocks_live_without_approval(check_provider_keys_mod, tmp_path: Path) -> None:
    env_file = tmp_path / "e.env"
    env_file.write_text("ALPACA_TRADING_MODE=live\nPERSONAL_LIVE_APPROVED=false\n", encoding="utf-8")
    report = check_provider_keys_mod.build_report(env_file=env_file)
    assert report["alpaca_live_policy_violations"]


def test_retrieve_provider_samples_no_network(tmp_path: Path, retrieve_provider_samples_mod) -> None:
    rc = retrieve_provider_samples_mod.main(
        [
            "--public-only",
            "--no-network",
            "--output-dir",
            str(tmp_path / "samples"),
            "--manifest-json",
            "--max-samples",
            "2",
        ]
    )
    assert rc == 0
    manifest = json.loads((tmp_path / "samples" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "provider_samples_manifest/v1"
    assert len(manifest["entries"]) == 2
    for row in manifest["entries"]:
        assert row["status"] in {"SKIPPED_NO_NETWORK", "OK", "PENDING_KEY", "PENDING_MANUAL_BROKER_SETUP"}
        assert row["classified_status"] in {
            "SKIPPED_NO_NETWORK",
            "PENDING_KEY",
            "PENDING_MANUAL_BROKER_SETUP",
        }
        assert row["http_status"] == -2


def test_keyed_fred_classifies_401_without_leaking_key(tmp_path: Path, retrieve_provider_samples_mod, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_http_get(url: str, headers=None, timeout=None):  # noqa: ANN001
        _ = (url, headers, timeout)
        return 401, b'{"error":"Unauthorized"}', "HTTP Error 401: Unauthorized"

    monkeypatch.setattr(retrieve_provider_samples_mod, "_http_get", fake_http_get)
    env_file = tmp_path / "e.env"
    env_file.write_text("FRED_API_KEY=testfredkey_value_12345678\n", encoding="utf-8")
    out = tmp_path / "keyed_out"
    rc = retrieve_provider_samples_mod.main(
        [
            "--providers",
            "fred",
            "--env-file",
            str(env_file),
            "--output-dir",
            str(out),
            "--manifest-json",
        ]
    )
    assert rc == 0
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    entry = manifest["entries"][0]
    assert entry["classified_status"] == "AUTH_FAILED"
    assert entry["http_status"] == 401
    raw = json.dumps(manifest)
    assert "testfredkey" not in raw


def test_alpaca_base_url_with_v2_suffix_is_normalized(tmp_path: Path, retrieve_provider_samples_mod, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    def fake_http_get(url: str, headers=None, timeout=None):  # noqa: ANN001
        seen["url"] = url
        seen["headers"] = headers
        seen["timeout"] = timeout
        return 200, b'{"account_number":"redacted-test"}', None

    monkeypatch.setattr(retrieve_provider_samples_mod, "_http_get", fake_http_get)
    env_file = tmp_path / "e.env"
    env_file.write_text(
        "\n".join(
            [
                "ALPACA_API_KEY=test-alpaca-key",
                "ALPACA_API_SECRET=test-alpaca-secret",
                "ALPACA_BASE_URL=https://paper-api.alpaca.markets/v2",
                "ALPACA_TRADING_MODE=paper",
            ]
        ),
        encoding="utf-8",
    )
    out = tmp_path / "keyed_out"
    rc = retrieve_provider_samples_mod.main(
        [
            "--providers",
            "alpaca",
            "--env-file",
            str(env_file),
            "--output-dir",
            str(out),
            "--manifest-json",
        ]
    )
    assert rc == 0
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    entry = manifest["entries"][0]
    assert seen["url"] == "https://paper-api.alpaca.markets/v2/account"
    assert entry["endpoint"] == "https://paper-api.alpaca.markets/v2/account"
    raw = json.dumps(manifest)
    assert "test-alpaca-key" not in raw
    assert "test-alpaca-secret" not in raw


def test_manifest_does_not_embed_env_secrets(tmp_path: Path, retrieve_provider_samples_mod) -> None:
    env_file = tmp_path / "secrets.env"
    token = "NEWSAPI_LEAK_TEST_TOKEN_XYZ"
    env_file.write_text(f"NEWSAPI_KEY={token}\n", encoding="utf-8")
    out = tmp_path / "out"
    rc = retrieve_provider_samples_mod.main(
        [
            "--providers",
            "newsapi",
            "--no-network",
            "--env-file",
            str(env_file),
            "--output-dir",
            str(out),
            "--manifest-json",
        ]
    )
    assert rc == 0
    raw = (out / "manifest.json").read_text(encoding="utf-8")
    assert token not in raw
    sample_files = list(out.glob("*.json"))
    for path in sample_files:
        assert token not in path.read_text(encoding="utf-8")
