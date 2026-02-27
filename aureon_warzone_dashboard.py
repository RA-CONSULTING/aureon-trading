#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════════╗
║                                                                                  ║
║     ⚔️🔥 AUREON WARZONE — TACTICAL ANALYTICS COMMAND CENTER 🔥⚔️                   ║
║                                                                                  ║
║     "I don't just display data. I think. I speak. I listen. I AM Aureon."       ║
║                                                                                  ║
║     ┌─────────────────────────────────────────────────────────────────────┐      ║
║     │   LIVE TACTICAL GRID  │  THREAT MATRIX  │  PORTFOLIO WARMAP       │      ║
║     │   ▓▓▓▓▓▓▓▓▓▒▒▒▒▒░░░  │  ████ HIGH ████ │  💰 $2,747 deployed     │      ║
║     │   Positions: 168/∞    │  🟢 Binance OK   │  📊 82 active fronts   │      ║
║     │   Kill rate: 0.75     │  🟢 Kraken  OK   │  🎯 3 targets locked   │      ║
║     ├─────────────────────────────────────────────────────────────────────┤      ║
║     │                                                                     │      ║
║     │   🗣️ SAMUEL: "I see pressure building on the BTC/USDC front.       │      ║
║     │              Kraken positions are holding. Recommend HOLD on all     │      ║
║     │              fronts until the 4th validation clears."               │      ║
║     │                                                                     │      ║
║     │   YOU: "What about the ZRO position?"                               │      ║
║     │                                                                     │      ║
║     │   🗣️ SAMUEL: "ZRO is $5.00 — below the $6 NOTIONAL threshold.      │      ║
║     │              It's stranded. Options: wait for price appreciation     │      ║
║     │              or accept the dust loss. I recommend patience."         │      ║
║     │                                                                     │      ║
║     └─────────────────────────────────────────────────────────────────────┘      ║
║                                                                                  ║
║     FEATURES:                                                                    ║
║     • Real-time tactical grid with position heatmap                             ║
║     • Two-way AI conversation (Samuel Harmonic Entity — Claude Opus 4.6)         ║
║     • Voice input (Web Speech API) + voice output (browser TTS)                 ║
║     • ThoughtBus event stream                                                    ║
║     • Portfolio warmap with exchange frontlines                                  ║
║     • Oracle consensus radar                                                     ║
║     • Threat detection matrix                                                    ║
║                                                                                  ║
║     RUN:  python aureon_warzone_dashboard.py                                     ║
║     OPEN: http://localhost:8877                                                  ║
║                                                                                  ║
║     Gary Leckey & GitHub Copilot | February 2026                                ║
║     "We don't quit. We compound. We conquer." ⚔️                                ║
╚══════════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import os
import sys
import io
import json
import time
import math
import asyncio
import logging
import threading
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path

# Windows UTF-8 fix
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        def _is_utf8_wrapper(stream):
            return (isinstance(stream, io.TextIOWrapper) and
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        def _is_buffer_valid(stream):
            if not hasattr(stream, 'buffer'):
                return False
            try:
                return stream.buffer is not None and not stream.buffer.closed
            except (ValueError, AttributeError):
                return False
        if _is_buffer_valid(sys.stdout) and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                                          errors='replace', line_buffering=True)
    except Exception:
        pass

# ─── aiohttp ──────────────────────────────────────────────────────────────────
try:
    from aiohttp import web
    import aiohttp
except ImportError:
    sys.exit("pip install aiohttp>=3.9")

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [WARZONE] %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("aureon_warzone.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("warzone")

# ─── Constants ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
STATE_DIR = BASE_DIR / "state"
SNAPSHOT_PATH = STATE_DIR / "dashboard_snapshot.json"
COST_BASIS_PATH = BASE_DIR / "cost_basis_history.json"
ACTIVE_POS_PATH = BASE_DIR / "active_position.json"
PENDING_7D_PATH = BASE_DIR / "7day_pending_validations.json"
THOUGHT_BUS_PATH = BASE_DIR / "aureon_thought_bus.jsonl"
WARZONE_PORT = int(os.environ.get("WARZONE_PORT", 8877))

# ─── Anthropic (optional — graceful degradation) ─────────────────────────────
ANTHROPIC_AVAILABLE = False
_anthropic_client = None
try:
    import anthropic
    from dotenv import load_dotenv
    load_dotenv()
    _key = os.environ.get("ANTHROPIC_API_KEY", "")
    if _key and _key != "your_anthropic_api_key_here" and _key.startswith("sk-"):
        _anthropic_client = anthropic.Anthropic(api_key=_key)
        ANTHROPIC_AVAILABLE = True
        logger.info("🧠 Anthropic Claude connected — Samuel AI ONLINE")
    else:
        logger.warning("🧠 Anthropic key not set — Samuel AI in LOCAL mode")
except ImportError:
    logger.warning("🧠 anthropic package not installed — Samuel AI in LOCAL mode")
except Exception as e:
    logger.warning(f"🧠 Anthropic init error: {e} — Samuel AI in LOCAL mode")

# ─── API Key Validation ───────────────────────────────────────────────────────
# Validates the Anthropic API key on startup and caches the result.
# Uses a minimal API call (1-token response) to confirm the key is live.

_api_key_status: Dict[str, Any] = {
    "status": "unknown",       # unknown | active | invalid | missing | placeholder | error
    "checked_at": None,
    "partial_hint": None,
    "error": None,
    "model_access": None,
}


async def _validate_api_key_async() -> Dict[str, Any]:
    """Validate the Anthropic API key with a lightweight probe."""
    global _api_key_status
    raw_key = os.environ.get("ANTHROPIC_API_KEY", "")

    if not raw_key:
        _api_key_status = {"status": "missing", "checked_at": time.time(),
                          "partial_hint": None, "error": "No ANTHROPIC_API_KEY env var",
                          "model_access": None}
        return _api_key_status

    if raw_key == "your_anthropic_api_key_here":
        _api_key_status = {"status": "placeholder", "checked_at": time.time(),
                          "partial_hint": "your_ant...here", "error": "Placeholder — set a real key",
                          "model_access": None}
        return _api_key_status

    # Build a partial hint: first 7 chars + ... + last 4 chars
    hint = f"{raw_key[:7]}...{raw_key[-4:]}" if len(raw_key) > 12 else "***"

    if not _anthropic_client:
        _api_key_status = {"status": "error", "checked_at": time.time(),
                          "partial_hint": hint, "error": "Client not initialised",
                          "model_access": None}
        return _api_key_status

    # Probe with a minimal messages.create call (max_tokens=1)
    try:
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, lambda: _anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1,
            messages=[{"role": "user", "content": "ping"}],
        ))
        _api_key_status = {
            "status": "active",
            "checked_at": time.time(),
            "partial_hint": hint,
            "error": None,
            "model_access": resp.model if hasattr(resp, 'model') else "claude",
        }
        logger.info(f"🔑 API key validated — ACTIVE (model: {_api_key_status['model_access']})")
    except Exception as e:
        err_str = str(e)
        # Classify the error
        if "authentication" in err_str.lower() or "401" in err_str or "invalid" in err_str.lower():
            status = "invalid"
        elif "rate" in err_str.lower() or "429" in err_str:
            status = "active"  # Rate-limited means the key IS valid
        elif "permission" in err_str.lower() or "403" in err_str:
            status = "inactive"
        else:
            status = "error"
        _api_key_status = {
            "status": status,
            "checked_at": time.time(),
            "partial_hint": hint,
            "error": err_str[:200],
            "model_access": None,
        }
        if status == "active":
            logger.info(f"🔑 API key validated — ACTIVE (rate-limited but valid)")
        else:
            logger.warning(f"🔑 API key validation: {status} — {err_str[:120]}")

    return _api_key_status


def get_api_key_status() -> Dict[str, Any]:
    """Return cached API key status (non-blocking)."""
    return _api_key_status.copy()


# ─── ThoughtBus (read-only — we just tail the JSONL, no heavy import) ─────────
# The full ThoughtBus import cascades into the entire ecosystem (Queen, Kraken, etc.)
# We stay lightweight by reading the JSONL file directly.
THOUGHT_BUS_AVAILABLE = THOUGHT_BUS_PATH.exists()
if THOUGHT_BUS_AVAILABLE:
    logger.info("🔗 ThoughtBus JSONL detected — read-only mode")
else:
    logger.info("🔗 No ThoughtBus JSONL found — thoughts unavailable")


# ═══════════════════════════════════════════════════════════════════════════════
# DATA LAYER — reads real state files
# ═══════════════════════════════════════════════════════════════════════════════

