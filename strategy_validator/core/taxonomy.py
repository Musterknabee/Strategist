from enum import Enum, auto

class AssetClass(Enum):
    EQUITY = auto()
    FIXED_INCOME = auto()
    COMMODITIES = auto()
    FX = auto()
    CRYPTO = auto()
    OPTIONS = auto()

class StrategyType(Enum):
    TREND_FOLLOWING = auto()
    MEAN_REVERSION = auto()
    STAT_ARB = auto()
    MACRO = auto()
    VOLATILITY = auto()
