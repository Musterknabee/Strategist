from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.contracts.oracle import OracleStrategicBriefingReport, OracleStrategicFusionReport


def load_fusion_report(path: Path) -> OracleStrategicFusionReport:
    return OracleStrategicFusionReport.model_validate(json.loads(path.read_text(encoding="utf-8")))


def load_strategic_briefing_report(path: Path) -> OracleStrategicBriefingReport:
    return OracleStrategicBriefingReport.model_validate(json.loads(path.read_text(encoding="utf-8")))
