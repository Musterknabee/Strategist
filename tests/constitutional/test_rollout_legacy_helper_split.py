from __future__ import annotations

from tests.constitutional.test_boundaries import PKG_ROOT


def test_rollout_ops_is_dispatcher_without_legacy_helper_wall() -> None:
    rollout_ops = (PKG_ROOT / 'cli' / 'rollout_ops.py').read_text(encoding='utf-8')
    assert 'def _legacy_banner(' not in rollout_ops
    assert 'def _run_verify_manifest(' not in rollout_ops
    assert 'def _run_verify_and_append_manifest(' not in rollout_ops
    assert 'def _legacy_horizon_proxy(' not in rollout_ops


def test_legacy_helper_module_owns_shared_rollout_helper_wall() -> None:
    helper_module = (PKG_ROOT / 'cli' / 'oracle_rollout_legacy_helpers.py').read_text(encoding='utf-8')
    assert 'def legacy_banner(' in helper_module
    assert 'def run_verify_manifest(' in helper_module
    assert 'def run_verify_and_append_manifest(' in helper_module
    assert 'def legacy_horizon_proxy(' in helper_module
    assert 'def run_legacy_horizon_report(' in helper_module
