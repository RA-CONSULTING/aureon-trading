#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                      ║
║     🔍 ORCA TRADING ACTIVITY VERIFICATION SCRIPT 🔍                                  ║
║     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                                ║
║                                                                                      ║
║     Proves that Orca Kill Cycle is actively trading by:                             ║
║       1. Checking execution logs for order IDs                                       ║
║       2. Querying exchange APIs for recent trades                                    ║
║       3. Cross-referencing order IDs between logs and exchanges                      ║
║       4. Showing dashboard snapshot state                                            ║
║                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os

# Windows UTF-8 fix
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        if hasattr(sys.stdout, 'buffer') and not sys.stdout.buffer.closed:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if hasattr(sys.stderr, 'buffer') and not sys.stderr.buffer.closed:
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional


def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_section(title: str):
    """Print a section divider."""
    print(f"\n{'─'*50}")
    print(f"  {title}")
    print(f"{'─'*50}")


def check_execution_logs() -> Dict[str, Any]:
    """Check execution logs for recent trades."""
    print_section("📝 EXECUTION LOGS")
    
    log_dir = Path(os.environ.get("AUREON_TRADE_LOG_DIR", "/tmp/aureon_trade_logs"))
    results = {
        "log_dir_exists": log_dir.exists(),
        "execution_files": [],
        "recent_executions": [],
        "order_ids": []
    }
    
    if not log_dir.exists():
        print(f"   ❌ Log directory not found: {log_dir}")
        # Try alternative locations
        alt_dirs = [
            Path("/tmp/aureon_trade_logs"),
            Path("./state"),
            Path("/app/state"),
            Path(os.path.expanduser("~/aureon_trade_logs"))
        ]
        for alt in alt_dirs:
            if alt.exists():
                log_dir = alt
                results["log_dir_exists"] = True
                print(f"   ✅ Found alternative log dir: {alt}")
                break
    
    if results["log_dir_exists"]:
        print(f"   📁 Log directory: {log_dir}")
        
        # Find execution files
        exec_files = sorted(log_dir.glob("executions_*.jsonl"), reverse=True)
        trade_files = sorted(log_dir.glob("trades_*.jsonl"), reverse=True)
        
        all_files = list(exec_files) + list(trade_files)
        results["execution_files"] = [str(f) for f in all_files[:5]]
        
        print(f"   📄 Execution files found: {len(exec_files)}")
        print(f"   📄 Trade files found: {len(trade_files)}")
        
        # Read recent executions
        for log_file in all_files[:3]:
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()[-50:]  # Last 50 entries
                    for line in reversed(lines):
                        try:
                            entry = json.loads(line.strip())
                            if entry.get("type") == "execution" or entry.get("order_id"):
                                results["recent_executions"].append(entry)
                                if entry.get("order_id"):
                                    results["order_ids"].append({
                                        "order_id": entry.get("order_id"),
                                        "exchange": entry.get("exchange"),
                                        "symbol": entry.get("symbol"),
                                        "side": entry.get("side"),
                                        "timestamp": entry.get("timestamp")
                                    })
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                print(f"   ⚠️ Error reading {log_file}: {e}")
        
        # Display recent executions
        if results["recent_executions"]:
            print(f"\n   🔥 RECENT EXECUTIONS ({len(results['recent_executions'])} found):")
            for exec in results["recent_executions"][:10]:
                exec_type = exec.get("execution_type", exec.get("side", "?")).upper()
                exchange = exec.get("exchange", "?")
                symbol = exec.get("symbol", "?")
                order_id = exec.get("order_id", "?")
                ts = exec.get("timestamp", "?")
                status = exec.get("status", "?")
                qty = exec.get("quantity", 0)
                price = exec.get("price", 0)
                
                order_short = (order_id[:15] + "...") if order_id and len(str(order_id)) > 15 else order_id
                print(f"      ✅ {exec_type} | {exchange.upper()} | {symbol} | OrderID: {order_short}")
                print(f"         Qty: {qty:.6f} | Price: ${price:.4f} | Status: {status} | Time: {ts}")
        else:
            print(f"   ⚠️ No executions found in logs")
    
    return results


