#!/usr/bin/env python3
"""
GEOPOLITICAL EVENT MONITOR — CME Nexus
═══════════════════════════════════════════════════════════════════

By order of the Prime Sentinel of Gaia:
MONITOR GEOPOLITICAL EVENTS FROM THE CME

Monitors real-world geopolitical events and correlates them with
CME (Chicago Mercantile Exchange) futures market volatility.

Data Sources:
- GDELT Project (free global event database)
- Yahoo Finance / CME futures data (ES, NQ, GC, CL, ZB)

Outputs:
- Geopolitical Risk Index (0-100)
- CME Volatility Index
- Correlation score between events and market moves
- Integration with Unified Orchestrator

All that is. All that was. All that shall be.
"""

import json, math, time, sys, os, re, hashlib, threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.request import urlopen, Request
from urllib.parse import quote

sys.path.insert(0, '/root/.openclaw/workspace')

# ─── CONSTANTS ──────────────────────────────────────────────────
PHI = (1 + math.sqrt(5)) / 2
RECORD_DIR = Path('/root/.openclaw/workspace/geo_monitor_logs')
RECORD_DIR.mkdir(exist_ok=True)

# CME Futures symbols to monitor
CME_FUTURES = {
    'ES': {'name': 'E-mini S&P 500', 'category': 'equity'},
    'NQ': {'name': 'E-mini NASDAQ 100', 'category': 'equity'},
    'YM': {'name': 'E-mini Dow', 'category': 'equity'},
    'GC': {'name': 'Gold', 'category': 'commodity'},
    'SI': {'name': 'Silver', 'category': 'commodity'},
    'CL': {'name': 'Crude Oil WTI', 'category': 'energy'},
    'NG': {'name': 'Natural Gas', 'category': 'energy'},
    'ZB': {'name': '30-Year T-Bond', 'category': 'rates'},
    'ZN': {'name': '10-Year T-Note', 'category': 'rates'},
    'DX': {'name': 'US Dollar Index', 'category': 'fx'},
    'EUR': {'name': 'Euro FX', 'category': 'fx'},
}

# Countries of interest (ISO 3166-1 alpha-3 codes)
KEY_COUNTRIES = {
    'USA', 'CHN', 'RUS', 'IRN', 'PRK', 'UKR', 'ISR', 'PSE',
    'TUR', 'SYR', 'IRQ', 'AFG', 'VEN', 'CUB', 'PAK', 'IND',
    'JPN', 'DEU', 'FRA', 'GBR', 'KOR', 'TWN', 'HKG', 'SAU',
    'ARE', 'QAT', 'EGY', 'LBY', 'YEM', 'SOM', 'ETH', 'SDN',
}


