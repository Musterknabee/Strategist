"""Phase-decomposed retention custody parser registration for the paper broker CLI."""
from __future__ import annotations

import argparse

from strategy_validator.cli_support import (
    paper_broker_custody_archive_parser,
    paper_broker_custody_chain_parser,
    paper_broker_custody_renewal_parser,
)


def register_custody_parsers(sub: argparse._SubParsersAction) -> None:
    paper_broker_custody_chain_parser.register_custody_chain_parsers(sub)
    paper_broker_custody_renewal_parser.register_custody_renewal_parsers(sub)
    paper_broker_custody_archive_parser.register_custody_archive_parsers(sub)
