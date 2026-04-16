"""Append-only ledger writes. Production code must invoke only from validator.orchestrator."""

from __future__ import annotations

import hashlib
import inspect
import json
import math
from datetime import datetime, timezone

from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.core.enums import PromotionState
from strategy_validator.core.exceptions import (
    IllegalPromotionStateTransition,
    LedgerAuthorizationError,
    LedgerPayloadViolation,
)
from strategy_validator.core.manifest import compute_manifest_hash
from strategy_validator.ledger._append_only import LedgerEvent, append_event, read_latest_event

_ORCHESTRATOR_MODULE = "strategy_validator.validator.orchestrator"
_EVENT_TYPE = "adjudication.state_transition"


class _LedgerWriteAuthority:
    pass


_LEDGER_WRITE_AUTHORITY = _LedgerWriteAuthority()


def issue_write_authority() -> _LedgerWriteAuthority:
    caller = inspect.currentframe()
    caller_name = ""
    if caller is not None and caller.f_back is not None:
        caller_name = caller.f_back.f_globals.get("__name__", "")
    if caller_name != _ORCHESTRATOR_MODULE:
        raise LedgerAuthorizationError(
            "Only strategy_validator.validator.orchestrator may acquire ledger write authority."
        )
    return _LEDGER_WRITE_AUTHORITY


