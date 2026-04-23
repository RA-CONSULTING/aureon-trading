# Layer 1: Substrate (φ² Bridge Foundation)

## Purpose
The φ² Coherence Bridge foundation. This layer contains harmonic constants, real-time market data feeds, and core data structures that all other layers depend on.

## What Goes Here

### `frequencies/` — Harmonic Constants & φ-Ladder
- Fundamental frequency definitions (528.422 Hz seed, 1.42 GHz NIST anchor)
- φ-ladder frequency generators (f_k = f₀ · φᵏ)
- Schumann resonance constants
- Harmonic alphabet encodings
- Counter-frequency systems
- Any code that establishes φ-spaced relationships

**Key files:**
- `aureon_harmonic_*` modules
- Frequency counter scripts
- Seed generators

---

### `market_feeds/` — Real-Time Data Streams
- Live market data connectors (Alpaca SSE, Binance WebSocket, CoinAPI)
- Order book monitors
- OHLC candle feeds
- Exchange price tickers
- WebSocket handlers

**Key files:**
- `alpaca_sse_client.py` — Alpaca streaming
- `alpaca_client.py` — Alpaca REST client
- Market data consolidators
- Exchange adapters

---

### `data_models/` — Schemas & Caches
- Data structure definitions (prices, positions, orders)
- Unified cache representations (market cache, trade history)
- Database models
- State schemas
- Historical data structures

**Key files:**
- `queen_consciousness_model.py` — Core system state
- Cache consolidators (market, candle, portfolio)
- Schema validators

---

## Design Principle

**The Substrate is the foundation.** Everything above it depends on accuracy here. No code in Layer 1 should make decisions or contain trading logic. It should purely:

1. **Acquire** clean, φ-aligned market data
2. **Normalize** across exchanges to unified schemas
3. **Cache** for rapid access
4. **Validate** data integrity

---

## Quality Gates

Before moving code into Layer 1, ensure:

✓ It reads from external sources (markets, APIs, files)  
✓ It contains no trading decisions  
✓ It maintains φ-frequency relationships where applicable  
✓ Output is deterministic and fully tested  
✓ It provides clean, normalized data for Layer 2  

❌ Do NOT put decision logic here  
❌ Do NOT put execution code here  
❌ Do NOT put performance metrics here  

---

## Integration with Other Layers

- **← FROM:** External markets, APIs, data sources
- **→ TO:** Layer 2 (dynamics) consumes normalized data and frequencies
- **→ TO:** Layer 4 (output) uses cached data for portfolio tracking

---

**Last Updated:** 2026-04-23
