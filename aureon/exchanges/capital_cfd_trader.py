"""
capital_cfd_trader.py  —  Autonomous CFD Trader for Capital.com

Covers the non-crypto slice of the financial system:
  • Forex   — EURUSD · GBPUSD · USDJPY · AUDUSD · USDCAD · EURGBP
  • Indices — UK100 · US500 · US30 · DE40
  • Commodities — GOLD · SILVER · OIL_CRUDE · NATURALGAS
  • Stocks (CFDs) — AAPL · TSLA · NVDA · AMZN · MSFT

Design principles:
  - tick() is headless (no sleep / no while-True) → called by orca main loop
  - Gated by Seer + Lyra quick-check before opening any position
  - TP / SL / 1-hour time-limit on every position
  - Max 3 concurrent CFD positions to protect margin
  - Phase-aware scoring: momentum + spread quality
  - Status lines for orca dashboard

Author: Aureon Trading System  |  March 2026
"""

import contextlib
import io
import os
import sys
import time
import logging
import json
import importlib
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)
CAPITAL_TRACE_PATH = Path(os.getenv("CAPITAL_TRACE_PATH", os.path.join(os.path.dirname(__file__), "..", "..", "state", "capital_cfd_last_exchange_trace.json"))).resolve()
CAPITAL_PROMOTION_LOG_PATH = Path(os.getenv("CAPITAL_PROMOTION_LOG_PATH", os.path.join(os.path.dirname(__file__), "..", "..", "state", "capital_shadow_promotions.jsonl"))).resolve()

# ── IMPORT GUARDS ──────────────────────────────────────────────────────────────
try:
    from capital_client import CapitalClient
    HAS_CAPITAL = True
except ImportError:
    try:
        from aureon.exchanges.capital_client import CapitalClient
        HAS_CAPITAL = True
    except ImportError:
        CapitalClient = None          # type: ignore
        HAS_CAPITAL = False

# Seer + Lyra lightweight gates (used directly — no full orchestrator needed)
try:
    from aureon_quadrumvirate import seer_should_trade, lyra_should_trade
    HAS_QUAD_GATES = True
except ImportError:
    HAS_QUAD_GATES = False
    seer_should_trade = None      # type: ignore
    lyra_should_trade = None      # type: ignore

try:
    from aureon.intelligence.aureon_brain import AureonBrain
    HAS_AUREON_BRAIN = True
except Exception:
    AureonBrain = None            # type: ignore
    HAS_AUREON_BRAIN = False

try:
    from aureon.portfolio.trade_profit_validator import TradeProfitValidator
    HAS_TRADE_PROFIT_VALIDATOR = True
except Exception:
    TradeProfitValidator = None   # type: ignore
    HAS_TRADE_PROFIT_VALIDATOR = False

try:
    from aureon.trading.dynamic_take_profit import DynamicTakeProfit
    HAS_CAPITAL_DTP = True
except Exception:
    try:
        from dynamic_take_profit import DynamicTakeProfit
        HAS_CAPITAL_DTP = True
    except Exception:
        DynamicTakeProfit = None   # type: ignore
        HAS_CAPITAL_DTP = False

try:
    from aureon.intelligence.aureon_unified_intelligence_registry import get_unified_puller
    HAS_UNIFIED_REGISTRY = True
except Exception:
    get_unified_puller = None   # type: ignore
    HAS_UNIFIED_REGISTRY = False

try:
    from aureon.intelligence.aureon_unified_decision_engine import (
        UnifiedDecisionEngine,
        SignalInput,
        CoordinationInput,
        DecisionType,
        DecisionReason,
    )
    HAS_UNIFIED_DECISION = True
except Exception:
    UnifiedDecisionEngine = None   # type: ignore
    SignalInput = None             # type: ignore
    CoordinationInput = None       # type: ignore
    DecisionType = None            # type: ignore
    DecisionReason = None          # type: ignore
    HAS_UNIFIED_DECISION = False

try:
    from autonomous_trading_orchestrator import AutonomousOrchestrator
    HAS_CAPITAL_ORCHESTRATOR = True
except Exception:
    AutonomousOrchestrator = None   # type: ignore
    HAS_CAPITAL_ORCHESTRATOR = False

try:
    from aureon.intelligence.aureon_timeline_oracle import get_timeline_oracle
    HAS_TIMELINE_ORACLE = True
except Exception:
    get_timeline_oracle = None      # type: ignore
    HAS_TIMELINE_ORACLE = False

try:
    from aureon.harmonic.aureon_harmonic_fusion import HarmonicWaveFusion
    HAS_HARMONIC_FUSION = True
except Exception:
    HarmonicWaveFusion = None       # type: ignore
    HAS_HARMONIC_FUSION = False

try:
    from aureon.core.aureon_thought_bus import get_thought_bus, Thought
    HAS_THOUGHT_BUS = True
except Exception:
    get_thought_bus = None         # type: ignore
    Thought = None                 # type: ignore
    HAS_THOUGHT_BUS = False

try:
    from aureon.command_centers.aureon_system_hub import SystemRegistry
    HAS_SYSTEM_HUB = True
except Exception:
    SystemRegistry = None          # type: ignore
    HAS_SYSTEM_HUB = False

try:
    from aureon.core.aureon_mycelium import get_mycelium, MyceliumNetwork
    HAS_MYCELIUM = True
except Exception:
    try:
        _MYCELIUM_CORE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "core"))
        if _MYCELIUM_CORE_DIR not in sys.path:
            sys.path.insert(0, _MYCELIUM_CORE_DIR)
        from aureon_mycelium import get_mycelium, MyceliumNetwork
        HAS_MYCELIUM = True
    except Exception:
        get_mycelium = None        # type: ignore
        MyceliumNetwork = None     # type: ignore
        HAS_MYCELIUM = False

try:
    from aureon.trading.penny_profit_engine import get_penny_engine
    HAS_PENNY_ENGINE = True
except Exception:
    try:
        from penny_profit_engine import get_penny_engine
        HAS_PENNY_ENGINE = True
    except Exception:
        get_penny_engine = None     # type: ignore
        HAS_PENNY_ENGINE = False

# ── INSTRUMENT UNIVERSE ────────────────────────────────────────────────────────
# symbol → {class, tp_pct, sl_pct, size, max_spread_pct, momentum_threshold}
#   tp_pct / sl_pct  — take-profit / stop-loss as % of entry price
#   size             — position size in Capital.com lots / units
#   max_spread_pct   — reject trade if spread exceeds this % of mid-price
#   momentum_threshold — min |change_pct| to consider the move meaningful

CAPITAL_UNIVERSE: Dict[str, dict] = {
    # ── Forex (major pairs) ──────────────────────────────────────────────
    "EURUSD":     {"class": "forex",     "tp_pct": 0.35, "sl_pct": 0.20, "size": 0.01, "max_spread_pct": 0.06, "momentum_threshold": 0.06},
    "GBPUSD":     {"class": "forex",     "tp_pct": 0.35, "sl_pct": 0.20, "size": 0.01, "max_spread_pct": 0.08, "momentum_threshold": 0.06},
    "USDJPY":     {"class": "forex",     "tp_pct": 0.35, "sl_pct": 0.20, "size": 0.01, "max_spread_pct": 0.05, "momentum_threshold": 0.05},
    "AUDUSD":     {"class": "forex",     "tp_pct": 0.35, "sl_pct": 0.20, "size": 0.01, "max_spread_pct": 0.08, "momentum_threshold": 0.07},
    "USDCAD":     {"class": "forex",     "tp_pct": 0.35, "sl_pct": 0.20, "size": 0.01, "max_spread_pct": 0.08, "momentum_threshold": 0.07},
    "EURGBP":     {"class": "forex",     "tp_pct": 0.35, "sl_pct": 0.20, "size": 0.01, "max_spread_pct": 0.07, "momentum_threshold": 0.06},
    # ── Indices ──────────────────────────────────────────────────────────
    "UK100":      {"class": "index",     "tp_pct": 0.55, "sl_pct": 0.30, "size": 1,    "max_spread_pct": 0.05, "momentum_threshold": 0.10},
    "US500":      {"class": "index",     "tp_pct": 0.55, "sl_pct": 0.30, "size": 1,    "max_spread_pct": 0.05, "momentum_threshold": 0.10},
    "US30":       {"class": "index",     "tp_pct": 0.55, "sl_pct": 0.30, "size": 1,    "max_spread_pct": 0.05, "momentum_threshold": 0.10},
    "DE40":       {"class": "index",     "tp_pct": 0.55, "sl_pct": 0.30, "size": 1,    "max_spread_pct": 0.06, "momentum_threshold": 0.12},
    # ── Commodities ───────────────────────────────────────────────────────
    "GOLD":       {"class": "commodity", "tp_pct": 0.75, "sl_pct": 0.45, "size": 0.1,  "max_spread_pct": 0.08, "momentum_threshold": 0.15},
    "SILVER":     {"class": "commodity", "tp_pct": 0.75, "sl_pct": 0.45, "size": 1,    "max_spread_pct": 0.15, "momentum_threshold": 0.20},
    "OIL_CRUDE":  {"class": "commodity", "tp_pct": 0.75, "sl_pct": 0.45, "size": 1,    "max_spread_pct": 0.10, "momentum_threshold": 0.20},
    "NATURALGAS": {"class": "commodity", "tp_pct": 1.00, "sl_pct": 0.60, "size": 10,   "max_spread_pct": 0.25, "momentum_threshold": 0.30},
    # ── Stocks (CFDs) ─────────────────────────────────────────────────────
    "AAPL":       {"class": "stock",     "tp_pct": 0.90, "sl_pct": 0.55, "size": 1,    "max_spread_pct": 0.15, "momentum_threshold": 0.20},
    "TSLA":       {"class": "stock",     "tp_pct": 0.90, "sl_pct": 0.55, "size": 1,    "max_spread_pct": 0.20, "momentum_threshold": 0.25},
    "NVDA":       {"class": "stock",     "tp_pct": 0.90, "sl_pct": 0.55, "size": 1,    "max_spread_pct": 0.20, "momentum_threshold": 0.25},
    "AMZN":       {"class": "stock",     "tp_pct": 0.90, "sl_pct": 0.55, "size": 1,    "max_spread_pct": 0.15, "momentum_threshold": 0.20},
    "MSFT":       {"class": "stock",     "tp_pct": 0.90, "sl_pct": 0.55, "size": 1,    "max_spread_pct": 0.15, "momentum_threshold": 0.20},
}

# ── CONFIG ─────────────────────────────────────────────────────────────────────
def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except Exception:
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


CFD_CONFIG: Dict[str, float] = {
    "max_positions":      _env_float("CAPITAL_MAX_POSITIONS", 2.0),   # One BUY lane and one SELL lane
    "price_ttl_secs":    _env_float("CAPITAL_PRICE_TTL_SECS", 10.0),  # Price cache lifetime
    "position_ttl_secs": _env_float("CAPITAL_POSITION_TTL_SECS", 3600.0), # Selection benchmark only; not a forced close
    "scan_interval_secs": _env_float("CAPITAL_SCAN_INTERVAL_SECS", 8.0),  # Opportunity scan interval
    "monitor_interval":   _env_float("CAPITAL_MONITOR_INTERVAL_SECS", 2.0),  # Position monitor interval
    "exchange_sync_secs": _env_float("CAPITAL_EXCHANGE_SYNC_SECS", 5.0),  # Reconcile local CFD positions against Capital.com
    "quad_gate_ttl":      _env_float("CAPITAL_QUAD_GATE_TTL_SECS", 10.0),  # Cache Seer/Lyra gate results for N secs
}
CFD_FLAGS = {
    "profit_only_closes": _env_bool("CAPITAL_PROFIT_ONLY_CLOSES", True),
    "penny_take_profit": _env_bool("CAPITAL_PENNY_TAKE_PROFIT", True),
}
CAPITAL_REJECTION_COOLDOWN_SECS = _env_float("CAPITAL_REJECTION_COOLDOWN_SECS", 60.0)
CAPITAL_RISK_REJECTION_COOLDOWN_SECS = _env_float("CAPITAL_RISK_REJECTION_COOLDOWN_SECS", 180.0)

CAPITAL_MIN_PROFIT_GBP = 0.01
CAPITAL_DTP_TRIGGER_GBP = 0.01
CAPITAL_SHADOW_MIN_VALIDATE_SECS = _env_float("CAPITAL_SHADOW_MIN_VALIDATE_SECS", 3.0)
CAPITAL_SELF_CONFIDENCE_ENABLED = _env_bool("CAPITAL_SELF_CONFIDENCE_ENABLED", True)
CAPITAL_SELF_CONFIDENCE_MAX_BOOST = _env_float("CAPITAL_SELF_CONFIDENCE_MAX_BOOST", 0.35)
CAPITAL_SELF_CONFIDENCE_MIN_VALIDATE_SECS = _env_float("CAPITAL_SELF_CONFIDENCE_MIN_VALIDATE_SECS", 1.5)
CAPITAL_HISTORY_LOOKBACK_DAYS = int(_env_float("CAPITAL_HISTORY_LOOKBACK_DAYS", 90.0))
CAPITAL_MIN_PROBABILITY_ACCURACY = _env_float("CAPITAL_MIN_PROBABILITY_ACCURACY", 0.55)
CAPITAL_MIN_PROBABILITY_PROFIT_FACTOR = _env_float("CAPITAL_MIN_PROBABILITY_PROFIT_FACTOR", 1.05)
CAPITAL_FORCE_SLOT_FILL = _env_bool("CAPITAL_FORCE_SLOT_FILL", True)
CAPITAL_SLOT_FILL_INTERVAL_SECS = _env_float("CAPITAL_SLOT_FILL_INTERVAL_SECS", 8.0)
CAPITAL_DEADMAN_ENABLED = _env_bool("CAPITAL_DEADMAN_ENABLED", True)
CAPITAL_DEADMAN_STALE_SECS = _env_float("CAPITAL_DEADMAN_STALE_SECS", 300.0)  # 5 min — give the system time
CAPITAL_LIVE_REFRESH_ENABLED = _env_bool("CAPITAL_LIVE_REFRESH_ENABLED", True)
CAPITAL_LIVE_REFRESH_INTERVAL_SECS = _env_float("CAPITAL_LIVE_REFRESH_INTERVAL_SECS", 1.0)
CAPITAL_LIVE_EVENT_TRIGGER_PCT = _env_float("CAPITAL_LIVE_EVENT_TRIGGER_PCT", 0.03)
CAPITAL_LIVE_EVENT_MIN_INTERVAL_SECS = _env_float("CAPITAL_LIVE_EVENT_MIN_INTERVAL_SECS", 0.25)
CAPITAL_MIND_MAP_REFRESH_SECS = _env_float("CAPITAL_MIND_MAP_REFRESH_SECS", 300.0)
CAPITAL_MYCELIUM_REFRESH_SECS = _env_float("CAPITAL_MYCELIUM_REFRESH_SECS", 15.0)
CAPITAL_PROBABILITY_FEED_INTERVAL_SECS = _env_float("CAPITAL_PROBABILITY_FEED_INTERVAL_SECS", 15.0)
CAPITAL_FOCUS_SYMBOLS = tuple(
    symbol.strip().upper()
    for symbol in str(os.getenv("CAPITAL_FOCUS_SYMBOLS", "") or "").split(",")
    if symbol.strip()
)


# ── DATA CLASSES ───────────────────────────────────────────────────────────────
@dataclass
class CFDPosition:
    """A live Capital.com CFD position tracked by the trader."""
    symbol:        str
    deal_id:       str
    epic:          str
    direction:     str       # "BUY" or "SELL"
    size:          float
    entry_price:   float
    tp_price:      float
    sl_price:      float
    asset_class:   str
    opened_at:     float = field(default_factory=time.time)
    current_price: float = 0.0

    @property
    def age_secs(self) -> float:
        return time.time() - self.opened_at

    @property
    def pnl_pct(self) -> float:
        if self.entry_price <= 0 or self.current_price <= 0:
            return 0.0
        if self.direction == "BUY":
            return (self.current_price - self.entry_price) / self.entry_price * 100
        return (self.entry_price - self.current_price) / self.entry_price * 100

    def one_line(self) -> str:
        age_m = self.age_secs / 60
        pnl_s = f"{self.pnl_pct:+.3f}%"
        tp_dist = abs(self.tp_price - self.current_price) / self.current_price * 100 if self.current_price > 0 else 0
        return (
            f"    {self.direction:4} {self.symbol:12} [{self.asset_class:9}] "
            f"entry:{self.entry_price:.5g}  now:{self.current_price:.5g}  "
            f"PnL:{pnl_s}  TP-dist:{tp_dist:.2f}%  age:{age_m:.1f}m"
        )


@dataclass
class CFDShadowTrade:
    """Paper validation pass for Capital candidates before live deployment."""
    symbol: str
    direction: str
    asset_class: str
    size: float
    entry_price: float
    target_move_pct: float
    score: float
    created_at: float = field(default_factory=time.time)
    current_price: float = 0.0
    current_move_pct: float = 0.0
    peak_move_pct: float = 0.0
    validated: bool = False
    validation_time: float = 0.0

    @property
    def age_secs(self) -> float:
        return time.time() - self.created_at

    def update(self, price: float) -> None:
        self.current_price = price
        if self.entry_price <= 0 or price <= 0:
            return
        if self.direction == "BUY":
            move_pct = (price - self.entry_price) / self.entry_price * 100.0
        else:
            move_pct = (self.entry_price - price) / self.entry_price * 100.0
        self.current_move_pct = move_pct
        self.peak_move_pct = max(self.peak_move_pct, move_pct)
        if not self.validated and move_pct >= self.target_move_pct:
            self.validated = True
            self.validation_time = time.time()


@dataclass
class CapitalSwarmAgentVote:
    """One specialist agent's view of the best current Capital candidate."""
    agent: str
    symbol: str
    direction: str
    score: float
    confidence: float
    rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent": self.agent,
            "symbol": self.symbol,
            "direction": self.direction,
            "score": self.score,
            "confidence": self.confidence,
            "rationale": self.rationale,
        }


