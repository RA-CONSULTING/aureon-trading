#!/usr/bin/env python3
"""Map the ENTIRE global financial market as one energy field."""
import sys, io, os, time, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import numpy as np
import requests
from aureon.harmonic.aureon_market_energy_field import MarketEnergyField

for l in open(os.path.join(os.path.dirname(__file__), '..', '..', '.env')):
    l = l.strip()
    if l and not l.startswith('#') and '=' in l:
        k, _, v = l.partition('=')
        os.environ.setdefault(k.strip(), v.strip())

print("GLOBAL ENERGY MAP — Every market that costs energy to move")
print("=" * 60)

field = MarketEnergyField()
total_mapped = 0

# 1. CRYPTO — Top 20
print("\n[CRYPTO] Top 20 by market cap...")
try:
    r = requests.get("https://api.coingecko.com/api/v3/coins/markets",
        params={"vs_currency": "usd", "order": "market_cap_desc", "per_page": 20,
                "page": 1, "sparkline": "true"}, timeout=15)
    if r.status_code == 200:
        for coin in r.json():
            sym = coin.get("symbol", "?").upper()
            sparkline = coin.get("sparkline_in_7d", {}).get("price", [])
            vol = coin.get("total_volume", 0)
            price = coin.get("current_price", 0)
            for i, p in enumerate(sparkline):
                field.ingest_price(sym, p, vol / max(1, len(sparkline)),
                                   time.time() - (len(sparkline) - i) * 3600)
            sig = field.compute_signature(sym)
            if sig:
                total_mapped += 1
                print(f"  {sym:6s} ${price:>10,.0f} f={sig.dominant_frequency_hz:.4f} "
                      f"{sig.energy_state:13s} bot={sig.bot_activity:.2f} "
                      f"whale={sig.whale_presence:.2f} phi={sig.phi_alignment:.2f}")
except Exception as e:
    print(f"  Crypto: {e}")

# 2. US STOCKS
print("\n[US STOCKS] Tech + Finance + Healthcare...")
try:
    import yfinance as yf
    tickers = ["SPY", "QQQ", "AAPL", "MSFT", "TSLA", "NVDA", "GOOGL", "AMZN",
               "META", "JPM", "V", "JNJ", "WMT", "PG", "UNH"]
    data = yf.download(tickers, period="7d", interval="1h", progress=False)
    for sym in tickers:
        try:
            prices = data["Close"][sym].dropna().values
            vols = data["Volume"][sym].dropna().values
            for i, p in enumerate(prices):
                v = float(vols[i]) if i < len(vols) else 0
                field.ingest_price(sym, float(p), v, time.time() - (len(prices) - i) * 3600)
            sig = field.compute_signature(sym)
            if sig:
                total_mapped += 1
                print(f"  {sym:6s} ${prices[-1]:>10,.2f} f={sig.dominant_frequency_hz:.4f} "
                      f"{sig.energy_state:13s} bot={sig.bot_activity:.2f} phi={sig.phi_alignment:.2f}")
        except Exception:
            pass
except Exception as e:
    print(f"  Stocks: {e}")

# 3. FOREX
print("\n[FOREX] Major + Emerging...")
try:
    fx = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X",
          "NZDUSD=X", "USDCHF=X", "EURGBP=X", "USDINR=X", "USDCNY=X"]
    data = yf.download(fx, period="7d", interval="1h", progress=False)
    for sym in fx:
        try:
            label = sym.replace("=X", "")
            prices = data["Close"][sym].dropna().values
            for i, p in enumerate(prices):
                field.ingest_price(label, float(p), 0, time.time() - (len(prices) - i) * 3600)
            sig = field.compute_signature(label)
            if sig:
                total_mapped += 1
                print(f"  {label:8s} {prices[-1]:>10.4f} f={sig.dominant_frequency_hz:.4f} "
                      f"{sig.energy_state:13s} bot={sig.bot_activity:.2f}")
        except Exception:
            pass
except Exception as e:
    print(f"  Forex: {e}")

# 4. COMMODITIES
print("\n[COMMODITIES] Metals + Energy + Agriculture...")
try:
    cmd = {"GC=F": "GOLD", "SI=F": "SILVER", "CL=F": "OIL", "NG=F": "NATGAS",
           "HG=F": "COPPER", "PL=F": "PLATINUM", "ZW=F": "WHEAT", "ZC=F": "CORN"}
    data = yf.download(list(cmd.keys()), period="7d", interval="1h", progress=False)
    for sym, label in cmd.items():
        try:
            prices = data["Close"][sym].dropna().values
            for i, p in enumerate(prices):
                field.ingest_price(label, float(p), 0, time.time() - (len(prices) - i) * 3600)
            sig = field.compute_signature(label)
            if sig:
                total_mapped += 1
                print(f"  {label:8s} ${prices[-1]:>10,.2f} f={sig.dominant_frequency_hz:.4f} "
                      f"{sig.energy_state:13s} bot={sig.bot_activity:.2f}")
        except Exception:
            pass
