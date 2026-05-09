"""Legacy public facade for paper execution contracts.

Phase-specific definitions live in smaller contract modules so downstream callers can
continue importing from ``strategy_validator.contracts.paper_execution`` while the
contract surface remains maintainable.
"""
from __future__ import annotations

from strategy_validator.contracts.paper_execution_core import *
from strategy_validator.contracts.paper_execution_core import __all__ as _PAPER_EXECUTION_CORE_ALL
from strategy_validator.contracts.paper_execution_evidence_bundle import *
from strategy_validator.contracts.paper_execution_evidence_bundle import __all__ as _PAPER_EXECUTION_EVIDENCE_BUNDLE_ALL
from strategy_validator.contracts.paper_execution_retention import *
from strategy_validator.contracts.paper_execution_retention import __all__ as _PAPER_EXECUTION_RETENTION_ALL
from strategy_validator.contracts.paper_execution_retention_custody_chain import *
from strategy_validator.contracts.paper_execution_retention_custody_chain import __all__ as _PAPER_EXECUTION_RETENTION_CUSTODY_CHAIN_ALL
from strategy_validator.contracts.paper_execution_retention_custody_renewal import *
from strategy_validator.contracts.paper_execution_retention_custody_renewal import __all__ as _PAPER_EXECUTION_RETENTION_CUSTODY_RENEWAL_ALL
from strategy_validator.contracts.paper_execution_retention_custody_archive import *
from strategy_validator.contracts.paper_execution_retention_custody_archive import __all__ as _PAPER_EXECUTION_RETENTION_CUSTODY_ARCHIVE_ALL
from strategy_validator.contracts.paper_execution_cockpit_payload import *
from strategy_validator.contracts.paper_execution_cockpit_payload import __all__ as _PAPER_EXECUTION_COCKPIT_PAYLOAD_ALL

__all__ = tuple(
    _PAPER_EXECUTION_CORE_ALL +
    _PAPER_EXECUTION_EVIDENCE_BUNDLE_ALL +
    _PAPER_EXECUTION_RETENTION_ALL +
    _PAPER_EXECUTION_RETENTION_CUSTODY_CHAIN_ALL +
    _PAPER_EXECUTION_RETENTION_CUSTODY_RENEWAL_ALL +
    _PAPER_EXECUTION_RETENTION_CUSTODY_ARCHIVE_ALL +
    _PAPER_EXECUTION_COCKPIT_PAYLOAD_ALL
)
