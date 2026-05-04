from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def psp_mod():
    path = REPO_ROOT / "scripts" / "provider_sample_public.py"
    spec = importlib.util.spec_from_file_location("_provider_sample_public_test", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_analyze_sample_body_json(psp_mod) -> None:
    kind, meta = psp_mod.analyze_sample_body(b'{"x": [1, 2]}')
    assert kind == "json"
    assert "byte_length" in meta


def test_analyze_sample_body_xml(psp_mod) -> None:
    kind, meta = psp_mod.analyze_sample_body(b'<?xml version="1.0"?><root><a/></root>')
    assert kind == "xml"
    assert meta.get("xml_root_hint") == "root"


def test_analyze_sample_body_csv_like(psp_mod) -> None:
    payload = b"col1,col2\n1,2\n3,4\n"
    kind, meta = psp_mod.analyze_sample_body(payload)
    assert kind == "csv_like"
    assert "csv_header_hint" in meta


def test_classify_public_fetch_ok_json(psp_mod) -> None:
    st, meta = psp_mod.classify_public_fetch(200, None, b'{"ok": true}')
    assert st == psp_mod.CLASS_OK
    assert meta.get("detected_format") == "json"


def test_classify_public_fetch_non_json_xml(psp_mod) -> None:
    st, meta = psp_mod.classify_public_fetch(200, None, b"<series><v>1</v></series>")
    assert st == psp_mod.CLASS_NON_JSON_VALID
    assert meta.get("detected_format") == "xml"


def test_classify_public_fetch_rate_limited(psp_mod) -> None:
    st, _meta = psp_mod.classify_public_fetch(429, None, b"")
    assert st == psp_mod.CLASS_RATE_LIMITED


def test_classify_public_fetch_timeout(psp_mod) -> None:
    st, meta = psp_mod.classify_public_fetch(-1, "HTTP Error: timed out", b"")
    assert st == psp_mod.CLASS_TEMP_UNAVAILABLE
    assert meta.get("reason") == "timeout"


def test_classify_public_fetch_network_blocked(psp_mod) -> None:
    st, _meta = psp_mod.classify_public_fetch(-1, "getaddrinfo failed: Name or service not known", b"")
    assert st == psp_mod.CLASS_NETWORK_BLOCKED


def test_classify_public_fetch_404_endpoint_changed(psp_mod) -> None:
    st, meta = psp_mod.classify_public_fetch(404, None, b"")
    assert st == psp_mod.CLASS_ENDPOINT_CHANGED
    assert meta.get("http") == 404


def test_classify_json_invalid_is_parse_error(psp_mod) -> None:
    st, meta = psp_mod.classify_public_fetch(200, None, b'{"broken": ')
    assert st == psp_mod.CLASS_PARSE_ERROR
    assert meta.get("detected_format") == "json_invalid"


def test_classify_keyed_401_auth_failed(psp_mod) -> None:
    st, meta = psp_mod.classify_keyed_fetch(401, None, b"")
    assert st == psp_mod.CLASS_AUTH_FAILED
    assert meta.get("http") == 401


def test_classify_keyed_402_plan_limited(psp_mod) -> None:
    st, meta = psp_mod.classify_keyed_fetch(402, None, b"")
    assert st == psp_mod.CLASS_PLAN_LIMITED


def test_classify_keyed_403_plan_keywords(psp_mod) -> None:
    st, _meta = psp_mod.classify_keyed_fetch(403, None, b'{"message":"upgrade your subscription"}')
    assert st == psp_mod.CLASS_PLAN_LIMITED


def test_classify_keyed_403_auth_keywords(psp_mod) -> None:
    st, _meta = psp_mod.classify_keyed_fetch(403, None, b'{"error":"invalid api key"}')
    assert st == psp_mod.CLASS_AUTH_FAILED


def test_classify_keyed_451_plan(psp_mod) -> None:
    st, meta = psp_mod.classify_keyed_fetch(451, None, b"")
    assert st == psp_mod.CLASS_PLAN_LIMITED
    assert meta.get("http") == 451


def test_classify_keyed_200_alphavantage_note_rate(psp_mod) -> None:
    body = b'{"Note": "Thank you for using Alpha Vantage! Please contact..."}'
    st, meta = psp_mod.classify_keyed_fetch(200, None, body)
    assert st == psp_mod.CLASS_RATE_LIMITED
    assert meta.get("provider_signal") == "alphavantage_note"


def test_classify_keyed_200_error_message_auth(psp_mod) -> None:
    body = b'{"Error Message": "Invalid API call."}'
    st, meta = psp_mod.classify_keyed_fetch(200, None, body)
    assert st == psp_mod.CLASS_AUTH_FAILED
    assert meta.get("provider_signal") == "error_message_field"


def test_classify_keyed_200_ok_when_clean_json(psp_mod) -> None:
    st, meta = psp_mod.classify_keyed_fetch(200, None, b'{"Global Quote": {"01. symbol": "IBM"}}')
    assert st == psp_mod.CLASS_OK
    assert meta.get("detected_format") == "json"


def test_classify_keyed_200_parse_error_invalid_json(psp_mod) -> None:
    st, meta = psp_mod.classify_keyed_fetch(200, None, b'{"a":')
    assert st == psp_mod.CLASS_PARSE_ERROR


def test_classify_keyed_success_false(psp_mod) -> None:
    st, meta = psp_mod.classify_keyed_fetch(200, None, b'{"success": false, "error": {"code": 101}}')
    assert st == psp_mod.CLASS_AUTH_FAILED
    assert meta.get("provider_signal") == "success_false"


def test_classify_keyed_coinmarketcap_status_error(psp_mod) -> None:
    body = b'{"status": {"error_code": 401, "error_message": "bad key"}, "data": {}}'
    st, meta = psp_mod.classify_keyed_fetch(200, None, body)
    assert st == psp_mod.CLASS_AUTH_FAILED
    assert meta.get("provider_signal") == "status_object"


def test_classify_keyed_coinmarketcap_success_no_false_positive(psp_mod) -> None:
    body = b'{"status": {"timestamp": "x", "error_code": 0, "error_message": null}, "data": {}}'
    st, meta = psp_mod.classify_keyed_fetch(200, None, body)
    assert st == psp_mod.CLASS_OK


def test_redact_secret_in_url(psp_mod) -> None:
    secret = "my_secret_key_value_12345"
    url = f"https://example.com/x?apikey={secret}&fmt=json"
    red = psp_mod.redact_secret_in_url(url, secret)
    assert secret not in red
    assert "<redacted>" in red