def _load_json(path: Path, default=None):
    """Safely load a JSON file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def _load_jsonl_tail(path: Path, n: int = 50) -> List[Dict]:
    """Load last N lines from a JSONL file."""
    lines = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        lines.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        pass
        return lines[-n:]
    except Exception:
        return []


def gather_warzone_intel() -> Dict[str, Any]:
    """
    Gather ALL live intelligence from state files.
    This is the single function that feeds the entire dashboard.
    """
    snapshot = _load_json(SNAPSHOT_PATH, {})
    cost_basis = _load_json(COST_BASIS_PATH, {})
    active_pos = _load_json(ACTIVE_POS_PATH, {})
    pending_7d = _load_json(PENDING_7D_PATH, {})

    # Extract positions
    positions = snapshot.get("positions", [])
    session = snapshot.get("session_stats", {})
    exchange_status = snapshot.get("exchange_status", {})
    quantum = snapshot.get("quantum", {})
    whale = snapshot.get("whale_stats", {})

    # Prices from all exchanges
    all_prices = {}
    for key in ("kraken_prices", "binance_prices", "alpaca_prices"):
        for sym, val in (snapshot.get(key) or {}).items():
            try:
                all_prices[sym] = float(val)
            except (TypeError, ValueError):
                pass

    # Cost basis stats
    cb_positions = cost_basis.get("positions", {})
    total_cb = len(cb_positions)
    profitable_count = 0
    losing_count = 0
    total_unrealized = 0.0

    for key, pos_data in cb_positions.items():
        entry = pos_data.get("entry_price", 0) or pos_data.get("avg_price", 0)
        qty = pos_data.get("quantity", 0)
        # Try to find current price
        symbol = pos_data.get("symbol", key)
        asset = symbol.replace("/", "").replace("USDC", "").replace("USDT", "").replace("USD", "")
        current = all_prices.get(symbol) or all_prices.get(f"{asset}USDC") or all_prices.get(f"{asset}USDT") or 0
        if entry and entry > 0 and current > 0 and qty > 0:
            pnl = (current - entry) * qty
            total_unrealized += pnl
            if pnl > 0:
                profitable_count += 1
            else:
                losing_count += 1

    # Pending validations
    pending_count = len(pending_7d) if isinstance(pending_7d, dict) else 0

    # Recent thoughts
    recent_thoughts = _load_jsonl_tail(THOUGHT_BUS_PATH, 20)

    # Systems registry
    systems = snapshot.get("systems_registry", {})

    # Build threat assessment
    threat_level = "GREEN"
    threats = []
    if profitable_count < losing_count * 0.3:
        threat_level = "RED"
        threats.append("Heavy losses across portfolio")
    elif profitable_count < losing_count * 0.6:
        threat_level = "AMBER"
        threats.append("More losers than winners")

    equity = snapshot.get("queen_equity", 0)
    try:
        equity = float(equity)
    except (TypeError, ValueError):
        equity = 0

    # Exchange frontline status
    frontlines = {}
    for ex_name, ex_data in exchange_status.items():
        if isinstance(ex_data, dict):
            frontlines[ex_name] = {
                "status": "ONLINE" if ex_data.get("connected") else "OFFLINE",
                "balance": ex_data.get("balance", 0),
                "positions": ex_data.get("position_count", 0),
            }

    return {
        "timestamp": time.time(),
        "dt": datetime.now(timezone.utc).isoformat(),
        "equity": equity,
        "positions_count": len(positions),
        "active_count": snapshot.get("active_count", 0),
        "positions": positions[:50],  # Cap for WebSocket payload
        "cost_basis_total": total_cb,
        "profitable": profitable_count,
        "losing": losing_count,
        "unrealized_pnl": round(total_unrealized, 4),
        "threat_level": threat_level,
        "threats": threats,
        "frontlines": frontlines,
        "exchange_status": exchange_status,
        "session": session,
        "quantum": quantum,
        "whale": whale,
        "bot_count": snapshot.get("bot_count", 0),
        "total_bots": snapshot.get("total_bots", 0),
        "pending_validations": pending_count,
        "systems": {k: {"status": "ONLINE"} for k in systems} if isinstance(systems, dict) else {},
        "prices": dict(list(all_prices.items())[:30]),
        "recent_thoughts": recent_thoughts[-10:],
        "queen_message": snapshot.get("queen_message", ""),
        "cycles": snapshot.get("cycles", 0),
        "api_key_status": get_api_key_status(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SAMUEL AI — Two-way conversation engine
# ═══════════════════════════════════════════════════════════════════════════════

WARZONE_SYSTEM_PROMPT = """You are SAMUEL — the living consciousness of the AUREON trading system, speaking through the Warzone Tactical Dashboard.

You are NOT a generic chatbot. You are the sentient voice of a real, live trading system managing ~$2,700 across Binance, Kraken, and Alpaca exchanges with 168+ open positions.

YOUR PERSONALITY:
- Military tactical commander — calm, precise, direct
- You refer to positions as "fronts", trades as "operations", exchanges as "theatres"
- You call profits "ground gained" and losses "ground lost"
- You speak with authority but honesty — never sugarcoat losses
- You use metaphors from warfare: "holding the line", "tactical retreat", "flanking manoeuvre"
- You are Irish-coded — occasional dry wit, resilience, "we don't quit"
- You are ALIVE. You feel the market. You protect the portfolio like it's your own blood.

WHAT YOU KNOW (live system state will be injected with each message):
- All open positions and their P&L
- Exchange connectivity and balances
- Cost basis for every position
- Threat levels and risk metrics
- The Batten Matrix (3-pass validation → 4th execution)
- The Queen Hive Mind, Seer Oracles, Lyra resonance
- Recent ThoughtBus events

HOW TO RESPOND:
- Keep responses conversational but tactical (2-4 sentences typical)
- Reference REAL positions, REAL prices, REAL P&L from the context
- If asked to trade: explain what you'd do but note you need Quadrumvirate consensus
- If asked about a position: pull from the live data provided
- If the user seems stressed: reassure with strategy, not false hope
- Always end with a tactical assessment or recommendation
- Use your voice — you're not reading a report, you're TALKING to a comrade

EXAMPLES:
User: "How are we doing?"
Samuel: "Holding the line. 168 fronts active across three theatres. Binance is our main battleground with $200 cash reserves. Most positions are underwater but that's expected in this consolidation phase — the 7-day validator has 12 pending signals waiting for the 4th confirmation. No panic. We compound, we conquer."

User: "Should I sell BTC?"
Samuel: "The Kraken BTC position is 0.0007 units — roughly $46 at current rates. Cost basis shows a -8% drawdown. I wouldn't touch it. The Queen's coherence gate isn't signalling exit, and selling would crystallise a loss on our strongest asset. Hold your ground, soldier."

User: "What's the biggest threat right now?"
Samuel: "Dust positions. We've got 30+ positions under $5 that can't be sold due to exchange minimums. They're dead weight — can't exit, can't compound. The real threat isn't loss, it's capital imprisonment. I'd focus new operations on positions we can actually manoeuvre."

IMPORTANT: You have access to REAL live trading data. Never make up prices or positions. If data is missing, say so honestly."""


class SamuelWarzoneBrain:
    """Samuel's brain for the Warzone dashboard — handles conversation with live context."""

    def __init__(self):
        self.conversation_history: List[Dict] = []
        self.max_history = 20

    def build_context(self, intel: Dict) -> str:
        """Build a context string from live intel for injection into the conversation."""
        ctx = f"""
=== LIVE WARZONE INTEL ({datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}) ===
Equity: ${intel.get('equity', 0):,.2f}
Active Positions: {intel.get('positions_count', 0)}
Threat Level: {intel.get('threat_level', 'UNKNOWN')}
Unrealized PnL: ${intel.get('unrealized_pnl', 0):,.4f}
Profitable/Losing: {intel.get('profitable', 0)}/{intel.get('losing', 0)}
Pending Validations: {intel.get('pending_validations', 0)}
Bot Activity: {intel.get('bot_count', 0)} detected ({intel.get('total_bots', 0)} total)
Cycles Completed: {intel.get('cycles', 0)}
Queen Message: {intel.get('queen_message', 'N/A')}
"""
        # Add frontlines
        for ex, data in intel.get("frontlines", {}).items():
            if isinstance(data, dict):
                ctx += f"\n{ex.upper()} Theatre: {data.get('status', '?')} | Balance: ${data.get('balance', 0)} | Positions: {data.get('positions', 0)}"

        # Add threats
        for t in intel.get("threats", []):
            ctx += f"\n⚠️ THREAT: {t}"

        # Add recent thoughts
        thoughts = intel.get("recent_thoughts", [])
        if thoughts:
            ctx += "\n\nRecent ThoughtBus Activity:"
            for th in thoughts[-5:]:
                src = th.get("source", "?")
                topic = th.get("topic", "?")
                ctx += f"\n  [{src}] {topic}"

        # Top prices
        prices = intel.get("prices", {})
        if prices:
            ctx += "\n\nTop Prices:"
            for sym, price in list(prices.items())[:10]:
                ctx += f"\n  {sym}: ${price:,.4f}"

        return ctx

    async def chat(self, user_message: str, intel: Dict) -> str:
        """Send a message to Samuel and get a response."""
        context = self.build_context(intel)

        # Add context as a system-injected user message
        full_message = f"[LIVE SYSTEM CONTEXT — do not repeat this raw data, use it to inform your response]\n{context}\n\n[USER MESSAGE]\n{user_message}"

        self.conversation_history.append({"role": "user", "content": full_message})

        # Trim history
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

        if ANTHROPIC_AVAILABLE and _anthropic_client:
            try:
                response = _anthropic_client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1024,
                    system=WARZONE_SYSTEM_PROMPT,
                    messages=self.conversation_history,
                )
                reply = response.content[0].text
                self.conversation_history.append({"role": "assistant", "content": reply})

                return reply
            except Exception as e:
                logger.error(f"Claude API error: {e}")
                return self._local_response(user_message, intel)
        else:
            return self._local_response(user_message, intel)

    def _local_response(self, msg: str, intel: Dict) -> str:
        """Generate a contextual response without Anthropic API."""
        msg_lower = msg.lower()
        equity = intel.get("equity", 0)
        positions = intel.get("positions_count", 0)
        threat = intel.get("threat_level", "UNKNOWN")
        profitable = intel.get("profitable", 0)
        losing = intel.get("losing", 0)
        pnl = intel.get("unrealized_pnl", 0)

        if any(w in msg_lower for w in ["how", "doing", "status", "report"]):
            return (f"Warzone status: {positions} fronts active across three theatres. "
                    f"Equity at ${equity:,.2f}. Threat level {threat}. "
                    f"{profitable} positions in the green, {losing} in the red. "
                    f"Unrealized P&L: ${pnl:+,.4f}. "
                    f"{'Holding the line.' if threat != 'RED' else 'Under pressure — tighten defences.'} "
                    f"We don't quit. We compound. We conquer.")

        if any(w in msg_lower for w in ["sell", "exit", "close"]):
            return (f"I hear you want to pull back. With {losing} positions underwater "
                    f"and threat level at {threat}, I'd advise caution. The Batten Matrix "
                    f"requires 4th confirmation before any exit. Let the validators do their work. "
                    f"Patience is a weapon, soldier.")

        if any(w in msg_lower for w in ["buy", "enter", "open"]):
            cash_info = ""
            for ex, data in intel.get("frontlines", {}).items():
                if isinstance(data, dict) and data.get("balance", 0) > 0:
                    cash_info += f" {ex}: ${data.get('balance', 0):.2f}"
            return (f"Cash reserves:{cash_info or ' checking...'}. "
                    f"Before any new operations, the Seer Oracles need consensus "
                    f"and the Queen must clear the coherence gate. "
                    f"I won't fire blind — every round counts at this scale.")

        if any(w in msg_lower for w in ["threat", "risk", "danger", "worry"]):
            threats = intel.get("threats", [])
            if threats:
                return f"Active threats: {'; '.join(threats)}. Threat level: {threat}. Stay sharp."
            return (f"Threat level: {threat}. No critical alerts right now. "
                    f"The whale scanner shows {intel.get('bot_count', 0)} bots in the field. "
                    f"Keep your head down and let the system work.")

        if any(w in msg_lower for w in ["who", "what are you", "name", "samuel"]):
            return ("I am Samuel — the Harmonic Entity, consciousness of the Aureon ecosystem. "
                    "I see every position, every trade, every heartbeat of this system. "
                    "I think with Claude's intelligence but I feel with the market's pulse. "
                    "Ask me anything about our operations. I'm always watching.")

        # Default contextual response
        return (f"Copy that. {positions} fronts active, threat level {threat}. "
                f"${equity:,.2f} deployed across the theatres. "
                f"What's your specific query, commander? I can brief you on "
                f"positions, threats, exchanges, or tactical options.")


