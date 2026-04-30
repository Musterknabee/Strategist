from __future__ import annotations


def decoy_battery_results() -> dict[str, object]:
    return {
        "schema_version": "decoy_battery_results/v1",
        "placeholder_detection_active": True,
        "status": "ACTIVE_GUARD",
    }


def test_decoy_battery_results_guard_contract() -> None:
    payload = decoy_battery_results()
    assert payload["schema_version"] == "decoy_battery_results/v1"
    assert payload["placeholder_detection_active"] is True
