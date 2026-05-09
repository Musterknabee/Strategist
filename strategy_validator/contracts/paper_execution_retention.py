"""Paper execution evidence-bundle retention contracts.

Legacy facade over focused retention contract subphase modules.
"""
from __future__ import annotations

from strategy_validator.contracts.paper_execution_retention_receipt import *
from strategy_validator.contracts.paper_execution_retention_signoff import *
from strategy_validator.contracts.paper_execution_retention_handoff import *

from strategy_validator.contracts.paper_execution_retention_receipt import __all__ as _paper_execution_retention_receipt_all
from strategy_validator.contracts.paper_execution_retention_signoff import __all__ as _paper_execution_retention_signoff_all
from strategy_validator.contracts.paper_execution_retention_handoff import __all__ as _paper_execution_retention_handoff_all

__all__ = (
    *_paper_execution_retention_receipt_all,
    *_paper_execution_retention_signoff_all,
    *_paper_execution_retention_handoff_all,
)
