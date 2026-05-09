"""Paper-tracking lifecycle inventory projection."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from strategy_validator.application.paper_tracking_common import _paper_tracking_root, _read_json
from strategy_validator.application.paper_tracking_lifecycle_assessment import (
    derive_candidate_lifecycle_assessment,
)
from strategy_validator.application.paper_tracking_lifecycle_persistence import (
    _read_lifecycle_assessment_optional,
    _read_scorecard_optional,
)
from strategy_validator.contracts.paper_tracking import PaperTrackingManifest


def list_paper_tracking_entries(
    *,
    repo_root: Path | None = None,
) -> list[dict[str, Any]]:
    """Inventory tracking directories with derived lifecycle (for CLI list)."""

    root = _paper_tracking_root(repo_root)
    if not root.is_dir():
        return []
    rows: list[tuple[float, dict[str, Any]]] = []
    for mpath in sorted(root.glob("*/paper_tracking_manifest.json")):
        tdir = mpath.parent
        tid = tdir.name
        try:
            manifest = PaperTrackingManifest.model_validate(_read_json(mpath))
        except ValueError:
            continue
        mtime = mpath.stat().st_mtime
        score = _read_scorecard_optional(tdir)
        persisted = _read_lifecycle_assessment_optional(tdir)
        derived = derive_candidate_lifecycle_assessment(manifest, score, tracking_dir=tdir)
        rows.append(
            (
                mtime,
                {
                    "tracking_id": tid,
                    "strategy_id": manifest.candidate.strategy_id,
                    "lifecycle_state": derived.state.value,
                    "persisted_assessment_state": persisted.state.value if persisted is not None else None,
                    "lifecycle_assessment_path": str(tdir / "lifecycle_assessment.json"),
                    "manifest_path": str(mpath),
                    "has_persisted_assessment": persisted is not None,
                },
            )
        )
    rows.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in rows]


__all__ = ["list_paper_tracking_entries"]
