from __future__ import annotations

import json
from pathlib import Path

from scripts.openapi_contract_snapshot import main

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "docs" / "architecture" / "openapi.snapshot.json"


def _json_stdout(raw: str) -> dict[str, object]:
    assert raw
    return json.loads(raw)


def test_openapi_snapshot_check_rejects_symlinked_snapshot_input(tmp_path: Path, capsys) -> None:
    linked_snapshot = tmp_path / "linked-openapi.snapshot.json"
    linked_snapshot.symlink_to(SNAPSHOT)

    rc = main(["--check", "--output", str(linked_snapshot)])

    assert rc == 1
    payload = _json_stdout(capsys.readouterr().out)
    assert payload["schema_version"] == "openapi_contract_snapshot_path_error/v1"
    assert payload["code"] == "OPENAPI_SNAPSHOT_IS_SYMLINK"


def test_openapi_snapshot_write_rejects_symlinked_output_path(tmp_path: Path, capsys) -> None:
    real_output = tmp_path / "real-openapi.snapshot.json"
    real_output.write_text("do not overwrite\n", encoding="utf-8")
    linked_output = tmp_path / "openapi.snapshot.json"
    linked_output.symlink_to(real_output)

    rc = main(["--output", str(linked_output)])

    assert rc == 1
    payload = _json_stdout(capsys.readouterr().out)
    assert payload["schema_version"] == "openapi_contract_snapshot_path_error/v1"
    assert payload["code"] == "OPENAPI_SNAPSHOT_OUTPUT_IS_SYMLINK"
    assert real_output.read_text(encoding="utf-8") == "do not overwrite\n"


def test_openapi_snapshot_write_rejects_output_under_symlinked_parent(tmp_path: Path, capsys) -> None:
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)

    rc = main(["--output", str(linked_parent / "openapi.snapshot.json")])

    assert rc == 1
    payload = _json_stdout(capsys.readouterr().out)
    assert payload["schema_version"] == "openapi_contract_snapshot_path_error/v1"
    assert payload["code"] == "OPENAPI_SNAPSHOT_OUTPUT_PARENT_IS_SYMLINK"
    assert not (real_parent / "openapi.snapshot.json").exists()
