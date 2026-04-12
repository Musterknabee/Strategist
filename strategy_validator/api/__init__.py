"""Transport-thin public surface; no adjudication or ledger writes."""

from strategy_validator import __version__


def get_api_version() -> str:
    return __version__
