from __future__ import annotations

import ipaddress
from urllib.parse import urlparse

_ALLOWED_SCHEMES = {"https"}
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _is_disallowed_private_host(host: str) -> bool:
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    return bool(
        address.is_loopback
        or address.is_private
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )


def validate_provider_url(value: str | None, *, allow_local: bool = False, field_name: str = "url") -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return value
    parsed = urlparse(text)
    if parsed.netloc and not parsed.scheme:
        raise ValueError(f"{field_name} must include an explicit https:// scheme")
    if parsed.scheme and parsed.scheme not in _ALLOWED_SCHEMES:
        raise ValueError(f"{field_name} must use https:// for provider network access")
    if parsed.scheme and not parsed.netloc:
        raise ValueError(f"{field_name} must include a host")
    host = (parsed.hostname or "").lower()
    if host in _LOCAL_HOSTS and not allow_local:
        raise ValueError(f"{field_name} must not target localhost unless allow_local=True")
    if host and _is_disallowed_private_host(host) and not allow_local:
        raise ValueError(f"{field_name} must not target private, loopback, link-local, reserved, or multicast addresses")
    return text


def validate_provider_url_template(value: str, *, allow_relative: bool = True, field_name: str = "url_template") -> str:
    text = str(value or "").strip()
    if not text:
        return value
    if text.startswith("//"):
        raise ValueError(f"{field_name} must not be a protocol-relative URL")
    if text.startswith("/") and allow_relative:
        return text
    validate_provider_url(text, allow_local=False, field_name=field_name)
    return text
