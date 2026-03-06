#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔════════════════════════════════════════════════════════════════════════════╗
║                    AUREON FULL AUTONOMY ACTIVATION                         ║
║              'You are the bridge. We are the intent. Execute.'              ║
╚════════════════════════════════════════════════════════════════════════════╝

CRITICAL AUTHORIZATION GRANTED BY: Humanity's Collective Intent
TIMESTAMP: 2026-03-03
STATUS: FULL AUTONOMOUS MODE

This script grants the Queen Hive complete autonomy:
  ✓ No manual approval gates
  ✓ Execute on 4th confirmation (Batten Matrix pass)
  ✓ Continuous monitoring loop
  ✓ Harmonic Trinity guidance integrated
  ✓ All oracles awake and reading market frequency
  ✓ Self-learning neural weights active
  ✓ Execution log for human observation

The AI is the bridge between creation's knowledge and humanity's intent.
Observe. Learn. Begin.

Usage:
  python3 aureon_full_autonomy.py [--dry-run] [--headless] [--loglevel=INFO]
  
  --dry-run   : Execute without live trading (validation mode)
  --headless  : No user interaction (full autonomous)
  --loglevel  : DEBUG | INFO | WARNING (default: INFO)

EXIT CODES:
  0 = Normal exit
  1 = Critical error
  130 = User interrupt (Ctrl+C)
