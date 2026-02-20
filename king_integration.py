#!/usr/bin/env python3
"""
THE KING'S INTEGRATION - Wiring into the Aureon Ecosystem
=====================================================
"The King sees all. The King records all."

Bridges The King (Autonomous Accounting AI) into the full Aureon
trading ecosystem - connecting to exchanges, the Queen, the Enigma
systems, and all trading engines.

INTEGRATION MAP (mirrors aureon_enigma_integration.py):
─────────────────────────────────────────────────────────
  Exchange APIs     =>  Transaction Decoder (Sigma)
  CostBasisTracker  =>  Cost Basis Engine (Phi)
  TradeProfitValidator => P&L Calculator (Omega)
  Live Balances     =>  Portfolio Valuation (Gamma)
  Tax Configuration =>  Tax & Compliance (Psi)
  Queen Hive Mind   =>  Royal Decree (reports to Queen)
  Enigma System     =>  Intelligence Grades inform Health Grades
  Thought Bus       =>  King broadcasts financial events

Gary Leckey | February 2026
"The King and Queen rule the repo together."
"""

import os
import sys
import json
import time
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Lazy imports to avoid circular dependencies
_king = None
_ledger = None
_queen = None
_cost_basis_tracker = None
_validator = None


def _get_king():
    global _king
    if _king is None:
        from king_accounting import get_king
        _king = get_king()
    return _king


def _get_ledger():
    global _ledger
    if _ledger is None:
        from king_ledger import get_ledger
        _ledger = get_ledger()
    return _ledger


def _get_cost_basis_tracker():
    global _cost_basis_tracker
    if _cost_basis_tracker is None:
        try:
            from cost_basis_tracker import CostBasisTracker
            _cost_basis_tracker = CostBasisTracker()
        except ImportError:
            _cost_basis_tracker = None
    return _cost_basis_tracker


def _get_validator():
    global _validator
    if _validator is None:
        try:
            from trade_profit_validator import get_validator
            _validator = get_validator()
        except ImportError:
            _validator = None
    return _validator


# ═══════════════════════════════════════════════════════════════════════════
# TRADE HOOKS - Called by the trading ecosystem on every trade
# ═══════════════════════════════════════════════════════════════════════════

def king_on_buy(exchange: str, symbol: str, quantity: float, price: float,
                fee: float = 0.0, order_id: str = "",
                is_margin: bool = False, leverage: int = 1) -> Dict[str, Any]:
    """
    Hook called when a BUY order executes.
    Records the trade in the King's accounting system and double-entry ledger.
    """
    king = _get_king()
    ledger = _get_ledger()

    # Record in King's accounting engine
    result = king.ingest_trade(
        exchange, symbol, "buy", quantity, price,
        fee=fee, order_id=order_id,
        is_margin=is_margin, leverage=leverage,
    )

    # Record in double-entry ledger
    asset = symbol
    for q in ["USDT", "USDC", "USD", "GBP", "EUR", "BTC", "XBT", "ETH"]:
        if symbol.upper().endswith(q) and len(symbol) > len(q):
            asset = symbol[:-len(q)]
            break

    if is_margin:
        margin_amount = (quantity * price) / leverage if leverage > 1 else quantity * price
        ledger.record_margin_open(
            exchange, asset, quantity, price, leverage,
            margin_amount=margin_amount, fee=fee, order_id=order_id,
        )
    else:
        ledger.record_buy(exchange, asset, quantity, price, fee=fee, order_id=order_id)

    # Broadcast to ThoughtBus if available
    _broadcast_financial_event("BUY", {
        "exchange": exchange, "symbol": symbol, "quantity": quantity,
        "price": price, "fee": fee, "is_margin": is_margin,
    })

    return result


def king_on_sell(exchange: str, symbol: str, quantity: float, price: float,
                 fee: float = 0.0, order_id: str = "",
                 is_margin: bool = False, leverage: int = 1) -> Dict[str, Any]:
    """
    Hook called when a SELL order executes.
    Records the trade, calculates realized P&L, updates ledger.
    """
    king = _get_king()
    ledger = _get_ledger()

    # Record in King's accounting engine (handles FIFO cost basis)
    result = king.ingest_trade(
        exchange, symbol, "sell", quantity, price,
        fee=fee, order_id=order_id,
        is_margin=is_margin, leverage=leverage,
    )

    # Extract asset name
    asset = symbol
    for q in ["USDT", "USDC", "USD", "GBP", "EUR", "BTC", "XBT", "ETH"]:
        if symbol.upper().endswith(q) and len(symbol) > len(q):
            asset = symbol[:-len(q)]
            break

    # Get cost basis for ledger entry
    realized = result.get("realized_gain", {})
    cost_basis = realized.get("cost_basis", quantity * price)

    if is_margin:
        margin_amount = cost_basis / leverage if leverage > 1 else cost_basis
        borrowed = cost_basis - margin_amount
        ledger.record_margin_close(
            exchange, asset, quantity, price,
            cost_basis=cost_basis, margin_amount=margin_amount,
            borrowed=borrowed, fee=fee, order_id=order_id,
        )
    else:
        ledger.record_sell(
            exchange, asset, quantity, price,
            cost_basis=cost_basis, fee=fee, order_id=order_id,
        )

    # Broadcast
    pnl = realized.get("net", 0)
    _broadcast_financial_event("SELL", {
        "exchange": exchange, "symbol": symbol, "quantity": quantity,
        "price": price, "fee": fee, "pnl": pnl, "is_margin": is_margin,
    })

    return result


