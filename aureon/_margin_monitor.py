#!/usr/bin/env python3
"""
MARGIN POSITION MONITOR — No Stop Loss, Hold Until Profit
==========================================================
Monitors open margin positions and closes them ONLY when:
1. Price is above breakeven (entry + all fees)
2. Net P&L is confirmed positive
3. Profit is locked in

Philosophy: NO STOP LOSS. We hold with patience until profitable.
Only exceptions:
  — Margin liquidation risk (<110% margin level)
  — Dead Man's Switch floor hit (DTP)
  — 1-hour ride limit reached (rotate to next stallion)
"""
import os, sys, time, json, logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('margin_monitor')

# ══════════════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════════════
CHECK_INTERVAL   = 30       # Seconds between price checks
MIN_PROFIT_USD   = 0.001    # Minimum net profit in USD to trigger close
MIN_PROFIT_PCT   = 0.10     # Minimum % above breakeven to close (0.10%)
LIQUIDATION_WARN  = 120     # Margin level % warning threshold
LIQUIDATION_FORCE = 110     # Margin level % force-close threshold

# Top-10 Kraken margin pairs for shadow rides (the "herd")
CANDIDATE_PAIRS = [
    'XBTUSD', 'SOLUSD', 'XRPUSD', 'ADAUSD', 'DOTUSD',
    'LINKUSD', 'UNIUSD', 'AVAXUSD', 'MATICUSD', 'LTCUSD',
]

# ══════════════════════════════════════════════════════════════
#  DEAD MAN'S SWITCH IMPORT
# ══════════════════════════════════════════════════════════════
try:
    from dynamic_take_profit import DynamicTakeProfit, DTP_CONFIG
    _DTP_AVAILABLE = True
except ImportError:
    _DTP_AVAILABLE = False
    DynamicTakeProfit = None
    DTP_CONFIG = {'activation_threshold': 15.0, 'trailing_distance_pct': 0.02, 'gbp_usd_rate': 1.27}

# ══════════════════════════════════════════════════════════════
#  MARGIN WAVE RIDER IMPORT
# ══════════════════════════════════════════════════════════════
try:
    from margin_wave_rider import MarginWaveRider, WAVE_CONFIG
    _WAVE_RIDER_AVAILABLE = True
    _wave_rider = MarginWaveRider()
except ImportError:
    _WAVE_RIDER_AVAILABLE = False
    _wave_rider = None
    WAVE_CONFIG = {'entry_min_margin_pct': 250.0, 'danger_margin_pct': 110.0}

# ══════════════════════════════════════════════════════════════
#  STALLION TRACKER IMPORT
# ══════════════════════════════════════════════════════════════
try:
    from stallion_tracker import classify_phase as _classify_phase
    _STALLION_AVAILABLE = True
except ImportError:
    _STALLION_AVAILABLE = False
    _classify_phase = None

# ══════════════════════════════════════════════════════════════
#  STALLION MULTIVERSE IMPORT
# ══════════════════════════════════════════════════════════════
try:
    from stallion_multiverse import StallionMultiverse, MULTIVERSE_CONFIG
    _MULTIVERSE_AVAILABLE = True
except ImportError:
    _MULTIVERSE_AVAILABLE = False
    StallionMultiverse = None
    MULTIVERSE_CONFIG = {'real_ride_limit_secs': 3600}

# ══════════════════════════════════════════════════════════════
#  MULTIVERSE LEARNING BRIDGE IMPORT
# ══════════════════════════════════════════════════════════════
try:
    from multiverse_learning_bridge import MultiverseLearningBridge
    _LEARNING_BRIDGE_AVAILABLE = True
except ImportError:
    _LEARNING_BRIDGE_AVAILABLE = False
    MultiverseLearningBridge = None


