from __future__ import annotations

from strategy_validator.contracts.oracle_cadence_memory import *
from strategy_validator.contracts.oracle_cadence_weekly import *
from strategy_validator.contracts.oracle_cadence_doctrine_drift import *
from strategy_validator.contracts.oracle_cadence_monthly import *
from strategy_validator.contracts.oracle_cadence_quarterly import *
from strategy_validator.contracts.oracle_cadence_semiannual import *
from strategy_validator.contracts.oracle_cadence_annual import *
from strategy_validator.contracts.oracle_cadence_constitutional import *

from strategy_validator.contracts.oracle_cadence_memory import __all__ as _memory_all
from strategy_validator.contracts.oracle_cadence_weekly import __all__ as _weekly_all
from strategy_validator.contracts.oracle_cadence_doctrine_drift import __all__ as _doctrine_drift_all
from strategy_validator.contracts.oracle_cadence_monthly import __all__ as _monthly_all
from strategy_validator.contracts.oracle_cadence_quarterly import __all__ as _quarterly_all
from strategy_validator.contracts.oracle_cadence_semiannual import __all__ as _semiannual_all
from strategy_validator.contracts.oracle_cadence_annual import __all__ as _annual_all
from strategy_validator.contracts.oracle_cadence_constitutional import __all__ as _constitutional_all

__all__ = (
    *_memory_all,
    *_weekly_all,
    *_doctrine_drift_all,
    *_monthly_all,
    *_quarterly_all,
    *_semiannual_all,
    *_annual_all,
    *_constitutional_all,
)
