
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Capital.com stock snapshot cache feeder.

Purpose:
- Offload stock market-data “heavy lifting” to Capital.com.
- Persist a small local JSON cache for other processes to consume.

Default behavior is safe: this script does nothing unless Capital credentials exist.

Environment:
- CAPITAL_API_KEY / CAPITAL_IDENTIFIER / CAPITAL_PASSWORD (required)
- CAPITAL_DEMO=1 (optional)
- CAPITAL_MAX_TICKER_SNAPSHOTS (optional; defaults inside CapitalClient)

Output schema:
{
  "generated_at": <unix_seconds>,
  "source": "capital.get_24h_tickers",
  "tickers": {
	"AAPL": {"price":..., "bid":..., "ask":..., "change_pct":..., "epic":...},
	...
  }
}

Notes:
- Best-effort and designed to be lightweight.
"""

import sys
import os

# Windows UTF-8 Fix
if sys.platform == 'win32':
	os.environ['PYTHONIOENCODING'] = 'utf-8'
	try:
		import io

		def _is_utf8_wrapper(stream):
			return (
				isinstance(stream, io.TextIOWrapper)
				and hasattr(stream, 'encoding')
				and stream.encoding
				and stream.encoding.lower().replace('-', '') == 'utf8'
			)

		if hasattr(sys.stdout, 'buffer') and not _is_utf8_wrapper(sys.stdout):
			sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
		if hasattr(sys.stderr, 'buffer') and not _is_utf8_wrapper(sys.stderr):
			sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
	except Exception:
		pass

import argparse
import json
import time
from typing import Any, Dict

from capital_client import CapitalClient


def _atomic_write_json(path: str, data: Dict[str, Any]) -> None:
	tmp = f"{path}.tmp"
	os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
	with open(tmp, 'w', encoding='utf-8') as f:
		json.dump(data, f, ensure_ascii=False)
	os.replace(tmp, path)


def _build_ticker_map(tickers) -> Dict[str, Dict[str, Any]]:
	out: Dict[str, Dict[str, Any]] = {}
	for t in tickers or []:
		ticker = (t.get('ticker') or '').strip().upper()
		if not ticker:
			continue
		out[ticker] = {
			'price': float(t.get('price', 0) or 0),
			'bid': float(t.get('bid', 0) or 0),
			'ask': float(t.get('ask', 0) or 0),
			'change_pct': float(t.get('priceChangePercent', 0) or 0),
			'epic': t.get('epic') or t.get('symbol') or '',
		}
	return out


def main() -> int:
	parser = argparse.ArgumentParser(description='Capital.com stock snapshot cache feeder')
	parser.add_argument('--out', default=os.getenv('CAPITAL_STOCK_CACHE_PATH', 'ws_cache/capital_stocks.json'))
	parser.add_argument('--interval-s', type=float, default=float(os.getenv('CAPITAL_STOCK_CACHE_INTERVAL_S', '15')))
	parser.add_argument('--once', action='store_true', help='Write cache once and exit')
	args = parser.parse_args()

	client = CapitalClient()
	if not getattr(client, 'enabled', False):
		print('CapitalClient disabled (missing/invalid credentials).')
		return 2

	while True:
		started = time.time()
		tickers = client.get_24h_tickers()
		ticker_map = _build_ticker_map(tickers)

		payload = {
			'generated_at': time.time(),
			'source': 'capital.get_24h_tickers',
			'count': len(ticker_map),
			'tickers': ticker_map,
		}
		_atomic_write_json(args.out, payload)

		took = time.time() - started
		print(f"Wrote {len(ticker_map)} Capital tickers to {args.out} in {took:.2f}s")

		if args.once:
			return 0

		sleep_for = max(0.5, args.interval_s - took)
		time.sleep(sleep_for)


if __name__ == '__main__':
	raise SystemExit(main())

