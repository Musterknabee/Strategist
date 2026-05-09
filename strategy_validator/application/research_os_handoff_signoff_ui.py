"""UI payload projection for Research OS handoff verification/signoff status."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_handoff_signoff_common import (
    _SCHEMA,
    research_os_handoff_reviewer_signoff_latest_path,
    research_os_handoff_verification_latest_path,
)
from strategy_validator.application.research_os_handoff_signoff_reviewer import load_latest_research_os_handoff_reviewer_signoff
from strategy_validator.application.research_os_handoff_signoff_verification import load_latest_research_os_handoff_verification_result
from strategy_validator.contracts.research_os_handoff_signoff import (
    ResearchOsHandoffReviewerDecision,
    ResearchOsHandoffVerificationStatus,
)


def build_ui_research_os_handoff_signoff_latest_payload(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> dict[str, Any]:
    verification_path = research_os_handoff_verification_latest_path(repo_root, artifact_root)
    signoff_path = research_os_handoff_reviewer_signoff_latest_path(repo_root, artifact_root)
    verification = load_latest_research_os_handoff_verification_result(repo_root=repo_root, artifact_root=artifact_root)
    signoff = load_latest_research_os_handoff_reviewer_signoff(repo_root=repo_root, artifact_root=artifact_root)
    degraded: list[str] = []
    if verification is None:
        degraded.append("NO_RESEARCH_OS_HANDOFF_VERIFICATION_RESULT")
    elif verification.status != ResearchOsHandoffVerificationStatus.VERIFIED:
        degraded.append(f"HANDOFF_VERIFICATION_{verification.status.value}")
    if signoff is None:
        degraded.append("NO_RESEARCH_OS_HANDOFF_REVIEWER_SIGNOFF")
    elif signoff.decision in {ResearchOsHandoffReviewerDecision.BLOCKED, ResearchOsHandoffReviewerDecision.REJECTED}:
        degraded.append(f"HANDOFF_SIGNOFF_{signoff.decision.value}")
    return {
        "schema_version": _SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PRESENT" if verification is not None or signoff is not None else "MISSING",
        "degraded": degraded,
        "verification_path": str(verification_path),
        "signoff_path": str(signoff_path),
        "latest_verification": verification.model_dump(mode="json") if verification is not None else None,
        "latest_signoff": signoff.model_dump(mode="json") if signoff is not None else None,
        "read_plane_only": True,
        "no_live_trading": True,
        "no_broker_orders": True,
        "no_order_controls": True,
    }

__all__ = ["build_ui_research_os_handoff_signoff_latest_payload"]
