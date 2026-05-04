from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pandas as pd

from strategy_validator.data_spine.universe.governance import PITUniverseGovernor


def test_pit_universe_converts_aware_timestamp_to_utc_without_relocalizing() -> None:
    governor = PITUniverseGovernor(universe_id="u", snapshot_hash="sha")
    membership = pd.DataFrame(
        [
            {
                "asset_id": "A",
                "valid_from": "2026-04-29T13:30:00Z",
                "valid_to": "2026-04-29T14:30:00Z",
            }
        ]
    )

    decision_time = datetime(2026, 4, 29, 16, 0, tzinfo=ZoneInfo("Europe/Berlin"))
    provenance = governor.get_lawful_membership(membership, decision_time, asset_ids=["A"])

    assert provenance.decision_time_utc == datetime(2026, 4, 29, 14, 0, tzinfo=timezone.utc)
    assert provenance.memberships[0].is_member is True
