#!/usr/bin/env python3
"""
CHECK GOAL PROOF
================
Reads margin_goal_proof.jsonl and proves whether the entry goal system
(goal_score) correctly identifies the fastest-to-profit signals.

Usage:
    python check_goal_proof.py              # Full report
    python check_goal_proof.py --tail 20   # Last N outcomes
    python check_goal_proof.py --live      # Watch file, print new entries
"""

import json
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

PROOF_FILE = "margin_goal_proof.jsonl"


def load_records(path: str = PROOF_FILE) -> list:
    records = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except FileNotFoundError:
        print(f"No proof file found: {path}")
        print("Run the trader first to generate data.")
    return records


def correlate(records: list) -> list:
    """Match scan + link + outcome records into unified trade rows."""
    scans    = {r["scan_id"]: r for r in records if r["type"] == "scan"}
    links    = {r["scan_id"]: r for r in records if r["type"] == "link"}
    outcomes = {r.get("order_id"): r for r in records if r["type"] == "outcome"}

    rows = []
    for r in records:
        if r["type"] != "outcome":
            continue
        scan_id  = r.get("scan_id", "unknown")
        scan     = scans.get(scan_id, {})
        rows.append({
            "timestamp":          r.get("timestamp"),
            "pair":               r.get("pair"),
            "side":               r.get("side"),
            "leverage":           r.get("leverage"),
            "net_pnl":            r.get("net_pnl"),
            "hold_minutes":       r.get("hold_minutes"),
            "close_reason":       r.get("close_reason"),
            "goal_score":         r.get("goal_score_selected"),
            "eta_predicted_min":  r.get("eta_predicted_min"),
            "goal_hit":           r.get("goal_hit"),
            "n_candidates":       r.get("n_candidates"),
            "scan_candidates":    r.get("scan_candidates") or scan.get("candidates", []),
        })
    return rows


def fmt_pnl(v):
    if v is None: return "     ?"
    return f"${v:+7.2f}"

def fmt_min(v):
    if v is None: return "   ?"
    return f"{v:5.1f}m"

def fmt_score(v):
    if v is None: return "  ?"
    return f"{v:.3f}"


def print_summary(rows: list, tail: int = None):
    if not rows:
        print("No completed trades in proof file yet.")
        return

    if tail:
        rows = rows[-tail:]

    # ── Header ───────────────────────────────────────────────────────────────
    print()
    print("=" * 100)
    print(" GOAL PROOF REPORT — entry goal_score vs actual trade outcome")
    print("=" * 100)
    print(f"{'Time':>20}  {'Pair':>10}  {'Side':>4}  {'Lev':>3}  "
          f"{'Net P&L':>8}  {'Hold':>6}  {'ETA pred':>8}  {'Goal':>5}  "
          f"{'Hit?':>5}  {'Close Reason'}")
    print("-" * 100)

    wins = losses = goal_hits = goal_misses = 0
    total_pnl = 0.0
    goal_scores_win  = []
    goal_scores_loss = []
    hold_win_min     = []
    hold_loss_min    = []

    for r in rows:
        pnl   = r["net_pnl"]
        hold  = r["hold_minutes"]
        score = r["goal_score"]
        hit   = r["goal_hit"]
        eta   = r["eta_predicted_min"]

        if pnl is not None:
            total_pnl += pnl
            if pnl >= 0:
                wins += 1
                if score is not None: goal_scores_win.append(score)
                if hold  is not None: hold_win_min.append(hold)
            else:
                losses += 1
                if score is not None: goal_scores_loss.append(score)
                if hold  is not None: hold_loss_min.append(hold)

        if hit is True:  goal_hits   += 1
        if hit is False: goal_misses += 1

        ts_str = (r["timestamp"] or "")[:19].replace("T", " ")
        hit_str = "✓" if hit else ("✗" if hit is False else "-")
        reason_short = (r["close_reason"] or "")[:30]

        print(
            f"{ts_str:>20}  {(r['pair'] or '?'):>10}  {(r['side'] or '?'):>4}  "
            f"{(r['leverage'] or 0):>3}x  {fmt_pnl(pnl):>8}  {fmt_min(hold):>6}  "
            f"{fmt_min(eta):>8}  {fmt_score(score):>5}  {hit_str:>5}  {reason_short}"
        )

    print("-" * 100)

    total = wins + losses
    wr    = wins / total * 100 if total else 0
    print(f"\n{'TOTALS':>20}  {'':>10}  {'':>4}  {'':>3}   {fmt_pnl(total_pnl):>8}"
          f"  Trades: {total}  Win%: {wr:.1f}%  GoalHit: {goal_hits}/{goal_hits+goal_misses}")

    # ── Goal-score correlation ───────────────────────────────────────────────
    print()
    print("─" * 60)
    print(" GOAL SCORE ANALYSIS")
    print("─" * 60)

    avg_score_win  = sum(goal_scores_win)  / len(goal_scores_win)  if goal_scores_win  else None
    avg_score_loss = sum(goal_scores_loss) / len(goal_scores_loss) if goal_scores_loss else None
    avg_hold_win   = sum(hold_win_min)  / len(hold_win_min)  if hold_win_min  else None
    avg_hold_loss  = sum(hold_loss_min) / len(hold_loss_min) if hold_loss_min else None

    print(f"  Winning trades  ({wins:>3}): avg goal_score = {fmt_score(avg_score_win)}  "
          f"avg hold = {fmt_min(avg_hold_win)}")
    print(f"  Losing  trades  ({losses:>3}): avg goal_score = {fmt_score(avg_score_loss)}  "
          f"avg hold = {fmt_min(avg_hold_loss)}")

    if avg_score_win and avg_score_loss:
        delta = avg_score_win - avg_score_loss
        verdict = "GOAL SCORE PREDICTS WINNERS ✓" if delta > 0 else "needs more data"
        print(f"\n  Δ goal_score (win−loss) = {delta:+.3f}  →  {verdict}")

    if avg_hold_win and avg_hold_loss:
        speed_ratio = avg_hold_win / avg_hold_loss if avg_hold_loss > 0 else None
        if speed_ratio:
            print(f"  Winning trades close {speed_ratio:.1f}× faster than losing trades")

    # ── Top rejected candidates (what was NOT chosen) ───────────────────────
    print()
    print("─" * 60)
    print(" SELECTION ACCURACY — top-2 candidates vs winner")
    print("─" * 60)
    print(f"  {'Rank':>4}  {'Pair':>10}  {'Goal':>5}  {'ETA pred':>8}  {'Selected':>8}")
    shown = 0
    for r in rows[-5:]:  # last 5 trades
        cands = r.get("scan_candidates") or []
        if not cands:
            continue
        print(f"\n  Trade: {r['pair']} {r['side']} — actual hold {fmt_min(r['hold_minutes'])}, "
              f"net {fmt_pnl(r['net_pnl'])}")
        for c in cands[:5]:
            sel = "◄ CHOSEN" if c.get("selected") else ""
            eta_str = fmt_min(c.get("eta_minutes"))
            print(f"  {c['rank']:>4}  {c['pair']:>10}  {fmt_score(c['goal_score']):>5}  "
                  f"{eta_str:>8}  {sel}")
        shown += 1
    if not shown:
        print("  (no scan_candidates data yet — will appear after first trade)")

    print()


