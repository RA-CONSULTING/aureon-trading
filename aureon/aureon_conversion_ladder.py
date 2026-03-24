#!/usr/bin/env python3
"""Conversion Ladder (Capital Momentum Builder)

Purpose:
- Rotate capital between assets using existing exchange conversion paths.
- Use Mycelium directional intelligence (queen/coherence/memory) as the primary driver.
- Operate in stages:
  1) Suggestion-only (emit events + logs)
  2) Execution (call existing client.convert_crypto)

This module intentionally does not hard-depend on Binance Convert OTC APIs.
It uses the repo's existing conversion plumbing via `MultiExchangeClient`.
"""

from __future__ import annotations
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


STABLES = ("USDT", "USDC", "USD", "GBP", "EUR")
BLUECHIPS = (
    "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "AVAX", "DOT", "LINK", "LTC"
)


@dataclass
class LadderDecision:
    ts: float
    mode: str  # suggest|execute
    direction: str  # UP|DOWN|LEFT|RIGHT|A-Z|Z-A
    exchange: str
    from_asset: str
    to_asset: str
    amount: float
    reason: str
    path: Optional[List[Dict[str, Any]]] = None
    result: Optional[Dict[str, Any]] = None


class ConversionLadder:
    """Mycelium-guided capital rotation using conversion paths."""

    def __init__(self, *, bus: Any = None, mycelium: Any = None, client: Any = None):
        self.bus = bus
        self.mycelium = mycelium
        self.client = client

        self.mode = (os.getenv("AUREON_LADDER_MODE", "suggest") or "suggest").strip().lower()
        if self.mode not in ("suggest", "execute"):
            self.mode = "suggest"

        self.enabled = (os.getenv("AUREON_LADDER_ENABLED", "0") or "0").strip() in ("1", "true", "yes", "on")

        self.fraction = self._safe_float(os.getenv("AUREON_LADDER_FRACTION", "0.25"), 0.25, lo=0.01, hi=0.95)
        self.min_value_usd = self._safe_float(os.getenv("AUREON_LADDER_MIN_VALUE_USD", "8"), 8.0, lo=0.0, hi=1e9)
        self.cooldown_s = self._safe_float(os.getenv("AUREON_LADDER_COOLDOWN_S", "60"), 60.0, lo=0.0, hi=1e9)

        # Net-profit gate: follow the ecosystem rule that we prefer confirmed net profit.
        # If net profit is negative, the ladder will only de-risk (DOWN) and will not rotate out of stables.
        self.net_profit_gate_enabled = (os.getenv("AUREON_LADDER_NET_PROFIT_GATE", "1") or "1").strip() in (
            "1", "true", "yes", "on"
        )
        # Bootstrap: allow early rotations while net profit is flat (>=0) but below floor.
        # Default off for safety; enable in sims or deliberate ladder bootstrapping.
        self.bootstrap_enabled = (os.getenv("AUREON_LADDER_BOOTSTRAP", "0") or "0").strip().lower() in (
            "1", "true", "yes", "on"
        )
        # Absolute floor (USD) can be overridden, but defaults to "penny" minimum.
        self.penny_min_net = self._safe_float(os.getenv("AUREON_LADDER_PENNY_MIN_NET", "0.01"), 0.01, lo=0.0, hi=1e9)
        self.net_profit_floor = self._safe_float(os.getenv("AUREON_LADDER_NET_PROFIT_FLOOR", "0"), 0.0, lo=-1e12, hi=1e12)
        # Optional dynamic scaling: require net_profit >= max(penny, equity * pct).
        self.net_profit_pct = self._safe_float(os.getenv("AUREON_LADDER_NET_PROFIT_PCT", "0"), 0.0, lo=0.0, hi=1.0)

        # Exchange selection: prefer certain venues first (e.g., "binance,kraken").
        # Default is Binance-first to match the intended ladder flow.
        prio_raw = (os.getenv("AUREON_LADDER_EXCHANGE_PRIORITY", "binance") or "binance").strip()
        prio = [p.strip().lower() for p in prio_raw.replace(";", ",").split(",") if p.strip()]
        self.exchange_priority: List[str] = prio or ["binance"]

        self._last_action_ts: float = 0.0
        self._last_decision: Optional[LadderDecision] = None

    def _ordered_exchanges(self, balances: Dict[str, Dict[str, float]]) -> List[str]:
        present = [str(ex) for ex in (balances or {}).keys()]
        present_lc = {ex.lower(): ex for ex in present}

        ordered: List[str] = []
        for want in self.exchange_priority:
            ex = present_lc.get(want.lower())
            if ex and ex not in ordered:
                ordered.append(ex)
        for ex in present:
            if ex not in ordered:
                ordered.append(ex)
        return ordered

    @staticmethod
    def _safe_float(v: Any, default: float, *, lo: float, hi: float) -> float:
        try:
            x = float(v)
            if x != x:
                return default
            return max(lo, min(hi, x))
        except Exception:
            return default

    def _emit(self, topic: str, payload: Dict[str, Any]) -> None:
        """Emit into ThoughtBus if available."""
        if not self.bus:
            return
        try:
            from aureon_thought_bus import Thought

            self.bus.publish(
                Thought(source="ladder", topic=f"ladder.{topic}", payload=payload)
            )
        except Exception:
            # Non-fatal; ladder still works without bus.
            return

    def _emit_to_mycelium_link(self, topic: str, payload: Dict[str, Any]) -> None:
        """Emit a normalized Mycelium link event (so the neural system can ingest it)."""
        if not self.bus:
            return
        try:
            from aureon_thought_bus import Thought

            self.bus.publish(
                Thought(source="ladder", topic=f"mycelium.link.{topic}", payload=payload)
            )
        except Exception:
            return

    def _resolve_direction(self, fallback_scan_direction: str = "A→Z") -> str:
        """Map Mycelium state to directional movement."""
        override = (os.getenv("AUREON_LADDER_DIRECTION") or "").strip().upper()
        if override:
            # Accept variants
            if override in ("UP", "DOWN", "LEFT", "RIGHT", "A-Z", "Z-A"):
                return override
            if override in ("A→Z", "A->Z"):
                return "A-Z"
            if override in ("Z→A", "Z->A"):
                return "Z-A"

        queen = 0.0
        coherence = 0.5
        try:
            if self.mycelium and hasattr(self.mycelium, "get_queen_signal"):
                queen = float(self.mycelium.get_queen_signal())
        except Exception:
            queen = 0.0
        try:
            if self.mycelium and hasattr(self.mycelium, "get_network_coherence"):
                coherence = float(self.mycelium.get_network_coherence())
        except Exception:
            coherence = 0.5

        # Clear intent mapping:
        # - Strong bullish queen or high coherence => climb (UP)
        # - Strong bearish queen => de-risk (DOWN)
        if queen >= 0.35 or coherence >= 0.72:
            return "UP"
        if queen <= -0.35 or coherence <= 0.35:
            return "DOWN"

        # Otherwise follow fairness scan direction
        fsd = (fallback_scan_direction or "").strip()
        if "Z" in fsd and fsd.startswith("Z"):
            return "Z-A"
        return "A-Z"

    def _pick_source_holding(self, balances: Dict[str, Dict[str, float]]) -> Optional[Tuple[str, str, float, float]]:
        """Pick a source holding: (exchange, asset, qty, value_usd).

        Behavior:
        - Prefer exchanges in `self.exchange_priority` (default: Binance first).
        - If none of the preferred exchanges have an eligible holding, fall back to others.
        - Within the chosen exchange, pick the largest eligible holding by USD value.
        """

        exchanges = self._ordered_exchanges(balances)
        # Track the best holding within each exchange; pick the first exchange that yields one.
        locked: set[str] = set()
        try:
            locked = set(getattr(self, '_locked_assets', set()) or set())
        except Exception:
            locked = set()

        for ex in exchanges:
            b = (balances or {}).get(ex)
            if not isinstance(b, dict):
                continue

            best_in_ex = None
            for asset, qty in b.items():
                try:
                    q = float(qty or 0)
                except Exception:
                    continue
                if q <= 0:
                    continue
                asset_u = str(asset).upper()
                if locked and asset_u in locked:
                    continue
                if asset_u in ("NFT", "BONUS"):
                    continue
                # Estimate USD value via existing convert_to_quote if possible
                value = 0.0
                try:
                    if self.client and hasattr(self.client, "convert_to_quote"):
                        value = float(self.client.convert_to_quote(ex, asset_u, q, "USDT") or 0.0)
                except Exception:
                    value = 0.0

                if value <= 0:
                    # Fallback heuristic: treat stables as face value
                    if asset_u in STABLES:
                        value = q

                if value < self.min_value_usd:
                    continue

                if best_in_ex is None or value > best_in_ex[3]:
                    best_in_ex = (ex, asset_u, q, value)

            if best_in_ex is not None:
                return best_in_ex

        return None

    def _candidate_targets(self, exchange: str, from_asset: str, convertible: Dict[str, Dict[str, List[str]]]) -> List[str]:
        m = convertible.get(exchange) or {}
        nxt = m.get(from_asset) or []
        out = [str(a).upper() for a in nxt if a]
        # Never target the same asset
        out = [a for a in out if a != from_asset]
        return out

    def _choose_target(self, *, direction: str, from_asset: str, candidates: List[str], ticker_cache: Dict[str, Dict[str, Any]]) -> Optional[str]:
        if not candidates:
            return None

        # DOWN: de-risk into stables if possible
        if direction == "DOWN":
            for s in STABLES:
                if s != from_asset and s in candidates:
                    return s
            # If no stable available, prefer BTC/ETH
            for s in ("BTC", "ETH"):
                if s != from_asset and s in candidates:
                    return s

        # LEFT/RIGHT: rotate inside bluechips if possible
        if direction in ("LEFT", "RIGHT"):
            band = [a for a in candidates if a in BLUECHIPS]
            if band:
                band_sorted = sorted(band)
                if direction == "LEFT":
                    return band_sorted[0]
                return band_sorted[-1]

        # A-Z / Z-A: deterministic alphabetical move
        if direction in ("A-Z", "Z-A"):
            alpha = sorted(candidates)
            return alpha[0] if direction == "A-Z" else alpha[-1]

        # UP: choose highest momentum target (using tickers if available)
        if direction == "UP":
            scored: List[Tuple[float, str]] = []
            for asset in candidates:
                score = self._asset_momentum_score(asset, ticker_cache)
                scored.append((score, asset))
            scored.sort(reverse=True)
            # Prefer best score; if all scores are 0, fall back to alpha
            if scored and scored[0][0] > 0:
                return scored[0][1]
            return sorted(candidates)[0]

        # Default
        return sorted(candidates)[0]

    @staticmethod
    def _asset_momentum_score(asset: str, tickers: Dict[str, Dict[str, Any]]) -> float:
        """Compute a rough momentum score for a base asset.

        Uses whichever quotes exist in ticker_cache; prefers USDT/USD/GBP/EUR.
        Score is volume-weighted 24h change.
        """
        if not tickers:
            return 0.0
        best = 0.0
        for q in ("USDT", "USD", "GBP", "EUR", "USDC"):
            sym = f"{asset}{q}"
            t = tickers.get(sym)
            if not isinstance(t, dict):
                continue
            try:
                change = float(t.get("change24h", 0) or 0)
            except Exception:
                change = 0.0
            try:
                vol = float(t.get("volume", 0) or 0)
            except Exception:
                vol = 0.0
            # squash volume so it doesn't dominate
            score = change * (1.0 + min(vol / 1e7, 5.0) * 0.15)
            if score > best:
                best = score
        return best

    def step(
        self,
        *,
        ticker_cache: Dict[str, Dict[str, Any]],
        scan_direction: str = "A→Z",
        net_profit: Optional[float] = None,
        portfolio_equity: Optional[float] = None,
        preferred_assets: Optional[List[str]] = None,
        locked_assets: Optional[List[str]] = None,
    ) -> Optional[LadderDecision]:
        """One ladder step.

        Stage behavior:
        - suggest: compute next hop and emit event
        - execute: call convert_crypto via existing client plumbing

        Returns the decision when one is made.
        """
        if not self.enabled:
            return None

        now = time.time()
        if self.cooldown_s and (now - self._last_action_ts) < self.cooldown_s:
            return None

        if not self.client or not hasattr(self.client, "get_all_balances"):
            return None

        # Stash locked assets for this step (used by _pick_source_holding).
        try:
            self._locked_assets = set(a.upper() for a in (locked_assets or []) if a)
        except Exception:
            self._locked_assets = set()

        # Build convertible map
        convertible: Dict[str, Dict[str, List[str]]] = {}
        try:
            if hasattr(self.client, "get_all_convertible_assets"):
                convertible = self.client.get_all_convertible_assets() or {}
        except Exception:
            convertible = {}

        # Pick largest holding as source
        try:
            balances = self.client.get_all_balances() or {}
        except Exception:
            balances = {}

        src = self._pick_source_holding(balances)
        if not src:
            return None
        exchange, from_asset, qty, value_usd = src

        direction = self._resolve_direction(fallback_scan_direction=scan_direction)

        # 🪙 Net-profit gate: if we're not net-positive, de-risk instead of chasing momentum.
        # (Uses the ecosystem-wide net profit metric when provided.)
        if self.net_profit_gate_enabled and net_profit is not None:
            try:
                np = float(net_profit)
            except Exception:
                np = None

            dyn_floor = max(self.penny_min_net, self.net_profit_floor)
            if self.net_profit_pct and portfolio_equity is not None:
                try:
                    eq = float(portfolio_equity)
                    if eq > 0:
                        dyn_floor = max(dyn_floor, eq * float(self.net_profit_pct))
                except Exception:
                    pass

            if np is not None and np < dyn_floor:
                # Bootstrap exception: allow early capital motion while flat (>=0).
                if not (self.bootstrap_enabled and np >= 0):
                    direction = "DOWN"
                    # If we're already in a stable, don't churn.
                    if from_asset in STABLES:
                        return None

        # Candidate targets must be convertible from the current asset on that exchange
        candidates = self._candidate_targets(exchange, from_asset, convertible)
        if not candidates:
            # If we can't convert directly from this asset, try going to stable as an intermediate
            # (stage keeps it as a suggestion only)
            candidates = [s for s in STABLES if s != from_asset]

        # Use mycelium memory to bias the candidate list if possible
        try:
            if self.mycelium and hasattr(self.mycelium, "rank_symbols_by_memory"):
                # Convert assets -> synthetic symbols for ranking (assetUSDT)
                sym_list = [f"{a}USDT" for a in candidates]
                ranked = self.mycelium.rank_symbols_by_memory(sym_list)
                # Map back to assets
                ranked_assets = [s.replace("USDT", "") for s in ranked]
                # Keep order but only assets we still have
                ordered = [a for a in ranked_assets if a in candidates]
                if ordered:
                    candidates = ordered
        except Exception:
            pass

        # Unity bias: if the main system has a preferred target universe (from opportunities),
        # prefer those assets when we are in risk-on mode.
        preferred_set = set()
        if preferred_assets:
            try:
                preferred_set = {str(a).upper() for a in preferred_assets if a}
            except Exception:
                preferred_set = set()
        if preferred_set and direction == "UP":
            # Keep only candidates that are in the preferred universe if any match.
            inter = [c for c in candidates if c in preferred_set]
            if inter:
                candidates = inter

        to_asset = self._choose_target(direction=direction, from_asset=from_asset, candidates=candidates, ticker_cache=ticker_cache)
        if not to_asset:
            return None

        amount = qty * self.fraction
        if amount <= 0:
            return None

        # Ensure the rotated fraction is meaningful (not just the whole holding).
        if (value_usd * self.fraction) < self.min_value_usd:
            return None

        # Find path (optional informational)
        path = None
        try:
            if hasattr(self.client, "find_conversion_path"):
                path = self.client.find_conversion_path(exchange, from_asset, to_asset)
        except Exception:
            path = None

        decision = LadderDecision(
            ts=now,
            mode=self.mode,
            direction=direction,
            exchange=str(exchange),
            from_asset=from_asset,
            to_asset=to_asset,
            amount=float(amount),
            reason=(
                f"mycelium_direction={direction} source_value_usd≈{value_usd:.2f} "
                f"fraction={self.fraction:.2f} net_profit={net_profit if net_profit is not None else 'n/a'}"
            ),
            path=path,
        )

        payload = {
            'ts': decision.ts,
            'mode': decision.mode,
            'direction': decision.direction,
            'exchange': decision.exchange,
            'from': decision.from_asset,
            'to': decision.to_asset,
            'amount': decision.amount,
            'reason': decision.reason,
            'net_profit': float(net_profit) if net_profit is not None else None,
            'path_len': len(path) if isinstance(path, list) else 0,
        }
        self._emit('decision', payload)

        # Tell the Mycelium which way we're moving, using its native link vocabulary.
        self._emit_to_mycelium_link('ladder.decision', {
            'timestamp': decision.ts,
            'exchange': decision.exchange,
            'from_asset': decision.from_asset,
            'to_asset': decision.to_asset,
            'direction': decision.direction,
            'amount': decision.amount,
            'mode': decision.mode,
            'reason': decision.reason,
            'net_profit': float(net_profit) if net_profit is not None else None,
        })

        # Seed Mycelium activations so the network can "feel" the rotation direction.
        try:
            if self.mycelium and hasattr(self.mycelium, 'add_signal'):
                # Bias toward target when climbing, bias away when de-risking.
                if decision.direction in ("UP", "RIGHT"):
                    s = 0.62
                elif decision.direction in ("DOWN", "LEFT"):
                    s = 0.38
                else:
                    s = 0.55
                self.mycelium.add_signal(f"{decision.to_asset}USDT", float(s))
        except Exception:
            pass

        if self.mode == "execute":
            if not (isinstance(path, list) and len(path) > 0):
                decision.result = {'skipped': 'no conversion path'}
                self._emit('executed', {**payload, 'result': decision.result})
                self._emit_to_mycelium_link('ladder.executed', {
                    'timestamp': decision.ts,
                    'exchange': decision.exchange,
                    'from_asset': decision.from_asset,
                    'to_asset': decision.to_asset,
                    'direction': decision.direction,
                    'amount': decision.amount,
                    'mode': decision.mode,
                    'result': decision.result,
                })
                self._last_action_ts = now
                self._last_decision = decision
                return decision

            # Safety: do not execute if exchange client is in dry_run
            dry_run = False
            try:
                if hasattr(self.client, 'clients') and decision.exchange in getattr(self.client, 'clients', {}):
                    ex_client = self.client.clients[decision.exchange]
                    dry_run = bool(getattr(ex_client, 'dry_run', False))
                else:
                    dry_run = bool(getattr(self.client, 'dry_run', False))
            except Exception:
                dry_run = True

            if dry_run:
                decision.result = {'dry_run': True, 'skipped': 'exchange client in dry_run'}
            else:
                # === CALCULATE INPUT VALUE FOR PROFIT TRACKING ===
                input_value_usd = 0.0
                try:
                    if self.client and hasattr(self.client, "convert_to_quote"):
                        input_value_usd = float(self.client.convert_to_quote(
                            decision.exchange, decision.from_asset, decision.amount, "USDT"
                        ) or 0.0)
                except Exception:
                    input_value_usd = value_usd * self.fraction if value_usd else 0.0
                
                try:
                    decision.result = self.client.convert_crypto(decision.exchange, decision.from_asset, decision.to_asset, decision.amount)
                    
                    # === CALCULATE NET PROFIT AND RECORD TO MYCELIUM ===
                    if decision.result and not decision.result.get('error'):
                        output_value_usd = 0.0
                        output_amount = 0.0
                        fees = 0.0
                        
                        # Extract output from result
                        if 'orders' in decision.result:
                            # Multi-hop conversion
                            orders = decision.result.get('orders', [])
                            if orders:
                                last_order = orders[-1]
                                output_amount = float(last_order.get('executedQty', 0) or 
                                                      last_order.get('cummulativeQuoteQty', 0) or 0)
                        elif 'sell' in decision.result and 'buy' in decision.result:
                            # Two-step conversion
                            buy_order = decision.result.get('buy', {})
                            output_amount = float(buy_order.get('executedQty', 0) or 0)
                        elif 'direct' in decision.result:
                            # Direct conversion
                            direct_order = decision.result.get('direct', {})
                            output_amount = float(direct_order.get('executedQty', 0) or 0)
                        
                        # Get output value in USD
                        if output_amount > 0:
                            try:
                                if self.client and hasattr(self.client, "convert_to_quote"):
                                    output_value_usd = float(self.client.convert_to_quote(
                                        decision.exchange, decision.to_asset, output_amount, "USDT"
                                    ) or 0.0)
                            except Exception:
                                pass
                            
                            # For stables, use face value
                            if output_value_usd == 0 and decision.to_asset in STABLES:
                                output_value_usd = output_amount
                        
                        # Estimate fees (typically 0.1% per hop)
                        hops = decision.result.get('hops', len(path) if path else 1)
                        fees = input_value_usd * 0.001 * hops  # 0.1% per hop
                        
                        # Calculate net profit
                        net_profit = output_value_usd - input_value_usd
                        
                        # Record to Mycelium
                        if self.mycelium and hasattr(self.mycelium, 'record_conversion_profit'):
                            try:
                                self.mycelium.record_conversion_profit({
                                    'from_asset': decision.from_asset,
                                    'to_asset': decision.to_asset,
                                    'exchange': decision.exchange,
                                    'path': path,
                                    'input_amount': decision.amount,
                                    'output_amount': output_amount,
                                    'input_value_usd': input_value_usd,
                                    'output_value_usd': output_value_usd,
                                    'fees': fees,
                                    'net_profit': net_profit,
                                    'success': True,
                                    'hops': hops,
                                    'direction': decision.direction,
                                })
                            except Exception as e:
                                # Log but don't fail
                                pass
                        
                        # Add profit info to result
                        decision.result['net_profit'] = net_profit
                        decision.result['input_value_usd'] = input_value_usd
                        decision.result['output_value_usd'] = output_value_usd
                        decision.result['fees_estimated'] = fees
                    
                except Exception as e:
                    decision.result = {'error': str(e)}
                    
                    # Record failed conversion
                    if self.mycelium and hasattr(self.mycelium, 'record_conversion_profit'):
                        try:
                            self.mycelium.record_conversion_profit({
                                'from_asset': decision.from_asset,
                                'to_asset': decision.to_asset,
                                'exchange': decision.exchange,
                                'path': path,
                                'input_amount': decision.amount,
                                'output_amount': 0,
                                'input_value_usd': input_value_usd,
                                'output_value_usd': 0,
                                'fees': 0,
                                'net_profit': 0,
                                'success': False,
                                'hops': len(path) if path else 1,
                                'error': str(e),
                            })
                        except Exception:
                            pass

            self._emit('executed', {**payload, 'result': decision.result})
            self._emit_to_mycelium_link('ladder.executed', {
                'timestamp': decision.ts,
                'exchange': decision.exchange,
                'from_asset': decision.from_asset,
                'to_asset': decision.to_asset,
                'direction': decision.direction,
                'amount': decision.amount,
                'mode': decision.mode,
                'result': decision.result,
            })

        self._last_action_ts = now
        self._last_decision = decision
        return decision

    def last_decision(self) -> Optional[LadderDecision]:
        return self._last_decision
