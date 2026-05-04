from __future__ import annotations

import json
from pathlib import Path

from scripts.ui_facade_contract_snapshot import main

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "docs" / "api" / "ui-public-facade.snapshot.json"


def _json_stdout(raw: str) -> dict[str, object]:
    assert raw
    return json.loads(raw)


def test_ui_facade_snapshot_check_rejects_symlinked_snapshot_input(tmp_path: Path, capsys) -> None:
    linked_snapshot = tmp_path / "linked-ui-snapshot.json"
    linked_snapshot.symlink_to(SNAPSHOT)

    rc = main(["--check", "--output", str(linked_snapshot)])

    assert rc == 1
    payload = _json_stdout(capsys.readouterr().out)
    assert payload["schema_version"] == "ui_facade_contract_snapshot_path_error/v1"
    assert payload["code"] == "UI_FACADE_SNAPSHOT_IS_SYMLINK"


def test_ui_facade_snapshot_write_rejects_symlinked_output_path(tmp_path: Path, capsys) -> None:
    real_output = tmp_path / "real-ui-snapshot.json"
    real_output.write_text("do not overwrite\n", encoding="utf-8")
    linked_output = tmp_path / "ui-snapshot.json"
    linked_output.symlink_to(real_output)

    rc = main(["--output", str(linked_output)])

    assert rc == 1
    payload = _json_stdout(capsys.readouterr().out)
    assert payload["schema_version"] == "ui_facade_contract_snapshot_path_error/v1"
    assert payload["code"] == "UI_FACADE_SNAPSHOT_OUTPUT_IS_SYMLINK"
    assert real_output.read_text(encoding="utf-8") == "do not overwrite\n"


def test_ui_facade_snapshot_write_rejects_output_under_symlinked_parent(tmp_path: Path, capsys) -> None:
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)

    rc = main(["--output", str(linked_parent / "ui-snapshot.json")])

    assert rc == 1
    payload = _json_stdout(capsys.readouterr().out)
    assert payload["schema_version"] == "ui_facade_contract_snapshot_path_error/v1"
    assert payload["code"] == "UI_FACADE_SNAPSHOT_OUTPUT_PARENT_IS_SYMLINK"
    assert not (real_parent / "ui-snapshot.json").exists()


def test_ui_facade_snapshot_rejects_symlinked_repo_root(tmp_path: Path, capsys) -> None:
    linked_repo = tmp_path / "linked-repo"
    linked_repo.symlink_to(ROOT, target_is_directory=True)
    output = tmp_path / "snapshot.json"

    rc = main(["--repo-root", str(linked_repo), "--output", str(output)])

    assert rc == 1
    payload = _json_stdout(capsys.readouterr().out)
    assert payload["schema_version"] == "ui_facade_contract_snapshot_path_error/v1"
    assert payload["code"] == "UI_FACADE_REPO_ROOT_IS_SYMLINK"
    assert not output.exists()


def test_ui_facade_snapshot_rejects_repo_root_under_symlinked_parent(tmp_path: Path, capsys) -> None:
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)
    unsafe_repo_root = linked_parent / "repo"
    output = tmp_path / "snapshot.json"

    rc = main(["--repo-root", str(unsafe_repo_root), "--output", str(output)])

    assert rc == 1
    payload = _json_stdout(capsys.readouterr().out)
    assert payload["schema_version"] == "ui_facade_contract_snapshot_path_error/v1"
    assert payload["code"] == "UI_FACADE_REPO_ROOT_PARENT_IS_SYMLINK"
    assert not output.exists()