except Exception as e:
    print(f"  Commodities: {e}")

# 5. GLOBAL INDICES
print("\n[INDICES] Global markets...")
try:
    idx = {"^GSPC": "SP500", "^DJI": "DOW", "^IXIC": "NASDAQ", "^FTSE": "FTSE",
           "^N225": "NIKKEI", "^GDAXI": "DAX", "^HSI": "HANGSENG", "^BVSP": "BOVESPA"}
    data = yf.download(list(idx.keys()), period="7d", interval="1h", progress=False)
    for sym, label in idx.items():
        try:
            prices = data["Close"][sym].dropna().values
            for i, p in enumerate(prices):
                field.ingest_price(label, float(p), 0, time.time() - (len(prices) - i) * 3600)
            sig = field.compute_signature(label)
            if sig:
                total_mapped += 1
                print(f"  {label:8s} {prices[-1]:>10,.0f} f={sig.dominant_frequency_hz:.4f} "
                      f"{sig.energy_state:13s} bot={sig.bot_activity:.2f}")
        except Exception:
            pass
except Exception as e:
    print(f"  Indices: {e}")

# 6. ETFs (sector energy flows)
print("\n[ETFs] Sector energy flows...")
try:
    etfs = {"XLF": "FINANCE", "XLE": "ENERGY", "XLK": "TECH", "XLV": "HEALTH",
            "GLD": "GOLDETF", "TLT": "BONDS", "IWM": "SMALLCAP", "EEM": "EMERGING"}
    data = yf.download(list(etfs.keys()), period="7d", interval="1h", progress=False)
    for sym, label in etfs.items():
        try:
            prices = data["Close"][sym].dropna().values
            for i, p in enumerate(prices):
                field.ingest_price(label, float(p), 0, time.time() - (len(prices) - i) * 3600)
            sig = field.compute_signature(label)
            if sig:
                total_mapped += 1
                print(f"  {label:8s} ${prices[-1]:>10,.2f} f={sig.dominant_frequency_hz:.4f} "
                      f"{sig.energy_state:13s} bot={sig.bot_activity:.2f}")
        except Exception:
            pass
except Exception as e:
    print(f"  ETFs: {e}")

# COMPUTE FULL FIELD
state = field.compute_field()
n = len(state.instruments)
acc = sum(1 for s in state.instruments.values() if s.energy_state == "accumulating")
dist = sum(1 for s in state.instruments.values() if s.energy_state == "distributing")
neut = n - acc - dist

print(f"\n{'='*60}")
print(f"  GLOBAL ENERGY FIELD: {n} instruments mapped")
print(f"  Categories: Crypto + Stocks + Forex + Commodities + Indices + ETFs")
print(f"  Accumulating: {acc} | Distributing: {dist} | Neutral: {neut}")
print(f"  Total energy:  {state.total_energy:.4f}")
print(f"  Net flow:      {'INFLOW' if state.net_flow > 0 else 'OUTFLOW'}")
print(f"  Coherence:     {state.coherence:.3f}")
print(f"  Dominant freq: {state.dominant_frequency:.4f}")
print(f"  Extraction:    {'ACTIVE' if state.extraction_active else 'quiet'}")

# SIGNALS
signals = field.get_trading_signals()
print(f"\n  TRADING SIGNALS ({len(signals)}):")
for s in signals[:10]:
    print(f"    {s['action']:4s} {s['symbol']:8s} conf={s['confidence']:.2f} -- {s['reason']}")

# PHI-ALIGNED instruments
phi_aligned = [(sym, sig) for sym, sig in state.instruments.items() if sig.phi_alignment > 0.2]
if phi_aligned:
    print(f"\n  PHI-ALIGNED INSTRUMENTS ({len(phi_aligned)}):")
    for sym, sig in sorted(phi_aligned, key=lambda x: -x[1].phi_alignment):
        print(f"    {sym:8s} phi={sig.phi_alignment:.2f} f={sig.dominant_frequency_hz:.4f}")

print(f"{'='*60}")

# Save
json.dump({
    "instruments": n, "accumulating": acc, "distributing": dist, "neutral": neut,
    "total_energy": state.total_energy, "coherence": state.coherence,
    "signals": signals[:10], "phi_aligned": [(s, sig.phi_alignment) for s, sig in phi_aligned],
    "timestamp": time.time(),
}, open("state/global_energy_field.json", "w"), indent=2, default=str)
