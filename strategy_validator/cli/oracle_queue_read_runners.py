from __future__ import annotations

from strategy_validator.cli.oracle_queue_read_query_runners import *
from strategy_validator.cli.oracle_queue_read_contract_runners import *

__all__ = [name for name in globals() if name.startswith('cmd_oracle_operator_')]
