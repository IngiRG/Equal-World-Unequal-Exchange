"""Equal World Analysis reference implementation."""
from .labor import equal_world_wages
from .prices import production_prices
from .hierarchy import trade_revaluation

__all__ = ["equal_world_wages", "production_prices", "trade_revaluation"]
__version__ = "0.1.0"
