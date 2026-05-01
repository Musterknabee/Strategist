from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

GENERIC_HUMAN_CONFIRM_WARNING = (
    "Human must confirm APPROVED_FOR_SINGLE_TENANT_BACKEND after reviewing artifacts/deployment/release-evidence/."
)
EVIDENCE_PACK_FAILED_WARNING = "Evidence pack reported ok=false"


def _load_signoff_module():
    path = REPO_ROOT / "scripts" / "generate_operator_deployment_signoff.py"
    spec = importlib.util.spec_from_file_location("_generate_operator_deployment_signoff", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def signoff_mod():
    return _load_signoff_module()


def test_pending_signoff_includes_generic_human_confirm_warning(signoff_mod) -> None:
    w = signoff_mod.compute_known_warnings(
        operator_decision="APPROVED_FOR_SINGLE_TENANT_BACKEND",
        manual_signoff="",
        evidence_pack_ok=True,
    )
    assert GENERIC_HUMAN_CONFIRM_WARNING in w
    assert EVIDENCE_PACK_FAILED_WARNING not in w


def test_approved_named_signoff_omits_generic_warning(signoff_mod) -> None:
    w = signoff_mod.compute_known_warnings(
        operator_decision="APPROVED_FOR_SINGLE_TENANT_BACKEND",
        manual_signoff="Jean-Pierre Kemper (single-tenant operator)",
        evidence_pack_ok=True,
    )
    assert w == []


def test_placeholder_manual_signoff_treated_as_pending(signoff_mod) -> None:
    w = signoff_mod.compute_known_warnings(
        operator_decision="APPROVED_FOR_SINGLE_TENANT_BACKEND",
        manual_signoff=signoff_mod.PENDING_MANUAL_SIGNOFF,
        evidence_pack_ok=True,
    )
    assert GENERIC_HUMAN_CONFIRM_WARNING in w


def test_approved_with_failed_evidence_includes_evidence_warning_not_generic(signoff_mod) -> None:
    w = signoff_mod.compute_known_warnings(
        operator_decision="APPROVED_FOR_SINGLE_TENANT_BACKEND",
        manual_signoff="Some Operator",
        evidence_pack_ok=False,
    )
    assert EVIDENCE_PACK_FAILED_WARNING in w
    assert GENERIC_HUMAN_CONFIRM_WARNING not in w