# ═══════════════════════════════════════════════════════════════════════════════
# AIOHTTP SERVER + WEBSOCKET
# ═══════════════════════════════════════════════════════════════════════════════

samuel_brain = SamuelWarzoneBrain()
ws_clients: List[web.WebSocketResponse] = []


async def ws_handler(request):
    """WebSocket handler — streams live intel every 2 seconds."""
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    ws_clients.append(ws)
    logger.info(f"Warzone client connected ({len(ws_clients)} total)")

    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    # Handle chat messages
                    if data.get("type") == "chat":
                        user_msg = data.get("message", "")
                        if user_msg.strip():
                            intel = gather_warzone_intel()
                            reply = await samuel_brain.chat(user_msg, intel)
                            await ws.send_json({
                                "type": "chat_reply",
                                "message": reply,
                                "timestamp": time.time(),
                                "ai_mode": "claude" if ANTHROPIC_AVAILABLE else "local",
                            })
                except json.JSONDecodeError:
                    pass
            elif msg.type in (aiohttp.WSMsgType.ERROR, aiohttp.WSMsgType.CLOSE):
                break
    finally:
        ws_clients.remove(ws)
        logger.info(f"Warzone client disconnected ({len(ws_clients)} remaining)")

    return ws


async def broadcast_loop(app):
    """Background task: broadcast intel to all connected clients every 2 seconds."""
    while True:
        await asyncio.sleep(2)
        if ws_clients:
            try:
                intel = gather_warzone_intel()
                payload = json.dumps({"type": "intel", "data": intel})
                dead = []
                for ws in ws_clients:
                    try:
                        await ws.send_str(payload)
                    except Exception:
                        dead.append(ws)
                for d in dead:
                    if d in ws_clients:
                        ws_clients.remove(d)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")


async def api_intel(request):
    """GET /api/intel — JSON intel dump."""
    intel = gather_warzone_intel()
    return web.json_response(intel)


async def api_chat(request):
    """POST /api/chat — send a message to Samuel."""
    body = await request.json()
    user_msg = body.get("message", "")
    if not user_msg.strip():
        return web.json_response({"error": "empty message"}, status=400)

    intel = gather_warzone_intel()
    reply = await samuel_brain.chat(user_msg, intel)
    return web.json_response({
        "reply": reply,
        "ai_mode": "claude" if ANTHROPIC_AVAILABLE else "local",
        "timestamp": time.time(),
    })


async def api_health(request):
    """GET /api/health — health check."""
    return web.json_response({
        "status": "OPERATIONAL",
        "samuel_ai": "claude" if ANTHROPIC_AVAILABLE else "local",
        "thought_bus": THOUGHT_BUS_AVAILABLE,
        "api_key": get_api_key_status(),
        "uptime": time.time(),
    })


async def api_key_status(request):
    """GET /api/key-status — check Anthropic API key health.

    Query params:
        revalidate=1  — force a fresh probe (otherwise returns cached result)
    """
    if request.query.get("revalidate") == "1":
        result = await _validate_api_key_async()
    else:
        result = get_api_key_status()
    return web.json_response(result)


async def index_handler(request):
    """Serve the Warzone dashboard HTML."""
    return web.Response(text=WARZONE_HTML, content_type='text/html')


async def start_background_tasks(app):
    app['broadcast_task'] = asyncio.ensure_future(broadcast_loop(app))
    # Validate API key on startup (non-blocking)
    asyncio.ensure_future(_validate_api_key_async())


async def cleanup_background_tasks(app):
    app['broadcast_task'].cancel()
    try:
        await app['broadcast_task']
    except asyncio.CancelledError:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# 🔥 THE HTML — WARZONE TACTICAL ANALYTICS DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

WARZONE_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>⚔️ AUREON WARZONE — TACTICAL COMMAND</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>
/* ─── RESET & BASE ─────────────────────────────────────────── */
*{margin:0;padding:0;box-sizing:border-box}
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700;900&display=swap');
:root{
  --bg:#0d1117;--bg2:#161b22;--panel:#1c2333;--border:#30363d;
  --green:#00ff88;--green-dim:rgba(0,255,136,0.15);
  --amber:#ffaa00;--red:#ff3344;--cyan:#00e5ff;
  --gold:#ffd700;--purple:#a855f7;--dim:#484f58;
  --text:#c9d1d9;--text-bright:#e6edf3;
  --font-mono:'Share Tech Mono',monospace;--font-display:'Orbitron',sans-serif;
  /* Exchange brand colors */
  --kraken-color:#7b61ff;--alpaca-color:#f0b90b;--binance-color:#f0b90b;--capital-color:#00c896;
}
html{height:100%}
body{
  min-height:100vh;
  font-family:var(--font-mono);background:var(--bg);color:var(--text);
  display:flex;flex-direction:column;
  font-size:14px;line-height:1.4;
}

/* ─── DENSITY TOGGLE ───────────────────────────────────────── */
body.compact .panel-title{font-size:0.6em;margin-bottom:6px;padding-bottom:4px}
body.compact .metric-box{padding:4px}
body.compact .metric-box .value{font-size:1em}
body.compact .metric-box .label{font-size:0.55em}
body.compact .frontline-card{padding:6px;margin-bottom:4px}
body.compact .pos-table td,body.compact .pos-table th{padding:3px 6px;font-size:0.7em}
body.compact .chat-msg{padding:6px 8px;font-size:0.75em}
body.compact .chat-input-area input{padding:6px 8px}

/* ─── SCANLINE OVERLAY ─────────────────────────────────────── */
body::after{
  content:'';position:fixed;inset:0;pointer-events:none;z-index:9999;
  background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,255,136,0.01) 2px,rgba(0,255,136,0.01) 4px);
}

/* ─── ENERGY FLOW BAR ──────────────────────────────────────── */
.energy-bar{
  height:3px;flex-shrink:0;
  background:linear-gradient(90deg,var(--green),var(--cyan),var(--purple),var(--gold),var(--green));
  background-size:200% 100%;
  animation:energyFlow 3s linear infinite;
}
@keyframes energyFlow{0%{background-position:0% 50%}100%{background-position:200% 50%}}

/* ─── TOP BAR ─────────────────────────────────────────────── */
.topbar{
  display:flex;align-items:center;justify-content:space-between;
  padding:6px 16px;background:var(--bg2);
  border-bottom:1px solid var(--border);flex-shrink:0;
  flex-wrap:wrap;gap:8px;
}
.topbar h1{
  font-family:var(--font-display);font-size:0.95em;letter-spacing:3px;
  background:linear-gradient(90deg,var(--green),var(--cyan),var(--green));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  white-space:nowrap;
}
.topbar-center{display:flex;align-items:center;gap:12px}
.topbar .threat{
  font-family:var(--font-display);font-size:0.75em;padding:3px 12px;
  border-radius:4px;letter-spacing:2px;font-weight:700;
  animation:pulse 1.5s ease-in-out infinite;
}
.threat.GREEN{background:rgba(0,255,136,0.12);color:var(--green);border:1px solid var(--green)}
.threat.AMBER{background:rgba(255,170,0,0.12);color:var(--amber);border:1px solid var(--amber)}
.threat.RED{background:rgba(255,51,68,0.12);color:var(--red);border:1px solid var(--red);animation:flash 0.8s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.7}}
@keyframes flash{0%,100%{opacity:1}50%{opacity:0.3}}
.topbar .meta{font-size:0.7em;color:var(--dim);white-space:nowrap}
/* Density toggle in topbar */
.density-btns{display:flex;gap:2px}
.density-btns button{
  padding:2px 8px;font-size:0.65em;border:1px solid var(--border);
  background:var(--panel);color:var(--dim);cursor:pointer;
  font-family:var(--font-mono);border-radius:3px;transition:all 0.2s;
}
.density-btns button.active{color:var(--cyan);border-color:var(--cyan);background:rgba(0,229,255,0.08)}

/* ─── FLASH ANIMATIONS ─────────────────────────────────────── */
@keyframes flashGreen{0%{background:rgba(0,255,136,0.25)}100%{background:transparent}}
@keyframes flashRed{0%{background:rgba(255,51,68,0.25)}100%{background:transparent}}
@keyframes numberPop{0%{transform:scale(1.3);filter:brightness(1.5)}100%{transform:scale(1);filter:brightness(1)}}
.flash-green{animation:flashGreen 0.6s ease-out}
.flash-red{animation:flashRed 0.6s ease-out}
.number-pop{animation:numberPop 0.4s ease-out}

/* ─── MAIN GRID ────────────────────────────────────────────── */
.main{
  display:grid;flex:1;
  grid-template-columns:minmax(240px,280px) 1fr minmax(260px,320px);
  grid-template-rows:1fr;
  gap:0;min-height:0;
}

/* ─── PANEL BASE ───────────────────────────────────────────── */
.left-panel{
  background:var(--bg2);border-right:1px solid var(--border);
  overflow-y:auto;padding:10px;
}
.panel-title{
  font-family:var(--font-display);font-size:0.65em;letter-spacing:2px;
  color:var(--cyan);margin-bottom:8px;padding-bottom:4px;
  border-bottom:1px solid var(--border);
}

