from __future__ import annotations

from fastapi import APIRouter, Query

from strategy_validator.api.routes._ui_detail_legacy import legacy_callable


build_ui_semantic_validator_handoff_archive_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_archive_latest_payload')
build_ui_semantic_validator_handoff_archive_payload = legacy_callable('build_ui_semantic_validator_handoff_archive_payload')
build_ui_semantic_validator_handoff_closure_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_closure_latest_payload')
build_ui_semantic_validator_handoff_closure_payload = legacy_callable('build_ui_semantic_validator_handoff_closure_payload')
build_ui_semantic_validator_handoff_continuity_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_continuity_latest_payload')
build_ui_semantic_validator_handoff_continuity_payload = legacy_callable('build_ui_semantic_validator_handoff_continuity_payload')
build_ui_semantic_validator_handoff_custody_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_custody_latest_payload')
build_ui_semantic_validator_handoff_custody_payload = legacy_callable('build_ui_semantic_validator_handoff_custody_payload')
build_ui_semantic_validator_handoff_decision_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_decision_latest_payload')
build_ui_semantic_validator_handoff_decision_payload = legacy_callable('build_ui_semantic_validator_handoff_decision_payload')
build_ui_semantic_validator_handoff_lineage_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_lineage_latest_payload')
build_ui_semantic_validator_handoff_lineage_payload = legacy_callable('build_ui_semantic_validator_handoff_lineage_payload')
build_ui_semantic_validator_handoff_remediation_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_remediation_latest_payload')
build_ui_semantic_validator_handoff_remediation_payload = legacy_callable('build_ui_semantic_validator_handoff_remediation_payload')
build_ui_semantic_validator_handoff_review_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_review_latest_payload')
build_ui_semantic_validator_handoff_review_payload = legacy_callable('build_ui_semantic_validator_handoff_review_payload')
build_ui_semantic_validator_handoff_runbook_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_runbook_latest_payload')
build_ui_semantic_validator_handoff_runbook_payload = legacy_callable('build_ui_semantic_validator_handoff_runbook_payload')
build_ui_semantic_validator_handoff_signoff_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_signoff_latest_payload')
build_ui_semantic_validator_handoff_signoff_payload = legacy_callable('build_ui_semantic_validator_handoff_signoff_payload')

router = APIRouter()

