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


def _write_evidence_manifest(path: Path, *, ok: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        '{"ok": %s, "files": [{"name": "deployment-summary.md", "sha256": "abc123"}]}'
        % ("true" if ok else "false"),
        encoding="utf-8",
    )


def test_main_writes_signoff_for_regular_evidence_manifest(signoff_mod, tmp_path, capsys) -> None:
    manifest = tmp_path / "evidence" / "deployment-evidence.json"
    output = tmp_path / "operator_signoff.json"
    _write_evidence_manifest(manifest)

    rc = signoff_mod.main(
        [
            "--evidence-manifest",
            str(manifest),
            "--output",
            str(output),
            "--repo-root",
            str(tmp_path),
            "--decision",
            "APPROVED_FOR_SINGLE_TENANT_BACKEND",
            "--manual-signoff",
            "Operator One",
        ]
    )

    assert rc == 0
    payload = output.read_text(encoding="utf-8")
    assert '"schema_version": "operator_deployment_signoff/v1"' in payload
    assert '"evidence_pack_ok": true' in payload
    captured = capsys.readouterr()
    assert "operator_deployment_signoff/v1" in captured.out


def test_main_rejects_symlinked_evidence_manifest(signoff_mod, tmp_path, capsys) -> None:
    manifest = tmp_path / "real" / "deployment-evidence.json"
    _write_evidence_manifest(manifest)
    link = tmp_path / "deployment-evidence.json"
    link.symlink_to(manifest)
    output = tmp_path / "operator_signoff.json"

    rc = signoff_mod.main(["--evidence-manifest", str(link), "--output", str(output), "--repo-root", str(tmp_path)])

    assert rc == 2
    assert not output.exists()
    captured = capsys.readouterr()
    assert "operator_deployment_signoff_path_error/v1" in captured.out
    assert "SIGNOFF_EVIDENCE_MANIFEST_IS_SYMLINK" in captured.out


def test_main_rejects_symlinked_provider_evidence_manifest(signoff_mod, tmp_path, capsys) -> None:
    evidence_dir = tmp_path / "evidence"
    manifest = evidence_dir / "deployment-evidence.json"
    _write_evidence_manifest(manifest)
    provider_real = tmp_path / "provider-real.json"
    provider_real.write_text('{"ok": true}', encoding="utf-8")
    (evidence_dir / "provider-evidence-manifest.json").symlink_to(provider_real)
    output = tmp_path / "operator_signoff.json"

    rc = signoff_mod.main(["--evidence-dir", str(evidence_dir), "--output", str(output), "--repo-root", str(tmp_path)])

    assert rc == 2
    assert not output.exists()
    captured = capsys.readouterr()
    assert "SIGNOFF_PROVIDER_EVIDENCE_MANIFEST_IS_SYMLINK" in captured.out


def test_main_rejects_symlinked_output_path(signoff_mod, tmp_path, capsys) -> None:
    manifest = tmp_path / "evidence" / "deployment-evidence.json"
    _write_evidence_manifest(manifest)
    real_output = tmp_path / "real-output.json"
    real_output.write_text("{}", encoding="utf-8")
    output_link = tmp_path / "operator_signoff.json"
    output_link.symlink_to(real_output)

    rc = signoff_mod.main(["--evidence-manifest", str(manifest), "--output", str(output_link), "--repo-root", str(tmp_path)])

    assert rc == 2
    captured = capsys.readouterr()
    assert "SIGNOFF_OUTPUT_IS_SYMLINK" in captured.out


def test_main_rejects_symlinked_repo_root(signoff_mod, tmp_path, capsys) -> None:
    manifest = tmp_path / "evidence" / "deployment-evidence.json"
    _write_evidence_manifest(manifest)
    real_repo = tmp_path / "real-repo"
    real_repo.mkdir()
    repo_link = tmp_path / "repo-link"
    repo_link.symlink_to(real_repo, target_is_directory=True)
    output = tmp_path / "operator_signoff.json"

    rc = signoff_mod.main(
        [
            "--evidence-manifest",
            str(manifest),
            "--output",
            str(output),
            "--repo-root",
            str(repo_link),
        ]
    )

    assert rc == 2
    assert not output.exists()
    captured = capsys.readouterr()
    assert "operator_deployment_signoff_path_error/v1" in captured.out
    assert "SIGNOFF_REPO_ROOT_IS_SYMLINK" in captured.out


def test_main_rejects_repo_root_under_symlinked_parent(signoff_mod, tmp_path, capsys) -> None:
    manifest = tmp_path / "evidence" / "deployment-evidence.json"
    _write_evidence_manifest(manifest)
    real_parent = tmp_path / "real-parent"
    repo = real_parent / "repo"
    repo.mkdir(parents=True)
    parent_link = tmp_path / "parent-link"
    parent_link.symlink_to(real_parent, target_is_directory=True)
    output = tmp_path / "operator_signoff.json"

    rc = signoff_mod.main(
        [
            "--evidence-manifest",
            str(manifest),
            "--output",
            str(output),
            "--repo-root",
            str(parent_link / "repo"),
        ]
    )

    assert rc == 2
    assert not output.exists()
    captured = capsys.readouterr()
    assert "operator_deployment_signoff_path_error/v1" in captured.out
    assert "SIGNOFF_REPO_ROOT_PARENT_IS_SYMLINK" in captured.out
