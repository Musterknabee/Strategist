from __future__ import annotations

from strategy_validator.contracts.oracle_strategic_memory import OracleStrategicMemoryHorizonReport


HistoryIntegrityStatus = str


def history_integrity_status(memory_report: OracleStrategicMemoryHorizonReport | None) -> HistoryIntegrityStatus:
    return getattr(memory_report, "history_integrity_status", "CURRENT_ONLY") if memory_report is not None else "CURRENT_ONLY"


def sealed_history_observation_count(memory_report: OracleStrategicMemoryHorizonReport | None) -> int:
    return int(getattr(memory_report, "sealed_history_observation_count", 0) or 0) if memory_report is not None else 0


def unsealed_history_excluded_count(memory_report: OracleStrategicMemoryHorizonReport | None) -> int:
    return int(getattr(memory_report, "unsealed_history_excluded_count", 0) or 0) if memory_report is not None else 0


def contradiction_penalty(memory_report: OracleStrategicMemoryHorizonReport | None) -> float:
    status = history_integrity_status(memory_report)
    if status == "SEALED_HISTORY":
        return 0.0
    if status == "MIXED_HISTORY":
        return 0.14
    return 0.22


def campaign_friction(memory_report: OracleStrategicMemoryHorizonReport | None) -> float:
    status = history_integrity_status(memory_report)
    if status == "SEALED_HISTORY":
        return 0.12
    if status == "MIXED_HISTORY":
        return 0.52
    return 0.78


def integrity_operator_action(memory_report: OracleStrategicMemoryHorizonReport | None) -> str:
    status = history_integrity_status(memory_report)
    if status == "SEALED_HISTORY":
        return "Keep sealing prior strategic stacks before using historical drift to rank contradictions or continue campaigns."
    if status == "MIXED_HISTORY":
        return "Reduce strategic action velocity until mixed history is replaced by verified strategic stack bundles."
    return "Do not rely on historical drift for contradiction ranking or campaign expansion until at least one prior strategic stack is sealed and verified."


def integrity_fact(memory_report: OracleStrategicMemoryHorizonReport | None) -> str:
    return (
        f"history_integrity={history_integrity_status(memory_report)}:"
        f"sealed={sealed_history_observation_count(memory_report)}:"
        f"excluded_unsealed={unsealed_history_excluded_count(memory_report)}"
    )



def queue_operator_friction(memory_report: OracleStrategicMemoryHorizonReport | None) -> float:
    status = history_integrity_status(memory_report)
    if status == "SEALED_HISTORY":
        return 0.0
    if status == "MIXED_HISTORY":
        return 0.16
    return 0.24


def research_priority_penalty(memory_report: OracleStrategicMemoryHorizonReport | None) -> float:
    status = history_integrity_status(memory_report)
    if status == "SEALED_HISTORY":
        return 0.0
    if status == "MIXED_HISTORY":
        return 0.12
    return 0.18


def intervention_penalty(memory_report: OracleStrategicMemoryHorizonReport | None) -> float:
    status = history_integrity_status(memory_report)
    if status == "SEALED_HISTORY":
        return 0.0
    if status == "MIXED_HISTORY":
        return 0.10
    return 0.16


def campaign_penalty(memory_report: OracleStrategicMemoryHorizonReport | None) -> float:
    status = history_integrity_status(memory_report)
    if status == "SEALED_HISTORY":
        return 0.0
    if status == "MIXED_HISTORY":
        return 0.14
    return 0.22


def campaign_operator_friction(memory_report: OracleStrategicMemoryHorizonReport | None) -> float:
    status = history_integrity_status(memory_report)
    if status == "SEALED_HISTORY":
        return 0.0
    if status == "MIXED_HISTORY":
        return 0.20
    return 0.32


def preferred_strategic_backing_source(memory_report: OracleStrategicMemoryHorizonReport | None) -> str | None:
    if memory_report is None:
        return None
    manifest_paths = [str(item).strip() for item in getattr(memory_report, "source_stack_manifest_paths", []) if str(item).strip()]
    status = history_integrity_status(memory_report)
    if manifest_paths and status == "SEALED_HISTORY":
        return "strategic_stack_manifest"
    if status == "MIXED_HISTORY":
        return "mixed_lineage_context"
    if status == "CURRENT_ONLY":
        return "current_epoch_only"
    return None


def preferred_strategic_backing_classification(memory_report: OracleStrategicMemoryHorizonReport | None) -> str | None:
    if memory_report is None:
        return None
    manifest_paths = [str(item).strip() for item in getattr(memory_report, "source_stack_manifest_paths", []) if str(item).strip()]
    status = history_integrity_status(memory_report)
    if manifest_paths and status == "SEALED_HISTORY":
        return "SEALED_STRATEGIC_STACK_BACKED"
    if status in {"MIXED_HISTORY", "CURRENT_ONLY"}:
        return "NO_STRATEGIC_STACK_HISTORY"
    return None


def strategic_backing_facts(memory_report: OracleStrategicMemoryHorizonReport | None) -> list[str]:
    source = preferred_strategic_backing_source(memory_report)
    classification = preferred_strategic_backing_classification(memory_report)
    facts: list[str] = []
    if source:
        facts.append(f"preferred_backing_source={source}")
    if classification:
        facts.append(f"preferred_backing_classification={classification}")
    return facts