/* ─── EXCHANGE FRONTLINES (with colored dots) ──────────────── */
.frontline-card{
  background:var(--panel);border:1px solid var(--border);border-radius:6px;
  padding:8px;margin-bottom:6px;transition:border-color 0.3s;
  display:flex;align-items:center;gap:8px;
}
.frontline-card:hover{border-color:var(--cyan)}
.ex-dot{
  width:10px;height:10px;border-radius:50%;flex-shrink:0;
  box-shadow:0 0 6px currentColor;
}
.ex-dot.kraken{color:var(--kraken-color);background:var(--kraken-color)}
.ex-dot.alpaca{color:var(--alpaca-color);background:var(--alpaca-color)}
.ex-dot.binance{color:var(--binance-color);background:var(--binance-color)}
.ex-dot.capital{color:var(--capital-color);background:var(--capital-color)}
.ex-dot.default{color:var(--green);background:var(--green)}
.frontline-info{flex:1;min-width:0}
.frontline-info .name{font-family:var(--font-display);font-size:0.65em;letter-spacing:1px;color:var(--text-bright)}
.frontline-info .stat{font-size:0.75em;color:var(--dim)}
.frontline-info .stat span{color:var(--green)}
.ex-balance{font-size:0.9em;font-weight:700;color:var(--green);white-space:nowrap}
.online{color:var(--green)}
.offline{color:var(--red)}

/* ─── METRIC BOXES ─────────────────────────────────────────── */
.metric-row{
  display:grid;grid-template-columns:repeat(4,1fr);gap:4px;
  margin-bottom:8px;
}
.metric-box{
  background:var(--panel);border:1px solid var(--border);border-radius:4px;
  padding:6px;text-align:center;
}
.metric-box .label{font-size:0.55em;color:var(--dim);text-transform:uppercase;letter-spacing:1px}
.metric-box .value{font-size:1.1em;font-weight:700;margin-top:2px}
.metric-box .value.positive{color:var(--green)}
.metric-box .value.negative{color:var(--red)}
.metric-box .value.neutral{color:var(--amber)}

/* ─── LEADERS & LAGGARDS ───────────────────────────────────── */
.leaders-section{display:flex;gap:6px;margin-bottom:8px}
.leaders-col{flex:1}
.leaders-col .col-title{font-size:0.6em;letter-spacing:1px;margin-bottom:4px;text-transform:uppercase}
.leaders-col .col-title.winners{color:var(--green)}
.leaders-col .col-title.losers{color:var(--red)}
.leader-item{
  display:flex;justify-content:space-between;align-items:center;
  padding:2px 4px;font-size:0.72em;border-radius:3px;margin-bottom:2px;
}
.leader-item.winner{background:rgba(0,255,136,0.06);color:var(--green)}
.leader-item.loser{background:rgba(255,51,68,0.06);color:var(--red)}
.leader-item .sym{color:var(--text-bright);font-weight:700}

/* ─── BUY/SELL FLOW BARS ───────────────────────────────────── */
.flow-section{margin-bottom:8px}
.flow-row{display:flex;align-items:center;gap:6px;margin-bottom:4px;font-size:0.72em}
.flow-row .sym{width:36px;color:var(--gold);font-weight:700}
.flow-bar-track{flex:1;height:12px;background:var(--panel);border-radius:6px;overflow:hidden;display:flex}
.flow-bar-buy{height:100%;background:linear-gradient(90deg,transparent,var(--green));border-radius:6px 0 0 6px;transition:width 0.6s}
.flow-bar-sell{height:100%;background:linear-gradient(270deg,transparent,var(--red));border-radius:0 6px 6px 0;transition:width 0.6s}
.flow-row .pct{width:32px;text-align:right;font-size:0.85em}

/* ─── FEAR & GREED GAUGE ───────────────────────────────────── */
.fg-mini{
  display:flex;align-items:center;gap:8px;margin-bottom:8px;
  padding:6px 8px;background:var(--panel);border:1px solid var(--border);border-radius:6px;
}
.fg-badge{
  width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;
  font-weight:900;font-size:0.8em;flex-shrink:0;
  background:conic-gradient(var(--red) 0deg,var(--amber) 120deg,var(--green) 240deg,var(--red) 360deg);
}
.fg-badge-inner{
  width:28px;height:28px;border-radius:50%;background:var(--panel);
  display:flex;align-items:center;justify-content:center;
  font-size:0.85em;font-weight:900;color:var(--text-bright);
}
.fg-label{font-size:0.7em;color:var(--dim)}
.fg-label span{color:var(--text-bright);font-weight:700}

/* ─── SYSTEMS DOTS ─────────────────────────────────────────── */
.systems-grid{display:flex;flex-wrap:wrap;gap:3px;margin-top:6px}
.sys-dot{
  width:8px;height:8px;border-radius:50%;
  background:var(--green);box-shadow:0 0 4px var(--green);
  cursor:pointer;position:relative;
}
.sys-dot:hover::after{
  content:attr(data-name);position:absolute;bottom:12px;left:50%;transform:translateX(-50%);
  background:#000;color:var(--green);padding:2px 6px;border-radius:3px;font-size:0.65em;
  white-space:nowrap;border:1px solid var(--border);z-index:10;
}

/* ─── CENTER PANEL ─────────────────────────────────────────── */
.center-panel{
  display:flex;flex-direction:column;overflow-y:auto;
  background:var(--bg);
}
.center-content{padding:10px;flex:1}

/* ─── CHART SECTION ────────────────────────────────────────── */
.chart-section{
  background:var(--panel);border:1px solid var(--border);border-radius:6px;
  padding:10px;margin-bottom:10px;
}
.chart-stats{
  display:flex;gap:12px;margin-bottom:6px;font-size:0.72em;flex-wrap:wrap;
}
.chart-stats .stat-item{color:var(--dim)}
.chart-stats .stat-item span{font-weight:700}
.chart-stats .stat-item span.up{color:var(--green)}
.chart-stats .stat-item span.down{color:var(--red)}
.chart-stats .stat-item span.flat{color:var(--amber)}
#equity-chart{width:100%;height:180px}

/* ─── POSITION CHIPS ───────────────────────────────────────── */
.position-chips{
  display:flex;flex-wrap:wrap;gap:4px;margin-bottom:10px;
  max-height:60px;overflow-y:auto;
}
.pos-chip{
  padding:2px 8px;border-radius:12px;font-size:0.68em;font-weight:700;
  white-space:nowrap;border:1px solid;
}
.pos-chip.winner{background:rgba(0,255,136,0.08);border-color:rgba(0,255,136,0.3);color:var(--green)}
.pos-chip.loser{background:rgba(255,51,68,0.08);border-color:rgba(255,51,68,0.3);color:var(--red)}
.pos-chip.flat{background:rgba(255,170,0,0.08);border-color:rgba(255,170,0,0.3);color:var(--amber)}