def main():
    from kraken_client import KrakenClient
    client = KrakenClient()

    assert not client.dry_run, "ERROR: Client is in dry-run mode!"

    ride_limit_mins = MULTIVERSE_CONFIG['real_ride_limit_secs'] // 60

    print("=" * 70)
    print("  MARGIN POSITION MONITOR")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Check interval: {CHECK_INTERVAL}s")
    print(f"  Min profit to close: ${MIN_PROFIT_USD} or {MIN_PROFIT_PCT}%")
    print(f"  Stop loss: NONE (patience mode)")
    print(f"  Wave Rider: entry gate {WAVE_CONFIG['entry_min_margin_pct']:.0f}% margin")
    print(f"  Ride limit: {ride_limit_mins} min then rotate to next stallion")
    print(f"  Shadow rides: up to {MULTIVERSE_CONFIG.get('max_shadows', 10)} candidates tracked")
    print("=" * 70)

    closed_positions = []
    cycle = 0

    # Dead Man's Switch trackers — persisted across cycles, keyed by position_id
    dtp_trackers: dict = {}

    # Stallion Multiverse — shadow rides on the top-10 herd
    _multiverse = StallionMultiverse() if _MULTIVERSE_AVAILABLE else None
    _multiverse_registered = False   # True once start_real_ride() called
    # Learning Bridge — wires multiverse learning into Seer, Lyra, ThoughtBus
    _learning_bridge = (
        MultiverseLearningBridge(_multiverse)
        if _LEARNING_BRIDGE_AVAILABLE and _multiverse is not None
        else None
    )

    while True:
        cycle += 1
        try:
            # ── Get open margin positions ───────────────────────────────────
            positions = client.get_open_margin_positions()

            if not positions:
                if closed_positions:
                    print(f"\n{'=' * 70}")
                    print(f"  ALL MARGIN POSITIONS CLOSED WITH PROFIT!")
                    print(f"  Closed {len(closed_positions)} positions:")
                    total_profit = 0
                    for cp in closed_positions:
                        print(f"    {cp['pair']}: ${cp['pnl']:+.4f}")
                        total_profit += cp['pnl']
                    print(f"  Total profit: ${total_profit:+.4f}")
                    print(f"{'=' * 70}")
                else:
                    print(f"\n  No open margin positions found. Nothing to monitor.")
                break

            # ── Get margin account health ───────────────────────────────────
            tb = client.get_trade_balance()
            margin_level = float(tb.get('margin_level', 0) or 0)
            free_margin  = float(tb.get('free_margin',  0) or 0)

            # ── Get ETH price ───────────────────────────────────────────────
            ticker      = client.get_ticker('ETHUSD')
            current_bid = float(ticker.get('bid', 0))
            current_ask = float(ticker.get('ask', 0))

            # ── Fetch candidate prices for multiverse shadow tracking ───────
            candidate_prices = {}
            if _multiverse is not None:
                for cpair in CANDIDATE_PAIRS:
                    try:
                        ct = client.get_ticker(cpair)
                        cp = float(ct.get('bid', 0) or 0)
                        if cp > 0:
                            candidate_prices[cpair] = cp
                    except Exception:
                        pass

            timestamp = datetime.now().strftime('%H:%M:%S')
            print(
                f"\n[{timestamp}] Cycle {cycle} | ETH: ${current_bid:,.2f} | "
                f"Margin Level: {margin_level:.0f}% | Free: ${free_margin:.2f}"
            )
            print(f"  {'─' * 60}")

            # ── Liquidation check — highest priority ────────────────────────
            if margin_level > 0 and margin_level < LIQUIDATION_FORCE:
                print(f"  CRITICAL: Margin level {margin_level:.1f}% < {LIQUIDATION_FORCE}%!")
                print(f"  Force closing ALL positions to prevent liquidation!")
                for pos in positions:
                    _force_close(client, pos, "LIQUIDATION_RISK")
                continue
            elif margin_level > 0 and margin_level < LIQUIDATION_WARN:
                print(f"  WARNING: Margin level {margin_level:.1f}% approaching danger zone")

            # ── Register the real ride with the multiverse (first cycle) ────
            if _multiverse is not None and not _multiverse_registered and positions:
                first_pos   = positions[0]
                real_opentm = float(first_pos.get('opentm', 0) or 0) or time.time()
                real_pair   = first_pos.get('pair', 'ETHUSD')
                _multiverse.start_real_ride(real_pair, real_opentm)
                mv_candidates = [
                    {'pair': p, 'volume': 0.01, 'leverage': 5}
                    for p in CANDIDATE_PAIRS
                    if p != real_pair
                ]
                _multiverse.set_candidates(mv_candidates, candidate_prices)
                _multiverse_registered = True

            # ── Update multiverse shadows with latest prices ────────────────
            if _multiverse is not None and candidate_prices:
                _multiverse.update(candidate_prices, margin_level)

            # ── Sync learning bridge → Seer, Lyra, ThoughtBus ──────────────
            if _learning_bridge is not None:
                try:
                    _learning_bridge.sync()
                except Exception as _lb_err:
                    logger.debug(f"Learning bridge sync skipped: {_lb_err}")

            # ── Monitor each position ───────────────────────────────────────
            for i, pos in enumerate(positions):
                pair          = pos.get('pair', '?')
                pos_type      = pos.get('type', '?')   # buy=long, sell=short
                volume        = float(pos.get('volume', 0))
                volume_closed = float(pos.get('volume_closed', 0))
                remaining     = volume - volume_closed
                cost          = float(pos.get('cost', 0))
                fee           = float(pos.get('fee', 0))
                leverage      = pos.get('leverage', '1')
                unrealized    = float(pos.get('unrealized_pnl', 0) or 0)
                margin_used   = float(pos.get('margin', 0))

                # Entry price and breakeven
                entry_price    = cost / volume if volume > 0 else 0
                exit_fee_est   = fee
                total_fees     = fee + exit_fee_est
                breakeven      = entry_price + (total_fees / remaining) if remaining > 0 else entry_price

                # P&L
                gross_pnl      = (current_bid - entry_price) * remaining
                net_pnl        = gross_pnl - total_fees
                pnl_pct        = (net_pnl / cost * 100) if cost > 0 else 0
                to_breakeven   = current_bid - breakeven
                to_breakeven_pct = (to_breakeven / breakeven * 100) if breakeven > 0 else 0

                # Status indicator
                if net_pnl > MIN_PROFIT_USD:
                    status = "PROFITABLE"
                    icon   = "+"
                elif current_bid >= entry_price:
                    status = "ABOVE ENTRY (fees not covered)"
                    icon   = "~"
                else:
                    underwater_pct = abs((current_bid / entry_price - 1) * 100)
                    status = f"UNDERWATER (-{underwater_pct:.2f}%)"
                    icon   = "-"

                lev_int = int(leverage) if str(leverage).isdigit() else 1

                # Wave capacity (how far price can fall before danger zone)
                wave_cap_str = ""
                if _WAVE_RIDER_AVAILABLE and _wave_rider and margin_level > 0:
                    wave_cap_val = _wave_rider.wave_capacity_pct(margin_level, lev_int)
                    wave_cap_str = f" | Wave cap: {wave_cap_val:.1f}% cushion"

                # ── Display position summary ────────────────────────────────
                print(f"  [{i}] {pair} LONG {remaining:.6f} ETH (lev={lev_int}x)")
                print(f"      Entry: ${entry_price:,.2f} | Breakeven: ${breakeven:,.2f} | Current: ${current_bid:,.2f}")
                print(f"      Gross PnL: ${gross_pnl:+.4f} | Fees: ${total_fees:.4f} | Net PnL: ${net_pnl:+.4f} ({pnl_pct:+.3f}%)")
                print(f"      To breakeven: ${to_breakeven:+.2f} ({to_breakeven_pct:+.3f}%){wave_cap_str}")
                print(f"      Status: [{icon}] {status}")

                # ════════════════════════════════════════════════════════════
                #  DEAD MAN'S SWITCH — feed net_pnl into DTP engine
                # ════════════════════════════════════════════════════════════
                dtp_close     = False
                dtp_reason_str = ""
                dtp_state_str  = ""
                # dtp_state is used below by the stallion classifier
                dtp_state      = None

                if _DTP_AVAILABLE and DynamicTakeProfit is not None:
                    pos_key = pos.get('position_id', pair)
                    if pos_key not in dtp_trackers:
                        dtp_trackers[pos_key] = DynamicTakeProfit(
                            activation_threshold_gbp = DTP_CONFIG['activation_threshold'],
                            gbp_usd_rate             = DTP_CONFIG['gbp_usd_rate'],
                            trailing_distance_pct    = DTP_CONFIG['trailing_distance_pct'],
                        )
                        print(
                            f"      [DTP] Dead Man's Switch armed: activates at "
                            f"£{DTP_CONFIG['activation_threshold']:.2f} net profit"
                        )
                    dtp = dtp_trackers[pos_key]
                    dtp_triggered, dtp_reason_str, dtp_state = dtp.update(net_pnl)
                    if dtp_state.activated:
                        dtp_state_str = (
                            f"  [DTP] floor=£{dtp_state.floor_gbp:.2f} "
                            f"peak=£{dtp_state.peak_profit_gbp:.2f} "
                            f"ratchets={dtp_state.trigger_count}"
                        )
                    if dtp_triggered:
                        dtp_close = True
                        print(f"      [DTP] DEAD MAN TRIGGERED: {dtp_reason_str}")

                if dtp_state_str:
                    print(f"      {dtp_state_str}")

                # ════════════════════════════════════════════════════════════
                #  STALLION PHASE — fresh classification using current DTP state
                # ════════════════════════════════════════════════════════════
                if _STALLION_AVAILABLE and _classify_phase is not None:
                    _open_ts   = float(pos.get('opentm', 0) or 0)
                    _hold_secs = (time.time() - _open_ts) if _open_ts > 0 else 0.0
                    _dtp_on    = dtp_state.activated      if dtp_state else False
                    _dtp_trig  = dtp_state.trigger_count  if dtp_state else 0
                    _dtp_floor = dtp_state.floor_gbp       if dtp_state else 0.0
                    _dtp_peak  = dtp_state.peak_profit_gbp if dtp_state else 0.0
                    try:
                        _snap = _classify_phase(
                            hold_seconds      = _hold_secs,
                            entry_price       = entry_price,
                            current_price     = current_bid,
                            net_pnl           = net_pnl,
                            trade_side        = pos_type if pos_type in ('buy', 'sell') else 'buy',
                            dtp_activated     = _dtp_on,
                            dtp_trigger_count = _dtp_trig,
                            dtp_floor_gbp     = _dtp_floor,
                            dtp_peak_gbp      = _dtp_peak,
                            margin_level      = margin_level,
                            leverage          = float(lev_int),
                        )
                        print(f"      [STALLION:{_snap.phase.value}] {_snap.description}")
                    except Exception:
                        pass

                # ════════════════════════════════════════════════════════════
                #  1-HOUR ROTATION CHECK
                # ════════════════════════════════════════════════════════════
                rotation_close = False
                if _multiverse is not None and _multiverse.is_rotation_due():
                    rotation_close = True
                    _next = _multiverse.get_next_stallion()
                    print(f"      [ROTATE] 1-hour ride limit reached!")
                    if _next:
                        print(f"      [ROTATE] Closing this ride — next stallion → {_next}")

                # ════════════════════════════════════════════════════════════
                #  CLOSE DECISION — priority: DTP > Rotation > Profit Target
                # ════════════════════════════════════════════════════════════
                should_close = False
                close_reason = ""

                if dtp_close:
                    if net_pnl >= 0:
                        should_close = True
                        close_reason = f"DTP_DEAD_MAN ({dtp_reason_str})"
                    else:
                        print(f"      [DTP] Triggered but net_pnl=${net_pnl:+.4f} < 0 — holding until profitable.")
                elif rotation_close:
                    if net_pnl >= MIN_PROFIT_USD:
                        should_close = True
                        _next = (_multiverse.get_next_stallion() or '?') if _multiverse else '?'
                        close_reason = f"ROTATION_DUE (1h limit | next→{_next})"
                    else:
                        # Underwater — reset rotation clock instead of closing at a loss
                        print(f"      [ROTATE] net_pnl=${net_pnl:+.4f} < target — holding, resetting rotation clock.")
                        if _multiverse is not None:
                            _multiverse.start_real_ride(pair, time.time())
                elif net_pnl >= MIN_PROFIT_USD and to_breakeven_pct >= MIN_PROFIT_PCT:
                    should_close = True
                    close_reason = f"PROFIT_TARGET (net=${net_pnl:+.4f}, {to_breakeven_pct:+.3f}% above breakeven)"

                if should_close:
                    print(f"      >>> CLOSING: {close_reason}")
                    try:
                        close_order = client.close_margin_position(
                            symbol   = 'ETHUSD',
                            side     = 'sell',   # sell to close LONG
                            volume   = remaining,
                            leverage = int(leverage) if str(leverage).isdigit() else None
                        )
                        close_txid   = close_order.get('orderId') or close_order.get('txid', 'UNKNOWN')
                        close_status = close_order.get('status', 'UNKNOWN')
                        print(f"      >>> CLOSED! Order ID: {close_txid} | Status: {close_status}")
                        print(f"      >>> Net Profit: ${net_pnl:+.4f}")
                        closed_positions.append({
                            'pair':        pair,
                            'entry_price': entry_price,
                            'exit_price':  current_bid,
                            'volume':      remaining,
                            'pnl':         net_pnl,
                            'order_id':    str(close_txid),
                            'reason':      close_reason,
                            'timestamp':   datetime.now().isoformat(),
                        })
                        # Advance multiverse to next stallion on rotation
                        if rotation_close and _multiverse is not None:
                            _next = _multiverse.get_next_stallion()
                            if _next:
                                _multiverse.start_real_ride(_next, time.time())
                                print(f"      [MULTIVERSE] Real ride advanced to {_next}")
                    except Exception as e:
                        print(f"      >>> CLOSE FAILED: {e}")
                else:
                    if net_pnl < 0:
                        needed = breakeven - current_bid
                        print(f"      HOLDING — Need ETH +${needed:.2f} to breakeven. Patience.")
                    else:
                        print(f"      HOLDING — Profitable but below {MIN_PROFIT_PCT}% threshold. Patience.")

            # ── Multiverse shadow status ────────────────────────────────────
            if _multiverse is not None:
                print()
                for mv_line in _multiverse.status_lines():
                    print(mv_line)

            # ── Learning bridge status (Seer / Lyra / conviction summary) ──
            if _learning_bridge is not None:
                for lb_line in _learning_bridge.learning_status_lines():
                    print(lb_line)

            # Sleep until next check
            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print(f"\n  Monitor stopped by user. Positions remain open.")
            break
        except Exception as e:
            logger.error(f"Monitor error: {e}", exc_info=True)
            time.sleep(CHECK_INTERVAL)

    # Save results
    if closed_positions:
        results = {
            'timestamp':         datetime.now().isoformat(),
            'positions_closed':  closed_positions,
            'total_profit':      sum(cp['pnl'] for cp in closed_positions),
        }
        with open('_margin_monitor_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to _margin_monitor_results.json")

    # Save multiverse learning data
    if _multiverse is not None:
        insights = _multiverse.learning_insights()
        if insights.get('shadows_analyzed', 0) > 0:
            with open('_multiverse_learning.json', 'w') as f:
                json.dump(insights, f, indent=2)
            print(
                f"Multiverse learning data saved: "
                f"{insights['shadows_analyzed']} shadows, "
                f"{insights['profitable_rate']:.0%} profitable"
            )


def _force_close(client, pos, reason):
    """Emergency close a margin position."""
    volume   = float(pos.get('volume', 0)) - float(pos.get('volume_closed', 0))
    leverage = pos.get('leverage', None)
    try:
        close_order = client.close_margin_position(
            symbol   = 'ETHUSD',
            side     = 'sell',
            volume   = volume,
            leverage = int(leverage) if leverage and str(leverage).isdigit() else None
        )
        print(f"  Force closed: {close_order.get('orderId', '?')} reason={reason}")
    except Exception as e:
        print(f"  Force close failed: {e}")


if __name__ == '__main__':
    main()