def _canonical_json(payload: dict[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _compute_event_hash(
    *,
    experiment_id: str,
    sequence_number: int,
    event_type: str,
    promotion_state: str,
    event_payload_json: str,
    manifest_hash: str,
    previous_event_hash: str | None,
    created_at_utc: datetime,
    writer_identity: str,
) -> str:
    hash_input = _canonical_json(
        {
            "experiment_id": experiment_id,
            "sequence_number": sequence_number,
            "event_type": event_type,
            "promotion_state": promotion_state,
            "event_payload_json": event_payload_json,
            "manifest_hash": manifest_hash,
            "previous_event_hash": previous_event_hash,
            "created_at_utc": created_at_utc.isoformat(),
            "writer_identity": writer_identity,
        }
    )
    return hashlib.sha256(hash_input.encode("utf-8")).hexdigest()


def _validate_state_transition(
    previous_state_name: str | None,
    next_state_name: str,
) -> None:
    if previous_state_name is None:
        return
    previous_state = PromotionState[previous_state_name]
    next_state = PromotionState[next_state_name]
    allowed: dict[PromotionState, set[PromotionState]] = {
        PromotionState.INVALID: {
            PromotionState.INVALID,
            PromotionState.REJECTED,
            PromotionState.QUARANTINED,
            PromotionState.CONDITIONAL,
            PromotionState.CANARY_ONLY,
            PromotionState.PROMOTABLE,
        },
        PromotionState.QUARANTINED: {
            PromotionState.QUARANTINED,
            PromotionState.REJECTED,
            PromotionState.INVALID,
            PromotionState.CONDITIONAL,
            PromotionState.CANARY_ONLY,
            PromotionState.PROMOTABLE,
        },
        PromotionState.CONDITIONAL: {
            PromotionState.CONDITIONAL,
            PromotionState.CANARY_ONLY,
            PromotionState.PROMOTABLE,
            PromotionState.REJECTED,
            PromotionState.INVALID,
        },
        PromotionState.CANARY_ONLY: {
            PromotionState.CANARY_ONLY,
            PromotionState.PROMOTABLE,
            PromotionState.REJECTED,
            PromotionState.INVALID,
        },
        PromotionState.PROMOTABLE: {
            PromotionState.PROMOTABLE,
            PromotionState.CANARY_ONLY,
            PromotionState.REJECTED,
            PromotionState.INVALID,
        },
        PromotionState.REJECTED: {
            PromotionState.REJECTED,
            PromotionState.INVALID,
        },
    }
    if next_state not in allowed[previous_state]:
        raise IllegalPromotionStateTransition(
            f"Illegal promotion-state transition: {previous_state.name} -> {next_state.name}"
        )


def _validate_ledger_payload(payload: dict[str, object], next_state: PromotionState) -> None:
    payload_state = payload.get("state")
    valid_payload_state_reprs = {next_state.name, next_state.value}
    if payload_state not in valid_payload_state_reprs:
        raise LedgerPayloadViolation(
            f"Payload state mismatch: payload.state={payload_state!r} vs next_state={next_state.name!r}"
        )
    evidence_bundle = payload.get("evidence_bundle")
    if not isinstance(evidence_bundle, dict):
        raise LedgerPayloadViolation("Missing evidence_bundle in manifest payload.")
    reproducibility = evidence_bundle.get("reproducibility")
    if not isinstance(reproducibility, dict):
        raise LedgerPayloadViolation("Missing reproducibility contract in evidence_bundle.")
    required_hash_fields = (
        "code_hash",
        "data_snapshot_hash",
        "universe_hash",
        "feature_graph_hash",
        "parameter_manifest_hash",
        "benchmark_version",
        "cost_model_version",
        "calendar_version",
    )
    for field in required_hash_fields:
        value = reproducibility.get(field)
        if not isinstance(value, str) or not value:
            raise LedgerPayloadViolation(f"Missing reproducibility field: {field}")
    if not isinstance(evidence_bundle.get("benchmark_rung"), str) or not evidence_bundle.get("benchmark_rung"):
        raise LedgerPayloadViolation("Missing benchmark_rung in evidence_bundle.")
    if next_state == PromotionState.PROMOTABLE:
        payload_experiment_id = payload.get("experiment_id")
        evidence_items = evidence_bundle.get("evidence_items")
        if not isinstance(evidence_items, list) or not evidence_items:
            raise LedgerPayloadViolation("PROMOTABLE writes require evidence_items.")
        has_benchmark_delta = False
        for ev in evidence_items:
            if isinstance(ev, dict) and isinstance(ev.get("payload"), dict):
                if ev.get("experiment_id") != payload_experiment_id:
                    raise LedgerPayloadViolation("PROMOTABLE writes require evidence_items experiment_id to match manifest.")
                payload_dict = ev["payload"]
                required_benchmark_fields = ("benchmark_id", "benchmark_version", "benchmark_delta")
                if all(field in payload_dict for field in required_benchmark_fields):
                    if not isinstance(payload_dict["benchmark_id"], str) or not payload_dict["benchmark_id"]:
                        continue
                    if payload_dict["benchmark_version"] != reproducibility["benchmark_version"]:
                        continue
                    try:
                        benchmark_delta = float(payload_dict["benchmark_delta"])
                    except Exception as exc:
                        raise LedgerPayloadViolation("PROMOTABLE benchmark_delta must be numeric.") from exc
                    if not math.isfinite(benchmark_delta):
                        raise LedgerPayloadViolation("PROMOTABLE benchmark_delta must be finite.")
                    has_benchmark_delta = True
                    break
        if not has_benchmark_delta:
            raise LedgerPayloadViolation(
                "PROMOTABLE writes require typed benchmark evidence: benchmark_id, benchmark_version, benchmark_delta."
            )
        if evidence_bundle.get("cpcv_passed") is not True:
            raise LedgerPayloadViolation("PROMOTABLE writes require cpcv_passed=True.")
        if not isinstance(evidence_bundle.get("cpcv_folds"), int) or int(evidence_bundle["cpcv_folds"]) < 2:
            raise LedgerPayloadViolation("PROMOTABLE writes require cpcv_folds>=2.")
        if "cpcv_path_coverage" not in evidence_bundle or evidence_bundle.get("cpcv_path_coverage") is None:
            raise LedgerPayloadViolation("PROMOTABLE writes require cpcv_path_coverage.")
        if float(evidence_bundle["cpcv_path_coverage"]) < 0.7:
            raise LedgerPayloadViolation("PROMOTABLE writes require cpcv_path_coverage >= 0.7.")
        if float(evidence_bundle["cpcv_path_coverage"]) > 1.0:
            raise LedgerPayloadViolation("PROMOTABLE writes require cpcv_path_coverage <= 1.0.")
        if "cpcv_path_stability" in evidence_bundle and evidence_bundle.get("cpcv_path_stability") is not None:
            if float(evidence_bundle["cpcv_path_stability"]) < 0.0:
                raise LedgerPayloadViolation("PROMOTABLE writes require cpcv_path_stability >= 0.0.")
            if float(evidence_bundle["cpcv_path_stability"]) > 1.0:
                raise LedgerPayloadViolation("PROMOTABLE writes require cpcv_path_stability <= 1.0.")
        if "dsr_estimate" not in evidence_bundle or evidence_bundle.get("dsr_estimate") is None:
            raise LedgerPayloadViolation("PROMOTABLE writes require dsr_estimate.")
        if float(evidence_bundle["dsr_estimate"]) < 0.0:
            raise LedgerPayloadViolation("PROMOTABLE writes require dsr_estimate >= 0.")
        if "pbo_estimate" not in evidence_bundle or evidence_bundle.get("pbo_estimate") is None:
            raise LedgerPayloadViolation("PROMOTABLE writes require pbo_estimate.")
        if float(evidence_bundle["pbo_estimate"]) > 0.2:
            raise LedgerPayloadViolation("PROMOTABLE writes require pbo_estimate <= 0.2.")
        if float(evidence_bundle["pbo_estimate"]) < 0.0:
            raise LedgerPayloadViolation("PROMOTABLE writes require pbo_estimate >= 0.0.")
        if evidence_bundle.get("decoy_survival_passed") is not True:
            raise LedgerPayloadViolation("PROMOTABLE writes require decoy_survival_passed=True.")
        if not isinstance(evidence_bundle.get("decoy_suite_version"), str) or not evidence_bundle.get("decoy_suite_version"):
            raise LedgerPayloadViolation("PROMOTABLE writes require decoy_suite_version.")
        if "decoy_coverage" not in evidence_bundle or evidence_bundle.get("decoy_coverage") is None:
            raise LedgerPayloadViolation("PROMOTABLE writes require decoy_coverage.")
        if float(evidence_bundle["decoy_coverage"]) < 1.0:
            raise LedgerPayloadViolation("PROMOTABLE writes require decoy_coverage == 1.0.")
        if float(evidence_bundle["decoy_coverage"]) > 1.0:
            raise LedgerPayloadViolation("PROMOTABLE writes require decoy_coverage <= 1.0.")
        # Capacity / Borrow realism validation for PROMOTABLE
        # execution_report lives in the most recent adjudication decision in promotion_history
        promotion_history = payload.get("promotion_history", [])
        if not isinstance(promotion_history, list) or not promotion_history:
            raise LedgerPayloadViolation("PROMOTABLE writes require promotion_history with at least one decision.")
        latest_decision = promotion_history[-1]
        execution_report = latest_decision.get("execution_report") if isinstance(latest_decision, dict) else None
        if not isinstance(execution_report, dict):
            raise LedgerPayloadViolation("PROMOTABLE writes require execution_report in the latest adjudication decision.")
        # Capacity gate must have been evaluated
        capacity = execution_report.get("capacity")
        if not isinstance(capacity, dict):
            raise LedgerPayloadViolation("PROMOTABLE writes require typed capacity evidence in execution_report.")
        if capacity.get("capacity_limit_passed") is not True:
            raise LedgerPayloadViolation("PROMOTABLE writes require capacity_limit_passed=True.")
        # Borrow gate: shortability must pass
        borrow = execution_report.get("borrow")
        if not isinstance(borrow, dict):
            raise LedgerPayloadViolation("PROMOTABLE writes require typed borrow evidence in execution_report.")
        requires_shorting = borrow.get("requires_shorting", False)
        shortability_passed = borrow.get("shortability_passed")
        if requires_shorting and shortability_passed is not True:
            raise LedgerPayloadViolation("PROMOTABLE writes require shortability_passed=True when shorting is required.")
        # Impact model mode must be declared (never ambiguous)
        impact_model_mode = execution_report.get("impact_model_mode")
        if not isinstance(impact_model_mode, str) or not impact_model_mode:
            raise LedgerPayloadViolation("PROMOTABLE writes require impact_model_mode in execution_report.")


def commit_state_transition(
    experiment: ExperimentManifest,
    authority: _LedgerWriteAuthority,
    *,
    adjudication_source: str = _ORCHESTRATOR_MODULE,
    created_at: datetime | None = None,
) -> str:
    """
    Persist an append-only manifest snapshot after adjudication.

    Restricted: only the orchestrator can acquire the authority token required here.
    """
    if authority is not _LEDGER_WRITE_AUTHORITY:
        raise LedgerAuthorizationError("Ledger writes require the orchestrator authority token.")

    payload = experiment.model_dump(mode="json")
    _validate_ledger_payload(payload, experiment.state)
    manifest_hash = compute_manifest_hash(payload)
    event_payload_json = _canonical_json(payload)
    previous_event = read_latest_event(experiment.experiment_id)
    sequence_number = 1 if previous_event is None else previous_event.sequence_number + 1
    previous_event_hash = None if previous_event is None else previous_event.event_hash
    _validate_state_transition(
        None if previous_event is None else previous_event.promotion_state,
        experiment.state.name,
    )
    created_at_utc = created_at or datetime.now(timezone.utc)
    event = LedgerEvent(
        experiment_id=experiment.experiment_id,
        sequence_number=sequence_number,
        event_type=_EVENT_TYPE,
        promotion_state=experiment.state.name,
        event_payload_json=event_payload_json,
        manifest_hash=manifest_hash,
        event_hash=_compute_event_hash(
            experiment_id=experiment.experiment_id,
            sequence_number=sequence_number,
            event_type=_EVENT_TYPE,
            promotion_state=experiment.state.name,
            event_payload_json=event_payload_json,
            manifest_hash=manifest_hash,
            previous_event_hash=previous_event_hash,
            created_at_utc=created_at_utc,
            writer_identity=adjudication_source,
        ),
        previous_event_hash=previous_event_hash,
        created_at_utc=created_at_utc,
        writer_identity=adjudication_source,
    )
    append_event(event)
    return event.event_hash
