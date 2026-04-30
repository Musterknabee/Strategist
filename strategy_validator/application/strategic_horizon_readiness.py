from __future__ import annotations

import ast
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Literal

StrategicHorizonStatus = Literal['READY', 'CONDITIONAL', 'DEFERRED', 'BLOCKED']
StrategicHorizonAction = Literal[
    'PROCEED_WITH_BOUNDED_IMPLEMENTATION',
    'PROCEED_ONLY_WITH_GOVERNED_EXCEPTION',
    'DEFER_UNTIL_PREREQUISITES_EXIST',
    'DO_NOT_BUILD',
]


@dataclass(frozen=True)
class StrategicHorizonCheck:
    """One Horizon-C capability gate derived from repository/runtime evidence."""

    capability: str
    status: StrategicHorizonStatus
    recommended_action: StrategicHorizonAction
    evidence: tuple[str, ...] = field(default_factory=tuple)
    blockers: tuple[str, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_payload(self) -> dict[str, Any]:
        return {
            'capability': self.capability,
            'status': self.status,
            'recommended_action': self.recommended_action,
            'evidence': list(self.evidence),
            'blockers': list(self.blockers),
            'notes': list(self.notes),
        }


@dataclass(frozen=True)
class StrategicHorizonReadinessReport:
    """Operator-facing gate for later strategic horizons.

    This is deliberately conservative: Horizon C items are not marked READY
    unless the repository/runtime contains concrete implementation evidence.
    """

    schema_version: str
    status: StrategicHorizonStatus
    recommended_action: StrategicHorizonAction
    checks: tuple[StrategicHorizonCheck, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'status': self.status,
            'recommended_action': self.recommended_action,
            'checks': [check.to_payload() for check in self.checks],
        }


def _repo_path(repo_root: Path, *parts: str) -> Path:
    return (repo_root / Path(*parts)).resolve()


def _existing(paths: Iterable[Path]) -> tuple[str, ...]:
    return tuple(str(path) for path in paths if path.exists())


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _check_frontend_operator_ui(repo_root: Path) -> StrategicHorizonCheck:
    package_json = _repo_path(repo_root, 'ui', 'strategist-web', 'package.json')
    app_dir = _repo_path(repo_root, 'ui', 'strategist-web')
    if package_json.exists():
        return StrategicHorizonCheck(
            capability='frontend_operator_ui',
            status='CONDITIONAL',
            recommended_action='PROCEED_ONLY_WITH_GOVERNED_EXCEPTION',
            evidence=(str(package_json),),
            notes=('Frontend package exists; require CI typecheck/test/build before treating it as productized.',),
        )
    return StrategicHorizonCheck(
        capability='frontend_operator_ui',
        status='DEFERRED',
        recommended_action='DEFER_UNTIL_PREREQUISITES_EXIST',
        evidence=_existing((app_dir, package_json)),
        blockers=('FRONTEND_PACKAGE_NOT_PRESENT',),
        notes=('Backend UI/read-model seams exist, but no ui/strategist-web implementation is present in this repository.',),
    )


def _check_credentialed_provider_burnin(repo_root: Path) -> StrategicHorizonCheck:
    marker_env = (os.environ.get('STRATEGY_VALIDATOR_CREDENTIALED_BURNIN_ARTIFACT') or '').strip()
    candidate_paths: list[Path] = []
    if marker_env:
        candidate_paths.append(Path(marker_env).expanduser())
    candidate_paths.extend(_repo_path(repo_root, 'docs', 'artifacts').glob('**/*CREDENTIALED*BURNIN*.json'))
    candidate_paths.extend(_repo_path(repo_root, 'docs', 'artifacts').glob('**/*credentialed*burnin*.json'))

    for path in candidate_paths:
        if not path.exists():
            continue
        data = _load_json(path)
        if not data:
            continue
        credentialed = data.get('credentialed_live_provider') is True or data.get('provider_credentials_verified') is True
        fallback_disabled = data.get('fallback_used') is False or data.get('total_fallback_count') == 0
        freshness_validated = data.get('freshness_validated') is True or data.get('live_freshness_validated') is True
        if credentialed and fallback_disabled and freshness_validated:
            return StrategicHorizonCheck(
                capability='credentialed_live_provider_burnin',
                status='READY',
                recommended_action='PROCEED_WITH_BOUNDED_IMPLEMENTATION',
                evidence=(str(path),),
                notes=('Credentialed burn-in marker declares live credentials, no fallback, and freshness validation.',),
            )

    return StrategicHorizonCheck(
        capability='credentialed_live_provider_burnin',
        status='BLOCKED',
        recommended_action='DEFER_UNTIL_PREREQUISITES_EXIST',
        evidence=tuple(str(path) for path in candidate_paths if path.exists()),
        blockers=('NO_CREDENTIALED_LIVE_PROVIDER_BURNIN_ARTIFACT',),
        notes=(
            'Existing pilot artifacts are not enough for live-provider readiness unless a credentialed marker proves live credentials, no fallback, and freshness validation.',
        ),
    )


def _check_multi_tenant_scaling(repo_root: Path) -> StrategicHorizonCheck:
    tenancy_paths = _existing((
        _repo_path(repo_root, 'strategy_validator', 'tenancy'),
        _repo_path(repo_root, 'strategy_validator', 'ledger', 'tenant_store.py'),
    ))
    if tenancy_paths:
        return StrategicHorizonCheck(
            capability='multi_tenant_scaling',
            status='CONDITIONAL',
            recommended_action='PROCEED_ONLY_WITH_GOVERNED_EXCEPTION',
            evidence=tenancy_paths,
            blockers=('TENANCY_SECURITY_REVIEW_REQUIRED',),
            notes=('Tenant isolation code exists, but requires explicit security and ledger-isolation review before rollout.',),
        )
    return StrategicHorizonCheck(
        capability='multi_tenant_scaling',
        status='DEFERRED',
        recommended_action='DO_NOT_BUILD',
        blockers=('SINGLE_TENANT_LEDGER_MODEL_IS_CURRENT_AUTHORITY',),
        notes=('The current architecture is a single-tenant/operator control plane; horizontal/multi-tenant scale is not justified yet.',),
    )


def _oracle_python_files(repo_root: Path) -> tuple[Path, ...]:
    return tuple(sorted(_repo_path(repo_root, 'strategy_validator', 'validator').glob('oracle_*.py')))


def _syntax_failures(paths: Iterable[Path]) -> tuple[str, ...]:
    failures: list[str] = []
    for path in paths:
        try:
            ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        except SyntaxError as exc:
            failures.append(f'{path}:{exc.lineno}:{exc.msg}')
        except OSError as exc:
            failures.append(f'{path}:0:{exc}')
    return tuple(failures)


def _check_oracle_advisory_expansion(repo_root: Path) -> StrategicHorizonCheck:
    oracle_files = _oracle_python_files(repo_root)
    failures = _syntax_failures(oracle_files)
    if failures:
        return StrategicHorizonCheck(
            capability='oracle_advisory_expansion',
            status='BLOCKED',
            recommended_action='DEFER_UNTIL_PREREQUISITES_EXIST',
            evidence=tuple(str(path) for path in oracle_files[:10]),
            blockers=failures,
            notes=('Oracle/advisory source must be syntax-clean before advisory expansion.',),
        )
    return StrategicHorizonCheck(
        capability='oracle_advisory_expansion',
        status='CONDITIONAL',
        recommended_action='PROCEED_ONLY_WITH_GOVERNED_EXCEPTION',
        evidence=(f'oracle_python_file_count={len(oracle_files)}',),
        blockers=('EVENT_SPINE_AND_PROJECTION_BOUNDARIES_MUST_REMAIN_AUTHORITATIVE',),
        notes=('Oracle/advisory work may continue only as read-only/evidence-producing surfaces; no ledger mutation authority may move there.',),
    )


def _check_workflow_engine_integration(repo_root: Path) -> StrategicHorizonCheck:
    config = (os.environ.get('STRATEGY_VALIDATOR_WORKFLOW_ENGINE') or 'DISABLED').strip().upper()
    workflow_paths = _existing((
        _repo_path(repo_root, 'strategy_validator', 'workflows'),
        _repo_path(repo_root, 'strategy_validator', 'control_plane', 'workflow_engine.py'),
    ))
    if config in {'PREFECT', 'TEMPORAL'} and workflow_paths:
        return StrategicHorizonCheck(
            capability='workflow_engine_integration',
            status='CONDITIONAL',
            recommended_action='PROCEED_ONLY_WITH_GOVERNED_EXCEPTION',
            evidence=workflow_paths + (f'STRATEGY_VALIDATOR_WORKFLOW_ENGINE={config}',),
            blockers=('IDEMPOTENT_EVENT_REPLAY_REVIEW_REQUIRED',),
            notes=('External orchestration must wrap application/control-plane commands without gaining decision authority.',),
        )
    return StrategicHorizonCheck(
        capability='workflow_engine_integration',
        status='DEFERRED',
        recommended_action='DEFER_UNTIL_PREREQUISITES_EXIST',
        evidence=workflow_paths,
        blockers=('NO_WORKFLOW_ENGINE_BOUNDARY_PRESENT',),
        notes=('Keep workflows as explicit application/control-plane calls until idempotent replay and event boundaries are proven.',),
    )


def build_strategic_horizon_readiness_report(*, repo_root: str | Path | None = None) -> StrategicHorizonReadinessReport:
    root = Path(repo_root).resolve() if repo_root is not None else Path.cwd().resolve()
    checks = (
        _check_frontend_operator_ui(root),
        _check_credentialed_provider_burnin(root),
        _check_multi_tenant_scaling(root),
        _check_oracle_advisory_expansion(root),
        _check_workflow_engine_integration(root),
    )
    if any(check.status == 'BLOCKED' for check in checks):
        status: StrategicHorizonStatus = 'BLOCKED'
        recommended_action: StrategicHorizonAction = 'DEFER_UNTIL_PREREQUISITES_EXIST'
    elif any(check.status == 'DEFERRED' for check in checks):
        status = 'DEFERRED'
        recommended_action = 'DEFER_UNTIL_PREREQUISITES_EXIST'
    elif any(check.status == 'CONDITIONAL' for check in checks):
        status = 'CONDITIONAL'
        recommended_action = 'PROCEED_ONLY_WITH_GOVERNED_EXCEPTION'
    else:
        status = 'READY'
        recommended_action = 'PROCEED_WITH_BOUNDED_IMPLEMENTATION'
    return StrategicHorizonReadinessReport(
        schema_version='strategic_horizon_readiness/v1',
        status=status,
        recommended_action=recommended_action,
        checks=checks,
    )


def get_strategic_horizon_readiness_payload(*, repo_root: str | Path | None = None) -> dict[str, Any]:
    return build_strategic_horizon_readiness_report(repo_root=repo_root).to_payload()


__all__ = [
    'StrategicHorizonCheck',
    'StrategicHorizonReadinessReport',
    'build_strategic_horizon_readiness_report',
    'get_strategic_horizon_readiness_payload',
]