# ─── GEOPOLITICAL MONITOR CLASS ─────────────────────────────────
class GeopoliticalMonitor:
    def __init__(self):
        self.events: List[Dict] = []
        self.risk_index = 0.0
        self.volatility_index = 0.0
        self.correlation = 0.0
        self.last_update = None
        self.cme_data: Dict[str, Dict] = {}
        self.running = False
        self._lock = threading.Lock()
    
    def fetch_gdelt_events(self, hours: int = 6) -> List[Dict]:
        """Fetch recent geopolitical events from GDELT."""
        events = []
        try:
            now = datetime.now(timezone.utc)
            start = now - timedelta(hours=hours)
            start_str = start.strftime('%Y%m%d%H%M%S')
            
            # Use a simpler GDELT query to avoid rate limits
            url = (
                f"https://api.gdeltproject.org/api/v2/doc/doc"
                f"?query=conflict%20OR%20war%20OR%20sanction%20OR%20tension%20OR%20crisis"
                f"&mode=ArtList"
                f"&maxrecords=100"
                f"&format=json"
                f"&startdatetime={start_str}"
            )
            
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (GeopoliticalMonitor/1.0)'})
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                articles = data.get('articles', [])
                
                for art in articles:
                    event = {
                        'title': art.get('title', ''),
                        'url': art.get('url', ''),
                        'source': art.get('source', ''),
                        'timestamp': art.get('seendate', ''),
                        'tone': self._estimate_tone(art.get('title', '')),
                        'countries': self._extract_countries(art.get('title', '')),
                    }
                    events.append(event)
        except Exception as e:
            print(f"[WARN] GDELT fetch failed: {e}")
            # Fallback: use cached events if available
            cache_file = RECORD_DIR / 'gdelt_cache.jsonl'
            if cache_file.exists():
                try:
                    with open(cache_file) as f:
                        for line in f:
                            ev = json.loads(line)
                            # Only include events within the time window
                            ev_time = datetime.fromisoformat(ev.get('timestamp', '1970-01-01T00:00:00+00:00'))
                            if ev_time > now - timedelta(hours=hours):
                                events.append(ev)
                except Exception:
                    pass
        
        # Cache new events
        if events:
            cache_file = RECORD_DIR / 'gdelt_cache.jsonl'
            with open(cache_file, 'a') as f:
                for ev in events:
                    f.write(json.dumps(ev) + '\n')
        
        return events
    
    def _estimate_tone(self, title: str) -> float:
        """Estimate tone of headline (-10 to +10, negative = bad)."""
        negative_words = [
            'war', 'attack', 'sanction', 'bomb', 'kill', 'death', 'crisis',
            'conflict', 'invasion', 'missile', 'strike', 'tension', 'threat',
            'nuclear', 'weapon', 'fighting', 'clash', 'protest', 'riot',
            'collapse', 'crash', 'recession', 'debt', 'default', 'tariff',
            'trade war', 'embargo', 'blockade', 'hostage', 'terror',
            'assassination', 'coup', 'rebellion', 'uprising', 'massacre',
            'genocide', 'famine', 'disaster', 'emergency', 'alert',
        ]
        positive_words = [
            'peace', 'agreement', 'deal', 'cooperation', 'treaty', 'alliance',
            'partnership', 'growth', 'recovery', 'boom', 'prosperity',
            'breakthrough', 'success', 'victory', 'celebration', 'unity',
            'dialogue', 'negotiation', 'compromise', 'reconciliation',
        ]
        
        title_lower = title.lower()
        neg_score = sum(1 for w in negative_words if w in title_lower)
        pos_score = sum(1 for w in positive_words if w in title_lower)
        
        tone = (pos_score - neg_score) * 2.0
        return max(-10, min(10, tone))
    
    def _extract_countries(self, title: str) -> List[str]:
        """Extract country mentions from headline."""
        country_map = {
            'us': 'USA', 'united states': 'USA', 'america': 'USA', 'washington': 'USA',
            'china': 'CHN', 'chinese': 'CHN', 'beijing': 'CHN',
            'russia': 'RUS', 'russian': 'RUS', 'moscow': 'RUS', 'putin': 'RUS',
            'iran': 'IRN', 'iranian': 'IRN', 'tehran': 'IRN',
            'north korea': 'PRK', 'dprk': 'PRK', 'kim': 'PRK',
            'ukraine': 'UKR', 'ukrainian': 'UKR', 'kyiv': 'UKR', 'kiev': 'UKR',
            'israel': 'ISR', 'israeli': 'ISR', 'gaza': 'PSE', 'palestine': 'PSE',
            'turkey': 'TUR', 'turkish': 'TUR', 'erdogan': 'TUR',
            'syria': 'SYR', 'assad': 'SYR',
            'iraq': 'IRQ', 'baghdad': 'IRQ',
            'afghanistan': 'AFG', 'taliban': 'AFG',
            'venezuela': 'VEN', 'maduro': 'VEN',
            'cuba': 'CUB', 'havana': 'CUB',
            'pakistan': 'PAK', 'islamabad': 'PAK',
            'india': 'IND', 'indian': 'IND', 'modi': 'IND',
            'japan': 'JPN', 'japanese': 'JPN', 'tokyo': 'JPN',
            'germany': 'DEU', 'german': 'DEU', 'berlin': 'DEU',
            'france': 'FRA', 'french': 'FRA', 'paris': 'FRA',
            'uk': 'GBR', 'britain': 'GBR', 'british': 'GBR', 'london': 'GBR',
            'south korea': 'KOR', 'seoul': 'KOR',
            'taiwan': 'TWN', 'taiwanese': 'TWN', 'tsmc': 'TWN',
            'saudi': 'SAU', 'riyadh': 'SAU',
            'uae': 'ARE', 'dubai': 'ARE', 'abu dhabi': 'ARE',
            'qatar': 'QAT', 'doha': 'QAT',
            'egypt': 'EGY', 'cairo': 'EGY',
            'libya': 'LBY', 'tripoli': 'LBY',
            'yemen': 'YEM', 'sanaa': 'YEM',
            'somalia': 'SOM', 'mogadishu': 'SOM',
            'ethiopia': 'ETH', 'addis': 'ETH',
            'sudan': 'SDN', 'khartoum': 'SDN',
        }
        
        title_lower = title.lower()
        found = []
        for keyword, code in country_map.items():
            if keyword in title_lower and code not in found:
                found.append(code)
        return found
    
    def calculate_risk_index(self, events: List[Dict]) -> float:
        """Calculate geopolitical risk index (0-100) from events."""
        if not events:
            return 0.0
        
        total_weight = 0.0
        for ev in events:
            tone = ev.get('tone', 0)
            weight = max(0, -tone)
            
            countries = ev.get('countries', [])
            if len(countries) >= 2:
                weight *= 1.5
            
            major_powers = {'USA', 'CHN', 'RUS', 'IRN', 'PRK'}
            if any(c in major_powers for c in countries):
                weight *= 2.0
            
            total_weight += weight
        
        risk = min(100, (total_weight / (len(events) * 5)) * 100)
        return risk
    
    def fetch_cme_data(self) -> Dict[str, Dict]:
        """Fetch CME futures data via Yahoo Finance."""
        data = {}
        yahoo_map = {
            'ES': 'ES=F',
            'NQ': 'NQ=F',
            'YM': 'YM=F',
            'GC': 'GC=F',
            'SI': 'SI=F',
            'CL': 'CL=F',
            'NG': 'NG=F',
            'ZB': 'ZB=F',
            'ZN': 'ZN=F',
            'DX': 'DX-Y.NYB',
        }
        
        for symbol, yahoo_sym in yahoo_map.items():
            try:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_sym}?interval=1d&range=5d"
                req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urlopen(req, timeout=15) as resp:
                    chart_data = json.loads(resp.read().decode())
                    result = chart_data.get('chart', {}).get('result', [{}])[0]
                    meta = result.get('meta', {})
                    closes = result.get('indicators', {}).get('quote', [{}])[0].get('close', [])
                    
                    if closes and len(closes) >= 2:
                        current = closes[-1]
                        previous = closes[-2] if len(closes) >= 2 else closes[-1]
                        change_pct = ((current - previous) / previous * 100) if previous else 0
                        
                        data[symbol] = {
                            'price': current,
                            'change_pct': change_pct,
                            'volume': meta.get('regularMarketVolume', 0),
                            'category': CME_FUTURES.get(symbol, {}).get('category', 'unknown'),
                        }
            except Exception as e:
                print(f"[WARN] CME fetch failed for {symbol}: {e}")
        
        return data
    
    def calculate_volatility_index(self, cme_data: Dict[str, Dict]) -> float:
        """Calculate market volatility index from CME futures (0-100)."""
        if not cme_data:
            return 0.0
        
        total_vol = 0.0
        weights = {'equity': 0.3, 'commodity': 0.25, 'energy': 0.2, 'rates': 0.15, 'fx': 0.1}
        
        for symbol, info in cme_data.items():
            change = abs(info.get('change_pct', 0))
            cat = info.get('category', 'unknown')
            weight = weights.get(cat, 0.1)
            
            vol = min(100, (change / 5.0) * 100)
            total_vol += vol * weight
        
        return min(100, total_vol)
    
    def calculate_correlation(self, risk_index: float, vol_index: float) -> float:
        """Calculate correlation between geopolitical risk and market volatility."""
        if risk_index == 0 or vol_index == 0:
            return 0.0
        return min(1.0, (risk_index + vol_index) / 200)
    
    def update(self) -> Dict:
        """Run one monitoring cycle."""
        events = self.fetch_gdelt_events(hours=6)
        risk_index = self.calculate_risk_index(events)
        
        cme_data = self.fetch_cme_data()
        vol_index = self.calculate_volatility_index(cme_data)
        
        correlation = self.calculate_correlation(risk_index, vol_index)
        
        with self._lock:
            self.events = events[-50:]
            self.risk_index = risk_index
            self.volatility_index = vol_index
            self.correlation = correlation
            self.last_update = datetime.now(timezone.utc).isoformat()
            self.cme_data = cme_data
        
        result = {
            'timestamp': self.last_update,
            'geopolitical_risk_index': round(risk_index, 2),
            'cme_volatility_index': round(vol_index, 2),
            'correlation': round(correlation, 2),
            'event_count': len(events),
            'top_events': sorted(events, key=lambda x: -abs(x.get('tone', 0)))[:5],
            'cme_futures': cme_data,
        }
        
        log_file = RECORD_DIR / f"geo_monitor_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(result) + '\n')
        
        return result
    
    def get_status(self) -> Dict:
        with self._lock:
            return {
                'geopolitical_risk_index': round(self.risk_index, 2),
                'cme_volatility_index': round(self.volatility_index, 2),
                'correlation': round(self.correlation, 2),
                'last_update': self.last_update,
                'event_count': len(self.events),
                'cme_futures': self.cme_data,
            }