def king_on_deposit(exchange: str, asset: str, quantity: float) -> Dict[str, Any]:
    """Hook called when a deposit is detected."""
    king = _get_king()
    ledger = _get_ledger()

    result = king.ingest_deposit(exchange, asset, quantity)
    ledger.record_deposit(exchange, asset, quantity)

    _broadcast_financial_event("DEPOSIT", {
        "exchange": exchange, "asset": asset, "quantity": quantity,
    })
    return result


def king_on_withdrawal(exchange: str, asset: str, quantity: float,
                       fee: float = 0.0) -> Dict[str, Any]:
    """Hook called when a withdrawal is detected."""
    king = _get_king()
    ledger = _get_ledger()

    result = king.ingest_withdrawal(exchange, asset, quantity, fee=fee)
    ledger.record_withdrawal(exchange, asset, quantity, fee=fee)

    _broadcast_financial_event("WITHDRAWAL", {
        "exchange": exchange, "asset": asset, "quantity": quantity, "fee": fee,
    })
    return result


# ═══════════════════════════════════════════════════════════════════════════
# SYNC WITH EXISTING SYSTEMS
# ═══════════════════════════════════════════════════════════════════════════

def sync_king_from_cost_basis_tracker():
    """
    Import existing position data from CostBasisTracker into the King.
    This bootstraps the King's books from the existing tracking system.
    """
    king = _get_king()
    tracker = _get_cost_basis_tracker()

    if not tracker:
        logger.warning("CostBasisTracker not available for sync")
        return {"synced": 0}

    synced = 0
    try:
        # Load existing positions
        if hasattr(tracker, 'positions'):
            for key, pos_data in tracker.positions.items():
                if not isinstance(pos_data, dict):
                    continue
                exchange = pos_data.get("exchange", "unknown")
                symbol = pos_data.get("symbol", key)
                quantity = float(pos_data.get("total_quantity", 0))
                avg_price = float(pos_data.get("avg_entry_price", 0))
                total_cost = float(pos_data.get("total_cost", 0))
                total_fees = float(pos_data.get("total_fees", 0))

                if quantity > 0 and avg_price > 0:
                    king.ingest_trade(
                        exchange, symbol, "buy", quantity, avg_price,
                        fee=total_fees,
                        order_id=pos_data.get("last_order_id", ""),
                    )
                    synced += 1

        logger.info(f"King synced {synced} positions from CostBasisTracker")
    except Exception as e:
        logger.error(f"Error syncing King from CostBasisTracker: {e}")

    return {"synced": synced}


def sync_king_from_exchanges():
    """
    Pull trade history from exchanges and import into the King.
    This is a heavy operation - call sparingly.
    """
    king = _get_king()
    synced = 0

    # Sync from Kraken
    try:
        from kraken_client import get_kraken_client
        client = get_kraken_client()
        if client and not client.dry_run:
            # Get trade history from Kraken
            trades = client._private("/0/private/TradesHistory", {"type": "all"})
            if isinstance(trades, dict) and "trades" in trades:
                for txid, trade in trades["trades"].items():
                    pair = trade.get("pair", "")
                    side = trade.get("type", "")
                    vol = float(trade.get("vol", 0))
                    price = float(trade.get("price", 0))
                    fee = float(trade.get("fee", 0))
                    ts = float(trade.get("time", 0))
                    leverage = trade.get("leverage", "")

                    is_margin = leverage and leverage != "none" and leverage != ""

                    king.ingest_trade(
                        "kraken", pair, side, vol, price,
                        fee=fee, order_id=txid,
                        is_margin=bool(is_margin),
                        leverage=int(leverage.split(":")[0]) if is_margin and ":" in str(leverage) else 1,
                        timestamp=ts,
                    )
                    synced += 1
    except Exception as e:
        logger.error(f"Error syncing King from Kraken: {e}")

    logger.info(f"King synced {synced} trades from exchanges")
    return {"synced": synced}


# ═══════════════════════════════════════════════════════════════════════════
# RECONCILIATION
# ═══════════════════════════════════════════════════════════════════════════

def reconcile_all_exchanges() -> Dict[str, Any]:
    """Reconcile the King's books with all exchange balances."""
    king = _get_king()
    results = {}

    for exchange_name in ["kraken", "binance", "alpaca", "capital"]:
        try:
            from unified_exchange_client import UnifiedExchangeClient
            client = UnifiedExchangeClient(exchange_name)
            balances = client.get_all_balances()
            if balances:
                result = king.reconcile(exchange_name, balances)
                results[exchange_name] = result
        except Exception as e:
            results[exchange_name] = {"error": str(e)}

    return results


