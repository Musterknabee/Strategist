from __future__ import annotations

from pathlib import Path

import pytest

from scripts.local_certify import planned_steps

ROOT = Path(__file__).resolve().parents[2]
CI = ROOT / ".github" / "workflows" / "ci.yml"


def _frontend_step(name: str, *, exit_code: int = 0, timed_out: bool = False) -> dict[str, object]:
    return {
        "name": name,
        "command": ["npm", "run", name],
        "cwd": str(ROOT / "ui" / "strategist-web"),
        "timeout_seconds": 300,
        "started_at": "2026-01-01T00:00:00+00:00",
        "finished_at": "2026-01-01T00:00:01+00:00",
        "duration_seconds": 1.0,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "stdout_tail": "",
        "stderr_tail": "",
        "artifact_paths": [],
    }


def _frontend_report_payload(report: Path, *, steps: list[dict[str, object]] | None = None, **overrides: object) -> dict[str, object]:
    from scripts.local_certify import _file_sha256, _frontend_source_tree_digest

    payload: dict[str, object] = {
        "schema_version": "frontend_certify/v1",
        "status": "PASS",
        "failed_step": None,
        "started_at": "2026-01-01T00:00:00+00:00",
        "finished_at": "2026-01-01T00:01:00+00:00",
        "report_path": str(report),
        "node_version": "v-test",
        "default_step_timeout_seconds": 900,
        "frontend_source_tree_digest": _frontend_source_tree_digest(),
        "package_json_sha256": _file_sha256(ROOT / "ui" / "strategist-web" / "package.json"),
        "package_lock_sha256": _file_sha256(ROOT / "ui" / "strategist-web" / "package-lock.json"),
        "steps": steps
        if steps is not None
        else [
            _frontend_step(name)
            for name in (
                "contract_check",
                "lint",
                "typecheck",
                "test",
                "acceptance",
                "build",
                "audit",
            )
        ],
    }
    payload.update(overrides)
    return payload


def _plan_commands() -> dict[str, str]:
    return {name: " ".join(command) for name, command, _cwd in planned_steps(include_frontend=True)}


def test_local_certify_plan_covers_ci_validate_canonical_gates() -> None:
    plan = _plan_commands()

    assert "compileall" in plan
    assert "source_health" in plan
    assert "repository_truth" in plan
    assert "migration_truth" in plan
    assert "public_surface_dashboard" in plan
    assert "package_repo_check" in plan
    assert "pytest" in plan
    assert "frontend_npm_ci" in plan
    assert "frontend_certify" in plan

    assert "compileall" in plan["compileall"]
    assert "scripts/source_health.py" in plan["source_health"]
    assert "scripts/repository_truth_check.py" in plan["repository_truth"]
    assert "scripts/migration_truth_check.py" in plan["migration_truth"]
    assert "scripts/public_surface_dashboard.py" in plan["public_surface_dashboard"]
    assert "--check-ratchet" in plan["public_surface_dashboard"]
    assert "scripts/package_repo.py" in plan["package_repo_check"]
    assert "--report-output" in plan["package_repo_check"]
    assert "pytest" in plan["pytest"]
    assert plan["frontend_npm_ci"].endswith(" ci")
    assert plan["frontend_certify"].endswith(" run certify")


def test_ci_validate_job_covers_local_certify_canonical_gates() -> None:
    ci_text = CI.read_text(encoding="utf-8")

    for required in (
        "python -m compileall -q strategy_validator tests scripts",
        "python scripts/source_health.py",
        "python scripts/repository_truth_check.py",
        "python scripts/migration_truth_check.py",
        "python scripts/public_surface_dashboard.py --check-doc docs/audits/public_surface_dashboard.md --check-ratchet docs/governance/public_surface_budget_ratchet.json",
        "python scripts/package_repo.py --check --json --report-output artifacts/package_repo/latest/package_repo_check.json",
        "npm ci",
        "npm run certify",
        "python -m pytest -q",
    ):
        assert required in ci_text

from scripts.certification_stability import (
    _aggregate_collection_shard_reports,
    _aggregate_constitutional_shard_reports,
    _collection_shard_plan,
    _collection_source_manifest_digest,
    _pytest_execution_shard_plan,
    _pytest_execution_source_manifest_digest,
    _aggregate_pytest_execution_shard_reports,
    _verify_pytest_execution_summary_report,
    _constitutional_shard_plan,
    _constitutional_source_manifest_digest,
    _pytest_shard_plan,
    _summary_payload_digest,
    _verify_collection_summary_report,
    _verify_constitutional_summary_report,
    _build_shard_suite_manifest,
    _verify_shard_suite_manifest,
    main as certification_stability_main,
)


def test_certification_stability_all_uses_bounded_constitutional_shards() -> None:
    plan = _constitutional_shard_plan("python", shard_count=8)

    assert plan.name == "constitutional_shards"
    assert len(plan.steps) == 8
    commands = [" ".join(command) for _name, command, _cwd in plan.steps]
    assert all("tests/constitutional/test_" in command for command in commands)
    assert all("--tb=short" in command for command in commands)


def test_certification_stability_pytest_shards_do_not_duplicate_constitutional_monolith() -> None:
    plan = _pytest_shard_plan("python")

    commands = [" ".join(command) for _name, command, _cwd in plan.steps]
    assert all("tests/constitutional" not in command for command in commands)
    assert any("tests/api" in command for command in commands)
    assert any("tests/application" in command for command in commands)


def test_certification_stability_shard_suite_manifest_records_collection_runbook(tmp_path) -> None:
    payload = _build_shard_suite_manifest(
        suites=["collection"],
        py="python",
        output_root=tmp_path / "certification_stability",
        collection_shard_count=3,
        constitutional_shard_count=4,
        pytest_shard_count=5,
        timeout_seconds=120,
        heartbeat_seconds=7,
    )

    assert payload["schema_version"] == "certification_stability_shard_suite_manifest/v1"
    suites = payload["suites"]
    assert len(suites) == 1
    collection = suites[0]
    assert collection["suite"] == "collection"
    assert collection["shard_count"] == 3
    assert len(collection["shard_reports"]) == 3
    first_command = " ".join(collection["shard_reports"][0]["command"])
    assert "--phase collect-shards" in first_command
    assert "--collection-shard-index 1" in first_command
    assert "--timeout-seconds 120" in first_command
    aggregate_command = " ".join(collection["aggregate"]["command"])
    assert "--aggregate-collection-shard-reports" in aggregate_command
    assert "shard_1.json" in aggregate_command
    assert "shard_3.json" in aggregate_command
    verify_command = " ".join(collection["verify"]["command"])
    assert "--verify-collection-summary" in verify_command
    local_certify_command = " ".join(collection["local_certify"]["command"])
    assert "--include-collection-shards" in local_certify_command
    assert collection["source_tree"]["manifest_sha256"]


def test_certification_stability_cli_writes_all_shard_suite_manifest(tmp_path, capsys) -> None:
    output = tmp_path / "shard_suite_manifest.json"
    code = certification_stability_main([
        "--write-shard-suite-manifest",
        "all",
        "--collection-shard-count",
        "2",
        "--constitutional-shard-count",
        "3",
        "--pytest-shard-count",
        "4",
        "--timeout-seconds",
        "111",
        "--heartbeat-seconds",
        "5",
        "--shard-suite-output-root",
        str(tmp_path / "certification_stability"),
        "--output",
        str(output),
        "--json",
    ])

    assert code == 0
    payload = __import__("json").loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "certification_stability_shard_suite_manifest/v1"
    assert Path(payload["output_path"]) == output
    suites = {suite["suite"]: suite for suite in payload["suites"]}
    assert set(suites) == {"collection", "constitutional", "pytest-execution"}
    assert len(suites["collection"]["shard_reports"]) == 2
    assert len(suites["constitutional"]["shard_reports"]) == 3
    assert len(suites["pytest-execution"]["shard_reports"]) == 4
    assert "--include-pytest-shards" in " ".join(suites["pytest-execution"]["local_certify"]["command"])
    capsys.readouterr()


def test_certification_stability_verifies_shard_suite_manifest(tmp_path) -> None:
    manifest = tmp_path / "shard_suite_manifest.json"
    payload = _build_shard_suite_manifest(
        suites=["collection"],
        py="python",
        output_root=tmp_path / "certification_stability",
        collection_shard_count=2,
        constitutional_shard_count=2,
        pytest_shard_count=2,
        timeout_seconds=120,
        heartbeat_seconds=5,
    )
    manifest.write_text(__import__("json").dumps(payload), encoding="utf-8")

    verification = _verify_shard_suite_manifest(manifest, output_path=tmp_path / "verification.json")

    assert verification["schema_version"] == "certification_stability_shard_suite_manifest_verification/v1"
    assert verification["status"] == "PASS"
    assert verification["blockers"] == []


def test_certification_stability_shard_suite_manifest_verification_blocks_stale_source_tree(tmp_path) -> None:
    manifest = tmp_path / "shard_suite_manifest.json"
    payload = _build_shard_suite_manifest(
        suites=["constitutional"],
        py="python",
        output_root=tmp_path / "certification_stability",
        collection_shard_count=2,
        constitutional_shard_count=2,
        pytest_shard_count=2,
        timeout_seconds=120,
        heartbeat_seconds=5,
    )
    payload["suites"][0]["source_tree"]["manifest_sha256"] = "stale"
    manifest.write_text(__import__("json").dumps(payload), encoding="utf-8")

    verification = _verify_shard_suite_manifest(manifest, output_path=tmp_path / "verification.json")

    assert verification["status"] == "FAIL"
    assert any(str(blocker).startswith("SHARD_SUITE_MANIFEST_SOURCE_TREE_STALE:constitutional") for blocker in verification["blockers"])


def test_certification_stability_cli_verifies_shard_suite_manifest(tmp_path, capsys) -> None:
    manifest = tmp_path / "shard_suite_manifest.json"
    verification = tmp_path / "shard_suite_manifest_verification.json"
    code = certification_stability_main([
        "--write-shard-suite-manifest",
        "collection",
        "--collection-shard-count",
        "2",
        "--shard-suite-output-root",
        str(tmp_path / "certification_stability"),
        "--output",
        str(manifest),
        "--json",
    ])
    assert code == 0

    code = certification_stability_main([
        "--verify-shard-suite-manifest",
        str(manifest),
        "--output",
        str(verification),
        "--json",
    ])

    assert code == 0
    payload = __import__("json").loads(verification.read_text(encoding="utf-8"))
    assert payload["status"] == "PASS"
    capsys.readouterr()


def test_certification_stability_report_records_runtime_metadata(tmp_path, capsys) -> None:
    output = tmp_path / "certification_stability_report.json"

    code = certification_stability_main([
        "--phase",
        "python-core",
        "--timeout-seconds",
        "120",
        "--constitutional-shard-count",
        "4",
        "--output",
        str(output),
        "--json",
    ])

    assert code == 0
    payload = __import__("json").loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "certification_stability/v2"
    assert payload["status"] == "PASS"
    assert payload["constitutional_shard_count"] == 4
    assert payload["python_version"]
    assert payload["timestamp"]
    assert payload["repo_root"]
    assert Path(payload["output_path"]) == output
    assert payload["steps"]
    capsys.readouterr()


def test_certification_stability_constitutional_shard_index_selects_one_resumable_shard() -> None:
    full_plan = _constitutional_shard_plan("python", shard_count=8)
    selected_plan = _constitutional_shard_plan("python", shard_count=8, shard_index=3)

    assert selected_plan.name == "constitutional_shards"
    assert len(selected_plan.steps) == 1
    assert selected_plan.steps[0] == full_plan.steps[2]
    assert selected_plan.steps[0][0] == "pytest_constitutional_03_of_08"


def test_certification_stability_constitutional_shard_index_is_reported(tmp_path, capsys) -> None:
    output = tmp_path / "certification_stability_report.json"

    code = certification_stability_main([
        "--phase",
        "python-core",
        "--timeout-seconds",
        "120",
        "--constitutional-shard-count",
        "8",
        "--constitutional-shard-index",
        "3",
        "--output",
        str(output),
        "--json",
    ])

    assert code == 0
    payload = __import__("json").loads(output.read_text(encoding="utf-8"))
    assert payload["constitutional_shard_count"] == 8
    assert payload["constitutional_shard_index"] == 3
    capsys.readouterr()


def test_local_certify_optional_constitutional_shard_steps_are_resumable() -> None:
    from scripts.local_certify import planned_constitutional_shard_steps

    steps = planned_constitutional_shard_steps(shard_count=3, timeout_seconds=45)

    assert [name for name, _command, _cwd in steps] == [
        "constitutional_shard_01_of_03",
        "constitutional_shard_02_of_03",
        "constitutional_shard_03_of_03",
        "constitutional_shards_summary",
        "constitutional_shards_summary_verification",
    ]
    shard_commands = [" ".join(command) for _name, command, _cwd in steps[:3]]
    assert all("--phase constitutional-shards" in command for command in shard_commands)
    assert all("--constitutional-shard-count 3" in command for command in shard_commands)
    assert all("--timeout-seconds 45" in command for command in shard_commands)
    assert "--aggregate-constitutional-shard-reports" in " ".join(steps[-2][1])
    assert "--verify-constitutional-summary" in " ".join(steps[-1][1])


