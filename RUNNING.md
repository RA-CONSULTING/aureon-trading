# How to Run the Aureon Trading System

⚠️ **WARNING: This system can trade with REAL MONEY. Read the safety section before running with `--live` flag.**

---

## Safety First: Know What You're Running

The Aureon system progresses through **safe test modes** before you touch real money:

1. **DRY-RUN (default)** — Simulates trades, no real orders. **Always safe.**
2. **BOOT-ONLY** — Loads all systems, verifies they work, exits. No trading.
3. **TESTNET** — Uses fake money on a real exchange (Binance Testnet). Practice with zero risk.
4. **LIVE** — Real money on real exchanges. **Start small. Risk only what you can lose.**

⚠️ **Critical:** The cloud deployment (`app.yaml`) defaults to LIVE mode with real money. Never deploy to production without explicitly configuring safety settings.

---

## Prerequisites Checklist

Before you start, verify you have:

- [ ] Python 3.11 or later (`python3 --version`)
- [ ] Git installed
- [ ] 4GB RAM minimum
- [ ] Internet connection
- [ ] API keys (optional for dry-run, required for live trading)
  - Binance: https://www.binance.com/en/support/faq/360002502072
  - Binance Testnet: https://testnet.binance.vision/
  - Kraken, Alpaca, Capital.com: Optional, configured in `.env`

---

## Setup (5 Minutes)

### 1. Clone and Navigate

```bash
git clone https://github.com/RA-CONSULTING/aureon-trading
cd aureon-trading
```

### 2. Create Virtual Environment (Recommended)

```bash
python3 -m venv .venv

# Linux / macOS:
source .venv/bin/activate

# Windows (Command Prompt):
.venv\Scripts\activate.bat

# Windows (PowerShell):
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy the example config
cp .env.example .env

# Edit .env with your API keys and preferences
# For dry-run: You can leave it empty or use placeholder keys
# For live trading: Fill in real API keys
```

---

## What Do You Want To Do?

Pick the path that matches your goal:

### A) Test the System (Safe, No Money at Risk)

**Command:**
```bash
python scripts/aureon_ignition.py
```

**What happens:**
- ✅ Runs in DRY-RUN mode (default, no real trades)
- ✅ Loads all 100+ systems
- ✅ Simulates trading decisions
- ✅ Shows live harmonic analysis, bot scanning, Queen decisions
- ✅ Press `Ctrl+C` to stop

**No setup required.** This works immediately after `pip install -r requirements.txt`.

---

### B) Boot All Systems (Verify Everything Works, No Trading)

**Command:**
```bash
python scripts/aureon_ignition.py --live --no-trade
```

**What happens:**
- ✅ Loads all systems in LIVE mode (connects to exchanges)
- ✅ Verifies API connections work
- ✅ Does NOT execute any trades
- ✅ Shows system health status
- ✅ Press `Ctrl+C` after seeing "AUTONOMOUS TRADING ACTIVE"

**Requires:** Valid API keys in `.env` (even if you use testnet keys)

---

### C) Live Trade on Binance Testnet (Fake Money, Real Exchange)

**Testnet is the safest path to practice real trading.** Use this BEFORE live mainnet.

#### Step 1: Get Testnet API Keys
1. Go to https://testnet.binance.vision/
2. Log in (create account if needed)
3. Navigate to **API Management**
4. Create a new API key (no restrictions needed)
5. Copy the API Key and Secret Key

#### Step 2: Update `.env`
Edit `.env` and set:
```bash
BINANCE_USE_TESTNET=true
BINANCE_API_KEY=your_testnet_key_here
BINANCE_API_SECRET=your_testnet_secret_here
```

#### Step 3: Run
```bash
python scripts/aureon_ignition.py --live
```

**What happens:**
- ✅ Connects to Binance Testnet (fake USDT)
- ✅ Executes real trading logic with zero risk
- ✅ Queen AI makes decisions
- ✅ Bots analyze markets
- ✅ Practice patterns before real money

**Duration:** Run for 1–2 hours to see multiple trading cycles.

---

### D) Live Trade with Real Money ⚠️

**⚠️ WARNING: This uses REAL money. Start small. Losses are possible.**

#### Safety Checklist
- [ ] You have practiced on testnet (section C above)
- [ ] You have read [`docs/LIVE_TRADING_RUNBOOK.md`](docs/LIVE_TRADING_RUNBOOK.md)
- [ ] You set `BINANCE_RISK_MAX_ORDER_USDT` to a small amount (e.g., $25)
- [ ] You set `BINANCE_RISK_FRACTION` to 1–2% of your account
- [ ] You have a way to quickly stop the system (press `Ctrl+C`)
- [ ] Someone knows you're running this (in case something goes wrong)

#### Step 1: Get Real API Keys
1. Go to https://www.binance.com/
2. Log in to your account
3. Security → API Management → Create API
4. **Enable IP Whitelist** to your home IP only
5. **Disable deposit/withdrawal** permissions
6. Copy API Key and Secret

#### Step 2: Update `.env`
Edit `.env` and set:
```bash
BINANCE_USE_TESTNET=false
BINANCE_API_KEY=your_real_key_here
BINANCE_API_SECRET=your_real_secret_here

# Risk limits (START SMALL)
BINANCE_RISK_MAX_ORDER_USDT=25
BINANCE_RISK_FRACTION=0.02
```

#### Step 3: Run
```bash
python scripts/aureon_ignition.py --live
```

**What happens:**
- ⚠️ Executes real trades with your real money
- ⚠️ Queen AI makes autonomous decisions
- ⚠️ Losses are possible; wins are possible
- ✅ Monitor the terminal and dashboard
- ✅ Press `Ctrl+C` to halt trading