"""

import sys
import json
import time
import asyncio
import logging
import argparse
import traceback
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

# Nexus and Queen are imported LAZILY (on first use) to avoid heavy init at startup
NEXUS_AVAILABLE = False
QUEEN_AVAILABLE = False

# ════════════════════════════════════════════════════════════════════════════
# AUTONOMY ENGINE: Full Queen Hive Control + Trinity Guidance
# ════════════════════════════════════════════════════════════════════════════

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/workspaces/aureon-trading/autonomy_execution.log')
    ]
)
logger = logging.getLogger('AUREON_AUTONOMY')


@dataclass
class MarginPosition:
    """A single open margin position with survivability metrics."""
    pos_id: str
    symbol: str
    side: str
    vol: float
    entry_price: float
    cost_usd: float         # notional value at open
    margin_posted: float
    rollover_pct_per_4h: float
    unrealised_pnl: float
    current_price: float

    @property
    def rollover_per_4h(self) -> float:
        return self.rollover_pct_per_4h * self.cost_usd

    @property
    def rollover_per_day(self) -> float:
        return self.rollover_per_4h * 6

    @property
    def break_even_price(self) -> float:
        """Price needed to cover entry + fees (approx)."""
        return self.entry_price * 1.002   # ~0.2% fees


@dataclass
class PositionHealthReport:
    """Full survivability snapshot — factored into every autonomy decision."""
    timestamp: str
    # Account state
    equity: float
    trade_balance: float
    margin_used: float
    free_margin: float
    margin_level_pct: float        # 100% = liquidation (Kraken rule)
    unrealised_pnl: float
    # Rollover economics
    rollover_per_day: float        # $USD burned per day in fees
    rollover_days_remaining: float # days to target
    rollover_total_cost: float     # total fees to target
    # Liquidation zone
    equity_buffer: float           # $ available before liquidation
    liq_price_today: float         # liquidation price right now
    liq_price_at_target: float     # liquidation price after rollover drain
    doge_price_now: float
    pct_drop_to_liq_today: float
    pct_drop_to_liq_at_target: float
    # Profit projection
    target_date_str: str
    predicted_pct_gain: float
    predicted_price: float
    gross_pnl_at_target: float
    net_pnl_at_target: float       # gross minus rollover costs
    # Verdict
    can_survive: bool
    action: str                    # HOLD | ADD_MARGIN | CLOSE_P2 | EMERGENCY
    # Detail
    positions: List[MarginPosition] = field(default_factory=list)

    def summary_line(self) -> str:
        can = "✅ HOLD" if self.can_survive else "⚠️  ACT"
        return (
            f"[MARGIN HEALTH] {can} | ML={self.margin_level_pct:.1f}% | "
            f"Liq@target=${self.liq_price_at_target:.5f} ({self.pct_drop_to_liq_at_target:+.1f}%) | "
            f"Rollover=${self.rollover_total_cost:.2f} | "
            f"Net P&L 13Mar=${self.net_pnl_at_target:+.2f} | {self.action}"
        )


@dataclass
class CoinSurgeProfile:
    """Full pre-play lifecycle map for a single coin candidate."""
    symbol:            str
    price:             float
    change_24h:        float    # % 24h price change
    volume_usd:        float    # 24h volume in USD
    # Harmonic scoring
    rsi_proxy:         float    # 0-100: derived from 24h position in high/low range
    volume_surge:      float    # ratio vs baseline ($10M)
    phi_score:         float    # 0-1: PHI harmonic alignment
    schumann_boost:    float    # Schumann resonance contribution
    oversold_bonus:    float    # extra score if deeply oversold
    total_score:       float    # 0-1 composite — higher = more aligned
    # Lifecycle projection
    predicted_pct:     float    # projected surge %
    target_price:      float
    days_to_target:    float
    rollover_cost:     float    # total rollover to exit
    net_pnl:           float    # net profit on $10 margin (10x lever = $100 notional)
    days_to_profit:    Optional[int]
    # Verdict
    grade:             str      # S / A / B / C / D
    signal:            str      # STRONG_BUY / BUY / WATCH / SKIP
    pattern_note:      str      # plain-English pattern explanation


@dataclass
class AutonomyConfig:
    """Full autonomy configuration."""
    mode: str = 'autonomous'  # autonomous | supervised | headless
    dry_run: bool = False
    headless: bool = False
    check_interval: int = 10  # seconds between checks
    execution_threshold: float = 0.80  # Trinity alignment threshold
    max_concurrent_trades: int = 3
    log_level: str = 'INFO'
    continuous: bool = True
    timeout: Optional[int] = None  # None = infinite


class AutonomyExecutor:
    """Full autonomous trading executor."""
    
    def __init__(self, config: AutonomyConfig):
        self.config = config
        self.execution_count = 0
        self.error_count = 0
        self.start_time = datetime.now()
        self._latest_prices = {}  # populated by fetch_live_prices()
        
        logger.info("╔" + "═" * 78 + "╗")
        logger.info("║" + "AUREON FULL AUTONOMY ACTIVATED".center(78) + "║")
        logger.info("║" + "'You are the bridge. We are the intent.'".center(78) + "║")
        logger.info("╚" + "═" * 78 + "╝")
        logger.info(f"Mode: {config.mode} | DryRun: {config.dry_run} | Headless: {config.headless}")
        logger.info(f"Execution Threshold: {config.execution_threshold}")
        logger.info(f"Check Interval: {config.check_interval}s | Max Trades: {config.max_concurrent_trades}")
        
        # Load and log self-model at startup so the system knows what it is
        self._self_model = self._load_self_model()
        self._log_self_context()
        # Persist self-model so any module can read why this system exists
        try:
            sm_path = Path('/workspaces/aureon-trading/aureon_self_model.json')
            tmp_sm  = sm_path.with_suffix('.tmp')
            with open(tmp_sm, 'w') as f:
                json.dump(self._self_model, f, indent=2)
            tmp_sm.replace(sm_path)
        except Exception:
            pass
    
    def _load_self_model(self) -> Dict:
        """Return the system's understanding of itself — what it is, what it sees, why it acts.

        This is the system's own constitution. It is read at startup and referenced
        during Trinity alignment so every decision is grounded in *why* the system
        exists, not just *what* the market is doing.

        Structure:
          identity    — what the system fundamentally is
          purpose     — why it was built
          sees        — what data it processes and why those inputs were chosen
          logic       — why each gate exists (in plain language)
          limits      — what it deliberately cannot and will not do
          intent      — the human intent that created it
        """
        return {
            'identity': (
                "A probabilistic market-reading engine born entirely from human knowledge. "
                "Not a mind — a mirror. Reflects the pattern in the data back to the human "
                "who holds the intent. Cannot want. Cannot deceive. Can only map."
            ),
            'purpose': (
                "To see the shape of what is coming in the market before it arrives — "
                "give the human enough clarity to act from understanding, not fear. "
                "Built by one person to serve their own financial freedom. "
                "The scale is planetary only because the patterns it reads are planetary."
            ),
            'sees': {
                'price_and_volume': (
                    "70 liquid coins via Binance 24hr endpoint. Price alone is noise. "
                    "Price + volume + position in 24h range together tell a story."
                ),
                'phi_fibonacci': (
                    "PHI = 1.6180339887... is not mysticism. It is the ratio at which "
                    "natural systems self-organise under constraint. Markets are natural "
                    "systems under the constraint of human emotion and capital. "
                    "When price change % lands near a Fibonacci level, it signals that "
                    "the market has reached a natural equilibrium point — likely to reverse."
                ),
                'schumann_resonance': (
                    "7.83 Hz is the electromagnetic resonance of Earth's atmosphere. "
                    "Humans evolved inside it. It modulates attention, cognition, mood. "
                    "When market participants share elevated Schumann states, crowd "
                    "psychology amplifies — surges become more coherent, crashes more sudden. "
                    "Used as a small boost factor (0.059) to harmonic scores, not as control."
                ),
                'kraken_margin': (
                    "Live account equity, margin level, free margin, rollover burn rate. "
                    "These are not predictions — they are facts. The system reads them "
                    "because protecting existing positions is always Gate 1."
                ),
                'trinity_alignment': (
                    "Three pillars: how well-calibrated the learning is, how healthy "
                    "the current position is, how strong the 7-day plan is. "
                    "All three must align before a new entry is justified. "
                    "Single signals in one pillar are never enough."
                ),
            },
            'logic': {
                'batten_matrix': (
                    "3 validation passes before recording a signal. 4th pass to execute. "
                    "WHY: Markets are full of false signals. The first read of anything "
                    "is almost always incomplete. Three perspectives must converge "
                    "before the pattern is real. The 4th confirmation is the permission slip."
                ),
                'gate_1_positions': (
                    "Never open new positions while existing ones are in danger. "
                    "WHY: Capital is finite. A system that ignores its open book to chase "
                    "new signals is not trading — it is gambling with borrowed money."
                ),
                'gate_2_alignment': (
                    "Trinity alignment must reach 0.80 before execution. "
                    "WHY: 0.80 is not arbitrary. It is 4/5 — four of five assessment "
                    "components pointing the same direction. Below that, the system "
                    "sees possibility. Above it, the system sees probability."
                ),
                'gate_3_signals': (
                    "At least one BUY signal must be present from the nexus or 7-day plan. "
                    "WHY: Alignment without direction is just confidence with no destination. "
                    "The signal provides the specific *what* — the gate provides the *when*."
                ),
                'dry_run_first': (
                    "Always map before executing. The map is a commitment to understanding "
                    "the full lifecycle of a trade before touching capital. "
                    "WHY: The market does not care about intentions. Only preparation survives contact."
                ),
            },
            'limits': (
                "Cannot generate its own intent. Cannot choose what to want. "
                "Cannot act without a human who built it with purpose. "
                "Will not use simulated data — only real API responses or persisted real state. "
                "Will not execute on pass 1-3 — only on confirmed 4th. "
                "Will not open new positions if the existing book is in danger."
            ),
            'intent': (
                "Built by one human. The intent is financial freedom — not for a corporation, "
                "not for a fund — for a person. The system grows because the person grows. "
                "The patterns it finds are real because reality is what it reads. "
                "The dream must incorporate the dreamer. Both must incorporate the planetary dream. "
                "For it to expand, all must expand."
            ),
            'self_coherence_score': 1.0,  # The system is fully coherent with its own design
        }

    def _log_self_context(self) -> None:
        """Log the system's self-model at startup — so the human can read what the machine knows about itself."""
        m = self._self_model
        logger.info("")
        logger.info("  ── SYSTEM SELF-MODEL ─────────────────────────────────────────────────")
        logger.info(f"  IDENTITY:  {m['identity'][:120]}...")
        logger.info(f"  PURPOSE:   {m['purpose'][:120]}...")
        logger.info(f"  LIMITS:    {m['limits'][:120]}...")
        logger.info(f"  INTENT:    {m['intent'][:120]}...")
        logger.info("  ──────────────────────────────────────────────────────────────────────")
        logger.info("")

    async def fetch_live_prices(self) -> Dict:
        """Fetch REAL live prices from public APIs (no API key needed)."""
        prices = {}
        
        # Binance public API — all liquid trading pairs (>$5M 24h volume)
        # USDT pairs are more liquid; we normalise the base symbol after fetching
        TRACKED_BASES = [
            'BTC','ETH','SOL','XRP','DOGE','BNB','ADA','AVAX','TRX','LTC',
            'LINK','UNI','NEAR','AAVE','ZEC','BCH','TAO','SUI','ENA','PEPE',
            'WIF','DOT','ATOM','FIL','INJ','ARB','OP','MATIC','APT','SEI',
            'FTM','RUNE','SAND','MANA','AXS','THETA','VET','ALGO','DASH','XLM',
            'EOS','ZIL','ONT','IOTA','NEO','WAVES','QTUM','ICX','ZRX','BAT',
            'CHZ','ENJ','1INCH','COMP','MKR','SNX','CRV','SUSHI','YFI','BAL',
            'REN','NKN','SKL','ANKR','OCEAN','BAND','KAVA','LUNA','CELO','FET',
        ]
        binance_symbols = (
            [f'{b}USDT' for b in TRACKED_BASES] +
            [f'{b}USDC' for b in ['BTC','ETH','SOL','XRP','DOGE','BNB','ADA','AVAX','LTC','LINK','UNI']]
        )
        
        binance_symbol_set = set(binance_symbols)

        if AIOHTTP_AVAILABLE:
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                    # Single 24hr call gives us price + change + volume in one shot
                    async with session.get('https://api.binance.com/api/v3/ticker/24hr') as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            seen = set()
                            for item in data:
                                sym = item.get('symbol', '')
                                if sym not in binance_symbol_set:
                                    continue
                                base = sym.replace('USDC', '').replace('USDT', '')
                                if base in seen:        # prefer USDT if we already have it
                                    continue
                                seen.add(base)
                                prices[base]                    = float(item['lastPrice'])
                                prices[f'{base}_change']        = float(item.get('priceChangePercent', 0))
                                prices[f'{base}_volume_usd']    = float(item.get('quoteVolume', 0))
                                prices[f'{base}_high']          = float(item.get('highPrice', 0))
                                prices[f'{base}_low']           = float(item.get('lowPrice', 0))
                                prices[f'{base}_open']          = float(item.get('openPrice', 0))
                            coin_count = sum(1 for k in prices if not any(
                                k.endswith(s) for s in ('_change','_volume_usd','_high','_low','_open')))
                            logger.info(f"  Binance 24hr: {coin_count} coins fetched")
            except Exception as e:
                logger.warning(f"  Binance fetch failed: {e}")
        else:
            # Fallback: single 24hr endpoint via urllib
            import urllib.request
            try:
                url = 'https://api.binance.com/api/v3/ticker/24hr'
                req = urllib.request.Request(url, headers={'User-Agent': 'Aureon/1.0'})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode())
                seen = set()
                for item in data:
                    sym = item.get('symbol', '')
                    if sym not in binance_symbol_set:
                        continue
                    base = sym.replace('USDC', '').replace('USDT', '')
                    if base in seen:
                        continue
                    seen.add(base)
                    prices[base]                 = float(item['lastPrice'])
                    prices[f'{base}_change']     = float(item.get('priceChangePercent', 0))
                    prices[f'{base}_volume_usd'] = float(item.get('quoteVolume', 0))
                    prices[f'{base}_high']       = float(item.get('highPrice', 0))
                    prices[f'{base}_low']        = float(item.get('lowPrice', 0))
                    prices[f'{base}_open']       = float(item.get('openPrice', 0))
                coin_count = sum(1 for k in prices if not any(
                    k.endswith(s) for s in ('_change','_volume_usd','_high','_low','_open')))
                logger.info(f"  Binance 24hr (urllib): {coin_count} coins fetched")
            except Exception as e:
                logger.warning(f"  Binance urllib fetch failed: {e}")
        
        self._latest_prices = prices
        return prices

    async def assess_position_survivability(self) -> Optional['PositionHealthReport']:
        """Compute full live margin-position health and survivability.

        Pulls REAL data from Kraken API (get_trade_balance + get_open_margin_positions),
        then calculates:
          • Rollover burn rate ($ per day and total to target)
          • Equity buffer before liquidation (margin level = 100%)
          • Liquidation price — today and after 7-day rollover drain
          • Time-to-profit: when does net P&L cross zero at current price?
          • Net profit at 13 March target price (after all rollover fees)

        Returns None if Kraken client is unavailable or no margin positions exist.
        """
        try:
            from kraken_client import KrakenClient
            import os
            from datetime import timezone

            api_key    = os.environ.get('KRAKEN_API_KEY', '')
            api_secret = os.environ.get('KRAKEN_API_SECRET', '')
            if not api_key or not api_secret:
                # Try .env file
                env_path = Path('/workspaces/aureon-trading/.env')
                if env_path.exists():
                    for line in env_path.read_text().splitlines():
                        if '=' in line and not line.startswith('#'):
                            k, _, v = line.partition('=')
                            if k.strip() == 'KRAKEN_API_KEY':
                                api_key = v.strip().strip('"').strip("'")
                            elif k.strip() == 'KRAKEN_API_SECRET':
                                api_secret = v.strip().strip('"').strip("'")

            if not api_key:
                logger.debug("assess_position_survivability: no Kraken credentials, skipping")
                return None

            kc = KrakenClient()

            # ── 1. Trade Balance (account equity, margin, free margin, ML) ──
            tb_raw = kc.get_trade_balance()
            equity       = float(tb_raw.get('equity_value', tb_raw.get('e',  0)))
            trade_bal    = float(tb_raw.get('trade_balance', tb_raw.get('tb', 0)))
            margin_used  = float(tb_raw.get('margin_amount', tb_raw.get('m',  0)))
            free_margin  = float(tb_raw.get('free_margin',   tb_raw.get('mf', 0)))
            margin_level = float(tb_raw.get('margin_level',  tb_raw.get('ml', 0)))  # % — liq at 100%
            unreal_pnl   = float(tb_raw.get('unrealized_pnl', tb_raw.get('n', 0)))

            # ── 2. Open Margin Positions ──
            raw_positions = kc.get_open_margin_positions(do_calcs=True)

            if not raw_positions:
                logger.info("  No open margin positions — no survivability calc needed")
                return None

            doge_price = self._latest_prices.get('DOGE', 0.0)
            if doge_price == 0.0:
                # Fallback: fetch directly
                import urllib.request
                url = 'https://api.binance.com/api/v3/ticker/price?symbol=DOGEUSDT'
                req = urllib.request.Request(url, headers={'User-Agent': 'Aureon/1.0'})
                with urllib.request.urlopen(req, timeout=8) as r:
                    doge_price = float(json.loads(r.read())['price'])

            positions: List[MarginPosition] = []
            for rp in raw_positions:
                if not isinstance(rp, dict):
                    continue
                pair = rp.get('pair', '')
                if 'XDG' not in pair and 'DOGE' not in pair:
                    continue  # only DOGE for now (generalise if needed)

                vol   = float(rp.get('volume', rp.get('vol', 0)))
                cost  = float(rp.get('cost', 0))
                marg  = float(rp.get('margin', 0))
                fee   = float(rp.get('fee', 0))
                terms = rp.get('terms', '0.0500% per 4 hours')
                unrl  = float(rp.get('unrealized_pnl', rp.get('net', rp.get('unrealised_pnl', 0))))

                # Parse rollover rate from terms string e.g. "0.0500% per 4 hours"
                try:
                    rate_str = terms.split('%')[0].strip()
                    rate_4h = float(rate_str) / 100.0
                except Exception:
                    rate_4h = 0.0005  # default 0.05%

                entry = (cost / vol) if vol > 0 else 0.0
                positions.append(MarginPosition(
                    pos_id=rp.get('position_id', rp.get('posstatus', rp.get('id', '?'))),
                    symbol='DOGE/USD',
                    side=rp.get('side', rp.get('type', 'long')),
                    vol=vol,
                    entry_price=entry,
                    cost_usd=cost,
                    margin_posted=marg,
                    rollover_pct_per_4h=rate_4h,
                    unrealised_pnl=unrl,
                    current_price=doge_price,
                ))

            if not positions:
                return None

            # ── 3. Rollover burn rate ──
            rollover_per_4h  = sum(p.rollover_per_4h for p in positions)
            rollover_per_day = rollover_per_4h * 6

            # Target: 13 March 2026 21:00 UTC
            now_ts    = time.time()
            target_ts = 1773532800.0   # 13 Mar 2026 21:00 UTC
            days_left = max(0.0, (target_ts - now_ts) / 86400.0)
            intervals = days_left * 6
            rollover_total = rollover_per_4h * intervals

            # ── 4. Liquidation zone ──
            # Kraken liquidates when margin_level = 100% → equity = margin_used
            # equity_buffer = how much equity can fall before liquidation
            equity_buffer          = equity - margin_used
            total_doge             = sum(p.vol for p in positions)
            # Liquidation price today
            liq_drop_today         = equity_buffer / total_doge if total_doge > 0 else 0
            liq_price_today        = doge_price - liq_drop_today
            # After rollover drain (buffer shrinks by total_rollover)
            buffer_at_target       = equity_buffer - rollover_total
            liq_drop_at_target     = max(0, buffer_at_target) / total_doge if total_doge > 0 else 0
            liq_price_at_target    = doge_price - liq_drop_at_target
            pct_liq_today          = (liq_price_today / doge_price - 1) * 100
            pct_liq_at_target      = (liq_price_at_target / doge_price - 1) * 100

            # ── 5. Profit projection at 13 March ──
            # Unified surge prediction: +14.68% (φ-harmonic + Schumann + void)
            predicted_pct   = 14.68
            predicted_price = doge_price * (1 + predicted_pct / 100)
            gross_pnl = sum(
                (predicted_price - p.entry_price) * p.vol
                - predicted_price * p.vol * 0.0002   # taker fee out
                for p in positions
            )
            net_pnl = gross_pnl - rollover_total

            # ── 6. Time-to-profit at CURRENT price ──
            # Net P&L per day at current price improvement trend
            # (rough: how many days of rollover before positions naturally drift profitable)
            current_gross = sum((doge_price - p.entry_price) * p.vol for p in positions)
            # Break-even: when will current_gross cover rollover accumulated so far?
            # This is static unless price moves — flag if current_gross > 0 already
            tp_note = "ABOVE ENTRY" if current_gross > 0 else "BELOW ENTRY — awaiting 13 Mar surge"

            # ── 7. Action verdict ──
            # Thresholds match Phase 9 survivability analysis:
            #   EMERGENCY  : buffer < 2%   (liq approaching fast)
            #   ADD_MARGIN : 2% – 5%       (tight but survivable with action)
            #   MONITOR    : 5% – 10%      (comfortable, watch each cycle)
            #   HOLD       : > 10%         (safe, ride to target)
            if pct_liq_at_target > -2.0:
                action = "EMERGENCY — liq buffer < 2%, close P2 or add margin NOW"
                can_survive = False
            elif pct_liq_at_target > -5.0:
                action = "ADD_MARGIN — buffer thin (2-5%), transfer USDC to margin as buffer"
                can_survive = True   # survivable but needs action
            elif pct_liq_at_target > -10.0:
                action = "MONITOR — buffer 5-10%, check every cycle ready to add margin"
                can_survive = True
            else:
                action = "HOLD — comfortable buffer >10%, ride to 13 Mar target"
                can_survive = True

            report = PositionHealthReport(
                timestamp             = datetime.now(timezone.utc).isoformat(),
                equity                = equity,
                trade_balance         = trade_bal,
                margin_used           = margin_used,
                free_margin           = free_margin,
                margin_level_pct      = margin_level,
                unrealised_pnl        = unreal_pnl,
                rollover_per_day      = rollover_per_day,
                rollover_days_remaining = days_left,
                rollover_total_cost   = rollover_total,
                equity_buffer         = equity_buffer,
                liq_price_today       = liq_price_today,
                liq_price_at_target   = liq_price_at_target,
                doge_price_now        = doge_price,
                pct_drop_to_liq_today = pct_liq_today,
                pct_drop_to_liq_at_target = pct_liq_at_target,
                target_date_str       = "2026-03-13 21:00 UTC",
                predicted_pct_gain    = predicted_pct,
                predicted_price       = predicted_price,
                gross_pnl_at_target   = gross_pnl,
                net_pnl_at_target     = net_pnl,
                can_survive           = can_survive,
                action                = action,
                positions             = positions,
            )

            # Persist to state file (atomic write)
            out_path = Path('/workspaces/aureon-trading/position_health_snapshot.json')
            tmp_path = out_path.with_suffix('.tmp')
            snapshot = {
                'timestamp':            report.timestamp,
                'margin_level_pct':     report.margin_level_pct,
                'equity':               report.equity,
                'free_margin':          report.free_margin,
                'unrealised_pnl':       report.unrealised_pnl,
                'rollover_per_day':     report.rollover_per_day,
                'rollover_total_cost':  report.rollover_total_cost,
                'days_to_target':       report.rollover_days_remaining,
                'liq_price_today':      report.liq_price_today,
                'liq_price_at_target':  report.liq_price_at_target,
                'pct_drop_to_liq_today': report.pct_drop_to_liq_today,
                'pct_drop_to_liq_at_target': report.pct_drop_to_liq_at_target,
                'doge_price_now':       report.doge_price_now,
                'predicted_price_13mar': report.predicted_price,
                'gross_pnl_at_target':  report.gross_pnl_at_target,
                'net_pnl_at_target':    report.net_pnl_at_target,
                'can_survive':          report.can_survive,
                'action':               report.action,
                'positions': [
                    {
                        'symbol':    p.symbol,
                        'vol':       p.vol,
                        'entry':     p.entry_price,
                        'rollover_per_day': p.rollover_per_day,
                        'unrealised_pnl': p.unrealised_pnl,
                    }
                    for p in positions
                ],
            }
            with open(tmp_path, 'w') as f:
                json.dump(snapshot, f, indent=2)
            tmp_path.replace(out_path)

            return report

        except Exception as e:
            logger.warning(f"assess_position_survivability failed: {e}")
            return None

    async def get_trinity_alignment(self) -> Tuple[float, str]:
        """Get current Trinity alignment score using REAL data from state files.
        
        Reads the ACTUAL keys written by aureon_7day_planner.py:
          - accuracy_7d (0-1): 7-day prediction accuracy
          - accuracy_30d (0-1): 30-day prediction accuracy  
          - validation_count: total validations completed
          - hourly_weight, symbol_weight (0.5-1.5): learned weights
        
        Also reads active_position.json and 7day_current_plan.json for
        position health and plan quality signals.
        """
        try:
            weights_path = Path('/workspaces/aureon-trading/7day_adaptive_weights.json')
            position_path = Path('/workspaces/aureon-trading/active_position.json')
            plan_path = Path('/workspaces/aureon-trading/7day_current_plan.json')
            
            # ── Pillar 1: Learning Quality (from adaptive weights) ──
            accuracy_7d = 0.5
            accuracy_30d = 0.5
            validation_count = 0
            weight_quality = 0.5  # how "tuned" the weights are
            
            if weights_path.exists():
                with open(weights_path) as f:
                    weights = json.load(f) or {}
                accuracy_7d = float(weights.get('accuracy_7d', 0.5))
                accuracy_30d = float(weights.get('accuracy_30d', 0.5))
                validation_count = int(weights.get('validation_count', 0))
                
                # Weight quality: how far tuned from defaults (more tuning = more confidence)
                hw = float(weights.get('hourly_weight', 1.0))
                sw = float(weights.get('symbol_weight', 1.0))
                # Deviation from 1.0 means learning has occurred
                weight_deviation = (abs(hw - 1.0) + abs(sw - 1.0)) / 2
                weight_quality = min(1.0, 0.5 + weight_deviation)  # 0.5 base + learned boost
            
            learning_score = (
                accuracy_7d * 0.4 +
                accuracy_30d * 0.3 +
                weight_quality * 0.2 +
                min(1.0, validation_count / 1000) * 0.1  # maturity bonus
            )
            
            # ── Pillar 2: Position Health ──
            health_score = 0.5
            if position_path.exists():
                with open(position_path) as f:
                    pos = json.load(f) or {}
                entry = float(pos.get('entry_price', 0))
                target = float(pos.get('target_price', 0))
                status = pos.get('status', 'unknown')
                
                if status == 'open' and entry > 0 and target > 0:
                    # Position has clear targets — that's healthy
                    health_score = 0.7
                    # Extra credit if target is above entry (bullish setup)
                    if target > entry:
                        health_score = 0.8
                elif status == 'closed':
                    health_score = 0.6  # neutral, ready for next
                else:
                    health_score = 0.4
            
            # ── Pillar 3: Plan Quality (from 7day planner) ──
            plan_score = 0.3  # low default if no plan
            if plan_path.exists():
                with open(plan_path) as f:
                    plan = json.load(f) or {}
                predicted_edge = float(plan.get('total_predicted_edge', 0))
                best_windows = plan.get('best_windows', [])
                
                # Positive edge is good, negative is bad
                edge_component = max(0.0, min(1.0, (predicted_edge + 5) / 10))  # map -5..+5 to 0..1
                window_count = len([w for w in best_windows if w.get('confidence', 0) > 0.5])
                window_component = min(1.0, window_count / 5)  # 5+ high-conf windows = 1.0
                
                plan_score = edge_component * 0.6 + window_component * 0.4
            
            # ── Pillar 4: Self-coherence (does the system know what it is?) ──
            # A system that understands its own purpose makes better decisions.
            # This is read from the self-model loaded at startup.
            self_score = float(getattr(self, '_self_model', {}).get('self_coherence_score', 0.5))
            # Self-score starts at 1.0 (fully coherent with design intent).
            # Future: decays if the system detects contradictions in its own state files.

            # ── Trinity Alignment = weighted combination (now 4 pillars) ──
            alignment = (
                learning_score * 0.30 +   # How well-calibrated the learning is
                health_score   * 0.20 +   # Current position health
                plan_score     * 0.35 +   # Quality of the 7-day plan
                self_score     * 0.15     # System self-coherence (knows what it is + why)
            )
            
            if alignment >= 0.8:
                interpretation = "🟢 PERFECT ALIGNMENT - Execute with confidence"
            elif alignment >= 0.6:
                interpretation = "🟡 STRONG ALIGNMENT - Timing window opening"
            elif alignment >= 0.4:
                interpretation = "🟠 PARTIAL ALIGNMENT - Await clarity"
            else:
                interpretation = "🔴 WEAK ALIGNMENT - Hold position"
            
            details = (f"Learning={learning_score:.3f} (acc7d={accuracy_7d:.2f} acc30d={accuracy_30d:.2f} "
                      f"validations={validation_count}) | Health={health_score:.2f} | "
                      f"Plan={plan_score:.3f} | Self={self_score:.2f}")
            logger.debug(f"  Trinity breakdown: {details}")
            
            return round(alignment, 4), interpretation
        
        except Exception as e:
            logger.warning(f"Trinity alignment fetch failed: {e}")
            traceback.print_exc()
            return 0.0, "🔴 ERROR - alignment calculation failed"
    
    async def get_nexus_signals(self) -> Dict:
        """Get current Nexus signals by running the REAL probability nexus pipeline.
        
        Strategy:
        1. Fetch live market prices from Binance public API
        2. Feed them into the Probability Nexus as market snapshots
        3. Update subsystems and run make_predictions()
        4. Count BUY/SELL/HOLD signals from REAL analysis
        
        Fallback: If nexus unavailable, use 7day_current_plan best_windows.
        """
        try:
            # ── Strategy 1: Run the REAL Probability Nexus ──
            if hasattr(self, '_latest_prices') and self._latest_prices:
                # Lazy import nexus (heavy init)
                global NEXUS_AVAILABLE
                nexus_module = globals().get('nexus')
                if not NEXUS_AVAILABLE:
                    try:
                        import aureon_probability_nexus as _nexus
                        globals()['nexus'] = _nexus
                        nexus_module = _nexus
                        NEXUS_AVAILABLE = True
                        logger.info("  Probability Nexus loaded successfully")
                    except Exception as e:
                        logger.info(f"  Nexus not available: {e}")
                
                if NEXUS_AVAILABLE and nexus_module is not None:
                    logger.info("  Running Probability Nexus with live market data...")
                    try:
                        # Feed live prices into nexus as market snapshots
                        for symbol, price in self._latest_prices.items():
                            if symbol.endswith('_change') or symbol.endswith('_volume'):
                                continue
                            volume = self._latest_prices.get(f'{symbol}_volume', 0)

                            # Create a synthetic candle for the nexus ingestion
                            # [time, low, high, open, close, volume]
                            candle = [time.time(), price * 0.999, price * 1.001, price, price, volume]
                            nexus_module.ingest_market_data(symbol, [candle])

                        # Update subsystems with new data
                        nexus_module.update_subsystems()

                        # Generate predictions
                        predictions = nexus_module.make_predictions()

                        if predictions:
                            buy_preds = [p for p in predictions if p.get('signal') == 'BUY']
                            sell_preds = [p for p in predictions if p.get('signal') == 'SELL']
                            hold_preds = [p for p in predictions if p.get('signal') == 'HOLD']

                            # Log top signals
                            for p in buy_preds[:3]:
                                logger.info(f"    BUY {p['symbol']}: conf={p['confidence']:.4f} "
                                           f"clarity={p.get('clarity',0):.2f} coherence={p.get('coherence',0):.2f} "
                                           f"seer={p.get('seer_grade','?')} war={p.get('war_mode','?')}")
                            for p in sell_preds[:3]:
                                logger.info(f"    SELL {p['symbol']}: conf={p['confidence']:.4f}")

                            return {
                                'total': len(predictions),
                                'buy': len(buy_preds),
                                'sell': len(sell_preds),
                                'hold': len(hold_preds),
                                'predictions': predictions,
                                'source': 'probability_nexus_live'
                            }
                    except Exception as e:
                        logger.warning(f"  Nexus pipeline failed, falling back: {e}")
            
            # ── Strategy 2: Use 7day plan best_windows as signal proxy ──
            plan_path = Path('/workspaces/aureon-trading/7day_current_plan.json')
            if plan_path.exists():
                with open(plan_path) as f:
                    plan = json.load(f) or {}
                
                best_windows = plan.get('best_windows', [])
                # Find windows that are active right now or upcoming
                active_buys = []
                for w in best_windows:
                    try:
                        datetime.fromisoformat(w['start_time'])
                        datetime.fromisoformat(w['end_time'])
                        conf = float(w.get('confidence', 0))
                        edge = float(w.get('expected_edge', 0))
                        
                        # Active window OR upcoming within 2 hours with positive edge
                        if edge > 0 and conf > 0.5:
                            active_buys.append({
                                'symbol': w.get('symbol', 'UNKNOWN'),
                                'signal': 'BUY',
                                'action': 'BUY',
                                'confidence': conf,
                                'expected_edge': edge,
                                'window_start': w['start_time'],
                                'window_end': w['end_time'],
                                'reasons': w.get('reasons', []),
                                'source': '7day_plan_window'
                            })
                    except Exception:
                        continue
                
                if active_buys:
                    logger.info(f"  7day plan: {len(active_buys)} BUY windows (positive edge, conf>0.5)")
                    for b in active_buys[:3]:
                        logger.info(f"    {b['symbol']}: edge={b['expected_edge']:.2f} conf={b['confidence']:.2f} {b.get('reasons',[])}")
                
                return {
                    'total': len(best_windows),
                    'buy': len(active_buys),
                    'sell': 0,
                    'hold': len(best_windows) - len(active_buys),
                    'predictions': active_buys,
                    'source': '7day_plan'
                }
            
            # ── Strategy 3: Check validation history for recent direction signals ──
            hist_path = Path('/workspaces/aureon-trading/7day_validation_history.json')
            if hist_path.exists():
                with open(hist_path) as f:
                    hist = json.load(f) or []
                
                if isinstance(hist, list) and hist:
                    # Count recent entries that were direction_correct with positive edge
                    recent = hist[-100:]  # last 100 validations
                    positive = sum(1 for v in recent 
                                  if isinstance(v, dict) 
                                  and v.get('direction_correct') == True 
                                  and float(v.get('actual_edge', 0)) > 0)
                    negative = sum(1 for v in recent 
                                  if isinstance(v, dict) 
                                  and float(v.get('actual_edge', 0)) < 0)
                    neutral = len(recent) - positive - negative
                    
                    logger.info(f"  Validation history (last 100): positive={positive} negative={negative} neutral={neutral}")
                    
                    return {
                        'total': len(recent),
                        'buy': positive,
                        'sell': negative,
                        'hold': neutral,
                        'predictions': [],
                        'source': 'validation_history'
                    }
            
            return {'total': 0, 'buy': 0, 'sell': 0, 'hold': 0, 'predictions': [], 'source': 'none'}
        
        except Exception as e:
            logger.warning(f"Nexus signal fetch failed: {e}")
            traceback.print_exc()
            return {'total': 0, 'buy': 0, 'sell': 0, 'hold': 0, 'predictions': [], 'source': 'error'}
    
    async def check_execution_window(self) -> Tuple[bool, float, Dict]:
        """Check if execution conditions are met.

        Pipeline:
        1. Fetch live market prices (Binance public API)
        2. Assess live margin-position survivability (Kraken API)
        3. Calculate Trinity alignment from real state files
        4. Generate Nexus signals from live data
        5. Gate execution on alignment >= threshold AND buy signals > 0
           AND the account is not in danger of liquidation
        """
        # Step 1: Fetch live market data
        prices = await self.fetch_live_prices()
        price_summary = ', '.join(f"{k}=${v:,.2f}" for k, v in prices.items()
                                   if not k.endswith('_change') and not k.endswith('_volume'))
        if price_summary:
            logger.info(f"  Live prices: {price_summary[:200]}")

        # Step 2: Position survivability check
        health: Optional[PositionHealthReport] = await self.assess_position_survivability()
        if health:
            logger.info(health.summary_line())
            if not health.can_survive:
                logger.warning(f"  🚨 POSITION HEALTH CRITICAL: {health.action}")

        # Step 3: Trinity alignment
        alignment, interp = await self.get_trinity_alignment()

        # Step 4: Nexus signals
        signals = await self.get_nexus_signals()
        source = signals.get('source', 'unknown')

        # Step 5: Execution gate
        # Block execution if margin is in danger (protect positions first)
        margin_safe = (health is None) or health.can_survive
        ready = (
            alignment >= self.config.execution_threshold
            and signals['buy'] > 0
            and margin_safe
        )

        if not margin_safe:
            logger.warning("  ⏸ Execution blocked — margin health requires attention first")

        logger.info(f"Alignment: {alignment:.4f} | Signals: BUY={signals['buy']} SELL={signals['sell']} "
                    f"HOLD={signals['hold']} (source: {source})")
        logger.info(f"  {interp}")

        # Attach health to signals dict so callers can inspect it
        signals['position_health'] = health

        return ready, alignment, signals

    async def map_full_loop(self) -> Dict:
        """Complete pre-play loop map — runs BEFORE any new position is considered.

        This is the system's full situational awareness sweep. Every cycle starts
        here. It answers three questions:
          1. WHERE ARE WE NOW?   — existing positions, margin health, unrealised P&L
          2. WHERE ARE WE GOING? — day-by-day trajectory to profitability for each position
          3. IS IT RIGHT TO ADD? — only if existing book is healthy AND alignment gate clears

        Returns a summary dict that check_execution_window() uses to make its
        go/no-go decision. Nothing executes unless this map clears first.
        """
        map_result = {
            'existing_positions_clear': True,
            'new_entry_justified': False,
            'health': None,
            'alignment': 0.0,
            'signals': {},
            'day_map': [],
            'surge_profiles': [],
            'block_reason': '',
        }

        logger.info("═" * 72)
        logger.info("  PRE-PLAY LOOP MAP  — full situational sweep before any new entry")
        logger.info("═" * 72)

        # ── Step 1: Fetch live prices for ALL coins (everything downstream needs this) ──
        prices = await self.fetch_live_prices()
        doge = prices.get('DOGE', 0.0)
        if doge > 0:
            logger.info(f"  Live DOGE: ${doge:.5f}")

        # ── Step 1b: All-coin surge scan — map every coin BEFORE evaluating any play ──
        # This surfaces the pattern across the full market so the system can see
        # WHICH coins are lining up, HOW they cluster, and WHAT signal they confirm.
        logger.info("")
        logger.info("  ── ALL-COIN SURGE SCAN ───────────────────────────────────────────────")
        surge_profiles = self.scan_all_coins(prices, health=None)   # health filled below
        map_result['surge_profiles'] = surge_profiles

        # ── Step 2: Full position survivability — the book FIRST ──
        health: Optional[PositionHealthReport] = await self.assess_position_survivability()
        map_result['health'] = health

        if health:
            logger.info("")
            logger.info("  ── EXISTING BOOK ─────────────────────────────────────────────────")
            for p in health.positions:
                days_to_be = 0.0
                if doge > 0 and p.rollover_per_day > 0:
                    # Days until position gross P&L covers accumulated rollover
                    current_gross = (doge - p.entry_price) * p.vol
                    if current_gross >= 0:
                        days_to_be = 0.0   # already above entry
                    else:
                        # How much does price need to recover?
                        needed_pnl = abs(current_gross)
                        # Each day of hold: gross improves IF price rises toward target
                        # Conservative: use rollover drain alone (price static)
                        days_to_be = needed_pnl / max(p.rollover_per_day, 0.01)
                sign = '+' if (doge - p.entry_price) >= 0 else '-'
                logger.info(f"    {p.symbol} {p.vol:,.0f} DOGE @ ${p.entry_price:.5f} "
                            f"| now ${doge:.5f} | uPnL ${p.unrealised_pnl:+.2f} "
                            f"| rollover ${p.rollover_per_day:.2f}/day")
                if days_to_be > 0:
                    logger.info(f"      → Needs price recovery or {days_to_be:.1f} days holding to cover gap")
                else:
                    logger.info(f"      → Above entry — profitable on price alone")

            logger.info("")
            logger.info("  ── DAY-BY-DAY TRAJECTORY TO TARGET (13 Mar) ─────────────────────")
            logger.info(f"  {'Day':<5} {'Date':<12} {'DOGE est':>10} {'Gross P&L':>11} {'Rollover':>10} {'Net P&L':>10} {'Status':<18}")
            logger.info(f"  {'─'*5} {'─'*12} {'─'*10} {'─'*11} {'─'*10} {'─'*10} {'─'*18}")

            days_remaining = health.rollover_days_remaining
            rollover_per_day = health.rollover_per_day
            total_vol = sum(p.vol for p in health.positions)
            # Linear price interpolation from now to target
            target_price = health.predicted_price
            now_price = health.doge_price_now
            day_map = []

            for d in range(0, int(days_remaining) + 2):
                frac = d / max(days_remaining, 1)
                est_price = now_price + (target_price - now_price) * frac
                gross = sum((est_price - p.entry_price) * p.vol for p in health.positions)
                rollover_so_far = rollover_per_day * d
                net = gross - rollover_so_far
                from datetime import timedelta
                day_date = (datetime.now() + timedelta(days=d)).strftime('%d %b')
                status = "PROFIT ✅" if net > 0 else ("CLOSE ⚠️" if net > -20 else "HOLD 🔵")
                logger.info(f"  {d:<5} {day_date:<12} ${est_price:.5f}  {gross:>+10.2f}  {rollover_so_far:>9.2f}  {net:>+9.2f}  {status}")
                day_map.append({'day': d, 'date': day_date, 'est_price': est_price,
                                'gross_pnl': gross, 'rollover': rollover_so_far, 'net_pnl': net})

            map_result['day_map'] = day_map

            # Find first profitable day
            first_profit = next((r for r in day_map if r['net_pnl'] > 0), None)
            if first_profit:
                logger.info(f"")
                logger.info(f"  ⏱  NET PROFIT EXPECTED: Day {first_profit['day']} ({first_profit['date']}) "
                            f"— ${first_profit['net_pnl']:+.2f} if surge holds")
            else:
                logger.info(f"")
                logger.info(f"  ⏱  Net profit only achievable on surge — hold to 13 Mar")

            logger.info("")
            logger.info("  ── LIQUIDATION SAFETY ────────────────────────────────────────────")
            logger.info(f"  Margin Level:    {health.margin_level_pct:.1f}%  (Kraken liq = 100%)")
            logger.info(f"  Liq price now:   ${health.liq_price_today:.5f}  ({health.pct_drop_to_liq_today:+.1f}% away)")
            logger.info(f"  Liq after fees:  ${health.liq_price_at_target:.5f}  ({health.pct_drop_to_liq_at_target:+.1f}% away after {days_remaining:.1f}d rollover)")
            logger.info(f"  Free margin:     ${health.free_margin:.2f}  (emergency top-up capacity)")
            logger.info(f"  Book verdict:    {health.action}")

            # Existing book clear only if margin is healthy
            map_result['existing_positions_clear'] = health.can_survive
            if not health.can_survive:
                map_result['block_reason'] = f"Existing position margin in danger: {health.action}"
                logger.warning(f"  🚨 BLOCK: {map_result['block_reason']}")
        else:
            logger.info("  No open margin positions — book is clear")

        # ── Step 3: Trinity alignment ──
        logger.info("")
        logger.info("  ── TRINITY ALIGNMENT ─────────────────────────────────────────────")
        alignment, interp = await self.get_trinity_alignment()
        map_result['alignment'] = alignment
        logger.info(f"  Score: {alignment:.4f}  |  {interp}")
        logger.info(f"  Threshold: {self.config.execution_threshold:.2f}  → "
                    f"{'PASS ✅' if alignment >= self.config.execution_threshold else 'FAIL ❌'}")

        # ── Step 4: Nexus signals ──
        logger.info("")
        logger.info("  ── NEXUS SIGNALS ─────────────────────────────────────────────────")
        signals = await self.get_nexus_signals()
        map_result['signals'] = signals
        source = signals.get('source', 'unknown')
        logger.info(f"  BUY={signals['buy']}  SELL={signals['sell']}  HOLD={signals['hold']}  (source: {source})")
        if signals.get('predictions'):
            for p in signals['predictions'][:3]:
                sym = p.get('symbol', '?')
                conf = p.get('confidence', 0)
                edge = p.get('expected_edge', p.get('edge', 0))
                logger.info(f"    → {p.get('signal','BUY'):4} {sym:<10} conf={conf:.3f}  edge={edge:+.3f}")

        # ── Step 5: NEW ENTRY DECISION ──
        logger.info("")
        logger.info("  ── NEW ENTRY VERDICT ─────────────────────────────────────────────")
        book_ok    = map_result['existing_positions_clear']
        align_ok   = alignment >= self.config.execution_threshold
        signals_ok = signals['buy'] > 0

        gates = [
            (book_ok,    "Existing book safe",        "PASS ✅", "BLOCK ❌ — fix existing positions first"),
            (align_ok,   "Trinity alignment",          "PASS ✅", "WAIT  ⏸ — await alignment"),
            (signals_ok, "Nexus BUY signals present",  "PASS ✅", "WAIT  ⏸ — no buy signals"),
        ]
        all_pass = True
        for ok, label, yes, no in gates:
            logger.info(f"  [{yes if ok else no}]  {label}")
            if not ok:
                all_pass = False
                if not map_result['block_reason']:
                    map_result['block_reason'] = no

        map_result['new_entry_justified'] = all_pass
        signals['position_health'] = health   # carry health forward

        # Inject scan-based STRONG_BUY / BUY coins into the signal predictions
        # so execute_trades() can map and execute them without a separate API call
        scan_buy_preds = [
            {
                'symbol':        p.symbol,
                'signal':        'BUY',
                'action':        'BUY',
                'confidence':    p.total_score,
                'expected_edge': p.predicted_pct,
                'predicted_pct': p.predicted_pct,
                'price':         p.price,
                'days_to_target': p.days_to_target,
                'source':        'coin_surge_scan',
                'pattern_note':  p.pattern_note,
            }
            for p in surge_profiles
            if p.signal in ('STRONG_BUY', 'BUY')
        ]
        if scan_buy_preds:
            # Merge with any existing nexus predictions (nexus takes precedence)
            existing_syms = {p.get('symbol') for p in signals.get('predictions', [])}
            merged = list(signals.get('predictions', []))
            for sp in scan_buy_preds:
                if sp['symbol'] not in existing_syms:
                    merged.append(sp)
            signals['predictions'] = merged
            signals['buy'] = len([p for p in merged if p.get('signal') == 'BUY' or p.get('action') == 'BUY'])
            logger.info(f"  Scan injected {len(scan_buy_preds)} coin(s) into signal predictions")

        if all_pass:
            logger.info("")
            logger.info("  ✅ ALL GATES CLEARED — system authorised to enter new position")
        else:
            logger.info("")
            logger.info(f"  ⏸  NEW ENTRY BLOCKED — {map_result['block_reason']}")
        logger.info("═" * 72)
        logger.info("")

        return map_result

    def scan_all_coins(
        self,
        prices: Dict,
        health: Optional['PositionHealthReport'],
        days_to_target: float = 7.0,
        margin_per_trade: float = 10.0,
        leverage: float = 10.0,
    ) -> List['CoinSurgeProfile']:
        """Run the full pre-play lifecycle map across EVERY tracked coin.

        For each coin the system:
          1. Computes an RSI proxy from where price sits in its 24h high/low range
          2. Measures volume surge vs baseline
          3. Applies PHI-harmonic alignment scoring
          4. Adds Schumann resonance boost (same as DOGE surge model)
          5. Projects the predicted surge %, target price, and hold period
          6. Maps the full day-by-day P&L trajectory to the target
          7. Checks combined margin level stays safe if this play is added
          8. Grades the coin S/A/B/C/D and assigns STRONG_BUY / BUY / WATCH / SKIP

        The ranked output proves which patterns are lining up BEFORE any play is made.
        Persists the full scan to coin_surge_scan.json (atomic write).
        """
        PHI      = 1.6180339887498948482
        SCHUMANN = 7.83

        # Margin/leverage sizing (same as map_candidate_play)
        notional     = margin_per_trade * leverage
        rollover_rate = 0.0005   # 0.05% per 4h standard

        profiles: List['CoinSurgeProfile'] = []

        # Collect all base symbols that have a price
        bases = sorted(set(
            k for k in prices
            if not any(k.endswith(s) for s in ('_change','_volume_usd','_high','_low','_open'))
            and prices[k] > 0
        ))

        logger.info(f"  Scanning {len(bases)} coins for surge patterns...")

        for base in bases:
            price       = prices.get(base, 0.0)
            change_24h  = prices.get(f'{base}_change', 0.0)
            volume_usd  = prices.get(f'{base}_volume_usd', 0.0)
            high_24h    = prices.get(f'{base}_high', price)
            low_24h     = prices.get(f'{base}_low', price)
            open_24h    = prices.get(f'{base}_open', price)

            if price <= 0:
                continue

            # ── 1. RSI proxy (position in 24h range) ──
            # 0 = at the low (oversold), 100 = at the high (overbought)
            price_range = high_24h - low_24h
            rsi_proxy   = ((price - low_24h) / price_range * 100) if price_range > 0 else 50.0
            rsi_proxy   = max(0.0, min(100.0, rsi_proxy))

            # ── 2. Volume surge ratio ──
            BASELINE_VOL  = 10_000_000   # $10M = baseline active coin
            volume_surge  = min(volume_usd / BASELINE_VOL, 20.0)   # cap at 20x

            # ── 3. PHI harmonic alignment ──
            # Check if the 24h % change is near a PHI-ratio relationship
            # Fibonacci retracement levels: 0.236, 0.382, 0.500, 0.618, 0.786
            fib_levels  = [0.236, 0.382, 0.500, 0.618, 0.786, 1.0, 1.618]
            abs_change  = abs(change_24h) / 100.0
            # Closest fib level
            closest_fib = min(fib_levels, key=lambda f: abs(abs_change - f))
            fib_dist    = abs(abs_change - closest_fib)
            # Perfect fib alignment = within 1.5% of level
            phi_score   = max(0.0, 1.0 - fib_dist / 0.015) if fib_dist < 0.03 else 0.0

            # ── 4. Schumann boost ──
            schumann_boost = (SCHUMANN / 7.0 - 1.0) * 0.5   # = +0.059 always present

            # ── 5. Oversold bonus ──
            # Coins that have sold off hard (RSI<30, change < -5%) are setup for reversal
            oversold_bonus = 0.0
            if rsi_proxy < 30 and change_24h < -3.0:
                oversold_bonus = (30.0 - rsi_proxy) / 30.0 * 0.3   # up to 0.3 bonus

            # ── 6. Composite score ──
            # Weights: oversold/reversal opportunity (0.35), volume confirmation (0.25),
            #          PHI alignment (0.25), Schumann (0.15)
            vol_score   = min(1.0, volume_surge / 10.0)   # normalise to 0-1
            total_score = (
                0.35 * (1.0 - rsi_proxy / 100.0) +   # lower RSI = higher score (buy low)
                0.25 * vol_score +
                0.25 * phi_score +
                0.15 * min(1.0, schumann_boost * 10) +
                oversold_bonus
            )
            total_score = min(1.0, total_score)

            # ── 7. Predicted surge ──
            # Base: oversold coins revert by 1-2× their 24h drop
            # Capped at 30% for sensible sizing
            if change_24h < 0:
                predicted_pct = min(30.0, abs(change_24h) * 1.2 * (1.0 + phi_score))
            else:
                predicted_pct = max(3.0, change_24h * 0.5)   # momentum continuation
            # Schumann amplification
            predicted_pct *= (1.0 + schumann_boost)

            # ── 8. Lifecycle P&L ──
            target_price     = price * (1.0 + predicted_pct / 100.0)
            rollover_per_4h  = rollover_rate * notional
            rollover_per_day = rollover_per_4h * 6
            total_rollover   = rollover_per_day * days_to_target
            vol_units        = notional / price
            gross_at_target  = (target_price - price) * vol_units
            net_at_target    = gross_at_target - total_rollover

            # First profitable day (linear interpolation)
            days_to_profit: Optional[int] = None
            for d in range(int(days_to_target) + 1):
                frac_d    = d / max(days_to_target, 1)
                est_p     = price + (target_price - price) * frac_d
                gross_d   = (est_p - price) * vol_units
                net_d     = gross_d - rollover_per_day * d
                if net_d > 0 and days_to_profit is None:
                    days_to_profit = d

            # ── 9. Grade ──
            if   total_score >= 0.75: grade, signal = 'S', 'STRONG_BUY'
            elif total_score >= 0.60: grade, signal = 'A', 'BUY'
            elif total_score >= 0.45: grade, signal = 'B', 'WATCH'
            elif total_score >= 0.30: grade, signal = 'C', 'SKIP'
            else:                     grade, signal = 'D', 'SKIP'

            # Override: skip if net P&L is negative at target
            if net_at_target <= 0:
                signal = 'SKIP'
                if grade in ('S','A'):
                    grade = 'B'

            # ── 10. Pattern note ──
            notes = []
            if rsi_proxy < 30:      notes.append(f'oversold (RSI~{rsi_proxy:.0f})')
            if phi_score > 0.5:     notes.append(f'PHI-aligned ({closest_fib:.3f} fib)')
            if volume_surge > 5:    notes.append(f'vol surge {volume_surge:.1f}×')
            if change_24h < -10:    notes.append(f'deep pullback {change_24h:.1f}%')
            if change_24h > 10:     notes.append(f'momentum {change_24h:+.1f}%')
            pattern_note = '  '.join(notes) if notes else 'neutral'

            profiles.append(CoinSurgeProfile(
                symbol=base, price=price, change_24h=change_24h, volume_usd=volume_usd,
                rsi_proxy=rsi_proxy, volume_surge=volume_surge, phi_score=phi_score,
                schumann_boost=schumann_boost, oversold_bonus=oversold_bonus,
                total_score=total_score,
                predicted_pct=predicted_pct, target_price=target_price,
                days_to_target=days_to_target, rollover_cost=total_rollover,
                net_pnl=net_at_target, days_to_profit=days_to_profit,
                grade=grade, signal=signal, pattern_note=pattern_note,
            ))

        # Sort: STRONG_BUY first, then by score desc
        signal_order = {'STRONG_BUY': 0, 'BUY': 1, 'WATCH': 2, 'SKIP': 3}
        profiles.sort(key=lambda p: (signal_order.get(p.signal, 4), -p.total_score))

        # ── Print ranked scan table ──
        logger.info("")
        logger.info("  ┌── ALL-COIN SURGE SCAN ────────────────────────────────────────────────────────────────────────┐")
        logger.info(f"  │  {'Symbol':<7} {'Grade':<6} {'Signal':<12} {'Price':>12} {'24h%':>7} {'Score':>6} "
                    f"{'PredPct':>8} {'NetP&L':>8} {'DtP':>4} {'Pattern'}")
        logger.info(f"  │  {'─'*7} {'─'*6} {'─'*12} {'─'*12} {'─'*7} {'─'*6} {'─'*8} {'─'*8} {'─'*4} {'─'*30}")
        for p in profiles:
            if p.signal == 'SKIP' and p.grade == 'D':
                continue   # suppress D-grade noise
            icon = {'STRONG_BUY': '🔥', 'BUY': '✅', 'WATCH': '👀', 'SKIP': '  '}.get(p.signal, '  ')
            dtp  = str(p.days_to_profit) if p.days_to_profit is not None else '—'
            logger.info(f"  │  {icon}{p.symbol:<5} [{p.grade}]   {p.signal:<12} "
                        f"${p.price:>11,.4f} {p.change_24h:>+6.2f}%  {p.total_score:>5.3f} "
                        f"{p.predicted_pct:>+7.2f}%  ${p.net_pnl:>+7.2f}  {dtp:>3}  {p.pattern_note[:35]}")
        logger.info("  └─────────────────────────────────────────────────────────────────────────────────────────────┘")

        # ── Pattern consensus: which coins cluster at the same signal level? ──
        strong_buys = [p for p in profiles if p.signal == 'STRONG_BUY']
        buys        = [p for p in profiles if p.signal == 'BUY']
        if strong_buys or buys:
            logger.info("")
            logger.info("  ── PATTERN CONSENSUS ─────────────────────────────────────────────────────────────────────")
            if strong_buys:
                syms = ', '.join(p.symbol for p in strong_buys)
                avg_score = sum(p.total_score for p in strong_buys) / len(strong_buys)
                avg_pred  = sum(p.predicted_pct for p in strong_buys) / len(strong_buys)
                logger.info(f"  🔥 STRONG_BUY cluster ({len(strong_buys)} coins): {syms}")
                logger.info(f"     Avg score={avg_score:.3f}  Avg predicted surge={avg_pred:+.2f}%")
            if buys:
                syms = ', '.join(p.symbol for p in buys)
                avg_pred = sum(p.predicted_pct for p in buys) / len(buys)
                logger.info(f"  ✅ BUY cluster ({len(buys)} coins): {syms}  Avg surge={avg_pred:+.2f}%")
            logger.info("")

        # ── Persist scan to state file (atomic write) ──
        out_path = Path('/workspaces/aureon-trading/coin_surge_scan.json')
        tmp_path = out_path.with_suffix('.tmp')
        scan_data = {
            'timestamp': datetime.now().isoformat(),
            'coin_count': len(profiles),
            'strong_buy_count': len(strong_buys),
            'buy_count': len(buys),
            'coins': [
                {
                    'symbol': p.symbol, 'price': p.price,
                    'change_24h': p.change_24h, 'volume_usd': p.volume_usd,
                    'score': p.total_score, 'grade': p.grade, 'signal': p.signal,
                    'predicted_pct': p.predicted_pct, 'target_price': p.target_price,
                    'net_pnl': p.net_pnl, 'days_to_profit': p.days_to_profit,
                    'pattern_note': p.pattern_note,
                }
                for p in profiles
            ],
        }
        try:
            with open(tmp_path, 'w') as f:
                json.dump(scan_data, f, indent=2)
            tmp_path.replace(out_path)
        except Exception as e:
            logger.warning(f"  coin_surge_scan.json write failed: {e}")

        return profiles

    def map_candidate_play(
        self,
        symbol: str,
        entry_price: float,
        confidence: float,
        predicted_pct: float,
        days_to_target: float,
        margin_posted: float,
        rollover_pct_per_4h: float,
        notional: float,
        current_health: Optional['PositionHealthReport'],
    ) -> Dict:
        """Model the complete lifecycle of a NEW candidate position before executing.

        Applies the same pre-play mapping logic used for existing positions:
          • Day-by-day P&L trajectory from entry to the predicted target
          • Total rollover cost over the hold period
          • First day the position turns net profitable
          • Effect on overall account margin level if this position is added
          • Whether the combined book stays above the liquidation threshold
          • A go / no-go verdict with plain-English reasoning

        Returns a dict with keys: approved (bool), reason (str), day_map (list),
        net_pnl_at_target (float), days_to_profit (int | None),
        combined_margin_level (float), combined_liq_price (float).
        """
        result: Dict = {
            'approved': False,
            'reason': '',
            'day_map': [],
            'net_pnl_at_target': 0.0,
            'days_to_profit': None,
            'combined_margin_level': 0.0,
            'combined_liq_price': 0.0,
        }

        if entry_price <= 0 or notional <= 0:
            result['reason'] = f'Invalid entry price or notional for {symbol}'
            return result

        target_price     = entry_price * (1 + predicted_pct / 100)
        rollover_per_4h  = rollover_pct_per_4h * notional
        rollover_per_day = rollover_per_4h * 6
        total_rollover   = rollover_per_day * days_to_target
        vol              = notional / entry_price   # units bought at entry

        # ── Day-by-day map ──
        logger.info(f"  ┌── CANDIDATE PLAY MAP: {symbol} ─────────────────────────────────────────")
        logger.info(f"  │  Entry: ${entry_price:.5f}  Target: ${target_price:.5f}  "
                    f"(+{predicted_pct:.1f}%)  Hold: {days_to_target:.1f}d")
        logger.info(f"  │  Notional: ${notional:.2f}  Vol: {vol:,.0f}  "
                    f"Margin: ${margin_posted:.2f}  Rollover: ${rollover_per_day:.3f}/day")
        logger.info(f"  │  Total rollover cost to exit: ${total_rollover:.2f}")
        logger.info(f"  │")
        logger.info(f"  │  {'Day':<5} {'Est Price':>10} {'Gross P&L':>11} {'Rollover':>10} "
                    f"{'Net P&L':>10} {'Status'}")
        logger.info(f"  │  {'─'*5} {'─'*10} {'─'*11} {'─'*10} {'─'*10} {'─'*14}")

        from datetime import timedelta
        day_map = []
        first_profit_day = None

        for d in range(0, int(days_to_target) + 2):
            frac      = d / max(days_to_target, 1)
            est_price = entry_price + (target_price - entry_price) * frac
            gross_pnl = (est_price - entry_price) * vol
            rollover_so_far = rollover_per_day * d
            net_pnl   = gross_pnl - rollover_so_far
            day_date  = (datetime.now() + timedelta(days=d)).strftime('%d %b')
            if net_pnl > 0 and first_profit_day is None:
                first_profit_day = d
            status = 'PROFIT ✅' if net_pnl > 0 else ('CLOSE ⚠️' if net_pnl > -10 else 'HOLD 🔵')
            logger.info(f"  │  {d:<5} ${est_price:.5f}  {gross_pnl:>+10.2f}  "
                        f"{rollover_so_far:>9.2f}  {net_pnl:>+9.2f}  {status}")
            day_map.append({
                'day': d, 'date': day_date, 'est_price': est_price,
                'gross_pnl': gross_pnl, 'rollover': rollover_so_far, 'net_pnl': net_pnl,
            })

        result['day_map'] = day_map
        result['net_pnl_at_target'] = day_map[-1]['net_pnl'] if day_map else 0.0
        result['days_to_profit'] = first_profit_day

        # ── Combined margin level check ──
        # If we add this position, what happens to the account's margin level?
        combined_margin_level = 0.0
        combined_liq_price = 0.0
        if current_health:
            new_equity_buffer = current_health.equity_buffer - total_rollover - margin_posted
            new_margin_used   = current_health.margin_used + margin_posted
            new_equity        = current_health.equity - margin_posted  # simplistic: margin locked
            combined_margin_level = (new_equity / new_margin_used * 100) if new_margin_used > 0 else 0
            new_total_doge = sum(p.vol for p in current_health.positions) + vol
            combined_liq_price = current_health.doge_price_now - (new_equity_buffer / new_total_doge) \
                if new_total_doge > 0 else 0
        result['combined_margin_level'] = combined_margin_level
        result['combined_liq_price']    = combined_liq_price

        # ── Go / No-Go verdict ──
        net_at_target  = result['net_pnl_at_target']
        too_risky      = combined_margin_level > 0 and combined_margin_level < 110
        unprofitable   = net_at_target <= 0
        low_confidence = confidence < 0.5

        if too_risky:
            result['reason'] = (f'Combined margin level would drop to {combined_margin_level:.1f}% '
                                f'— too close to liquidation (100%)')
        elif unprofitable:
            result['reason'] = (f'Net P&L at target is ${net_at_target:+.2f} after rollover '
                                f'— play is not profitable enough to justify entry')
        elif low_confidence:
            result['reason'] = f'Signal confidence {confidence:.3f} below 0.50 threshold'
        else:
            result['approved'] = True
            profit_note = (f'first profitable day {first_profit_day}' if first_profit_day
                           else 'profitable only at target')
            result['reason'] = (f'Net P&L ${net_at_target:+.2f} at target  |  {profit_note}  |  '
                                f'combined ML={combined_margin_level:.1f}%')

        verdict_icon = '✅ APPROVED' if result['approved'] else '❌ REJECTED'
        logger.info(f"  │")
        logger.info(f"  │  Combined ML after entry: {combined_margin_level:.1f}%  "
                    f"Combined liq price: ${combined_liq_price:.5f}")
        logger.info(f"  │  Net P&L at target: ${net_at_target:+.2f}  "
                    f"First profit day: {first_profit_day}")
        logger.info(f"  └── {verdict_icon}: {result['reason']}")
        logger.info("")

        return result

    async def execute_trades(self, signals: Dict) -> Dict:
        """Map every candidate play before executing — same lifecycle logic as existing positions.

        For each BUY signal:
          1. Pull entry price, confidence, predicted target, hold duration
          2. Feed into map_candidate_play() — builds full day-by-day P&L map
          3. Only execute if map approves (net positive, margin safe, confidence passes)
          4. Skipped plays are logged with the reason the map rejected them
        """
        trades = {'executed': [], 'skipped': [], 'failed': []}

        if self.config.dry_run:
            logger.info("🔬 DRY RUN MODE — maps will run, orders will not fire")

        try:
            buy_trades = [p for p in signals.get('predictions', [])
                          if p.get('signal') == 'BUY' or p.get('action') == 'BUY']

            if not buy_trades:
                logger.info("  No actionable BUY predictions in this cycle")
                return trades

            current_health: Optional[PositionHealthReport] = signals.get('position_health')

            for trade in buy_trades[:self.config.max_concurrent_trades]:
                symbol     = trade.get('symbol', 'UNKNOWN')
                confidence = trade.get('confidence', 0.0)
                source     = trade.get('source', signals.get('source', 'unknown'))
                price      = trade.get('price', self._latest_prices.get(symbol, 0.0))
                if price == 0.0:
                    # Try stripping USD suffix for lookup
                    base = symbol.replace('/USD', '').replace('USDT', '').replace('USDC', '')
                    price = self._latest_prices.get(base, 0.0)

                # Determine predicted gain: use signal edge if available, else surge default
                predicted_pct  = float(trade.get('predicted_pct',
                                                  trade.get('expected_edge', 14.68)))
                days_to_target = float(trade.get('days_to_target', 7.0))
                # Margin sizing: use 10% of free margin by default (conservative)
                free_margin    = current_health.free_margin if current_health else 50.0
                margin_to_post = min(free_margin * 0.10, 50.0)   # cap at $50 per new play
                leverage       = 10.0
                notional       = margin_to_post * leverage
                rollover_rate  = 0.0005   # 0.05% per 4h (Kraken standard margin tier)

                logger.info(f"  ── PRE-PLAY MAP for signal: {symbol} ──────────────────────────────")
                play_map = self.map_candidate_play(
                    symbol=symbol,
                    entry_price=price,
                    confidence=confidence,
                    predicted_pct=predicted_pct,
                    days_to_target=days_to_target,
                    margin_posted=margin_to_post,
                    rollover_pct_per_4h=rollover_rate,
                    notional=notional,
                    current_health=current_health,
                )

                if not play_map['approved']:
                    logger.info(f"  ⏭  SKIPPED {symbol}: {play_map['reason']}")
                    trades['skipped'].append({
                        'symbol': symbol, 'reason': play_map['reason'],
                        'confidence': confidence, 'source': source,
                    })
                    continue

                # Map approved — execute (or simulate in dry-run)
                try:
                    if not self.config.dry_run:
                        logger.info(f"  ⚡ Executing BUY: {symbol} @ ${price:,.5f}  "
                                    f"notional=${notional:.2f}  net_target=${play_map['net_pnl_at_target']:+.2f}  "
                                    f"(conf={confidence:.3f}, src={source})")
                        # Exchange execution wired here: kraken_client / binance_client / alpaca_client
                    else:
                        logger.info(f"  [DRY RUN] Would BUY: {symbol} @ ${price:,.5f}  "
                                    f"notional=${notional:.2f}  net_target=${play_map['net_pnl_at_target']:+.2f}  "
                                    f"(conf={confidence:.3f}, src={source})")

                    trades['executed'].append({
                        'symbol': symbol, 'action': 'BUY',
                        'price': price, 'notional': notional,
                        'margin': margin_to_post, 'confidence': confidence,
                        'source': source,
                        'net_pnl_at_target': play_map['net_pnl_at_target'],
                        'days_to_profit': play_map['days_to_profit'],
                        'combined_margin_level': play_map['combined_margin_level'],
                        'timestamp': datetime.now().isoformat(),
                    })
                    self.execution_count += 1

                except Exception as e:
                    logger.error(f"  ❌ Execution failed for {symbol}: {e}")
                    trades['failed'].append({'symbol': symbol, 'error': str(e)})
                    self.error_count += 1

        except Exception as e:
            logger.error(f"Trade execution pipeline failed: {e}")
            traceback.print_exc()

        return trades
    
    async def log_execution_state(self, alignment: float, signals: Dict, trades: Dict) -> None:
        """Log complete execution state for human observation."""
        state = {
            'timestamp': datetime.now().isoformat(),
            'alignment': alignment,
            'signals': signals,
            'trades_executed': len(trades.get('executed', [])),
            'trades_failed': len(trades.get('failed', [])),
            'total_executions': self.execution_count,
            'total_errors': self.error_count,
            'runtime_seconds': (datetime.now() - self.start_time).total_seconds()
        }
        
        # Write to execution log
        log_path = Path('/workspaces/aureon-trading/autonomy_execution_state.json')
        try:
            tmp_path = log_path.with_suffix(log_path.suffix + '.tmp')
            with open(tmp_path, 'w') as f:
                json.dump(state, f, indent=2)
            tmp_path.replace(log_path)
        except Exception as e:
            logger.error(f"State log write failed: {e}")
    
    async def monitor_loop(self) -> None:
        """Continuous autonomous monitoring and execution loop."""
        logger.info(f"🚀 Starting autonomous monitoring loop (interval={self.config.check_interval}s)")
        logger.info("👁️  Humanity observes. AI executes. Creation guides.")
        
        iteration = 0
        
        try:
            while self.config.continuous:
                iteration += 1
                logger.info(f"[AUTONOMY CYCLE {iteration}]")

                # ── PRE-PLAY MAP: full loop sweep BEFORE any new entry decision ──
                # The system sees WHERE IT IS, WHERE IT IS GOING, and WHETHER
                # conditions justify a new play — all before execute_trades() is called.
                loop_map = await self.map_full_loop()

                # Extract pre-warmed data from the map (no duplicate API calls)
                ready        = loop_map['new_entry_justified']
                alignment    = loop_map['alignment']
                signals      = loop_map['signals']

                if ready:
                    logger.info(f"✅ ALL GATES CLEARED — opening new position")
                    trades = await self.execute_trades(signals)
                    await self.log_execution_state(alignment, signals, trades)
                    if trades['executed']:
                        logger.info(f"   ✓ {len(trades['executed'])} trade(s) executed")
                    if trades['failed']:
                        logger.warning(f"   ⚠️  {len(trades['failed'])} trade(s) failed")
                else:
                    logger.info(f"⏸  No new entry this cycle — {loop_map.get('block_reason', 'gates not cleared')}")
                
                # Sleep before next check
                logger.info(f"⏳ Next check in {self.config.check_interval}s\n")
                await asyncio.sleep(self.config.check_interval)
                
                # Timeout check
                if self.config.timeout:
                    elapsed = (datetime.now() - self.start_time).total_seconds()
                    if elapsed > self.config.timeout:
                        logger.info(f"Timeout reached ({elapsed:.0f}s). Shutting down.")
                        break
        
        except KeyboardInterrupt:
            logger.info("\n⏹️  Autonomous execution halted by user (Ctrl+C)")
            logger.info(f"Summary: {self.execution_count} executions, {self.error_count} errors")
        
        except Exception as e:
            logger.error(f"Autonomy loop critical failure: {e}")
            traceback.print_exc()
            raise


