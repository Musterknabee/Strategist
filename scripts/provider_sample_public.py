"""Pure helpers for classifying public provider sample responses (no I/O)."""
from __future__ import annotations

import json
import re
from typing import Any

# Semantic buckets for manifest.classified_status (public samples).
CLASS_OK = "OK"
CLASS_NON_JSON_VALID = "NON_JSON_BUT_VALID"
CLASS_RATE_LIMITED = "RATE_LIMITED"
CLASS_TEMP_UNAVAILABLE = "TEMPORARILY_UNAVAILABLE"
CLASS_ENDPOINT_CHANGED = "ENDPOINT_CHANGED"
CLASS_NETWORK_BLOCKED = "NETWORK_BLOCKED"
CLASS_PARSE_ERROR = "PARSE_ERROR"
CLASS_SKIPPED_NO_NETWORK = "SKIPPED_NO_NETWORK"
CLASS_PENDING_KEY = "PENDING_KEY"
CLASS_PENDING_BROKER = "PENDING_MANUAL_BROKER_SETUP"
CLASS_POLICY_SKIP = "POLICY_SKIP"
CLASS_AUTH_FAILED = "AUTH_FAILED"
CLASS_PLAN_LIMITED = "PLAN_LIMITED"


def analyze_sample_body(body: bytes) -> tuple[str, dict[str, Any]]:
    """Return (kind, metadata) where kind is json|xml|csv_like|text|empty|binary|json_invalid."""
    meta: dict[str, Any] = {"byte_length": len(body)}
    if not body:
        return "empty", meta
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        return "binary", meta
    stripped = text.strip()
    if not stripped:
        return "empty", meta
    if stripped[0] in "{[":
        try:
            json.loads(stripped)
            return "json", meta
        except json.JSONDecodeError:
            meta["fragment"] = stripped[:200].replace("\n", " ")
            return "json_invalid", meta
    head = stripped[:800]
    if stripped.startswith("<?xml") or head.lstrip().startswith("<"):
        m = re.search(r"<([A-Za-z0-9_:.-]+)(\s|>|/)", stripped[:2000])
        meta["xml_root_hint"] = m.group(1) if m else "unknown"
        return "xml", meta
    lines = stripped.splitlines()
    if len(lines) >= 2 and "," in lines[0]:
        meta["csv_header_hint"] = lines[0][:160]
        return "csv_like", meta
    meta["text_preview"] = stripped[:160]
    return "text", meta


def classify_public_http_transport(http_code: int, err_msg: str | None) -> tuple[str | None, dict[str, Any]]:
    """If transport alone determines classification, return (status, meta); else (None, {})."""
    meta: dict[str, Any] = {}
    err_l = (err_msg or "").lower()
    if http_code == -1:
        if any(s in err_l for s in ("timed out", "timeout")):
            return CLASS_TEMP_UNAVAILABLE, {**meta, "reason": "timeout", "detail": (err_msg or "")[:200]}
        if any(
            s in err_l
            for s in (
                "unreachable",
                "getaddrinfo",
                "name or service not known",
                "name resolution",
                "no route to host",
                "connection refused",
                "network is unreachable",
            )
        ):
            return CLASS_NETWORK_BLOCKED, {**meta, "detail": (err_msg or "")[:200]}
        return CLASS_TEMP_UNAVAILABLE, {**meta, "detail": (err_msg or "")[:200]}
    if http_code == 429:
        return CLASS_RATE_LIMITED, meta
    if http_code in (502, 503, 504):
        return CLASS_TEMP_UNAVAILABLE, {**meta, "http": http_code}
    if http_code == 404:
        return CLASS_ENDPOINT_CHANGED, {**meta, "http": http_code}
    if http_code == 403:
        return CLASS_TEMP_UNAVAILABLE, {**meta, "http": 403, "hint": "forbidden_or_waf"}
    if http_code != 200:
        return CLASS_TEMP_UNAVAILABLE, {**meta, "http": http_code}
    return None, meta


