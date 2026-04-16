from pathlib import Path


def test_governance_workflows_is_compatibility_shim() -> None:
    text = Path("strategy_validator/control_plane/workflows.py").read_text(encoding="utf-8")
    assert "Compatibility shim for governance workflow materialization" in text
    assert "from strategy_validator.control_plane.governance_review_dispatch import (" in text
    assert "from strategy_validator.control_plane.governance_claim_workflows import (" in text
    assert "def materialize_governance_claim_envelope(" not in text
    assert "def materialize_governance_dispatch_envelope(" not in text


def test_governance_workflow_implementations_live_in_bounded_modules() -> None:
    review_text = Path("strategy_validator/control_plane/governance_review_dispatch.py").read_text(encoding="utf-8")
    claim_text = Path("strategy_validator/control_plane/governance_claim_workflows.py").read_text(encoding="utf-8")
    assert "def materialize_governance_review_envelope(" in review_text
    assert "def materialize_governance_dispatch_envelope(" in review_text
    assert "def build_governance_review_sort_key(" in review_text
    assert "def materialize_governance_claim_envelope(" in claim_text
