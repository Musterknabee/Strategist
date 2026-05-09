from __future__ import annotations

import ast
import importlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "strategy_validator" / "contracts"

PHASE_MODULES = (
    "paper_execution_core",
    "paper_execution_evidence_bundle",
    "paper_execution_retention",
    "paper_execution_retention_custody_chain",
    "paper_execution_retention_custody_renewal",
    "paper_execution_retention_custody_archive",
    "paper_execution_cockpit_payload",
)

CUSTODY_SUBPHASE_MODULES = (
    "paper_execution_retention_custody_register",
    "paper_execution_retention_custody_audit",
    "paper_execution_retention_custody_review",
    "paper_execution_retention_custody_renewal_cycle",
    "paper_execution_retention_custody_renewal_notice",
    "paper_execution_retention_custody_renewal_closeout",
    "paper_execution_retention_custody_archive_core",
    "paper_execution_retention_custody_archive_return",
    "paper_execution_retention_custody_archive_inventory",
    "paper_execution_retention_custody_archive_certification",
)

EVIDENCE_BUNDLE_SUBPHASE_MODULES = (
    "paper_execution_evidence_bundle_core",
    "paper_execution_evidence_bundle_verification",
    "paper_execution_evidence_bundle_rotation",
    "paper_execution_evidence_bundle_attestation",
    "paper_execution_evidence_bundle_closure",
    "paper_execution_evidence_bundle_export",
)

RETENTION_SUBPHASE_MODULES = (
    "paper_execution_retention_receipt",
    "paper_execution_retention_signoff",
    "paper_execution_retention_handoff",
)

COCKPIT_PAYLOAD_SUBPHASE_MODULES = (
    "paper_execution_cockpit_summary",
    "paper_execution_cockpit_payload_view",
)


def _class_names(path: Path) -> list[str]:
    tree = ast.parse(path.read_text())
    return [node.name for node in tree.body if isinstance(node, ast.ClassDef)]


def test_paper_execution_public_module_is_legacy_facade() -> None:
    facade_path = CONTRACTS / "paper_execution.py"
    tree = ast.parse(facade_path.read_text())

    assert len(facade_path.read_text().splitlines()) <= 80
    assert not [node.name for node in tree.body if isinstance(node, ast.ClassDef)]

    facade = importlib.import_module("strategy_validator.contracts.paper_execution")
    phase_exports: list[str] = []
    for module_name in PHASE_MODULES:
        module = importlib.import_module(f"strategy_validator.contracts.{module_name}")
        phase_exports.extend(module.__all__)

    assert list(facade.__all__) == phase_exports