def _write_fake_constitutional_report(
    path: Path,
    *,
    index: int,
    count: int,
    command: tuple[str, ...] | list[str],
    status: str = "PASS",
    exit_code: int = 0,
    timed_out: bool = False,
) -> None:
    import json

    payload = {
        "schema_version": "certification_stability/v2",
        "status": status,
        "failed_step": None if status == "PASS" else f"pytest_constitutional_{index:02d}_of_{count:02d}",
        "timeout_seconds": 120,
        "constitutional_shard_count": count,
        "constitutional_shard_index": index,
        "constitutional_source_tree": {
            "file_count": len(tuple((ROOT / "tests" / "constitutional").glob("test_*.py"))),
            "manifest_sha256": _constitutional_source_manifest_digest(),
        },
        "phases": ["constitutional_shards"],
        "python_version": "3.test",
        "node_version": None,
        "timestamp": "2026-01-01T00:00:00+00:00",
        "repo_root": str(ROOT),
        "output_path": str(path),
        "steps": [
            {
                "name": f"pytest_constitutional_{index:02d}_of_{count:02d}",
                "command": list(command),
                "cwd": ".",
                "exit_code": exit_code,
                "timed_out": timed_out,
                "duration_seconds": 1.0,
                "stdout_tail": "",
                "stderr_tail": "",
            }
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_constitutional_shard_report_aggregation_requires_complete_passing_set(tmp_path) -> None:
    import json
    from scripts.certification_stability import _aggregate_constitutional_shard_reports

    plan = _constitutional_shard_plan("python", shard_count=3)
    report_paths = []
    for index, (_name, command, _cwd) in enumerate(plan.steps, start=1):
        path = tmp_path / f"constitutional_shard_{index}.json"
        _write_fake_constitutional_report(path, index=index, count=3, command=command)
        report_paths.append(path)
    output = tmp_path / "constitutional_shards_summary.json"

    payload = _aggregate_constitutional_shard_reports(report_paths, expected_shard_count=3, output_path=output)

    assert payload["schema_version"] == "certification_stability_constitutional_summary/v2"
    assert payload["status"] == "PASS"
    assert payload["constitutional_shard_count"] == 3
    assert payload["observed_shard_indexes"] == [1, 2, 3]
    assert payload["missing_shard_indexes"] == []
    assert payload["blockers"] == []
    assert payload["constitutional_source_tree"]["manifest_sha256"] == _constitutional_source_manifest_digest()
    assert payload["source_reports_sha256"]
    assert payload["summary_payload_sha256"] == _summary_payload_digest(payload)
    assert output.exists()
    persisted = json.loads(output.read_text(encoding="utf-8"))
    assert persisted["status"] == "PASS"
    assert persisted["summary_payload_sha256"] == _summary_payload_digest(persisted)


def test_constitutional_shard_report_aggregation_blocks_missing_or_failed_shards(tmp_path) -> None:
    from scripts.certification_stability import _aggregate_constitutional_shard_reports

    first = tmp_path / "constitutional_shard_1.json"
    second = tmp_path / "constitutional_shard_2.json"
    plan = _constitutional_shard_plan("python", shard_count=3)
    _write_fake_constitutional_report(first, index=1, count=3, command=plan.steps[0][1])
    _write_fake_constitutional_report(second, index=2, count=3, command=plan.steps[1][1], status="FAIL", exit_code=1)

    payload = _aggregate_constitutional_shard_reports([first, second], expected_shard_count=3, output_path=tmp_path / "summary.json")

    assert payload["status"] == "FAIL"
    assert payload["missing_shard_indexes"] == [3]
    blockers = "\n".join(payload["blockers"])
    assert "CONSTITUTIONAL_SHARD_REPORT_NOT_PASSING" in blockers
    assert "CONSTITUTIONAL_SHARD_NONZERO_EXIT" in blockers
    assert "CONSTITUTIONAL_SHARD_INDEX_MISSING:3" in blockers



def test_constitutional_aggregation_emits_exact_failed_shard_blockers(tmp_path) -> None:
    import json

    plan = _constitutional_shard_plan("python", shard_count=3)
    reports = []
    for index, (_name, command, _cwd) in enumerate(plan.steps, start=1):
        path = tmp_path / f"constitutional_shard_{index}.json"
        if index == 2:
            _write_fake_constitutional_report(
                path,
                index=index,
                count=3,
                command=command,
                status="FAIL",
                exit_code=124,
                timed_out=True,
            )
        else:
            _write_fake_constitutional_report(path, index=index, count=3, command=command)
        reports.append(path)

    summary = tmp_path / "constitutional_shards_summary.json"
    payload = _aggregate_constitutional_shard_reports(reports, expected_shard_count=3, output_path=summary)

    assert payload["status"] == "FAIL"
    assert payload["failed_shard_count"] == 1
    assert payload["timed_out_shard_count"] == 1
    assert payload["nonzero_shard_count"] == 1
    assert payload["first_failed_shard"]["shard_index"] == 2
    assert "--constitutional-shard-index" in payload["next_diagnostic"]
    blockers = "\n".join(payload["blockers"])
    assert "CONSTITUTIONAL_SHARD_TIMED_OUT" in blockers
    assert "CONSTITUTIONAL_SHARD_NONZERO_EXIT" in blockers

    persisted = json.loads(summary.read_text(encoding="utf-8"))
    assert persisted["failed_constitutional_shards"][0]["timeout_seconds"] == 120


def test_constitutional_summary_verification_requires_exact_blocker_fields(tmp_path) -> None:
    import json

    summary, _reports = _write_complete_summary(tmp_path)
    payload = json.loads(summary.read_text(encoding="utf-8"))
    payload.pop("failed_shard_count")
    payload["summary_payload_sha256"] = _summary_payload_digest(payload)
    summary.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    verification = _verify_constitutional_summary_report(summary, output_path=tmp_path / "verification.json")

    assert verification["status"] == "FAIL"
    blockers = "\n".join(verification["blockers"])
    assert "CONSTITUTIONAL_SUMMARY_FIELD_MISSING:failed_shard_count" in blockers

def test_constitutional_shard_report_aggregation_blocks_missing_test_file_coverage(tmp_path) -> None:
    from scripts.certification_stability import _aggregate_constitutional_shard_reports, _constitutional_shard_plan

    plan = _constitutional_shard_plan("python", shard_count=3)
    report_paths = []
    for index, (_name, command, _cwd) in enumerate(plan.steps, start=1):
        path = tmp_path / f"constitutional_shard_{index}.json"
        if index == 3:
            command = tuple(part for part in command if not str(part).startswith("tests/constitutional/test_"))
        _write_fake_constitutional_report(path, index=index, count=3, command=command)
        report_paths.append(path)

    payload = _aggregate_constitutional_shard_reports(report_paths, expected_shard_count=3, output_path=tmp_path / "summary.json")

    assert payload["status"] == "FAIL"
    assert payload["missing_constitutional_test_files"]
    blockers = "\n".join(payload["blockers"])
    assert "CONSTITUTIONAL_TEST_FILE_MISSING_FROM_SHARDS" in blockers


def test_certification_stability_report_records_constitutional_source_tree_identity(tmp_path, capsys) -> None:
    output = tmp_path / "certification_stability_report.json"

    code = certification_stability_main([
        "--phase",
        "python-core",
        "--timeout-seconds",
        "120",
        "--output",
        str(output),
        "--json",
    ])

    assert code == 0
    payload = __import__("json").loads(output.read_text(encoding="utf-8"))
    assert payload["constitutional_source_tree"]["manifest_sha256"] == _constitutional_source_manifest_digest()
    assert payload["constitutional_source_tree"]["file_count"] > 0
    capsys.readouterr()


def test_constitutional_shard_report_aggregation_blocks_foreign_repo_root(tmp_path) -> None:
    import json
    from scripts.certification_stability import _aggregate_constitutional_shard_reports

    plan = _constitutional_shard_plan("python", shard_count=1)
    report = tmp_path / "constitutional_shard_1.json"
    _write_fake_constitutional_report(report, index=1, count=1, command=plan.steps[0][1])
    payload = json.loads(report.read_text(encoding="utf-8"))
    payload["repo_root"] = "/tmp/foreign-strategy-validator"
    report.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    summary = _aggregate_constitutional_shard_reports([report], expected_shard_count=1, output_path=tmp_path / "summary.json")

    assert summary["status"] == "FAIL"
    blockers = "\n".join(summary["blockers"])
    assert "CONSTITUTIONAL_SHARD_REPO_ROOT_MISMATCH" in blockers


def test_constitutional_shard_report_aggregation_blocks_stale_source_tree(tmp_path) -> None:
    import json
    from scripts.certification_stability import _aggregate_constitutional_shard_reports

    plan = _constitutional_shard_plan("python", shard_count=1)
    report = tmp_path / "constitutional_shard_1.json"
    _write_fake_constitutional_report(report, index=1, count=1, command=plan.steps[0][1])
    payload = json.loads(report.read_text(encoding="utf-8"))
    payload["constitutional_source_tree"]["manifest_sha256"] = "0" * 64
    report.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    summary = _aggregate_constitutional_shard_reports([report], expected_shard_count=1, output_path=tmp_path / "summary.json")

    assert summary["status"] == "FAIL"
    blockers = "\n".join(summary["blockers"])
    assert "CONSTITUTIONAL_SHARD_SOURCE_TREE_MISMATCH" in blockers


def _write_complete_summary(tmp_path: Path, *, shard_count: int = 3) -> tuple[Path, list[Path]]:
    plan = _constitutional_shard_plan("python", shard_count=shard_count)
    report_paths: list[Path] = []
    for index, (_name, command, _cwd) in enumerate(plan.steps, start=1):
        report = tmp_path / f"constitutional_shard_{index}.json"
        _write_fake_constitutional_report(report, index=index, count=shard_count, command=command)
        report_paths.append(report)
    summary = tmp_path / "constitutional_shards_summary.json"
    payload = _aggregate_constitutional_shard_reports(report_paths, expected_shard_count=shard_count, output_path=summary)
    assert payload["status"] == "PASS"
    return summary, report_paths


def test_constitutional_summary_verification_accepts_current_complete_summary(tmp_path) -> None:
    summary, _reports = _write_complete_summary(tmp_path)

    verification = _verify_constitutional_summary_report(summary, output_path=tmp_path / "verification.json")

    assert verification["schema_version"] == "certification_stability_constitutional_summary_verification/v1"
    assert verification["status"] == "PASS"
    assert verification["blockers"] == []
    assert (tmp_path / "verification.json").exists()


def test_constitutional_summary_verification_blocks_summary_payload_tampering(tmp_path) -> None:
    import json

    summary, _reports = _write_complete_summary(tmp_path)
    payload = json.loads(summary.read_text(encoding="utf-8"))
    payload["status"] = "FAIL"
    summary.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    verification = _verify_constitutional_summary_report(summary, output_path=tmp_path / "verification.json")

    assert verification["status"] == "FAIL"
    blockers = "\n".join(verification["blockers"])
    assert "CONSTITUTIONAL_SUMMARY_NOT_PASSING" in blockers
    assert "CONSTITUTIONAL_SUMMARY_PAYLOAD_DIGEST_MISMATCH" in blockers


def test_constitutional_summary_verification_blocks_source_report_tampering(tmp_path) -> None:
    import json

    summary, reports = _write_complete_summary(tmp_path)
    report_payload = json.loads(reports[0].read_text(encoding="utf-8"))
    report_payload["status"] = "FAIL"
    reports[0].write_text(json.dumps(report_payload, indent=2, sort_keys=True), encoding="utf-8")

    verification = _verify_constitutional_summary_report(summary, output_path=tmp_path / "verification.json")

    assert verification["status"] == "FAIL"
    assert verification["source_report_mismatch_count"] == 1
    blockers = "\n".join(verification["blockers"])
    assert "CONSTITUTIONAL_SUMMARY_SOURCE_REPORT_SHA256_MISMATCH" in blockers


def test_certification_stability_cli_verifies_constitutional_summary(tmp_path, capsys) -> None:
    summary, _reports = _write_complete_summary(tmp_path)
    verification = tmp_path / "verification.json"

    code = certification_stability_main([
        "--verify-constitutional-summary",
        str(summary),
        "--output",
        str(verification),
        "--json",
    ])

    assert code == 0
    payload = __import__("json").loads(verification.read_text(encoding="utf-8"))
    assert payload["status"] == "PASS"
    capsys.readouterr()


def test_npm_public_registry_env_pins_registry() -> None:
    from scripts.local_certify import _npm_public_registry_env

    assert _npm_public_registry_env() == {"NPM_CONFIG_REGISTRY": "https://registry.npmjs.org/"}


def test_frontend_certify_runs_dependency_audit_gate() -> None:
    import json

    package = json.loads((ROOT / "ui" / "strategist-web" / "package.json").read_text(encoding="utf-8"))
    scripts = package["scripts"]

    assert scripts["audit"] == "npm audit --audit-level=high"
    assert scripts["certify"] == "node ./scripts/certify.mjs"
    certify_runner = ROOT / "ui" / "strategist-web" / "scripts" / "certify.mjs"
    certify_text = certify_runner.read_text(encoding="utf-8")
    assert "npm" in certify_text and "audit" in certify_text and "--audit-level=high" in certify_text
    assert "frontend certify" in certify_text
    assert package["dependencies"]["next"] == "15.5.18"
    assert package["devDependencies"]["eslint-config-next"] == "15.5.18"


def test_frontend_certify_writes_operator_grade_report() -> None:
    runner = ROOT / "ui" / "strategist-web" / "scripts" / "certify.mjs"
    text = runner.read_text(encoding="utf-8")

    assert "frontend_certify/v1" in text
    assert "FRONTEND_CERTIFY_REPORT" in text
    assert "artifacts/frontend_certify/latest/frontend_certify_report.json" in text
    assert "writeReport(\"PASS\")" in text
    assert "writeReport(\"FAIL\", step.name)" in text
    for required_step in (
        "contract_check",
        "lint",
        "typecheck",
        "test",
        "acceptance",
        "build",
        "audit",
    ):
        assert f'name: "{required_step}"' in text
    assert 'args: ["run", "lint"]' in text
    assert 'args: ["run", "typecheck"]' in text


def test_local_certify_validates_and_references_frontend_certify_report(tmp_path) -> None:
    import json
    from scripts.local_certify import validate_frontend_certify_report

    report = tmp_path / "frontend_certify_report.json"
    report.write_text(json.dumps(_frontend_report_payload(report), indent=2), encoding="utf-8")

    summary, blockers = validate_frontend_certify_report(report)

    assert blockers == []
    assert summary is not None
    assert summary["schema_version"] == "frontend_certify/v1"
    assert summary["status"] == "PASS"
    assert summary["proof_name"] == "frontend_certify_report"
    assert summary["path"] == str(report)
    assert summary["sha256"]
    assert summary["source_tree_digest"]
    assert summary["created_at"] == "2026-01-01T00:01:00+00:00"
    assert summary["verified_at"]
    assert summary["step_names"] == [
        "contract_check",
        "lint",
        "typecheck",
        "test",
        "acceptance",
        "build",
        "audit",
    ]


def test_local_certify_blocks_incomplete_frontend_certify_report(tmp_path) -> None:
    import json
    from scripts.local_certify import validate_frontend_certify_report

    report = tmp_path / "frontend_certify_report.json"
    report.write_text(
        json.dumps(
            _frontend_report_payload(
                report,
                steps=[_frontend_step("contract_check"), _frontend_step("lint")],
            )
        ),
        encoding="utf-8",
    )

    summary, blockers = validate_frontend_certify_report(report)

    assert summary is not None
    assert summary["status"] == "PASS"
    assert any("FRONTEND_CERTIFY_REPORT_REQUIRED_STEPS_MISSING" in blocker for blocker in blockers)


def test_local_certify_payload_embeds_frontend_certify_report_summary() -> None:
    from scripts.local_certify import _build_payload

    frontend_report = {
        "schema_version": "frontend_certify/v1",
        "status": "PASS",
        "sha256": "abc123",
        "step_names": ["contract_check", "lint", "typecheck", "test", "acceptance", "build", "audit"],
    }

    payload = _build_payload(
        results=[],
        failed=None,
        frontend_included=True,
        constitutional_shards_included=False,
        constitutional_shard_count=None,
        frontend_certify_report=frontend_report,
    )

    assert payload["schema_version"] == "local_certify/v5"
    assert payload["status"] == "PASS"
    assert payload["frontend_certify_report"] == frontend_report



def _base_local_certify_results_and_proofs(tmp_path: Path):
    import json
    from scripts.local_certify import (
        LocalCertifyStep,
        validate_package_repo_check_report,
        validate_public_surface_dashboard_report,
        validate_python_core_report,
        _write_python_core_report,
    )

    public_report = tmp_path / "public_surface_dashboard.json"
    public_report.write_text(
        json.dumps(
            {
                "schema_version": "public_surface_dashboard/v1",
                "ok": True,
                "repo_root": str(ROOT),
                "generated_at": "2026-01-01T00:00:00+00:00",
                "violations": [],
                "ratchet_validation": {
                    "schema_version": "public_surface_ratchet_validation/v1",
                    "status": "PASS",
                    "blockers": [],
                },
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    public_summary, public_blockers = validate_public_surface_dashboard_report(public_report)
    assert public_blockers == []
    assert public_summary is not None

    package_report = tmp_path / "package_repo_check.json"
    package_report.write_text(
        json.dumps(
            {
                "schema_version": "clean_repo_archive/v2",
                "status": "PASS",
                "repo_root": str(ROOT),
                "output_path": None,
                "generated_at": "2026-01-01T00:01:00+00:00",
                "included_file_count": 1,
                "skipped_file_count": 0,
                "skipped_generated_roots": [],
                "exclusions_applied": [],
                "warnings": [],
                "blockers": [],
                "archive_sha256": None,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    package_summary, package_blockers = validate_package_repo_check_report(package_report)
    assert package_blockers == []
    assert package_summary is not None

    names = (
        "compileall",
        "source_health",
        "repository_truth",
        "migration_truth",
        "public_surface_dashboard",
        "public_surface_dashboard_report_validation",
        "package_repo_check",
        "package_repo_check_report_validation",
        "pytest",
    )
    results = [
        LocalCertifyStep(
            name=name,
            command=("python", name),
            cwd=".",
            exit_code=0,
            duration_seconds=0.01,
            stdout_tail="",
            stderr_tail="",
            artifact_paths=(str(public_report),)
            if name == "public_surface_dashboard_report_validation"
            else (str(package_report),)
            if name == "package_repo_check_report_validation"
            else (),
        )
        for name in names
    ]
    python_report = tmp_path / "python_core_report.json"
    _write_python_core_report(results=results, failed=None, report_path=python_report)
    python_summary, python_blockers = validate_python_core_report(python_report)
    assert python_blockers == []
    assert python_summary is not None
    results.append(
        LocalCertifyStep(
            name="python_core_report_validation",
            command=("internal", "validate_python_core_report", str(python_report)),
            cwd=".",
            exit_code=0,
            duration_seconds=0.01,
            stdout_tail="",
            stderr_tail="",
            artifact_paths=(str(python_report),),
        )
    )
    return results, python_summary, public_summary, package_summary, public_report, package_report

def _minimal_local_certify_report(tmp_path: Path, *, frontend: bool = False) -> tuple[Path, Path | None]:
    import json
    from scripts.local_certify import LocalCertifyStep, _build_payload

    frontend_report_path: Path | None = None
    frontend_summary = None
    results, python_summary, public_summary, package_summary, _public_report, _package_report = _base_local_certify_results_and_proofs(tmp_path)
    if frontend:
        frontend_report_path = tmp_path / "frontend_certify_report.json"
        frontend_payload = _frontend_report_payload(frontend_report_path, finished_at="2026-01-01T00:02:00+00:00")
        frontend_report_path.write_text(json.dumps(frontend_payload, indent=2), encoding="utf-8")
        from scripts.local_certify import validate_frontend_certify_report

        frontend_summary, blockers = validate_frontend_certify_report(frontend_report_path)
        assert blockers == []
        results.extend(
            [
                LocalCertifyStep("frontend_npm_ci", ("npm", "ci"), "ui/strategist-web", 0, 0.01, "", ""),
                LocalCertifyStep("frontend_certify", ("npm", "run", "certify"), "ui/strategist-web", 0, 0.01, "", ""),
                LocalCertifyStep(
                    "frontend_certify_report_validation",
                    ("internal", "validate_frontend_certify_report", str(frontend_report_path)),
                    ".",
                    0,
                    0.01,
                    "",
                    "",
                    (str(frontend_report_path),),
                ),
            ]
        )
    payload = _build_payload(
        results=results,
        failed=None,
        frontend_included=frontend,
        constitutional_shards_included=False,
        constitutional_shard_count=None,
        frontend_certify_report=frontend_summary,
        python_core_report=python_summary,
        public_surface_dashboard=public_summary,
        package_repo_check=package_summary,
    )
    report = tmp_path / "local_certify_report.json"
    report.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return report, frontend_report_path


def test_local_certify_report_verification_accepts_complete_sealed_report(tmp_path) -> None:
    from scripts.local_certify import verify_local_certify_report

    report, _frontend = _minimal_local_certify_report(tmp_path, frontend=True)
    verification = verify_local_certify_report(report, output_path=tmp_path / "verification.json")

    assert verification["schema_version"] == "local_certify_report_verification/v1"
    assert verification["status"] == "PASS"
    assert verification["blockers"] == []
    assert verification["step_count"] == 13
    assert (tmp_path / "verification.json").exists()


def test_local_certify_report_verification_blocks_payload_tampering(tmp_path) -> None:
    import json
    from scripts.local_certify import verify_local_certify_report

    report, _frontend = _minimal_local_certify_report(tmp_path, frontend=False)
    payload = json.loads(report.read_text(encoding="utf-8"))
    payload["status"] = "FAIL"
    report.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    verification = verify_local_certify_report(report)

    assert verification["status"] == "FAIL"
    blockers = "\n".join(verification["blockers"])
    assert "LOCAL_CERTIFY_REPORT_PAYLOAD_DIGEST_MISMATCH" in blockers
    assert "LOCAL_CERTIFY_REPORT_FAIL_MISSING_FAILED_STEP" in blockers


def test_local_certify_report_verification_blocks_frontend_report_tampering(tmp_path) -> None:
    import json
    from scripts.local_certify import verify_local_certify_report

    report, frontend_report = _minimal_local_certify_report(tmp_path, frontend=True)
    assert frontend_report is not None
    frontend_payload = json.loads(frontend_report.read_text(encoding="utf-8"))
    frontend_payload["status"] = "FAIL"
    frontend_report.write_text(json.dumps(frontend_payload, indent=2, sort_keys=True), encoding="utf-8")

    verification = verify_local_certify_report(report)

    assert verification["status"] == "FAIL"
    blockers = "\n".join(verification["blockers"])
    assert "LOCAL_CERTIFY_FRONTEND_REPORT_SHA256_MISMATCH" in blockers


def test_local_certify_cli_verifies_existing_report(tmp_path, capsys) -> None:
    import json
    from scripts.local_certify import main as local_certify_main

    report, _frontend = _minimal_local_certify_report(tmp_path, frontend=False)
    verification = tmp_path / "local_certify_report_verification.json"

    code = local_certify_main(["--verify-report", str(report), "--verification-output", str(verification), "--json"])

    assert code == 0
    payload = json.loads(verification.read_text(encoding="utf-8"))
    assert payload["status"] == "PASS"
    capsys.readouterr()



def test_certification_stability_collection_shard_index_selects_one_resumable_shard() -> None:
    full_plan = _collection_shard_plan("python", shard_count=7)
    selected_plan = _collection_shard_plan("python", shard_count=7, shard_index=4)

    assert selected_plan.name == "collect_shards"
    assert len(selected_plan.steps) == 1
    assert selected_plan.steps[0] == full_plan.steps[3]
    assert selected_plan.steps[0][0] == "pytest_collect_04_of_07"
    assert "--collect-only" in selected_plan.steps[0][1]


def test_local_certify_optional_collection_shard_steps_are_resumable() -> None:
    from scripts.local_certify import planned_collection_shard_steps

    steps = planned_collection_shard_steps(shard_count=3, timeout_seconds=45)

    assert [name for name, _command, _cwd in steps] == [
        "collection_shard_01_of_03",
        "collection_shard_02_of_03",
        "collection_shard_03_of_03",
        "collection_shards_summary",
        "collection_shards_summary_verification",
    ]
    shard_commands = [" ".join(command) for _name, command, _cwd in steps[:3]]
    assert all("--phase collect-shards" in command for command in shard_commands)
    assert all("--collection-shard-count 3" in command for command in shard_commands)
    assert all("--timeout-seconds 45" in command for command in shard_commands)
    assert "--aggregate-collection-shard-reports" in " ".join(steps[-2][1])
    assert "--verify-collection-summary" in " ".join(steps[-1][1])


def _write_fake_collection_report(
    path: Path,
    *,
    index: int,
    count: int,
    command: tuple[str, ...] | list[str],
    status: str = "PASS",
    exit_code: int = 0,
    timed_out: bool = False,
) -> None:
    import json

    payload = {
        "schema_version": "certification_stability/v2",
        "status": status,
        "failed_step": None if status == "PASS" else f"pytest_collect_{index:02d}_of_{count:02d}",
        "timeout_seconds": 120,
        "collection_shard_count": count,
        "collection_shard_index": index,
        "collection_source_tree": {
            "file_count": len(tuple((ROOT / "tests").rglob("test_*.py"))),
            "manifest_sha256": _collection_source_manifest_digest(),
        },
        "constitutional_shard_count": 32,
        "constitutional_shard_index": None,
        "constitutional_source_tree": {
            "file_count": len(tuple((ROOT / "tests" / "constitutional").glob("test_*.py"))),
            "manifest_sha256": _constitutional_source_manifest_digest(),
        },
        "phases": ["collect_shards"],
        "python_version": "3.test",
        "node_version": None,
        "timestamp": "2026-01-01T00:00:00+00:00",
        "repo_root": str(ROOT),
        "output_path": str(path),
        "steps": [
            {
                "name": f"pytest_collect_{index:02d}_of_{count:02d}",
                "command": list(command),
                "cwd": ".",
                "exit_code": exit_code,
                "timed_out": timed_out,
                "duration_seconds": 1.0,
                "stdout_tail": "",
                "stderr_tail": "",
            }
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_complete_collection_summary(tmp_path: Path, *, shard_count: int = 5) -> tuple[Path, list[Path]]:
    plan = _collection_shard_plan("python", shard_count=shard_count)
    report_paths = []
    for index, (_name, command, _cwd) in enumerate(plan.steps, start=1):
        path = tmp_path / f"collection_shard_{index}.json"
        _write_fake_collection_report(path, index=index, count=shard_count, command=command)
        report_paths.append(path)
    summary = tmp_path / "collection_shards_summary.json"
    payload = _aggregate_collection_shard_reports(report_paths, expected_shard_count=shard_count, output_path=summary)
    assert payload["status"] == "PASS"
    return summary, report_paths


def test_collection_shard_report_aggregation_requires_complete_passing_set(tmp_path) -> None:
    import json

    summary, _reports = _write_complete_collection_summary(tmp_path, shard_count=5)
    payload = json.loads(summary.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "certification_stability_collection_summary/v1"
    assert payload["status"] == "PASS"
    assert payload["collection_shard_count"] == 5
    assert payload["missing_shard_indexes"] == []
    assert payload["blockers"] == []
    assert payload["expected_collection_test_file_count"] == len(tuple((ROOT / "tests").rglob("test_*.py")))
    assert payload["expected_collection_test_file_count"] == payload["covered_collection_test_file_count"]
    assert payload["collection_source_tree"]["manifest_sha256"] == _collection_source_manifest_digest()
    assert payload["source_reports_sha256"]
    assert payload["summary_payload_sha256"] == _summary_payload_digest(payload)


def test_collection_shard_report_aggregation_blocks_missing_or_failed_shards(tmp_path) -> None:
    plan = _collection_shard_plan("python", shard_count=4)
    first = tmp_path / "collection_shard_1.json"
    second = tmp_path / "collection_shard_2.json"
    _write_fake_collection_report(first, index=1, count=4, command=plan.steps[0][1])
    _write_fake_collection_report(second, index=2, count=4, command=plan.steps[1][1], status="FAIL", exit_code=1)

    payload = _aggregate_collection_shard_reports([first, second], expected_shard_count=4, output_path=tmp_path / "summary.json")

    assert payload["status"] == "FAIL"
    assert payload["missing_shard_indexes"] == [3, 4]
    blockers = "\n".join(payload["blockers"])
    assert "COLLECTION_SHARD_REPORT_NOT_PASSING" in blockers
    assert "COLLECTION_SHARD_NONZERO_EXIT" in blockers
    assert "COLLECTION_SHARD_INDEX_MISSING:3" in blockers



def test_collection_aggregation_emits_exact_failed_shard_blockers(tmp_path) -> None:
    import json

    plan = _collection_shard_plan("python", shard_count=4)
    reports = []
    for index, (_name, command, _cwd) in enumerate(plan.steps, start=1):
        path = tmp_path / f"collection_shard_{index}.json"
        if index == 3:
            _write_fake_collection_report(
                path,
                index=index,
                count=4,
                command=command,
                status="FAIL",
                exit_code=124,
                timed_out=True,
            )
        else:
            _write_fake_collection_report(path, index=index, count=4, command=command)
        reports.append(path)

    summary = tmp_path / "collection_shards_summary.json"
    payload = _aggregate_collection_shard_reports(reports, expected_shard_count=4, output_path=summary)

    assert payload["status"] == "FAIL"
    assert payload["failed_shard_count"] == 1
    assert payload["timed_out_shard_count"] == 1
    assert payload["nonzero_shard_count"] == 1
    assert payload["first_failed_shard"]["shard_index"] == 3
    assert "--collection-shard-index" in payload["next_diagnostic"]
    blockers = "\n".join(payload["blockers"])
    assert "COLLECTION_SHARD_TIMED_OUT" in blockers
    assert "COLLECTION_SHARD_NONZERO_EXIT" in blockers

    persisted = json.loads(summary.read_text(encoding="utf-8"))
    assert persisted["failed_collection_shards"][0]["timeout_seconds"] == 120


def test_collection_summary_verification_requires_exact_blocker_fields(tmp_path) -> None:
    import json

    summary, _reports = _write_complete_collection_summary(tmp_path, shard_count=5)
    payload = json.loads(summary.read_text(encoding="utf-8"))
    payload.pop("failed_shard_count")
    payload["summary_payload_sha256"] = _summary_payload_digest(payload)
    summary.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    verification = _verify_collection_summary_report(summary, output_path=tmp_path / "collection_verification.json")

    assert verification["status"] == "FAIL"
    blockers = "\n".join(verification["blockers"])
    assert "COLLECTION_SUMMARY_FIELD_MISSING:failed_shard_count" in blockers

def test_collection_summary_verification_accepts_complete_summary(tmp_path) -> None:
    summary, _reports = _write_complete_collection_summary(tmp_path, shard_count=5)

    verification = _verify_collection_summary_report(summary, output_path=tmp_path / "collection_verification.json")

    assert verification["schema_version"] == "certification_stability_collection_summary_verification/v1"
    assert verification["status"] == "PASS"
    assert verification["blockers"] == []
    assert (tmp_path / "collection_verification.json").exists()


def test_collection_summary_verification_blocks_source_report_tampering(tmp_path) -> None:
    import json

    summary, reports = _write_complete_collection_summary(tmp_path, shard_count=5)
    report_payload = json.loads(reports[0].read_text(encoding="utf-8"))
    report_payload["status"] = "FAIL"
    reports[0].write_text(json.dumps(report_payload, indent=2, sort_keys=True), encoding="utf-8")

    verification = _verify_collection_summary_report(summary, output_path=tmp_path / "collection_verification.json")

    assert verification["status"] == "FAIL"
    assert verification["source_report_mismatch_count"] == 1
    blockers = "\n".join(verification["blockers"])
    assert "COLLECTION_SUMMARY_SOURCE_REPORT_SHA256_MISMATCH" in blockers


def test_certification_stability_cli_verifies_collection_summary(tmp_path, capsys) -> None:
    summary, _reports = _write_complete_collection_summary(tmp_path, shard_count=5)
    verification = tmp_path / "collection_verification.json"

    code = certification_stability_main([
        "--verify-collection-summary",
        str(summary),
        "--output",
        str(verification),
        "--json",
    ])

    assert code == 0
    payload = __import__("json").loads(verification.read_text(encoding="utf-8"))
    assert payload["status"] == "PASS"
    capsys.readouterr()


def test_local_certify_payload_embeds_collection_shard_proof_summary(tmp_path) -> None:
    from scripts.local_certify import _build_payload, validate_collection_shards_proof

    summary, _reports = _write_complete_collection_summary(tmp_path, shard_count=5)
    verification = tmp_path / "collection_verification.json"
    _verify_collection_summary_report(summary, output_path=verification)

    proof, blockers = validate_collection_shards_proof(summary, verification)
    assert blockers == []
    assert proof is not None
    _results, python_summary, public_summary, package_summary, _public_report, _package_report = _base_local_certify_results_and_proofs(tmp_path)

    payload = _build_payload(
        results=[],
        failed=None,
        frontend_included=False,
        collection_shards_included=True,
        collection_shard_count=5,
        constitutional_shards_included=False,
        constitutional_shard_count=None,
        collection_shards_proof=proof,
        python_core_report=python_summary,
        public_surface_dashboard=public_summary,
        package_repo_check=package_summary,
    )

    assert payload["schema_version"] == "local_certify/v5"
    assert payload["collection_shards_proof"] == proof
    assert payload["collection_shards_proof"]["path"] == payload["collection_shards_proof"]["summary_path"]
    assert payload["collection_shards_proof"]["sha256"] == payload["collection_shards_proof"]["summary_sha256"]
    assert payload["collection_shards_proof"]["schema_version"] == "certification_stability_collection_summary/v1"
    assert payload["collection_shards_proof"]["source_tree_digest"]
    assert payload["collection_shards_proof"]["created_at"]
    assert payload["collection_shards_proof"]["verified_at"]
    assert payload["collection_shards_proof"]["verification_sha256"]


def _minimal_local_certify_report_with_collection(tmp_path: Path, *, shard_count: int = 5) -> tuple[Path, Path, Path]:
    import json
    from scripts.local_certify import LocalCertifyStep, _build_payload, validate_collection_shards_proof

    summary, _reports = _write_complete_collection_summary(tmp_path, shard_count=shard_count)
    verification = tmp_path / "collection_shards_summary_verification.json"
    _verify_collection_summary_report(summary, output_path=verification)
    proof, blockers = validate_collection_shards_proof(summary, verification)
    assert blockers == []
    assert proof is not None

    base_results, python_summary, public_summary, package_summary, _public_report, _package_report = _base_local_certify_results_and_proofs(tmp_path)
    collection_names = [f"collection_shard_{index:02d}_of_{shard_count:02d}" for index in range(1, shard_count + 1)]
    collection_names.extend(["collection_shards_summary", "collection_shards_summary_verification", "collection_shards_report_validation"])
    results = [
        LocalCertifyStep(
            name=name,
            command=("python", name),
            cwd=".",
            exit_code=0,
            duration_seconds=0.01,
            stdout_tail="",
            stderr_tail="",
        )
        for name in collection_names
    ]
    results = [*base_results, *results]
    payload = _build_payload(
        results=results,
        failed=None,
        frontend_included=False,
        collection_shards_included=True,
        collection_shard_count=shard_count,
        constitutional_shards_included=False,
        constitutional_shard_count=None,
        collection_shards_proof=proof,
        python_core_report=python_summary,
        public_surface_dashboard=public_summary,
        package_repo_check=package_summary,
    )
    report = tmp_path / "local_certify_report.json"
    report.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return report, summary, verification


def test_local_certify_report_verification_accepts_collection_shard_proof(tmp_path) -> None:
    from scripts.local_certify import verify_local_certify_report

    report, _summary, _verification = _minimal_local_certify_report_with_collection(tmp_path, shard_count=5)
    verification = verify_local_certify_report(report, output_path=tmp_path / "local_verification.json")

    assert verification["status"] == "PASS"
    assert verification["blockers"] == []
    assert verification["collection_shards_proof"]["summary_status"] == "PASS"
    assert verification["collection_shards_proof"]["verification_status"] == "PASS"


def test_local_certify_report_verification_blocks_collection_summary_tampering(tmp_path) -> None:
    import json
    from scripts.local_certify import verify_local_certify_report

    report, summary, _verification = _minimal_local_certify_report_with_collection(tmp_path, shard_count=5)
    payload = json.loads(summary.read_text(encoding="utf-8"))
    payload["status"] = "FAIL"
    summary.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    verification = verify_local_certify_report(report)

    assert verification["status"] == "FAIL"
    blockers = "\n".join(verification["blockers"])
    assert "LOCAL_CERTIFY_COLLECTION_SHARDS_PROOF_SUMMARY_SHA256_MISMATCH" in blockers


def test_local_certify_step_records_watchdog_metadata(tmp_path) -> None:
    from scripts.local_certify import _run

    step = _run(
        "watchdog_probe",
        ["python", "-c", "print('ok')"],
        cwd=ROOT,
        timeout_seconds=5,
        heartbeat_seconds=0,
    )

    assert step.exit_code == 0
    assert step.timeout_seconds == 5
    assert step.started_at
    assert step.ended_at
    assert step.timed_out is False
    assert step.stdout_tail.strip() == "ok"


def test_local_certify_step_timeout_returns_structured_blocker() -> None:
    from scripts.local_certify import _build_payload, _run

    step = _run(
        "pytest",
        ["python", "-c", "import time; time.sleep(2)"],
        cwd=ROOT,
        timeout_seconds=1,
        heartbeat_seconds=0,
    )
    payload = _build_payload(results=[step], failed=step, frontend_included=False)

    assert step.timed_out is True
    assert step.exit_code == 124
    assert payload["status"] == "TIMEOUT"
    assert payload["failed_step"] == "pytest"
    assert payload["timeout_seconds"] == 1
    assert "--include-collection-shards" in payload["next_diagnostic"]


def test_local_certify_optional_pytest_execution_shard_steps_are_resumable() -> None:
    from scripts.local_certify import planned_pytest_execution_shard_steps

    steps = planned_pytest_execution_shard_steps(shard_count=3, timeout_seconds=45)

    assert [name for name, _command, _cwd in steps] == [
        "pytest_execution_shard_01_of_03",
        "pytest_execution_shard_02_of_03",
        "pytest_execution_shard_03_of_03",
        "pytest_execution_shards_summary",
        "pytest_execution_shards_summary_verification",
    ]
    shard_commands = [" ".join(command) for _name, command, _cwd in steps[:3]]
    assert all("--phase pytest-execution-shards" in command for command in shard_commands)
    assert all("--pytest-shard-count 3" in command for command in shard_commands)
    assert all("--timeout-seconds 45" in command for command in shard_commands)
    assert "--aggregate-pytest-execution-shard-reports" in " ".join(steps[-2][1])
    assert "--verify-pytest-execution-summary" in " ".join(steps[-1][1])


def _write_fake_pytest_execution_report(
    path: Path,
    *,
    index: int,
    count: int,
    command: tuple[str, ...] | list[str],
    status: str = "PASS",
    exit_code: int = 0,
    timed_out: bool = False,
) -> None:
    import json

    payload = {
        "schema_version": "certification_stability/v2",
        "status": status,
        "failed_step": None if status == "PASS" else f"pytest_execution_{index:02d}_of_{count:02d}",
        "timeout_seconds": 120,
        "pytest_shard_count": count,
        "pytest_shard_index": index,
        "pytest_execution_source_tree": {
            "file_count": len(tuple((ROOT / "tests").rglob("test_*.py"))),
            "manifest_sha256": _pytest_execution_source_manifest_digest(),
        },
        "collection_shard_count": 32,
        "collection_shard_index": None,
        "collection_source_tree": {
            "file_count": len(tuple((ROOT / "tests").rglob("test_*.py"))),
            "manifest_sha256": _collection_source_manifest_digest(),
        },
        "constitutional_shard_count": 32,
        "constitutional_shard_index": None,
        "constitutional_source_tree": {
            "file_count": len(tuple((ROOT / "tests" / "constitutional").glob("test_*.py"))),
            "manifest_sha256": _constitutional_source_manifest_digest(),
        },
        "phases": ["pytest_execution_shards"],
        "python_version": "3.test",
        "node_version": None,
        "timestamp": "2026-01-01T00:00:00+00:00",
        "repo_root": str(ROOT),
        "output_path": str(path),
        "steps": [
            {
                "name": f"pytest_execution_{index:02d}_of_{count:02d}",
                "command": list(command),
                "cwd": ".",
                "exit_code": exit_code,
                "timed_out": timed_out,
                "duration_seconds": 1.0,
                "stdout_tail": "2 passed in 0.10s",
                "stderr_tail": "",
            }
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_complete_pytest_execution_summary(tmp_path: Path, *, shard_count: int = 5) -> tuple[Path, list[Path]]:
    plan = _pytest_execution_shard_plan("python", shard_count=shard_count)
    report_paths = []
    for index, (_name, command, _cwd) in enumerate(plan.steps, start=1):
        path = tmp_path / f"pytest_execution_shard_{index}.json"
        _write_fake_pytest_execution_report(path, index=index, count=shard_count, command=command)
        report_paths.append(path)
    summary = tmp_path / "pytest_execution_shards_summary.json"
    payload = _aggregate_pytest_execution_shard_reports(report_paths, expected_shard_count=shard_count, output_path=summary)
    assert payload["status"] == "PASS"
    return summary, report_paths


def test_pytest_execution_shard_report_aggregation_requires_complete_passing_set(tmp_path) -> None:
    import json

    summary, _reports = _write_complete_pytest_execution_summary(tmp_path, shard_count=5)
    payload = json.loads(summary.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "certification_stability_pytest_execution_summary/v1"
    assert payload["status"] == "PASS"
    assert payload["pytest_shard_count"] == 5
    assert payload["missing_shard_indexes"] == []
    assert payload["blockers"] == []
    assert payload["expected_pytest_execution_test_file_count"] == len(tuple((ROOT / "tests").rglob("test_*.py")))
    assert payload["expected_pytest_execution_test_file_count"] == payload["covered_pytest_execution_test_file_count"]
    assert payload["pytest_execution_source_tree"]["manifest_sha256"] == _pytest_execution_source_manifest_digest()
    assert payload["total_test_count"] >= 10
    assert payload["total_duration_seconds"] == 5.0
    assert payload["source_reports_sha256"]
    assert payload["summary_payload_sha256"] == _summary_payload_digest(payload)


def test_pytest_execution_summary_verification_accepts_complete_summary(tmp_path) -> None:
    summary, _reports = _write_complete_pytest_execution_summary(tmp_path, shard_count=5)

    verification = _verify_pytest_execution_summary_report(summary, output_path=tmp_path / "pytest_execution_verification.json")

    assert verification["schema_version"] == "certification_stability_pytest_execution_summary_verification/v1"
    assert verification["status"] == "PASS"
    assert verification["blockers"] == []
    assert (tmp_path / "pytest_execution_verification.json").exists()


def test_pytest_execution_summary_verification_blocks_source_report_tampering(tmp_path) -> None:
    import json

    summary, reports = _write_complete_pytest_execution_summary(tmp_path, shard_count=5)
    report_payload = json.loads(reports[0].read_text(encoding="utf-8"))
    report_payload["status"] = "FAIL"
    reports[0].write_text(json.dumps(report_payload, indent=2, sort_keys=True), encoding="utf-8")

    verification = _verify_pytest_execution_summary_report(summary, output_path=tmp_path / "pytest_execution_verification.json")

    assert verification["status"] == "FAIL"
    assert verification["source_report_mismatch_count"] == 1
    blockers = "\n".join(verification["blockers"])
    assert "PYTEST_EXECUTION_SUMMARY_SOURCE_REPORT_SHA256_MISMATCH" in blockers


def test_pytest_execution_aggregation_emits_exact_failed_shard_blockers(tmp_path) -> None:
    import json

    plan = _pytest_execution_shard_plan("python", shard_count=5)
    reports = []
    for index, (_name, command, _cwd) in enumerate(plan.steps, start=1):
        path = tmp_path / f"pytest_execution_shard_{index}.json"
        if index == 3:
            _write_fake_pytest_execution_report(
                path,
                index=index,
                count=5,
                command=command,
                status="FAIL",
                exit_code=124,
                timed_out=True,
            )
        else:
            _write_fake_pytest_execution_report(path, index=index, count=5, command=command)
        reports.append(path)

    summary = tmp_path / "pytest_execution_shards_summary.json"
    payload = _aggregate_pytest_execution_shard_reports(reports, expected_shard_count=5, output_path=summary)

    assert payload["status"] == "FAIL"
    assert payload["failed_shard_count"] == 1
    assert payload["timed_out_shard_count"] == 1
    assert payload["nonzero_shard_count"] == 1
    assert payload["first_failed_shard"]["shard_index"] == 3
    assert payload["first_failed_shard"]["timed_out"] is True
    assert "--pytest-shard-index" in payload["next_diagnostic"]
    blockers = "\n".join(payload["blockers"])
    assert "PYTEST_EXECUTION_SHARD_TIMED_OUT" in blockers
    assert "PYTEST_EXECUTION_SHARD_NONZERO_EXIT" in blockers

    persisted = json.loads(summary.read_text(encoding="utf-8"))
    assert persisted["failed_pytest_execution_shards"][0]["timeout_seconds"] == 120


def test_pytest_execution_summary_verification_requires_exact_blocker_fields(tmp_path) -> None:
    import json

    summary, _reports = _write_complete_pytest_execution_summary(tmp_path, shard_count=5)
    payload = json.loads(summary.read_text(encoding="utf-8"))
    payload.pop("failed_shard_count")
    payload["summary_payload_sha256"] = _summary_payload_digest(payload)
    summary.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    verification = _verify_pytest_execution_summary_report(summary, output_path=tmp_path / "pytest_execution_verification.json")

    assert verification["status"] == "FAIL"
    blockers = "\n".join(verification["blockers"])
    assert "PYTEST_EXECUTION_SUMMARY_FIELD_MISSING:failed_shard_count" in blockers


def test_local_certify_payload_embeds_pytest_execution_shard_proof_summary(tmp_path) -> None:
    from scripts.local_certify import _build_payload, validate_pytest_execution_shards_proof

    summary, _reports = _write_complete_pytest_execution_summary(tmp_path, shard_count=5)
    verification = tmp_path / "pytest_execution_shards_summary_verification.json"
    _verify_pytest_execution_summary_report(summary, output_path=verification)

    proof, blockers = validate_pytest_execution_shards_proof(summary, verification)
    assert blockers == []
    assert proof is not None
    _results, python_summary, public_summary, package_summary, _public_report, _package_report = _base_local_certify_results_and_proofs(tmp_path)

    payload = _build_payload(
        results=[],
        failed=None,
        frontend_included=False,
        pytest_execution_shards_included=True,
        pytest_shard_count=5,
        pytest_execution_shards_proof=proof,
        python_core_report=python_summary,
        public_surface_dashboard=public_summary,
        package_repo_check=package_summary,
    )

    assert payload["schema_version"] == "local_certify/v5"
    assert payload["pytest_execution_shards_proof"] == proof
    assert payload["pytest_execution_shards_proof"]["path"] == payload["pytest_execution_shards_proof"]["summary_path"]
    assert payload["pytest_execution_shards_proof"]["sha256"] == payload["pytest_execution_shards_proof"]["summary_sha256"]
    assert payload["pytest_execution_shards_proof"]["schema_version"] == "certification_stability_pytest_execution_summary/v1"
    assert payload["pytest_execution_shards_proof"]["source_tree_digest"]
    assert payload["pytest_execution_shards_proof"]["created_at"]
    assert payload["pytest_execution_shards_proof"]["verified_at"]
    assert payload["pytest_execution_shards_proof"]["verification_sha256"]


def test_local_certify_report_verification_blocks_pytest_execution_summary_tampering(tmp_path) -> None:
    import json
    from scripts.local_certify import LocalCertifyStep, _build_payload, validate_pytest_execution_shards_proof, verify_local_certify_report

    summary, _reports = _write_complete_pytest_execution_summary(tmp_path, shard_count=5)
    verification_path = tmp_path / "pytest_execution_shards_summary_verification.json"
    _verify_pytest_execution_summary_report(summary, output_path=verification_path)
    proof, blockers = validate_pytest_execution_shards_proof(summary, verification_path)
    assert blockers == []
    assert proof is not None

    base_results, python_summary, public_summary, package_summary, _public_report, _package_report = _base_local_certify_results_and_proofs(tmp_path)
    pytest_names = [f"pytest_execution_shard_{index:02d}_of_05" for index in range(1, 6)]
    pytest_names.extend(["pytest_execution_shards_summary", "pytest_execution_shards_summary_verification", "pytest_execution_shards_report_validation"])
    results = [
        LocalCertifyStep(
            name=name,
            command=("python", name),
            cwd=".",
            exit_code=0,
            duration_seconds=0.01,
            stdout_tail="",
            stderr_tail="",
        )
        for name in pytest_names
    ]
    results = [*base_results, *results]
    payload = _build_payload(
        results=results,
        failed=None,
        frontend_included=False,
        pytest_execution_shards_included=True,
        pytest_shard_count=5,
        pytest_execution_shards_proof=proof,
        python_core_report=python_summary,
        public_surface_dashboard=public_summary,
        package_repo_check=package_summary,
    )
    report = tmp_path / "local_certify_report.json"
    report.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    tampered = json.loads(summary.read_text(encoding="utf-8"))
    tampered["status"] = "FAIL"
    summary.write_text(json.dumps(tampered, indent=2, sort_keys=True), encoding="utf-8")

    verification = verify_local_certify_report(report)

    assert verification["status"] == "FAIL"
    blockers_text = "\n".join(verification["blockers"])
    assert "LOCAL_CERTIFY_PYTEST_EXECUTION_SHARDS_PROOF_SUMMARY_SHA256_MISMATCH" in blockers_text


def test_public_surface_dashboard_doc_is_current(capsys) -> None:
    from scripts.public_surface_dashboard import main as public_surface_dashboard_main

    doc = ROOT / "docs" / "audits" / "public_surface_dashboard.md"
    code = public_surface_dashboard_main(["--check-doc", str(doc)])

    assert code == 0
    assert "public_surface_dashboard_doc: current" in capsys.readouterr().out



def test_frontend_certify_report_negative_matrix_blocks_malformed_reports(tmp_path) -> None:
    import json
    from scripts.local_certify import validate_frontend_certify_report

    required_steps = ("contract_check", "lint", "typecheck", "test", "acceptance", "build", "audit")

    def write_report(name: str, **overrides):
        path = tmp_path / f"{name}.json"
        payload = _frontend_report_payload(path)
        payload.update(overrides)
        if overrides.get("__raw_text") is not None:
            path.write_text(str(overrides["__raw_text"]), encoding="utf-8")
        else:
            payload.pop("__raw_text", None)
            path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

    cases = [
        ("missing_required_step", {"steps": [_frontend_step("contract_check")]}, "FRONTEND_CERTIFY_REPORT_REQUIRED_STEPS_MISSING"),
        (
            "duplicate_step",
            {"steps": [_frontend_step(step) for step in (*required_steps, "audit")]},
            "FRONTEND_CERTIFY_REPORT_DUPLICATE_STEPS:audit",
        ),
        (
            "unexpected_step",
            {"steps": [_frontend_step(step) for step in (*required_steps, "storybook")]},
            "FRONTEND_CERTIFY_REPORT_UNEXPECTED_STEPS:storybook",
        ),
        (
            "nonzero_step",
            {"steps": [_frontend_step(step, exit_code=1 if step == "lint" else 0) for step in required_steps]},
            "FRONTEND_CERTIFY_REPORT_NONZERO_STEPS:lint:1",
        ),
        ("wrong_schema", {"schema_version": "frontend_certify/v0"}, "FRONTEND_CERTIFY_REPORT_SCHEMA_UNEXPECTED"),
        ("invalid_json", {"__raw_text": "{"}, "FRONTEND_CERTIFY_REPORT_INVALID_JSON"),
        ("report_path_mismatch", {"report_path": str(tmp_path / "other.json")}, "FRONTEND_CERTIFY_REPORT_PATH_MISMATCH"),
        (
            "time_range_invalid",
            {"started_at": "2026-01-01T00:02:00+00:00", "finished_at": "2026-01-01T00:01:00+00:00"},
            "FRONTEND_CERTIFY_REPORT_TIME_RANGE_INVALID",
        ),
    ]

    for name, overrides, expected in cases:
        path = write_report(name, **overrides)
        _summary, blockers = validate_frontend_certify_report(path)
        assert any(expected in blocker for blocker in blockers), (name, blockers)

    missing_timeout_path = write_report(
        "missing_timeout_field",
        steps=[{key: value for key, value in _frontend_step(step).items() if key != "timeout_seconds"} for step in required_steps],
    )
    _summary, malformed_blockers = validate_frontend_certify_report(missing_timeout_path)
    assert any("FRONTEND_CERTIFY_REPORT_STEP_FIELDS_INVALID" in blocker and "timeout_seconds:missing" in blocker for blocker in malformed_blockers)

    timed_out_path = write_report(
        "timed_out_step",
        status="FAIL",
        failed_step="test",
        steps=[_frontend_step(step, exit_code=124 if step == "test" else 0, timed_out=step == "test") for step in required_steps],
    )
    _summary, timeout_blockers = validate_frontend_certify_report(timed_out_path)
    assert any("FRONTEND_CERTIFY_REPORT_TIMED_OUT_STEPS:test" in blocker for blocker in timeout_blockers)

    stale_source_path = write_report("stale_source", frontend_source_tree_digest="deadbeef")
    _summary, source_blockers = validate_frontend_certify_report(stale_source_path)
    assert any("FRONTEND_CERTIFY_REPORT_SOURCE_TREE_DIGEST_MISMATCH" in blocker for blocker in source_blockers)

    stale_path = write_report("stale", finished_at="2000-01-01T00:01:00+00:00")
    _summary, stale_blockers = validate_frontend_certify_report(stale_path, max_report_age_seconds=60)
    assert any("FRONTEND_CERTIFY_REPORT_STALE" in blocker for blocker in stale_blockers)


def test_ci_validate_job_seals_and_verifies_local_certify_report() -> None:
    ci_text = CI.read_text(encoding="utf-8")

    assert "Research-and-Paper-Discovery full local certify (validate)" in ci_text
    assert "python scripts/local_certify.py --certify-research-paper-discovery --json" in ci_text
    assert "Upload local certify report" in ci_text
    assert "python scripts/local_certify.py --verify-report artifacts/local_certify/latest/local_certify_report.json --json" in ci_text
    assert "Upload local certify report verification" in ci_text
    assert "Verify Research-and-Paper-Discovery phase profile plan (validate)" in ci_text
    assert "python scripts/local_certify.py --verify-phase-profile-plan artifacts/local_certify/latest/research_paper_discovery_profile_plan.json --json" in ci_text
    assert "Verify Research-and-Paper-Discovery closure report (validate)" in ci_text
    assert "python scripts/local_certify.py --verify-phase-closure-report artifacts/local_certify/latest/research_paper_discovery_closure_report.json --json" in ci_text
    assert "Upload Research-and-Paper-Discovery closure-report" not in ci_text  # guard against typo regression
    assert "Upload Research-and-Paper-Discovery closure report" in ci_text
    assert "Export portable Research-and-Paper-Discovery evidence bundle (validate)" in ci_text
    assert "python scripts/local_certify.py --export-phase-evidence-bundle artifacts/local_certify/latest/research_paper_discovery_evidence_bundle.json --phase-evidence-bundle-export-dir artifacts/local_certify/latest/research_paper_discovery_evidence_bundle_export --json" in ci_text
    assert "Verify portable Research-and-Paper-Discovery evidence bundle (validate)" in ci_text
    assert "Verify final Research-and-Paper-Discovery certificate (validate)" in ci_text
    assert "python scripts/local_certify.py --verify-final-phase-certificate docs/audits/final_research_paper_discovery_certification.md --json" in ci_text



def test_ci_exposes_manual_research_paper_discovery_phase_certification_job() -> None:
    ci_text = CI.read_text(encoding="utf-8")

    assert "research-paper-discovery-certification:" in ci_text
    assert "github.event_name == 'workflow_dispatch'" in ci_text
    assert "python scripts/local_certify.py --certify-research-paper-discovery --phase-profile-plan-only --json" in ci_text
    assert "python scripts/local_certify.py --certify-research-paper-discovery --json" in ci_text
    assert "python scripts/local_certify.py --verify-report artifacts/local_certify/latest/local_certify_report.json --json" in ci_text
    assert "python scripts/local_certify.py --verify-phase-closure-report artifacts/local_certify/latest/research_paper_discovery_closure_report.json --json" in ci_text
    assert "research-paper-discovery-certification" in ci_text

def test_duration_report_parser_classifies_slow_constitutional() -> None:
    from scripts.test_duration_report import parse_pytest_durations, summarize_by_file

    transcript = """
============================= slowest 3 durations =============================
12.34s call     tests/constitutional/test_anti_leakage_replay.py::TestLedgerIsolation::test_append_isolation_persists_within_test
2.00s setup    tests/application/test_example.py::test_fastish
0.50s call     tests/api/test_route.py::test_route
"""
    entries = parse_pytest_durations(transcript)

    assert entries[0].nodeid.startswith("tests/constitutional/test_anti_leakage_replay.py")
    assert entries[0].recommended_marker == "slow_constitutional"
    assert entries[0].recommended_shard_category == "constitutional_shards"
    by_file = summarize_by_file(entries)
    assert by_file[0]["file"] == "tests/constitutional/test_anti_leakage_replay.py"
    assert by_file[0]["total_duration_seconds"] == 12.34


def test_public_surface_ratchet_blocks_growth_without_rationale(tmp_path) -> None:
    import json
    from strategy_validator.application.public_surface_dashboard import build_public_surface_dashboard
    from scripts.public_surface_dashboard import validate_public_surface_ratchet

    dashboard = build_public_surface_dashboard(ROOT).to_payload()
    baselines = {}
    for metric_name, metric in dashboard["metrics"].items():
        actual = int(metric["actual"])
        baselines[metric_name] = {
            "actual": actual - 1 if metric_name == "test_files" else actual,
            "budget": int(metric["budget"]),
            "baseline_reason": "test baseline",
        }
    ratchet_path = tmp_path / "ratchet.json"
    ratchet_path.write_text(
        json.dumps(
            {
                "schema_version": "public_surface_budget_ratchet/v1",
                "policy": "test",
                "baselines": baselines,
                "approved_surface_growth": [],
                "approved_budget_increases": [],
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    validation = validate_public_surface_ratchet(dashboard, ratchet_path)

    assert validation["status"] == "FAIL"
    assert any("PUBLIC_SURFACE_GROWTH_REQUIRES_RATIONALE:test_files" in blocker for blocker in validation["blockers"])


def test_public_surface_ratchet_allows_growth_with_explicit_offset(tmp_path) -> None:
    import json
    from strategy_validator.application.public_surface_dashboard import build_public_surface_dashboard
    from scripts.public_surface_dashboard import validate_public_surface_ratchet

    dashboard = build_public_surface_dashboard(ROOT).to_payload()
    actual = int(dashboard["metrics"]["test_files"]["actual"])
    baselines = {
        metric_name: {
            "actual": int(metric["actual"]),
            "budget": int(metric["budget"]),
            "baseline_reason": "test baseline",
        }
        for metric_name, metric in dashboard["metrics"].items()
    }
    baselines["test_files"]["actual"] = actual - 1
    ratchet_path = tmp_path / "ratchet.json"
    ratchet_path.write_text(
        json.dumps(
            {
                "schema_version": "public_surface_budget_ratchet/v1",
                "policy": "test",
                "baselines": baselines,
                "approved_surface_growth": [
                    {
                        "metric": "test_files",
                        "old_actual": actual - 1,
                        "new_actual": actual,
                        "consolidation_offset": "retired obsolete duplicate test module",
                        "rationale": "New certification negative case replaces broader ad-hoc coverage.",
                    }
                ],
                "approved_budget_increases": [],
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    validation = validate_public_surface_ratchet(dashboard, ratchet_path)

    assert validation["status"] == "PASS"
    assert validation["blockers"] == []


def test_local_certify_report_verification_blocks_python_core_report_tampering(tmp_path) -> None:
    import json
    from scripts.local_certify import verify_local_certify_report

    report, _frontend = _minimal_local_certify_report(tmp_path, frontend=False)
    payload = json.loads(report.read_text(encoding="utf-8"))
    python_core_path = Path(payload["python_core_report"]["path"])
    python_core_payload = json.loads(python_core_path.read_text(encoding="utf-8"))
    python_core_payload["status"] = "FAIL"
    python_core_path.write_text(json.dumps(python_core_payload, indent=2, sort_keys=True), encoding="utf-8")

    verification = verify_local_certify_report(report)

    assert verification["status"] == "FAIL"
    blockers = "\n".join(verification["blockers"])
    assert "LOCAL_CERTIFY_PYTHON_CORE_REPORT_SHA256_MISMATCH" in blockers


def test_local_certify_file_sha256_matches_standard_sha256(tmp_path) -> None:
    import hashlib
    from scripts.local_certify import _file_sha256

    path = tmp_path / "sample.txt"
    path.write_bytes(b"certification-proof")

    assert _file_sha256(path) == hashlib.sha256(b"certification-proof").hexdigest()


def test_local_certify_can_replace_monolithic_pytest_with_execution_shards() -> None:
    from scripts.local_certify import planned_steps, planned_pytest_execution_shard_steps

    core_without_monolith = [name for name, _command, _cwd in planned_steps(include_frontend=False, include_pytest=False)]
    assert "pytest" not in core_without_monolith
    assert core_without_monolith[-1] == "package_repo_check"

    shard_steps = planned_pytest_execution_shard_steps(shard_count=2, timeout_seconds=30)
    shard_commands = [list(command) for _name, command, _cwd in shard_steps[:2]]
    assert all(command.count("pytest-execution-shards") == 1 for command in shard_commands)
    assert all("--pytest-shard-index" in command for command in shard_commands)


def test_local_certify_defers_resumable_shard_failures_to_proof_validation() -> None:
    import argparse
    from scripts.local_certify import _is_resumable_proof_step, _local_wrapper_timeout_for_step

    args = argparse.Namespace(
        collection_shard_timeout_seconds=41,
        constitutional_shard_timeout_seconds=42,
        pytest_shard_timeout_seconds=43,
        step_timeout_seconds=900,
    )

    assert _is_resumable_proof_step("pytest_execution_shard_03_of_16") is True
    assert _is_resumable_proof_step("pytest_execution_shards_summary") is True
    assert _is_resumable_proof_step("pytest_execution_shards_summary_verification") is True
    assert _is_resumable_proof_step("pytest") is False
    assert _local_wrapper_timeout_for_step("pytest_execution_shard_03_of_16", args) == 103
    assert _local_wrapper_timeout_for_step("collection_shard_01_of_16", args) == 101
    assert _local_wrapper_timeout_for_step("constitutional_shard_01_of_16", args) == 102
    assert _local_wrapper_timeout_for_step("pytest_execution_shards_summary", args) == 300


def test_local_certify_report_verification_blocks_python_core_source_tree_drift(tmp_path) -> None:
    import json
    from scripts.local_certify import verify_local_certify_report

    report, _frontend = _minimal_local_certify_report(tmp_path, frontend=False)
    payload = json.loads(report.read_text(encoding="utf-8"))
    python_core_path = Path(payload["python_core_report"]["path"])
    python_core_payload = json.loads(python_core_path.read_text(encoding="utf-8"))
    python_core_payload["source_tree_digest"] = "stale-python-core-digest"
    python_core_payload["report_payload_sha256"] = __import__("scripts.local_certify", fromlist=["_canonical_json_digest"]). _canonical_json_digest(
        {key: value for key, value in python_core_payload.items() if key != "report_payload_sha256"}
    )
    python_core_path.write_text(json.dumps(python_core_payload, indent=2, sort_keys=True), encoding="utf-8")
    payload["python_core_report"]["sha256"] = __import__("scripts.local_certify", fromlist=["_file_sha256"]). _file_sha256(python_core_path)
    payload["report_payload_sha256"] = __import__("scripts.local_certify", fromlist=["local_certify_payload_digest"]).local_certify_payload_digest(payload)
    report.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    verification = verify_local_certify_report(report)

    assert verification["status"] == "FAIL"
    blockers = "\n".join(verification["blockers"])
    assert "LOCAL_CERTIFY_PYTHON_CORE_REPORT_CURRENT_VALIDATION_FAILED" in blockers
    assert "PYTHON_CORE_REPORT_SOURCE_TREE_MISMATCH" in blockers


def _write_fake_researcher_fixture_report(tmp_path: Path) -> tuple[Path, dict[str, object]]:
    import json
    from scripts.local_certify import validate_researcher_fixture_report

    artifact_root = tmp_path / "researcher_fixture"
    certification_path = artifact_root / "researcher_certification" / "latest" / "researcher_certification_report.json"
    certification_path.parent.mkdir(parents=True, exist_ok=True)
    certification_path.write_text(
        json.dumps(
            {
                "schema_version": "researcher_certification_report/v1",
                "decision": "CERTIFIED",
                "blockers": [],
                "checks": {
                    "source_policy_present": "PASS",
                    "research_capsule_verified": "PASS",
                    "paper_evidence_consequences_complete": "PASS",
                    "paper_pass_does_not_imply_live_readiness": "PASS",
                    "no_live_broker_authority": "PASS",
                },
                "no_live_broker_authority": True,
                "read_plane_only": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    release_path = artifact_root / "research_os_release_readiness" / "latest" / "research_os_release_readiness_report.json"
    release_path.parent.mkdir(parents=True, exist_ok=True)
    release_path.write_text(json.dumps({"schema_version": "release_readiness/v1", "status": "PASS"}), encoding="utf-8")
    paper_path = artifact_root / "paper_evidence" / "latest" / "candidate_paper_evidence_evaluation.json"
    paper_path.parent.mkdir(parents=True, exist_ok=True)
    paper_path.write_text(json.dumps({"decision": "PAPER_EVIDENCE_PASSED"}), encoding="utf-8")

    report = tmp_path / "researcher_fixture_report.json"
    report.write_text(
        json.dumps(
            {
                "schema_version": "certification_stability/v2",
                "status": "PASS",
                "failed_step": None,
                "repo_root": str(ROOT),
                "output_path": str(report),
                "researcher_artifact_root": str(artifact_root),
                "phases": ["researcher_fixture"],
                "timestamp": "2026-01-01T00:00:00+00:00",
                "steps": [
                    {"name": "researcher_cycle_fixture", "command": ["python"], "cwd": ".", "exit_code": 0, "duration_seconds": 0.1, "stdout_tail": "", "stderr_tail": "", "timed_out": False},
                    {"name": "researcher_certify_fixture", "command": ["python"], "cwd": ".", "exit_code": 0, "duration_seconds": 0.1, "stdout_tail": "", "stderr_tail": "", "timed_out": False},
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    summary, blockers = validate_researcher_fixture_report(report)
    assert blockers == []
    assert summary is not None
    return report, summary


def test_local_certify_validates_researcher_fixture_report(tmp_path) -> None:
    from scripts.local_certify import validate_researcher_fixture_report

    report, _summary = _write_fake_researcher_fixture_report(tmp_path)

    summary, blockers = validate_researcher_fixture_report(report)

    assert blockers == []
    assert summary is not None
    assert summary["proof_name"] == "researcher_fixture_report"
    assert summary["status"] == "PASS"
    assert summary["certification_decision"] == "CERTIFIED"
    assert summary["paper_evidence_report_count"] == 1


def test_local_certify_blocks_researcher_fixture_live_authority(tmp_path) -> None:
    import json
    from scripts.local_certify import validate_researcher_fixture_report

    report, _summary = _write_fake_researcher_fixture_report(tmp_path)
    payload = json.loads(report.read_text(encoding="utf-8"))
    artifact_root = Path(payload["researcher_artifact_root"])
    certification_path = artifact_root / "researcher_certification" / "latest" / "researcher_certification_report.json"
    certification = json.loads(certification_path.read_text(encoding="utf-8"))
    certification["no_live_broker_authority"] = False
    certification_path.write_text(json.dumps(certification, indent=2), encoding="utf-8")

    summary, blockers = validate_researcher_fixture_report(report)

    assert summary is not None
    assert summary["status"] == "FAIL"
    assert "RESEARCHER_FIXTURE_CERTIFICATION_LIVE_AUTHORITY_NOT_DENIED" in "\n".join(blockers)


def test_local_certify_payload_embeds_researcher_fixture_report_summary(tmp_path) -> None:
    from scripts.local_certify import _build_payload

    _report, summary = _write_fake_researcher_fixture_report(tmp_path)
    payload = _build_payload(
        results=[],
        failed=None,
        frontend_included=False,
        researcher_fixture_included=True,
        researcher_fixture_report=summary,
    )

    assert payload["researcher_fixture_included"] is True
    assert payload["researcher_fixture_report"] == summary


def test_local_certify_report_verification_blocks_researcher_fixture_tampering(tmp_path) -> None:
    import json
    from scripts.local_certify import LocalCertifyStep, _build_payload, verify_local_certify_report

    researcher_report, researcher_summary = _write_fake_researcher_fixture_report(tmp_path)
    results, python_summary, public_summary, package_summary, _public_report, _package_report = _base_local_certify_results_and_proofs(tmp_path)
    results.extend(
        [
            LocalCertifyStep("researcher_fixture", ("python", "scripts/certification_stability.py"), ".", 0, 0.01, "", "", (str(researcher_report),)),
            LocalCertifyStep("researcher_fixture_report_validation", ("internal", "validate_researcher_fixture_report", str(researcher_report)), ".", 0, 0.01, "", "", (str(researcher_report),)),
        ]
    )
    payload = _build_payload(
        results=results,
        failed=None,
        frontend_included=False,
        researcher_fixture_included=True,
        researcher_fixture_report=researcher_summary,
        python_core_report=python_summary,
        public_surface_dashboard=public_summary,
        package_repo_check=package_summary,
    )
    local_report = tmp_path / "local_certify_report.json"
    local_report.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    researcher_payload = json.loads(researcher_report.read_text(encoding="utf-8"))
    researcher_payload["status"] = "FAIL"
    researcher_report.write_text(json.dumps(researcher_payload, indent=2, sort_keys=True), encoding="utf-8")

    verification = verify_local_certify_report(local_report)

    assert verification["status"] == "FAIL"
    blockers = "\n".join(verification["blockers"])
    assert "LOCAL_CERTIFY_RESEARCHER_FIXTURE_REPORT_SHA256_MISMATCH" in blockers


def test_local_certify_researcher_fixture_plan_runs_stability_fixture(tmp_path) -> None:
    from scripts.local_certify import planned_researcher_fixture_steps

    steps = planned_researcher_fixture_steps(
        artifact_root=tmp_path / "fixture",
        report_path=tmp_path / "researcher_fixture_report.json",
        timeout_seconds=123,
        heartbeat_seconds=4,
    )

    assert [name for name, _command, _cwd in steps] == ["researcher_fixture"]
    command = " ".join(steps[0][1])
    assert "scripts/certification_stability.py" in command
    assert "--phase researcher-fixture" in command
    assert "--researcher-artifact-root" in command
    assert "--timeout-seconds 123" in command
    assert "--heartbeat-seconds 4" in command
    assert "researcher_fixture_report.json" in command

def test_local_certify_clean_frontend_workspace_plan_and_validator(tmp_path) -> None:
    from scripts.clean_frontend_workspace import clean_frontend_workspace
    from scripts.local_certify import validate_frontend_clean_workspace_report

    plan = {name: " ".join(command) for name, command, _cwd in planned_steps(include_frontend=True, clean_frontend_workspace=True)}
    assert "frontend_clean_workspace" in plan
    assert "scripts/clean_frontend_workspace.py" in plan["frontend_clean_workspace"]
    assert "frontend_npm_ci" in plan
    assert "frontend_certify" in plan

    report = tmp_path / "frontend_clean_workspace_report.json"
    payload = clean_frontend_workspace(output=report, dry_run=True)
    assert payload["status"] == "PASS"
    summary, blockers = validate_frontend_clean_workspace_report(report)
    assert blockers == []
    assert summary is not None
    assert summary["proof_name"] == "frontend_clean_workspace_report"
    assert summary["status"] == "PASS"


def test_research_paper_discovery_profile_expands_required_flags() -> None:
    import argparse

    from scripts.local_certify import apply_research_paper_discovery_profile

    args = argparse.Namespace(
        certify_research_paper_discovery=True,
        clean_frontend_workspace=False,
        include_collection_shards=False,
        include_constitutional_shards=False,
        include_pytest_shards=False,
        include_researcher_fixture=False,
        no_fail_fast=False,
    )

    apply_research_paper_discovery_profile(args)

    assert args.clean_frontend_workspace is True
    assert args.include_collection_shards is True
    assert args.include_constitutional_shards is True
    assert args.include_pytest_shards is True
    assert args.include_researcher_fixture is True
    assert args.no_fail_fast is True


def test_local_certify_payload_embeds_research_paper_discovery_profile_contract() -> None:
    from scripts.local_certify import (
        RESEARCH_PAPER_DISCOVERY_PROFILE,
        RESEARCH_PAPER_DISCOVERY_PROFILE_VERSION,
        _build_payload,
        _research_paper_discovery_profile_contract,
    )

    contract = _research_paper_discovery_profile_contract(frontend_included=True)
    payload = _build_payload(
        results=[],
        failed=None,
        frontend_included=True,
        frontend_clean_workspace_included=True,
        researcher_fixture_included=True,
        collection_shards_included=True,
        collection_shard_count=16,
        constitutional_shards_included=True,
        constitutional_shard_count=16,
        pytest_execution_shards_included=True,
        pytest_shard_count=16,
        monolithic_pytest_included=False,
        pytest_execution_shards_replace_monolith=True,
        certification_profile=RESEARCH_PAPER_DISCOVERY_PROFILE,
        certification_profile_contract=contract,
    )

    assert payload["certification_profile"] == RESEARCH_PAPER_DISCOVERY_PROFILE
    assert payload["certification_profile_contract"]["schema_version"] == RESEARCH_PAPER_DISCOVERY_PROFILE_VERSION
    assert "researcher_fixture_report" in payload["certification_profile_contract"]["required_proofs"]
    assert "pytest_execution_shards_proof" in payload["certification_profile_contract"]["required_proofs"]



def test_research_paper_discovery_profile_frontend_proof_is_not_contractually_optional(tmp_path) -> None:
    from scripts.local_certify import (
        RESEARCH_PAPER_DISCOVERY_PROFILE,
        _research_paper_discovery_profile_contract,
        local_certify_payload_digest,
        verify_local_certify_report,
    )

    contract = _research_paper_discovery_profile_contract(frontend_included=False)
    assert contract["frontend_required"] is True
    assert contract["frontend_skip_allowed"] is False
    assert "frontend_clean_workspace_report" in contract["required_proofs"]
    assert "frontend_certify_report" in contract["required_proofs"]

    report = tmp_path / "local_certify_report.json"
    payload = {
        "schema_version": "local_certify/v5",
        "status": "PASS",
        "failed_step": None,
        "repo_root": str(ROOT),
        "frontend_included": False,
        "frontend_clean_workspace_included": False,
        "researcher_fixture_included": True,
        "collection_shards_included": True,
        "constitutional_shards_included": True,
        "pytest_execution_shards_included": True,
        "pytest_execution_shards_replace_monolith": True,
        "certification_profile": RESEARCH_PAPER_DISCOVERY_PROFILE,
        "certification_profile_contract": contract,
        "researcher_fixture_report": {"status": "PASS"},
        "collection_shards_proof": {"status": "PASS"},
        "constitutional_shards_proof": {"status": "PASS"},
        "pytest_execution_shards_proof": {"status": "PASS"},
        "python_core_report": {"status": "PASS"},
        "public_surface_dashboard": {"status": "PASS"},
        "package_repo_check": {"status": "PASS"},
        "steps": [],
        "step_manifest_sha256": "not-the-real-step-manifest",
    }
    payload["report_payload_sha256"] = local_certify_payload_digest(payload)
    report.write_text(__import__("json").dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    verification = verify_local_certify_report(report, output_path=tmp_path / "verification.json")

    blockers = "\n".join(verification["blockers"])
    assert verification["status"] == "FAIL"
    assert "LOCAL_CERTIFY_RESEARCH_PAPER_DISCOVERY_PROFILE_FLAG_MISMATCH:frontend_included=False:expected=True" in blockers
    assert "LOCAL_CERTIFY_RESEARCH_PAPER_DISCOVERY_PROFILE_FLAG_MISMATCH:frontend_clean_workspace_included=False:expected=True" in blockers
    assert "LOCAL_CERTIFY_RESEARCH_PAPER_DISCOVERY_PROFILE_PROOF_MISSING:frontend_clean_workspace_report" in blockers
    assert "LOCAL_CERTIFY_RESEARCH_PAPER_DISCOVERY_PROFILE_PROOF_MISSING:frontend_certify_report" in blockers

def test_local_certify_verification_blocks_incomplete_research_paper_discovery_profile(tmp_path) -> None:
    from scripts.local_certify import (
        RESEARCH_PAPER_DISCOVERY_PROFILE,
        _research_paper_discovery_profile_contract,
        local_certify_payload_digest,
        verify_local_certify_report,
    )

    report = tmp_path / "local_certify_report.json"
    payload = {
        "schema_version": "local_certify/v5",
        "status": "PASS",
        "failed_step": None,
        "repo_root": str(ROOT),
        "frontend_included": False,
        "frontend_clean_workspace_included": False,
        "researcher_fixture_included": False,
        "collection_shards_included": False,
        "constitutional_shards_included": False,
        "pytest_execution_shards_included": False,
        "pytest_execution_shards_replace_monolith": False,
        "certification_profile": RESEARCH_PAPER_DISCOVERY_PROFILE,
        "certification_profile_contract": _research_paper_discovery_profile_contract(frontend_included=False),
        "steps": [],
        "step_manifest_sha256": "not-the-real-step-manifest",
    }
    payload["report_payload_sha256"] = local_certify_payload_digest(payload)
    report.write_text(__import__("json").dumps(payload, indent=2), encoding="utf-8")

    verification = verify_local_certify_report(report, output_path=tmp_path / "verification.json")

    assert verification["status"] == "FAIL"
    blockers = "\n".join(verification["blockers"])
    assert "LOCAL_CERTIFY_RESEARCH_PAPER_DISCOVERY_PROFILE_FLAG_MISMATCH:collection_shards_included=False:expected=True" in blockers
    assert "LOCAL_CERTIFY_RESEARCH_PAPER_DISCOVERY_PROFILE_PROOF_MISSING:researcher_fixture_report" in blockers
    assert "LOCAL_CERTIFY_RESEARCH_PAPER_DISCOVERY_PROFILE_PROOF_MISSING:pytest_execution_shards_proof" in blockers



def test_research_paper_discovery_closure_report_summarizes_profile_blockers(tmp_path) -> None:
    from scripts.local_certify import (
        RESEARCH_PAPER_DISCOVERY_PROFILE,
        _research_paper_discovery_profile_contract,
        local_certify_payload_digest,
        validate_research_paper_discovery_closure_report,
        verify_local_certify_report,
        write_research_paper_discovery_closure_report,
    )

    report = tmp_path / "local_certify_report.json"
    verification_path = tmp_path / "local_certify_report_verification.json"
    closure_path = tmp_path / "research_paper_discovery_closure_report.json"
    payload = {
        "schema_version": "local_certify/v5",
        "status": "PASS",
        "failed_step": None,
        "repo_root": str(ROOT),
        "certification_run_id": "test-certification-run-closure-summarizes",
        "frontend_included": False,
        "frontend_clean_workspace_included": False,
        "researcher_fixture_included": False,
        "collection_shards_included": False,
        "constitutional_shards_included": False,
        "pytest_execution_shards_included": False,
        "pytest_execution_shards_replace_monolith": False,
        "certification_profile": RESEARCH_PAPER_DISCOVERY_PROFILE,
        "certification_profile_contract": _research_paper_discovery_profile_contract(frontend_included=False),
        "steps": [],
        "step_manifest_sha256": "not-the-real-step-manifest",
    }
    payload["report_payload_sha256"] = local_certify_payload_digest(payload)
    report.write_text(__import__("json").dumps(payload, indent=2), encoding="utf-8")

    verification = verify_local_certify_report(report, output_path=verification_path)
    closure = write_research_paper_discovery_closure_report(
        payload,
        verification,
        output_path=closure_path,
        report_path=report,
        verification_path=verification_path,
    )

    assert closure["status"] == "FAIL"
    blockers = "\n".join(closure["blockers"])
    assert "RESEARCH_PAPER_DISCOVERY_CLOSURE_LOCAL_CERTIFY_VERIFICATION_NOT_PASSING:FAIL" in blockers
    assert "RESEARCH_PAPER_DISCOVERY_CLOSURE_PROOF_MISSING:researcher_fixture_report" in blockers
    assert "pytest_execution_shards_proof" in closure["failed_proofs"]
    assert "inspect required proof" in closure["next_diagnostic"]

    closure_payload, closure_blockers = validate_research_paper_discovery_closure_report(closure_path)
    assert closure_blockers == []
    assert closure_payload is not None
    assert closure_payload["status"] == "FAIL"


def test_research_paper_discovery_closure_report_validation_detects_referenced_report_tampering(tmp_path) -> None:
    from scripts.local_certify import (
        RESEARCH_PAPER_DISCOVERY_PROFILE,
        _research_paper_discovery_profile_contract,
        local_certify_payload_digest,
        validate_research_paper_discovery_closure_report,
        verify_local_certify_report,
        write_research_paper_discovery_closure_report,
    )

    report = tmp_path / "local_certify_report.json"
    verification_path = tmp_path / "local_certify_report_verification.json"
    closure_path = tmp_path / "research_paper_discovery_closure_report.json"
    payload = {
        "schema_version": "local_certify/v5",
        "status": "PASS",
        "failed_step": None,
        "repo_root": str(ROOT),
        "certification_run_id": "test-certification-run-closure-tamper",
        "frontend_included": False,
        "frontend_clean_workspace_included": False,
        "researcher_fixture_included": False,
        "collection_shards_included": False,
        "constitutional_shards_included": False,
        "pytest_execution_shards_included": False,
        "pytest_execution_shards_replace_monolith": False,
        "certification_profile": RESEARCH_PAPER_DISCOVERY_PROFILE,
        "certification_profile_contract": _research_paper_discovery_profile_contract(frontend_included=False),
        "steps": [],
        "step_manifest_sha256": "not-the-real-step-manifest",
    }
    payload["report_payload_sha256"] = local_certify_payload_digest(payload)
    report.write_text(__import__("json").dumps(payload, indent=2), encoding="utf-8")
    verification = verify_local_certify_report(report, output_path=verification_path)
    write_research_paper_discovery_closure_report(
        payload,
        verification,
        output_path=closure_path,
        report_path=report,
        verification_path=verification_path,
    )

    report.write_text(report.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    _closure_payload, closure_blockers = validate_research_paper_discovery_closure_report(closure_path)

    assert any(
        blocker.startswith("RESEARCH_PAPER_DISCOVERY_CLOSURE_LOCAL_CERTIFY_REPORT_SHA256_MISMATCH")
        for blocker in closure_blockers
    )


def test_research_paper_discovery_closure_validation_detects_nested_proof_tampering(tmp_path) -> None:
    import json
    from scripts.local_certify import (
        RESEARCH_PAPER_DISCOVERY_CLOSURE_SCHEMA_VERSION,
        RESEARCH_PAPER_DISCOVERY_PROFILE,
        _file_sha256,
        _python_core_source_tree_digest,
        validate_research_paper_discovery_closure_report,
    )

    local_report = tmp_path / "local_certify_report.json"
    local_report.write_text("{\n  \"status\": \"PASS\"\n}\n", encoding="utf-8")
    verification_report = tmp_path / "local_certify_report_verification.json"
    verification_report.write_text("{\n  \"status\": \"PASS\"\n}\n", encoding="utf-8")
    proof_report = tmp_path / "python_core_report.json"
    proof_report.write_text(
        "{\n  \"schema_version\": \"python_core_report/v1\",\n  \"status\": \"PASS\"\n}\n",
        encoding="utf-8",
    )
    closure_path = tmp_path / "research_paper_discovery_closure_report.json"
    closure_payload = {
        "schema_version": RESEARCH_PAPER_DISCOVERY_CLOSURE_SCHEMA_VERSION,
        "status": "PASS",
        "phase": RESEARCH_PAPER_DISCOVERY_PROFILE,
        "certification_profile": RESEARCH_PAPER_DISCOVERY_PROFILE,
        "certification_run_id": "unit_test_certification_run_id_01",
        "local_certify_status": "PASS",
        "local_certify_failed_step": None,
        "local_certify_report_path": str(local_report),
        "local_certify_report_sha256": _file_sha256(local_report),
        "local_certify_verification_status": "PASS",
        "local_certify_verification_path": str(verification_report),
        "local_certify_verification_sha256": _file_sha256(verification_report),
        "required_proofs": [
            {
                "proof_name": "python_core_report",
                "present": True,
                "status": "PASS",
                "schema_version": "python_core_report/v1",
                "path": str(proof_report),
                "sha256": _file_sha256(proof_report),
                "source_tree_digest": "unit-test",
                "summary_status": "PASS",
                "verification_status": "PASS",
            }
        ],
        "required_proof_count": 1,
        "failed_proofs": [],
        "blocker_count": 0,
        "blockers": [],
        "next_diagnostic": None,
        "generated_at": "2026-01-01T00:00:00+00:00",
        "source_tree_digest": _python_core_source_tree_digest(),
        "no_live_authority_assertion": True,
        "paper_live_firewall_assertion": True,
        "repo_root": str(ROOT),
    }
    closure_path.write_text(json.dumps(closure_payload, indent=2, sort_keys=True), encoding="utf-8")

    _payload, blockers = validate_research_paper_discovery_closure_report(closure_path)
    assert blockers == []

    proof_report.write_text(proof_report.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    _payload, blockers = validate_research_paper_discovery_closure_report(closure_path)

    assert any(
        blocker.startswith("RESEARCH_PAPER_DISCOVERY_CLOSURE_PROOF_SHA256_MISMATCH:python_core_report")
        for blocker in blockers
    )


def _write_minimal_pass_phase_closure_inputs(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    import json
    from scripts.local_certify import (
        RESEARCH_PAPER_DISCOVERY_CLOSURE_SCHEMA_VERSION,
        RESEARCH_PAPER_DISCOVERY_PROFILE,
        _file_sha256,
        _python_core_source_tree_digest,
        validate_research_paper_discovery_closure_report,
    )

    local_report = tmp_path / "local_certify_report.json"
    local_report.write_text(
        json.dumps(
            {
                "schema_version": "local_certify/v5",
                "status": "PASS",
                "certification_run_id": "unit_test_certification_run_id_01",
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    verification_report = tmp_path / "local_certify_report_verification.json"
    verification_report.write_text(
        json.dumps({"schema_version": "local_certify_report_verification/v1", "status": "PASS"}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    proof_report = tmp_path / "python_core_report.json"
    proof_report.write_text(
        json.dumps({"schema_version": "python_core_report/v1", "status": "PASS"}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    closure_path = tmp_path / "research_paper_discovery_closure_report.json"
    closure_payload = {
        "schema_version": RESEARCH_PAPER_DISCOVERY_CLOSURE_SCHEMA_VERSION,
        "status": "PASS",
        "phase": RESEARCH_PAPER_DISCOVERY_PROFILE,
        "certification_profile": RESEARCH_PAPER_DISCOVERY_PROFILE,
        "certification_run_id": "unit_test_certification_run_id_01",
        "local_certify_status": "PASS",
        "local_certify_failed_step": None,
        "local_certify_report_path": str(local_report),
        "local_certify_report_sha256": _file_sha256(local_report),
        "local_certify_verification_status": "PASS",
        "local_certify_verification_path": str(verification_report),
        "local_certify_verification_sha256": _file_sha256(verification_report),
        "required_proofs": [
            {
                "proof_name": "python_core_report",
                "present": True,
                "status": "PASS",
                "schema_version": "python_core_report/v1",
                "path": str(proof_report),
                "sha256": _file_sha256(proof_report),
                "source_tree_digest": "unit-test",
                "summary_status": "PASS",
                "verification_status": "PASS",
            }
        ],
        "required_proof_count": 1,
        "failed_proofs": [],
        "blocker_count": 0,
        "blockers": [],
        "next_diagnostic": None,
        "generated_at": "2026-01-01T00:00:00+00:00",
        "source_tree_digest": _python_core_source_tree_digest(),
        "no_live_authority_assertion": True,
        "paper_live_firewall_assertion": True,
        "repo_root": str(ROOT),
    }
    closure_path.write_text(json.dumps(closure_payload, indent=2, sort_keys=True), encoding="utf-8")
    _payload, blockers = validate_research_paper_discovery_closure_report(closure_path)
    assert blockers == []
    return local_report, verification_report, closure_path, proof_report


def test_research_paper_discovery_evidence_bundle_inventory_and_verification(tmp_path) -> None:
    from scripts.local_certify import (
        validate_research_paper_discovery_evidence_bundle,
        write_research_paper_discovery_evidence_bundle,
    )

    local_report, verification_report, closure_path, _proof_report = _write_minimal_pass_phase_closure_inputs(tmp_path)
    bundle_path = tmp_path / "research_paper_discovery_evidence_bundle.json"

    bundle = write_research_paper_discovery_evidence_bundle(
        local_report_path=local_report,
        verification_path=verification_report,
        closure_path=closure_path,
        output_path=bundle_path,
    )

    assert bundle["schema_version"] == "research_paper_discovery_evidence_bundle/v1"
    assert bundle["status"] == "PASS"
    assert bundle["artifact_count"] == 4
    assert {artifact["proof_name"] for artifact in bundle["artifacts"]} == {
        "local_certify_report",
        "local_certify_report_verification",
        "research_paper_discovery_closure_report",
        "python_core_report",
    }

    payload, blockers = validate_research_paper_discovery_evidence_bundle(bundle_path)
    assert blockers == []
    assert payload is not None
    assert payload["status"] == "PASS"


def test_research_paper_discovery_evidence_bundle_records_generation_provenance(tmp_path) -> None:
    from scripts.local_certify import (
        RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PROVENANCE_SCHEMA_VERSION,
        RESEARCH_PAPER_DISCOVERY_PROFILE,
        write_research_paper_discovery_evidence_bundle,
        validate_research_paper_discovery_evidence_bundle,
    )

    local_report, verification_report, closure_path, _proof_report = _write_minimal_pass_phase_closure_inputs(tmp_path)
    bundle_path = tmp_path / "research_paper_discovery_evidence_bundle.json"
    bundle = write_research_paper_discovery_evidence_bundle(
        local_report_path=local_report,
        verification_path=verification_report,
        closure_path=closure_path,
        output_path=bundle_path,
    )

    provenance = bundle["provenance"]
    assert provenance["schema_version"] == RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PROVENANCE_SCHEMA_VERSION
    assert provenance["phase"] == RESEARCH_PAPER_DISCOVERY_PROFILE
    assert provenance["generated_by"] == "scripts/local_certify.py"
    assert provenance["artifact_count"] == bundle["artifact_count"]
    assert provenance["artifact_manifest_sha256"]
    assert provenance["local_certify_report_sha256"]
    assert provenance["phase_closure_report_sha256"]

    payload, blockers = validate_research_paper_discovery_evidence_bundle(bundle_path)
    assert blockers == []
    assert payload is not None


def test_research_paper_discovery_evidence_bundle_writes_and_verifies_deterministic_seal(tmp_path) -> None:
    from scripts.local_certify import (
        RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_SCHEMA_VERSION,
        _evidence_bundle_seal_path_for,
        validate_research_paper_discovery_evidence_bundle,
        validate_research_paper_discovery_evidence_bundle_seal,
        write_research_paper_discovery_evidence_bundle,
    )

    local_report, verification_report, closure_path, _proof_report = _write_minimal_pass_phase_closure_inputs(tmp_path)
    bundle_path = tmp_path / "research_paper_discovery_evidence_bundle.json"
    write_research_paper_discovery_evidence_bundle(
        local_report_path=local_report,
        verification_path=verification_report,
        closure_path=closure_path,
        output_path=bundle_path,
    )

    seal_path = _evidence_bundle_seal_path_for(bundle_path)
    assert seal_path.exists()
    seal_payload, seal_blockers = validate_research_paper_discovery_evidence_bundle_seal(seal_path, bundle_path=bundle_path)
    assert seal_blockers == []
    assert seal_payload is not None
    assert seal_payload["schema_version"] == RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_SCHEMA_VERSION
    assert seal_payload["status"] == "PASS"
    assert seal_payload["seal_kind"] == "UNSIGNED_DETERMINISTIC_ATTESTATION"
    assert seal_payload["subject"]["bundle_sha256"]
    assert seal_payload["subject_sha256"]
    assert seal_payload["seal_payload_sha256"]

    bundle_payload, bundle_blockers = validate_research_paper_discovery_evidence_bundle(bundle_path)
    assert bundle_blockers == []
    assert bundle_payload is not None


def test_research_paper_discovery_evidence_bundle_validation_detects_seal_tampering(tmp_path) -> None:
    import json
    from scripts.local_certify import (
        _evidence_bundle_seal_path_for,
        validate_research_paper_discovery_evidence_bundle,
        write_research_paper_discovery_evidence_bundle,
    )

    local_report, verification_report, closure_path, _proof_report = _write_minimal_pass_phase_closure_inputs(tmp_path)
    bundle_path = tmp_path / "research_paper_discovery_evidence_bundle.json"
    write_research_paper_discovery_evidence_bundle(
        local_report_path=local_report,
        verification_path=verification_report,
        closure_path=closure_path,
        output_path=bundle_path,
    )

    seal_path = _evidence_bundle_seal_path_for(bundle_path)
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    seal["subject"]["bundle_manifest_sha256"] = "tampered"
    seal_path.write_text(json.dumps(seal, indent=2, sort_keys=True), encoding="utf-8")

    _payload, blockers = validate_research_paper_discovery_evidence_bundle(bundle_path)

    joined = "\n".join(blockers)
    assert "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL:" in joined
    assert "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_PAYLOAD_DIGEST_MISMATCH" in joined




def test_research_paper_discovery_evidence_bundle_validation_detects_resealed_missing_seal_subject_field(tmp_path) -> None:
    import json
    from scripts.local_certify import (
        _canonical_json_digest,
        _evidence_bundle_seal_path_for,
        validate_research_paper_discovery_evidence_bundle,
        write_research_paper_discovery_evidence_bundle,
    )

    local_report, verification_report, closure_path, _proof_report = _write_minimal_pass_phase_closure_inputs(tmp_path)
    bundle_path = tmp_path / "research_paper_discovery_evidence_bundle.json"
    write_research_paper_discovery_evidence_bundle(
        local_report_path=local_report,
        verification_path=verification_report,
        closure_path=closure_path,
        output_path=bundle_path,
    )

    seal_path = _evidence_bundle_seal_path_for(bundle_path)
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    seal["subject"].pop("required_artifact_proof_names_sha256")
    seal["subject_sha256"] = _canonical_json_digest(seal["subject"])
    seal["seal_payload_sha256"] = _canonical_json_digest(
        {key: value for key, value in seal.items() if key != "seal_payload_sha256"}
    )
    seal_path.write_text(json.dumps(seal, indent=2, sort_keys=True), encoding="utf-8")

    _payload, blockers = validate_research_paper_discovery_evidence_bundle(bundle_path)

    assert any(
        "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_SUBJECT_FIELD_MISSING:required_artifact_proof_names_sha256"
        in blocker
        for blocker in blockers
    )


def test_research_paper_discovery_evidence_bundle_validation_detects_resealed_seal_phase_mismatch(tmp_path) -> None:
    import json
    from scripts.local_certify import (
        _canonical_json_digest,
        _evidence_bundle_seal_path_for,
        validate_research_paper_discovery_evidence_bundle,
        write_research_paper_discovery_evidence_bundle,
    )

    local_report, verification_report, closure_path, _proof_report = _write_minimal_pass_phase_closure_inputs(tmp_path)
    bundle_path = tmp_path / "research_paper_discovery_evidence_bundle.json"
    write_research_paper_discovery_evidence_bundle(
        local_report_path=local_report,
        verification_path=verification_report,
        closure_path=closure_path,
        output_path=bundle_path,
    )

    seal_path = _evidence_bundle_seal_path_for(bundle_path)
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    seal["phase"] = "LIVE_TRADING"
    seal["subject"]["phase"] = "LIVE_TRADING"
    seal["subject_sha256"] = _canonical_json_digest(seal["subject"])
    seal["seal_payload_sha256"] = _canonical_json_digest(
        {key: value for key, value in seal.items() if key != "seal_payload_sha256"}
    )
    seal_path.write_text(json.dumps(seal, indent=2, sort_keys=True), encoding="utf-8")

    _payload, blockers = validate_research_paper_discovery_evidence_bundle(bundle_path)
    joined = "\n".join(blockers)

    assert "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_PHASE_UNEXPECTED:LIVE_TRADING" in joined
    assert "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_SUBJECT_PHASE_UNEXPECTED:LIVE_TRADING" in joined


def test_research_paper_discovery_evidence_bundle_export_detects_resealed_portable_seal_absolute_path(tmp_path) -> None:
    import json
    from scripts.local_certify import (
        _canonical_json_digest,
        _evidence_bundle_seal_path_for,
        export_research_paper_discovery_evidence_bundle,
        validate_research_paper_discovery_evidence_bundle,
        write_research_paper_discovery_evidence_bundle,
    )

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    local_report, verification_report, closure_path, _proof_report = _write_minimal_pass_phase_closure_inputs(source_dir)
    bundle_path = source_dir / "research_paper_discovery_evidence_bundle.json"
    write_research_paper_discovery_evidence_bundle(
        local_report_path=local_report,
        verification_path=verification_report,
        closure_path=closure_path,
        output_path=bundle_path,
    )
    export_dir = tmp_path / "exported"
    _exported, export_blockers = export_research_paper_discovery_evidence_bundle(
        bundle_path=bundle_path,
        export_dir=export_dir,
    )
    assert export_blockers == []

    portable_manifest = export_dir / "research_paper_discovery_evidence_bundle.json"
    seal_path = _evidence_bundle_seal_path_for(portable_manifest)
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    seal["subject"]["bundle_path"] = str(portable_manifest.resolve())
    seal["subject_sha256"] = _canonical_json_digest(seal["subject"])
    seal["seal_payload_sha256"] = _canonical_json_digest(
        {key: value for key, value in seal.items() if key != "seal_payload_sha256"}
    )
    seal_path.write_text(json.dumps(seal, indent=2, sort_keys=True), encoding="utf-8")

    _payload, blockers = validate_research_paper_discovery_evidence_bundle(portable_manifest)

    assert any(
        "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_PORTABLE_BUNDLE_PATH_UNSAFE" in blocker
        for blocker in blockers
    )

def test_research_paper_discovery_evidence_bundle_validation_detects_provenance_manifest_drift(tmp_path) -> None:
    import json
    from scripts.local_certify import (
        _canonical_json_digest,
        validate_research_paper_discovery_evidence_bundle,
        write_research_paper_discovery_evidence_bundle,
    )

    local_report, verification_report, closure_path, _proof_report = _write_minimal_pass_phase_closure_inputs(tmp_path)
    bundle_path = tmp_path / "research_paper_discovery_evidence_bundle.json"
    write_research_paper_discovery_evidence_bundle(
        local_report_path=local_report,
        verification_path=verification_report,
        closure_path=closure_path,
        output_path=bundle_path,
    )
    payload = json.loads(bundle_path.read_text(encoding="utf-8"))
    payload["artifacts"][0]["status"] = "FAIL"
    payload["bundle_payload_sha256"] = _canonical_json_digest(
        {k: v for k, v in payload.items() if k != "bundle_payload_sha256"}
    )
    bundle_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    _payload, blockers = validate_research_paper_discovery_evidence_bundle(bundle_path)

    joined = "\n".join(blockers)
    assert "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PROVENANCE_ARTIFACT_MANIFEST_SHA256_MISMATCH" in joined


def test_research_paper_discovery_evidence_bundle_detects_nested_artifact_tampering(tmp_path) -> None:
    import json
    from scripts.local_certify import (
        validate_research_paper_discovery_evidence_bundle,
        write_research_paper_discovery_evidence_bundle,
    )

    local_report, verification_report, closure_path, proof_report = _write_minimal_pass_phase_closure_inputs(tmp_path)
    bundle_path = tmp_path / "research_paper_discovery_evidence_bundle.json"
    write_research_paper_discovery_evidence_bundle(
        local_report_path=local_report,
        verification_path=verification_report,
        closure_path=closure_path,
        output_path=bundle_path,
    )

    payload = json.loads(proof_report.read_text(encoding="utf-8"))
    payload["status"] = "FAIL"
    proof_report.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    _payload, blockers = validate_research_paper_discovery_evidence_bundle(bundle_path)

    joined = "\n".join(blockers)
    assert "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_ARTIFACT_SHA256_MISMATCH:python_core_report" in joined
    assert "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_CLOSURE:RESEARCH_PAPER_DISCOVERY_CLOSURE_PROOF_SHA256_MISMATCH:python_core_report" in joined


def test_research_paper_discovery_evidence_bundle_tamper_matrix_phase_duplicate_and_seal_export_flag(tmp_path) -> None:
    """Negative cases emit stable, grep-friendly blocker tokens (evidence_bundle / closure / seal)."""
    import json
    from scripts.local_certify import (
        _canonical_json_digest,
        _evidence_bundle_artifact_manifest_digest,
        _evidence_bundle_seal_path_for,
        export_research_paper_discovery_evidence_bundle,
        validate_research_paper_discovery_evidence_bundle,
        write_research_paper_discovery_evidence_bundle,
    )

    local_report, verification_report, closure_path, _proof_report = _write_minimal_pass_phase_closure_inputs(tmp_path)
    bundle_path = tmp_path / "research_paper_discovery_evidence_bundle.json"
    write_research_paper_discovery_evidence_bundle(
        local_report_path=local_report,
        verification_path=verification_report,
        closure_path=closure_path,
        output_path=bundle_path,
    )

    payload = json.loads(bundle_path.read_text(encoding="utf-8"))
    payload["phase"] = "LIVE_TRADING"
    payload["bundle_payload_sha256"] = _canonical_json_digest({k: v for k, v in payload.items() if k != "bundle_payload_sha256"})
    bundle_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    _payload, phase_blockers = validate_research_paper_discovery_evidence_bundle(bundle_path)
    assert any("RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PHASE_UNEXPECTED" in b for b in phase_blockers)

    write_research_paper_discovery_evidence_bundle(
        local_report_path=local_report,
        verification_path=verification_report,
        closure_path=closure_path,
        output_path=bundle_path,
    )
    payload = json.loads(bundle_path.read_text(encoding="utf-8"))
    dup = dict(payload["artifacts"][0])
    dup["proof_name"] = payload["artifacts"][1]["proof_name"]
    payload["artifacts"].append(dup)
    payload["artifact_count"] = len(payload["artifacts"])
    payload["bundle_manifest_sha256"] = _evidence_bundle_artifact_manifest_digest(payload["artifacts"])
    payload["provenance"]["artifact_count"] = len(payload["artifacts"])
    payload["provenance"]["artifact_manifest_sha256"] = payload["bundle_manifest_sha256"]
    payload["bundle_payload_sha256"] = _canonical_json_digest({k: v for k, v in payload.items() if k != "bundle_payload_sha256"})
    bundle_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    _payload, dup_blockers = validate_research_paper_discovery_evidence_bundle(bundle_path)
    joined_dup = "\n".join(dup_blockers)
    assert "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_DUPLICATE_PROOF_NAMES" in joined_dup

    source_dir = tmp_path / "export_src"
    source_dir.mkdir()
    local_report2, verification_report2, closure_path2, _proof_report2 = _write_minimal_pass_phase_closure_inputs(source_dir)
    bundle_path2 = source_dir / "research_paper_discovery_evidence_bundle.json"
    write_research_paper_discovery_evidence_bundle(
        local_report_path=local_report2,
        verification_path=verification_report2,
        closure_path=closure_path2,
        output_path=bundle_path2,
    )
    export_dir = tmp_path / "export_out"
    _exported, export_blockers = export_research_paper_discovery_evidence_bundle(bundle_path=bundle_path2, export_dir=export_dir)
    assert export_blockers == []
    portable_manifest = export_dir / "research_paper_discovery_evidence_bundle.json"
    seal_path = _evidence_bundle_seal_path_for(portable_manifest)
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    seal["subject"]["exported"] = False
    seal["subject_sha256"] = _canonical_json_digest(seal["subject"])
    seal["seal_payload_sha256"] = _canonical_json_digest({k: v for k, v in seal.items() if k != "seal_payload_sha256"})
    seal_path.write_text(json.dumps(seal, indent=2, sort_keys=True), encoding="utf-8")
    _payload, seal_blockers = validate_research_paper_discovery_evidence_bundle(portable_manifest)
    joined_seal = "\n".join(seal_blockers)
    assert (
        "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL:RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_SUBJECT_EXPORTED_FLAG_MISMATCH"
        in joined_seal
    )


def test_ci_validates_and_uploads_research_paper_discovery_evidence_bundle() -> None:
    ci_text = CI.read_text(encoding="utf-8")
    if "--verify-phase-evidence-bundle" not in ci_text:
        pytest.skip("ci.yml does not document Research-and-Paper-Discovery evidence bundle verification")

    assert "Verify Research-and-Paper-Discovery evidence bundle (validate)" in ci_text
    assert "python scripts/local_certify.py --verify-phase-evidence-bundle artifacts/local_certify/latest/research_paper_discovery_evidence_bundle.json --json" in ci_text
    assert "research-paper-discovery-evidence-bundle" in ci_text
    assert "research_paper_discovery_evidence_bundle_seal.json" in ci_text


def test_research_paper_discovery_evidence_bundle_export_is_portable(tmp_path) -> None:
    import shutil
    from pathlib import Path
    from scripts.local_certify import (
        export_research_paper_discovery_evidence_bundle,
        validate_research_paper_discovery_evidence_bundle,
        write_research_paper_discovery_evidence_bundle,
    )

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    local_report, verification_report, closure_path, _proof_report = _write_minimal_pass_phase_closure_inputs(source_dir)
    bundle_path = source_dir / "research_paper_discovery_evidence_bundle.json"
    write_research_paper_discovery_evidence_bundle(
        local_report_path=local_report,
        verification_path=verification_report,
        closure_path=closure_path,
        output_path=bundle_path,
    )

    export_dir = tmp_path / "portable_bundle"
    exported, blockers = export_research_paper_discovery_evidence_bundle(bundle_path=bundle_path, export_dir=export_dir)

    assert blockers == []
    assert exported is not None
    assert exported["exported"] is True
    assert exported["provenance"]["exported"] is True
    assert exported["provenance"]["export_root"] == str(export_dir)
    assert exported["provenance"]["exported_from_bundle_path"] == str(bundle_path)
    assert (export_dir / "research_paper_discovery_evidence_bundle.json").exists()
    assert all(not Path(artifact["path"]).is_absolute() for artifact in exported["artifacts"])

    moved_dir = tmp_path / "moved_bundle"
    shutil.copytree(export_dir, moved_dir)
    shutil.rmtree(source_dir)

    payload, replay_blockers = validate_research_paper_discovery_evidence_bundle(
        moved_dir / "research_paper_discovery_evidence_bundle.json"
    )
    assert replay_blockers == []
    assert payload is not None
    assert payload["status"] == "PASS"


def test_research_paper_discovery_portable_bundle_passes_after_source_export_tree_renamed(tmp_path) -> None:
    """Portable verification must not depend on the original export source directory remaining in place."""
    import shutil
    from pathlib import Path
    from scripts.local_certify import (
        export_research_paper_discovery_evidence_bundle,
        validate_research_paper_discovery_evidence_bundle,
        write_research_paper_discovery_evidence_bundle,
    )

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    local_report, verification_report, closure_path, _proof_report = _write_minimal_pass_phase_closure_inputs(source_dir)
    bundle_path = source_dir / "research_paper_discovery_evidence_bundle.json"
    write_research_paper_discovery_evidence_bundle(
        local_report_path=local_report,
        verification_path=verification_report,
        closure_path=closure_path,
        output_path=bundle_path,
    )
    export_dir = tmp_path / "portable_bundle"
    exported, blockers = export_research_paper_discovery_evidence_bundle(bundle_path=bundle_path, export_dir=export_dir)
    assert blockers == []
    assert exported is not None

    moved_dir = tmp_path / "moved_bundle"
    shutil.copytree(export_dir, moved_dir)
    source_dir.rename(tmp_path / "source_hidden")

    payload, replay_blockers = validate_research_paper_discovery_evidence_bundle(
        moved_dir / "research_paper_discovery_evidence_bundle.json"
    )
    assert replay_blockers == []
    assert payload is not None
    assert payload["status"] == "PASS"
    assert all(not Path(artifact["path"]).is_absolute() for artifact in payload["artifacts"])


def test_research_paper_discovery_evidence_bundle_export_detects_portable_artifact_tampering(tmp_path) -> None:
    import json
    from scripts.local_certify import (
        export_research_paper_discovery_evidence_bundle,
        validate_research_paper_discovery_evidence_bundle,
        write_research_paper_discovery_evidence_bundle,
    )

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    local_report, verification_report, closure_path, _proof_report = _write_minimal_pass_phase_closure_inputs(source_dir)
    bundle_path = source_dir / "research_paper_discovery_evidence_bundle.json"
    write_research_paper_discovery_evidence_bundle(
        local_report_path=local_report,
        verification_path=verification_report,
        closure_path=closure_path,
        output_path=bundle_path,
    )

    export_dir = tmp_path / "portable_bundle"
    _exported, blockers = export_research_paper_discovery_evidence_bundle(bundle_path=bundle_path, export_dir=export_dir)
    assert blockers == []

    portable_manifest = export_dir / "research_paper_discovery_evidence_bundle.json"
    payload = json.loads(portable_manifest.read_text(encoding="utf-8"))
    proof_row = next(artifact for artifact in payload["artifacts"] if artifact["proof_name"] == "python_core_report")
    proof_path = export_dir / proof_row["path"]
    proof_payload = json.loads(proof_path.read_text(encoding="utf-8"))
    proof_payload["status"] = "FAIL"
    proof_path.write_text(json.dumps(proof_payload, indent=2, sort_keys=True), encoding="utf-8")

    _payload, replay_blockers = validate_research_paper_discovery_evidence_bundle(portable_manifest)
    joined = "\n".join(replay_blockers)
    assert "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_ARTIFACT_SHA256_MISMATCH:python_core_report" in joined
    assert "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_CLOSURE:RESEARCH_PAPER_DISCOVERY_CLOSURE_PROOF_SHA256_MISMATCH:python_core_report" in joined



def test_research_paper_discovery_closure_blocks_missing_phase_assertions(tmp_path) -> None:
    import json
    from scripts.local_certify import (
        _canonical_json_digest,
        validate_research_paper_discovery_closure_report,
    )

    _local_report, _verification_report, closure_path, _proof_report = _write_minimal_pass_phase_closure_inputs(tmp_path)
    payload = json.loads(closure_path.read_text(encoding="utf-8"))
    payload.pop("no_live_authority_assertion")
    payload.pop("paper_live_firewall_assertion")
    closure_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    _payload, blockers = validate_research_paper_discovery_closure_report(closure_path)

    joined = "\n".join(blockers)
    assert "RESEARCH_PAPER_DISCOVERY_CLOSURE_NO_LIVE_AUTHORITY_ASSERTION_MISSING" in joined
    assert "RESEARCH_PAPER_DISCOVERY_CLOSURE_PAPER_LIVE_FIREWALL_ASSERTION_MISSING" in joined


def test_research_paper_discovery_evidence_bundle_rejects_unknown_artifact_even_if_resealed(tmp_path) -> None:
    import json
    from scripts.local_certify import (
        _canonical_json_digest,
        _evidence_bundle_artifact_manifest_digest,
        validate_research_paper_discovery_evidence_bundle,
        write_research_paper_discovery_evidence_bundle,
    )

    local_report, verification_report, closure_path, _proof_report = _write_minimal_pass_phase_closure_inputs(tmp_path)
    bundle_path = tmp_path / "research_paper_discovery_evidence_bundle.json"
    bundle = write_research_paper_discovery_evidence_bundle(
        local_report_path=local_report,
        verification_path=verification_report,
        closure_path=closure_path,
        output_path=bundle_path,
    )
    payload = json.loads(bundle_path.read_text(encoding="utf-8"))
    extra = dict(payload["artifacts"][0])
    extra["proof_name"] = "unknown_extra_proof"
    payload["artifacts"].append(extra)
    payload["artifact_count"] = len(payload["artifacts"])
    payload["bundle_manifest_sha256"] = _evidence_bundle_artifact_manifest_digest(payload["artifacts"])
    payload["provenance"]["artifact_count"] = len(payload["artifacts"])
    payload["provenance"]["artifact_manifest_sha256"] = payload["bundle_manifest_sha256"]
    payload["bundle_payload_sha256"] = _canonical_json_digest(
        {k: v for k, v in payload.items() if k != "bundle_payload_sha256"}
    )
    bundle_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    _payload, blockers = validate_research_paper_discovery_evidence_bundle(bundle_path)

    assert any(blocker == "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_UNKNOWN_ARTIFACT:unknown_extra_proof" for blocker in blockers)


def test_research_paper_discovery_evidence_bundle_export_rejects_path_traversal_and_absolute_leakage(tmp_path) -> None:
    import json
    from scripts.local_certify import (
        _canonical_json_digest,
        _evidence_bundle_artifact_manifest_digest,
        export_research_paper_discovery_evidence_bundle,
        validate_research_paper_discovery_evidence_bundle,
        write_research_paper_discovery_evidence_bundle,
    )

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    local_report, verification_report, closure_path, _proof_report = _write_minimal_pass_phase_closure_inputs(source_dir)
    bundle_path = source_dir / "research_paper_discovery_evidence_bundle.json"
    write_research_paper_discovery_evidence_bundle(
        local_report_path=local_report,
        verification_path=verification_report,
        closure_path=closure_path,
        output_path=bundle_path,
    )
    export_dir = tmp_path / "exported"
    _exported, blockers = export_research_paper_discovery_evidence_bundle(bundle_path=bundle_path, export_dir=export_dir)
    assert blockers == []
    portable_manifest = export_dir / "research_paper_discovery_evidence_bundle.json"
    payload = json.loads(portable_manifest.read_text(encoding="utf-8"))

    payload["artifacts"][0]["path"] = "../escape.json"
    payload["bundle_manifest_sha256"] = _evidence_bundle_artifact_manifest_digest(payload["artifacts"])
    payload["provenance"]["artifact_manifest_sha256"] = payload["bundle_manifest_sha256"]
    payload["bundle_payload_sha256"] = _canonical_json_digest(
        {k: v for k, v in payload.items() if k != "bundle_payload_sha256"}
    )
    portable_manifest.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    _payload, traversal_blockers = validate_research_paper_discovery_evidence_bundle(portable_manifest)
    assert any("RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PORTABLE_ARTIFACT_PATH_UNSAFE" in b for b in traversal_blockers)

    payload["artifacts"][0]["path"] = str((export_dir / "proof_artifacts" / "absolute.json").resolve())
    payload["bundle_manifest_sha256"] = _evidence_bundle_artifact_manifest_digest(payload["artifacts"])
    payload["provenance"]["artifact_manifest_sha256"] = payload["bundle_manifest_sha256"]
    payload["bundle_payload_sha256"] = _canonical_json_digest(
        {k: v for k, v in payload.items() if k != "bundle_payload_sha256"}
    )
    portable_manifest.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    _payload, absolute_blockers = validate_research_paper_discovery_evidence_bundle(portable_manifest)
    assert any("RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PORTABLE_ARTIFACT_PATH_UNSAFE" in b for b in absolute_blockers)


def test_research_paper_discovery_moved_export_missing_artifact_does_not_fallback_to_source(tmp_path) -> None:
    import shutil
    from scripts.local_certify import (
        export_research_paper_discovery_evidence_bundle,
        validate_research_paper_discovery_evidence_bundle,
        write_research_paper_discovery_evidence_bundle,
    )

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    local_report, verification_report, closure_path, _proof_report = _write_minimal_pass_phase_closure_inputs(source_dir)
    bundle_path = source_dir / "research_paper_discovery_evidence_bundle.json"
    write_research_paper_discovery_evidence_bundle(
        local_report_path=local_report,
        verification_path=verification_report,
        closure_path=closure_path,
        output_path=bundle_path,
    )
    export_dir = tmp_path / "exported"
    _exported, blockers = export_research_paper_discovery_evidence_bundle(bundle_path=bundle_path, export_dir=export_dir)
    assert blockers == []
    moved_dir = tmp_path / "moved"
    shutil.copytree(export_dir, moved_dir)

    missing_artifact = next((moved_dir / "proof_artifacts").glob("*python_core_report*.json"))
    missing_artifact.unlink()

    _payload, replay_blockers = validate_research_paper_discovery_evidence_bundle(
        moved_dir / "research_paper_discovery_evidence_bundle.json"
    )

    joined = "\n".join(replay_blockers)
    assert "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_ARTIFACT_FILE_MISSING:python_core_report" in joined
    assert str(source_dir) not in joined



def test_research_paper_discovery_export_carries_terminal_run_reports(tmp_path, capsys) -> None:
    import json
    from scripts.local_certify import (
        export_research_paper_discovery_evidence_bundle,
        main,
        validate_research_paper_discovery_evidence_bundle,
        write_research_paper_discovery_evidence_bundle,
    )

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    local_report, verification_report, closure_path, _proof_report = _write_minimal_pass_phase_closure_inputs(source_dir)
    bundle_path = source_dir / "research_paper_discovery_evidence_bundle.json"
    write_research_paper_discovery_evidence_bundle(
        local_report_path=local_report,
        verification_path=verification_report,
        closure_path=closure_path,
        output_path=bundle_path,
    )
    phase_run_report = source_dir / "research_paper_discovery_phase_run_report.json"
    phase_run_report.write_text(
        json.dumps({"schema_version": "research_paper_discovery_phase_run/v1", "status": "PASS"}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    phase_run_verification = source_dir / "research_paper_discovery_phase_run_report_verification.json"
    phase_run_verification.write_text(
        json.dumps({"schema_version": "research_paper_discovery_phase_run_verification/v1", "status": "PASS"}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    export_dir = tmp_path / "exported"
    exported, blockers = export_research_paper_discovery_evidence_bundle(bundle_path=bundle_path, export_dir=export_dir)

    assert blockers == []
    assert exported is not None
    proof_names = {artifact["proof_name"] for artifact in exported["artifacts"]}
    assert "research_paper_discovery_phase_run_report" in proof_names
    assert "research_paper_discovery_phase_run_report_verification" in proof_names
    assert "research_paper_discovery_phase_run_report" in exported["required_artifact_proof_names"]
    assert "research_paper_discovery_phase_run_report_verification" in exported["required_artifact_proof_names"]
    assert (export_dir / "proof_artifacts").exists()
    payload, replay_blockers = validate_research_paper_discovery_evidence_bundle(
        export_dir / "research_paper_discovery_evidence_bundle.json"
    )
    assert replay_blockers == []
    assert payload is not None

    export_verification = tmp_path / "export_verification.json"
    assert main([
        "--export-phase-evidence-bundle",
        str(bundle_path),
        "--phase-evidence-bundle-export-dir",
        str(export_dir / "cli"),
        "--phase-evidence-bundle-export-verification-output",
        str(export_verification),
        "--json",
    ]) == 0
    capsys.readouterr()
    verification_payload = json.loads(export_verification.read_text(encoding="utf-8"))
    assert verification_payload["exported_phase_run_report_path"]
    assert verification_payload["exported_phase_run_report_verification_path"]

def test_research_paper_discovery_evidence_bundle_export_cli(tmp_path, capsys) -> None:
    from scripts.local_certify import main, write_research_paper_discovery_evidence_bundle

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    local_report, verification_report, closure_path, _proof_report = _write_minimal_pass_phase_closure_inputs(source_dir)
    bundle_path = source_dir / "research_paper_discovery_evidence_bundle.json"
    write_research_paper_discovery_evidence_bundle(
        local_report_path=local_report,
        verification_path=verification_report,
        closure_path=closure_path,
        output_path=bundle_path,
    )
    export_dir = tmp_path / "exported"

    code = main([
        "--export-phase-evidence-bundle",
        str(bundle_path),
        "--phase-evidence-bundle-export-dir",
        str(export_dir),
        "--json",
    ])

    assert code == 0
    assert (export_dir / "research_paper_discovery_evidence_bundle.json").exists()
    output = capsys.readouterr().out
    assert "research_paper_discovery_evidence_bundle_export/v1" in output


def test_manual_ci_exports_and_replays_portable_evidence_bundle() -> None:
    ci_text = CI.read_text(encoding="utf-8")
    if "--export-phase-evidence-bundle" not in ci_text:
        pytest.skip("ci.yml does not document portable evidence bundle export")

    assert "Export portable Research-and-Paper-Discovery evidence bundle" in ci_text
    assert "--export-phase-evidence-bundle artifacts/local_certify/latest/research_paper_discovery_evidence_bundle.json" in ci_text
    assert "Verify portable Research-and-Paper-Discovery evidence bundle" in ci_text
    assert "research_paper_discovery_evidence_bundle_export/research_paper_discovery_evidence_bundle.json" in ci_text
    assert "research_paper_discovery_closure_report_verification.json" in ci_text
    assert "research_paper_discovery_evidence_bundle_seal.json" in ci_text
    assert "research_paper_discovery_evidence_bundle_verification.json" in ci_text
    assert "research_paper_discovery_evidence_bundle_export_verification.json" in ci_text
    assert "research_paper_discovery_profile_plan.json" in ci_text
    assert "research_paper_discovery_profile_plan_verification.json" in ci_text
    assert "--verify-phase-profile-plan artifacts/local_certify/latest/research_paper_discovery_profile_plan.json" in ci_text
    assert "artifacts/local_certify/latest/research_paper_discovery_evidence_bundle_export/**" in ci_text

def test_local_certify_clean_frontend_workspace_plan_and_validator(tmp_path) -> None:
    from scripts.clean_frontend_workspace import clean_frontend_workspace
    from scripts.local_certify import validate_frontend_clean_workspace_report

    plan = {name: " ".join(command) for name, command, _cwd in planned_steps(include_frontend=True, clean_frontend_workspace=True)}
    assert "frontend_clean_workspace" in plan
    assert "scripts/clean_frontend_workspace.py" in plan["frontend_clean_workspace"]
    assert "frontend_npm_ci" in plan
    assert "frontend_certify" in plan

    report = tmp_path / "frontend_clean_workspace_report.json"
    payload = clean_frontend_workspace(output=report, dry_run=True)
    assert payload["status"] == "PASS"
    summary, blockers = validate_frontend_clean_workspace_report(report)
    assert blockers == []
    assert summary is not None
    assert summary["proof_name"] == "frontend_clean_workspace_report"
    assert summary["status"] == "PASS"


def test_phase_replay_commands_write_verification_artifacts(tmp_path, capsys) -> None:
    import json
    from scripts.local_certify import main, write_research_paper_discovery_evidence_bundle

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    local_report, verification_report, closure_path, _proof_report = _write_minimal_pass_phase_closure_inputs(source_dir)
    bundle_path = source_dir / "research_paper_discovery_evidence_bundle.json"
    write_research_paper_discovery_evidence_bundle(
        local_report_path=local_report,
        verification_path=verification_report,
        closure_path=closure_path,
        output_path=bundle_path,
    )
    closure_verification = tmp_path / "closure_verification.json"
    bundle_verification = tmp_path / "bundle_verification.json"
    export_verification = tmp_path / "export_verification.json"
    export_dir = tmp_path / "exported"

    assert main([
        "--verify-phase-closure-report",
        str(closure_path),
        "--phase-closure-verification-output",
        str(closure_verification),
        "--json",
    ]) == 0
    assert main([
        "--verify-phase-evidence-bundle",
        str(bundle_path),
        "--phase-evidence-bundle-verification-output",
        str(bundle_verification),
        "--json",
    ]) == 0
    assert main([
        "--export-phase-evidence-bundle",
        str(bundle_path),
        "--phase-evidence-bundle-export-dir",
        str(export_dir),
        "--phase-evidence-bundle-export-verification-output",
        str(export_verification),
        "--json",
    ]) == 0

    capsys.readouterr()
    closure_payload = json.loads(closure_verification.read_text(encoding="utf-8"))
    bundle_payload = json.loads(bundle_verification.read_text(encoding="utf-8"))
    export_payload = json.loads(export_verification.read_text(encoding="utf-8"))

    assert closure_payload["schema_version"] == "research_paper_discovery_closure_verification/v1"
    assert closure_payload["status"] == "PASS"
    assert bundle_payload["schema_version"] == "research_paper_discovery_evidence_bundle_verification/v1"
    assert bundle_payload["status"] == "PASS"
    assert export_payload["schema_version"] == "research_paper_discovery_evidence_bundle_export/v1"
    assert export_payload["status"] == "PASS"
    assert export_payload["exported_bundle_sha256"]
    assert export_payload["exported_bundle_seal_sha256"]
    assert (export_dir / "research_paper_discovery_evidence_bundle.json").exists()
    assert (export_dir / "research_paper_discovery_evidence_bundle_seal.json").exists()


def test_frontend_preflight_report_blocks_skip_frontend_for_phase(tmp_path) -> None:
    from scripts.local_certify import (
        FRONTEND_PREFLIGHT_REPORT_PATH,
        validate_frontend_preflight_report,
        write_frontend_preflight_report,
    )

    report = tmp_path / "frontend_preflight_report.json"
    payload = write_frontend_preflight_report(skip_frontend_requested=True, output_path=report)

    assert payload["status"] == "FAIL"
    summary, blockers = validate_frontend_preflight_report(report)
    assert summary is not None
    assert summary["proof_name"] == "frontend_preflight_report"
    assert summary["status"] == "FAIL"
    assert any("FRONTEND_PREFLIGHT_SKIP_FRONTEND_FORBIDDEN_FOR_PHASE" in blocker for blocker in blockers)
    assert FRONTEND_PREFLIGHT_REPORT_PATH.name == "frontend_preflight_report.json"


def test_research_paper_discovery_profile_fails_fast_on_frontend_preflight_skip(tmp_path) -> None:
    import json
    import subprocess
    import sys

    iso = tmp_path / "iso"
    iso.mkdir()
    plan = iso / "research_paper_discovery_profile_plan.json"
    plan_v = iso / "research_paper_discovery_profile_plan_verification.json"
    report = iso / "local_certify_report.json"
    report_v = iso / "local_certify_report_verification.json"
    preflight = iso / "frontend_preflight_report.json"
    py_core = iso / "python_core_report.json"
    closure = iso / "research_paper_discovery_closure_report.json"
    bundle = iso / "research_paper_discovery_evidence_bundle.json"
    phase_run = iso / "research_paper_discovery_phase_run_report.json"
    final_index = iso / "final_research_paper_discovery_certification_index.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/local_certify.py",
            "--certify-research-paper-discovery",
            "--skip-frontend",
            "--phase-profile-plan-output",
            str(plan),
            "--phase-profile-plan-verification-output",
            str(plan_v),
            "--local-certify-report-output",
            str(report),
            "--verification-output",
            str(report_v),
            "--frontend-preflight-report-output",
            str(preflight),
            "--python-core-report-output",
            str(py_core),
            "--phase-closure-output",
            str(closure),
            "--phase-evidence-bundle-output",
            str(bundle),
            "--phase-run-report-output",
            str(phase_run),
            "--final-phase-certificate-index-output",
            str(final_index),
            "--json",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=False,
    )

    assert result.returncode != 0
    payload = json.loads(result.stdout[result.stdout.find("{") :])
    assert payload["status"] == "FAIL"
    assert payload["failed_step"] == "frontend_preflight"
    assert payload["frontend_preflight_report"]["status"] == "FAIL"
    step_names = [step["name"] for step in payload["steps"]]
    assert step_names == ["frontend_preflight", "python_core_report_validation"]
    assert "FRONTEND_PREFLIGHT_SKIP_FRONTEND_FORBIDDEN_FOR_PHASE" in result.stderr or "FRONTEND_PREFLIGHT_SKIP_FRONTEND_FORBIDDEN_FOR_PHASE" in json.dumps(payload)



def test_research_paper_discovery_profile_plan_records_full_step_graph(tmp_path) -> None:
    import argparse

    from scripts.local_certify import (
        RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_SCHEMA_VERSION,
        build_research_paper_discovery_steps,
        validate_research_paper_discovery_profile_plan,
        write_frontend_preflight_report,
        write_research_paper_discovery_profile_plan,
    )

    args = argparse.Namespace(
        skip_frontend=False,
        clean_frontend_workspace=True,
        include_collection_shards=True,
        collection_shard_count=2,
        collection_shard_timeout_seconds=120,
        collection_shard_heartbeat_seconds=5,
        include_constitutional_shards=True,
        constitutional_shard_count=2,
        constitutional_shard_timeout_seconds=120,
        constitutional_shard_heartbeat_seconds=5,
        include_pytest_shards=True,
        pytest_shard_count=2,
        pytest_shard_timeout_seconds=180,
        pytest_shard_heartbeat_seconds=5,
        include_researcher_fixture=True,
        researcher_fixture_artifact_root=tmp_path / "researcher_fixture",
        researcher_fixture_timeout_seconds=900,
        researcher_fixture_heartbeat_seconds=10,
        run_monolithic_pytest_with_shards=False,
        step_timeout_seconds=None,
    )
    preflight_report = tmp_path / "frontend_preflight_report.json"
    preflight_payload = write_frontend_preflight_report(
        skip_frontend_requested=False,
        output_path=preflight_report,
    )
    steps = build_research_paper_discovery_steps(
        args,
        frontend_included=True,
        phase_preflight_failed=False,
    )
    plan_path = tmp_path / "research_paper_discovery_profile_plan.json"
    payload = write_research_paper_discovery_profile_plan(
        args=args,
        certification_run_id="test_run_id_0000000000000001",
        frontend_included=True,
        frontend_preflight_report={"status": "PASS", "path": str(preflight_report)},
        frontend_preflight_blockers=[],
        phase_preflight_failed=False,
        steps_to_run=steps,
        output_path=plan_path,
    )

    assert payload["schema_version"] == RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_SCHEMA_VERSION
    assert payload["status"] == "PASS"
    step_names = [step["name"] for step in payload["planned_steps"]]
    assert "frontend_clean_workspace" in step_names
    assert "frontend_npm_ci" in step_names
    assert "frontend_certify" in step_names
    assert "collection_shards_summary" in step_names
    assert "constitutional_shards_summary" in step_names
    assert "pytest_execution_shards_summary" in step_names
    assert "researcher_fixture" in step_names
    assert payload["would_run_expensive_steps"] is True
    assert payload["plan_payload_sha256"]

    summary, blockers = validate_research_paper_discovery_profile_plan(plan_path)
    assert blockers == []
    assert summary is not None
    assert summary["status"] == "PASS"
    assert preflight_payload["status"] == "PASS"


def test_research_paper_discovery_profile_plan_cli_verification_writes_artifact(tmp_path, capsys) -> None:
    import argparse
    import json

    from scripts.local_certify import (
        build_research_paper_discovery_steps,
        main as local_certify_main,
        validate_frontend_preflight_report,
        write_frontend_preflight_report,
        write_research_paper_discovery_profile_plan,
    )

    args = argparse.Namespace(
        skip_frontend=False,
        clean_frontend_workspace=True,
        include_collection_shards=True,
        collection_shard_count=2,
        collection_shard_timeout_seconds=120,
        collection_shard_heartbeat_seconds=5,
        include_constitutional_shards=True,
        constitutional_shard_count=2,
        constitutional_shard_timeout_seconds=120,
        constitutional_shard_heartbeat_seconds=5,
        include_pytest_shards=True,
        pytest_shard_count=2,
        pytest_shard_timeout_seconds=180,
        pytest_shard_heartbeat_seconds=5,
        include_researcher_fixture=True,
        researcher_fixture_artifact_root=tmp_path / "researcher_fixture",
        researcher_fixture_timeout_seconds=900,
        researcher_fixture_heartbeat_seconds=10,
        run_monolithic_pytest_with_shards=False,
        step_timeout_seconds=None,
    )
    preflight_path = tmp_path / "frontend_preflight_report.json"
    write_frontend_preflight_report(skip_frontend_requested=False, output_path=preflight_path)
    preflight_summary, blockers = validate_frontend_preflight_report(preflight_path)
    assert blockers == []
    steps = build_research_paper_discovery_steps(args, frontend_included=True, phase_preflight_failed=False)
    plan_path = tmp_path / "research_paper_discovery_profile_plan.json"
    write_research_paper_discovery_profile_plan(
        args=args,
        certification_run_id="test_run_id_0000000000000001",
        frontend_included=True,
        frontend_preflight_report=preflight_summary,
        frontend_preflight_blockers=[],
        phase_preflight_failed=False,
        steps_to_run=steps,
        output_path=plan_path,
    )
    verification_path = tmp_path / "research_paper_discovery_profile_plan_verification.json"

    code = local_certify_main([
        "--verify-phase-profile-plan",
        str(plan_path),
        "--phase-profile-plan-verification-output",
        str(verification_path),
        "--json",
    ])

    assert code == 0
    capsys.readouterr()
    payload = json.loads(verification_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "research_paper_discovery_profile_plan_verification/v1"
    assert payload["status"] == "PASS"
    assert payload["plan_sha256"]
    assert payload["plan_summary"]["status"] == "PASS"


def test_research_paper_discovery_profile_plan_verification_blocks_tampering(tmp_path) -> None:
    import argparse
    import json

    from scripts.local_certify import (
        build_research_paper_discovery_steps,
        validate_frontend_preflight_report,
        verify_research_paper_discovery_profile_plan,
        write_frontend_preflight_report,
        write_research_paper_discovery_profile_plan,
    )

    args = argparse.Namespace(
        skip_frontend=False,
        clean_frontend_workspace=True,
        include_collection_shards=True,
        collection_shard_count=2,
        collection_shard_timeout_seconds=120,
        collection_shard_heartbeat_seconds=5,
        include_constitutional_shards=True,
        constitutional_shard_count=2,
        constitutional_shard_timeout_seconds=120,
        constitutional_shard_heartbeat_seconds=5,
        include_pytest_shards=True,
        pytest_shard_count=2,
        pytest_shard_timeout_seconds=180,
        pytest_shard_heartbeat_seconds=5,
        include_researcher_fixture=True,
        researcher_fixture_artifact_root=tmp_path / "researcher_fixture",
        researcher_fixture_timeout_seconds=900,
        researcher_fixture_heartbeat_seconds=10,
        run_monolithic_pytest_with_shards=False,
        step_timeout_seconds=None,
    )
    preflight_path = tmp_path / "frontend_preflight_report.json"
    write_frontend_preflight_report(skip_frontend_requested=False, output_path=preflight_path)
    preflight_summary, blockers = validate_frontend_preflight_report(preflight_path)
    assert blockers == []
    plan_path = tmp_path / "research_paper_discovery_profile_plan.json"
    write_research_paper_discovery_profile_plan(
        args=args,
        certification_run_id="test_run_id_0000000000000001",
        frontend_included=True,
        frontend_preflight_report=preflight_summary,
        frontend_preflight_blockers=[],
        phase_preflight_failed=False,
        steps_to_run=build_research_paper_discovery_steps(args, frontend_included=True, phase_preflight_failed=False),
        output_path=plan_path,
    )
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    payload["frontend_source_tree_digest"] = "tampered"
    plan_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    verification = verify_research_paper_discovery_profile_plan(plan_path)

    assert verification["status"] == "FAIL"
    blockers_text = "\n".join(verification["blockers"])
    assert "RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_FRONTEND_SOURCE_TREE_MISMATCH" in blockers_text
    assert "RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_PAYLOAD_DIGEST_MISMATCH" in blockers_text


def test_research_paper_discovery_profile_plan_only_blocks_skip_frontend(tmp_path) -> None:
    import json
    import subprocess
    import sys

    iso = tmp_path / "iso"
    iso.mkdir()
    plan = iso / "research_paper_discovery_profile_plan.json"
    plan_v = iso / "research_paper_discovery_profile_plan_verification.json"
    preflight = iso / "frontend_preflight_report.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/local_certify.py",
            "--certify-research-paper-discovery",
            "--skip-frontend",
            "--phase-profile-plan-only",
            "--phase-profile-plan-output",
            str(plan),
            "--phase-profile-plan-verification-output",
            str(plan_v),
            "--frontend-preflight-report-output",
            str(preflight),
            "--json",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=False,
    )

    assert result.returncode != 0
    payload = json.loads(result.stdout[result.stdout.find("{") :])
    assert payload["schema_version"] == "research_paper_discovery_profile_plan/v1"
    assert payload["status"] == "FAIL"
    assert payload["phase_preflight_failed"] is True
    assert payload["planned_step_count"] == 0
    assert payload["would_run_expensive_steps"] is False
    assert "FRONTEND_PREFLIGHT_SKIP_FRONTEND_FORBIDDEN_FOR_PHASE" in json.dumps(payload)
    assert "Research-and-Paper-Discovery phase profile plan: FAIL" in result.stderr

def test_local_certify_clean_frontend_workspace_plan_and_validator(tmp_path) -> None:
    from scripts.clean_frontend_workspace import clean_frontend_workspace
    from scripts.local_certify import validate_frontend_clean_workspace_report

    plan = {name: " ".join(command) for name, command, _cwd in planned_steps(include_frontend=True, clean_frontend_workspace=True)}
    assert "frontend_clean_workspace" in plan
    assert "scripts/clean_frontend_workspace.py" in plan["frontend_clean_workspace"]
    assert "frontend_npm_ci" in plan
    assert "frontend_certify" in plan

    report = tmp_path / "frontend_clean_workspace_report.json"
    payload = clean_frontend_workspace(output=report, dry_run=True)
    assert payload["status"] == "PASS"
    summary, blockers = validate_frontend_clean_workspace_report(report)
    assert blockers == []
    assert summary is not None
    assert summary["proof_name"] == "frontend_clean_workspace_report"
    assert summary["status"] == "PASS"


def test_phase_replay_commands_write_verification_artifacts(tmp_path, capsys) -> None:
    import json
    from scripts.local_certify import main, write_research_paper_discovery_evidence_bundle

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    local_report, verification_report, closure_path, _proof_report = _write_minimal_pass_phase_closure_inputs(source_dir)
    bundle_path = source_dir / "research_paper_discovery_evidence_bundle.json"
    write_research_paper_discovery_evidence_bundle(
        local_report_path=local_report,
        verification_path=verification_report,
        closure_path=closure_path,
        output_path=bundle_path,
    )
    closure_verification = tmp_path / "closure_verification.json"
    bundle_verification = tmp_path / "bundle_verification.json"
    export_verification = tmp_path / "export_verification.json"
    export_dir = tmp_path / "exported"

    assert main([
        "--verify-phase-closure-report",
        str(closure_path),
        "--phase-closure-verification-output",
        str(closure_verification),
        "--json",
    ]) == 0
    assert main([
        "--verify-phase-evidence-bundle",
        str(bundle_path),
        "--phase-evidence-bundle-verification-output",
        str(bundle_verification),
        "--json",
    ]) == 0
    assert main([
        "--export-phase-evidence-bundle",
        str(bundle_path),
        "--phase-evidence-bundle-export-dir",
        str(export_dir),
        "--phase-evidence-bundle-export-verification-output",
        str(export_verification),
        "--json",
    ]) == 0

    capsys.readouterr()
    closure_payload = json.loads(closure_verification.read_text(encoding="utf-8"))
    bundle_payload = json.loads(bundle_verification.read_text(encoding="utf-8"))
    export_payload = json.loads(export_verification.read_text(encoding="utf-8"))

    assert closure_payload["schema_version"] == "research_paper_discovery_closure_verification/v1"
    assert closure_payload["status"] == "PASS"
    assert bundle_payload["schema_version"] == "research_paper_discovery_evidence_bundle_verification/v1"
    assert bundle_payload["status"] == "PASS"
    assert export_payload["schema_version"] == "research_paper_discovery_evidence_bundle_export/v1"
    assert export_payload["status"] == "PASS"
    assert export_payload["exported_bundle_sha256"]
    assert (export_dir / "research_paper_discovery_evidence_bundle.json").exists()


def test_research_paper_discovery_phase_run_report_records_full_profile_blocker(tmp_path) -> None:
    import json
    import subprocess
    import sys

    iso = tmp_path / "iso"
    iso.mkdir()
    plan = iso / "research_paper_discovery_profile_plan.json"
    plan_v = iso / "research_paper_discovery_profile_plan_verification.json"
    report = iso / "local_certify_report.json"
    report_v = iso / "local_certify_report_verification.json"
    preflight = iso / "frontend_preflight_report.json"
    py_core = iso / "python_core_report.json"
    closure = iso / "research_paper_discovery_closure_report.json"
    bundle = iso / "research_paper_discovery_evidence_bundle.json"
    phase_run = iso / "research_paper_discovery_phase_run_report.json"
    final_index = iso / "final_research_paper_discovery_certification_index.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/local_certify.py",
            "--certify-research-paper-discovery",
            "--skip-frontend",
            "--phase-profile-plan-output",
            str(plan),
            "--phase-profile-plan-verification-output",
            str(plan_v),
            "--local-certify-report-output",
            str(report),
            "--verification-output",
            str(report_v),
            "--frontend-preflight-report-output",
            str(preflight),
            "--python-core-report-output",
            str(py_core),
            "--phase-closure-output",
            str(closure),
            "--phase-evidence-bundle-output",
            str(bundle),
            "--phase-run-report-output",
            str(phase_run),
            "--final-phase-certificate-index-output",
            str(final_index),
            "--json",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=False,
    )

    assert result.returncode != 0
    stdout_payload = json.loads(result.stdout[result.stdout.find("{") :])
    run_report_path = phase_run
    assert stdout_payload["phase_run_report_path"] == str(run_report_path)
    run_report = json.loads(run_report_path.read_text(encoding="utf-8"))
    assert run_report["schema_version"] == "research_paper_discovery_phase_run/v1"
    assert run_report["status"] == "FAIL"
    assert run_report["local_certify_failed_step"] == "frontend_preflight"
    assert run_report["blocker_count"] >= 1
    assert any("RESEARCH_PAPER_DISCOVERY_PHASE_RUN_FAILED_STEP:frontend_preflight" == blocker for blocker in run_report["blockers"])
    assert any("FRONTEND_PREFLIGHT_SKIP_FRONTEND_FORBIDDEN_FOR_PHASE" in blocker for blocker in run_report["blockers"])
    assert run_report["phase_profile_plan"]["present"] is True
    assert run_report["phase_profile_plan_verification"]["present"] is True
    assert run_report["next_diagnostic"]


def test_research_paper_discovery_phase_run_report_detects_referenced_artifact_tampering(tmp_path) -> None:
    import json

    from scripts.local_certify import (
        RESEARCH_PAPER_DISCOVERY_PROFILE,
        validate_research_paper_discovery_phase_run_report,
        write_research_paper_discovery_phase_run_report,
    )

    def write_json(path, payload):
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    local_report = tmp_path / "local_certify_report.json"
    local_verification = tmp_path / "local_certify_report_verification.json"
    plan = tmp_path / "research_paper_discovery_profile_plan.json"
    plan_verification = tmp_path / "research_paper_discovery_profile_plan_verification.json"
    closure = tmp_path / "research_paper_discovery_closure_report.json"
    bundle = tmp_path / "research_paper_discovery_evidence_bundle.json"
    run_id = "phase_run_tamper_test_rid________________"
    for path, status in [
        (local_report, "PASS"),
        (local_verification, "PASS"),
        (plan, "PASS"),
        (plan_verification, "PASS"),
        (closure, "PASS"),
        (bundle, "PASS"),
    ]:
        write_json(path, {"schema_version": path.stem + "/v1", "status": status, "certification_run_id": run_id})

    run_report_path = tmp_path / "research_paper_discovery_phase_run_report.json"
    write_research_paper_discovery_phase_run_report(
        local_certify_payload={
            "status": "PASS",
            "failed_step": None,
            "certification_profile": RESEARCH_PAPER_DISCOVERY_PROFILE,
            "certification_run_id": run_id,
            "next_diagnostic": None,
        },
        local_report_path=local_report,
        local_report_verification={"status": "PASS"},
        local_report_verification_path=local_verification,
        phase_profile_plan_report={"status": "PASS"},
        phase_profile_plan_path=plan,
        phase_profile_plan_verification={"status": "PASS"},
        phase_profile_plan_verification_path=plan_verification,
        phase_closure_report={"status": "PASS", "no_live_authority_assertion": True, "paper_live_firewall_assertion": True},
        phase_closure_path=closure,
        phase_evidence_bundle={"status": "PASS"},
        phase_evidence_bundle_path=bundle,
        phase_profile_blockers=[],
        output_path=run_report_path,
    )
    summary, blockers = validate_research_paper_discovery_phase_run_report(run_report_path)
    assert blockers == []
    assert summary is not None
    assert summary["status"] == "PASS"

    write_json(local_report, {"schema_version": "local_certify/v5", "status": "TAMPERED", "certification_run_id": run_id})
    summary, blockers = validate_research_paper_discovery_phase_run_report(run_report_path)
    assert summary is not None
    assert summary["status"] == "FAIL"
    assert any("RESEARCH_PAPER_DISCOVERY_PHASE_RUN_ARTIFACT_SHA256_MISMATCH:local_certify_report" in blocker for blocker in blockers)


def test_research_paper_discovery_phase_run_report_cli_verification_writes_artifact(tmp_path, capsys) -> None:
    import json

    from scripts.local_certify import (
        RESEARCH_PAPER_DISCOVERY_PROFILE,
        main,
        write_research_paper_discovery_phase_run_report,
    )

    def write_json(path: Path, payload: dict[str, object]) -> None:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    local_report = tmp_path / "local_certify_report.json"
    local_verification = tmp_path / "local_certify_report_verification.json"
    plan = tmp_path / "research_paper_discovery_profile_plan.json"
    plan_verification = tmp_path / "research_paper_discovery_profile_plan_verification.json"
    closure = tmp_path / "research_paper_discovery_closure_report.json"
    bundle = tmp_path / "research_paper_discovery_evidence_bundle.json"
    run_id = "phase_run_cli_test_rid__________________"
    for path in (local_report, local_verification, plan, plan_verification, closure, bundle):
        write_json(path, {"schema_version": f"{path.stem}/v1", "status": "PASS", "certification_run_id": run_id})

    run_report_path = tmp_path / "research_paper_discovery_phase_run_report.json"
    write_research_paper_discovery_phase_run_report(
        local_certify_payload={
            "status": "PASS",
            "failed_step": None,
            "certification_profile": RESEARCH_PAPER_DISCOVERY_PROFILE,
            "certification_run_id": run_id,
            "next_diagnostic": None,
        },
        local_report_path=local_report,
        local_report_verification={"status": "PASS"},
        local_report_verification_path=local_verification,
        phase_profile_plan_report={"status": "PASS"},
        phase_profile_plan_path=plan,
        phase_profile_plan_verification={"status": "PASS"},
        phase_profile_plan_verification_path=plan_verification,
        phase_closure_report={"status": "PASS", "no_live_authority_assertion": True, "paper_live_firewall_assertion": True},
        phase_closure_path=closure,
        phase_evidence_bundle={"status": "PASS"},
        phase_evidence_bundle_path=bundle,
        phase_profile_blockers=[],
        output_path=run_report_path,
    )
    verification_path = tmp_path / "research_paper_discovery_phase_run_report_verification.json"

    assert main([
        "--verify-phase-run-report",
        str(run_report_path),
        "--phase-run-report-verification-output",
        str(verification_path),
        "--json",
    ]) == 0

    capsys.readouterr()
    payload = json.loads(verification_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "research_paper_discovery_phase_run_verification/v1"
    assert payload["status"] == "PASS"
    assert payload["phase_run_report_sha256"]
    assert payload["phase_run_report"]["proof_name"] == "research_paper_discovery_phase_run_report"


def test_ci_replays_and_uploads_phase_run_report_verification() -> None:
    ci_text = CI.read_text(encoding="utf-8")
    if "--verify-phase-run-report" not in ci_text:
        pytest.skip("ci.yml does not document phase run report verification")

    assert "--verify-phase-run-report artifacts/local_certify/latest/research_paper_discovery_phase_run_report.json" in ci_text
    assert "research_paper_discovery_phase_run_report_verification.json" in ci_text


def test_final_research_paper_discovery_certificate_index_binds_commands_assertions_and_artifacts(tmp_path) -> None:
    import json

    from scripts.local_certify import (
        FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_REQUIRED_COMMANDS,
        FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_REQUIRED_PHRASES,
        build_final_research_paper_discovery_certification_index,
        validate_final_research_paper_discovery_certification_index,
    )

    def write_json(path: Path, payload: dict[str, object]) -> None:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    artifact_paths = {
        "phase_profile_plan": tmp_path / "research_paper_discovery_profile_plan.json",
        "local_certify_report": tmp_path / "local_certify_report.json",
        "phase_run_report": tmp_path / "research_paper_discovery_phase_run_report.json",
        "phase_closure_report": tmp_path / "research_paper_discovery_closure_report.json",
        "phase_evidence_bundle": tmp_path / "research_paper_discovery_evidence_bundle.json",
        "frontend_certify_report": tmp_path / "frontend_certify_report.json",
        "researcher_fixture_report": tmp_path / "researcher_fixture_report.json",
        "public_surface_dashboard": tmp_path / "public_surface_dashboard.json",
        "package_repo_check": tmp_path / "package_repo_check.json",
    }
    for path in artifact_paths.values():
        write_json(path, {"schema_version": f"{path.stem}/v1", "status": "PASS"})

    doc = tmp_path / "final_research_paper_discovery_certification.md"
    doc.write_text(
        "\n".join(
            ["# Final Research-and-Paper-Discovery certification report"]
            + list(FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_REQUIRED_COMMANDS)
            + list(FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_REQUIRED_PHRASES)
            + [str(path) for path in artifact_paths.values()]
        )
        + "\n",
        encoding="utf-8",
    )
    index_path = tmp_path / "final_research_paper_discovery_certification_index.json"
    index = build_final_research_paper_discovery_certification_index(
        final_certificate_doc_path=doc,
        artifact_paths=artifact_paths,
        output_path=index_path,
    )
    index_path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    assert index["status"] == "PASS"
    summary, blockers = validate_final_research_paper_discovery_certification_index(index_path)
    assert summary is not None
    assert blockers == []


def test_final_research_paper_discovery_certificate_index_blocks_stale_human_report(tmp_path) -> None:
    import json

    from scripts.local_certify import (
        FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_REQUIRED_COMMANDS,
        build_final_research_paper_discovery_certification_index,
    )

    artifact = tmp_path / "local_certify_report.json"
    artifact.write_text(json.dumps({"schema_version": "local_certify/v5", "status": "PASS"}) + "\n", encoding="utf-8")
    doc = tmp_path / "final_research_paper_discovery_certification.md"
    # Intentionally omit one canonical command and all required assertion phrases.
    doc.write_text("\n".join(FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_REQUIRED_COMMANDS[:-1]) + "\n", encoding="utf-8")

    index = build_final_research_paper_discovery_certification_index(
        final_certificate_doc_path=doc,
        artifact_paths={"local_certify_report": artifact},
        output_path=tmp_path / "index.json",
    )

    assert index["status"] == "FAIL"
    assert any(str(blocker).startswith("FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_COMMAND_MISSING") for blocker in index["blockers"])
    assert any(str(blocker).startswith("FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_ASSERTION_TEXT_MISSING") for blocker in index["blockers"])


def test_ci_verifies_and_uploads_final_phase_certificate_index() -> None:
    ci_text = CI.read_text(encoding="utf-8")

    assert "--verify-final-phase-certificate docs/audits/final_research_paper_discovery_certification.md" in ci_text
    assert "final_research_paper_discovery_certification_index.json" in ci_text
    assert "final_research_paper_discovery_certification_verification.json" in ci_text
