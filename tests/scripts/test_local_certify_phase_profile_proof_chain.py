from __future__ import annotations

import argparse
from pathlib import Path

import pytest

import scripts.local_certify as lc


def test_expected_step_names_include_frontend_preflight_for_discovery_profile() -> None:
    payload: dict[str, object] = {
        "certification_profile": lc.RESEARCH_PAPER_DISCOVERY_PROFILE,
        "frontend_included": False,
        "frontend_clean_workspace_included": False,
        "researcher_fixture_included": False,
        "collection_shards_included": False,
        "constitutional_shards_included": False,
        "pytest_execution_shards_included": False,
    }
    names = lc._expected_local_certify_step_names(payload)
    assert names[0] == "frontend_preflight"
    assert "compileall" in names


def test_temporary_certify_artifact_paths_restores_after_exception(tmp_path: Path) -> None:
    saved_r, saved_p, saved_c = lc.REPORT_PATH, lc.FRONTEND_PREFLIGHT_REPORT_PATH, lc.PYTHON_CORE_REPORT_PATH
    args = argparse.Namespace(
        local_certify_report_output=tmp_path / "local_certify_report.json",
        frontend_preflight_report_output=tmp_path / "frontend_preflight_report.json",
        python_core_report_output=tmp_path / "python_core_report.json",
    )
    with pytest.raises(RuntimeError):
        with lc._temporary_certify_artifact_paths(args):
            assert lc.REPORT_PATH == args.local_certify_report_output.resolve()
            assert lc.FRONTEND_PREFLIGHT_REPORT_PATH == args.frontend_preflight_report_output.resolve()
            assert lc.PYTHON_CORE_REPORT_PATH == args.python_core_report_output.resolve()
            raise RuntimeError("expected")
    assert lc.REPORT_PATH == saved_r
    assert lc.FRONTEND_PREFLIGHT_REPORT_PATH == saved_p
    assert lc.PYTHON_CORE_REPORT_PATH == saved_c


def test_phase_run_report_surfaces_local_certify_verification_blocker_codes() -> None:
    report = lc.build_research_paper_discovery_phase_run_report(
        local_certify_payload={
            "status": "PASS",
            "failed_step": None,
            "certification_profile": lc.RESEARCH_PAPER_DISCOVERY_PROFILE,
            "next_diagnostic": None,
        },
        local_report_verification={
            "status": "FAIL",
            "blockers": ["LOCAL_CERTIFY_REPORT_PAYLOAD_DIGEST_MISMATCH:old:new"],
        },
        phase_profile_plan_report={"status": "PASS"},
        phase_profile_plan_verification={"status": "PASS"},
        phase_closure_report={
            "status": "PASS",
            "no_live_authority_assertion": True,
            "paper_live_firewall_assertion": True,
        },
        phase_evidence_bundle={"status": "PASS"},
        phase_profile_blockers=[],
    )
    joined = "\n".join(str(b) for b in report["blockers"])
    assert "RESEARCH_PAPER_DISCOVERY_PHASE_RUN_LOCAL_REPORT_VERIFICATION_NOT_PASSING:FAIL" in joined
    assert "RESEARCH_PAPER_DISCOVERY_PHASE_RUN_LOCAL_REPORT_VERIFICATION_BLOCKER:LOCAL_CERTIFY_REPORT_PAYLOAD_DIGEST_MISMATCH:old:new" in joined


def test_phase_run_report_no_closure_false_positive_when_nested_pass(tmp_path: Path) -> None:
    report = lc.build_research_paper_discovery_phase_run_report(
        local_certify_payload={
            "status": "PASS",
            "failed_step": None,
            "certification_profile": lc.RESEARCH_PAPER_DISCOVERY_PROFILE,
            "next_diagnostic": None,
        },
        local_report_verification={"status": "PASS", "blockers": []},
        phase_profile_plan_report={"status": "PASS"},
        phase_profile_plan_verification={"status": "PASS"},
        phase_closure_report={
            "status": "PASS",
            "no_live_authority_assertion": True,
            "paper_live_firewall_assertion": True,
        },
        phase_evidence_bundle={"status": "PASS"},
        phase_profile_blockers=[],
        output_path=tmp_path / "phase_run.json",
    )
    assert report["status"] == "PASS"
    assert not any("RESEARCH_PAPER_DISCOVERY_PHASE_RUN_CLOSURE_NOT_PASSING" in str(b) for b in report["blockers"])
    assert not any("RESEARCH_PAPER_DISCOVERY_PHASE_RUN_EVIDENCE_BUNDLE_NOT_PASSING" in str(b) for b in report["blockers"])