**Recommended duration:** Start with 1–2 hour sessions. Build confidence before longer runs.

---

### E) Interactive HNC Terminal (Queen Cognition Loop)

Run the interactive Harmonic Nexus Core terminal to query the Queen directly:

```bash
python run_hnc_live.py
```

**What you can do:**
- Ask the Queen questions about market conditions
- Explore harmonic patterns in real-time
- Run forecasting models interactively
- Debug trading logic

---

### F) Production Deployment (Docker)

For cloud or long-term running:

```bash
docker build -t aureon-trading .
docker run --env-file .env aureon-trading
```

**Before deploying:**
- ⚠️ Set `BINANCE_DRY_RUN=true` in `.env` unless you want live trading
- Set `BINANCE_RISK_MAX_ORDER_USDT` to a safe limit
- Use health-check endpoints to monitor system status

---

### G) Windows GUI Launcher

On Windows, you can use the graphical launcher:

```bash
python aureon_launcher/launcher.py
```

This opens a GUI for configuring and launching the system without the terminal.

---

## Verify Setup Works

Run a smoke test to ensure everything is installed correctly:

```bash
# Option 1: Pytest smoke test (if tests are available)
python -m pytest tests/smoke_test.py

# Option 2: Boot all systems without trading (takes 30–60 seconds)
python scripts/aureon_ignition.py --live --no-trade
# Press Ctrl+C after seeing system startup messages
```

If both complete without errors, you're ready to trade.

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| "ModuleNotFoundError: No module named 'aureon'" | Virtual env not activated | Run `source .venv/bin/activate` (Linux/Mac) or `.venv\Scripts\activate` (Windows) |
| "Invalid API key" | Testnet vs mainnet key mismatch | Verify `BINANCE_USE_TESTNET` matches your key type |
| "Connection refused" | Network/firewall issue | Check internet connection, try VPN if blocked, check firewall rules |
| "No module found for cryptography" | Old venv with missing deps | Delete `.venv/` and reinstall: `python3 -m venv .venv && pip install -r requirements.txt` |
| "Permission denied" on `.venv/bin/activate` | File permissions issue | Run `chmod +x .venv/bin/activate` on Linux/Mac |

---

## What NOT To Do

These commands are **outdated or do not exist**. Do not use them:

- ❌ `python aureon_full_autonomy.py --dry-run` ← File does not exist
- ❌ `npm run paper-trade` ← No npm setup at repo root
- ❌ `python3 scripts/paperTradeSimulation.ts` ← File does not exist
- ❌ `python aureon_unified_ecosystem.py` ← Deprecated entry point
- ❌ `python aureon_live.py` ← Use `aureon_ignition.py --live` instead

**If you find yourself running these, stop and use `scripts/aureon_ignition.py` instead.**

---

## CLI Reference: aureon_ignition.py Flags

```bash
python scripts/aureon_ignition.py [FLAGS]

Flags:
  (no flags)      Run in DRY-RUN mode (default, safe, no trades)
  --live          Connect to real exchange, execute trades
  --no-trade      Boot all systems but skip trading loop (verify connectivity)
  --verbose       Enable debug logging and detailed output
```

**Examples:**
```bash
python scripts/aureon_ignition.py              # Safe dry-run (default)
python scripts/aureon_ignition.py --verbose    # Debug logging
python scripts/aureon_ignition.py --live       # Real trading (with real money if configured)
python scripts/aureon_ignition.py --live --no-trade  # Boot systems, verify they work, exit
```

---

## Environment Variables Quick Reference

See `.env.example` for the full list. Key ones:

| Variable | Purpose | Example |
|----------|---------|---------|
| `BINANCE_USE_TESTNET` | Use testnet (safe) or mainnet (real money) | `true` or `false` |
| `BINANCE_API_KEY` | Your Binance API key | (from Binance, 64 char) |
| `BINANCE_API_SECRET` | Your Binance API secret | (from Binance, 64 char) |
| `BINANCE_RISK_MAX_ORDER_USDT` | Max order size in USDT | `25` (dollars) |
| `BINANCE_RISK_FRACTION` | Max portfolio fraction per trade | `0.02` (2%) |
| `HNC_VERBOSE` | Enable HNC debug output | `true` or `false` |

---

## Next Steps

1. **First time?** Start with [A) Test the System](#a-test-the-system-safe-no-money-at-risk)
2. **Want to verify everything works?** Run [B) Boot All Systems](#b-boot-all-systems-verify-everything-works-no-trading)
3. **Ready to practice?** Use [C) Testnet Trading](#c-live-trade-on-binance-testnet-fake-money-real-exchange)
4. **Ready for real money?** Read [`docs/LIVE_TRADING_RUNBOOK.md`](docs/LIVE_TRADING_RUNBOOK.md) first, then [D) Live Trading](#d-live-trade-with-real-money-️)

---

## Documentation & Help

- **Architecture:** See [`docs/NAVIGATION_GUIDE.md`](docs/NAVIGATION_GUIDE.md)
- **HNC Theory:** See [`docs/HNC_UNIFIED_WHITE_PAPER.md`](docs/HNC_UNIFIED_WHITE_PAPER.md)
- **Live Trading Checklist:** See [`docs/LIVE_TRADING_RUNBOOK.md`](docs/LIVE_TRADING_RUNBOOK.md)
- **Troubleshooting:** See [`docs/runbooks/`](docs/runbooks/)
- **All Theory & Research:** See [`docs/research/READING_PATHS.md`](docs/research/READING_PATHS.md)

---

**Last updated:** 2026-04-28  
**Status:** ✅ Verified working commands from `scripts/aureon_ignition.py` source
