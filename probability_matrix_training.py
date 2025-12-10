#!/usr/bin/env python3
"""
Probability Matrix Training Runner
- Runs fast momentum-based sims using Kraken tickers
- Aggregates per-symbol win rates/PNL
- Emits probability reports consumed by UnifiedStateAggregator
"""
import json
import random
import sys
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List
from pathlib import Path

sys.path.insert(0, '/workspaces/aureon-trading')
from kraken_client import KrakenClient

# Strategy constants aligned with aureon_51_sim
KRAKEN_FEE = 0.0026
ROUND_TRIP_FEE = 0.0052
TAKE_PROFIT_PCT = 2.0
STOP_LOSS_PCT = 0.8
POSITION_SIZE = 100.0
MOMENTUM_THRESHOLD = 5.0
MIN_VOLUME = 5000

@dataclass
class SymbolStats:
    symbol: str
    trades: int = 0
    wins: int = 0
    losses: int = 0
    gross_pnl: float = 0.0
    fees: float = 0.0
    net_pnl: float = 0.0
    win_net_sum: float = 0.0
    loss_net_sum: float = 0.0

    def record(self, net: float, gross: float, fee: float, is_win: bool) -> None:
        self.trades += 1
        if is_win:
            self.wins += 1
            self.win_net_sum += net
        else:
            self.losses += 1
            self.loss_net_sum += net
        self.gross_pnl += gross
        self.fees += fee
        self.net_pnl += net

    def to_entry(self, run_id: str, ts: str) -> Dict:
        win_rate = self.wins / self.trades if self.trades else 0.0
        avg_win = self.win_net_sum / self.wins if self.wins else 0.0
        avg_loss = self.loss_net_sum / self.losses if self.losses else 0.0
        return {
            'symbol': self.symbol,
            'probability': win_rate,
            'win_rate': win_rate,
            'trades': self.trades,
            'wins': self.wins,
            'losses': self.losses,
            'gross_pnl': self.gross_pnl,
            'fees': self.fees,
            'net_pnl': self.net_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'source': 'probability_matrix_training',
            'run_id': run_id,
            'timestamp': ts,
        }


def fetch_momentum_pairs(client: KrakenClient) -> List[Dict]:
    tickers = client.get_24h_tickers()
    pairs = []
    for t in tickers:
        symbol = t.get('symbol', '')
        if not symbol.endswith('USD'):
            continue
        if symbol in ['USDCUSD', 'USDTUSD', 'EURUSD', 'GBPUSD']:
            continue
        price = float(t.get('lastPrice', 0) or 0)
        change = float(t.get('priceChangePercent', 0) or 0)
        volume = float(t.get('quoteVolume', 0) or 0)
        if price > 0.00001 and change > MOMENTUM_THRESHOLD and volume > MIN_VOLUME:
            pairs.append({'symbol': symbol, 'price': price, 'momentum': change, 'volume': volume})
    pairs.sort(key=lambda x: x['momentum'], reverse=True)
    return pairs


def simulate_training(trades_per_run: int = 200) -> Dict[str, SymbolStats]:
    client = KrakenClient()
    momentum_pairs = fetch_momentum_pairs(client)
    if not momentum_pairs:
        raise RuntimeError('No momentum pairs available for training')
    stats: Dict[str, SymbolStats] = {}
    for _ in range(trades_per_run):
        pair = random.choice(momentum_pairs)
        sym = pair['symbol']
        entry_price = pair['price']
        momentum = pair['momentum']
        if momentum > 30:
            win_prob = 0.58
        elif momentum > 20:
            win_prob = 0.55
        elif momentum > 15:
            win_prob = 0.53
        elif momentum > 10:
            win_prob = 0.52
        else:
            win_prob = 0.51
        is_win = random.random() < win_prob
        if is_win:
            gross_pnl = POSITION_SIZE * (TAKE_PROFIT_PCT / 100)
        else:
            gross_pnl = -POSITION_SIZE * (STOP_LOSS_PCT / 100)
        entry_fee = POSITION_SIZE * KRAKEN_FEE
        exit_value = POSITION_SIZE + gross_pnl
        exit_fee = exit_value * KRAKEN_FEE
        total_fee = entry_fee + exit_fee
        net_pnl = gross_pnl - total_fee
        if sym not in stats:
            stats[sym] = SymbolStats(symbol=sym)
        stats[sym].record(net=net_pnl, gross=gross_pnl, fee=total_fee, is_win=is_win)
    return stats


def write_reports(entries: List[Dict], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    training_report = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'source': 'probability_matrix_training',
        'data': entries,
    }
    with open(out_dir / 'probability_training_report.json', 'w') as f:
        json.dump(training_report, f, indent=2)

    prob_file = out_dir / 'probability_data.json'
    existing = {}
    if prob_file.exists():
        try:
            existing = json.loads(prob_file.read_text())
        except Exception:
            existing = {}
    if 'data_points' not in existing or not isinstance(existing.get('data_points'), list):
        existing['data_points'] = []
    existing['data_points'].extend(entries)
    existing['last_updated'] = datetime.now(timezone.utc).isoformat()
    with open(prob_file, 'w') as f:
        json.dump(existing, f, indent=2)


def main():
    trades_per_run = int(os.getenv('PROB_TRAIN_TRADES', '300'))
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
    stats = simulate_training(trades_per_run=trades_per_run)
    ts = datetime.now(timezone.utc).isoformat()
    entries = [s.to_entry(run_id=run_id, ts=ts) for s in stats.values() if s.trades >= 5]
    entries.sort(key=lambda x: x['probability'], reverse=True)
    out_dir = Path('/workspaces/aureon-trading')
    write_reports(entries, out_dir)
    print(f"📊 Probability training run {run_id} complete")
    print(f"   Symbols trained: {len(entries)}")
    if entries:
        top = entries[:5]
        print("   Top signals:")
        for e in top:
            print(f"      {e['symbol']}: p={e['probability']:.2f} trades={e['trades']} net={e['net_pnl']:+.2f}")


if __name__ == '__main__':
    main()
