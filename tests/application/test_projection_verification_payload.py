from __future__ import annotations

from strategy_validator.application.projection_backfill import _canonical_payload_digest


def test_projection_payload_digest_is_order_stable_for_dict_keys() -> None:
    assert _canonical_payload_digest({"b": 2, "a": 1}) == _canonical_payload_digest({"a": 1, "b": 2})
