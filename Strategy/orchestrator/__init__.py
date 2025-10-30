# -*- coding: utf-8 -*-
"""Public orchestrators API (package exports) — synced with current repo state."""

# Core runners
from .market_one_shot import run_market_one_shot
from .pending_bracket import run_pending_bracket
from .ladder_builder import build_ladder_limits
from .spread_guard import market_with_spread_guard
from .cleanup import panic_close_symbol

# Advanced runners (present in repo)
from .oco_straddle import run_oco_straddle
from .bracket_trailing_activation import run_bracket_with_trailing_activation
from .grid_dca_common_sl import run_grid_dca_common_sl
from .kill_switch_review import run_kill_switch_with_review

# Guards / wrappers (present in repo)
from .session_guard import run_with_session_guard, SESSIONS as SESSION_WINDOWS
from .rollover_avoidance import run_with_rollover_avoidance
from .dynamic_deviation_guard import run_with_dynamic_deviation
from .equity_circuit_breaker import run_with_equity_circuit_breaker

__all__ = [
    # Core
    "run_market_one_shot",
    "run_pending_bracket",
    "build_ladder_limits",
    "market_with_spread_guard",
    "panic_close_symbol",
    # Advanced
    "run_oco_straddle",
    "run_bracket_with_trailing_activation",
    "run_grid_dca_common_sl",
    "run_kill_switch_with_review",
    # Guards / wrappers
    "run_with_session_guard",
    "SESSION_WINDOWS",
    "run_with_rollover_avoidance",
    "run_with_dynamic_deviation",
    "run_with_equity_circuit_breaker",
]