def check_exchange_trades() -> Dict[str, Any]:
    """Query exchanges for recent trade history."""
    print_section("🏦 EXCHANGE TRADE HISTORY")
    
    results = {
        "kraken": {"available": False, "trades": []},
        "binance": {"available": False, "trades": []},
        "alpaca": {"available": False, "trades": []}
    }
    
    # Check Kraken
    try:
        from kraken_client import KrakenClient, get_kraken_client
        kraken = get_kraken_client()
        
        # Get recent trades
        trades = kraken.get_trades_history()
        if trades:
            results["kraken"]["available"] = True
            
            # Parse trades
            trade_list = []
            for txid, trade in trades.items():
                if isinstance(trade, dict):
                    trade_list.append({
                        "txid": txid,
                        "pair": trade.get("pair", "?"),
                        "type": trade.get("type", "?"),
                        "price": float(trade.get("price", 0)),
                        "vol": float(trade.get("vol", 0)),
                        "cost": float(trade.get("cost", 0)),
                        "fee": float(trade.get("fee", 0)),
                        "time": datetime.fromtimestamp(float(trade.get("time", 0))).isoformat()
                    })
            
            # Sort by time
            trade_list.sort(key=lambda x: x.get("time", ""), reverse=True)
            results["kraken"]["trades"] = trade_list[:20]
            
            print(f"   ✅ KRAKEN: {len(trade_list)} trades found")
            for t in trade_list[:5]:
                print(f"      📈 {t['type'].upper()} {t['pair']} | Vol: {t['vol']:.6f} | Price: ${t['price']:.4f} | TxID: {t['txid'][:12]}...")
                print(f"         Cost: ${t['cost']:.4f} | Fee: ${t['fee']:.6f} | Time: {t['time']}")
        else:
            print(f"   ⚠️ KRAKEN: No trades found or API error")
    except ImportError:
        print(f"   ❌ KRAKEN: Client not available")
    except Exception as e:
        print(f"   ❌ KRAKEN: Error - {e}")
    
    # Check Alpaca
    try:
        from alpaca_client import AlpacaClient
        alpaca = AlpacaClient()
        
        # Get recent orders
        orders = alpaca.get_all_orders(status="closed", limit=20)
        if orders:
            results["alpaca"]["available"] = True
            
            trade_list = []
            for order in orders:
                if isinstance(order, dict) and order.get("filled_qty"):
                    trade_list.append({
                        "order_id": order.get("id", "?"),
                        "symbol": order.get("symbol", "?"),
                        "side": order.get("side", "?"),
                        "qty": float(order.get("filled_qty", 0)),
                        "price": float(order.get("filled_avg_price", 0)),
                        "status": order.get("status", "?"),
                        "time": order.get("filled_at", order.get("created_at", "?"))
                    })
            
            results["alpaca"]["trades"] = trade_list
            
            print(f"   ✅ ALPACA: {len(trade_list)} filled orders found")
            for t in trade_list[:5]:
                print(f"      📈 {t['side'].upper()} {t['symbol']} | Qty: {t['qty']:.6f} | Price: ${t['price']:.4f}")
                print(f"         OrderID: {t['order_id'][:12]}... | Status: {t['status']} | Time: {t['time']}")
        else:
            print(f"   ⚠️ ALPACA: No filled orders found")
    except ImportError:
        print(f"   ❌ ALPACA: Client not available")
    except Exception as e:
        print(f"   ❌ ALPACA: Error - {e}")
    
    # Check Binance
    try:
        from binance_client import BinanceClient
        binance = BinanceClient()
        
        # Binance requires specific symbol for trade history
        # Try to get account info instead
        balances = binance.get_balances() if hasattr(binance, 'get_balances') else {}
        if balances:
            results["binance"]["available"] = True
            print(f"   ✅ BINANCE: Connected (balance check)")
            print(f"      Assets with balance: {list(balances.keys())[:5]}")
        else:
            print(f"   ⚠️ BINANCE: Connected but no balances")
    except ImportError:
        print(f"   ❌ BINANCE: Client not available")
    except Exception as e:
        print(f"   ❌ BINANCE: Error - {e}")
    
    return results