def test_paper_execution_contracts_are_owned_by_focused_phase_modules() -> None:
    expected_classes = {
        "paper_execution_core": {
            "PaperExecutionIntentPreview",
            "PaperExecutionTimelineSummary",
        },
        "paper_execution_evidence_bundle_core": {
            "PaperExecutionEvidenceBundleArtifact",
            "PaperExecutionEvidenceBundleView",
        },
        "paper_execution_evidence_bundle_verification": {
            "PaperExecutionEvidenceBundleVerificationArtifact",
            "PaperExecutionEvidenceBundleDriftView",
        },
        "paper_execution_evidence_bundle_rotation": {
            "PaperExecutionEvidenceBundleRotationArtifact",
            "PaperExecutionEvidenceBundleRotationExecutionView",
        },
        "paper_execution_evidence_bundle_attestation": {
            "PaperExecutionEvidenceBundleAttestationArtifact",
            "PaperExecutionEvidenceBundleAttestationVerificationView",
        },
        "paper_execution_evidence_bundle_closure": {
            "PaperExecutionEvidenceBundleClosureArtifact",
            "PaperExecutionEvidenceBundleClosureVerificationView",
        },
        "paper_execution_evidence_bundle_export": {
            "PaperExecutionEvidenceBundleExportManifestArtifact",
            "PaperExecutionEvidenceBundleExportVerificationView",
        },
        "paper_execution_retention_receipt": {
            "PaperExecutionEvidenceBundleRetentionReceiptArtifact",
            "PaperExecutionEvidenceBundleRetentionVerificationView",
        },
        "paper_execution_retention_signoff": {
            "PaperExecutionEvidenceBundleRetentionSignoffArtifact",
            "PaperExecutionEvidenceBundleRetentionSignoffVerificationView",
        },
        "paper_execution_retention_handoff": {
            "PaperExecutionEvidenceBundleRetentionHandoffArtifact",
            "PaperExecutionEvidenceBundleRetentionHandoffAcceptanceVerificationView",
        },
        "paper_execution_retention_custody_register": {
            "PaperExecutionEvidenceBundleRetentionCustodyRegisterArtifact",
            "PaperExecutionEvidenceBundleRetentionCustodySealVerificationView",
        },
        "paper_execution_retention_custody_audit": {
            "PaperExecutionEvidenceBundleRetentionCustodyAuditArtifact",
            "PaperExecutionEvidenceBundleRetentionCustodyContinuityVerificationView",
        },
        "paper_execution_retention_custody_review": {
            "PaperExecutionEvidenceBundleRetentionCustodyReviewArtifact",
            "PaperExecutionEvidenceBundleRetentionCustodyReviewVerificationView",
        },
        "paper_execution_retention_custody_renewal_cycle": {
            "PaperExecutionEvidenceBundleRetentionCustodyRenewalArtifact",
            "PaperExecutionEvidenceBundleRetentionCustodyScheduleVerificationView",
        },
        "paper_execution_retention_custody_renewal_notice": {
            "PaperExecutionEvidenceBundleRetentionCustodyNoticeArtifact",
            "PaperExecutionEvidenceBundleRetentionCustodyAcknowledgmentVerificationView",
        },
        "paper_execution_retention_custody_renewal_closeout": {
            "PaperExecutionEvidenceBundleRetentionCustodyCompletionArtifact",
            "PaperExecutionEvidenceBundleRetentionCustodyCloseoutVerificationView",
        },
        "paper_execution_retention_custody_archive_core": {
            "PaperExecutionEvidenceBundleRetentionCustodyArchiveArtifact",
            "PaperExecutionEvidenceBundleRetentionCustodyRetrievalVerificationView",
        },
        "paper_execution_retention_custody_archive_return": {
            "PaperExecutionEvidenceBundleRetentionCustodyReturnArtifact",
            "PaperExecutionEvidenceBundleRetentionCustodyRedepositVerificationView",
        },
        "paper_execution_retention_custody_archive_inventory": {
            "PaperExecutionEvidenceBundleRetentionCustodyInventoryArtifact",
            "PaperExecutionEvidenceBundleRetentionCustodyReconciliationVerificationView",
        },
        "paper_execution_retention_custody_archive_certification": {
            "PaperExecutionEvidenceBundleRetentionCustodyCertificationArtifact",
            "PaperExecutionEvidenceBundleRetentionCustodyAttestationVerificationView",
        },
        "paper_execution_cockpit_summary": {
            "PaperExecutionSummary",
        },
        "paper_execution_cockpit_payload_view": {
            "PaperExecutionCockpitPayload",
        },
    }

    for module_name, class_names in expected_classes.items():
        owned = set(_class_names(CONTRACTS / f"{module_name}.py"))
        assert class_names <= owned


def test_evidence_bundle_contract_facade_is_subphase_only() -> None:
    facade_path = CONTRACTS / "paper_execution_evidence_bundle.py"

    assert len(facade_path.read_text().splitlines()) <= 40
    assert _class_names(facade_path) == []


def test_evidence_bundle_facade_exports_match_subphases() -> None:
    facade = importlib.import_module("strategy_validator.contracts.paper_execution_evidence_bundle")
    expected_exports: list[str] = []
    for subphase_name in EVIDENCE_BUNDLE_SUBPHASE_MODULES:
        subphase = importlib.import_module(f"strategy_validator.contracts.{subphase_name}")
        expected_exports.extend(subphase.__all__)

    assert list(facade.__all__) == expected_exports



def test_retention_contract_facade_is_subphase_only() -> None:
    facade_path = CONTRACTS / "paper_execution_retention.py"

    assert len(facade_path.read_text().splitlines()) <= 40
    assert _class_names(facade_path) == []