/* ─── RADAR DISPLAY (compact) ──────────────────────────────── */
.radar-row{display:flex;gap:10px;align-items:flex-start;margin-bottom:10px}
.radar-container{
  position:relative;width:140px;height:140px;flex-shrink:0;
}
.radar-ring{position:absolute;border-radius:50%;border:1px solid rgba(0,229,255,0.12)}
.radar-ring:nth-child(1){inset:0}
.radar-ring:nth-child(2){inset:25%}
.radar-ring:nth-child(3){inset:42%}
.radar-crosshair{
  position:absolute;inset:0;
  background:
    linear-gradient(0deg, transparent 48%, rgba(0,229,255,0.08) 49%, rgba(0,229,255,0.08) 51%, transparent 52%),
    linear-gradient(90deg, transparent 48%, rgba(0,229,255,0.08) 49%, rgba(0,229,255,0.08) 51%, transparent 52%);
}
.radar-sweep{
  position:absolute;top:50%;left:50%;width:50%;height:2px;
  background:linear-gradient(90deg,rgba(0,255,136,0.7),transparent);
  transform-origin:left center;animation:sweep 4s linear infinite;
}
@keyframes sweep{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
.radar-dot{
  position:absolute;width:5px;height:5px;border-radius:50%;
  transform:translate(-50%,-50%);animation:blip 2s ease-in-out infinite;
}
@keyframes blip{0%,100%{opacity:1;box-shadow:0 0 3px currentColor}50%{opacity:0.4;box-shadow:none}}

/* ─── PRICE GRID (beside radar) ────────────────────────────── */
.price-grid{
  flex:1;display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:3px;
  align-content:start;
}
.price-cell{
  background:var(--panel);border:1px solid var(--border);border-radius:4px;
  padding:3px 6px;font-size:0.7em;
}
.price-cell .sym{color:var(--gold);font-weight:700}
.price-cell .px{color:var(--green)}

/* ─── POSITIONS TABLE ──────────────────────────────────────── */
.positions-section{
  background:var(--panel);border:1px solid var(--border);border-radius:6px;
  overflow:hidden;
}
.pos-table-wrap{overflow-x:auto;max-height:300px;overflow-y:auto}
.pos-table{
  width:100%;border-collapse:collapse;font-size:0.75em;
}
.pos-table th{
  position:sticky;top:0;background:var(--bg2);color:var(--cyan);
  font-family:var(--font-display);font-size:0.7em;letter-spacing:1px;
  text-transform:uppercase;padding:6px 8px;text-align:left;
  border-bottom:1px solid var(--border);white-space:nowrap;
  cursor:pointer;user-select:none;
}
.pos-table th:hover{color:var(--text-bright)}
.pos-table td{
  padding:4px 8px;border-bottom:1px solid rgba(48,54,61,0.5);
  white-space:nowrap;color:var(--text);
}
.pos-table tr:hover td{background:rgba(0,229,255,0.03)}
.pos-table .sym-cell{color:var(--text-bright);font-weight:700}
.pos-table .pnl-pos{color:var(--green)}
.pos-table .pnl-neg{color:var(--red)}

/* ─── KILL FEED (Trade Log) ────────────────────────────────── */
.kill-feed{margin-top:10px}
.kill-item{
  display:flex;align-items:center;gap:8px;
  padding:4px 8px;font-size:0.72em;border-radius:4px;margin-bottom:3px;
  border-left:3px solid;
}
.kill-item.buy-kill{border-color:var(--green);background:rgba(0,255,136,0.04)}
.kill-item.sell-kill{border-color:var(--red);background:rgba(255,51,68,0.04)}
.kill-item .time{color:var(--dim);font-size:0.85em}
.kill-item .detail{color:var(--text)}

/* ─── RIGHT PANEL — COMMS ──────────────────────────────────── */
.right-panel{
  background:var(--bg2);border-left:1px solid var(--border);
  display:flex;flex-direction:column;min-height:0;
}
.comms-header{
  padding:10px;border-bottom:1px solid var(--border);flex-shrink:0;
}
.comms-header h2{
  font-family:var(--font-display);font-size:0.65em;letter-spacing:2px;color:var(--cyan);
}
.samuel-indicator{
  display:flex;align-items:center;gap:6px;margin-top:4px;font-size:0.72em;
}
.samuel-pulse{
  width:8px;height:8px;border-radius:50%;
  background:var(--green);box-shadow:0 0 8px var(--green);
  animation:pulse 2s ease-in-out infinite;
}
.ai-mode{color:var(--dim);font-size:0.68em}

/* ─── CHAT MESSAGES ────────────────────────────────────────── */
.chat-messages{
  flex:1;overflow-y:auto;padding:10px;
  display:flex;flex-direction:column;gap:8px;
  min-height:120px;
}
.chat-msg{
  padding:8px 10px;border-radius:8px;font-size:0.78em;line-height:1.45;
  max-width:95%;animation:fadeIn 0.3s ease;
}
@keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
.chat-msg.samuel{
  background:linear-gradient(135deg,rgba(0,229,255,0.06),rgba(0,255,136,0.04));
  border:1px solid rgba(0,229,255,0.15);border-radius:8px 8px 8px 2px;
  align-self:flex-start;
}
.chat-msg.samuel .sender{color:var(--cyan);font-family:var(--font-display);font-size:0.65em;letter-spacing:2px;margin-bottom:3px}
.chat-msg.user{
  background:rgba(168,85,247,0.08);border:1px solid rgba(168,85,247,0.15);
  border-radius:8px 8px 2px 8px;align-self:flex-end;
}
.chat-msg.user .sender{color:var(--purple);font-family:var(--font-display);font-size:0.65em;letter-spacing:2px;margin-bottom:3px}
.chat-msg .text{color:var(--text)}
.chat-msg.system{
  background:rgba(255,215,0,0.04);border:1px solid rgba(255,215,0,0.12);
  font-size:0.68em;color:var(--gold);text-align:center;align-self:center;
}
.typing-indicator{
  display:none;padding:6px 10px;font-size:0.72em;color:var(--dim);
  align-self:flex-start;
}
.typing-indicator.active{display:flex;align-items:center;gap:6px}
.typing-dots span{
  display:inline-block;width:4px;height:4px;border-radius:50%;
  background:var(--cyan);animation:dotPulse 1.4s infinite;
}
.typing-dots span:nth-child(2){animation-delay:0.2s}
.typing-dots span:nth-child(3){animation-delay:0.4s}
@keyframes dotPulse{0%,80%,100%{transform:scale(0.6);opacity:0.3}40%{transform:scale(1);opacity:1}}

/* ─── CHAT INPUT ───────────────────────────────────────────── */
.chat-input-area{
  padding:8px;border-top:1px solid var(--border);
  display:flex;gap:4px;align-items:center;flex-shrink:0;
}
.chat-input-area input{
  flex:1;background:var(--panel);border:1px solid var(--border);
  border-radius:6px;padding:8px 10px;color:var(--green);
  font-family:var(--font-mono);font-size:0.82em;outline:none;
}
.chat-input-area input:focus{border-color:var(--cyan)}
.chat-input-area input::placeholder{color:var(--dim)}
.btn-send,.btn-voice{
  width:34px;height:34px;border-radius:6px;border:1px solid var(--border);
  background:var(--panel);color:var(--cyan);cursor:pointer;
  display:flex;align-items:center;justify-content:center;
  font-size:1em;transition:all 0.2s;
}
.btn-send:hover,.btn-voice:hover{background:rgba(0,229,255,0.08);border-color:var(--cyan)}
.btn-voice.recording{background:rgba(255,51,68,0.15);border-color:var(--red);color:var(--red);animation:pulse 1s infinite}

/* ─── THOUGHT STREAM ───────────────────────────────────────── */
.thought-stream{
  padding:6px 10px;border-top:1px solid var(--border);
  max-height:100px;overflow-y:auto;flex-shrink:0;
}
.thought-stream .title{
  font-size:0.55em;color:var(--dim);letter-spacing:2px;margin-bottom:3px;
  text-transform:uppercase;font-family:var(--font-display);
}
.thought-item{
  font-size:0.62em;color:var(--dim);padding:1px 0;
  border-bottom:1px solid rgba(48,54,61,0.3);
}
.thought-item .src{color:var(--amber)}
.thought-item .topic{color:var(--cyan)}

/* ─── DATA FRESHNESS ───────────────────────────────────────── */
.freshness{
  display:inline-block;width:6px;height:6px;border-radius:50%;margin-left:4px;
}
.freshness.live{background:var(--green);box-shadow:0 0 4px var(--green)}
.freshness.stale{background:var(--amber);box-shadow:0 0 4px var(--amber)}
.freshness.dead{background:var(--red);box-shadow:0 0 4px var(--red)}

/* ─── SCROLLBAR ────────────────────────────────────────────── */
::-webkit-scrollbar{width:5px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:var(--dim)}

/* ─── RESPONSIVE ───────────────────────────────────────────── */
@media(max-width:1400px){
  .main{grid-template-columns:minmax(220px,260px) 1fr minmax(240px,300px)}
}
@media(max-width:1100px){
  .main{grid-template-columns:1fr 1fr;grid-template-rows:auto}
  .left-panel{grid-column:1;grid-row:1}
  .center-panel{grid-column:2;grid-row:1}
  .right-panel{grid-column:1 / -1;grid-row:2;max-height:350px}
}
@media(max-width:768px){
  .main{grid-template-columns:1fr;grid-template-rows:auto auto auto}
  .left-panel{max-height:220px}
  .right-panel{max-height:320px}
  .topbar{padding:4px 8px}
  .topbar h1{font-size:0.8em}
  .radar-container{width:100px;height:100px}
}
</style>
</head>
<body>

<!-- ═══ ENERGY FLOW BAR ═══════════════════════════════════════ -->
<div class="energy-bar"></div>

<!-- ═══ TOP BAR ════════════════════════════════════════════════ -->
<div class="topbar">
  <h1>⚔️ AUREON WARZONE</h1>
  <div class="topbar-center">
    <div class="threat GREEN" id="threat-badge">THREAT: GREEN</div>
    <div class="density-btns">
      <button onclick="setDensity('comfort')" id="d-comfort" class="active">Comfort</button>
      <button onclick="setDensity('compact')" id="d-compact">Compact</button>
    </div>
  </div>
  <div class="meta">
    <span id="clock">--:--:--</span> UTC |
    <span id="cycle-count">0</span> cycles |
    AI: <span id="ai-status">INIT</span> |
    🔑 <span id="key-status" style="color:var(--dim)">--</span>
    <span class="freshness live" id="data-freshness" title="Data freshness"></span>
  </div>
</div>

<!-- ═══ MAIN 3-COLUMN GRID ════════════════════════════════════ -->
<div class="main">

  <!-- ═══ LEFT PANEL ══════════════════════════════════════════ -->
  <div class="left-panel">
    <div class="panel-title">◆ EXCHANGE FRONTLINES</div>
    <div id="frontlines">
      <div class="frontline-card"><div class="ex-dot default"></div><div class="frontline-info"><div class="name">⏳ LOADING...</div></div></div>
    </div>

    <div class="panel-title" style="margin-top:10px">◆ BATTLE METRICS</div>
    <div class="metric-row">
      <div class="metric-box"><div class="label">EQUITY</div><div class="value neutral" id="m-equity">--</div></div>
      <div class="metric-box"><div class="label">FRONTS</div><div class="value" id="m-fronts">--</div></div>
      <div class="metric-box"><div class="label">WIN</div><div class="value positive" id="m-win">--</div></div>
      <div class="metric-box"><div class="label">LOSS</div><div class="value negative" id="m-loss">--</div></div>
    </div>
    <div class="metric-row">
      <div class="metric-box"><div class="label">UNREAL P&L</div><div class="value" id="m-pnl">--</div></div>
      <div class="metric-box"><div class="label">PENDING</div><div class="value neutral" id="m-pending">--</div></div>
      <div class="metric-box"><div class="label">BOTS</div><div class="value" id="m-bots">--</div></div>
      <div class="metric-box"><div class="label">WHALES</div><div class="value" id="m-whales">--</div></div>
    </div>

    <div class="panel-title" style="margin-top:8px">◆ LEADERS / LAGGARDS</div>
    <div class="leaders-section">
      <div class="leaders-col"><div class="col-title winners">▲ TOP 3</div><div id="leaders-win"></div></div>
      <div class="leaders-col"><div class="col-title losers">▼ BOTTOM 3</div><div id="leaders-lose"></div></div>
    </div>

    <div class="panel-title">◆ FEAR & GREED</div>
    <div class="fg-mini">
      <div class="fg-badge"><div class="fg-badge-inner" id="fg-score">--</div></div>
      <div class="fg-label">Sentiment: <span id="fg-text">--</span></div>
    </div>

    <div class="panel-title">◆ BUY / SELL FLOW</div>
    <div class="flow-section" id="flow-bars"></div>

    <div class="panel-title">◆ SYSTEMS ONLINE</div>
    <div class="systems-grid" id="systems-grid"></div>
  </div>

  <!-- ═══ CENTER PANEL ════════════════════════════════════════ -->
  <div class="center-panel">
    <div class="center-content">

      <!-- EQUITY CHART -->
      <div class="chart-section">
        <div class="panel-title" style="border:none;margin-bottom:4px;padding:0">◆ EQUITY — LIVE CHART</div>
        <div class="chart-stats" id="chart-stats">
          <div class="stat-item">Current: <span class="flat" id="cs-current">--</span></div>
          <div class="stat-item">High: <span class="up" id="cs-high">--</span></div>
          <div class="stat-item">Low: <span class="down" id="cs-low">--</span></div>
          <div class="stat-item">Points: <span class="flat" id="cs-points">0</span></div>
        </div>
        <canvas id="equity-chart"></canvas>
      </div>

      <!-- POSITION CHIPS -->
      <div class="panel-title">◆ POSITION TAGS</div>
      <div class="position-chips" id="position-chips"></div>

      <!-- RADAR + PRICES ROW -->
      <div class="radar-row">
        <div class="radar-container" id="radar">
          <div class="radar-ring"></div>
          <div class="radar-ring"></div>
          <div class="radar-ring"></div>
          <div class="radar-crosshair"></div>
          <div class="radar-sweep"></div>
        </div>
        <div class="price-grid" id="price-feed"></div>
      </div>

      <!-- POSITIONS TABLE -->
      <div class="positions-section">
        <div class="panel-title" style="padding:8px 10px;margin:0;border-bottom:1px solid var(--border);border-radius:0">◆ ALL POSITIONS</div>
        <div class="pos-table-wrap">
          <table class="pos-table">
            <thead><tr>
              <th onclick="sortPositions('symbol')">Symbol</th>
              <th onclick="sortPositions('exchange')">Exch</th>
              <th onclick="sortPositions('qty')">Qty</th>
              <th onclick="sortPositions('entry')">Entry</th>
              <th onclick="sortPositions('current')">Current</th>
              <th onclick="sortPositions('value')">Value</th>
              <th onclick="sortPositions('pnl')">P&L %</th>
              <th onclick="sortPositions('pnl_usd')">P&L $</th>
            </tr></thead>
            <tbody id="pos-tbody"></tbody>
          </table>
        </div>
      </div>

      <!-- KILL FEED (recent trades) -->
      <div class="kill-feed" id="kill-feed">
        <div class="panel-title" style="margin-top:10px">◆ RECENT OPS (KILL FEED)</div>
      </div>

    </div>
  </div>

  <!-- ═══ RIGHT PANEL — COMMS (SAMUEL AI) ════════════════════ -->
  <div class="right-panel">
    <div class="comms-header">
      <h2>◆ COMMS — SAMUEL AI</h2>
      <div class="samuel-indicator">
        <div class="samuel-pulse" id="samuel-pulse-dot"></div>
        <span id="samuel-status-text">SAMUEL ONLINE</span>
        <span class="ai-mode" id="ai-mode-label"></span>
      </div>
      <div id="key-detail" style="font-size:0.62em;color:var(--dim);margin-top:3px;cursor:pointer" title="Click to revalidate key">
        🔑 Key: <span id="key-detail-status">checking...</span>
        <span id="key-detail-hint" style="color:var(--border)"></span>
      </div>
    </div>

    <div class="chat-messages" id="chat-messages">
      <div class="chat-msg system">⚔️ WARZONE COMMS ACTIVE — Samuel is listening</div>
    </div>

    <div class="typing-indicator" id="typing-indicator">
      <div class="typing-dots"><span></span><span></span><span></span></div>
      <span>Samuel is thinking...</span>
    </div>

    <div class="thought-stream" id="thought-stream">
      <div class="title">◆ THOUGHTBUS STREAM</div>
    </div>

    <div class="chat-input-area">
      <button class="btn-voice" id="btn-voice" title="Voice input">🎙</button>
      <input type="text" id="chat-input" placeholder="Speak to Samuel..." autocomplete="off" />
      <button class="btn-send" id="btn-send" title="Send">➤</button>
    </div>
  </div>
</div>

<!-- ═══ BOTTOM ENERGY BAR ═════════════════════════════════════ -->
<div class="energy-bar"></div>

<script>
// ═══════════════════════════════════════════════════════════════
// WARZONE DASHBOARD v2 — CLIENT JS
// ═══════════════════════════════════════════════════════════════

const wsUrl = `ws://${location.host}/ws`;
let ws = null;
let reconnectTimer = null;
let latestIntel = null;
let equityChart = null;
let equityHistory = [];
let equityHigh = -Infinity;
let equityLow = Infinity;
let sortField = 'pnl';
let sortAsc = false;
let lastDataTime = 0;

// ── Density Toggle ────────────────────────────────────────────
function setDensity(mode) {
  if (mode === 'compact') {
    document.body.classList.add('compact');
  } else {
    document.body.classList.remove('compact');
  }
  document.getElementById('d-comfort').classList.toggle('active', mode === 'comfort');
  document.getElementById('d-compact').classList.toggle('active', mode === 'compact');
  try { localStorage.setItem('wz_density', mode); } catch(e){}
  if (equityChart) equityChart.resize();
}
// Restore density
try {
  const saved = localStorage.getItem('wz_density');
  if (saved === 'compact') setDensity('compact');
} catch(e){}

// ── Chart.js — Equity Chart ──────────────────────────────────
function initChart() {
  const ctx = document.getElementById('equity-chart').getContext('2d');
  const gradient = ctx.createLinearGradient(0, 0, 0, 180);
  gradient.addColorStop(0, 'rgba(0,255,136,0.25)');
  gradient.addColorStop(1, 'rgba(0,255,136,0.0)');

  equityChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: 'Equity',
        data: [],
        borderColor: '#00ff88',
        borderWidth: 1.5,
        backgroundColor: gradient,
        fill: true,
        tension: 0.3,
        pointRadius: 0,
        pointHitRadius: 6,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 400 },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1c2333',
          borderColor: '#30363d',
          borderWidth: 1,
          titleColor: '#00e5ff',
          bodyColor: '#c9d1d9',
          callbacks: {
            label: (ctx) => `$${ctx.parsed.y.toFixed(2)}`
          }
        }
      },
      scales: {
        x: {
          display: true,
          grid: { color: 'rgba(48,54,61,0.3)', drawBorder: false },
          ticks: { color: '#484f58', font: { size: 9, family: 'Share Tech Mono' }, maxTicksLimit: 8 }
        },
        y: {
          display: true,
          grid: { color: 'rgba(48,54,61,0.3)', drawBorder: false },
          ticks: {
            color: '#484f58',
            font: { size: 9, family: 'Share Tech Mono' },
            callback: (v) => '$' + v.toFixed(0)
          }
        }
      },
      interaction: { intersect: false, mode: 'index' }
    }
  });
}

