from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.release_publication_paths import resolve_release_publication_paths
from strategy_validator.application.strategic_horizon_readiness import build_strategic_horizon_readiness_report
from strategy_validator.core.path_guards import PathBoundaryError


def test_strategic_horizon_blocks_without_credentialed_burnin(tmp_path: Path) -> None:
    repo_root = tmp_path
    (repo_root / 'strategy_validator' / 'validator').mkdir(parents=True)
    (repo_root / 'strategy_validator' / 'validator' / 'oracle_stub.py').write_text('VALUE = 1\n', encoding='utf-8')
    (repo_root / 'docs' / 'artifacts').mkdir(parents=True)

    report = build_strategic_horizon_readiness_report(repo_root=repo_root)

    assert report.status == 'BLOCKED'
    payload = report.to_payload()
    checks = {item['capability']: item for item in payload['checks']}
    assert checks['credentialed_live_provider_burnin']['status'] == 'BLOCKED'
    assert 'NO_CREDENTIALED_LIVE_PROVIDER_BURNIN_ARTIFACT' in checks['credentialed_live_provider_burnin']['blockers']
    assert checks['frontend_operator_ui']['status'] == 'DEFERRED'
    assert checks['multi_tenant_scaling']['recommended_action'] == 'DO_NOT_BUILD'


def test_strategic_horizon_accepts_explicit_credentialed_burnin_marker(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path
    (repo_root / 'strategy_validator' / 'validator').mkdir(parents=True)
    (repo_root / 'strategy_validator' / 'validator' / 'oracle_stub.py').write_text('VALUE = 1\n', encoding='utf-8')
    marker = repo_root / 'docs' / 'artifacts' / 'CREDENTIALED_BURNIN.json'
    marker.parent.mkdir(parents=True)
    marker.write_text(
        json.dumps(
            {
                'credentialed_live_provider': True,
                'fallback_used': False,
                'freshness_validated': True,
            }
        ),
        encoding='utf-8',
    )
    monkeypatch.setenv('STRATEGY_VALIDATOR_CREDENTIALED_BURNIN_ARTIFACT', str(marker))

    report = build_strategic_horizon_readiness_report(repo_root=repo_root)

    checks = {check.capability: check for check in report.checks}
    assert checks['credentialed_live_provider_burnin'].status == 'READY'
    assert str(marker) in checks['credentialed_live_provider_burnin'].evidence


def test_release_publication_paths_require_explicit_root(tmp_path: Path) -> None:
    root = tmp_path / 'artifacts'
    root.mkdir()
    resolved = resolve_release_publication_paths(
        artifact_root=root,
        policy_path='policy.json',
        keyed_host_fingerprint_path='host.json',
        publication_path='out/release.json',
        burnin_artifact_paths=['burnin.json'],
    )

    assert resolved['policy_path'] == root / 'policy.json'
    assert resolved['publication_path'] == root / 'out' / 'release.json'
    assert resolved['burnin_artifact_paths'] == [root / 'burnin.json']


def test_release_publication_paths_reject_escape(tmp_path: Path) -> None:
    root = tmp_path / 'artifacts'
    root.mkdir()

    try:
        resolve_release_publication_paths(
            artifact_root=root,
            policy_path='../policy.json',
            keyed_host_fingerprint_path='host.json',
            publication_path='out/release.json',
        )
    except PathBoundaryError as exc:
        assert 'POLICY_PATH_OUTSIDE_ALLOWED_ROOT' in str(exc)
    else:  # pragma: no cover - explicit safety assertion
        raise AssertionError('expected path boundary rejection')
