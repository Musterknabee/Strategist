from pathlib import Path

from strategy_validator.application.research_os_operator_run_ops import (
    build_and_write_research_os_operator_run,
    build_ui_research_os_operator_run_latest_payload,
)


def test_operator_run_writes_manifest(tmp_path: Path) -> None:
    manifest, path = build_and_write_research_os_operator_run(
        run_id="unit-run",
        operator_id="unit-operator",
        artifact_root=tmp_path,
        overwrite=True,
        include_export_archive=False,
    )

    assert path.is_file()
    assert manifest.run_id == "unit-run"
    assert manifest.no_live_trading is True
    assert manifest.no_broker_orders is True
    assert manifest.no_order_controls is True
    assert len(manifest.steps) == 5
    assert manifest.manifest_sha256
    assert manifest.digests["operator_run_spine_sha256"]


def test_operator_run_read_plane_degrades_empty(tmp_path: Path) -> None:
    payload = build_ui_research_os_operator_run_latest_payload(artifact_root=tmp_path)

    assert payload["status"] == "NOT_PRESENT"
    assert "NO_RESEARCH_OS_OPERATOR_RUN_MANIFEST" in payload["degraded"]


def test_operator_run_read_plane_latest(tmp_path: Path) -> None:
    build_and_write_research_os_operator_run(
        run_id="unit-run-latest",
        operator_id="unit-operator",
        artifact_root=tmp_path,
        overwrite=True,
        include_export_archive=False,
    )

    payload = build_ui_research_os_operator_run_latest_payload(artifact_root=tmp_path)
    assert payload["status"] == "PRESENT"
    assert payload["latest"]["run_id"] == "unit-run-latest"