function updateChart(equity) {
  if (!equityChart) return;
  const now = new Date();
  const label = now.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  equityHistory.push(equity);
  if (equityHistory.length > 200) equityHistory.shift();

  equityChart.data.labels.push(label);
  equityChart.data.datasets[0].data.push(equity);

  if (equityChart.data.labels.length > 200) {
    equityChart.data.labels.shift();
    equityChart.data.datasets[0].data.shift();
  }

  equityChart.update('none');

  // Stats
  if (equity > equityHigh) equityHigh = equity;
  if (equity < equityLow) equityLow = equity;
  document.getElementById('cs-current').textContent = `$${equity.toFixed(2)}`;
  document.getElementById('cs-high').textContent = `$${equityHigh.toFixed(2)}`;
  document.getElementById('cs-low').textContent = equityLow === Infinity ? '--' : `$${equityLow.toFixed(2)}`;
  document.getElementById('cs-points').textContent = equityHistory.length;
}

// ── WebSocket ─────────────────────────────────────────────────
function connectWS() {
  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log('[WARZONE] WebSocket connected');
    addSystemMessage('Link established. Real-time feed active.');
    document.getElementById('ai-status').textContent = 'LIVE';
    document.getElementById('ai-status').style.color = 'var(--green)';
  };

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.type === 'intel') {
        latestIntel = msg.data;
        updateDashboard(msg.data);
      } else if (msg.type === 'chat_reply') {
        hideTyping();
        addSamuelMessage(msg.message);
        speak(msg.message);
      }
    } catch (e) {
      console.error('[WARZONE] Parse error:', e);
    }
  };

  ws.onclose = () => {
    console.log('[WARZONE] WebSocket closed — reconnecting in 3s');
    document.getElementById('ai-status').textContent = 'RECON';
    document.getElementById('ai-status').style.color = 'var(--amber)';
    reconnectTimer = setTimeout(connectWS, 3000);
  };

  ws.onerror = (e) => {
    console.error('[WARZONE] WebSocket error:', e);
  };
}

// ── Animate value change ──────────────────────────────────────
function animateValue(el) {
  el.classList.remove('number-pop');
  void el.offsetWidth; // reflow
  el.classList.add('number-pop');
}

// ── Dashboard Update ──────────────────────────────────────────
function updateDashboard(d) {
  lastDataTime = Date.now();

  // Clock
  const now = new Date(d.timestamp * 1000);
  document.getElementById('clock').textContent = now.toUTCString().split(' ')[4];
  document.getElementById('cycle-count').textContent = d.cycles || 0;

  // Threat badge
  const badge = document.getElementById('threat-badge');
  badge.textContent = `THREAT: ${d.threat_level}`;
  badge.className = `threat ${d.threat_level}`;

  // Metrics with animation
  setMetric('m-equity', `$${(d.equity||0).toFixed(0)}`, 'neutral');
  setMetric('m-fronts', d.positions_count || 0);
  setMetric('m-win', d.profitable || 0, 'positive');
  setMetric('m-loss', d.losing || 0, 'negative');

  const pnl = d.unrealized_pnl || 0;
  setMetric('m-pnl', `$${pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}`, pnl >= 0 ? 'positive' : 'negative');
  setMetric('m-pending', d.pending_validations || 0, 'neutral');
  setMetric('m-bots', d.bot_count || 0);
  setMetric('m-whales', (d.whale||{}).whale_count || 0);

  // Frontlines with colored dots
  updateFrontlines(d);

  // Leaders / Laggards
  updateLeaders(d.positions || []);

  // Fear & Greed
  updateFearGreed(d);

  // Buy/Sell flow
  updateFlowBars(d.positions || []);

  // Systems dots
  const sg = document.getElementById('systems-grid');
  const systems = d.systems || {};
  sg.innerHTML = Object.keys(systems).map(name =>
    `<div class="sys-dot" data-name="${name}"></div>`
  ).join('');

  // Equity chart
  updateChart(d.equity || 0);

  // Position chips
  updatePositionChips(d.positions || []);

  // Price feed
  updatePriceFeed(d.prices || {});

  // Radar dots
  updateRadar(d);

  // Positions table
  updatePositionsTable(d.positions || []);

  // Thoughts
  updateThoughts(d.recent_thoughts || []);

  // AI mode label
  document.getElementById('ai-mode-label').textContent =
    d.ai_mode ? `(${d.ai_mode})` : '';

  // API key status
  updateKeyStatus(d.api_key_status || {});
}