def test_retention_facade_exports_match_subphases() -> None:
    facade = importlib.import_module("strategy_validator.contracts.paper_execution_retention")
    expected_exports: list[str] = []
    for subphase_name in RETENTION_SUBPHASE_MODULES:
        subphase = importlib.import_module(f"strategy_validator.contracts.{subphase_name}")
        expected_exports.extend(subphase.__all__)

    assert list(facade.__all__) == expected_exports

def test_cockpit_payload_contract_facade_is_subphase_only() -> None:
    facade_path = CONTRACTS / "paper_execution_cockpit_payload.py"

    assert len(facade_path.read_text().splitlines()) <= 40
    assert _class_names(facade_path) == []


def test_cockpit_payload_facade_exports_match_subphases() -> None:
    facade = importlib.import_module("strategy_validator.contracts.paper_execution_cockpit_payload")
    expected_exports: list[str] = []
    for subphase_name in COCKPIT_PAYLOAD_SUBPHASE_MODULES:
        subphase = importlib.import_module(f"strategy_validator.contracts.{subphase_name}")
        expected_exports.extend(subphase.__all__)

    assert list(facade.__all__) == expected_exports

def test_retention_custody_contract_facades_are_subphase_only() -> None:
    facade_names = (
        "paper_execution_retention_custody_chain",
        "paper_execution_retention_custody_renewal",
        "paper_execution_retention_custody_archive",
    )

    for module_name in facade_names:
        facade_path = CONTRACTS / f"{module_name}.py"
        assert len(facade_path.read_text().splitlines()) <= 40
        assert _class_names(facade_path) == []


def test_retention_custody_facade_exports_match_subphases() -> None:
    expected_groups = {
        "paper_execution_retention_custody_chain": (
            "paper_execution_retention_custody_register",
            "paper_execution_retention_custody_audit",
            "paper_execution_retention_custody_review",
        ),
        "paper_execution_retention_custody_renewal": (
            "paper_execution_retention_custody_renewal_cycle",
            "paper_execution_retention_custody_renewal_notice",
            "paper_execution_retention_custody_renewal_closeout",
        ),
        "paper_execution_retention_custody_archive": (
            "paper_execution_retention_custody_archive_core",
            "paper_execution_retention_custody_archive_return",
            "paper_execution_retention_custody_archive_inventory",
            "paper_execution_retention_custody_archive_certification",
        ),
    }

    for facade_name, subphase_names in expected_groups.items():
        facade = importlib.import_module(f"strategy_validator.contracts.{facade_name}")
        expected_exports: list[str] = []
        for subphase_name in subphase_names:
            subphase = importlib.import_module(f"strategy_validator.contracts.{subphase_name}")
            expected_exports.extend(subphase.__all__)

        assert list(facade.__all__) == expected_exports


def test_legacy_paper_execution_import_path_still_exposes_key_contracts() -> None:
    from strategy_validator.contracts.paper_execution import (
        PaperExecutionCockpitPayload,
        PaperExecutionEvidenceBundleRetentionCustodyAttestationVerificationView,
        PaperExecutionEvidenceBundleRetentionCustodyRegisterView,
        PaperExecutionEvidenceBundleView,
        PaperExecutionIntentPreview,
        PaperExecutionSummary,
        PaperExecutionTimelineSummary,
    )

    assert PaperExecutionIntentPreview.model_fields["symbol"].is_required()
    assert PaperExecutionTimelineSummary.model_fields["sequence_status"].default == "EMPTY"
    assert "timeline_sequence_status" in PaperExecutionEvidenceBundleView.model_fields
    assert "custody_register_id" in PaperExecutionEvidenceBundleRetentionCustodyRegisterView.model_fields
    assert "verification_status" in PaperExecutionEvidenceBundleRetentionCustodyAttestationVerificationView.model_fields
    assert "latest_order_status" in PaperExecutionSummary.model_fields
    assert PaperExecutionCockpitPayload.model_fields["schema_version"].default == "ui_paper_execution_cockpit/v1"
