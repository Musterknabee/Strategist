"""Oracle mutation proposal engine: advisory artifacts only (no writes, no trading)."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from strategy_validator.contracts.oracle_mutation_proposal import (
    OracleMutationProposalArtifact,
    OracleMutationProposalItem,
)
from strategy_validator.contracts.strategy_thesis import StrategyThesis


def build_mutation_proposals(
    *,
    thesis: StrategyThesis,
    batch_run_id: str,
    strategy_type: str | None = None,
) -> OracleMutationProposalArtifact:
    """Derive bounded parameter-delta proposals from thesis falsification posture."""
    st = strategy_type or thesis.strategy_id or "unknown"
    proposals: list[OracleMutationProposalItem] = []

    proposals.append(
        OracleMutationProposalItem(
            proposal_id=f"{batch_run_id}:tighten_falsification",
            summary="Tighten falsification observability before expanding risk budget.",
            suggested_param_delta={"signal_window_delta": 4, "oos_holdout_bars_suggestion": 24},
            rationale="Thesis stresses falsification-first posture; prefer smaller parameter nudges with explicit OOS replay.",
        )
    )
    if "momentum" in st or "trend" in st:
        proposals.append(
            OracleMutationProposalItem(
                proposal_id=f"{batch_run_id}:momentum_defensive",
                summary="Reduce breakout participation under marginal robustness.",
                suggested_param_delta={"breakout_k_delta": 0.05, "exposure_delta": -0.05},
                rationale="Trend families degrade when participation thins; proposal is paper-only sensitivity guidance.",
            )
        )
    if "reversion" in st or "mean" in st:
        proposals.append(
            OracleMutationProposalItem(
                proposal_id=f"{batch_run_id}:reversion_widen_band",
                summary="Widen entry band slightly if OOS degradation is marginal.",
                suggested_param_delta={"z_entry_delta": 0.1},
                rationale="Mean-reversion templates may need wider bands when microstructure noise rises; validate on holdout.",
            )
        )

    body = OracleMutationProposalArtifact(
        batch_run_id=batch_run_id,
        thesis_id=thesis.thesis_id,
        proposals=proposals,
    )
    digest = hashlib.sha256(
        json.dumps(body.model_dump(mode="json", exclude={"digest_sha256"}), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return body.model_copy(update={"digest_sha256": digest})