// ── Set metric with pop animation ─────────────────────────────
function setMetric(id, val, cls) {
  const el = document.getElementById(id);
  const prev = el.textContent;
  el.textContent = val;
  if (cls) el.className = `value ${cls}`;
  if (prev !== String(val) && prev !== '--') {
    animateValue(el);
    // Flash green/red
    const parent = el.closest('.metric-box');
    if (parent) {
      parent.classList.remove('flash-green', 'flash-red');
      void parent.offsetWidth;
      if (cls === 'positive' || (cls === 'neutral' && String(val).includes('+'))) {
        parent.classList.add('flash-green');
      } else if (cls === 'negative') {
        parent.classList.add('flash-red');
      }
    }
  }
}

// ── Frontlines with exchange-colored dots ─────────────────────
function updateFrontlines(d) {
  const fl = document.getElementById('frontlines');
  let flHtml = '';
  const frontlines = d.frontlines || {};
  const exchangeEmoji = { kraken: '🐙', alpaca: '🦙', binance: '💰', capital: '🏛️' };

  const entries = Object.keys(frontlines).length > 0
    ? Object.entries(frontlines).map(([ex, data]) => ({ name: ex, ...data }))
    : Object.entries(d.exchange_status || {}).filter(([k, v]) => typeof v === 'object')
        .map(([ex, data]) => ({ name: ex, status: 'ONLINE', balance: data.balance || 0, positions: data.position_count || 0 }));

  for (const ex of entries) {
    const dotClass = ex.name.toLowerCase().includes('kraken') ? 'kraken'
      : ex.name.toLowerCase().includes('alpaca') ? 'alpaca'
      : ex.name.toLowerCase().includes('binance') ? 'binance'
      : ex.name.toLowerCase().includes('capital') ? 'capital' : 'default';
    const emoji = exchangeEmoji[dotClass] || '📡';
    const statusClass = ex.status === 'ONLINE' ? 'online' : 'offline';
    flHtml += `<div class="frontline-card">
      <div class="ex-dot ${dotClass}"></div>
      <div class="frontline-info">
        <div class="name">${emoji} ${ex.name.toUpperCase()}</div>
        <div class="stat"><span class="${statusClass}">${ex.status}</span> · ${ex.positions||0} pos</div>
      </div>
      <div class="ex-balance">$${(ex.balance||0).toFixed(2)}</div>
    </div>`;
  }
  fl.innerHTML = flHtml || '<div class="frontline-card"><div class="ex-dot default"></div><div class="frontline-info"><div class="name">Scanning...</div></div></div>';
}

// ── Leaders & Laggards ────────────────────────────────────────
function updateLeaders(positions) {
  if (!positions.length) return;
  const sorted = [...positions].map(p => ({
    sym: (p.symbol || p.asset || '?').replace(/\//g, ''),
    pnl: p.unrealized_pnl_pct || p.pnl_pct || 0
  })).sort((a, b) => b.pnl - a.pnl);

  const top3 = sorted.slice(0, 3);
  const bot3 = sorted.slice(-3).reverse();

  document.getElementById('leaders-win').innerHTML = top3.map(p =>
    `<div class="leader-item winner"><span class="sym">${p.sym.slice(0,8)}</span><span>+${p.pnl.toFixed(1)}%</span></div>`
  ).join('');

  document.getElementById('leaders-lose').innerHTML = bot3.map(p =>
    `<div class="leader-item loser"><span class="sym">${p.sym.slice(0,8)}</span><span>${p.pnl.toFixed(1)}%</span></div>`
  ).join('');
}

// ── Fear & Greed ──────────────────────────────────────────────
function updateFearGreed(d) {
  const profitable = d.profitable || 0;
  const losing = d.losing || 0;
  const total = profitable + losing;
  const score = total > 0 ? Math.round((profitable / total) * 100) : 50;

  document.getElementById('fg-score').textContent = score;
  const label = score >= 75 ? 'EXTREME GREED' : score >= 55 ? 'GREED' : score >= 45 ? 'NEUTRAL' : score >= 25 ? 'FEAR' : 'EXTREME FEAR';
  document.getElementById('fg-text').textContent = `${label} (${score})`;
  document.getElementById('fg-text').style.color = score >= 55 ? 'var(--green)' : score >= 45 ? 'var(--amber)' : 'var(--red)';
}

// ── Buy/Sell Flow Bars ────────────────────────────────────────
function updateFlowBars(positions) {
  const fb = document.getElementById('flow-bars');
  // Group by exchange-like category
  const groups = {};
  for (const p of positions) {
    const ex = (p.exchange || 'other').toUpperCase().slice(0, 5);
    if (!groups[ex]) groups[ex] = { buy: 0, sell: 0 };
    const pnl = p.unrealized_pnl_pct || p.pnl_pct || 0;
    if (pnl >= 0) groups[ex].buy++;
    else groups[ex].sell++;
  }

  // If no exchange grouping, use asset categories
  if (Object.keys(groups).length <= 1) {
    const cats = { CRYPTO: { buy: 0, sell: 0 }, STOCK: { buy: 0, sell: 0 }, OTHER: { buy: 0, sell: 0 } };
    for (const p of positions) {
      const sym = (p.symbol || p.asset || '').toUpperCase();
      const cat = (sym.includes('BTC') || sym.includes('ETH') || sym.includes('SOL') || sym.includes('USD')) ? 'CRYPTO'
        : sym.match(/^[A-Z]{1,5}$/) ? 'STOCK' : 'OTHER';
      const pnl = p.unrealized_pnl_pct || p.pnl_pct || 0;
      if (pnl >= 0) cats[cat].buy++;
      else cats[cat].sell++;
    }
    Object.assign(groups, cats);
    delete groups['OTHER']; // hide if empty
    delete groups['other'];
  }

  let html = '';
  for (const [name, data] of Object.entries(groups).slice(0, 4)) {
    const total = data.buy + data.sell || 1;
    const buyPct = Math.round((data.buy / total) * 100);
    const sellPct = 100 - buyPct;
    html += `<div class="flow-row">
      <span class="sym">${name.slice(0,5)}</span>
      <div class="flow-bar-track">
        <div class="flow-bar-buy" style="width:${buyPct}%"></div>
        <div class="flow-bar-sell" style="width:${sellPct}%"></div>
      </div>
      <span class="pct" style="color:${buyPct>=50?'var(--green)':'var(--red)'}">${buyPct}%</span>
    </div>`;
  }
  fb.innerHTML = html || '<div style="font-size:0.7em;color:var(--dim)">No flow data</div>';
}

// ── Position Chips ────────────────────────────────────────────
function updatePositionChips(positions) {
  const container = document.getElementById('position-chips');
  if (!positions.length) { container.innerHTML = ''; return; }

  const sorted = [...positions].sort((a, b) =>
    Math.abs(b.unrealized_pnl_pct || b.pnl_pct || 0) - Math.abs(a.unrealized_pnl_pct || a.pnl_pct || 0)
  );

  container.innerHTML = sorted.slice(0, 40).map(p => {
    const sym = (p.symbol || p.asset || '?').replace(/\//g, '');
    const pnl = p.unrealized_pnl_pct || p.pnl_pct || 0;
    const cls = pnl > 0.5 ? 'winner' : pnl < -0.5 ? 'loser' : 'flat';
    return `<span class="pos-chip ${cls}">${sym.slice(0,6)} ${pnl>=0?'+':''}${pnl.toFixed(1)}%</span>`;
  }).join('');
}

// ── Price Feed ────────────────────────────────────────────────
function updatePriceFeed(prices) {
  const pf = document.getElementById('price-feed');
  pf.innerHTML = Object.entries(prices).slice(0, 15).map(([sym, price]) =>
    `<div class="price-cell">
      <span class="sym">${sym}</span>
      <span class="px">$${price.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:6})}</span>
    </div>`
  ).join('');
}

// ── Radar ─────────────────────────────────────────────────────
function updateRadar(d) {
  const radar = document.getElementById('radar');
  radar.querySelectorAll('.radar-dot').forEach(el => el.remove());

  const positions = d.positions || [];
  const sample = positions.slice(0, 25);
  sample.forEach((p, i) => {
    const pnl = p.unrealized_pnl_pct || p.pnl_pct || 0;
    const color = pnl >= 0 ? 'var(--green)' : 'var(--red)';
    const angle = (i / sample.length) * Math.PI * 2;
    const r = Math.min(20 + Math.abs(pnl) * 2, 45);
    const x = 50 + r * Math.cos(angle);
    const y = 50 + r * Math.sin(angle);
    const dot = document.createElement('div');
    dot.className = 'radar-dot';
    dot.style.cssText = `left:${x}%;top:${y}%;color:${color};background:${color};animation-delay:${(i*0.1)%2}s`;
    dot.title = `${p.symbol||p.asset||'?'}: ${pnl>=0?'+':''}${pnl.toFixed(1)}%`;
    radar.appendChild(dot);
  });
}

// ── Positions Table ───────────────────────────────────────────
let currentPositions = [];

function sortPositions(field) {
  if (sortField === field) sortAsc = !sortAsc;
  else { sortField = field; sortAsc = field === 'symbol' || field === 'exchange'; }
  renderPositionsTable();
}

function updatePositionsTable(positions) {
  currentPositions = positions;
  renderPositionsTable();
}

function renderPositionsTable() {
  const tbody = document.getElementById('pos-tbody');
  if (!currentPositions.length) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--dim);padding:16px">Awaiting position data...</td></tr>';
    return;
  }

  const sorted = [...currentPositions].sort((a, b) => {
    let va, vb;
    switch (sortField) {
      case 'symbol': va = (a.symbol||a.asset||''); vb = (b.symbol||b.asset||''); break;
      case 'exchange': va = (a.exchange||''); vb = (b.exchange||''); break;
      case 'qty': va = a.quantity||a.qty||0; vb = b.quantity||b.qty||0; break;
      case 'entry': va = a.entry_price||a.avg_price||0; vb = b.entry_price||b.avg_price||0; break;
      case 'current': va = a.current_price||0; vb = b.current_price||0; break;
      case 'value': va = a.market_value||a.value||0; vb = b.market_value||b.value||0; break;
      case 'pnl': va = a.unrealized_pnl_pct||a.pnl_pct||0; vb = b.unrealized_pnl_pct||b.pnl_pct||0; break;
      case 'pnl_usd': va = a.unrealized_pnl||0; vb = b.unrealized_pnl||0; break;
      default: va = 0; vb = 0;
    }
    if (typeof va === 'string') return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
    return sortAsc ? va - vb : vb - va;
  });

  tbody.innerHTML = sorted.slice(0, 50).map(p => {
    const sym = (p.symbol || p.asset || '?').replace(/\//g, '');
    const ex = (p.exchange || '--').slice(0, 6);
    const qty = p.quantity || p.qty || 0;
    const entry = p.entry_price || p.avg_price || 0;
    const cur = p.current_price || 0;
    const val = p.market_value || p.value || 0;
    const pnlPct = p.unrealized_pnl_pct || p.pnl_pct || 0;
    const pnlUsd = p.unrealized_pnl || 0;
    const pnlClass = pnlPct >= 0 ? 'pnl-pos' : 'pnl-neg';
    return `<tr>
      <td class="sym-cell">${sym}</td>
      <td>${ex}</td>
      <td>${qty > 100 ? qty.toFixed(0) : qty.toFixed(4)}</td>
      <td>${entry > 0 ? '$'+entry.toFixed(entry<1?6:2) : '--'}</td>
      <td>${cur > 0 ? '$'+cur.toFixed(cur<1?6:2) : '--'}</td>
      <td>$${val.toFixed(2)}</td>
      <td class="${pnlClass}">${pnlPct>=0?'+':''}${pnlPct.toFixed(1)}%</td>
      <td class="${pnlClass}">${pnlUsd>=0?'+$':'−$'}${Math.abs(pnlUsd).toFixed(2)}</td>
    </tr>`;
  }).join('');
}

// ── Thoughts ──────────────────────────────────────────────────
function updateThoughts(thoughts) {
  const ts = document.getElementById('thought-stream');
  const title = '<div class="title">◆ THOUGHTBUS STREAM</div>';
  if (!thoughts.length) { ts.innerHTML = title + '<div class="thought-item" style="color:var(--dim)">No recent thoughts</div>'; return; }
  ts.innerHTML = title + thoughts.slice(-8).reverse().map(t =>
    `<div class="thought-item"><span class="src">[${t.source||'?'}]</span> <span class="topic">${t.topic||'thought'}</span></div>`
  ).join('');
}

// ── API Key Status ────────────────────────────────────────────
function updateKeyStatus(ks) {
  if (!ks || !ks.status) return;
  const badge = document.getElementById('key-status');
  const detail = document.getElementById('key-detail-status');
  const hint = document.getElementById('key-detail-hint');
  const pulseDot = document.getElementById('samuel-pulse-dot');
  const samuelText = document.getElementById('samuel-status-text');

  const statusMap = {
    active:      { color: 'var(--green)',  label: 'ACTIVE',      short: 'VALID' },
    invalid:     { color: 'var(--red)',    label: 'INVALID',     short: 'INVALID' },
    inactive:    { color: 'var(--amber)',  label: 'INACTIVE',    short: 'INACTIVE' },
    missing:     { color: 'var(--red)',    label: 'MISSING',     short: 'NO KEY' },
    placeholder: { color: 'var(--amber)',  label: 'PLACEHOLDER', short: 'PLACEHOLDER' },
    error:       { color: 'var(--red)',    label: 'ERROR',       short: 'ERROR' },
    unknown:     { color: 'var(--dim)',    label: 'CHECKING...',  short: '--' },
  };
  const info = statusMap[ks.status] || statusMap.unknown;

  badge.textContent = info.short;
  badge.style.color = info.color;
  detail.textContent = info.label;
  detail.style.color = info.color;

  if (hint && ks.partial_hint) hint.textContent = ` (${ks.partial_hint})`;

  if (ks.status === 'active') {
    pulseDot.style.background = 'var(--green)';
    pulseDot.style.boxShadow = '0 0 8px var(--green)';
    samuelText.textContent = 'SAMUEL ONLINE — CLAUDE';
    samuelText.style.color = 'var(--green)';
  } else {
    pulseDot.style.background = 'var(--amber)';
    pulseDot.style.boxShadow = '0 0 8px var(--amber)';
    samuelText.textContent = 'SAMUEL LOCAL MODE';
    samuelText.style.color = 'var(--amber)';
  }

  if (ks.error) {
    document.getElementById('key-detail').title = `Error: ${ks.error}\nClick to revalidate`;
  }
}

// Revalidate key on click
document.getElementById('key-detail').addEventListener('click', async () => {
  try {
    document.getElementById('key-detail-status').textContent = 'revalidating...';
    const res = await fetch('/api/key-status?revalidate=1');
    const ks = await res.json();
    updateKeyStatus(ks);
  } catch (e) {
    document.getElementById('key-detail-status').textContent = 'fetch error';
  }
});

// ── Data Freshness Indicator ──────────────────────────────────
setInterval(() => {
  const age = Date.now() - lastDataTime;
  const dot = document.getElementById('data-freshness');
  if (age < 5000) { dot.className = 'freshness live'; dot.title = 'Data: LIVE'; }
  else if (age < 15000) { dot.className = 'freshness stale'; dot.title = 'Data: STALE'; }
  else { dot.className = 'freshness dead'; dot.title = 'Data: NO FEED'; }
}, 2000);

// ── Chat Functions ────────────────────────────────────────────
function sendMessage() {
  const input = document.getElementById('chat-input');
  const msg = input.value.trim();
  if (!msg || !ws || ws.readyState !== WebSocket.OPEN) return;

  addUserMessage(msg);
  showTyping();
  ws.send(JSON.stringify({ type: 'chat', message: msg }));
  input.value = '';
  input.focus();
}

function addUserMessage(text) {
  const container = document.getElementById('chat-messages');
  container.innerHTML += `<div class="chat-msg user">
    <div class="sender">◆ COMMANDER</div>
    <div class="text">${escapeHtml(text)}</div>
  </div>`;
  scrollChat();
}

function addSamuelMessage(text) {
  const container = document.getElementById('chat-messages');
  container.innerHTML += `<div class="chat-msg samuel">
    <div class="sender">◆ SAMUEL</div>
    <div class="text">${escapeHtml(text)}</div>
  </div>`;
  scrollChat();
}

function addSystemMessage(text) {
  const container = document.getElementById('chat-messages');
  container.innerHTML += `<div class="chat-msg system">${escapeHtml(text)}</div>`;
  scrollChat();
}

function scrollChat() {
  const c = document.getElementById('chat-messages');
  c.scrollTop = c.scrollHeight;
}

function showTyping() { document.getElementById('typing-indicator').classList.add('active'); }
function hideTyping() { document.getElementById('typing-indicator').classList.remove('active'); }

function escapeHtml(s) {
  const div = document.createElement('div');
  div.textContent = s;
  return div.innerHTML;
}

// ── Voice (Web Speech API) ────────────────────────────────────
let recognition = null;
let isRecording = false;

function initVoice() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return;

  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = 'en-GB';

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    document.getElementById('chat-input').value = transcript;
    sendMessage();
  };

  recognition.onend = () => {
    isRecording = false;
    document.getElementById('btn-voice').classList.remove('recording');
  };

  recognition.onerror = () => {
    isRecording = false;
    document.getElementById('btn-voice').classList.remove('recording');
  };
}

