from __future__ import annotations

import ast
from pathlib import Path

from tests.constitutional.test_boundaries import PKG_ROOT


def _top_level_class_names(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    return [node.name for node in tree.body if isinstance(node, ast.ClassDef)]


def test_bounded_contract_modules_exist() -> None:
    contracts_root = PKG_ROOT / 'contracts'
    for filename in (
        'governance.py',
        'operator_packs.py',
        'briefing.py',
        'event_views.py',
        'research.py',
        'strategic.py',
        'doctrine.py',
        'memory.py',
        'analytics.py',
        'transitions.py',
    ):
        assert (contracts_root / filename).exists(), f'missing bounded contract module: {filename}'


def test_oracle_contract_module_does_not_gain_new_pack_classes() -> None:
    oracle_path = PKG_ROOT / 'contracts' / 'oracle.py'
    class_names = _top_level_class_names(oracle_path)
    pack_class_names = [name for name in class_names if name.startswith(('OracleStatusPack', 'OracleIncidentPack', 'OracleBriefingPack'))]
    assert pack_class_names, 'expected compatibility classes to remain in contracts.oracle during migration'
    assert len(pack_class_names) <= 5, 'pack contracts are growing in contracts.oracle instead of bounded modules'


def test_oracle_contract_module_does_not_gain_new_research_or_strategic_clusters() -> None:
    oracle_path = PKG_ROOT / 'contracts' / 'oracle.py'
    class_names = _top_level_class_names(oracle_path)
    research_class_names = [name for name in class_names if name.startswith(('OracleOpportunityQueue', 'OracleResearch', 'OracleThesisGraph', 'OracleThesisMemory'))]
    strategic_class_names = [name for name in class_names if name.startswith(('OracleStrategic', 'OracleScenario', 'OracleStrategyCohort', 'OracleContradictionResolution'))]
    assert research_class_names and strategic_class_names, 'expected compatibility classes to remain in contracts.oracle during migration'
    assert len(research_class_names) <= 11, 'research contracts are growing in contracts.oracle instead of bounded modules'
    assert len(strategic_class_names) <= 31, 'strategic contracts are growing in contracts.oracle instead of bounded modules'


def test_oracle_contract_module_does_not_gain_new_analytics_or_transition_clusters() -> None:
    oracle_path = PKG_ROOT / 'contracts' / 'oracle.py'
    class_names = _top_level_class_names(oracle_path)
    analytics_class_names = [name for name in class_names if name.startswith(('StrategyHealthPosterior', 'OracleResearchPriority', 'OracleThesisGraph', 'OracleStrategicTension'))]
    transition_class_names = [name for name in class_names if name.startswith(('OracleRegimeTransition', 'OracleContradictionResolution', 'OracleStrategicIntervention'))]
    assert analytics_class_names and transition_class_names, 'expected compatibility classes to remain in contracts.oracle during migration'
    assert len(analytics_class_names) <= 8, 'analytics contracts are growing in contracts.oracle instead of bounded modules'
    assert len(transition_class_names) <= 6, 'transition contracts are growing in contracts.oracle instead of bounded modules'