def classify_public_fetch(http_code: int, err_msg: str | None, body: bytes) -> tuple[str, dict[str, Any]]:
    """Full classification for a completed HTTP exchange (public providers)."""
    early, early_meta = classify_public_http_transport(http_code, err_msg)
    if early is not None:
        return early, dict(sorted(early_meta.items()))

    assert http_code == 200
    kind, body_meta = analyze_sample_body(body)
    merged: dict[str, Any] = dict(sorted(body_meta.items()))
    merged["detected_format"] = kind
    if kind == "json":
        return CLASS_OK, merged
    if kind in ("xml", "csv_like", "text", "binary"):
        return CLASS_NON_JSON_VALID, merged
    if kind == "empty":
        return CLASS_TEMP_UNAVAILABLE, {**merged, "reason": "empty_body"}
    if kind == "json_invalid":
        return CLASS_PARSE_ERROR, merged
    return CLASS_PARSE_ERROR, merged


def normalized_metadata_for_manifest(meta: dict[str, Any]) -> dict[str, Any]:
    """Stable key order for JSON manifest output."""
    return dict(sorted(meta.items()))


def _body_text_lower(body: bytes, max_chars: int = 8000) -> str:
    if not body:
        return ""
    try:
        return body.decode("utf-8", errors="replace")[:max_chars].lower()
    except Exception:
        return ""


def infer_keyed_api_signal(body: bytes) -> tuple[str | None, dict[str, Any]]:
    """Detect provider-specific error/limit payloads that still return HTTP 200."""
    meta: dict[str, Any] = {}
    if not body:
        return None, meta
    try:
        data = json.loads(body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeError):
        return None, meta
    if not isinstance(data, dict):
        return None, meta

    if isinstance(data.get("Information"), str) and "call frequency" in data["Information"].lower():
        return CLASS_RATE_LIMITED, {**meta, "provider_signal": "alphavantage_information"}
    if isinstance(data.get("Note"), str):
        n = data["Note"].lower()
        if "call frequency" in n or "thank you for using alpha vantage" in n:
            return CLASS_RATE_LIMITED, {**meta, "provider_signal": "alphavantage_note"}
    if data.get("Error Message") or data.get("error message"):
        return CLASS_AUTH_FAILED, {**meta, "provider_signal": "error_message_field"}
    if isinstance(data.get("error"), str) and any(
        x in data["error"].lower() for x in ("invalid", "unauthor", "api key", "not allowed")
    ):
        return CLASS_AUTH_FAILED, {**meta, "provider_signal": "error_string"}
    if isinstance(data.get("error"), dict):
        err = str(data["error"]).lower()
        if any(x in err for x in ("invalid", "unauthor", "key")):
            return CLASS_AUTH_FAILED, {**meta, "provider_signal": "error_object"}
    if data.get("status") == "error":
        return CLASS_AUTH_FAILED, {**meta, "provider_signal": "status_error"}
    if isinstance(data.get("message"), str):
        m = data["message"].lower()
        if any(x in m for x in ("invalid api", "invalid key", "unauthor", "access denied", "forbidden")):
            return CLASS_AUTH_FAILED, {**meta, "provider_signal": "message_field"}
        if any(x in m for x in ("subscription", "upgrade", "plan", "premium", "quota", "limit exceeded")):
            return CLASS_PLAN_LIMITED, {**meta, "provider_signal": "message_field"}
    if isinstance(data.get("errors"), list) and data["errors"]:
        return CLASS_AUTH_FAILED, {**meta, "provider_signal": "errors_array"}
    resp = data.get("response")
    if isinstance(resp, dict) and resp.get("status") in ("failed", "error"):
        return CLASS_AUTH_FAILED, {**meta, "provider_signal": "nested_response"}
    if data.get("success") is False:
        return CLASS_AUTH_FAILED, {**meta, "provider_signal": "success_false"}
    st_cmc = data.get("status")
    if isinstance(st_cmc, dict):
        if st_cmc.get("error_message"):
            return CLASS_AUTH_FAILED, {**meta, "provider_signal": "status_object"}
        ec = st_cmc.get("error_code")
        try:
            if ec is not None and int(ec) != 0:
                return CLASS_AUTH_FAILED, {**meta, "provider_signal": "status_object"}
        except (TypeError, ValueError):
            if ec not in (None, "", "0", 0):
                return CLASS_AUTH_FAILED, {**meta, "provider_signal": "status_object"}

    return None, meta


