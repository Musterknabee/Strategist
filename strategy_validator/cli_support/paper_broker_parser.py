"""Argument parser construction for the paper broker CLI.

The paper broker command surface is intentionally large. Parser registration is
phase-decomposed into family modules so this public builder stays small while
preserving the exact CLI command contract.
"""
from __future__ import annotations

import argparse

from strategy_validator.cli_support.paper_broker_custody_parser import register_custody_parsers
from strategy_validator.cli_support.paper_broker_evidence_bundle_parser import register_evidence_bundle_parsers
from strategy_validator.cli_support.paper_broker_order_parser import register_order_parsers
from strategy_validator.cli_support.paper_broker_retention_parser import register_retention_parsers


def build_paper_broker_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Paper-only Alpaca broker evidence CLI.")
    sub = p.add_subparsers(dest="cmd", required=True)

    register_order_parsers(sub)
    register_evidence_bundle_parsers(sub)
    register_retention_parsers(sub)
    register_custody_parsers(sub)

    return p
