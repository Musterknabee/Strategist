from __future__ import annotations

from pathlib import Path
import runpy


def test_architecture_health_report_builds() -> None:
    module = runpy.run_path(str(Path('scripts/architecture_health_report.py')))
    build = module['build_architecture_health_report']
    report = build(Path('.').resolve())
    assert report['convergence_signals']['application_package_present'] is True
    assert report['convergence_signals']['contracts_oracle_lines'] > 0
    assert report['biggest_files']
