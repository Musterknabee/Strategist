from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.contracts.oracle_strategic_programs import OracleStrategicCampaignReport


def load_strategic_campaign_report(path: Path) -> OracleStrategicCampaignReport:
    return OracleStrategicCampaignReport.model_validate(json.loads(path.read_text(encoding="utf-8")))