@router.get('/semantic-validator-handoff/lineage')
def get_semantic_validator_handoff_lineage(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    chain_status: list[str] = Query(default=[]),
    ready_for_operator_review: bool | None = None,
    require_broken_links: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_lineage_payload(
        repo_root=repo_root,
        search_root=search_root,
        experiment_id_contains=experiment_id_contains,
        issue_contains=issue_contains,
        chain_status=tuple(chain_status or ()),
        ready_for_operator_review=ready_for_operator_review,
        require_broken_links=require_broken_links,
        limit=limit,
    )

@router.get('/semantic-validator-handoff/lineage/latest')
def get_semantic_validator_handoff_lineage_latest(
    repo_root: str | None = None,
    search_root: str | None = None,
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_lineage_latest_payload(repo_root=repo_root, search_root=search_root)

@router.get('/semantic-validator-handoff/remediation')
def get_semantic_validator_handoff_remediation(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    chain_status: list[str] = Query(default=[]),
    remediation_status: list[str] = Query(default=[]),
    severity: list[str] = Query(default=[]),
    require_operator_action: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_remediation_payload(
        repo_root=repo_root,
        search_root=search_root,
        experiment_id_contains=experiment_id_contains,
        issue_contains=issue_contains,
        chain_status=tuple(chain_status or ()),
        remediation_status=tuple(remediation_status or ()),
        severity=tuple(severity or ()),
        require_operator_action=require_operator_action,
        limit=limit,
    )

@router.get('/semantic-validator-handoff/remediation/latest')
def get_semantic_validator_handoff_remediation_latest(
    repo_root: str | None = None,
    search_root: str | None = None,
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_remediation_latest_payload(repo_root=repo_root, search_root=search_root)

@router.get('/semantic-validator-handoff/review')
def get_semantic_validator_handoff_review(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    review_status: list[str] = Query(default=[]),
    trust_banner: list[str] = Query(default=[]),
    operator_review_allowed: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_review_payload(
        repo_root=repo_root,
        search_root=search_root,
        experiment_id_contains=experiment_id_contains,
        issue_contains=issue_contains,
        review_status=tuple(review_status or ()),
        trust_banner=tuple(trust_banner or ()),
        operator_review_allowed=operator_review_allowed,
        limit=limit,
    )

@router.get('/semantic-validator-handoff/review/latest')
def get_semantic_validator_handoff_review_latest(
    repo_root: str | None = None,
    search_root: str | None = None,
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_review_latest_payload(repo_root=repo_root, search_root=search_root)

@router.get('/semantic-validator-handoff/decision')
def get_semantic_validator_handoff_decision(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    decision_status: list[str] = Query(default=[]),
    trust_banner: list[str] = Query(default=[]),
    decision_ready: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_decision_payload(
        repo_root=repo_root,
        search_root=search_root,
        experiment_id_contains=experiment_id_contains,
        issue_contains=issue_contains,
        decision_status=tuple(decision_status or ()),
        trust_banner=tuple(trust_banner or ()),
        decision_ready=decision_ready,
        limit=limit,
    )

@router.get('/semantic-validator-handoff/decision/latest')
def get_semantic_validator_handoff_decision_latest(
    repo_root: str | None = None,
    search_root: str | None = None,
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_decision_latest_payload(repo_root=repo_root, search_root=search_root)

@router.get('/semantic-validator-handoff/signoff')
def get_semantic_validator_handoff_signoff(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    signoff_status: list[str] = Query(default=[]),
    trust_banner: list[str] = Query(default=[]),
    signoff_recorded: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_signoff_payload(
        repo_root=repo_root,
        search_root=search_root,
        experiment_id_contains=experiment_id_contains,
        issue_contains=issue_contains,
        signoff_status=tuple(signoff_status or ()),
        trust_banner=tuple(trust_banner or ()),
        signoff_recorded=signoff_recorded,
        limit=limit,
    )

@router.get('/semantic-validator-handoff/signoff/latest')
def get_semantic_validator_handoff_signoff_latest(
    repo_root: str | None = None,
    search_root: str | None = None,
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_signoff_latest_payload(repo_root=repo_root, search_root=search_root)

@router.get('/semantic-validator-handoff/custody')
def get_semantic_validator_handoff_custody(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    custody_status: list[str] = Query(default=[]),
    trust_banner: list[str] = Query(default=[]),
    custody_seal_recorded: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_custody_payload(
        repo_root=repo_root,
        search_root=search_root,
        experiment_id_contains=experiment_id_contains,
        issue_contains=issue_contains,
        custody_status=tuple(custody_status or ()),
        trust_banner=tuple(trust_banner or ()),
        custody_seal_recorded=custody_seal_recorded,
        limit=limit,
    )

@router.get('/semantic-validator-handoff/custody/latest')
def get_semantic_validator_handoff_custody_latest(
    repo_root: str | None = None,
    search_root: str | None = None,
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_custody_latest_payload(repo_root=repo_root, search_root=search_root)

@router.get('/semantic-validator-handoff/archive')
def get_semantic_validator_handoff_archive(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    archive_status: list[str] = Query(default=[]),
    trust_banner: list[str] = Query(default=[]),
    archive_manifest_verified: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_archive_payload(
        repo_root=repo_root,
        search_root=search_root,
        experiment_id_contains=experiment_id_contains,
        issue_contains=issue_contains,
        archive_status=tuple(archive_status or ()),
        trust_banner=tuple(trust_banner or ()),
        archive_manifest_verified=archive_manifest_verified,
        limit=limit,
    )

@router.get('/semantic-validator-handoff/archive/latest')
def get_semantic_validator_handoff_archive_latest(
    repo_root: str | None = None,
    search_root: str | None = None,
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_archive_latest_payload(repo_root=repo_root, search_root=search_root)

@router.get('/semantic-validator-handoff/closure')
def get_semantic_validator_handoff_closure(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    closure_status: list[str] = Query(default=[]),
    trust_banner: list[str] = Query(default=[]),
    closure_attestation_recorded: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_closure_payload(
        repo_root=repo_root,
        search_root=search_root,
        experiment_id_contains=experiment_id_contains,
        issue_contains=issue_contains,
        closure_status=tuple(closure_status or ()),
        trust_banner=tuple(trust_banner or ()),
        closure_attestation_recorded=closure_attestation_recorded,
        limit=limit,
    )

@router.get('/semantic-validator-handoff/closure/latest')
def get_semantic_validator_handoff_closure_latest(
    repo_root: str | None = None,
    search_root: str | None = None,
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_closure_latest_payload(repo_root=repo_root, search_root=search_root)

@router.get('/semantic-validator-handoff/continuity')
def get_semantic_validator_handoff_continuity(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    terminal_status: list[str] = Query(default=[]),
    current_stage: list[str] = Query(default=[]),
    open_action: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_continuity_payload(
        repo_root=repo_root,
        search_root=search_root,
        experiment_id_contains=experiment_id_contains,
        issue_contains=issue_contains,
        terminal_status=tuple(terminal_status or ()),
        current_stage=tuple(current_stage or ()),
        open_action=open_action,
        limit=limit,
    )

@router.get('/semantic-validator-handoff/continuity/latest')
def get_semantic_validator_handoff_continuity_latest(
    repo_root: str | None = None,
    search_root: str | None = None,
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_continuity_latest_payload(repo_root=repo_root, search_root=search_root)

@router.get('/semantic-validator-handoff/runbook')
def get_semantic_validator_handoff_runbook(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    action_kind: list[str] = Query(default=[]),
    priority: list[str] = Query(default=[]),
    severity: list[str] = Query(default=[]),
    completed: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_runbook_payload(
        repo_root=repo_root,
        search_root=search_root,
        experiment_id_contains=experiment_id_contains,
        issue_contains=issue_contains,
        action_kind=tuple(action_kind or ()),
        priority=tuple(priority or ()),
        severity=tuple(severity or ()),
        completed=completed,
        limit=limit,
    )

@router.get('/semantic-validator-handoff/runbook/latest')
def get_semantic_validator_handoff_runbook_latest(
    repo_root: str | None = None,
    search_root: str | None = None,
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_runbook_latest_payload(repo_root=repo_root, search_root=search_root)

__all__ = (
    'router',
    'get_semantic_validator_handoff_lineage',
    'get_semantic_validator_handoff_lineage_latest',
    'get_semantic_validator_handoff_remediation',
    'get_semantic_validator_handoff_remediation_latest',
    'get_semantic_validator_handoff_review',
    'get_semantic_validator_handoff_review_latest',
    'get_semantic_validator_handoff_decision',
    'get_semantic_validator_handoff_decision_latest',
    'get_semantic_validator_handoff_signoff',
    'get_semantic_validator_handoff_signoff_latest',
    'get_semantic_validator_handoff_custody',
    'get_semantic_validator_handoff_custody_latest',
    'get_semantic_validator_handoff_archive',
    'get_semantic_validator_handoff_archive_latest',
    'get_semantic_validator_handoff_closure',
    'get_semantic_validator_handoff_closure_latest',
    'get_semantic_validator_handoff_continuity',
    'get_semantic_validator_handoff_continuity_latest',
    'get_semantic_validator_handoff_runbook',
    'get_semantic_validator_handoff_runbook_latest',
)
