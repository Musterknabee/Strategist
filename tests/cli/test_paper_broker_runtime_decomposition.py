from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from strategy_validator.cli import paper_broker
from strategy_validator.cli_support import paper_broker_runtime


def test_paper_broker_runtime_registry_is_outside_dispatcher() -> None:
    dispatcher_source = Path("strategy_validator/cli/paper_broker.py").read_text()
    runtime_source = Path("strategy_validator/cli_support/paper_broker_runtime.py").read_text()

    assert "lazy_callable(" not in dispatcher_source
    assert "lazy_model(" not in dispatcher_source
    assert "paper_broker_runtime" in dispatcher_source
    assert runtime_source.count("lazy_callable(") >= 70
    assert runtime_source.count("lazy_model(") >= 5


def test_dispatcher_delegates_legacy_runtime_symbols() -> None:
    assert paper_broker.dry_run_paper_order is paper_broker_runtime.dry_run_paper_order
    assert paper_broker.PaperBrokerOrderIntent is paper_broker_runtime.PaperBrokerOrderIntent
    assert "dry_run_paper_order" in dir(paper_broker)
    assert "PaperBrokerOrderIntent" in dir(paper_broker)


def test_legacy_paper_broker_surface_remains_monkeypatchable(monkeypatch) -> None:
    sentinel = object()

    monkeypatch.setattr(paper_broker, "dry_run_paper_order", sentinel)

    assert paper_broker.dry_run_paper_order is sentinel
    assert paper_broker_runtime.dry_run_paper_order is not sentinel


def test_dispatcher_import_does_not_import_heavy_runtime_targets() -> None:
    code = r"""
import sys
from strategy_validator.cli import paper_broker  # noqa: F401
blocked = [
    name for name in sys.modules
    if name == 'strategy_validator.brokers.alpaca_paper'
    or name.startswith('strategy_validator.application.paper_execution_')
    or name == 'strategy_validator.contracts.paper_broker'
    or name == 'strategy_validator.contracts.paper_execution'
]
if blocked:
    print('\n'.join(sorted(blocked)))
    raise SystemExit(1)
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=Path.cwd(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