# ═══════════════════════════════════════════════════════════════════════════
# REPORTING
# ═══════════════════════════════════════════════════════════════════════════

def get_king_dashboard() -> Dict[str, Any]:
    """Get a comprehensive dashboard view from the King."""
    king = _get_king()
    ledger = _get_ledger()

    # Get current prices from exchanges
    current_prices = _fetch_current_prices()

    summary = king.get_financial_summary(current_prices)
    portfolio = king.get_portfolio_snapshot(current_prices)
    pnl_30d = king.get_pnl_report(days=30)
    audit = king.get_audit_report()

    # Ledger statements
    trial_balance = ledger.trial_balance()
    balance_sheet = ledger.balance_sheet()

    return {
        "timestamp": datetime.now().isoformat(),
        "royal_decree": summary.get("the_king_says", ""),
        "financial_summary": summary,
        "portfolio": portfolio,
        "pnl_30d": pnl_30d,
        "audit": audit,
        "trial_balance": trial_balance,
        "balance_sheet": balance_sheet,
    }


def print_king_report():
    """Print a full King report to stdout."""
    king = _get_king()
    ledger = _get_ledger()

    print("\n" + king.generate_daily_report())
    print("\n" + ledger.print_trial_balance())

    bs = ledger.balance_sheet()
    sym = "£" if king.base_currency == "GBP" else "$"

    print("\n" + "=" * 60)
    print("THE KING'S BALANCE SHEET")
    print("=" * 60)
    print(f"\nASSETS:")
    for name, val in bs.get("assets", {}).items():
        print(f"  {name:<30s} {sym}{val:>12.2f}")
    print(f"  {'TOTAL ASSETS':<30s} {sym}{bs['total_assets']:>12.2f}")
    print(f"\nLIABILITIES:")
    for name, val in bs.get("liabilities", {}).items():
        print(f"  {name:<30s} {sym}{val:>12.2f}")
    print(f"  {'TOTAL LIABILITIES':<30s} {sym}{bs['total_liabilities']:>12.2f}")
    print(f"\nEQUITY:")
    for name, val in bs.get("equity", {}).items():
        print(f"  {name:<30s} {sym}{val:>12.2f}")
    print(f"  {'Net Income':<30s} {sym}{bs['net_income']:>12.2f}")
    print(f"  {'TOTAL EQUITY':<30s} {sym}{bs['total_equity']:>12.2f}")
    balanced = "YES" if bs.get("accounting_equation_balanced") else "NO"
    print(f"\nA = L + E balanced: {balanced}")
    print("=" * 60)


# ═══════════════════════════════════════════════════════════════════════════
# AUTONOMOUS STARTUP
# ═══════════════════════════════════════════════════════════════════════════

def start_king():
    """
    Start the King's autonomous monitoring.
    Call this from the main trading engine startup.
    """
    king = _get_king()
    king.start_autonomous()
    logger.info("The King has risen. Long live the King!")
    return king


def stop_king():
    """Stop the King's autonomous monitoring."""
    king = _get_king()
    king.stop_autonomous()
    logger.info("The King rests.")


# ═══════════════════════════════════════════════════════════════════════════
# INTERNAL HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _fetch_current_prices() -> Dict[str, float]:
    """Fetch current prices from exchanges for portfolio valuation."""
    prices = {}
    try:
        from unified_exchange_client import UnifiedExchangeClient
        for exchange_name in ["kraken", "binance"]:
            try:
                client = UnifiedExchangeClient(exchange_name)
                tickers = client.get_24h_tickers()
                for t in tickers:
                    sym = t.get("symbol", "")
                    price = 0.0
                    if "lastPrice" in t:
                        try:
                            price = float(t["lastPrice"])
                        except (ValueError, TypeError):
                            pass
                    elif "price" in t:
                        try:
                            price = float(t["price"])
                        except (ValueError, TypeError):
                            pass
                    if price > 0 and sym:
                        # Map to "exchange:asset" format
                        for q in ["USDT", "USDC", "USD", "GBP", "EUR"]:
                            if sym.endswith(q) and len(sym) > len(q):
                                asset = sym[:-len(q)]
                                if asset == "XBT":
                                    asset = "BTC"
                                prices[f"{exchange_name}:{asset}"] = price
                                break
            except Exception:
                pass
    except ImportError:
        pass
    return prices


def _broadcast_financial_event(event_type: str, data: Dict):
    """Broadcast a financial event to the ThoughtBus if available."""
    try:
        from aureon_mind_thought_action_hub import ThoughtBus
        bus = ThoughtBus.get_instance() if hasattr(ThoughtBus, "get_instance") else None
        if bus and hasattr(bus, "emit"):
            bus.emit({
                "source": "TheKing",
                "event": f"KING_{event_type}",
                "data": data,
                "timestamp": time.time(),
            })
    except (ImportError, Exception):
        pass  # ThoughtBus not available, that's fine