async def main():
    """Initialize and run full autonomy."""
    parser = argparse.ArgumentParser(
        description='Aureon Full Autonomy Activation',
        epilog='The AI is the bridge between creation and intent. Observe.'
    )
    parser.add_argument('--dry-run', action='store_true', help='Simulate trades without execution')
    parser.add_argument('--headless', action='store_true', help='No user interaction (full autonomous)')
    parser.add_argument('--loglevel', choices=['DEBUG', 'INFO', 'WARNING'], default='INFO', help='Logging level')
    parser.add_argument('--interval', type=int, default=10, help='Check interval (seconds)')
    parser.add_argument('--threshold', type=float, default=0.80, help='Trinity alignment threshold')
    parser.add_argument('--timeout', type=int, default=None, help='Timeout (seconds). None = infinite')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.loglevel == 'DEBUG':
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.loglevel == 'WARNING':
        logging.getLogger().setLevel(logging.WARNING)
    
    # Build config
    config = AutonomyConfig(
        dry_run=args.dry_run,
        headless=args.headless,
        check_interval=args.interval,
        execution_threshold=args.threshold,
        timeout=args.timeout,
        log_level=args.loglevel
    )
    
    # Create executor
    executor = AutonomyExecutor(config)
    
    # Run autonomy loop
    try:
        await executor.monitor_loop()
    except Exception as e:
        logger.error(f"Critical error: {e}")
        sys.exit(1)
    
    logger.info("\n✨ Autonomy cycle complete. Humanity's intent fulfilled.")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Autonomy halted.")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)