# ── MAIN CLASS ─────────────────────────────────────────────────────────────────
class CapitalCFDTrader:
    """
    Autonomous CFD trader for Capital.com (non-crypto asset classes).

    Instruments: Forex · Indices · Commodities · Stocks (CFDs)

    Designed to run inside orca_complete_kill_cycle via tick().
    Each tick() call executes one complete cycle:
      Phase 0: Refresh price cache
      Phase 1: Monitor open positions → TP / SL / time-limit
      Phase 2: Scan for new opportunity → Seer/Lyra gate → open
    Returns list of closed-trade records for orca session_stats.
    """

    SHADOW_MAX_AGE = 120.0
    SHADOW_MIN_VALIDATE = CAPITAL_SHADOW_MIN_VALIDATE_SECS
    SHADOW_MAX_ACTIVE = 4

    def __init__(self) -> None:
        self.client: Optional[CapitalClient] = None
        self._state_lock = threading.RLock()

        # Open position tracking
        self.positions: List[CFDPosition] = []
        self.shadow_trades: List[CFDShadowTrade] = []

        # Price cache
        self._prices: Dict[str, dict] = {}
        self._prices_lock = threading.RLock()
        self._prices_fetched_at: float = 0.0
        self._latest_candidate_snapshot: List[Dict[str, Any]] = []
        self._latest_target_snapshot: Dict[str, Any] = {}
        self._latest_status_lines: List[str] = []
        self._latest_monitor_line: str = ""
        self._latest_tick_line: str = ""
        self._latest_order_error: str = ""
        self._latest_order_trace_path: str = str(CAPITAL_TRACE_PATH)
        self._capital_snapshot_cache: Dict[str, float] = {}
        self._capital_snapshot_error: str = ""
        self._last_deadman_kick_at: float = time.time()
        self._recent_closed_trades: List[dict] = []
        self._shadow_validated_count: int = 0
        self._shadow_failed_count: int = 0
        self._rejection_cooldowns: Dict[str, Dict[str, Any]] = {}
        self._lane_snapshot: Dict[str, Any] = {}
        self._dtp_trackers: Dict[str, Any] = {}
        self.start_time: float = time.time()
        self.starting_equity_gbp: float = 0.0
        self._signal_brain = AureonBrain() if HAS_AUREON_BRAIN and AureonBrain is not None else None
        self._trade_profit_validator = (
            TradeProfitValidator(validation_log_file=os.path.join(os.path.dirname(__file__), "..", "..", "state", "capital_trade_validations.json"))
            if HAS_TRADE_PROFIT_VALIDATOR and TradeProfitValidator is not None
            else None
        )
        self.workspace_root = Path(os.path.join(os.path.dirname(__file__), "..", "..")).resolve()
        self.system_hub_registry = (
            SystemRegistry(workspace_path=str(self.workspace_root))
            if HAS_SYSTEM_HUB and SystemRegistry is not None
            else None
        )
        self.mycelium = (
            get_mycelium(initial_capital=100.0)
            if HAS_MYCELIUM and get_mycelium is not None
            else None
        )
        self.unified_registry = get_unified_puller() if HAS_UNIFIED_REGISTRY and get_unified_puller is not None else None
        self.unified_decision_engine = UnifiedDecisionEngine() if HAS_UNIFIED_DECISION and UnifiedDecisionEngine is not None else None
        self.orchestrator = (
            AutonomousOrchestrator(self)
            if HAS_CAPITAL_ORCHESTRATOR and AutonomousOrchestrator is not None
            else None
        )
        self.timeline_oracle = (
            get_timeline_oracle() if HAS_TIMELINE_ORACLE and get_timeline_oracle is not None else None
        )
        self.harmonic_fusion = (
            HarmonicWaveFusion() if HAS_HARMONIC_FUSION and HarmonicWaveFusion is not None else None
        )
        self.thought_bus = (
            get_thought_bus(os.path.join(os.path.dirname(__file__), "..", "..", "state", "capital_thoughts.jsonl"))
            if HAS_THOUGHT_BUS and get_thought_bus is not None else None
        )
        self._registry_snapshot: Dict[str, Any] = {}
        self._mind_map_snapshot: Dict[str, Any] = {}
        self._mind_map_snapshot_at: float = 0.0
        self._decision_snapshot: Dict[str, Any] = {}
        self._orchestrator_snapshot: Dict[str, Any] = {}
        self._timeline_snapshot: Dict[str, Any] = {}
        self._fusion_snapshot: Dict[str, Any] = {}
        self._thought_bus_snapshot: Dict[str, Any] = {}
        self._cognition_snapshot: Dict[str, Any] = {}
        self._mycelium_snapshot: Dict[str, Any] = {}
        self._mycelium_snapshot_at: float = 0.0
        self._live_system_activity_snapshot: Dict[str, Any] = {}
        self._probability_feed_snapshot: Dict[str, Any] = {}
        self._last_probability_feed_publish_at: float = 0.0
        self._last_live_confirmed_key: str = ""
        self._last_mycelium_message: Dict[str, Any] = {}
        self._swarm_snapshot: Dict[str, Any] = {
            "enabled": True,
            "leader": {},
            "votes": [],
            "ranked": [],
        }
        self._probability_snapshot: Dict[str, Any] = {}
        self._probability_snapshot_at: float = 0.0
        self._self_confidence_snapshot: Dict[str, Any] = {}
        self._harmonic_wiring_audit: Dict[str, Any] = self._build_harmonic_wiring_audit()
        self._harmonic_wiring_audit_at: float = time.time()
        self._last_slot_fill_attempt: Dict[str, float] = {"BUY": 0.0, "SELL": 0.0}
        self._last_client_reinit_at: float = 0.0
        self._live_refresh_thread: Optional[threading.Thread] = None
        self._live_refresh_stop = threading.Event()
        self._last_live_event_at: float = 0.0
        self.penny_engine = get_penny_engine() if HAS_PENNY_ENGINE and get_penny_engine is not None else None

        # Timing
        self._last_scan:    float = 0.0
        self._last_monitor: float = 0.0
        self._last_exchange_sync: float = 0.0
        self._last_shadow_scan: float = 0.0

        # Cached Seer/Lyra gate result
        self._quad_gate_modifier: float = 1.0   # Fail-open
        self._quad_gate_at:  float = 0.0

        # Hive Mind shared intelligence — set externally by TradingHiveMind
        # {symbol/alias: confidence_factor 0.0–1.0} from Market Harp ripples
        self._hive_boosts:   Dict[str, float] = {}

        # Session statistics
        self.stats: Dict[str, float] = {
            "trades_opened":  0.0,
            "trades_closed":  0.0,
            "winning_trades": 0.0,
            "losing_trades":  0.0,
            "total_pnl_gbp":  0.0,
            "best_trade":     0.0,
            "worst_trade":    0.0,
        }

        # Init Capital.com client
        self.init_error = ""
        if HAS_CAPITAL:
            self._ensure_client_ready(force=True)
        else:
            self.init_error = "capital_client_not_installed"
            logger.info("CapitalCFDTrader: capital_client not installed — disabled")

        # Subscribe to Queen Hive Command hunt signals
        if self.thought_bus is not None:
            try:
                self.thought_bus.subscribe("queen.command.hunt", self._on_queen_hunt)
                logger.info("[QUEEN HIVE] Subscribed to queen.command.hunt")
            except Exception:
                pass

    # ── QUEEN HIVE COMMAND ─────────────────────────────────────────────────────

    def _on_queen_hunt(self, thought) -> None:
        """Queen issued a hunt command — gate through orchestrator and execute."""
        try:
            payload = thought.payload if hasattr(thought, 'payload') else thought
            if not isinstance(payload, dict):
                return
            symbol = str(payload.get("symbol") or "")
            if not symbol:
                return
            composite = float(payload.get("composite_score", 0) or 0)
            consensus = int(payload.get("consensus_count", 0) or 0)
            logger.info(
                f"[QUEEN HUNT] Received: {symbol} composite={composite:.3f} consensus={consensus}"
            )
            # Gate through orchestrator sizing
            if self.orchestrator is not None:
                approved, reason, sizing = self.orchestrator.gate_pre_trade(symbol, "buy")
                if not approved:
                    logger.info(f"[QUEEN HUNT] Blocked by orchestrator: {reason}")
                    return
                logger.info(f"[QUEEN HUNT] Approved: {symbol} sizing={sizing:.2f}x reason={reason}")
                # TODO: Open CFD position with the approved sizing
                # self._open_cfd_position(symbol, "BUY", queen_sizing=sizing)
            else:
                logger.debug("[QUEEN HUNT] No orchestrator — skipping execution")
        except Exception as e:
            logger.debug(f"[QUEEN HUNT] Error: {e}")

    # ── PROPERTIES ─────────────────────────────────────────────────────────────
    @property
    def enabled(self) -> bool:
        if self.client is not None and not getattr(self.client, "enabled", False):
            self.init_error = str(getattr(self.client, "init_error", "") or self.init_error or "client_disabled_or_blocked")
        return self.client is not None and getattr(self.client, "enabled", False)

    def _ensure_client_ready(self, force: bool = False) -> bool:
        if not HAS_CAPITAL:
            self.init_error = "capital_client_not_installed"
            self.client = None
            return False
        now = time.time()
        if self.client is not None and getattr(self.client, "enabled", False):
            return True
        if not force and (now - float(getattr(self, "_last_client_reinit_at", 0.0) or 0.0)) < 15.0:
            return False
        self._last_client_reinit_at = now
        try:
            client = CapitalClient()  # type: ignore[misc]
            if not getattr(client, "enabled", False):
                self.init_error = str(getattr(client, "init_error", "") or "client_disabled_or_blocked")
                logger.warning("CapitalCFDTrader: Capital.com unavailable (%s)", self.init_error)
                self.client = None
                return False
            self.client = client
            self.init_error = ""
            logger.info("CapitalCFDTrader: Capital.com client READY")
            snap = self.get_capital_snapshot()
            if float(getattr(self, "starting_equity_gbp", 0.0) or 0.0) <= 0 and float(snap.get("equity_gbp", 0.0) or 0.0) > 0:
                self.starting_equity_gbp = float(snap.get("equity_gbp", 0.0) or 0.0)
            self._sync_positions_from_exchange(force=True)
            return True
        except Exception as _e:
            self.init_error = str(_e) or "client_init_exception"
            logger.debug(f"CapitalCFDTrader: client init failed: {_e}")
            self.client = None
            return False

    @property
    def position_count(self) -> int:
        return len(self.positions)

    def _required_tp_pct_for_profit(self, price: float, size: float) -> float:
        """Minimum percentage move required to realize the configured absolute GBP target."""
        notional = max(price * size, 0.0001)
        return (CAPITAL_MIN_PROFIT_GBP / notional) * 100.0

    def _effective_tp_pct(self, price: float, size: float, cfg: Optional[dict] = None) -> float:
        required_tp_pct = self._required_tp_pct_for_profit(price, size)
        configured_tp_pct = float((cfg or {}).get("tp_pct", 0.0) or 0.0)
        if CFD_FLAGS["penny_take_profit"]:
            threshold = self._capital_penny_threshold(price, size)
            if threshold is not None:
                try:
                    win_pct = float(getattr(threshold, "win_pct", 0.0) or 0.0)
                except (TypeError, ValueError):
                    win_pct = 0.0
                if win_pct > 0:
                    return win_pct
            return max(configured_tp_pct, required_tp_pct)
        # The penny target is a minimum viability floor, not the actual strategy TP.
        # Use the configured strategy target whenever it is larger.
        return max(configured_tp_pct, required_tp_pct)

    def _capital_penny_threshold(self, price: float, size: float) -> Optional[Any]:
        if not CFD_FLAGS["penny_take_profit"]:
            return None
        engine = getattr(self, "penny_engine", None)
        if engine is None:
            return None
        entry_value = max(float(price or 0.0), 0.0) * max(float(size or 0.0), 0.0)
        if entry_value <= 0:
            return None
        try:
            return engine.get_threshold("capital", entry_value)
        except Exception as e:
            logger.debug("Capital penny threshold unavailable: %s", e)
            return None

    def _penny_take_profit_reason(self, pos: CFDPosition, pnl_gbp: float) -> str:
        threshold = self._capital_penny_threshold(pos.entry_price, pos.size)
        if threshold is None:
            return ""
        try:
            target_gbp = float(getattr(threshold, "win_gte", 0.0) or 0.0)
        except (TypeError, ValueError):
            target_gbp = 0.0
        if target_gbp > 0 and pnl_gbp >= target_gbp:
            return f"PENNY_TP pnl={pnl_gbp:+.4f}GBP target={target_gbp:.4f}GBP"
        return ""

    def _refresh_unified_intel_snapshot(self) -> None:
        snapshot: Dict[str, Any] = {}
        if self.unified_registry is not None:
            try:
                snapshot["categories"] = self.unified_registry.get_category_summary()
                snapshot["chain_flow"] = self.unified_registry.get_chain_flow()
            except Exception as e:
                snapshot["error"] = str(e)
        self._registry_snapshot = snapshot

    def _refresh_mind_map_snapshot(self, force: bool = False) -> Dict[str, Any]:
        now = time.time()
        cached_snapshot = dict(getattr(self, "_mind_map_snapshot", {}) or {})
        cached_at = float(getattr(self, "_mind_map_snapshot_at", 0.0) or 0.0)
        workspace_root = Path(
            getattr(
                self,
                "workspace_root",
                Path(os.path.join(os.path.dirname(__file__), "..", "..")).resolve(),
            )
        ).resolve()
        if not force and cached_snapshot and (now - cached_at) < max(30.0, CAPITAL_MIND_MAP_REFRESH_SECS):
            return dict(cached_snapshot)

        snapshot: Dict[str, Any] = {
            "ok": False,
            "workspace": str(workspace_root),
            "systems_total": 0,
            "categories_total": 0,
            "running_systems": 0,
            "probability_systems": 0,
            "neural_systems": 0,
            "execution_systems": 0,
            "edges_total": 0,
            "updated": datetime.now().isoformat(),
            "reason": "system_hub_unavailable",
        }
        registry = getattr(self, "system_hub_registry", None)
        if registry is not None:
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    registry.scan_workspace()
                graph = registry.export_mind_map_data()
                category_stats = registry.get_category_stats()
                running_nodes = [node for node in graph.get("nodes", []) if bool(node.get("is_running"))]
                probability_category = registry.categories.get("Probability & Prediction")
                neural_category = registry.categories.get("Neural Networks")
                execution_category = registry.categories.get("Execution Engines")
                snapshot = {
                    "ok": True,
                    "workspace": str(registry.workspace_path),
                    "systems_total": len(registry.systems),
                    "categories_total": len(registry.categories),
                    "running_systems": len(running_nodes),
                    "running_examples": [str(node.get("id") or "") for node in running_nodes[:10]],
                    "probability_systems": int(category_stats.get("Probability & Prediction", {}).get("count", 0) or 0),
                    "neural_systems": int(category_stats.get("Neural Networks", {}).get("count", 0) or 0),
                    "execution_systems": int(category_stats.get("Execution Engines", {}).get("count", 0) or 0),
                    "probability_examples": [sys.name for sys in (probability_category.systems[:8] if probability_category else [])],
                    "neural_examples": [sys.name for sys in (neural_category.systems[:8] if neural_category else [])],
                    "execution_examples": [sys.name for sys in (execution_category.systems[:8] if execution_category else [])],
                    "categories": category_stats,
                    "edges_total": len(graph.get("edges", [])),
                    "updated": datetime.now().isoformat(),
                    "reason": "ok",
                }
            except Exception as e:
                snapshot["reason"] = f"scan_error:{e}"

        self._mind_map_snapshot = snapshot
        self._mind_map_snapshot_at = now
        return dict(snapshot)

    def _refresh_thought_bus_snapshot(self) -> None:
        if self.thought_bus is None:
            self._thought_bus_snapshot = {}
            self._cognition_snapshot = {}
            return
        try:
            market_events = self.thought_bus.recall("market.", limit=8)
            decision_events = self.thought_bus.recall("decisions.", limit=8)
            cognition_events = self.thought_bus.recall("brain.", limit=8)
            queen_events = self.thought_bus.recall("queen.", limit=8)
            self._thought_bus_snapshot = {
                "market_events": len(market_events),
                "decision_events": len(decision_events),
                "latest_market_topic": (market_events[-1].get("topic") if market_events else ""),
                "latest_decision_topic": (decision_events[-1].get("topic") if decision_events else ""),
            }
            self._cognition_snapshot = {
                "cognition_events": len(cognition_events),
                "queen_events": len(queen_events),
                "latest_cognition_topic": (cognition_events[-1].get("topic") if cognition_events else ""),
                "latest_queen_topic": (queen_events[-1].get("topic") if queen_events else ""),
            }
        except Exception as e:
            self._thought_bus_snapshot = {"error": str(e)}
            self._cognition_snapshot = {"error": str(e)}

    def receive_mycelium_message(self, message_type: str, payload: Dict[str, Any]) -> None:
        self._last_mycelium_message = {
            "type": str(message_type or ""),
            "payload": dict(payload or {}),
            "received_at": time.time(),
        }

    def _wire_mycelium_runtime(self) -> None:
        if self.mycelium is None:
            return
        try:
            mesh = self.mycelium.get_mesh_status() if hasattr(self.mycelium, "get_mesh_status") else {}
            connected_names = {
                str(item.get("name") or "")
                for item in list(mesh.get("connected_systems", []) or [])
            }
            targets = (
                ("capital_cfd_trader", self),
                ("system_hub_registry", getattr(self, "system_hub_registry", None)),
                ("capital_thought_bus", getattr(self, "thought_bus", None)),
            )
            for name, instance in targets:
                if not name or instance is None or name in connected_names:
                    continue
                if hasattr(self.mycelium, "connect_subsystem"):
                    self.mycelium.connect_subsystem(name, instance)
        except Exception as e:
            logger.debug("Capital Mycelium wiring failed: %s", e)

    def _refresh_mycelium_snapshot(self, force: bool = False) -> Dict[str, Any]:
        now = time.time()
        cached_snapshot = dict(getattr(self, "_mycelium_snapshot", {}) or {})
        cached_at = float(getattr(self, "_mycelium_snapshot_at", 0.0) or 0.0)
        mind_map_snapshot = dict(getattr(self, "_mind_map_snapshot", {}) or {})
        last_mycelium_message = dict(getattr(self, "_last_mycelium_message", {}) or {})
        if not force and cached_snapshot and (now - cached_at) < max(5.0, CAPITAL_MYCELIUM_REFRESH_SECS):
            return dict(cached_snapshot)

        snapshot: Dict[str, Any] = {
            "ok": False,
            "coherence": 0.0,
            "queen_signal": 0.0,
            "total_hives": 0,
            "total_agents": 0,
            "generation": 0,
            "connected_count": 0,
            "connected_systems": [],
            "external_signals": 0,
            "broadcasts_pending": 0,
            "mind_map_attached": False,
            "updated": datetime.now().isoformat(),
            "reason": "mycelium_unavailable",
        }
        mycelium = getattr(self, "mycelium", None)
        if mycelium is not None:
            try:
                self._wire_mycelium_runtime()
                capital = self.get_capital_snapshot()
                growth = self._compute_growth_metrics()
                drawdown_pct = abs(min(float(growth.get("equity_growth_pct", 0.0) or 0.0), 0.0))
                governing_metrics = {
                    "total_equity": float(capital.get("equity_gbp", 0.0) or 0.0),
                    "total_cash": float(capital.get("free_gbp", 0.0) or 0.0),
                    "realized_pnl_total": float((self.stats or {}).get("total_pnl_gbp", 0.0) or 0.0),
                    "win_rate": float(growth.get("win_rate", 0.0) or 0.0),
                    "drawdown_pct": drawdown_pct,
                    "positions_count": len(self.positions),
                }
                if hasattr(mycelium, "update_governing_metrics"):
                    mycelium.update_governing_metrics(governing_metrics)

                connection_map = dict(getattr(mycelium, "connection_map", {}) or {})
                connection_map["mind_map"] = {
                    "systems_total": int(mind_map_snapshot.get("systems_total", 0) or 0),
                    "categories_total": int(mind_map_snapshot.get("categories_total", 0) or 0),
                    "running_systems": int(mind_map_snapshot.get("running_systems", 0) or 0),
                    "probability_systems": int(mind_map_snapshot.get("probability_systems", 0) or 0),
                    "updated": mind_map_snapshot.get("updated", ""),
                }
                if last_mycelium_message:
                    connection_map["capital_last_message"] = dict(last_mycelium_message)
                if hasattr(mycelium, "update_connection_map"):
                    mycelium.update_connection_map(connection_map)

                target = dict(self._latest_target_snapshot or {})
                symbol = str(target.get("symbol") or "")
                score = max(0.0, min(1.0, float(target.get("score", 0.0) or 0.0)))
                direction = str(target.get("direction") or "").upper()
                if symbol and hasattr(mycelium, "receive_external_signal"):
                    signed_signal = score if direction == "BUY" else (-score if direction == "SELL" else 0.0)
                    mycelium.receive_external_signal("capital_probability", signed_signal, confidence=max(0.25, score))

                mesh = mycelium.get_mesh_status() if hasattr(mycelium, "get_mesh_status") else {}
                state = mycelium.get_state() if hasattr(mycelium, "get_state") else {}
                unified = (
                    mycelium.get_unified_signal(symbol, include_external=True)
                    if hasattr(mycelium, "get_unified_signal")
                    else {}
                )
                connected_systems = [
                    str(item.get("name") or "")
                    for item in list(mesh.get("connected_systems", []) or [])
                ]
                snapshot = {
                    "ok": True,
                    "coherence": float(mesh.get("coherence", 0.0) or 0.0),
                    "queen_signal": float(mesh.get("queen_signal", 0.0) or 0.0),
                    "total_hives": int(state.get("total_hives", 0) or 0),
                    "total_agents": int(state.get("total_agents", 0) or 0),
                    "generation": int(state.get("generation", 0) or 0),
                    "connected_count": len(connected_systems),
                    "connected_systems": connected_systems,
                    "external_signals": int(mesh.get("external_signals", 0) or 0),
                    "broadcasts_pending": int(mesh.get("broadcasts_pending", 0) or 0),
                    "mind_map_attached": bool(getattr(mycelium, "connection_map", {}).get("mind_map")),
                    "unified_signal": dict(unified or {}),
                    "last_received_message": dict(last_mycelium_message),
                    "updated": datetime.now().isoformat(),
                    "reason": "ok",
                }
            except Exception as e:
                snapshot["reason"] = f"mycelium_error:{e}"

        self._mycelium_snapshot = snapshot
        self._mycelium_snapshot_at = now
        return dict(snapshot)

    def _refresh_live_system_activity_snapshot(self) -> Dict[str, Any]:
        capital = self.get_capital_snapshot()
        probability = self._probability_validation_snapshot()
        target = dict(self._latest_target_snapshot or {})
        mind_map_snapshot = dict(getattr(self, "_mind_map_snapshot", {}) or {})
        mycelium_snapshot = dict(getattr(self, "_mycelium_snapshot", {}) or {})
        decision_snapshot = dict(getattr(self, "_decision_snapshot", {}) or {})
        systems: List[Dict[str, Any]] = []

        def add_system(
            name: str,
            active: bool,
            role: str,
            status: str,
            output_keys: Optional[List[str]] = None,
        ) -> None:
            systems.append({
                "name": name,
                "active": bool(active),
                "role": role,
                "status": status,
                "output_keys": list(output_keys or []),
            })

        add_system(
            "capital_client",
            self.enabled,
            "Live exchange execution and pricing",
            (
                f"positions={len(self.positions)} free_gbp={float(capital.get('free_gbp', 0.0) or 0.0):.2f} "
                f"stale={float(capital.get('stale', 0.0) or 0.0):.0f}"
            ),
            ["equity_gbp", "free_gbp", "used_gbp", "budget_gbp"],
        )
        add_system(
            "mind_map_registry",
            bool(mind_map_snapshot.get("ok")),
            "Exact workspace system census and category map",
            (
                f"systems={int(mind_map_snapshot.get('systems_total', 0) or 0)} "
                f"running={int(mind_map_snapshot.get('running_systems', 0) or 0)} "
                f"probability={int(mind_map_snapshot.get('probability_systems', 0) or 0)}"
            ),
            ["systems_total", "running_systems", "probability_systems", "neural_systems", "execution_systems"],
        )
        add_system(
            "mycelium_network",
            bool(mycelium_snapshot.get("ok")),
            "Neural mesh consensus and cross-system signal fusion",
            (
                f"hives={int(mycelium_snapshot.get('total_hives', 0) or 0)} "
                f"agents={int(mycelium_snapshot.get('total_agents', 0) or 0)} "
                f"coh={float(mycelium_snapshot.get('coherence', 0.0) or 0.0):.2f}"
            ),
            ["coherence", "queen_signal", "unified_signal", "external_signals", "connected_count"],
        )
        add_system(
            "probability_validation",
            bool(probability.get("ok")),
            "Probability quality gate and validation report",
            (
                f"direction_acc={float(probability.get('direction_accuracy', 0.0) or 0.0):.2f} "
                f"profit_factor={float(probability.get('profit_factor', 0.0) or 0.0):.2f}"
            ),
            ["direction_accuracy", "profit_factor", "updated", "reason"],
        )
        add_system(
            "unified_decision_engine",
            self.unified_decision_engine is not None,
            "Cross-system coordination and action arbitration",
            (
                f"latest={str((decision_snapshot.get('decision') or {}).get('type') or 'idle')} "
                f"conf={float((decision_snapshot.get('decision') or {}).get('confidence', 0.0) or 0.0):.2f}"
            ),
            ["decision.type", "decision.confidence"],
        )
        add_system(
            "timeline_oracle",
            self.timeline_oracle is not None,
            "Forward-branch timing and validation",
            f"target_conf={float(target.get('timeline_confidence', 0.0) or 0.0):.2f}",
            ["timeline_confidence", "timeline_reason"],
        )
        add_system(
            "harmonic_fusion",
            self.harmonic_fusion is not None,
            "Harmonic coherence and symbol phase scoring",
            f"global_coh={float(target.get('fusion_global_coherence', 0.0) or 0.0):.2f}",
            ["fusion_global_coherence", "fusion_symbol_phase"],
        )
        add_system(
            "candidate_engine",
            bool(self._latest_candidate_snapshot),
            "Ranks live Capital opportunities for the probability layer",
            f"candidates={len(self._latest_candidate_snapshot)} target={str(target.get('symbol') or 'none')}",
            ["symbol", "direction", "score", "change_pct", "spread_pct", "expected_net_profit"],
        )

        snapshot = {
            "total_systems": len(systems),
            "active_systems": sum(1 for system in systems if system["active"]),
            "systems": systems,
            "updated": datetime.now().isoformat(),
        }
        self._live_system_activity_snapshot = snapshot
        return dict(snapshot)

    def _refresh_probability_feed_snapshot(self) -> Dict[str, Any]:
        probability = self._probability_validation_snapshot()
        capital = self.get_capital_snapshot()
        target = dict(self._latest_target_snapshot or {})
        mind_map_snapshot = dict(getattr(self, "_mind_map_snapshot", {}) or {})
        mycelium_snapshot = dict(getattr(self, "_mycelium_snapshot", {}) or {})
        live_system_activity_snapshot = dict(getattr(self, "_live_system_activity_snapshot", {}) or {})
        candidates = []
        for candidate in list(self._latest_candidate_snapshot[:5]):
            candidates.append({
                "symbol": str(candidate.get("symbol") or ""),
                "direction": str(candidate.get("direction") or "").upper(),
                "score": float(candidate.get("score", 0.0) or 0.0),
                "change_pct": float(candidate.get("change_pct", 0.0) or 0.0),
                "spread_pct": float(candidate.get("spread_pct", 0.0) or 0.0),
                "expected_net_profit": float(candidate.get("expected_net_profit", 0.0) or 0.0),
                "timeline_confidence": float(candidate.get("timeline_confidence", 0.0) or 0.0),
                "fusion_global_coherence": float(candidate.get("fusion_global_coherence", 0.0) or 0.0),
                "brain_coherence": float(candidate.get("brain_coherence", 0.0) or 0.0),
            })

        live_confirmed = bool(
            probability.get("ok")
            and str(target.get("symbol") or "")
            and float(target.get("score", 0.0) or 0.0) > 0.0
        )
        snapshot = {
            "topic": "probability.capital_feed",
            "live_confirm_topic": "probability.live_confirmed",
            "generated_at": datetime.now().isoformat(),
            "mind_map": {
                "systems_total": int(mind_map_snapshot.get("systems_total", 0) or 0),
                "running_systems": int(mind_map_snapshot.get("running_systems", 0) or 0),
                "probability_systems": int(mind_map_snapshot.get("probability_systems", 0) or 0),
                "neural_systems": int(mind_map_snapshot.get("neural_systems", 0) or 0),
            },
            "mycelium": {
                "coherence": float(mycelium_snapshot.get("coherence", 0.0) or 0.0),
                "queen_signal": float(mycelium_snapshot.get("queen_signal", 0.0) or 0.0),
                "connected_count": int(mycelium_snapshot.get("connected_count", 0) or 0),
                "external_signals": int(mycelium_snapshot.get("external_signals", 0) or 0),
                "unified_signal": dict(mycelium_snapshot.get("unified_signal", {}) or {}),
            },
            "capital": {
                "equity_gbp": float(capital.get("equity_gbp", 0.0) or 0.0),
                "free_gbp": float(capital.get("free_gbp", 0.0) or 0.0),
                "used_gbp": float(capital.get("used_gbp", 0.0) or 0.0),
                "budget_gbp": float(capital.get("budget_gbp", 0.0) or 0.0),
                "positions": len(self.positions),
                "shadows": len(self.shadow_trades),
            },
            "validation": dict(probability),
            "target": {
                "symbol": str(target.get("symbol") or ""),
                "direction": str(target.get("direction") or "").upper(),
                "score": float(target.get("score", 0.0) or 0.0),
                "change_pct": float(target.get("change_pct", 0.0) or 0.0),
                "expected_net_profit": float(target.get("expected_net_profit", 0.0) or 0.0),
                "timeline_confidence": float(target.get("timeline_confidence", 0.0) or 0.0),
                "fusion_global_coherence": float(target.get("fusion_global_coherence", 0.0) or 0.0),
                "brain_coherence": float(target.get("brain_coherence", 0.0) or 0.0),
            },
            "candidates": candidates,
            "systems": list(live_system_activity_snapshot.get("systems", []) or []),
            "output_keys": [
                "mind_map.systems_total",
                "mind_map.running_systems",
                "mind_map.probability_systems",
                "mycelium.coherence",
                "mycelium.queen_signal",
                "mycelium.unified_signal.signal",
                "capital.equity_gbp",
                "capital.free_gbp",
                "validation.direction_accuracy",
                "validation.profit_factor",
                "target.symbol",
                "target.direction",
                "target.score",
                "target.expected_net_profit",
                "target.timeline_confidence",
                "target.fusion_global_coherence",
                "target.brain_coherence",
            ],
            "live_confirmed": live_confirmed,
        }
        self._probability_feed_snapshot = snapshot
        return dict(snapshot)

    def _publish_probability_feed(self, force: bool = False) -> None:
        thought_bus = getattr(self, "thought_bus", None)
        if thought_bus is None or Thought is None:
            return
        now = time.time()
        if not force and (now - float(getattr(self, "_last_probability_feed_publish_at", 0.0) or 0.0)) < max(5.0, CAPITAL_PROBABILITY_FEED_INTERVAL_SECS):
            return
        feed = self._refresh_probability_feed_snapshot()
        try:
            thought_bus.publish(Thought(
                source="capital_cfd_trader",
                topic="probability.capital_feed",
                payload=feed,
                meta={"mode": "capital_cfd"},
            ))
            if feed.get("live_confirmed"):
                target = dict(feed.get("target") or {})
                key = ":".join([
                    str(target.get("symbol") or ""),
                    str(target.get("direction") or ""),
                    f"{float(target.get('score', 0.0) or 0.0):.4f}",
                ])
                if key and key != self._last_live_confirmed_key:
                    thought_bus.publish(Thought(
                        source="capital_cfd_trader",
                        topic="probability.live_confirmed",
                        payload={
                            "symbol": str(target.get("symbol") or ""),
                            "direction": str(target.get("direction") or ""),
                            "score": float(target.get("score", 0.0) or 0.0),
                            "timeline_confidence": float(target.get("timeline_confidence", 0.0) or 0.0),
                            "fusion_global_coherence": float(target.get("fusion_global_coherence", 0.0) or 0.0),
                            "brain_coherence": float(target.get("brain_coherence", 0.0) or 0.0),
                        },
                        meta={"mode": "capital_cfd"},
                    ))
                    self._last_live_confirmed_key = key
            self._last_probability_feed_publish_at = now
        except Exception as e:
            logger.debug("Capital probability feed publish failed: %s", e)

    def _publish_market_snapshot_to_thought_bus(self) -> None:
        if self.thought_bus is None or Thought is None:
            return
        try:
            market_by_symbol: Dict[str, Dict[str, Any]] = {}
            universe: List[str] = []
            for candidate in self._latest_candidate_snapshot[:7]:
                symbol = str(candidate.get("symbol") or "").upper()
                if not symbol:
                    continue
                universe.append(symbol)
                market_by_symbol[symbol] = {
                    "momentum": float(candidate.get("change_pct", 0.0) or 0.0),
                    "score": float(candidate.get("score", 0.0) or 0.0),
                    "spread_pct": float(candidate.get("spread_pct", 0.0) or 0.0),
                    "direction": str(candidate.get("direction") or "BUY").upper(),
                    "eta_to_target": float(candidate.get("eta_to_target", 0.0) or 0.0),
                }
            if not universe:
                return
            self.thought_bus.publish(Thought(
                source="capital_cfd_trader",
                topic="market.snapshot",
                payload={
                    "venue": "capital",
                    "universe": universe,
                    "market_by_symbol": market_by_symbol,
                    "capital": self.get_capital_snapshot(),
                },
                meta={"mode": "capital_cfd"},
            ))
        except Exception as e:
            logger.debug(f"Capital ThoughtBus publish failed: {e}")

    def _publish_learning_update(self, record: Dict[str, Any]) -> None:
        thought_bus = getattr(self, "thought_bus", None)
        if thought_bus is None or Thought is None:
            return
        learning_update = dict(record.get("learning_update") or {})
        if not learning_update:
            return
        try:
            symbol = str(record.get("symbol") or "").upper()
            payload = {
                "venue": "capital",
                "symbol": symbol,
                "direction": str(record.get("direction") or "").upper(),
                "net_pnl_gbp": float(record.get("net_pnl", 0.0) or 0.0),
                "reason": str(record.get("reason") or ""),
                "learning_update": learning_update,
            }
            thought_bus.publish(Thought(
                source="capital_cfd_trader",
                topic="brain.learning",
                payload=payload,
                meta={"mode": "capital_cfd", "expressive": True},
            ))
            thought_bus.publish(Thought(
                source="capital_cfd_trader",
                topic="queen.learning",
                payload={
                    "voice": (
                        f"I learned from {symbol}. "
                        f"Net outcome was {float(record.get('net_pnl', 0.0) or 0.0):+.2f} GBP, "
                        f"and my bias is now {float(learning_update.get('symbol_bias', 0.0) or 0.0):+.3f}."
                    ),
                    **payload,
                },
                meta={"mode": "capital_cfd", "expressive": True},
            ))
        except Exception as e:
            logger.debug(f"Capital learning publish failed: {e}")

    def _feed_unified_decision_engine(self, symbol: str, side: str, score: float = 0.5, metadata: Optional[dict] = None) -> None:
        if self.unified_decision_engine is None or SignalInput is None:
            return
        try:
            direction = "bullish" if str(side).upper() == "BUY" else "bearish"
            self.unified_decision_engine.add_signal(
                SignalInput(
                    source="capital_cfd_trader",
                    symbol=symbol,
                    direction=direction,
                    strength=max(0.0, min(1.0, float(score))),
                    metadata=metadata or {},
                )
            )
            if CoordinationInput is not None:
                self.unified_decision_engine.set_coordination_state(
                    CoordinationInput(
                        orca_ready=True,
                        all_systems_ready=1,
                        total_systems=1,
                        blockers=[],
                    )
                )
            decision = None
            if DecisionType is not None and DecisionReason is not None:
                decision = self.unified_decision_engine.generate_decision(
                    symbol,
                    DecisionType.BUY if str(side).upper() == "BUY" else DecisionType.SELL,
                    DecisionReason.SIGNAL_STRENGTH,
                )
            self._decision_snapshot = {
                "symbol": symbol,
                "side": str(side).upper(),
                "score": float(score),
                "decision": {
                    "type": decision.decision_type.value,
                    "confidence": decision.confidence,
                    "reason": decision.reason.value,
                } if decision else None,
            }
        except Exception as e:
            self._decision_snapshot = {"error": str(e), "symbol": symbol, "side": str(side).upper()}

    def _write_exchange_trace(self, payload: Dict[str, Any]) -> None:
        """Persist the latest raw Capital exchange payloads for debugging live behavior."""
        try:
            CAPITAL_TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)
            trace = dict(payload)
            trace["written_at"] = time.time()
            with open(CAPITAL_TRACE_PATH, "w", encoding="utf-8") as f:
                json.dump(trace, f, indent=2, default=str)
            self._latest_order_trace_path = str(CAPITAL_TRACE_PATH)
        except Exception as _e:
            logger.debug(f"Capital trace write failed: {_e}")

    def _append_promotion_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Persist shadow lifecycle events for promotion debugging."""
        try:
            CAPITAL_PROMOTION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            row = {
                "event": str(event_type or "").strip() or "unknown",
                "written_at": time.time(),
                "written_at_iso": datetime.now().isoformat(),
                **dict(payload or {}),
            }
            with open(CAPITAL_PROMOTION_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, default=str) + "\n")
        except Exception as _e:
            logger.debug(f"Capital promotion event write failed: {_e}")

    def get_capital_snapshot(self) -> Dict[str, float]:
        """Expose Capital.com account state in the same style as the Kraken trader."""
        cached = dict(getattr(self, "_capital_snapshot_cache", {}) or {})
        if not self.client:
            return cached or {
                "equity_gbp": 0.0,
                "free_gbp": 0.0,
                "used_gbp": 0.0,
                "budget_gbp": 0.0,
                "target_pct_equity": 0.0,
            }
        try:
            accounts = self.client.get_accounts()
        except Exception as e:
            accounts = []
            self._capital_snapshot_error = f"accounts_error:{e}"
        if not accounts:
            try:
                balances = self.client.get_account_balance()
            except Exception as e:
                balances = {}
                self._capital_snapshot_error = f"balance_error:{e}"
            equity = float(sum(float(v or 0.0) for v in balances.values()))
            free = equity
        else:
            equity = sum(float(acc.get("balance", 0.0) or 0.0) for acc in accounts)
            free = sum(float(acc.get("available", 0.0) or 0.0) for acc in accounts)
        used = max(0.0, equity - free)
        budget = free * 0.70
        target_pct = (CAPITAL_MIN_PROFIT_GBP / equity * 100.0) if equity > 0 else 0.0
        snapshot = {
            "equity_gbp": equity,
            "free_gbp": free,
            "used_gbp": used,
            "budget_gbp": budget,
            "target_pct_equity": target_pct,
        }
        if equity > 0 or free > 0:
            self._capital_snapshot_cache = dict(snapshot)
            self._capital_snapshot_error = ""
            return snapshot
        if cached:
            cached["stale"] = 1.0
            return cached
        return snapshot

    def _extract_capital_min_size(self, market_info: dict) -> float:
        """Best-effort extraction of Capital's minimum deal size for a market."""
        if not isinstance(market_info, dict):
            return 0.0
        instrument = market_info.get("instrument", {}) if isinstance(market_info.get("instrument"), dict) else {}
        dealing_rules = market_info.get("dealingRules", {}) if isinstance(market_info.get("dealingRules"), dict) else {}
        candidates = [
            dealing_rules.get("minDealSize", {}).get("value") if isinstance(dealing_rules.get("minDealSize"), dict) else dealing_rules.get("minDealSize"),
            dealing_rules.get("minimumDealSize", {}).get("value") if isinstance(dealing_rules.get("minimumDealSize"), dict) else dealing_rules.get("minimumDealSize"),
            instrument.get("minDealSize"),
            instrument.get("minimumDealSize"),
            market_info.get("minDealSize"),
            market_info.get("minimumDealSize"),
        ]
        for candidate in candidates:
            try:
                value = float(candidate or 0.0)
                if value > 0:
                    return value
            except (TypeError, ValueError):
                continue
        return 0.0

    @staticmethod
    def _normalize_capital_margin_pct(candidate: Any, unit: str = "") -> float:
        """Normalize Capital margin values to a percentage of notional."""
        try:
            value = float(candidate or 0.0)
        except (TypeError, ValueError):
            return 0.0
        if value <= 0:
            return 0.0
        unit_text = str(unit or "").strip().upper()
        if unit_text in {"PERCENT", "PERCENTAGE", "PCT", "%"}:
            return value
        if unit_text in {"FACTOR", "DECIMAL", "FRACTION", "RATIO"}:
            return value * 100.0
        if value < 1.0:
            return value * 100.0
        return value

    def _extract_margin_factor_pct(self, market_info: dict, asset_class: str = "") -> float:
        """Best-effort extraction of Capital margin requirement percentage."""
        if not isinstance(market_info, dict):
            market_info = {}
        instrument = market_info.get("instrument", {}) if isinstance(market_info.get("instrument"), dict) else {}
        dealing_rules = market_info.get("dealingRules", {}) if isinstance(market_info.get("dealingRules"), dict) else {}
        snapshot = market_info.get("snapshot", {}) if isinstance(market_info.get("snapshot"), dict) else {}
        margin_factor_unit = str(
            instrument.get("marginFactorUnit")
            or dealing_rules.get("marginFactorUnit")
            or market_info.get("marginFactorUnit")
            or snapshot.get("marginFactorUnit")
            or ""
        )
        candidates = [
            (instrument.get("marginFactor"), margin_factor_unit),
            (instrument.get("marginFactorPercent"), "PERCENTAGE"),
            (dealing_rules.get("marginFactor"), dealing_rules.get("marginFactorUnit") or margin_factor_unit),
            (snapshot.get("marginFactor"), snapshot.get("marginFactorUnit") or margin_factor_unit),
            (market_info.get("marginFactor"), market_info.get("marginFactorUnit") or margin_factor_unit),
        ]
        margin_bands = instrument.get("marginDepositBands")
        if isinstance(margin_bands, list):
            for band in margin_bands:
                if not isinstance(band, dict):
                    continue
                band_unit = str(band.get("marginFactorUnit") or band.get("unit") or margin_factor_unit)
                candidates.extend([
                    (band.get("margin"), band_unit),
                    (band.get("marginFactor"), band_unit),
                    (band.get("marginRate"), band_unit),
                    (band.get("value"), band_unit),
                ])
        for candidate, unit in candidates:
            value = self._normalize_capital_margin_pct(candidate, str(unit or ""))
            if value > 0:
                return value
        return 0.0

    @staticmethod
    def _estimate_capital_margin_required(size: float, price: float, margin_factor_pct: float) -> float:
        notional = max(float(size or 0.0) * float(price or 0.0), 0.0)
        margin_pct = max(float(margin_factor_pct or 0.0), 0.0)
        if notional <= 0 or margin_pct <= 0:
            return 0.0
        return notional * (margin_pct / 100.0)

    def _is_capital_risk_rejection(self, reason: str) -> bool:
        text = str(reason or "").strip().upper()
        if not text:
            return False
        risk_tokens = (
            "RISK_CHECK",
            "INSUFFICIENT",
            "NOT_ENOUGH",
            "NO_CASH",
            "NO_FUNDS",
            "MARGIN",
            "EQUITY",
            "FUNDS",
            "BALANCE",
        )
        return any(token in text for token in risk_tokens)

    def _market_status_text(self, market_info: dict) -> str:
        if not isinstance(market_info, dict):
            return "UNKNOWN"
        snapshot = market_info.get("snapshot", {}) if isinstance(market_info.get("snapshot"), dict) else {}
        instrument = market_info.get("instrument", {}) if isinstance(market_info.get("instrument"), dict) else {}
        for candidate in (
            snapshot.get("marketStatus"),
            market_info.get("marketStatus"),
            instrument.get("marketStatus"),
            instrument.get("tradingStatus"),
            market_info.get("status"),
        ):
            text = str(candidate or "").strip()
            if text:
                return text.upper()
        return "UNKNOWN"

    def _capital_preflight(self, symbol: str, size: float, ticker: dict, cfg: Optional[dict] = None) -> Dict[str, Any]:
        """Collect exchange-side constraints before placing a Capital market order."""
        preflight: Dict[str, Any] = {
            "symbol": symbol,
            "epic": str(ticker.get("epic") or symbol),
            "requested_size": float(size or 0.0),
            "available_balance": 0.0,
            "market_status": "UNKNOWN",
            "minimum_deal_size": 0.0,
            "price": float(ticker.get("price") or 0.0),
            "spread": 0.0,
            "spread_pct": 0.0,
            "margin_factor_pct": 0.0,
            "estimated_margin_required": 0.0,
            "expected_gross_profit": 0.0,
            "expected_net_profit": 0.0,
            "round_trip_cost": 0.0,
            "ok": False,
            "reason": "",
        }
        if not self.client:
            preflight["reason"] = "capital client unavailable"
            return preflight

        try:
            accounts = self.client.get_accounts()
        except Exception as _e:
            accounts = []
            preflight["accounts_error"] = str(_e)
        preflight["accounts"] = accounts
        preflight["available_balance"] = float(
            sum(float(acc.get("available", 0.0) or 0.0) for acc in accounts)
        )

        market_summary: Dict[str, Any] = {}
        market_detail: Dict[str, Any] = {}
        try:
            if hasattr(self.client, "_resolve_market"):
                resolved = self.client._resolve_market(symbol)  # type: ignore[attr-defined]
                if isinstance(resolved, dict):
                    market_summary = resolved
                    preflight["epic"] = str(resolved.get("epic") or preflight["epic"])
        except Exception as _e:
            preflight["market_resolve_error"] = str(_e)

        try:
            if hasattr(self.client, "_get_market_snapshot"):
                snapshot = self.client._get_market_snapshot(preflight["epic"])  # type: ignore[attr-defined]
                if isinstance(snapshot, dict):
                    market_detail = snapshot
        except Exception as _e:
            preflight["market_snapshot_error"] = str(_e)

        market_info = market_detail or market_summary
        preflight["market_status"] = self._market_status_text(market_info)
        preflight["minimum_deal_size"] = self._extract_capital_min_size(market_info)
        preflight["margin_factor_pct"] = self._extract_margin_factor_pct(
            market_info,
            str((cfg or {}).get("class", "") or ""),
        )

        snapshot = market_detail.get("snapshot", {}) if isinstance(market_detail.get("snapshot"), dict) else {}
        bid = float(
            ticker.get("bid")
            or snapshot.get("bid")
            or market_summary.get("bid")
            or 0.0
        )
        ask = float(
            ticker.get("ask")
            or snapshot.get("offer")
            or market_summary.get("offer")
            or 0.0
        )
        price = float(
            ticker.get("price")
            or ((bid + ask) / 2.0 if bid > 0 and ask > 0 else 0.0)
            or snapshot.get("midOpen")
            or 0.0
        )
        spread = max(ask - bid, 0.0) if bid > 0 and ask > 0 else 0.0
        preflight["price"] = price
        preflight["bid"] = bid
        preflight["ask"] = ask
        preflight["spread"] = spread
        preflight["spread_pct"] = (spread / price * 100.0) if price > 0 and spread > 0 else 0.0

        if isinstance(cfg, dict):
            effective_tp_pct = self._effective_tp_pct(price or ask or 0.0, preflight["requested_size"], cfg)
            cost_profile = self._capital_cost_profile(
                symbol,
                preflight["requested_size"],
                price or ask or 0.0,
                effective_tp_pct,
                bid=bid,
                ask=ask,
            )
            preflight.update(cost_profile)
            preflight["effective_tp_pct"] = effective_tp_pct
            margin_factor_pct = float(preflight.get("margin_factor_pct", 0.0) or 0.0)
            preflight["estimated_margin_required"] = self._estimate_capital_margin_required(
                preflight["requested_size"],
                price or ask or 0.0,
                margin_factor_pct,
            )

        if preflight["requested_size"] <= 0:
            preflight["reason"] = "requested size <= 0"
            return preflight
        if preflight["minimum_deal_size"] > 0 and preflight["requested_size"] < preflight["minimum_deal_size"]:
            preflight["reason"] = (
                f"requested size {preflight['requested_size']:.6g} below Capital minimum "
                f"{preflight['minimum_deal_size']:.6g}"
            )
            return preflight
        if preflight["available_balance"] <= 0:
            preflight["reason"] = "available account balance <= 0"
            return preflight
        allowed_statuses = {"TRADEABLE", "TRADEABLE_ONLINE", "OPEN", "EDITS_ONLY", "ONLINE"}
        market_status = str(preflight["market_status"] or "").upper()
        if market_status and market_status not in allowed_statuses and market_status != "UNKNOWN":
            preflight["reason"] = f"market not tradeable: {market_status}"
            return preflight
        if price <= 0 and ask <= 0:
            preflight["reason"] = "missing live price"
            return preflight
        if isinstance(cfg, dict) and float(preflight.get("expected_net_profit", 0.0) or 0.0) <= 0:
            preflight["reason"] = (
                f"expected net profit {float(preflight.get('expected_net_profit', 0.0) or 0.0):+.4f} "
                f"does not clear costs {float(preflight.get('round_trip_cost', 0.0) or 0.0):.4f}"
            )
            return preflight
        if (
            isinstance(cfg, dict)
            and float(preflight.get("estimated_margin_required", 0.0) or 0.0) > 0
            and float(preflight.get("available_balance", 0.0) or 0.0) < float(preflight.get("estimated_margin_required", 0.0) or 0.0)
        ):
            preflight["reason"] = (
                f"insufficient equity for estimated margin "
                f"{float(preflight.get('estimated_margin_required', 0.0) or 0.0):.2f} "
                f"> available {float(preflight.get('available_balance', 0.0) or 0.0):.2f}"
            )
            return preflight

        preflight["ok"] = True
        preflight["reason"] = "ok"
        return preflight

    def _sized_cfg_from_preflight(self, cfg: dict, preflight: Dict[str, Any]) -> Optional[dict]:
        """Raise size to Capital's minimum when that is affordable and otherwise valid."""
        adjusted = dict(cfg)
        requested_size = float(adjusted.get("size", 0.0) or 0.0)
        minimum_size = float(preflight.get("minimum_deal_size", 0.0) or 0.0)
        price = float(preflight.get("price", 0.0) or 0.0)
        available_balance = float(preflight.get("available_balance", 0.0) or 0.0)
        if minimum_size <= 0 or minimum_size <= requested_size:
            return adjusted
        if price <= 0:
            return None
        min_margin_required = 0.0
        margin_factor_pct = float(preflight.get("margin_factor_pct", 0.0) or 0.0)
        if margin_factor_pct > 0:
            min_margin_required = self._estimate_capital_margin_required(minimum_size, price, margin_factor_pct)
        else:
            reported_margin_required = float(preflight.get("estimated_margin_required", 0.0) or 0.0)
            if reported_margin_required > 0 and requested_size > 0:
                min_margin_required = reported_margin_required * (minimum_size / requested_size)
        if min_margin_required <= 0:
            min_margin_required = minimum_size * price
        if available_balance > 0 and min_margin_required > available_balance:
            return None
        adjusted["size"] = minimum_size
        return adjusted

    def _capital_cost_profile(
        self,
        symbol: str,
        size: float,
        price: float,
        tp_pct: float,
        *,
        bid: float = 0.0,
        ask: float = 0.0,
    ) -> Dict[str, float]:
        """Estimate whether a Capital trade clears execution costs with the configured target."""
        notional = max(float(size or 0.0) * float(price or 0.0), 0.0)
        expected_gross_profit = notional * (max(float(tp_pct or 0.0), 0.0) / 100.0)
        if self._trade_profit_validator is None or notional <= 0:
            return {
                "notional": notional,
                "expected_gross_profit": expected_gross_profit,
                "round_trip_cost": 0.0,
                "expected_net_profit": expected_gross_profit,
            }
        try:
            live_bid = float(bid or 0.0)
            live_ask = float(ask or 0.0)
            if live_bid <= 0 or live_ask <= 0:
                ticker = self._get_price(symbol) or {}
                live_bid = float(ticker.get("bid") or 0.0)
                live_ask = float(ticker.get("ask") or 0.0)
            live_spread_cost = 0.0
            if live_bid > 0 and live_ask > 0 and live_ask >= live_bid:
                # Capital CFDs are spread-priced already; model the real quoted spread,
                # not a generic percentage of notional from the validator profile.
                live_spread_cost = max(live_ask - live_bid, 0.0) * max(float(size or 0.0), 0.0)
            # Use a small fraction of the quoted spread as slippage, not a fraction of notional.
            slippage_cost = live_spread_cost * 0.25
            round_trip_cost = live_spread_cost + slippage_cost
        except Exception:
            round_trip_cost = 0.0
        return {
            "notional": notional,
            "expected_gross_profit": expected_gross_profit,
            "round_trip_cost": round_trip_cost,
            "expected_net_profit": expected_gross_profit - round_trip_cost,
        }

    # ── PRICES ─────────────────────────────────────────────────────────────────
    def _refresh_prices(self) -> None:
        """Fetch prices for all universe symbols (thread-safe via concurrent futures)."""
        if not self.client:
            return
        if time.time() - self._prices_fetched_at < CFD_CONFIG["price_ttl_secs"]:
            return
        try:
            raw = self.client.get_tickers_for_symbols(list(self._active_universe().keys()))
            if raw:
                with self._prices_lock:
                    self._prices = raw
                    self._prices_fetched_at = time.time()
        except Exception as _e:
            logger.debug(f"CFD price refresh error: {_e}")

    def _get_price(self, symbol: str) -> Optional[dict]:
        with self._prices_lock:
            return self._prices.get(symbol.upper())

    def _canonical_symbol(self, value: Optional[str]) -> str:
        if not value:
            return ""
        return "".join(ch for ch in str(value).upper() if ch.isalnum())

    def _active_universe(self) -> Dict[str, dict]:
        if not CAPITAL_FOCUS_SYMBOLS:
            return CAPITAL_UNIVERSE
        focused = {
            symbol: dict(cfg)
            for symbol, cfg in CAPITAL_UNIVERSE.items()
            if symbol.upper() in CAPITAL_FOCUS_SYMBOLS
        }
        return focused or CAPITAL_UNIVERSE

    def _continuous_watch_symbols(self) -> List[str]:
        watched: List[str] = []
        with self._state_lock:
            for symbol in self._active_universe().keys():
                watched.append(str(symbol).upper())
            for pos in getattr(self, "positions", []) or []:
                watched.append(str(getattr(pos, "symbol", "") or "").upper())
            for shadow in getattr(self, "shadow_trades", []) or []:
                watched.append(str(getattr(shadow, "symbol", "") or "").upper())
        seen = set()
        ordered: List[str] = []
        for symbol in watched:
            if symbol and symbol not in seen:
                seen.add(symbol)
                ordered.append(symbol)
        return ordered

    def _continuous_price_refresh_loop(self) -> None:
        while not self._live_refresh_stop.wait(max(0.2, CAPITAL_LIVE_REFRESH_INTERVAL_SECS)):
            try:
                if not self._ensure_client_ready():
                    continue
                symbols = self._continuous_watch_symbols()
                if not symbols:
                    continue
                with self._prices_lock:
                    previous_prices = dict(self._prices)
                raw = self.client.get_tickers_for_symbols(symbols) if self.client else {}
                if raw:
                    with self._state_lock:
                        with self._prices_lock:
                            self._prices.update(raw)
                            self._prices_fetched_at = time.time()
                        self._update_position_prices()
                        self._last_monitor = time.time()
                        live_closed = self._monitor_positions()
                        self._update_shadows()
                        self._handle_live_price_events(previous_prices, raw, force=bool(live_closed))
            except Exception as e:
                logger.debug("Capital live refresh loop error: %s", e)

    def _ensure_live_refresh(self) -> None:
        if not CAPITAL_LIVE_REFRESH_ENABLED:
            return
        thread = getattr(self, "_live_refresh_thread", None)
        if thread is not None and thread.is_alive():
            return
        self._live_refresh_stop.clear()
        self._live_refresh_thread = threading.Thread(
            target=self._continuous_price_refresh_loop,
            name="capital_live_refresh",
            daemon=True,
        )
        self._live_refresh_thread.start()

    def _handle_live_price_events(self, previous: Dict[str, dict], updated: Dict[str, dict], force: bool = False) -> None:
        now = time.time()
        if (now - float(getattr(self, "_last_live_event_at", 0.0) or 0.0)) < max(0.05, CAPITAL_LIVE_EVENT_MIN_INTERVAL_SECS):
            return
        trigger_pct = max(0.0, float(CAPITAL_LIVE_EVENT_TRIGGER_PCT or 0.0))
        meaningful = bool(force)
        if not meaningful:
            for symbol, quote in (updated or {}).items():
                prev = (previous or {}).get(symbol, {}) if isinstance(previous, dict) else {}
                new_price = float((quote or {}).get("price", 0.0) or 0.0)
                old_price = float((prev or {}).get("price", 0.0) or 0.0)
                if new_price <= 0:
                    continue
                if old_price <= 0:
                    meaningful = True
                    break
                move_pct = abs((new_price - old_price) / old_price) * 100.0
                if move_pct >= trigger_pct:
                    meaningful = True
                    break
        if not meaningful:
            return
        self._last_live_event_at = now
        try:
            self._refresh_unified_intel_snapshot()
            self._refresh_thought_bus_snapshot()
            self._quad_gate()  # refresh modifier (always proceeds)
            self._find_best_opportunity()
            self._queue_background_shadows()
            if len(self.positions) < int(CFD_CONFIG["max_positions"]):
                if self._fill_live_monitoring_slots(now):
                    self._latest_monitor_line = self._latest_monitor_line or "CAPITAL LIVE EVENT FILL"
        except Exception as e:
            logger.debug("Capital live event actuation error: %s", e)

    def _symbol_from_market(self, market: dict) -> str:
        candidates = [
            market.get("symbol"),
            market.get("instrumentName"),
            market.get("epic"),
            market.get("marketId"),
        ]
        for candidate in candidates:
            canon = self._canonical_symbol(candidate)
            if canon in CAPITAL_UNIVERSE:
                return canon
        for candidate in candidates:
            canon = self._canonical_symbol(candidate)
            for known in CAPITAL_UNIVERSE:
                if canon == self._canonical_symbol(known):
                    return known
        return self._canonical_symbol(candidates[0]) or str(candidates[0] or "")

    def _position_from_exchange(self, raw: dict) -> Optional[CFDPosition]:
        position = raw.get("position", {}) if isinstance(raw, dict) else {}
        market = raw.get("market", {}) if isinstance(raw, dict) else {}

        deal_id = str(position.get("dealId") or position.get("dealReference") or "").strip()
        direction = str(position.get("direction") or "").upper()
        size = float(position.get("size", 0.0) or 0.0)
        entry_price = float(position.get("level", 0.0) or 0.0)
        epic = str(market.get("epic") or position.get("epic") or "").strip()
        symbol = self._symbol_from_market(market or position)
        if not deal_id or direction not in ("BUY", "SELL") or size <= 0 or entry_price <= 0:
            return None

        price = float(market.get("price") or 0.0)
        bid = float(market.get("bid") or 0.0)
        ask = float(market.get("offer") or market.get("ask") or 0.0)
        current_price = price or ((bid + ask) / 2 if bid > 0 and ask > 0 else bid or ask or entry_price)

        asset_class = str(market.get("instrumentType") or market.get("marketType") or "").lower()
        if not asset_class:
            asset_class = CAPITAL_UNIVERSE.get(symbol, {}).get("class", "unknown")

        tp_level = float(position.get("limitLevel", 0.0) or 0.0)
        sl_level = float(position.get("stopLevel", 0.0) or 0.0)
        cfg = CAPITAL_UNIVERSE.get(symbol, {})
        tp_pct = self._effective_tp_pct(entry_price, size, cfg)
        sl_pct = float(cfg.get("sl_pct", 0.0) or 0.0)
        if tp_level <= 0:
            tp_level = entry_price * (1 + tp_pct / 100.0) if direction == "BUY" else entry_price * (1 - tp_pct / 100.0)
        if sl_level <= 0:
            sl_level = entry_price * (1 - sl_pct / 100.0) if direction == "BUY" else entry_price * (1 + sl_pct / 100.0)

        opened_at = time.time()
        raw_created = position.get("createdDateUTC") or position.get("createdDate")
        if isinstance(raw_created, (int, float)):
            opened_at = float(raw_created)

        return CFDPosition(
            symbol=symbol,
            deal_id=deal_id,
            epic=epic or symbol,
            direction=direction,
            size=size,
            entry_price=entry_price,
            tp_price=tp_level,
            sl_price=sl_level,
            asset_class=asset_class,
            opened_at=opened_at,
            current_price=current_price,
        )

    def _sync_positions_from_exchange(self, force: bool = False) -> None:
        """Reconcile local CFD position state against Capital.com's open positions."""
        if not self.client:
            return
        now = time.time()
        if not force and (now - self._last_exchange_sync) < CFD_CONFIG["exchange_sync_secs"]:
            return
        self._last_exchange_sync = now

        try:
            raw_positions = self.client.get_positions()
            live_positions: List[CFDPosition] = []
            for raw in raw_positions:
                pos = self._position_from_exchange(raw)
                if pos is not None:
                    live_positions.append(pos)

            existing_by_deal = {p.deal_id: p for p in self.positions}
            merged: List[CFDPosition] = []
            for live in live_positions:
                existing = existing_by_deal.get(live.deal_id)
                if existing is not None:
                    live.opened_at = existing.opened_at
                    if existing.current_price > 0:
                        live.current_price = existing.current_price
                merged.append(live)

            self.positions = merged
        except Exception as _e:
            logger.debug(f"Capital CFD sync error: {_e}")

    # ── QUADRUMVIRATE GATE (lightweight) ───────────────────────────────────────
    def _quad_gate(self) -> float:
        """
        Quick Seer + Lyra sizing check — cached for quad_gate_ttl secs.
        Returns a sizing modifier (0.09–1.0) instead of blocking.
        Always allows trading; poor conditions just reduce size.
        """
        if not HAS_QUAD_GATES:
            return 1.0
        now = time.time()
        if now - self._quad_gate_at < CFD_CONFIG["quad_gate_ttl"]:
            return self._quad_gate_modifier
        self._quad_gate_at = now
        try:
            seer_ok = seer_should_trade() if seer_should_trade else True   # type: ignore[misc]
            lyra_ok = lyra_should_trade() if lyra_should_trade else True   # type: ignore[misc]
            seer_factor = 1.0 if seer_ok else 0.3
            lyra_factor = 1.0 if lyra_ok else 0.3
            self._quad_gate_modifier = seer_factor * lyra_factor
        except Exception:
            self._quad_gate_modifier = 1.0   # Fail-open
        return self._quad_gate_modifier

    # ── OPPORTUNITY SCANNER ────────────────────────────────────────────────────
    def _score_symbol(self, symbol: str, cfg: dict, ticker: dict) -> Tuple[float, str]:
        """
        Score a candidate for BUY/SELL entry.
        Returns (0.0, "") = skip; (>0.0, direction) = attractive, higher is better.

        Scoring:
          base = momentum magnitude (abs(change_pct))
          penalty = spread quality cost
          gate = spread too wide → 0
          gate = abs(momentum) below threshold → 0
        """
        price      = float(ticker.get("price") or 0)
        bid        = float(ticker.get("bid")   or 0)
        ask        = float(ticker.get("ask")   or 0)
        change_pct = float(ticker.get("change_pct") or 0)

        if price <= 0 or bid <= 0 or ask <= 0:
            return 0.0, ""

        # Spread guard
        spread_pct = (ask - bid) / price * 100
        max_spread = cfg.get("max_spread_pct", 0.2) * 100   # convert → %
        if spread_pct > max_spread:
            return 0.0, ""

        # Momentum gate — trade in the direction of the move
        threshold = cfg.get("momentum_threshold", 0.10)
        if abs(change_pct) < threshold:
            return 0.0, ""
        direction = "BUY" if change_pct > 0 else "SELL"

        # Score = momentum minus spread drag
        score = abs(change_pct) - spread_pct * 0.15

        # Must have enough room to clear the realized-profit floor.
        size = float(cfg.get("size", 0.0) or 0.0)
        required_tp_pct = self._required_tp_pct_for_profit(price, size)
        effective_tp_pct = self._effective_tp_pct(price, size, cfg)
        if effective_tp_pct <= 0:
            return 0.0, ""

        expected_profit_gbp = price * size * (effective_tp_pct / 100.0)
        if expected_profit_gbp < CAPITAL_MIN_PROFIT_GBP:
            return 0.0, ""

        score += min(1.0, expected_profit_gbp / max(CAPITAL_MIN_PROFIT_GBP, 0.0001)) * 0.25

        # Time-to-profit is a selection signal only: prefer the quickest realistic route
        # to the configured realized-profit floor, but never force a close because of time.
        threshold_safe = max(float(threshold or 0.0), 0.01)
        momentum_speed = max(abs(change_pct), threshold_safe)
        eta_to_target = required_tp_pct / momentum_speed if momentum_speed > 0 else 999.0
        eta_score = max(0.0, 2.0 - eta_to_target)
        score += eta_score * 0.5

        # Hive Mind ripple amplifier — Market Harp signals shared by TradingHiveMind
        # A ripple on a correlated market boosts this symbol's momentum score
        hive_factor = self._hive_boosts.get(symbol, self._hive_boosts.get(symbol.upper(), 0.0))
        if hive_factor > 0:
            score = score * (1.0 + float(hive_factor) * 0.40)

        central_symbols = getattr(self, "_central_beat_symbols", {}) or {}
        central_regime = getattr(self, "_central_beat_regime", {}) or {}
        central_signal = central_symbols.get(symbol) or central_symbols.get(symbol.upper()) or {}
        if isinstance(central_signal, dict) and central_signal:
            support_count = max(1, int(central_signal.get("support_count", 1) or 1))
            central_side = str(central_signal.get("side") or direction).upper()
            central_strength = max(0.0, float(central_signal.get("strength", 0.0) or 0.0))
            aligned = central_side == direction
            multiplier = 1.0 + min(0.18, central_strength * 0.12 + (support_count - 1) * 0.03)
            if aligned:
                score *= multiplier
            else:
                score *= max(0.82, 1.0 - min(0.18, central_strength * 0.10))

        if isinstance(central_regime, dict) and central_regime:
            regime_bias = str(central_regime.get("bias") or direction).upper()
            regime_conf = max(0.0, min(1.0, float(central_regime.get("confidence", 0.0) or 0.0)))
            if regime_conf > 0:
                regime_multiplier = 1.0 + regime_conf * 0.05 if regime_bias == direction else 1.0 - regime_conf * 0.05
                score *= max(0.9, regime_multiplier)

        return max(0.0, score), direction

    def _apply_hft_analysis(self, scored: List[Dict[str, Any]]) -> None:
        """Use the repo's viable HFT/intel helpers on Capital candidates."""
        positive_scores = [float(item.get("score", 0.0) or 0.0) for item in scored if float(item.get("score", 0.0) or 0.0) > 0]
        for item in scored:
            symbol = str(item.get("symbol") or "")
            score = float(item.get("score", 0.0) or 0.0)
            size = float(item.get("size", 0.0) or 0.0)
            price = float(item.get("price", 0.0) or 0.0)
            change_pct = float(item.get("change_pct", 0.0) or 0.0)
            spread_pct = float(item.get("spread_pct", 0.0) or 0.0)
            tp_pct = float(item.get("tp_pct", 0.0) or 0.0)

            cost_profile = self._capital_cost_profile(symbol, size, price, tp_pct)
            item.update(cost_profile)
            if cost_profile["expected_net_profit"] <= 0:
                item["hft_reason"] = "cost_gate"
                item["score"] = 0.0
                continue

            if self._signal_brain is None:
                item["brain_coherence"] = 0.0
                continue

            threshold = max(float(CAPITAL_UNIVERSE.get(symbol, {}).get("momentum_threshold", 0.1) or 0.1), 0.01)
            features = {
                "momentum": change_pct,
                "volatility": max(spread_pct, 0.0001),
                "trend_strength": min(abs(change_pct) / threshold, 1.0),
                "rsi": 50.0 + max(-45.0, min(45.0, change_pct * 10.0)),
            }
            try:
                decision = self._signal_brain.decide(symbol, score, features, positive_scores or [score])
            except Exception:
                decision = None

            if decision is None:
                item["brain_coherence"] = 0.0
                item["hft_reason"] = "brain_gate"
                item["score"] = 0.0
                continue

            item["brain_coherence"] = float(decision.coherence)
            item["score"] = float(decision.score)

    def _score_timeline_oracle(self, symbol: str, side: str, price: float, change_pct: float) -> Dict[str, Any]:
        result = {"bonus": 0.0, "action": "hold", "confidence": 0.0, "reason": ""}
        if self.timeline_oracle is None:
            return result
        try:
            action, confidence, reason = self.timeline_oracle.get_approved_action(
                symbol=symbol,
                price=price,
                volume=max(abs(change_pct), 0.01),
                change_pct=change_pct,
            )
            action_value = getattr(action, "value", "hold") if action is not None else "hold"
            confidence = float(confidence or 0.0)
            expected = "buy" if str(side).upper() == "BUY" else "sell"
            bonus = (confidence - 0.5) * 2.0
            if action_value == expected:
                bonus += 0.5
            elif action_value not in {"hold", "wait"}:
                bonus -= 0.75
            result.update({
                "bonus": max(-1.5, min(2.0, bonus)),
                "action": action_value,
                "confidence": confidence,
                "reason": str(reason or ""),
            })
        except Exception as e:
            result["error"] = str(e)
        self._timeline_snapshot = {"symbol": symbol, "side": str(side).upper(), **result}
        return result

    def _score_harmonic_fusion(self, symbol: str, side: str) -> Dict[str, Any]:
        result = {"bonus": 0.0, "global_coherence": 0.0, "symbol_coherence": 0.0}
        if self.harmonic_fusion is None:
            return result
        try:
            state = self.harmonic_fusion.get_harmonic_state() or {}
            phase = self.harmonic_fusion.get_symbol_phase(symbol) or {}
            global_coh = float(state.get("global_coherence", 0.0) or 0.0)
            symbol_coh = float(phase.get("coherence", phase.get("amplitude", 0.0)) or 0.0)
            bonus = max(-1.5, min(2.0, (global_coh - 0.5) * 2.0 + (symbol_coh - 0.5) * 2.0))
            result.update({
                "bonus": bonus,
                "global_coherence": global_coh,
                "symbol_coherence": symbol_coh,
            })
        except Exception as e:
            result["error"] = str(e)
        self._fusion_snapshot = {"symbol": symbol, "side": str(side).upper(), **result}
        return result

    def _orchestrator_pretrade_gate(self, symbol: str, side: str) -> Dict[str, Any]:
        result = {"approved": True, "reason": "orchestrator_unavailable", "sizing": {}}
        if self.orchestrator is None:
            return result
        try:
            approved, reason, sizing = self.orchestrator.gate_pre_trade(symbol, str(side).lower())
            result = {
                "approved": bool(approved),
                "reason": str(reason or "ok"),
                "sizing": sizing or {},
            }
        except Exception as e:
            result = {"approved": True, "reason": f"fail_open:{e}", "sizing": {}}
        self._orchestrator_snapshot = {"symbol": symbol, "side": str(side).upper(), **result}
        return result

    def _apply_intelligence_overlays(self, scored: List[Dict[str, Any]]) -> None:
        """Apply higher-level signal systems from the main margin trader to Capital candidates."""
        for item in scored:
            base_score = float(item.get("score", 0.0) or 0.0)
            if base_score <= 0:
                continue
            symbol = str(item.get("symbol") or "")
            side = str(item.get("direction") or "BUY").upper()
            price = float(item.get("price", 0.0) or 0.0)
            change_pct = float(item.get("change_pct", 0.0) or 0.0)

            timeline = self._score_timeline_oracle(symbol, side, price, change_pct)
            fusion = self._score_harmonic_fusion(symbol, side)
            gate = self._orchestrator_pretrade_gate(symbol, side)

            item["timeline_bonus"] = float(timeline.get("bonus", 0.0) or 0.0)
            item["timeline_action"] = str(timeline.get("action", "hold") or "hold")
            item["timeline_confidence"] = float(timeline.get("confidence", 0.0) or 0.0)
            item["fusion_bonus"] = float(fusion.get("bonus", 0.0) or 0.0)
            item["fusion_global_coherence"] = float(fusion.get("global_coherence", 0.0) or 0.0)
            item["fusion_symbol_coherence"] = float(fusion.get("symbol_coherence", 0.0) or 0.0)
            item["orchestrator_reason"] = str(gate.get("reason") or "")
            item["orchestrator_approved"] = bool(gate.get("approved"))

            # Extract Queen's sizing modifier from the orchestrator
            raw_sizing = gate.get("sizing", 1.0)
            queen_sizing = max(0.10, min(2.0, float(raw_sizing) if not isinstance(raw_sizing, dict) else 1.0))
            item["queen_sizing"] = queen_sizing

            if not gate.get("approved"):
                # Cross-system conflict is the only hard block — zero the score
                item["score"] = 0.0
                item["intel_reason"] = f"orchestrator_gate:{gate.get('reason') or 'blocked'}"
                continue

            item["score"] = max(
                0.0,
                base_score
                + float(timeline.get("bonus", 0.0) or 0.0) * 1.25
                + float(fusion.get("bonus", 0.0) or 0.0) * 1.0
            )
            confidence = self._compute_self_confidence(item)
            item["self_confidence"] = float(confidence.get("score", 0.0) or 0.0)
            item["self_confidence_boost"] = float(confidence.get("boost_multiplier", 1.0) or 1.0)
            item["self_confidence_reason"] = str(confidence.get("reason") or "")
            item["score"] = max(0.0, float(item.get("score", 0.0) or 0.0) * item["self_confidence_boost"])

    def _direction_counts(self) -> Dict[str, int]:
        counts = {"BUY": 0, "SELL": 0}
        for pos in self.positions:
            direction = str(getattr(pos, "direction", "") or "").upper()
            if direction in counts:
                counts[direction] += 1
        return counts

    def _cooldown_key(self, symbol: str, direction: str) -> str:
        return f"{self._canonical_symbol(symbol)}|{str(direction or '').upper()}"

    def _record_rejection(self, symbol: str, direction: str, reason: str) -> None:
        cooldown_secs = CAPITAL_RISK_REJECTION_COOLDOWN_SECS if self._is_capital_risk_rejection(reason) else CAPITAL_REJECTION_COOLDOWN_SECS
        self._rejection_cooldowns[self._cooldown_key(symbol, direction)] = {
            "until": time.time() + max(1.0, cooldown_secs),
            "reason": str(reason or "rejected"),
        }

    def _cooldown_info(self, symbol: str, direction: str) -> Optional[Dict[str, Any]]:
        key = self._cooldown_key(symbol, direction)
        info = self._rejection_cooldowns.get(key)
        if not info:
            return None
        if time.time() >= float(info.get("until", 0.0) or 0.0):
            self._rejection_cooldowns.pop(key, None)
            return None
        return info

    def _has_live_reading(self, ticker: Optional[dict]) -> bool:
        if not isinstance(ticker, dict):
            return False
        price = float(ticker.get("price") or 0.0)
        bid = float(ticker.get("bid") or 0.0)
        ask = float(ticker.get("ask") or 0.0)
        return price > 0 and bid > 0 and ask > 0 and ask >= bid

    def _preflight_allows_slot_fill(self, preflight: Dict[str, Any]) -> bool:
        if not isinstance(preflight, dict):
            return False
        if bool(preflight.get("ok")):
            return True
        reason = str(preflight.get("reason") or "").lower()
        return "expected net profit" in reason and self._has_live_reading({
            "price": preflight.get("price"),
            "bid": preflight.get("bid"),
            "ask": preflight.get("ask"),
        })

    def _preflight_allows_shadow(self, preflight: Dict[str, Any]) -> bool:
        if not isinstance(preflight, dict):
            return False
        if bool(preflight.get("ok")):
            return True
        reason = str(preflight.get("reason") or "").lower()
        return "expected net profit" in reason and self._has_live_reading({
            "price": preflight.get("price"),
            "bid": preflight.get("bid"),
            "ask": preflight.get("ask"),
        })

    def _ranked_live_slot_candidates(self, direction: str) -> List[Tuple[str, dict, dict]]:
        ranked: List[Tuple[str, dict, dict]] = []
        wanted = str(direction or "").upper()
        if wanted not in {"BUY", "SELL"}:
            return ranked
        counts = self._direction_counts()
        for candidate in list(getattr(self, "_latest_candidate_snapshot", []) or []):
            symbol = str(candidate.get("symbol") or "").upper()
            candidate_direction = str(candidate.get("direction") or "BUY").upper()
            cfg = CAPITAL_UNIVERSE.get(symbol)
            ticker = self._get_price(symbol)
            if candidate_direction != wanted or not symbol or not cfg or not ticker:
                continue
            if not self._has_live_reading(ticker):
                continue
            if not self._can_open_candidate(symbol, wanted, counts):
                continue
            ranked.append((symbol, {**dict(cfg), "direction": wanted}, ticker))
        return ranked

    def _build_lane_snapshot(self) -> Dict[str, Any]:
        lanes: Dict[str, Dict[str, Any]] = {}
        for direction in ("BUY", "SELL"):
            open_pos = next(
                (pos for pos in self.positions if str(pos.direction or "").upper() == direction),
                None,
            )
            validated_shadow = next(
                (
                    shadow for shadow in self.shadow_trades
                    if str(shadow.direction or "").upper() == direction and shadow.validated
                ),
                None,
            )
            queued_shadow = next(
                (
                    shadow for shadow in self.shadow_trades
                    if str(shadow.direction or "").upper() == direction and not shadow.validated
                ),
                None,
            )
            lane: Dict[str, Any] = {
                "direction": direction,
                "occupied": open_pos is not None,
                "hunting": open_pos is None,
                "position_symbol": getattr(open_pos, "symbol", ""),
                "validated_shadow_symbol": getattr(validated_shadow, "symbol", ""),
                "queued_shadow_symbol": getattr(queued_shadow, "symbol", ""),
            }
            if validated_shadow is not None:
                lane["next_action"] = "promote_validated_shadow"
            elif queued_shadow is not None:
                lane["next_action"] = "monitor_shadow"
            elif open_pos is not None:
                lane["next_action"] = "manage_live_position"
            else:
                lane["next_action"] = "scan_for_candidate"
            lanes[direction] = lane
        self._lane_snapshot = lanes
        return lanes

    def _build_swarm_snapshot(self, scored: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build a lightweight multi-agent consensus over ranked Capital candidates."""
        ranked = [
            dict(item)
            for item in scored
            if float(item.get("score", 0.0) or 0.0) > 0
        ]
        ranked.sort(key=lambda item: float(item.get("score", 0.0) or 0.0), reverse=True)
        if not ranked:
            return {"enabled": True, "leader": {}, "votes": [], "ranked": []}

        scout_pick = max(
            ranked,
            key=lambda item: (
                abs(float(item.get("change_pct", 0.0) or 0.0)),
                float(item.get("score", 0.0) or 0.0),
            ),
        )
        tactician_pick = max(
            ranked,
            key=lambda item: (
                float(item.get("expected_net_profit", 0.0) or 0.0),
                float(item.get("score", 0.0) or 0.0),
            ),
        )
        risk_pick = max(
            ranked,
            key=lambda item: (
                -float(item.get("spread_pct", 999.0) or 999.0),
                float(item.get("brain_coherence", 0.0) or 0.0),
                float(item.get("score", 0.0) or 0.0),
            ),
        )
        execution_pick = max(
            ranked,
            key=lambda item: (
                -float(item.get("eta_to_target", 999.0) or 999.0),
                float(item.get("expected_net_profit", 0.0) or 0.0),
                float(item.get("score", 0.0) or 0.0),
            ),
        )

        votes = [
            CapitalSwarmAgentVote(
                agent="scout",
                symbol=str(scout_pick.get("symbol") or ""),
                direction=str(scout_pick.get("direction") or "BUY").upper(),
                score=float(scout_pick.get("score", 0.0) or 0.0),
                confidence=min(1.0, abs(float(scout_pick.get("change_pct", 0.0) or 0.0)) / 3.0),
                rationale=f"momentum {float(scout_pick.get('change_pct', 0.0) or 0.0):+.3f}%",
            ),
            CapitalSwarmAgentVote(
                agent="tactician",
                symbol=str(tactician_pick.get("symbol") or ""),
                direction=str(tactician_pick.get("direction") or "BUY").upper(),
                score=float(tactician_pick.get("score", 0.0) or 0.0),
                confidence=min(1.0, max(0.0, float(tactician_pick.get("expected_net_profit", 0.0) or 0.0) * 20.0)),
                rationale=f"net £{float(tactician_pick.get('expected_net_profit', 0.0) or 0.0):+.4f}",
            ),
            CapitalSwarmAgentVote(
                agent="risk",
                symbol=str(risk_pick.get("symbol") or ""),
                direction=str(risk_pick.get("direction") or "BUY").upper(),
                score=float(risk_pick.get("score", 0.0) or 0.0),
                confidence=min(1.0, 1.0 / max(float(risk_pick.get("spread_pct", 1.0) or 1.0), 0.01) * 0.05),
                rationale=f"spread {float(risk_pick.get('spread_pct', 0.0) or 0.0):.3f}%",
            ),
            CapitalSwarmAgentVote(
                agent="execution",
                symbol=str(execution_pick.get("symbol") or ""),
                direction=str(execution_pick.get("direction") or "BUY").upper(),
                score=float(execution_pick.get("score", 0.0) or 0.0),
                confidence=min(1.0, 1.0 / max(float(execution_pick.get("eta_to_target", 1.0) or 1.0), 0.1)),
                rationale=f"eta {float(execution_pick.get('eta_to_target', 0.0) or 0.0):.2f}",
            ),
        ]

        weighted: Dict[str, float] = {}
        for vote in votes:
            key = f"{vote.symbol}|{vote.direction}"
            weighted[key] = weighted.get(key, 0.0) + max(vote.confidence, 0.05) * max(vote.score, 0.0)

        ranked_keys = sorted(weighted.items(), key=lambda item: item[1], reverse=True)
        ranked_consensus: List[Dict[str, Any]] = []
        for key, swarm_score in ranked_keys:
            symbol, direction = key.split("|", 1)
            source = next(
                (
                    item for item in ranked
                    if str(item.get("symbol") or "") == symbol and str(item.get("direction") or "BUY").upper() == direction
                ),
                None,
            )
            if source is None:
                continue
            ranked_consensus.append({
                "symbol": symbol,
                "direction": direction,
                "swarm_score": swarm_score,
                "score": float(source.get("score", 0.0) or 0.0),
                "expected_net_profit": float(source.get("expected_net_profit", 0.0) or 0.0),
                "spread_pct": float(source.get("spread_pct", 0.0) or 0.0),
                "eta_to_target": float(source.get("eta_to_target", 0.0) or 0.0),
            })

        leader = dict(ranked_consensus[0]) if ranked_consensus else {}
        if leader:
            leader["votes"] = sum(
                1 for vote in votes
                if vote.symbol == leader["symbol"] and vote.direction == leader["direction"]
            )
        return {
            "enabled": True,
            "leader": leader,
            "votes": [vote.to_dict() for vote in votes],
            "ranked": ranked_consensus,
        }

    def _probability_validation_snapshot(self, force: bool = False) -> Dict[str, Any]:
        now = time.time()
        cached_snapshot = dict(getattr(self, "_probability_snapshot", {}) or {})
        cached_at = float(getattr(self, "_probability_snapshot_at", 0.0) or 0.0)
        if not force and cached_snapshot and (now - cached_at) < 30.0:
            return dict(cached_snapshot)

        payload: Dict[str, Any] = {
            "ok": False,
            "direction_accuracy": 0.0,
            "profit_factor": 0.0,
            "updated": "",
            "reason": "file_missing",
        }
        report_path = Path(os.path.join(os.path.dirname(__file__), "..", "..", "state", "reports", "probability_validation.json")).resolve()
        try:
            if report_path.exists():
                raw = json.loads(report_path.read_text(encoding="utf-8"))
                stats = raw.get("stats", {}) if isinstance(raw, dict) else {}
                payload = {
                    "ok": True,
                    "direction_accuracy": float(stats.get("direction_accuracy", 0.0) or 0.0),
                    "profit_factor": float(stats.get("profit_factor", 0.0) or 0.0),
                    "updated": str(raw.get("updated") or ""),
                    "reason": "ok",
                }
        except Exception as e:
            payload = {
                "ok": False,
                "direction_accuracy": 0.0,
                "profit_factor": 0.0,
                "updated": "",
                "reason": f"load_error:{e}",
            }
        self._probability_snapshot = payload
        self._probability_snapshot_at = now
        return dict(payload)

    def _compute_self_confidence(self, candidate: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        snapshot: Dict[str, Any] = {
            "enabled": CAPITAL_SELF_CONFIDENCE_ENABLED,
            "score": 0.0,
            "boost_multiplier": 1.0,
            "validation_window_secs": self.SHADOW_MIN_VALIDATE,
            "recent_success_ratio": 0.0,
            "alignment_score": 0.0,
            "rejection_pressure": 0.0,
            "reason": "disabled" if not CAPITAL_SELF_CONFIDENCE_ENABLED else "cold_start",
        }
        if not CAPITAL_SELF_CONFIDENCE_ENABLED:
            self._self_confidence_snapshot = snapshot
            return dict(snapshot)

        opened = float((self.stats or {}).get("trades_opened", 0.0) or 0.0)
        validated = float(getattr(self, "_shadow_validated_count", 0) or 0.0)
        failed = float(getattr(self, "_shadow_failed_count", 0) or 0.0)
        completed_cycles = validated + failed
        if completed_cycles > 0:
            recent_success_ratio = validated / completed_cycles
        elif opened > 0:
            wins = float((self.stats or {}).get("winning_trades", 0.0) or 0.0)
            recent_success_ratio = wins / max(opened, 1.0)
        else:
            recent_success_ratio = 0.5

        alignment_inputs: List[float] = []
        source = dict(candidate or getattr(self, "_latest_target_snapshot", {}) or {})
        for key in ("brain_coherence", "timeline_confidence", "fusion_global_coherence"):
            try:
                value = float(source.get(key, 0.0) or 0.0)
            except Exception:
                value = 0.0
            if value > 0:
                alignment_inputs.append(max(0.0, min(1.0, value)))
        alignment_score = sum(alignment_inputs) / len(alignment_inputs) if alignment_inputs else 0.5

        cooldowns = [
            info for info in getattr(self, "_rejection_cooldowns", {}).values()
            if float((info or {}).get("until", 0.0) or 0.0) > time.time()
        ]
        rejection_pressure = min(1.0, len(cooldowns) / 4.0)

        raw_score = (recent_success_ratio * 0.5) + (alignment_score * 0.4) + ((1.0 - rejection_pressure) * 0.1)
        score = max(0.0, min(1.0, raw_score))
        boost_multiplier = 1.0 + max(0.0, score - 0.5) * 2.0 * max(0.0, CAPITAL_SELF_CONFIDENCE_MAX_BOOST)
        validation_floor = max(0.5, float(CAPITAL_SELF_CONFIDENCE_MIN_VALIDATE_SECS or 4.0))
        validation_window = max(
            validation_floor,
            float(self.SHADOW_MIN_VALIDATE) - max(0.0, score - 0.55) * (float(self.SHADOW_MIN_VALIDATE) - validation_floor),
        )

        snapshot.update({
            "score": score,
            "boost_multiplier": boost_multiplier,
            "validation_window_secs": validation_window,
            "recent_success_ratio": recent_success_ratio,
            "alignment_score": alignment_score,
            "rejection_pressure": rejection_pressure,
            "reason": "armed" if score >= 0.55 else "warming_up",
        })
        self._self_confidence_snapshot = snapshot
        return dict(snapshot)

    def _compute_growth_metrics(self) -> Dict[str, Any]:
        runtime_secs = max(1.0, time.time() - float(getattr(self, "start_time", time.time()) or time.time()))
        runtime_hours = runtime_secs / 3600.0
        pnl_gbp = float((self.stats or {}).get("total_pnl_gbp", 0.0) or 0.0)
        trades_closed = int((self.stats or {}).get("trades_closed", 0.0) or 0.0)
        wins = int((self.stats or {}).get("winning_trades", 0.0) or 0.0)
        losses = int((self.stats or {}).get("losing_trades", 0.0) or 0.0)
        equity_now = float(self.get_capital_snapshot().get("equity_gbp", 0.0) or 0.0)
        equity_start = float(getattr(self, "starting_equity_gbp", 0.0) or 0.0)
        equity_growth_pct = ((equity_now - equity_start) / equity_start * 100.0) if equity_start > 0 else 0.0
        pnl_per_hour = pnl_gbp / runtime_hours if runtime_hours > 0 else 0.0
        trades_per_hour = trades_closed / runtime_hours if runtime_hours > 0 else 0.0
        avg_pnl = pnl_gbp / trades_closed if trades_closed > 0 else 0.0
        recent = list(getattr(self, "_recent_closed_trades", []) or [])[-3:]
        recent_pnl = sum(float(item.get("net_pnl", 0.0) or 0.0) for item in recent)
        recent_avg = recent_pnl / len(recent) if recent else 0.0
        if recent_avg > avg_pnl + 1e-9:
            trend = "accelerating"
        elif recent_avg < avg_pnl - 1e-9:
            trend = "cooling"
        else:
            trend = "steady"
        return {
            "runtime_hours": runtime_hours,
            "equity_growth_pct": equity_growth_pct,
            "pnl_per_hour_gbp": pnl_per_hour,
            "trades_per_hour": trades_per_hour,
            "avg_pnl_per_close_gbp": avg_pnl,
            "recent_avg_pnl_gbp": recent_avg,
            "recent_total_pnl_gbp": recent_pnl,
            "win_rate": (wins / trades_closed) if trades_closed > 0 else 0.0,
            "closed_trades": trades_closed,
            "wins": wins,
            "losses": losses,
            "trend": trend,
        }

    def _build_harmonic_wiring_audit(self) -> Dict[str, Any]:
        """Audit harmonic/probability subsystem wiring required by Capital trader."""
        root = Path(os.path.join(os.path.dirname(__file__), "..", "..")).resolve()
        checks: List[Dict[str, Any]] = []

        import_specs = [
            ("timeline_oracle", "aureon.intelligence.aureon_timeline_oracle", "get_timeline_oracle"),
            ("harmonic_fusion", "aureon.harmonic.aureon_harmonic_fusion", "HarmonicWaveFusion"),
            ("unified_decision_engine", "aureon.intelligence.aureon_unified_decision_engine", "UnifiedDecisionEngine"),
            ("harmonic_nexus_bridge", "aureon.harmonic.harmonic_nexus_bridge", "HarmonicNexusBridge"),
            ("global_harmonic_field", "aureon.harmonic.global_harmonic_field", "GlobalHarmonicField"),
            ("probability_intelligence_matrix", "aureon.strategies.probability_intelligence_matrix", "ProbabilityIntelligenceMatrix"),
            ("hnc_probability_integration", "aureon.strategies.hnc_probability_matrix", "HNCProbabilityIntegration"),
            ("thought_bus", "aureon.core.aureon_thought_bus", "get_thought_bus"),
        ]
        for name, module_name, attr_name in import_specs:
            item = {
                "name": name,
                "kind": "import",
                "target": f"{module_name}:{attr_name}",
                "ok": False,
                "reason": "",
            }
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, attr_name):
                    item["ok"] = True
                    item["reason"] = "ok"
                else:
                    item["reason"] = "attribute_missing"
            except Exception as e:
                item["reason"] = str(e)
            checks.append(item)

        file_specs = [
            ("probability_validation_report", root / "state" / "reports" / "probability_validation.json"),
            ("trained_probability_matrix", root / "state" / "trained_probability_matrix.json"),
            ("wave_monitor_final", root / "state" / "wave_monitor_final.json"),
            ("money_flow_timeline", root / "state" / "money_flow_timeline.json"),
            ("harmonic_wave_data", root / "state" / "harmonic_wave_data.json"),
        ]
        for name, path in file_specs:
            path_obj = Path(path).resolve()
            checks.append({
                "name": name,
                "kind": "file",
                "target": str(path_obj),
                "ok": path_obj.exists(),
                "reason": "ok" if path_obj.exists() else "missing",
            })

        passed = sum(1 for item in checks if item.get("ok"))
        return {
            "ok": passed == len(checks),
            "passed": passed,
            "total": len(checks),
            "updated_at": datetime.now().isoformat(),
            "checks": checks,
        }

    def _build_shadow_promotion_gate(self, shadow: CFDShadowTrade, ticker: Optional[dict]) -> Dict[str, Any]:
        direction = str(shadow.direction or "BUY").upper()
        momentum = float((ticker or {}).get("change_pct") or 0.0)
        direction_aligned = (direction == "BUY" and momentum >= 0) or (direction == "SELL" and momentum <= 0)

        latest_target = dict(getattr(self, "_latest_target_snapshot", {}) or {})
        target_symbol = self._canonical_symbol(latest_target.get("symbol"))
        target_direction = str(latest_target.get("direction") or "").upper()
        target_aligned = target_symbol == self._canonical_symbol(shadow.symbol) and target_direction == direction

        timeline_confidence = float(latest_target.get("timeline_confidence", 0.0) or 0.0)
        fusion_coherence = float(latest_target.get("fusion_global_coherence", 0.0) or 0.0)
        brain_coherence = 0.0
        for candidate in getattr(self, "_latest_candidate_snapshot", []):
            if (
                self._canonical_symbol(candidate.get("symbol")) == self._canonical_symbol(shadow.symbol)
                and str(candidate.get("direction") or "").upper() == direction
            ):
                brain_coherence = float(candidate.get("brain_coherence", 0.0) or 0.0)
                break

        probability = self._probability_validation_snapshot()
        probability_ok = (
            bool(probability.get("ok"))
            and float(probability.get("direction_accuracy", 0.0) or 0.0) >= CAPITAL_MIN_PROBABILITY_ACCURACY
            and float(probability.get("profit_factor", 0.0) or 0.0) >= CAPITAL_MIN_PROBABILITY_PROFIT_FACTOR
        )

        checks = {
            "direction_live": bool(direction_aligned),
            "target_alignment": bool(target_aligned),
            "timeline_alignment": timeline_confidence >= 0.40,
            "fusion_alignment": fusion_coherence >= 0.40,
            "brain_alignment": brain_coherence >= 0.10,
            "probability_matrix": probability_ok,
        }
        confidence = self._compute_self_confidence({
            "brain_coherence": brain_coherence,
            "timeline_confidence": timeline_confidence,
            "fusion_global_coherence": fusion_coherence,
        })
        ok = all(checks.values())
        return {
            "ok": ok,
            "checks": checks,
            "momentum": momentum,
            "timeline_confidence": timeline_confidence,
            "fusion_global_coherence": fusion_coherence,
            "brain_coherence": brain_coherence,
            "probability": probability,
            "self_confidence": confidence,
            "history_lookback_days": CAPITAL_HISTORY_LOOKBACK_DAYS,
            "validation_window_secs": float(confidence.get("validation_window_secs", self.SHADOW_MIN_VALIDATE) or self.SHADOW_MIN_VALIDATE),
            "reason": "aligned" if ok else "gate_misaligned",
        }

    def _can_open_candidate(self, symbol: str, direction: str, counts: Optional[Dict[str, int]] = None) -> bool:
        direction = str(direction or "").upper()
        if direction not in {"BUY", "SELL"}:
            return False
        if counts is None:
            counts = self._direction_counts()
        if counts.get(direction, 0) >= 1:
            return False
        if self._cooldown_info(symbol, direction) is not None:
            return False
        for pos in self.positions:
            if pos.symbol == symbol and str(pos.direction or "").upper() == direction:
                return False
        return len(self.positions) < int(CFD_CONFIG["max_positions"])

    def _find_best_opportunity(self) -> Optional[Tuple[str, dict, dict]]:
        """
        Scan universe for the highest-scored directional opportunity.
        Returns (symbol, cfg, ticker) or None.
        """
        max_pos = int(CFD_CONFIG["max_positions"])
        if len(self.positions) >= max_pos:
            return None

        direction_counts = self._direction_counts()
        best_score = 0.0
        best: Optional[Tuple[str, dict, dict]] = None
        scored: List[Dict[str, Any]] = []

        for symbol, cfg in self._active_universe().items():
            ticker = self._get_price(symbol)
            if not ticker:
                continue
            score, direction = self._score_symbol(symbol, cfg, ticker)
            if not self._can_open_candidate(symbol, direction, direction_counts):
                continue
            price = float(ticker.get("price") or 0.0)
            bid = float(ticker.get("bid") or 0.0)
            ask = float(ticker.get("ask") or 0.0)
            spread_pct = ((ask - bid) / price * 100.0) if price > 0 and bid > 0 and ask > 0 else 0.0
            required_tp_pct = self._required_tp_pct_for_profit(price, float(cfg.get("size", 0.0) or 0.0))
            effective_tp_pct = self._effective_tp_pct(price, float(cfg.get("size", 0.0) or 0.0), cfg)
            scored.append({
                "symbol": symbol,
                "direction": direction,
                "asset_class": cfg.get("class", "unknown"),
                "score": score,
                "price": price,
                "bid": bid,
                "ask": ask,
                "spread_pct": spread_pct,
                "change_pct": float(ticker.get("change_pct") or 0.0),
                "size": float(cfg.get("size", 0.0) or 0.0),
                "tp_pct": effective_tp_pct,
                "sl_pct": float(cfg.get("sl_pct", 0.0) or 0.0),
                "profit_target_gbp": CAPITAL_MIN_PROFIT_GBP,
                "required_tp_pct": required_tp_pct,
                "eta_to_target": (
                    required_tp_pct / max(abs(float(ticker.get("change_pct") or 0.0)), max(float(cfg.get("momentum_threshold", 0.1) or 0.1), 0.01))
                ) if required_tp_pct > 0 else 0.0,
            })
            if score > best_score:
                best_score = score
                best = (symbol, {**cfg, "direction": direction}, ticker)

        self._apply_hft_analysis(scored)
        self._apply_intelligence_overlays(scored)
        scored.sort(key=lambda item: float(item.get("score", 0.0) or 0.0), reverse=True)
        self._latest_candidate_snapshot = scored[:7]
        self._swarm_snapshot = self._build_swarm_snapshot(scored)

        chosen_best = best
        swarm_leader = dict(getattr(self, "_swarm_snapshot", {}).get("leader", {}) or {})
        if swarm_leader:
            leader_symbol = str(swarm_leader.get("symbol") or "").upper()
            leader_direction = str(swarm_leader.get("direction") or "BUY").upper()
            for symbol, cfg, ticker in self._ranked_opportunities():
                if symbol == leader_symbol and str(cfg.get("direction") or "BUY").upper() == leader_direction:
                    chosen_best = (symbol, cfg, ticker)
                    break

        if chosen_best is not None:
            symbol, cfg, ticker = chosen_best
            best_score = 0.0
            for candidate in scored:
                if (
                    str(candidate.get("symbol") or "").upper() == symbol
                    and str(candidate.get("direction") or "BUY").upper() == str(cfg.get("direction") or "BUY").upper()
                ):
                    best_score = float(candidate.get("score", 0.0) or 0.0)
                    break
            self._latest_target_snapshot = {
                "symbol": symbol,
                "direction": cfg.get("direction", "BUY"),
                "asset_class": cfg.get("class", "unknown"),
                "score": best_score,
                "price": float(ticker.get("price") or 0.0),
                "change_pct": float(ticker.get("change_pct") or 0.0),
                "size": float(cfg.get("size", 0.0) or 0.0),
                "tp_pct": max(
                    self._effective_tp_pct(
                        float(ticker.get("price") or 0.0),
                        float(cfg.get("size", 0.0) or 0.0),
                        cfg,
                    ),
                    0.0,
                ),
                "sl_pct": float(cfg.get("sl_pct", 0.0) or 0.0),
                "profit_target_gbp": CAPITAL_MIN_PROFIT_GBP,
            }
            for candidate in scored:
                if str(candidate.get("symbol") or "").upper() == symbol:
                    self._latest_target_snapshot.update({
                        "brain_coherence": float(candidate.get("brain_coherence", 0.0) or 0.0),
                        "expected_net_profit": float(candidate.get("expected_net_profit", 0.0) or 0.0),
                        "round_trip_cost": float(candidate.get("round_trip_cost", 0.0) or 0.0),
                        "eta_to_target": float(candidate.get("eta_to_target", 0.0) or 0.0),
                        "timeline_confidence": float(candidate.get("timeline_confidence", 0.0) or 0.0),
                        "fusion_global_coherence": float(candidate.get("fusion_global_coherence", 0.0) or 0.0),
                        "orchestrator_reason": str(candidate.get("orchestrator_reason", "") or ""),
                        "swarm_score": float(swarm_leader.get("swarm_score", 0.0) or 0.0),
                        "swarm_votes": int(swarm_leader.get("votes", 0) or 0),
                    })
                    break
            self._feed_unified_decision_engine(
                symbol,
                cfg.get("direction", "BUY"),
                score=min(1.0, max(0.0, best_score / 10.0)),
                metadata=dict(self._latest_target_snapshot),
            )
        else:
            self._latest_target_snapshot = {}
            self._decision_snapshot = {}
            self._swarm_snapshot = {"enabled": True, "leader": {}, "votes": [], "ranked": []}
        self._publish_market_snapshot_to_thought_bus()
        self._refresh_thought_bus_snapshot()
        return chosen_best

    def _fill_live_monitoring_slots(self, now: float) -> bool:
        if not CAPITAL_FORCE_SLOT_FILL:
            return False
        opened_any = False
        direction_counts = self._direction_counts()
        for direction in ("BUY", "SELL"):
            if direction_counts.get(direction, 0) >= 1:
                continue
            last_attempt = float(self._last_slot_fill_attempt.get(direction, 0.0) or 0.0)
            if (now - last_attempt) < CAPITAL_SLOT_FILL_INTERVAL_SECS:
                continue
            self._last_slot_fill_attempt[direction] = now
            for sym, cfg, ticker in self._ranked_live_slot_candidates(direction):
                # Get Queen's dynamic sizing for slot fill
                slot_cfg = dict(cfg)
                if self.orchestrator is not None:
                    try:
                        _ok, _reason, sizing_mod = self.orchestrator.gate_pre_trade(
                            sym, direction.lower(), float(cfg.get("size", 0.0) or 0.0) * float((ticker or {}).get("price", 0) or 0),
                        )
                        if not _ok:
                            continue  # Cross-system conflict
                        slot_cfg["queen_sizing"] = max(0.10, min(2.0, float(sizing_mod or 1.0)))
                    except Exception:
                        pass  # fail-open
                preflight = self._capital_preflight(sym, float(slot_cfg.get("size", 0.0) or 0.0), ticker, slot_cfg)
                if not self._preflight_allows_slot_fill(preflight):
                    self._record_rejection(sym, direction, str(preflight.get("reason") or "preflight_failed"))
                    continue
                pos = self._open_position(sym, slot_cfg, ticker)
                if pos is not None:
                    self._latest_monitor_line = f"CAPITAL SLOT FILL {sym} {direction} deal={pos.deal_id}"
                    opened_any = True
                    direction_counts[direction] = direction_counts.get(direction, 0) + 1
                    break
        return opened_any

    def _queue_background_shadows(self) -> int:
        if len(self.shadow_trades) >= self.SHADOW_MAX_ACTIVE:
            return 0
        queued = 0
        for sym, cfg, ticker in self._ranked_opportunities():
            if len(self.shadow_trades) >= self.SHADOW_MAX_ACTIVE:
                break
            direction = str(cfg.get("direction", "BUY") or "BUY").upper()
            if self._shadow_blocks_symbol(sym, direction):
                continue
            preflight = self._capital_preflight(sym, float(cfg.get("size", 0.0) or 0.0), ticker, cfg)
            if not self._preflight_allows_shadow(preflight):
                continue
            if self._create_shadow(sym, dict(cfg), ticker) is not None:
                queued += 1
        return queued

    def mark_deadman_heartbeat(self) -> None:
        self._last_deadman_kick_at = time.time()

    def _deadman_close_all(self, reason: str) -> List[dict]:
        closed: List[dict] = []
        held_count = 0
        for pos in list(self.positions):
            # Respect profit_only_closes: never close a losing position
            pnl_gbp = self._position_pnl_gbp(pos)
            if CFD_FLAGS["profit_only_closes"] and pnl_gbp <= 0:
                held_count += 1
                logger.info(
                    "Capital deadman HOLDING %s pnl=£%.4f (profit_only mode) reason=%s",
                    pos.symbol, pnl_gbp, reason,
                )
                continue
            try:
                record = self._close_position(pos, reason)
                if record and not record.get("error"):
                    closed.append(record)
            except Exception as e:
                logger.warning("Capital deadman close failed for %s: %s", pos.symbol, e)
        self.positions = [pos for pos in self.positions if pos.deal_id not in {str(r.get('deal_id') or '') for r in closed}]
        if closed or held_count:
            self._latest_monitor_line = (
                f"CAPITAL DEADMAN closed={len(closed)} held={held_count} reason={reason}"
            )
        return closed

    def _deadman_guard(self, now: float) -> List[dict]:
        if not CAPITAL_DEADMAN_ENABLED:
            return []
        age = now - float(getattr(self, "_last_deadman_kick_at", 0.0) or 0.0)
        if age < max(1.0, CAPITAL_DEADMAN_STALE_SECS):
            return []
        if not self.positions:
            return []
        # Don't try to close positions when markets are closed — just reset the timer
        from datetime import datetime, timezone
        hour = datetime.now(timezone.utc).hour
        weekday = datetime.now(timezone.utc).weekday()
        if weekday >= 5:  # Weekend — most CFD markets closed
            self._last_deadman_kick_at = now
            return []
        # Gold closes 21:00-22:00 UTC daily, all day Saturday
        # Don't panic-close during known closures
        if 21 <= hour < 22:
            self._last_deadman_kick_at = now
            return []
        logger.warning("Capital deadman triggered: stale loop age=%.1fs", age)
        result = self._deadman_close_all(f"DEADMAN_STALE {age:.1f}s")
        # Reset timer so we don't keep firing every tick while holding losing positions
        self._last_deadman_kick_at = now
        return result

    def _ranked_opportunities(self) -> List[Tuple[str, dict, dict]]:
        ranked: List[Tuple[str, dict, dict]] = []
        direction_counts = self._direction_counts()
        ordered_candidates: List[Dict[str, Any]] = []
        swarm_ranked = list(getattr(self, "_swarm_snapshot", {}).get("ranked", []) or [])
        candidate_lookup = {
            f"{str(item.get('symbol') or '').upper()}|{str(item.get('direction') or 'BUY').upper()}": item
            for item in getattr(self, "_latest_candidate_snapshot", [])
        }
        for swarm_item in swarm_ranked:
            key = f"{str(swarm_item.get('symbol') or '').upper()}|{str(swarm_item.get('direction') or 'BUY').upper()}"
            if key in candidate_lookup:
                ordered_candidates.append(candidate_lookup[key])
        if not ordered_candidates:
            ordered_candidates = list(getattr(self, "_latest_candidate_snapshot", []) or [])

        for candidate in ordered_candidates:
            symbol = str(candidate.get("symbol") or "").upper()
            direction = str(candidate.get("direction") or "BUY").upper()
            cfg = CAPITAL_UNIVERSE.get(symbol)
            ticker = self._get_price(symbol)
            if (
                symbol
                and cfg
                and ticker
                and float(candidate.get("score", 0.0) or 0.0) > 0
                and self._can_open_candidate(symbol, direction, direction_counts)
            ):
                ranked.append((symbol, {**dict(cfg), "direction": direction}, ticker))
        return ranked

    def _shadow_blocks_symbol(self, symbol: str, direction: str) -> bool:
        canon = self._canonical_symbol(symbol)
        for pos in self.positions:
            if self._canonical_symbol(pos.symbol) == canon and str(pos.direction or "").upper() == direction:
                return True
        for shadow in self.shadow_trades:
            if self._canonical_symbol(shadow.symbol) == canon and str(shadow.direction or "").upper() == direction:
                return True
        return False

    def _create_shadow(self, symbol: str, cfg: dict, ticker: dict) -> Optional[CFDShadowTrade]:
        if len(self.shadow_trades) >= self.SHADOW_MAX_ACTIVE:
            return None
        direction = str(cfg.get("direction") or "BUY").upper()
        if self._shadow_blocks_symbol(symbol, direction):
            return None
        price = float(ticker.get("price") or ticker.get("ask") or ticker.get("bid") or 0.0)
        if price <= 0:
            return None
        size = float(cfg.get("size", 0.0) or 0.0)
        target_move_pct = self._effective_tp_pct(price, size, cfg)
        score = 0.0
        for candidate in self._latest_candidate_snapshot:
            if self._canonical_symbol(candidate.get("symbol")) == self._canonical_symbol(symbol):
                score = float(candidate.get("score", 0.0) or 0.0)
                break
        shadow = CFDShadowTrade(
            symbol=symbol,
            direction=direction,
            asset_class=str(cfg.get("class", "unknown")),
            size=size,
            entry_price=price,
            target_move_pct=max(target_move_pct, 0.0001),
            score=score,
        )
        self.shadow_trades.append(shadow)
        self._append_promotion_event(
            "shadow_opened",
            {
                "symbol": symbol,
                "direction": direction,
                "asset_class": str(cfg.get("class", "unknown")),
                "entry_price": price,
                "target_move_pct": shadow.target_move_pct,
                "size": size,
                "score": score,
            },
        )
        self._latest_monitor_line = (
            f"CAPITAL SHADOW OPEN {symbol} {direction} entry={price:.5g} need={shadow.target_move_pct:.4f}%"
        )
        logger.info(
            "CAPITAL SHADOW OPENED: %s %s entry=%.5g need %.4f%%",
            symbol,
            direction,
            price,
            shadow.target_move_pct,
        )
        return shadow

    def _update_shadows(self) -> None:
        survivors: List[CFDShadowTrade] = []
        for shadow in self.shadow_trades:
            ticker = self._get_price(shadow.symbol)
            price = float((ticker or {}).get("price") or (ticker or {}).get("bid") or (ticker or {}).get("ask") or 0.0)
            if price > 0:
                shadow.update(price)
            if shadow.validated:
                survivors.append(shadow)
                continue
            if shadow.age_secs > self.SHADOW_MAX_AGE:
                self._shadow_failed_count += 1
                logger.info(
                    "CAPITAL SHADOW EXPIRED: %s %s moved=%+.4f%% need=%.4f%% age=%.0fs",
                    shadow.symbol,
                    shadow.direction,
                    shadow.current_move_pct,
                    shadow.target_move_pct,
                    shadow.age_secs,
                )
                continue
            survivors.append(shadow)
        self.shadow_trades = survivors

    def _promote_shadow(self, shadow: CFDShadowTrade) -> Optional[CFDPosition]:
        ticker = self._get_price(shadow.symbol)
        cfg = CAPITAL_UNIVERSE.get(shadow.symbol)
        if not ticker or not cfg:
            return None
        gate = self._build_shadow_promotion_gate(shadow, ticker)
        if not gate.get("ok"):
            self._append_promotion_event(
                "shadow_promotion_blocked",
                {
                    "symbol": shadow.symbol,
                    "direction": str(shadow.direction or "BUY").upper(),
                    "gate": gate,
                },
            )
            return None
        direction = str(shadow.direction or "BUY").upper()
        if not self._can_open_candidate(shadow.symbol, direction):
            return None
        # Get Queen's dynamic sizing from orchestrator at promotion time
        queen_sizing = 1.0
        if self.orchestrator is not None:
            try:
                _ok, _reason, sizing_mod = self.orchestrator.gate_pre_trade(
                    shadow.symbol, direction.lower(), shadow.size * shadow.entry_price,
                )
                if not _ok:
                    return None  # Cross-system conflict only
                queen_sizing = max(0.10, min(2.0, float(sizing_mod or 1.0)))
            except Exception:
                pass  # fail-open
        working_cfg = {**dict(cfg), "direction": direction, "size": shadow.size, "queen_sizing": queen_sizing}
        pos = self._open_position(shadow.symbol, working_cfg, ticker)
        if pos is not None:
            self._shadow_validated_count += 1
            self._append_promotion_event(
                "shadow_promoted",
                {
                    "symbol": shadow.symbol,
                    "direction": direction,
                    "deal_id": pos.deal_id,
                    "entry_price": pos.entry_price,
                    "size": pos.size,
                    "peak_move_pct": shadow.peak_move_pct,
                    "current_move_pct": shadow.current_move_pct,
                    "validation_age_secs": max(0.0, time.time() - float(shadow.validation_time or time.time())),
                    "promotion_gate": gate,
                },
            )
            self._latest_monitor_line = (
                f"CAPITAL SHADOW PROMOTED {shadow.symbol} {direction} deal={pos.deal_id}"
            )
            logger.info(
                "CAPITAL SHADOW PROMOTED: %s %s peak=%+.4f%%",
                shadow.symbol,
                direction,
                shadow.peak_move_pct,
            )
        return pos

    # ── POSITION MANAGEMENT ────────────────────────────────────────────────────
    def _open_position(self, symbol: str, cfg: dict, ticker: dict) -> Optional[CFDPosition]:
        """Open a BUY or SELL CFD position on Capital.com."""
        if not self.client:
            return None

        ask   = float(ticker.get("ask") or ticker.get("price") or 0)
        bid   = float(ticker.get("bid") or ticker.get("price") or 0)
        direction = str(cfg.get("direction") or "BUY").upper()
        entry_price = ask if direction == "BUY" else bid
        if entry_price <= 0:
            return None

        base_size = float(cfg.get("size", 0.01) or 0.01)
        queen_sizing = float(cfg.get("queen_sizing", 1.0) or 1.0)
        size = max(base_size * 0.10, base_size * queen_sizing)  # floor at 10% of base
        effective_tp_pct = self._effective_tp_pct(entry_price, size, cfg)
        if direction == "BUY":
            tp_price = entry_price * (1 + effective_tp_pct / 100)
            sl_price = entry_price * (1 - cfg["sl_pct"] / 100)
        else:
            tp_price = entry_price * (1 - effective_tp_pct / 100)
            sl_price = entry_price * (1 + cfg["sl_pct"] / 100)

        try:
            preflight = self._capital_preflight(symbol, float(size), ticker, cfg)
            trace_payload: Dict[str, Any] = {
                "symbol": symbol,
                "direction": direction,
                "size": size,
                "ticker": dict(ticker),
                "preflight": preflight,
                "known_deal_ids_before": [],
                "order_response": None,
                "confirm_response": None,
                "positions_snapshots": [],
                "validated": False,
            }
            if not preflight.get("ok"):
                self._latest_order_error = f"{symbol} preflight failed: {preflight.get('reason') or 'unknown'}"
                trace_payload["final_error"] = self._latest_order_error
                self._write_exchange_trace(trace_payload)
                logger.warning("CFD preflight failed for %s: %s", symbol, preflight.get("reason") or "unknown")
                return None
            known_deal_ids = {
                str((raw.get("position", {}) if isinstance(raw, dict) else {}).get("dealId") or "")
                for raw in self.client.get_positions()
            }
            trace_payload["known_deal_ids_before"] = sorted([d for d in known_deal_ids if d])
            result = self.client.place_market_order(symbol, direction, size)
            trace_payload["order_response"] = dict(result) if isinstance(result, dict) else result
            if result.get("rejected") or result.get("error"):
                reason = result.get("reason") or result.get("error", "unknown")
                self._record_rejection(symbol, direction, str(reason))
                self._latest_order_error = f"{symbol} open rejected: {reason}"
                self._write_exchange_trace(trace_payload)
                logger.debug(f"CFD open rejected {symbol}: {reason}")
                return None

            deal_ref = result.get("dealReference", "")
            deal_id  = result.get("dealId", deal_ref) or deal_ref
            epic     = ticker.get("epic", symbol)
            fill_price = entry_price  # Estimate; confirm_order may refine
            confirmed_ok = False

            # Attempt to confirm fill price from Capital.com confirmation
            if deal_ref:
                try:
                    conf = self.client.confirm_order(deal_ref)
                    trace_payload["confirm_response"] = dict(conf) if isinstance(conf, dict) else conf
                    deal_status = str(conf.get("dealStatus") or "").upper()
                    reject_reason = str(conf.get("rejectReason") or conf.get("reason") or "").strip()
                    confirm_status = str(conf.get("status") or "").upper()
                    if reject_reason or deal_status == "REJECTED" or confirm_status == "DELETED":
                        self._record_rejection(symbol, direction, reject_reason or deal_status or confirm_status)
                        self._latest_order_error = f"{symbol} rejected by Capital: {reject_reason or deal_status or confirm_status}"
                        trace_payload["validated"] = False
                        trace_payload["final_error"] = self._latest_order_error
                        self._write_exchange_trace(trace_payload)
                        logger.warning("CFD open rejected by Capital for %s: %s", symbol, reject_reason or deal_status or confirm_status)
                        return None
                    if not conf.get("error") and not conf.get("reason"):
                        deal_id    = conf.get("dealId", deal_id) or deal_id
                        fill_price = float(conf.get("level", fill_price) or fill_price)
                        effective_tp_pct = self._effective_tp_pct(fill_price, size, cfg)
                        if direction == "BUY":
                            tp_price = fill_price * (1 + effective_tp_pct / 100)
                            sl_price = fill_price * (1 - cfg["sl_pct"] / 100)
                        else:
                            tp_price = fill_price * (1 - effective_tp_pct / 100)
                            sl_price = fill_price * (1 + cfg["sl_pct"] / 100)
                        confirmed_ok = bool(deal_id)
                except Exception:
                    pass

            live_raw = None
            for _attempt in range(4):
                position_snapshot = self.client.get_positions()
                trace_payload["positions_snapshots"].append(position_snapshot)
                for raw in position_snapshot:
                    raw_pos = raw.get("position", {}) if isinstance(raw, dict) else {}
                    raw_market = raw.get("market", {}) if isinstance(raw, dict) else {}
                    raw_deal_id = str(raw_pos.get("dealId") or raw_pos.get("dealReference") or "")
                    raw_symbol = self._symbol_from_market(raw_market or raw_pos)
                    raw_direction = str(raw_pos.get("direction") or "").upper()
                    if deal_id and raw_deal_id == str(deal_id):
                        live_raw = raw
                        break
                    if raw_deal_id and raw_deal_id not in known_deal_ids and raw_symbol == symbol and raw_direction == direction:
                        live_raw = raw
                        deal_id = raw_deal_id
                        break
                if live_raw is not None:
                    break
                time.sleep(0.5)

            if live_raw is None:
                self._latest_order_error = (
                    f"{symbol} open not validated: deal_ref={deal_ref or 'none'} "
                    f"deal_id={deal_id or 'none'} confirmed={confirmed_ok}"
                )
                trace_payload["validated"] = False
                trace_payload["final_error"] = self._latest_order_error
                self._write_exchange_trace(trace_payload)
                logger.warning(
                    "CFD open not validated on exchange for %s (deal_ref=%s deal_id=%s confirmed=%s)",
                    symbol, deal_ref, deal_id, confirmed_ok
                )
                return None

            pos = self._position_from_exchange(live_raw)
            if pos is None:
                logger.warning("CFD open validation returned unusable position for %s", symbol)
                trace_payload["validated"] = False
                trace_payload["final_error"] = f"{symbol} validated raw position could not be parsed"
                self._write_exchange_trace(trace_payload)
                return None
            pos.epic = epic or pos.epic
            pos.current_price = fill_price if fill_price > 0 else pos.current_price
            self.positions = [p for p in self.positions if p.deal_id != pos.deal_id]
            self.positions.append(pos)
            self.stats["trades_opened"] += 1
            self._latest_order_error = ""
            trace_payload["validated"] = True
            trace_payload["validated_deal_id"] = pos.deal_id
            trace_payload["validated_position"] = {
                "symbol": pos.symbol,
                "deal_id": pos.deal_id,
                "epic": pos.epic,
                "direction": pos.direction,
                "entry_price": pos.entry_price,
                "tp_price": pos.tp_price,
                "sl_price": pos.sl_price,
            }
            self._write_exchange_trace(trace_payload)
            self._latest_monitor_line = (
                f"CAPITAL OPEN {symbol} {direction} deal={pos.deal_id} size={size} entry={pos.entry_price:.5g} "
                f"tp={pos.tp_price:.5g} sl={pos.sl_price:.5g}"
            )

            open_line = (
                f"  CAPITAL CFD OPEN:  {symbol:12} [{cfg['class'].upper():9}] "
                f"{direction} {size} @ {pos.entry_price:.5g} | "
                f"TP:{pos.tp_price:.5g}  SL:{pos.sl_price:.5g} | Deal:{pos.deal_id}"
            )
            try:
                print(open_line)
            except (ValueError, OSError):
                logger.info(open_line.strip())
            return pos

        except Exception as _e:
            self._latest_order_error = f"{symbol} open exception: {_e}"
            self._write_exchange_trace({
                "symbol": symbol,
                "size": size,
                "ticker": dict(ticker),
                "validated": False,
                "final_error": self._latest_order_error,
            })
            logger.debug(f"CFD open exception {symbol}: {_e}")
            return None

    def _close_position(self, pos: CFDPosition, reason: str) -> dict:
        """
        Close a CFD position via Capital.com DELETE /positions/{dealId}.
        Falls back to a reverse market order if DELETE fails.
        Returns a closed-trade record compatible with orca session_stats.
        """
        close_ok = False
        close_detail: Dict[str, Any] = {}
        pnl_gbp = 0.0

        if self.client and pos.deal_id:
            try:
                result = self.client.close_position(pos.deal_id)
                close_ok = bool(result.get("success"))
                close_detail = dict(result)
                if not close_ok:
                    # Fallback: reverse market order to flatten the position
                    opposite = "SELL" if pos.direction == "BUY" else "BUY"
                    fallback = self.client.place_market_order(pos.symbol, opposite, pos.size)
                    close_detail["fallback"] = fallback
                    close_ok = not bool(fallback.get("rejected") or fallback.get("error"))
            except Exception as _e:
                logger.debug(f"CFD close error {pos.symbol}: {_e}")
                close_detail = {"error": str(_e)}

        if self.client and pos.deal_id:
            try:
                still_open = False
                for raw in self.client.get_positions():
                    raw_pos = raw.get("position", {}) if isinstance(raw, dict) else {}
                    if str(raw_pos.get("dealId") or raw_pos.get("dealReference") or "") == pos.deal_id:
                        still_open = True
                        break
                if still_open:
                    close_ok = False
            except Exception as _e:
                logger.debug(f"CFD close verification skipped {pos.symbol}: {_e}")

        # Estimate PnL from tracked prices
        cp = pos.current_price if pos.current_price > 0 else pos.entry_price
        if pos.entry_price > 0 and cp > 0:
            if pos.direction == "BUY":
                pnl_pct = (cp - pos.entry_price) / pos.entry_price
            else:
                pnl_pct = (pos.entry_price - cp) / pos.entry_price
            pnl_gbp = pnl_pct * pos.entry_price * pos.size

        if not close_ok:
            return {
                "error": "close_failed",
                "symbol": pos.symbol,
                "deal_id": pos.deal_id,
                "reason": reason,
                "detail": close_detail,
            }

        # Update session stats
        self.stats["trades_closed"]  += 1
        self.stats["total_pnl_gbp"]  += pnl_gbp
        if pnl_gbp > 0:
            self.stats["winning_trades"] += 1
            self.stats["best_trade"] = max(self.stats["best_trade"], pnl_gbp)
        else:
            self.stats["losing_trades"] += 1
            self.stats["worst_trade"] = min(self.stats["worst_trade"], pnl_gbp)

        close_line = (
            f"  CAPITAL CFD CLOSE: {pos.symbol:12} [{pos.asset_class.upper():9}] "
            f"{reason}  |  PnL: {pnl_gbp:+.4f} GBP  age:{pos.age_secs/60:.1f}m"
        )
        try:
            print(close_line)
        except (ValueError, OSError):
            logger.info(close_line.strip())
        self._latest_monitor_line = (
            f"CAPITAL CLOSE {pos.symbol} {reason} pnl={pnl_gbp:+.4f}GBP age={pos.age_secs/60:.1f}m"
        )

        record = {
            "symbol":           pos.symbol,
            "deal_id":          pos.deal_id,
            "asset_class":      pos.asset_class,
            "direction":        pos.direction,
            "entry_price":      pos.entry_price,
            "exit_price":       cp,
            "size":             pos.size,
            "net_pnl":          pnl_gbp,
            "net_pnl_currency": "GBP",
            "reason":           reason,
            "age_secs":         pos.age_secs,
            "closed_at":        datetime.now().isoformat(),
        }
        brain = getattr(self, "_signal_brain", None)
        if brain is not None and hasattr(brain, "learn_from_outcome"):
            try:
                confidence = 0.5
                for candidate in getattr(self, "_latest_candidate_snapshot", []):
                    if self._canonical_symbol(candidate.get("symbol")) == self._canonical_symbol(pos.symbol):
                        confidence = float(candidate.get("brain_coherence", candidate.get("self_confidence", 0.5)) or 0.5)
                        break
                learning_update = brain.learn_from_outcome(
                    pos.symbol,
                    pnl_gbp / max(abs(pos.entry_price * pos.size), 0.0001),
                    confidence=confidence,
                )
                record["learning_update"] = dict(learning_update or {})
            except Exception as e:
                record["learning_error"] = str(e)
        self._recent_closed_trades.append(record)
        self._recent_closed_trades = self._recent_closed_trades[-5:]
        self._publish_learning_update(record)
        return record

    def _update_position_prices(self) -> None:
        """Refresh current_price on all tracked positions from the price cache."""
        for pos in self.positions:
            ticker = self._get_price(pos.symbol)
            if ticker:
                cp = float(ticker.get("price") or 0)
                if cp > 0:
                    pos.current_price = cp
                    self._latest_monitor_line = (
                        f"CAPITAL MONITOR {pos.symbol} now={cp:.5g} entry={pos.entry_price:.5g} "
                        f"pnl={pos.pnl_pct:+.3f}% tp={pos.tp_price:.5g} sl={pos.sl_price:.5g}"
                    )

    def _position_pnl_gbp(self, pos: CFDPosition) -> float:
        cp = pos.current_price if pos.current_price > 0 else pos.entry_price
        if pos.entry_price <= 0 or cp <= 0:
            return 0.0
        if pos.direction == "BUY":
            pnl_pct = (cp - pos.entry_price) / pos.entry_price
        else:
            pnl_pct = (pos.entry_price - cp) / pos.entry_price
        return pnl_pct * pos.entry_price * pos.size

    def _get_capital_dtp(self, pos: CFDPosition):
        if not HAS_CAPITAL_DTP or DynamicTakeProfit is None or not pos.deal_id:
            return None
        tracker = self._dtp_trackers.get(pos.deal_id)
        if tracker is None:
            tracker = DynamicTakeProfit(
                position_size_usd=float(pos.entry_price * pos.size),
                entry_fee_usd=0.0,
                fee_rate=0.0,
                gbp_usd_rate=1.0,
                activation_threshold_gbp=CAPITAL_DTP_TRIGGER_GBP,
                trailing_distance_pct=0.02,
                thought_bus=getattr(self, 'thought_bus', None),
            )
            self._dtp_trackers[pos.deal_id] = tracker
        return tracker

    def _monitor_positions(self) -> List[dict]:
        """
        Check TP / SL / 1-hour time-limit on every open position.
        Closes any that trip a condition. Returns list of closed-trade records.
        """
        closed:    List[dict]       = []
        remaining: List[CFDPosition] = []
        for pos in self.positions:
            if pos.current_price <= 0:
                remaining.append(pos)
                continue

            close_reason: Optional[str] = None
            pnl_gbp = self._position_pnl_gbp(pos)
            dtp = self._get_capital_dtp(pos)
            dtp_triggered = False
            dtp_reason = ""
            dtp_state = None
            if dtp is not None:
                dtp_triggered, dtp_reason, dtp_state = dtp.update(pnl_gbp)
                if dtp_state and dtp_state.activated:
                    self._latest_monitor_line = (
                        f"CAPITAL DTP {pos.symbol} floor=£{dtp_state.floor_gbp:.4f} "
                        f"peak=£{dtp_state.peak_profit_gbp:.4f} pnl=£{pnl_gbp:+.4f}"
                    )

            if pos.direction == "BUY":
                if pos.current_price >= pos.tp_price:
                    close_reason = f"TP_HIT {pos.current_price:.5g}>={pos.tp_price:.5g}"
                elif pos.current_price <= pos.sl_price:
                    close_reason = f"SL_HIT {pos.current_price:.5g}<={pos.sl_price:.5g}"
            else:   # SELL
                if pos.current_price <= pos.tp_price:
                    close_reason = f"TP_HIT {pos.current_price:.5g}<={pos.tp_price:.5g}"
                elif pos.current_price >= pos.sl_price:
                    close_reason = f"SL_HIT {pos.current_price:.5g}>={pos.sl_price:.5g}"

            if close_reason is None:
                penny_reason = self._penny_take_profit_reason(pos, pnl_gbp)
                if penny_reason:
                    close_reason = penny_reason

            if close_reason and CFD_FLAGS["profit_only_closes"] and pnl_gbp <= 0:
                self._latest_monitor_line = (
                    f"CAPITAL HOLD {pos.symbol} reason={close_reason} pnl={pnl_gbp:+.4f}GBP "
                    f"mode=profit_only"
                )
                close_reason = None

            if dtp_triggered and pnl_gbp >= CAPITAL_DTP_TRIGGER_GBP:
                close_reason = f"DTP_DEAD_MAN {dtp_reason}"

            if close_reason:
                record = self._close_position(pos, close_reason)
                if record.get("error"):
                    remaining.append(pos)
                else:
                    self._dtp_trackers.pop(pos.deal_id, None)
                    closed.append(record)
            else:
                remaining.append(pos)

        self.positions = remaining
        return closed

    # ── HEADLESS TICK ──────────────────────────────────────────────────────────
    def tick(self) -> List[dict]:
        """
        Execute ONE complete autonomous CFD cycle (no sleep, no loop).
        Called by orca_complete_kill_cycle run_autonomous() every N seconds.

        Phases:
          0 – Refresh price cache (rate-limited to price_ttl_secs)
          1 – Update position prices + check TP/SL/time-limit
          2 – Quadrumvirate gate → scan → open if green

        Returns: list of closed-trade records
        """
        if not self._ensure_client_ready():
            return []
        self._ensure_live_refresh()
        with self._state_lock:
            return self._tick_locked()

        now = time.time()
        closed_this_tick: List[dict] = self._deadman_guard(now)
        self._last_deadman_kick_at = now
        if now - float(getattr(self, "_harmonic_wiring_audit_at", 0.0) or 0.0) > 120.0:
            self._harmonic_wiring_audit = self._build_harmonic_wiring_audit()
            self._harmonic_wiring_audit_at = now
        sync_elapsed = 0.0
        refresh_elapsed = 0.0
        monitor_elapsed = 0.0
        shadow_elapsed = 0.0
        scan_elapsed = 0.0

        stage_started = time.time()
        self._sync_positions_from_exchange()
        sync_elapsed = time.time() - stage_started
        self._refresh_unified_intel_snapshot()
        self._refresh_thought_bus_snapshot()

        # Phase 0: price refresh
        stage_started = time.time()
        self._refresh_prices()
        refresh_elapsed = time.time() - stage_started

        # Phase 1: monitor open positions
        if now - self._last_monitor >= CFD_CONFIG["monitor_interval"]:
            stage_started = time.time()
            self._last_monitor = now
            self._update_position_prices()
            closed_this_tick.extend(self._monitor_positions())
            monitor_elapsed = time.time() - stage_started

        # Phase 2: update and promote shadows
        stage_started = time.time()
        self._update_shadows()
        promoted_this_tick = False
        validated_shadows = sorted(
            [
                shadow for shadow in self.shadow_trades
                if shadow.validated
            ],
            key=lambda item: (float(item.validation_time or item.created_at or 0.0), -float(item.score or 0.0)),
        )
        for shadow in list(validated_shadows):
            if not shadow.validated:
                continue
            gate_preview = self._build_shadow_promotion_gate(shadow, self._get_price(shadow.symbol))
            min_validate_window = float(gate_preview.get("validation_window_secs", self.SHADOW_MIN_VALIDATE) or self.SHADOW_MIN_VALIDATE)
            if shadow.validation_time > 0 and (now - shadow.validation_time) < min_validate_window:
                continue
            promoted = self._promote_shadow(shadow)
            if promoted is not None:
                promoted_this_tick = True
                self.shadow_trades.remove(shadow)
                break
            if self._cooldown_info(shadow.symbol, str(shadow.direction or "").upper()) is not None:
                self.shadow_trades.remove(shadow)
        shadow_elapsed = time.time() - stage_started

        # Phase 3: scan for new opportunity
        should_scan = (now - self._last_scan >= CFD_CONFIG["scan_interval_secs"]) or bool(closed_this_tick)
        if should_scan:
            stage_started = time.time()
            self._last_scan = now

            self._quad_gate()  # refresh modifier (always proceeds)
            self._find_best_opportunity()
            self._queue_background_shadows()
            if len(self.positions) < int(CFD_CONFIG["max_positions"]) and not promoted_this_tick:
                slot_filled_this_tick = self._fill_live_monitoring_slots(now)
                if slot_filled_this_tick:
                    promoted_this_tick = True
                opened_directions = {str(pos.direction or "").upper() for pos in self.positions}
                for sym, cfg, ticker in self._ranked_opportunities():
                    direction = str(cfg.get("direction", "BUY") or "BUY").upper()
                    if direction in opened_directions:
                        continue
                    if CAPITAL_FORCE_SLOT_FILL:
                        continue
                    preflight = self._capital_preflight(sym, float(cfg.get("size", 0.0) or 0.0), ticker, cfg)
                    working_cfg = dict(cfg)
                    if (not preflight.get("ok")) and "below Capital minimum" in str(preflight.get("reason") or ""):
                        adjusted_cfg = self._sized_cfg_from_preflight(cfg, preflight)
                        if adjusted_cfg is not None:
                            adjusted_preflight = self._capital_preflight(
                                sym,
                                float(adjusted_cfg.get("size", 0.0) or 0.0),
                                ticker,
                                adjusted_cfg,
                            )
                            if adjusted_preflight.get("ok"):
                                working_cfg = adjusted_cfg
                                preflight = adjusted_preflight

                    self._latest_target_snapshot = {
                        **dict(self._latest_target_snapshot),
                        "symbol": sym,
                        "direction": str(working_cfg.get("direction", "BUY") or "BUY").upper(),
                        "asset_class": working_cfg.get("class", cfg.get("class", "unknown")),
                        "size": float(working_cfg.get("size", 0.0) or 0.0),
                        "preflight_reason": str(preflight.get("reason") or ""),
                        "market_status": str(preflight.get("market_status") or ""),
                        "minimum_deal_size": float(preflight.get("minimum_deal_size", 0.0) or 0.0),
                        "available_balance": float(preflight.get("available_balance", 0.0) or 0.0),
                    }

                    if not preflight.get("ok"):
                        self._record_rejection(sym, direction, str(preflight.get("reason") or "preflight_failed"))
                        self._latest_order_error = f"{sym} preflight failed: {preflight.get('reason') or 'unknown'}"
                        logger.warning("CFD candidate skipped for %s: %s", sym, preflight.get("reason") or "unknown")
                        continue

                    if self._create_shadow(sym, working_cfg, ticker) is not None:
                        opened_directions.add(direction)
                        if opened_directions >= {"BUY", "SELL"} or len(self.positions) >= int(CFD_CONFIG["max_positions"]):
                            break
                    else:
                        self._record_rejection(sym, direction, "shadow_blocked_or_duplicate")

        if should_scan:
            scan_elapsed = time.time() - stage_started

        self._latest_tick_line = (
            f"CAPITAL TICK sync={sync_elapsed:.2f}s prices={refresh_elapsed:.2f}s "
            f"monitor={monitor_elapsed:.2f}s shadows={shadow_elapsed:.2f}s scan={scan_elapsed:.2f}s "
            f"positions={len(self.positions)} shadows_active={len(self.shadow_trades)}"
        )
        self._build_lane_snapshot()
        self.status_lines()
        return closed_this_tick

    # ── STATUS ─────────────────────────────────────────────────────────────────
    def _tick_locked(self) -> List[dict]:
        now = time.time()
        closed_this_tick: List[dict] = self._deadman_guard(now)
        self._last_deadman_kick_at = now
        if now - float(getattr(self, "_harmonic_wiring_audit_at", 0.0) or 0.0) > 120.0:
            self._harmonic_wiring_audit = self._build_harmonic_wiring_audit()
            self._harmonic_wiring_audit_at = now
        sync_elapsed = 0.0
        refresh_elapsed = 0.0
        monitor_elapsed = 0.0
        shadow_elapsed = 0.0
        scan_elapsed = 0.0

        stage_started = time.time()
        self._sync_positions_from_exchange()
        sync_elapsed = time.time() - stage_started
        self._refresh_unified_intel_snapshot()
        self._refresh_mind_map_snapshot()
        self._refresh_thought_bus_snapshot()

        stage_started = time.time()
        self._refresh_prices()
        refresh_elapsed = time.time() - stage_started

        if now - self._last_monitor >= CFD_CONFIG["monitor_interval"]:
            stage_started = time.time()
            self._last_monitor = now
            self._update_position_prices()
            closed_this_tick.extend(self._monitor_positions())
            monitor_elapsed = time.time() - stage_started

        stage_started = time.time()
        self._update_shadows()
        promoted_this_tick = False
        validated_shadows = sorted(
            [
                shadow for shadow in self.shadow_trades
                if shadow.validated
            ],
            key=lambda item: (float(item.validation_time or item.created_at or 0.0), -float(item.score or 0.0)),
        )
        for shadow in list(validated_shadows):
            if not shadow.validated:
                continue
            gate_preview = self._build_shadow_promotion_gate(shadow, self._get_price(shadow.symbol))
            min_validate_window = float(gate_preview.get("validation_window_secs", self.SHADOW_MIN_VALIDATE) or self.SHADOW_MIN_VALIDATE)
            if shadow.validation_time > 0 and (now - shadow.validation_time) < min_validate_window:
                continue
            promoted = self._promote_shadow(shadow)
            if promoted is not None:
                promoted_this_tick = True
                self.shadow_trades.remove(shadow)
                break
            if self._cooldown_info(shadow.symbol, str(shadow.direction or "").upper()) is not None:
                self.shadow_trades.remove(shadow)
        shadow_elapsed = time.time() - stage_started

        should_scan = (now - self._last_scan >= CFD_CONFIG["scan_interval_secs"]) or bool(closed_this_tick)
        if should_scan:
            stage_started = time.time()
            self._last_scan = now

            self._quad_gate()  # refresh modifier (always proceeds)
            self._find_best_opportunity()
            self._queue_background_shadows()
            if len(self.positions) < int(CFD_CONFIG["max_positions"]) and not promoted_this_tick:
                slot_filled_this_tick = self._fill_live_monitoring_slots(now)
                if slot_filled_this_tick:
                    promoted_this_tick = True
                opened_directions = {str(pos.direction or "").upper() for pos in self.positions}
                for sym, cfg, ticker in self._ranked_opportunities():
                    direction = str(cfg.get("direction", "BUY") or "BUY").upper()
                    if direction in opened_directions:
                        continue
                    if CAPITAL_FORCE_SLOT_FILL:
                        continue
                    preflight = self._capital_preflight(sym, float(cfg.get("size", 0.0) or 0.0), ticker, cfg)
                    working_cfg = dict(cfg)
                    if (not preflight.get("ok")) and "below Capital minimum" in str(preflight.get("reason") or ""):
                        adjusted_cfg = self._sized_cfg_from_preflight(cfg, preflight)
                        if adjusted_cfg is not None:
                            adjusted_preflight = self._capital_preflight(
                                sym,
                                float(adjusted_cfg.get("size", 0.0) or 0.0),
                                ticker,
                                adjusted_cfg,
                            )
                            if adjusted_preflight.get("ok"):
                                working_cfg = adjusted_cfg
                                preflight = adjusted_preflight

                    self._latest_target_snapshot = {
                        **dict(self._latest_target_snapshot),
                        "symbol": sym,
                        "direction": str(working_cfg.get("direction", "BUY") or "BUY").upper(),
                        "asset_class": working_cfg.get("class", cfg.get("class", "unknown")),
                        "size": float(working_cfg.get("size", 0.0) or 0.0),
                        "preflight_reason": str(preflight.get("reason") or ""),
                        "market_status": str(preflight.get("market_status") or ""),
                        "minimum_deal_size": float(preflight.get("minimum_deal_size", 0.0) or 0.0),
                        "available_balance": float(preflight.get("available_balance", 0.0) or 0.0),
                    }

                    if not preflight.get("ok"):
                        self._record_rejection(sym, direction, str(preflight.get("reason") or "preflight_failed"))
                        self._latest_order_error = f"{sym} preflight failed: {preflight.get('reason') or 'unknown'}"
                        logger.warning("CFD candidate skipped for %s: %s", sym, preflight.get("reason") or "unknown")
                        continue

                    if self._create_shadow(sym, working_cfg, ticker) is not None:
                        opened_directions.add(direction)
                        if opened_directions >= {"BUY", "SELL"} or len(self.positions) >= int(CFD_CONFIG["max_positions"]):
                            break
                    else:
                        self._record_rejection(sym, direction, "shadow_blocked_or_duplicate")

        if should_scan:
            scan_elapsed = time.time() - stage_started

        self._latest_tick_line = (
            f"CAPITAL TICK sync={sync_elapsed:.2f}s prices={refresh_elapsed:.2f}s "
            f"monitor={monitor_elapsed:.2f}s shadows={shadow_elapsed:.2f}s scan={scan_elapsed:.2f}s "
            f"positions={len(self.positions)} shadows_active={len(self.shadow_trades)}"
        )
        self._build_lane_snapshot()
        self._refresh_mycelium_snapshot(force=True)
        self._refresh_live_system_activity_snapshot()
        self._refresh_probability_feed_snapshot()
        self._publish_probability_feed()
        self.status_lines()
        return closed_this_tick

    def status_lines(self) -> List[str]:
        """Return human-readable status lines for orca dashboard / print_status."""
        mind_map_snapshot = dict(getattr(self, "_mind_map_snapshot", {}) or {})
        mycelium_snapshot = dict(getattr(self, "_mycelium_snapshot", {}) or {})
        live_system_activity_snapshot = dict(getattr(self, "_live_system_activity_snapshot", {}) or {})
        probability_feed_snapshot = dict(getattr(self, "_probability_feed_snapshot", {}) or {})
        w = int(self.stats["winning_trades"])
        l = int(self.stats["losing_trades"])
        c = int(self.stats["trades_closed"])
        pnl = self.stats["total_pnl_gbp"]
        gate = "ARMED" if HAS_QUAD_GATES else "open"
        capital = self.get_capital_snapshot()
        eq_delta = capital["equity_gbp"] - self.starting_equity_gbp if self.starting_equity_gbp > 0 else 0.0
        runtime_m = (time.time() - self.start_time) / 60.0

        lines: List[str] = [
            f"  CAPITAL STATUS | runtime={runtime_m:.1f}m",
            (
                f"  Equity={capital['equity_gbp']:.2f} GBP | Free={capital['free_gbp']:.2f} GBP | "
                f"Used={capital['used_gbp']:.2f} GBP | Budget={capital['budget_gbp']:.2f} GBP | "
                f"EqDelta={eq_delta:+.2f} GBP"
            ),
            f"  CAPITAL CFD: {len(self.positions)} open / {c} closed | "
            f"W:{w} L:{l} | PnL:{pnl:+.2f} GBP | gate:{gate}",
            f"  Shadows: {len(self.shadow_trades)} active | validated={self._shadow_validated_count} failed={self._shadow_failed_count}",
        ]
        confidence = self._compute_self_confidence()
        growth = self._compute_growth_metrics()
        lines.append(
            f"  Confidence: {float(confidence.get('score', 0.0) or 0.0):.2f} "
            f"| boost={float(confidence.get('boost_multiplier', 1.0) or 1.0):.2f}x "
            f"| promote_wait={float(confidence.get('validation_window_secs', self.SHADOW_MIN_VALIDATE) or self.SHADOW_MIN_VALIDATE):.1f}s "
            f"| mode={confidence.get('reason', 'n/a')}"
        )
        lines.append(
            f"  Growth: eq={float(growth.get('equity_growth_pct', 0.0) or 0.0):+.2f}% "
            f"| pnl/hr=£{float(growth.get('pnl_per_hour_gbp', 0.0) or 0.0):+.3f} "
            f"| trades/hr={float(growth.get('trades_per_hour', 0.0) or 0.0):.2f} "
            f"| avg/close=£{float(growth.get('avg_pnl_per_close_gbp', 0.0) or 0.0):+.3f} "
            f"| trend={growth.get('trend', 'steady')}"
        )
        if self._signal_brain is not None and hasattr(self._signal_brain, "learning_snapshot"):
            try:
                learning = self._signal_brain.learning_snapshot()
                lines.append(
                    f"  Learning: feedback={int(learning.get('total_feedback', 0) or 0)} "
                    f"| win_bias={float(learning.get('win_bias', 0.0) or 0.0):.2f}"
                )
            except Exception:
                pass
        # Asset-class breakdown
        by_class: Dict[str, int] = {}
        for pos in self.positions:
            by_class[pos.asset_class] = by_class.get(pos.asset_class, 0) + 1
        if by_class:
            breakdown = "  ".join(f"{cls}:{n}" for cls, n in sorted(by_class.items()))
            lines.append(f"    Classes: {breakdown}")
        if self._latest_order_error:
            lines.append(f"    Last order: {self._latest_order_error}")
            lines.append(f"    Trace: {self._latest_order_trace_path}")
        if self._latest_monitor_line:
            lines.append(f"    Monitor: {self._latest_monitor_line}")
        if self._latest_tick_line:
            lines.append(f"    Tick: {self._latest_tick_line}")
        if self._capital_snapshot_error:
            lines.append(f"    CapitalFeed: degraded ({self._capital_snapshot_error})")
        elif float(capital.get("stale", 0.0) or 0.0) > 0:
            lines.append("    CapitalFeed: stale_snapshot")
        active_cooldowns = sum(
            1 for info in self._rejection_cooldowns.values()
            if float(info.get("until", 0.0) or 0.0) > time.time()
        )
        if active_cooldowns:
            lines.append(f"    Cooldowns: {active_cooldowns} rejected targets cooling off")
        if self._lane_snapshot:
            buy_lane = self._lane_snapshot.get("BUY", {}) or {}
            sell_lane = self._lane_snapshot.get("SELL", {}) or {}
            lines.append(
                f"  Lanes: BUY={buy_lane.get('next_action', 'scan_for_candidate')} "
                f"[pos={buy_lane.get('position_symbol', '-') or '-'} "
                f"valid={buy_lane.get('validated_shadow_symbol', '-') or '-'} "
                f"queue={buy_lane.get('queued_shadow_symbol', '-') or '-'}]"
            )
            lines.append(
                f"         SELL={sell_lane.get('next_action', 'scan_for_candidate')} "
                f"[pos={sell_lane.get('position_symbol', '-') or '-'} "
                f"valid={sell_lane.get('validated_shadow_symbol', '-') or '-'} "
                f"queue={sell_lane.get('queued_shadow_symbol', '-') or '-'}]"
            )
        for pos in self.positions:
            lines.append(pos.one_line())
            dtp = self._dtp_trackers.get(pos.deal_id)
            dtp_state = getattr(dtp, "state", None)
            if dtp_state and getattr(dtp_state, "activated", False):
                lines.append(
                    f"      DTP floor=£{float(getattr(dtp_state, 'floor_gbp', 0.0) or 0.0):.4f} "
                    f"peak=£{float(getattr(dtp_state, 'peak_profit_gbp', 0.0) or 0.0):.4f}"
                )
        for shadow in self.shadow_trades[:4]:
            lines.append(
                f"    SHADOW {shadow.direction:4} {shadow.symbol:12} [{shadow.asset_class:9}] "
                f"entry:{shadow.entry_price:.5g} now:{shadow.current_price or shadow.entry_price:.5g} "
                f"move:{shadow.current_move_pct:+.3f}% need:{shadow.target_move_pct:.3f}% "
                f"age:{shadow.age_secs/60:.1f}m{' VALID' if shadow.validated else ''}"
            )
        if self._latest_target_snapshot:
            target = self._latest_target_snapshot
            lines.append(
                f"  Target: {target.get('symbol', '?')} {target.get('direction', '?')} [{target.get('asset_class', '?')}] "
                f"score={float(target.get('score', 0.0) or 0.0):.3f} "
                f"chg={float(target.get('change_pct', 0.0) or 0.0):+.3f}% "
                f"goal=£{float(target.get('profit_target_gbp', CAPITAL_MIN_PROFIT_GBP) or CAPITAL_MIN_PROFIT_GBP):.2f}"
            )
            if "expected_net_profit" in target:
                lines.append(
                    f"    HFT: net=£{float(target.get('expected_net_profit', 0.0) or 0.0):+.4f} "
                    f"cost=£{float(target.get('round_trip_cost', 0.0) or 0.0):.4f} "
                    f"coh={float(target.get('brain_coherence', 0.0) or 0.0):.3f}"
                )
            if "timeline_confidence" in target or "fusion_global_coherence" in target or "orchestrator_reason" in target:
                lines.append(
                    f"    Intel: timeline={float(target.get('timeline_confidence', 0.0) or 0.0):.2f} "
                    f"fusion={float(target.get('fusion_global_coherence', 0.0) or 0.0):.2f} "
                    f"orch={target.get('orchestrator_reason', 'n/a')}"
                )
        if self._latest_candidate_snapshot:
            lines.append("  Top 7 candidates:")
            for idx, candidate in enumerate(self._latest_candidate_snapshot[:7], start=1):
                lines.append(
                    f"    #{idx} {candidate.get('symbol', '?')} {candidate.get('direction', '?')} [{candidate.get('asset_class', '?')}] "
                    f"score={float(candidate.get('score', 0.0) or 0.0):.3f} "
                    f"chg={float(candidate.get('change_pct', 0.0) or 0.0):+.3f}% "
                    f"spr={float(candidate.get('spread_pct', 0.0) or 0.0):.3f}% "
                    f"net=£{float(candidate.get('expected_net_profit', 0.0) or 0.0):+.4f} "
                    f"goal=£{float(candidate.get('profit_target_gbp', CAPITAL_MIN_PROFIT_GBP) or CAPITAL_MIN_PROFIT_GBP):.2f}"
                )
        swarm_leader = dict(getattr(self, "_swarm_snapshot", {}).get("leader", {}) or {})
        if swarm_leader:
            lines.append(
                f"  Swarm: {swarm_leader.get('symbol', '?')} {swarm_leader.get('direction', '?')} "
                f"votes={int(swarm_leader.get('votes', 0) or 0)} "
                f"swarm={float(swarm_leader.get('swarm_score', 0.0) or 0.0):.3f}"
            )
        for trade in reversed(self._recent_closed_trades[-3:]):
            lines.append(
                f"  CLOSE: {trade.get('symbol', '?')} {trade.get('direction', '?')} "
                f"{float(trade.get('net_pnl', 0.0) or 0.0):+.2f} GBP reason={trade.get('reason', '?')}"
            )
        if self._registry_snapshot.get("categories"):
            lines.append(f"  Registry: {len(self._registry_snapshot.get('categories', {}))} categories linked")
        if mind_map_snapshot:
            if mind_map_snapshot.get("ok"):
                lines.append(
                    f"  MindMap: systems={int(mind_map_snapshot.get('systems_total', 0) or 0)} "
                    f"running={int(mind_map_snapshot.get('running_systems', 0) or 0)} "
                    f"prob={int(mind_map_snapshot.get('probability_systems', 0) or 0)} "
                    f"neural={int(mind_map_snapshot.get('neural_systems', 0) or 0)}"
                )
            else:
                lines.append(f"  MindMap: {mind_map_snapshot.get('reason', 'unavailable')}")
        if mycelium_snapshot:
            if mycelium_snapshot.get("ok"):
                lines.append(
                    f"  Mycelium: hives={int(mycelium_snapshot.get('total_hives', 0) or 0)} "
                    f"agents={int(mycelium_snapshot.get('total_agents', 0) or 0)} "
                    f"coh={float(mycelium_snapshot.get('coherence', 0.0) or 0.0):.2f} "
                    f"queen={float(mycelium_snapshot.get('queen_signal', 0.0) or 0.0):.2f}"
                )
            else:
                lines.append(f"  Mycelium: {mycelium_snapshot.get('reason', 'unavailable')}")
        if live_system_activity_snapshot:
            lines.append(
                f"  Runtime: {int(live_system_activity_snapshot.get('active_systems', 0) or 0)}/"
                f"{int(live_system_activity_snapshot.get('total_systems', 0) or 0)} systems active"
            )
        if probability_feed_snapshot:
            lines.append(
                f"  ProbabilityFeed: topic={probability_feed_snapshot.get('topic', 'probability.capital_feed')} "
                f"candidates={len(probability_feed_snapshot.get('candidates', []) or [])} "
                f"live_confirmed={bool(probability_feed_snapshot.get('live_confirmed'))}"
            )
        if self._decision_snapshot:
            if self._decision_snapshot.get("decision"):
                decision = self._decision_snapshot.get("decision", {}) or {}
                lines.append(
                    f"  Decision: {self._decision_snapshot.get('symbol', '?')} {self._decision_snapshot.get('side', '?')} "
                    f"-> {decision.get('type', '?')} conf={float(decision.get('confidence', 0.0) or 0.0):.2f}"
                )
            elif self._decision_snapshot.get("error"):
                lines.append(f"  Decision: error={self._decision_snapshot.get('error')}")
        if self._orchestrator_snapshot:
            lines.append(
                f"  Orchestrator: {self._orchestrator_snapshot.get('symbol', '?')} "
                f"{self._orchestrator_snapshot.get('side', '?')} "
                f"approved={self._orchestrator_snapshot.get('approved', True)} "
                f"reason={self._orchestrator_snapshot.get('reason', '')}"
            )
        if self._thought_bus_snapshot:
            if self._thought_bus_snapshot.get("error"):
                lines.append(f"  ThoughtBus: error={self._thought_bus_snapshot.get('error')}")
            else:
                lines.append(
                    f"  ThoughtBus: market={int(self._thought_bus_snapshot.get('market_events', 0) or 0)} "
                    f"decision={int(self._thought_bus_snapshot.get('decision_events', 0) or 0)}"
                )
        if self._cognition_snapshot:
            if self._cognition_snapshot.get("error"):
                lines.append(f"  Cognition: error={self._cognition_snapshot.get('error')}")
            else:
                lines.append(
                    f"  Cognition: brain={int(self._cognition_snapshot.get('cognition_events', 0) or 0)} "
                    f"queen={int(self._cognition_snapshot.get('queen_events', 0) or 0)}"
                )
        self._latest_status_lines = lines
        return lines

    def recommendations_summary(self) -> str:
        """One-liner for quick console display."""
        return (
            f"Capital CFD: {len(self.positions)}/{int(CFD_CONFIG['max_positions'])} pos | "
            f"PnL:{self.stats['total_pnl_gbp']:+.2f} GBP"
        )

    def get_dashboard_payload(self) -> Dict[str, Any]:
        """Expose Capital trader state in the same local-dashboard style as the margin trader."""
        capital = self.get_capital_snapshot()
        growth = self._compute_growth_metrics()
        return {
            "exchange": "capital",
            "mode": "cfd",
            "ok": self.enabled,
            "equity_gbp": capital["equity_gbp"],
            "free_gbp": capital["free_gbp"],
            "used_gbp": capital["used_gbp"],
            "budget_gbp": capital["budget_gbp"],
            "target_pct_equity": capital["target_pct_equity"],
            "positions": [
                {
                    "symbol": pos.symbol,
                    "deal_id": pos.deal_id,
                    "epic": pos.epic,
                    "direction": pos.direction,
                    "size": pos.size,
                    "entry_price": pos.entry_price,
                    "current_price": pos.current_price,
                    "tp_price": pos.tp_price,
                    "sl_price": pos.sl_price,
                    "asset_class": pos.asset_class,
                    "age_secs": pos.age_secs,
                    "pnl_pct": pos.pnl_pct,
                }
                for pos in self.positions
            ],
            "shadows": [
                {
                    "symbol": shadow.symbol,
                    "direction": shadow.direction,
                    "asset_class": shadow.asset_class,
                    "size": shadow.size,
                    "entry_price": shadow.entry_price,
                    "current_price": shadow.current_price,
                    "current_move_pct": shadow.current_move_pct,
                    "peak_move_pct": shadow.peak_move_pct,
                    "target_move_pct": shadow.target_move_pct,
                    "age_secs": shadow.age_secs,
                    "validated": shadow.validated,
                }
                for shadow in self.shadow_trades
            ],
            "stats": dict(self.stats),
            "growth_metrics": growth,
            "latest_monitor_line": self._latest_monitor_line,
            "status_lines": self._latest_status_lines[-16:],
            "candidate_snapshot": list(self._latest_candidate_snapshot),
            "target_snapshot": dict(self._latest_target_snapshot),
            "swarm_snapshot": dict(getattr(self, "_swarm_snapshot", {}) or {}),
            "lane_snapshot": dict(getattr(self, "_lane_snapshot", {}) or {}),
            "registry_snapshot": dict(self._registry_snapshot),
            "mind_map_snapshot": dict(self._mind_map_snapshot),
            "decision_snapshot": dict(self._decision_snapshot),
            "orchestrator_snapshot": dict(getattr(self, "_orchestrator_snapshot", {}) or {}),
            "timeline_snapshot": dict(getattr(self, "_timeline_snapshot", {}) or {}),
            "fusion_snapshot": dict(getattr(self, "_fusion_snapshot", {}) or {}),
            "harmonic_wiring_audit": dict(getattr(self, "_harmonic_wiring_audit", {}) or {}),
            "thought_bus_snapshot": dict(self._thought_bus_snapshot),
            "cognition_snapshot": dict(self._cognition_snapshot),
            "mycelium_snapshot": dict(self._mycelium_snapshot),
            "live_system_activity": dict(self._live_system_activity_snapshot),
            "probability_feed_snapshot": dict(self._probability_feed_snapshot),
            "recent_closed_trades": list(self._recent_closed_trades[-5:]),
            "shadow_validated": self._shadow_validated_count,
            "shadow_failed": self._shadow_failed_count,
        }