def classify_keyed_http_transport(http_code: int, err_msg: str | None, body: bytes) -> tuple[str | None, dict[str, Any]]:
    """Classify keyed APIs from HTTP layer; return (None, {}) if body/200 handling should continue."""
    meta: dict[str, Any] = {}
    combined = ((err_msg or "").lower() + " " + _body_text_lower(body))[:12000]

    if http_code == 401:
        return CLASS_AUTH_FAILED, {**meta, "http": 401}
    if http_code == 402:
        return CLASS_PLAN_LIMITED, {**meta, "http": 402}
    if http_code == 429:
        return CLASS_RATE_LIMITED, {**meta, "http": 429}
    if http_code == 404:
        return CLASS_ENDPOINT_CHANGED, {**meta, "http": 404}
    if http_code == 403:
        if any(x in combined for x in ("plan", "subscription", "upgrade", "license", "premium", "payment", "billing")):
            return CLASS_PLAN_LIMITED, {**meta, "http": 403}
        if any(x in combined for x in ("invalid", "unauthor", "api key", "access denied", "forbidden", "not allowed")):
            return CLASS_AUTH_FAILED, {**meta, "http": 403}
        return CLASS_TEMP_UNAVAILABLE, {**meta, "http": 403, "hint": "forbidden"}
    if http_code == 451:
        return CLASS_PLAN_LIMITED, {**meta, "http": 451}
    if http_code == -1:
        early, m = classify_public_http_transport(-1, err_msg)
        return early, dict(sorted(m.items()))
    if 400 <= http_code < 500:
        if http_code == 422:
            if any(x in combined for x in ("plan", "quota", "limit", "subscription")):
                return CLASS_PLAN_LIMITED, {**meta, "http": 422}
            return CLASS_TEMP_UNAVAILABLE, {**meta, "http": 422}
        elif any(x in combined for x in ("invalid api key", "invalid key", "api key", "unauthor", "access denied")):
            return CLASS_AUTH_FAILED, {**meta, "http": http_code}
        elif any(x in combined for x in ("quota", "limit", "plan", "subscription", "upgrade")):
            return CLASS_PLAN_LIMITED, {**meta, "http": http_code}
        else:
            return CLASS_TEMP_UNAVAILABLE, {**meta, "http": http_code}
    if http_code in (502, 503, 504):
        return CLASS_TEMP_UNAVAILABLE, {**meta, "http": http_code}
    if http_code != 200 and http_code > 0:
        return CLASS_TEMP_UNAVAILABLE, {**meta, "http": http_code}
    return None, meta


def classify_keyed_fetch(http_code: int, err_msg: str | None, body: bytes) -> tuple[str, dict[str, Any]]:
    """Classification for API-key providers (HTTP + JSON error envelopes)."""
    early, early_meta = classify_keyed_http_transport(http_code, err_msg, body)
    if early is not None:
        return early, normalized_metadata_for_manifest(early_meta)

    assert http_code == 200
    api_sig, sig_meta = infer_keyed_api_signal(body)
    if api_sig:
        return api_sig, normalized_metadata_for_manifest(sig_meta)

    return classify_public_fetch(200, err_msg, body)


def redact_secret_in_url(url: str, secret: str | None) -> str:
    """Replace API key/token substrings in URL for manifest-safe logging."""
    if not secret or len(secret) < 8:
        if "?" in url:
            base, _q = url.split("?", 1)
            return base + "?<redacted_query>"
        return url
    redacted = url.replace(secret, "<redacted>")
    if redacted == url:
        from urllib.parse import quote, unquote

        for variant in (quote(secret, safe=""), unquote(secret)):
            if len(variant) > 7 and variant in url:
                redacted = url.replace(variant, "<redacted>")
                break
    return redacted