def check_dashboard_snapshot() -> Dict[str, Any]:
    """Check the Orca dashboard snapshot for active positions."""
    print_section("📊 DASHBOARD SNAPSHOT")
    
    state_dirs = [
        os.environ.get("AUREON_STATE_DIR", "state"),
        "state",
        "/app/state",
        "/tmp/aureon_state"
    ]
    
    results = {
        "snapshot_found": False,
        "positions": [],
        "closed_positions": [],
        "session_stats": {}
    }
    
    for state_dir in state_dirs:
        snapshot_file = Path(state_dir) / "dashboard_snapshot.json"
        if snapshot_file.exists():
            print(f"   📁 Found snapshot: {snapshot_file}")
            results["snapshot_found"] = True
            
            try:
                with open(snapshot_file, "r") as f:
                    data = json.load(f)
                
                # Active positions
                positions = data.get("positions", [])
                results["positions"] = positions
                
                print(f"\n   🎯 ACTIVE POSITIONS: {len(positions)}")
                for pos in positions:
                    symbol = pos.get("symbol", "?")
                    exchange = pos.get("exchange", "?")
                    entry_price = pos.get("entry_price", 0)
                    current_pnl = pos.get("current_pnl", 0)
                    pnl_emoji = "✅" if current_pnl >= 0 else "❌"
                    print(f"      {pnl_emoji} {symbol} ({exchange}) | Entry: ${entry_price:.4f} | P&L: ${current_pnl:+.4f}")
                
                # Closed positions
                closed = data.get("closed_positions", [])
                results["closed_positions"] = closed[-10:]  # Last 10
                
                print(f"\n   📜 CLOSED POSITIONS: {len(closed)}")
                for pos in closed[-5:]:
                    symbol = pos.get("symbol", "?")
                    pnl = pos.get("pnl", 0)
                    reason = pos.get("reason", "?")
                    pnl_emoji = "✅" if pnl >= 0 else "❌"
                    print(f"      {pnl_emoji} {symbol} | P&L: ${pnl:+.4f} | Reason: {reason}")
                
                # Session stats
                stats = data.get("session_stats", {})
                results["session_stats"] = stats
                
                print(f"\n   📈 SESSION STATS:")
                print(f"      Cycles: {stats.get('cycles', 0)}")
                print(f"      Total Trades: {stats.get('total_trades', 0)}")
                print(f"      Winning Trades: {stats.get('winning_trades', 0)}")
                print(f"      Total P&L: ${stats.get('total_pnl', 0):.4f}")
                print(f"      Active Count: {data.get('active_count', 0)}")
                
                # Timestamp
                ts = data.get("timestamp", 0)
                if ts:
                    age = time.time() - ts
                    print(f"\n   ⏱️ Snapshot age: {age:.1f}s ({datetime.fromtimestamp(ts).isoformat()})")
                
                break
                
            except Exception as e:
                print(f"   ⚠️ Error reading snapshot: {e}")
    
    if not results["snapshot_found"]:
        print(f"   ❌ No dashboard snapshot found")
        print(f"      Checked: {state_dirs}")
    
    return results


def cross_reference_orders(log_results: Dict, exchange_results: Dict) -> Dict[str, Any]:
    """Cross-reference order IDs between logs and exchanges."""
    print_section("🔗 ORDER ID CROSS-REFERENCE")
    
    results = {
        "matched": [],
        "unmatched_logs": [],
        "unmatched_exchange": []
    }
    
    log_order_ids = {o["order_id"]: o for o in log_results.get("order_ids", []) if o.get("order_id")}
    
    # Collect exchange order IDs
    exchange_order_ids = {}
    
    # Kraken uses txid
    for trade in exchange_results.get("kraken", {}).get("trades", []):
        txid = trade.get("txid")
        if txid:
            exchange_order_ids[txid] = {"exchange": "kraken", **trade}
    
    # Alpaca uses order_id
    for trade in exchange_results.get("alpaca", {}).get("trades", []):
        oid = trade.get("order_id")
        if oid:
            exchange_order_ids[oid] = {"exchange": "alpaca", **trade}
    
    # Find matches
    for order_id, log_data in log_order_ids.items():
        if order_id in exchange_order_ids:
            results["matched"].append({
                "order_id": order_id,
                "log_data": log_data,
                "exchange_data": exchange_order_ids[order_id]
            })
        else:
            results["unmatched_logs"].append(log_data)
    
    for order_id, exchange_data in exchange_order_ids.items():
        if order_id not in log_order_ids:
            results["unmatched_exchange"].append(exchange_data)
    
    # Display results
    print(f"\n   ✅ MATCHED ORDERS: {len(results['matched'])}")
    for match in results["matched"][:5]:
        oid = match["order_id"]
        log = match["log_data"]
        exch = match["exchange_data"]
        print(f"      🔗 {oid[:15]}...")
        print(f"         Log: {log.get('exchange')} {log.get('symbol')} {log.get('side')}")
        print(f"         Exchange: {exch.get('exchange')} confirmed")
    
    print(f"\n   ⚠️ UNMATCHED IN LOGS: {len(results['unmatched_logs'])}")
    for log in results["unmatched_logs"][:3]:
        print(f"      {log.get('order_id', '?')[:15]}... ({log.get('exchange')})")
    
    print(f"\n   ⚠️ UNMATCHED ON EXCHANGE: {len(results['unmatched_exchange'])}")
    for exch in results["unmatched_exchange"][:3]:
        oid = exch.get("txid") or exch.get("order_id", "?")
        print(f"      {oid[:15]}... ({exch.get('exchange')})")
    
    return results


