from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

from strategy_validator.control_plane._exports import _EXPORT_MAP
from strategy_validator.control_plane._exports_decision_integrity import (
    EXPORTS_DECISION_INTEGRITY,
)
from strategy_validator.control_plane._exports_operator_lifecycle import (
    EXPORTS_OPERATOR_LIFECYCLE,
)
from strategy_validator.control_plane._exports_pack_surfaces import EXPORTS_PACK_SURFACES
from strategy_validator.control_plane._exports_planes_and_sections import (
    EXPORTS_PLANES_AND_SECTIONS,
)
from strategy_validator.control_plane._exports_queue_governance import (
    EXPORTS_QUEUE_GOVERNANCE,
)

CONTROL_PLANE_INIT = Path('strategy_validator/control_plane/__init__.py')


def test_control_plane_root_package_avoids_eager_submodule_imports() -> None:
    tree = ast.parse(CONTROL_PLANE_INIT.read_text(encoding='utf-8'))
    eager_from_imports = [
        node.module
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module
        and node.module.startswith('strategy_validator.control_plane.')
    ]
    assert eager_from_imports == []



def test_control_plane_root_package_lazily_resolves_exports() -> None:
    sys.modules.pop('strategy_validator.control_plane', None)
    sys.modules.pop('strategy_validator.control_plane.operator_queue_service', None)
    module = importlib.import_module('strategy_validator.control_plane')
    assert 'strategy_validator.control_plane.operator_queue_service' not in sys.modules

    request_type = module.OracleGovernanceWorkQueueRequest
    assert request_type.__name__ == 'OracleGovernanceWorkQueueRequest'
    assert 'strategy_validator.control_plane.operator_queue_service' in sys.modules



def test_control_plane_export_map_is_composed_from_grouped_registries() -> None:
    expected = {
        **EXPORTS_PLANES_AND_SECTIONS,
        **EXPORTS_PACK_SURFACES,
        **EXPORTS_QUEUE_GOVERNANCE,
        **EXPORTS_DECISION_INTEGRITY,
        **EXPORTS_OPERATOR_LIFECYCLE,
    }
    assert _EXPORT_MAP == expected



def test_control_plane_grouped_exports_keep_key_surfaces_in_expected_buckets() -> None:
    assert EXPORTS_PLANES_AND_SECTIONS['OracleControlPlaneAssessment'] == (
        'strategy_validator.control_plane.control_plane'
    )
    assert EXPORTS_PACK_SURFACES['build_operator_pack_dashboard_request'] == (
        'strategy_validator.control_plane.operator_pack_dashboard'
    )
    assert EXPORTS_QUEUE_GOVERNANCE['OracleGovernanceWorkQueueRequest'] == (
        'strategy_validator.control_plane.operator_queue_service'
    )
    assert EXPORTS_DECISION_INTEGRITY['OracleOperatorDecisionJournal'] == (
        'strategy_validator.control_plane.operator_decision_journal'
    )
    assert EXPORTS_OPERATOR_LIFECYCLE['OracleOperatorReentryCompletionAttestation'] == (
        'strategy_validator.control_plane.operator_reentry_completion_attestation'
    )