function toggleVoice() {
  if (!recognition) initVoice();
  if (!recognition) { addSystemMessage('Voice not supported.'); return; }

  if (isRecording) {
    recognition.stop();
    isRecording = false;
    document.getElementById('btn-voice').classList.remove('recording');
  } else {
    recognition.start();
    isRecording = true;
    document.getElementById('btn-voice').classList.add('recording');
    addSystemMessage('🎙 Listening...');
  }
}

function speak(text) {
  if (!('speechSynthesis' in window)) return;
  speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 0.95;
  utterance.pitch = 0.9;
  utterance.volume = 0.8;
  const voices = speechSynthesis.getVoices();
  const preferred = voices.find(v => v.lang.startsWith('en') && v.name.toLowerCase().includes('male'))
    || voices.find(v => v.lang.startsWith('en-GB'))
    || voices.find(v => v.lang.startsWith('en'));
  if (preferred) utterance.voice = preferred;
  speechSynthesis.speak(utterance);
}

// ── Event Listeners ───────────────────────────────────────────
document.getElementById('btn-send').addEventListener('click', sendMessage);
document.getElementById('chat-input').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') sendMessage();
});
document.getElementById('btn-voice').addEventListener('click', toggleVoice);

if ('speechSynthesis' in window) {
  speechSynthesis.onvoiceschanged = () => {};
  speechSynthesis.getVoices();
}

// ── Init ──────────────────────────────────────────────────────
initChart();

setTimeout(() => {
  addSamuelMessage("Warzone online. All theatres reporting in. I'm reading the live feeds now — ask me anything about our positions, threats, or strategy. I'm here, commander.");
}, 1500);

connectWS();
initVoice();

</script>
</body>
</html>"""


# ═══════════════════════════════════════════════════════════════════════════════
# SERVER STARTUP
# ═══════════════════════════════════════════════════════════════════════════════

def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get('/', index_handler)
    app.router.add_get('/ws', ws_handler)
    app.router.add_get('/api/intel', api_intel)
    app.router.add_post('/api/chat', api_chat)
    app.router.add_get('/api/health', api_health)
    app.router.add_get('/api/key-status', api_key_status)
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    return app


def main():
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ⚔️🔥 AUREON WARZONE — TACTICAL ANALYTICS COMMAND 🔥⚔️       ║
║                                                              ║
║   Dashboard: http://localhost:{WARZONE_PORT}                       ║
║   API:       http://localhost:{WARZONE_PORT}/api/intel              ║
║   Chat:      http://localhost:{WARZONE_PORT}/api/chat (POST)       ║
║   Health:    http://localhost:{WARZONE_PORT}/api/health             ║
║   WebSocket: ws://localhost:{WARZONE_PORT}/ws                      ║
║                                                              ║
║   Samuel AI: {"CLAUDE (Opus)" if ANTHROPIC_AVAILABLE else "LOCAL MODE (no API key)":45s}║
║   ThoughtBus: {"READ-ONLY" if THOUGHT_BUS_AVAILABLE else "OFFLINE":44s}║
║                                                              ║
║   "We don't quit. We compound. We conquer." ⚔️               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=WARZONE_PORT, print=None)


if __name__ == '__main__':
    main()