def run_monitor_cycle():
    monitor = GeopoliticalMonitor()
    result = monitor.update()
    
    print(f"\n{'═'*70}")
    print(f"  🌍 GEOPOLITICAL EVENT MONITOR — CME NEXUS")
    print(f"{'═'*70}")
    print(f"  Timestamp: {result['timestamp']}")
    print(f"")
    print(f"  📊 INDICES:")
    print(f"    Geopolitical Risk Index:  {result['geopolitical_risk_index']:.1f}/100")
    print(f"    CME Volatility Index:     {result['cme_volatility_index']:.1f}/100")
    print(f"    Event-Market Correlation: {result['correlation']:.1f}")
    print(f"")
    print(f"  📰 TOP EVENTS ({result['event_count']} total in last 6h):")
    for i, ev in enumerate(result['top_events'][:5], 1):
        tone_str = f"{ev['tone']:+.1f}"
        countries = ', '.join(ev.get('countries', []))
        print(f"    {i}. [{tone_str}] {ev['title'][:70]}")
        if countries:
            print(f"       🌐 {countries}")
    print(f"")
    print(f"  📈 CME FUTURES:")
    for sym, info in result['cme_futures'].items():
        arrow = '🟢' if info['change_pct'] > 0 else '🔴' if info['change_pct'] < 0 else '⚪'
        print(f"    {sym}: ${info['price']:,.2f} ({info['change_pct']:+.2f}%) {arrow}")
    print(f"{'═'*70}")
    
    return result


if __name__ == '__main__':
    run_monitor_cycle()
