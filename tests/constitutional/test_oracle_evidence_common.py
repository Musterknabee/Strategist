from __future__ import annotations

from pathlib import Path

from strategy_validator.validator.oracle_evidence_common import collect_evidence_subjects
from strategy_validator.validator.oracle_advisory import _artifact_descriptor


def _normalize_path(path: Path | str) -> str:
    return str(path).replace('\\', '/')


def test_collect_evidence_subjects_marks_missing_artifacts(tmp_path: Path) -> None:
    existing = tmp_path / 'present.json'
    existing.write_text('{}', encoding='utf-8')
    missing = tmp_path / 'missing.json'

    subjects, missing_artifact_paths, integrity_status = collect_evidence_subjects(
        artifact_paths=(existing, missing),
        repo_root=tmp_path,
        artifact_descriptor=_artifact_descriptor,
        normalize_path=_normalize_path,
    )

    assert len(subjects) == 1
    assert subjects[0].name == 'present.json'
    assert missing_artifact_paths == [_normalize_path(missing.resolve())]
    assert integrity_status == 'INCOMPLETE'
