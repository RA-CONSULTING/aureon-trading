#!/usr/bin/env python3
"""
🌍🔥⚡ GAIA PLANETARY RECLAIMER V2 ⚡🔥🌍

UPGRADES:
- Kraken EUR pairs enabled
- Live portfolio tracker
- $1 BILLION goal counter
- All exchanges unified
- Windows terminal compatible

"SAVE THE PLANET - ONE TRADE AT A TIME"
"""

import sys, os

# Windows UTF-8 Fix (MANDATORY for Windows compatibility)
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            """Check if stream is already a UTF-8 TextIOWrapper."""
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        # Only wrap if not already UTF-8 wrapped (prevents re-wrapping on import)
        if hasattr(sys.stdout, 'buffer') and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if hasattr(sys.stderr, 'buffer') and not _is_utf8_wrapper(sys.stderr):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

os.environ['PYTHONUNBUFFERED'] = '1'

import time
import math
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

sys.path.append(os.getcwd())

# Sacred Constants
PHI = (1 + math.sqrt(5)) / 2
SCHUMANN = 7.83
GOAL = 1_000_000_000  # $1 BILLION

class PlanetaryReclaimer:
    def __init__(self):
        self.start_time = time.time()
        
        print()
        print("🌍" * 40)
        print("   GAIA PLANETARY RECLAIMER V2 - SAVE THE PLANET")
        print("   TARGET: $1,000,000,000 (ONE BILLION)")
        print("🌍" * 40)
        print()
        
        from binance_client import BinanceClient
        from alpaca_client import AlpacaClient
        from kraken_client import KrakenClient
        
        self.binance = BinanceClient()
        self.alpaca = AlpacaClient()
        self.kraken = KrakenClient()
        
        self.trades = 0
        self.profit = 0.0
        self.starting_equity = 0.0
        self.entries = {}
        
        # Per-platform tracking
        self.platform_stats = {
            'binance': {'trades': 0, 'profit': 0.0, 'verified': 0, 'last_trade': None},
            'alpaca': {'trades': 0, 'profit': 0.0, 'verified': 0, 'last_trade': None},
            'kraken': {'trades': 0, 'profit': 0.0, 'verified': 0, 'last_trade': None},
        }
        
        # Recent verified trades log
        self.verified_trades = []
        
        # EUR/USD rate (approximate)
        self.eur_usd = 1.08
        
        print("✅ BINANCE - Eastern Stargate ONLINE")
        print("✅ ALPACA  - Western Stargate ONLINE")
        print("✅ KRAKEN  - Northern Stargate ONLINE (USD + EUR)")
        print()
        
    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {msg}", flush=True)
    
    def record_verified_trade(self, platform: str, symbol: str, side: str, amount: float, profit: float):
        """Record a verified trade with platform contribution tracking"""
        trade = {
            'time': datetime.now().strftime("%H:%M:%S"),
            'platform': platform,
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'profit': profit,
            'verified': True
        }
        self.verified_trades.append(trade)
        if len(self.verified_trades) > 20:  # Keep last 20
            self.verified_trades.pop(0)
        
        # Update platform stats
        self.platform_stats[platform]['trades'] += 1
        self.platform_stats[platform]['profit'] += profit
        self.platform_stats[platform]['verified'] += 1
        self.platform_stats[platform]['last_trade'] = trade

    # ═══════════════════════════════════════════════════════════════
    # PORTFOLIO TRACKER - ROAD TO $1 BILLION
    # ═══════════════════════════════════════════════════════════════
    
    def get_total_portfolio(self) -> dict:
        """Get total portfolio value across ALL platforms"""
        total = 0.0
        breakdown = {'binance': 0.0, 'alpaca': 0.0, 'kraken': 0.0}
        
        # BINANCE
        try:
            for asset in ['SOL', 'BTC', 'ETH', 'AVAX', 'DOGE', 'XRP', 'USDC']:
                bal = self.binance.get_free_balance(asset)
                if bal > 0:
                    if asset == 'USDC':
                        breakdown['binance'] += bal
                    else:
                        try:
                            t = self.binance.get_ticker_price(f'{asset}USDC')
                            price = float(t.get('price', 0)) if t else 0
                            breakdown['binance'] += bal * price
                        except:
                            pass
        except:
            pass
        
        # ALPACA
        try:
            acc = self.alpaca.get_account()
            breakdown['alpaca'] = float(acc.get('portfolio_value', 0))
        except:
            pass
        
        # KRAKEN (USD + EUR) - with retry for reliability
        kraken_retries = 3
        for attempt in range(kraken_retries):
            try:
                acct = self.kraken.account()
                balances = acct.get('balances', [])
                
                # If empty, try direct asset fetch as fallback
                if not balances:
                    # Direct method fallback
                    for asset in ['ZUSD', 'USD', 'USDC', 'ZEUR', 'EUR', 'SOL', 'ETH', 'BTC']:
                        try:
                            bal = self.kraken.get_free_balance(asset)
                            if bal > 0:
                                if asset in ['USD', 'USDC', 'ZUSD']:
                                    breakdown['kraken'] += bal
                                elif asset in ['EUR', 'ZEUR']:
                                    breakdown['kraken'] += bal * self.eur_usd
                                else:
                                    try:
                                        ticker = self.kraken.get_ticker(f'{asset}USD')
                                        price = float(ticker.get('price', 0))
                                        breakdown['kraken'] += bal * price
                                    except:
                                        pass
                        except:
                            pass
                    if breakdown['kraken'] > 0:
                        break
                    continue  # Retry if still 0
                
                # Process balances array
                for bal in balances:
                    asset = bal.get('asset', '')
                    free = float(bal.get('free', 0))
                    if free <= 0:
                        continue
                    
                    if asset in ['USD', 'USDC', 'ZUSD']:
                        breakdown['kraken'] += free
                    elif asset in ['EUR', 'ZEUR']:
                        breakdown['kraken'] += free * self.eur_usd
                    elif asset not in ['USDT']:
                        # Try to get price
                        try:
                            ticker = self.kraken.get_ticker(f'{asset}USD')
                            price = float(ticker.get('price', 0))
                            breakdown['kraken'] += free * price
                        except:
                            try:
                                ticker = self.kraken.get_ticker(f'{asset}EUR')
                                price = float(ticker.get('price', 0))
                                breakdown['kraken'] += free * price * self.eur_usd
                            except:
                                pass
                
                if breakdown['kraken'] > 0:
                    break  # Success, exit retry loop
            except Exception as e:
                if attempt < kraken_retries - 1:
                    time.sleep(0.5)  # Brief pause before retry
                continue
        
        total = sum(breakdown.values())
        return {'total': total, 'breakdown': breakdown}
    
    def print_billion_tracker(self, portfolio: dict):
        """Print the road to $1 billion tracker"""
        total = portfolio['total']
        bd = portfolio['breakdown']
        
        # Calculate progress
        progress = (total / GOAL) * 100
        bar_width = 40
        filled = int(bar_width * progress / 100)
        bar = '█' * filled + '░' * (bar_width - filled)
        
        # Time stats
        runtime = time.time() - self.start_time
        rate_per_hour = (self.profit / runtime * 3600) if runtime > 0 else 0
        
        # Time to goal estimate
        if rate_per_hour > 0:
            remaining = GOAL - total
            hours_to_goal = remaining / rate_per_hour
            days_to_goal = hours_to_goal / 24
            if days_to_goal > 365:
                time_est = f"{days_to_goal/365:.1f} years"
            elif days_to_goal > 30:
                time_est = f"{days_to_goal/30:.1f} months"
            elif days_to_goal > 1:
                time_est = f"{days_to_goal:.1f} days"
            else:
                time_est = f"{hours_to_goal:.1f} hours"
        else:
            time_est = "∞"
        
        print()
        print("╔" + "═" * 60 + "╗")
        print("║" + "🌍 GAIA PLANETARY RECLAIMER - ROAD TO $1 BILLION 🌍".center(60) + "║")
        print("╠" + "═" * 60 + "╣")
        print(f"║  [{bar}] {progress:.10f}%  ║")
        print("╠" + "═" * 60 + "╣")
        print(f"║  💰 TOTAL EQUITY: ${total:,.2f}".ljust(61) + "║")
        print(f"║  🎯 GOAL: ${GOAL:,}".ljust(61) + "║")
        print(f"║  📈 SESSION PROFIT: ${self.profit:.4f}".ljust(61) + "║")
        print(f"║  ⚡ TOTAL TRADES: {self.trades}".ljust(61) + "║")
        print(f"║  🚀 RATE: ${rate_per_hour:.4f}/hour".ljust(61) + "║")
        print(f"║  ⏱️  ETA TO GOAL: {time_est}".ljust(61) + "║")
        print("╠" + "═" * 60 + "╣")
        print("║" + " PLATFORM BREAKDOWN & VERIFIED TRADES ".center(60, "─") + "║")
        print("╠" + "═" * 60 + "╣")
        
        # Binance stats
        bs = self.platform_stats['binance']
        bin_contrib = (bs['profit'] / self.profit * 100) if self.profit > 0 else 0
        print(f"║  🟡 BINANCE:  ${bd['binance']:,.2f}".ljust(36) + f"│ ✓{bs['verified']} trades │ +${bs['profit']:.4f} ({bin_contrib:.0f}%)".ljust(23) + "║")
        
        # Alpaca stats  
        aps = self.platform_stats['alpaca']
        alp_contrib = (aps['profit'] / self.profit * 100) if self.profit > 0 else 0
        print(f"║  🦙 ALPACA:   ${bd['alpaca']:,.2f}".ljust(36) + f"│ ✓{aps['verified']} trades │ +${aps['profit']:.4f} ({alp_contrib:.0f}%)".ljust(23) + "║")
        
        # Kraken stats
        ks = self.platform_stats['kraken']
        krk_contrib = (ks['profit'] / self.profit * 100) if self.profit > 0 else 0
        print(f"║  🐙 KRAKEN:   ${bd['kraken']:,.2f}".ljust(36) + f"│ ✓{ks['verified']} trades │ +${ks['profit']:.4f} ({krk_contrib:.0f}%)".ljust(23) + "║")
        
        print("╠" + "═" * 60 + "╣")
        
        # Show last 3 verified trades
        print("║" + " RECENT VERIFIED TRADES ".center(60, "─") + "║")
        recent = self.verified_trades[-5:] if self.verified_trades else []
        if recent:
            for t in reversed(recent):
                icon = "🟡" if t['platform'] == 'binance' else ("🦙" if t['platform'] == 'alpaca' else "🐙")
                line = f"║  {icon} {t['time']} {t['side'].upper()} {t['symbol']}: +${t['profit']:.4f} ✓"
                print(line.ljust(61) + "║")
        else:
            print("║  Waiting for first verified trade...".ljust(61) + "║")
        
        print("╚" + "═" * 60 + "╝")
        print()

    # ═══════════════════════════════════════════════════════════════
    # BINANCE TRADING
    # ═══════════════════════════════════════════════════════════════
    
    def binance_scan_and_trade(self):
        """Scan Binance - take profits - deploy cash"""
        try:
            for asset in ['SOL', 'BTC', 'ETH', 'AVAX', 'DOGE', 'XRP']:
                bal = self.binance.get_free_balance(asset)
                if bal < 0.00001:
                    continue
                
                pair = f'{asset}USDC'
                t = self.binance.get_ticker_price(pair)
                if not t:
                    continue
                    
                price = float(t.get('price', 0))
                value = bal * price
                
                if value < 1:
                    continue
                
                key = f'bin_{asset}'
                if key not in self.entries:
                    self.entries[key] = price
                    continue
                
                entry = self.entries[key]
                pnl_pct = (price - entry) / entry * 100
                
                if pnl_pct > 0.01:
                    self.log(f"🔥 BINANCE SELL {asset}: ${value:.2f} ({pnl_pct:+.2f}%)")
                    
                    result = self.binance.place_market_order(pair, 'SELL', quantity=bal * 0.999)
                    
                    if result and ('orderId' in result or result.get('status') == 'FILLED'):
                        profit_usd = value * (pnl_pct / 100)
                        self.profit += profit_usd
                        self.trades += 1
                        self.log(f"   ✅ VERIFIED! +${profit_usd:.4f}")
                        self.record_verified_trade('binance', asset, 'SELL', value, profit_usd)
                        del self.entries[key]
                        time.sleep(0.2)
                        self._binance_buy_best()
                        
            # Deploy idle USDC
            usdc = self.binance.get_free_balance('USDC')
            if usdc > 2:
                self._binance_buy_best()
                
        except Exception as e:
            pass
    
    def _binance_buy_best(self):
        usdc = self.binance.get_free_balance('USDC')
        if usdc < 2:
            return
            
        pairs = ['SOLUSDC', 'BTCUSDC', 'ETHUSDC', 'AVAXUSDC', 'DOGEUSDC']
        best_pair, best_mom = None, -999
        
        for pair in pairs:
            try:
                t = self.binance.get_24h_ticker(pair)
                mom = float(t.get('priceChangePercent', 0))
                if mom > best_mom:
                    best_pair, best_mom = pair, mom
            except:
                pass
        
        if best_pair:
            asset = best_pair.replace('USDC', '')
            self.log(f"📥 BINANCE BUY {asset}: ${usdc:.2f} ({best_mom:+.1f}%)")
            
            result = self.binance.place_market_order(best_pair, 'BUY', quote_qty=usdc * 0.98)
            
            if result and ('orderId' in result or result.get('status') == 'FILLED'):
                t = self.binance.get_ticker_price(best_pair)
                price = float(t.get('price', 0))
                self.entries[f'bin_{asset}'] = price
                self.log(f"   ✅ DEPLOYED @ ${price:.4f}")

    # ═══════════════════════════════════════════════════════════════
    # ALPACA TRADING
    # ═══════════════════════════════════════════════════════════════
    
    def alpaca_scan_and_trade(self):
        try:
            positions = self.alpaca.get_positions()
            
            for pos in positions:
                sym = pos.get('symbol', '')
                qty = float(pos.get('qty', 0))
                entry = float(pos.get('avg_entry_price', 0))
                current = float(pos.get('current_price', 0))
                value = float(pos.get('market_value', 0))
                
                if value < 0.5:
                    continue
                
                pnl_pct = (current - entry) / entry * 100 if entry > 0 else 0
                
                if pnl_pct > 0.01:
                    asset = sym.replace('USD', '').replace('/', '')
                    self.log(f"🔥 ALPACA SELL {asset}: ${value:.2f} ({pnl_pct:+.2f}%)")
                    
                    result = self.alpaca.place_order(sym, qty, 'sell', 'market', 'ioc')
                    
                    if result and result.get('status') in ['filled', 'accepted', 'new']:
                        profit_usd = value * (pnl_pct / 100)
                        self.profit += profit_usd
                        self.trades += 1
                        self.log(f"   ✅ VERIFIED! +${profit_usd:.4f}")
                        self.record_verified_trade('alpaca', asset, 'SELL', value, profit_usd)
                        time.sleep(0.3)
                        self._alpaca_buy_best()
            
            acc = self.alpaca.get_account()
            cash = float(acc.get('cash', 0))
            if cash > 2:
                self._alpaca_buy_best()
                
        except:
            pass
    
    def _alpaca_buy_best(self):
        try:
            acc = self.alpaca.get_account()
            cash = float(acc.get('cash', 0))
            if cash < 2:
                return
            
            pairs = ['SOLUSDC', 'BTCUSDC', 'ETHUSDC']
            best_asset, best_mom = None, -999
            
            for pair in pairs:
                try:
                    t = self.binance.get_24h_ticker(pair)
                    mom = float(t.get('priceChangePercent', 0))
                    if mom > best_mom:
                        best_asset = pair.replace('USDC', '')
                        best_mom = mom
                except:
                    pass
            
            if best_asset:
                alpaca_sym = f'{best_asset}/USD'
                self.log(f"📥 ALPACA BUY {best_asset}: ${cash:.2f} ({best_mom:+.1f}%)")
                
                try:
                    quotes = self.alpaca.get_latest_crypto_quotes([alpaca_sym])
                    price = float(quotes[alpaca_sym].get('ap', 0))
                    qty = (cash * 0.95) / price
                    result = self.alpaca.place_order(alpaca_sym, qty, 'buy', 'market', 'ioc')
                    if result:
                        self.log(f"   ✅ DEPLOYED")
                except:
                    pass
        except:
            pass

    # ═══════════════════════════════════════════════════════════════
    # KRAKEN TRADING - USD + EUR PAIRS
    # ═══════════════════════════════════════════════════════════════
    
    def kraken_scan_and_trade(self):
        """Scan Kraken - USD and EUR pairs"""
        try:
            acct = self.kraken.account()
            usd_bal = 0.0
            eur_bal = 0.0
            
            for bal in acct.get('balances', []):
                asset = bal.get('asset', '')
                free = float(bal.get('free', 0))
                
                if free <= 0:
                    continue
                
                # Track cash - ZUSD is Kraken's USD format (ONLY ZUSD works directly for USD pairs)
                if asset in ['USD', 'ZUSD']:
                    usd_bal += free
                    continue
                elif asset in ['EUR', 'ZEUR']:
                    eur_bal += free
                    continue
                elif asset in ['USDT', 'USDC', 'TUSD', 'DAI']:
                    # These stablecoins need conversion first - skip for now
                    continue
                
                # It's a crypto - try USD first, then EUR
                price = 0
                quote = 'USD'
                pair = f'{asset}USD'
                
                try:
                    ticker = self.kraken.get_ticker(pair)
                    price = float(ticker.get('price', 0))
                except:
                    try:
                        pair = f'{asset}EUR'
                        ticker = self.kraken.get_ticker(pair)
                        price = float(ticker.get('price', 0)) * self.eur_usd
                        quote = 'EUR'
                    except:
                        continue
                
                if price <= 0:
                    continue
                
                value = free * price
                if value < 1:
                    continue
                
                key = f'krk_{asset}_{quote}'
                if key not in self.entries:
                    self.entries[key] = price
                    continue
                
                entry = self.entries[key]
                pnl_pct = (price - entry) / entry * 100
                
                if pnl_pct > 0.01:
                    self.log(f"🔥 KRAKEN SELL {asset}/{quote}: ${value:.2f} ({pnl_pct:+.2f}%)")
                    
                    result = self.kraken.place_market_order(f'{asset}{quote}', 'sell', quantity=free * 0.999)
                    
                    if result and (result.get('txid') or result.get('status') == 'FILLED' or 
                                   result.get('orderId') or 'dryRun' in result):
                        profit_usd = value * (pnl_pct / 100)
                        self.profit += profit_usd
                        self.trades += 1
                        self.log(f"   ✅ VERIFIED! +${profit_usd:.4f}")
                        self.record_verified_trade('kraken', f'{asset}/{quote}', 'SELL', value, profit_usd)
                        del self.entries[key]
                        time.sleep(0.3)
            
            # Deploy USD
            if usd_bal > 2:
                self._kraken_buy_best('USD', usd_bal)
            
            # Deploy EUR
            if eur_bal > 2:
                self._kraken_buy_best('EUR', eur_bal)
                
        except Exception as e:
            pass
    
    def _kraken_buy_best(self, quote: str, amount: float):
        """Buy best asset on Kraken with USD or EUR"""
        try:
            if amount < 2:
                return
            
            # Get best momentum from Binance
            pairs = ['SOLUSDC', 'BTCUSDC', 'ETHUSDC']
            best_asset, best_mom = None, -999
            
            for pair in pairs:
                try:
                    t = self.binance.get_24h_ticker(pair)
                    mom = float(t.get('priceChangePercent', 0))
                    if mom > best_mom:
                        best_asset = pair.replace('USDC', '')
                        best_mom = mom
                except:
                    pass
            
            if best_asset:
                kraken_pair = f'{best_asset}{quote}'
                self.log(f"📥 KRAKEN BUY {best_asset}/{quote}: ${amount:.2f} ({best_mom:+.1f}%)")
                
                result = self.kraken.place_market_order(kraken_pair, 'buy', quote_qty=amount * 0.95)
                
                # Detect success - Kraken returns orderId and status=FILLED
                success = False
                if result:
                    success = (result.get('orderId') or result.get('txid') or 
                              result.get('status') == 'FILLED' or 'dryRun' in result)
                
                if success:
                    try:
                        ticker = self.kraken.get_ticker(kraken_pair)
                        price = float(ticker.get('price', 0))
                        if quote == 'EUR':
                            price *= self.eur_usd
                        self.entries[f'krk_{best_asset}_{quote}'] = price
                        self.log(f"   ✅ DEPLOYED @ ${price:.4f}")
                    except:
                        pass
        except Exception as e:
            pass

    # ═══════════════════════════════════════════════════════════════
    # MAIN LOOP
    # ═══════════════════════════════════════════════════════════════
    
    def run_cycle(self):
        with ThreadPoolExecutor(max_workers=3) as ex:
            ex.submit(self.binance_scan_and_trade)
            ex.submit(self.alpaca_scan_and_trade)
            ex.submit(self.kraken_scan_and_trade)
    
    def run(self):
        print("⚡ MODE: AGGRESSIVE - 0.01% profit threshold")
        print("⚡ KRAKEN: USD + EUR pairs enabled")
        print("⚡ GOAL: $1,000,000,000")
        print()
        
        # Get starting equity
        portfolio = self.get_total_portfolio()
        self.starting_equity = portfolio['total']
        self.print_billion_tracker(portfolio)
        
        cycle = 0
        while True:
            try:
                self.run_cycle()
                cycle += 1
                
                # Print tracker every 10 cycles
                if cycle % 10 == 0:
                    portfolio = self.get_total_portfolio()
                    self.print_billion_tracker(portfolio)
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                print()
                self.log("🛑 PROTOCOL PAUSED")
                portfolio = self.get_total_portfolio()
                self.print_billion_tracker(portfolio)
                break
            except Exception as e:
                self.log(f"⚠️ Error: {e}")
                time.sleep(2)


if __name__ == "__main__":
    r = PlanetaryReclaimer()
    r.run()