def generate_proof_summary(all_results: Dict) -> None:
    """Generate a summary proving trading activity."""
    print_header("🏆 TRADING ACTIVITY PROOF SUMMARY")
    
    log_results = all_results.get("logs", {})
    exchange_results = all_results.get("exchanges", {})
    snapshot_results = all_results.get("snapshot", {})
    cross_ref = all_results.get("cross_reference", {})
    
    evidence = []
    
    # Evidence 1: Execution logs
    exec_count = len(log_results.get("recent_executions", []))
    if exec_count > 0:
        evidence.append(f"✅ {exec_count} executions logged with order IDs")
    else:
        evidence.append("❌ No executions in logs")
    
    # Evidence 2: Exchange trades
    kraken_trades = len(exchange_results.get("kraken", {}).get("trades", []))
    alpaca_trades = len(exchange_results.get("alpaca", {}).get("trades", []))
    if kraken_trades > 0:
        evidence.append(f"✅ {kraken_trades} trades confirmed on Kraken")
    if alpaca_trades > 0:
        evidence.append(f"✅ {alpaca_trades} orders confirmed on Alpaca")
    if kraken_trades == 0 and alpaca_trades == 0:
        evidence.append("⚠️ No trades found on exchanges (may need API keys)")
    
    # Evidence 3: Dashboard activity
    stats = snapshot_results.get("session_stats", {})
    total_trades = stats.get("total_trades", 0)
    cycles = stats.get("cycles", 0)
    if total_trades > 0:
        evidence.append(f"✅ {total_trades} trades in session ({cycles} cycles)")
    elif cycles > 0:
        evidence.append(f"⚠️ {cycles} cycles completed, {total_trades} trades")
    else:
        evidence.append("❌ No session activity in dashboard")
    
    # Evidence 4: Cross-reference
    matched = len(cross_ref.get("matched", []))
    if matched > 0:
        evidence.append(f"✅ {matched} order IDs verified on exchanges")
    
    # Evidence 5: Active positions
    positions = len(snapshot_results.get("positions", []))
    if positions > 0:
        evidence.append(f"✅ {positions} positions currently active")
    
    # Evidence 6: P&L
    total_pnl = stats.get("total_pnl", 0)
    if total_pnl != 0:
        emoji = "✅" if total_pnl > 0 else "⚠️"
        evidence.append(f"{emoji} Total P&L: ${total_pnl:+.4f}")
    
    print("\n   EVIDENCE OF TRADING ACTIVITY:")
    print("   " + "-" * 40)
    for e in evidence:
        print(f"   {e}")
    
    # Verdict
    positive_evidence = sum(1 for e in evidence if e.startswith("✅"))
    print("\n   " + "=" * 40)
    if positive_evidence >= 3:
        print("   🏆 VERDICT: TRADING ACTIVITY CONFIRMED!")
        print(f"      {positive_evidence} pieces of evidence support active trading")
    elif positive_evidence >= 1:
        print("   ⚠️ VERDICT: PARTIAL TRADING ACTIVITY")
        print(f"      {positive_evidence} pieces of evidence found")
        print("      Check if Orca is running and API keys are configured")
    else:
        print("   ❌ VERDICT: NO TRADING ACTIVITY DETECTED")
        print("      Ensure Orca Kill Cycle is running")
        print("      Check API key configuration")
    print("   " + "=" * 40)


def main():
    """Main verification routine."""
    print("\n" + "🦈" * 35)
    print("   ORCA KILL CYCLE - TRADING ACTIVITY VERIFICATION")
    print("🦈" * 35)
    print(f"\n   Timestamp: {datetime.now().isoformat()}")
    
    all_results = {}
    
    # 1. Check execution logs
    all_results["logs"] = check_execution_logs()
    
    # 2. Check exchange trade history
    all_results["exchanges"] = check_exchange_trades()
    
    # 3. Check dashboard snapshot
    all_results["snapshot"] = check_dashboard_snapshot()
    
    # 4. Cross-reference orders
    all_results["cross_reference"] = cross_reference_orders(
        all_results["logs"],
        all_results["exchanges"]
    )
    
    # 5. Generate summary
    generate_proof_summary(all_results)
    
    # Save results
    output_file = Path("trading_verification_report.json")
    try:
        with open(output_file, "w") as f:
            json.dump(all_results, f, indent=2, default=str)
        print(f"\n   📄 Full report saved to: {output_file}")
    except Exception as e:
        print(f"\n   ⚠️ Could not save report: {e}")
    
    print("\n" + "🦈" * 35 + "\n")
    
    return all_results


if __name__ == "__main__":
    main()