def live_watch(path: str = PROOF_FILE):
    """Tail the proof file and print new outcome lines as they arrive."""
    print(f"Watching {path} for new trade outcomes… (Ctrl+C to stop)\n")
    seen = 0
    try:
        while True:
            records = load_records(path)
            outcomes = [r for r in records if r["type"] == "outcome"]
            if len(outcomes) > seen:
                for r in outcomes[seen:]:
                    pnl   = r.get("net_pnl")
                    hold  = r.get("hold_minutes")
                    score = r.get("goal_score_selected")
                    eta   = r.get("eta_predicted_min")
                    hit   = r.get("goal_hit")
                    ts    = (r.get("timestamp") or "")[:19].replace("T", " ")
                    hit_str = "GOAL HIT ✓" if hit else ("GOAL MISS ✗" if hit is False else "?")
                    print(
                        f"[{ts}] {r.get('pair')} {r.get('side')} {r.get('leverage')}x | "
                        f"net {fmt_pnl(pnl)} | hold {fmt_min(hold)} | "
                        f"eta_pred {fmt_min(eta)} | goal_score {fmt_score(score)} | {hit_str} | "
                        f"{r.get('close_reason','')}"
                    )
                seen = len(outcomes)
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nStopped.")


def main():
    parser = argparse.ArgumentParser(description="Check goal proof data")
    parser.add_argument("--tail", type=int, default=None, help="Show last N trades only")
    parser.add_argument("--live", action="store_true", help="Watch for new outcomes in real time")
    parser.add_argument("--file", default=PROOF_FILE, help=f"Proof file path (default: {PROOF_FILE})")
    args = parser.parse_args()

    if args.live:
        live_watch(args.file)
        return

    records = load_records(args.file)
    rows    = correlate(records)
    print_summary(rows, tail=args.tail)

    # Quick stats on scans even if no outcomes yet
    scans = [r for r in records if r["type"] == "scan"]
    if scans and not rows:
        print(f"  {len(scans)} scans recorded, no completed trades yet.")
        last = scans[-1]
        print(f"  Last scan: {last['timestamp']} — {last['n_candidates']} candidates, winner: "
              f"{last['winner_pair']} {last['winner_side']}")
        print()
        print(f"  {'Rank':>4}  {'Pair':>10}  {'Side':>4}  {'Lev':>3}  "
              f"{'Mom%':>6}  {'Need%':>6}  {'Goal':>5}  {'ETA':>6}  {'Score':>6}")
        for c in last.get("candidates", [])[:10]:
            sel = " ◄" if c.get("selected") else ""
            eta_str = f"{c['eta_minutes']:.0f}m" if c.get("eta_minutes") else "  ∞"
            print(
                f"  {c['rank']:>4}  {c['pair']:>10}  {c['side']:>4}  {c['leverage']:>3}x  "
                f"{c['momentum_pct']:>+6.2f}  {c['required_move_pct']:>6.3f}  "
                f"{c['goal_score']:>5.3f}  {eta_str:>6}  {c['total_score']:>6.3f}{sel}"
            )
        print()


if __name__ == "__main__":
    main()
