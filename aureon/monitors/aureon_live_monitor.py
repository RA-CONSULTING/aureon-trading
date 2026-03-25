#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║          AUREON LIVE MONITOR — Standalone Dashboard          ║
║                                                              ║
║  Lightweight real-time portfolio monitoring dashboard.        ║
║  Reads state files directly — NO engine imports required.     ║
║  Auto-refreshes every 10 seconds from persisted JSON state.  ║
║                                                              ║
║  Usage: python aureon_live_monitor.py [--port 14000]          ║
║                                                              ║
║  Creator: Gary Leckey (02.11.1991) — Prime Sentinel Decree   ║
╚══════════════════════════════════════════════════════════════╝
"""
# ── Windows UTF-8 Wrapper ──────────────────────────────────────────
import sys, os, io
if sys.platform == 'win32':
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    for _stream_name in ('stdout', 'stderr'):
        _stream = getattr(sys, _stream_name, None)
        if _stream and hasattr(_stream, 'buffer'):
            try:
                _wrapped = io.TextIOWrapper(
                    _stream.buffer, encoding='utf-8',
                    errors='replace', line_buffering=True
                )
                setattr(sys, _stream_name, _wrapped)
            except Exception:
                pass
# ── End Windows UTF-8 Wrapper ──────────────────────────────────────

import json
import time
import asyncio
import argparse
import logging
from pathlib import Path
from datetime import datetime

try:
    from aiohttp import web
except ImportError:
    print("aiohttp not installed. Run: pip install aiohttp")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')
logger = logging.getLogger('aureon_live_monitor')

# ── Paths ──────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.resolve()
STATE_FILES = {
    'portfolio': BASE_DIR / 'portfolio_intelligence_snapshot.json',
    'cost_basis': BASE_DIR / 'cost_basis_history.json',
    'active_position': BASE_DIR / 'active_position.json',
    'pending_validations': BASE_DIR / '7day_pending_validations.json',
    'validation_history': BASE_DIR / '7day_validation_history.json',
    'current_plan': BASE_DIR / '7day_current_plan.json',
    'adaptive_weights': BASE_DIR / '7day_adaptive_weights.json',
    'kraken_state': BASE_DIR / 'aureon_kraken_state.json',
    'alpaca_state': BASE_DIR / 'alpaca_truth_tracker_state.json',
}

# ── Helpers ────────────────────────────────────────────────────────
def safe_load_json(path: Path, default=None):
    """Atomically load JSON file, return default on any error."""
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def format_usd(val):
    """Format a number as USD string."""
    try:
        v = float(val)
        if abs(v) >= 1:
            return f"${v:,.2f}"
        elif abs(v) >= 0.01:
            return f"${v:.4f}"
        else:
            return f"${v:.8f}"
    except (TypeError, ValueError):
        return "$0.00"


def format_pct(val):
    """Format a number as percentage."""
    try:
        return f"{float(val):+.2f}%"
    except (TypeError, ValueError):
        return "0.00%"


# ── Dashboard HTML ─────────────────────────────────────────────────
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aureon Live Monitor</title>
<style>
:root {
    --bg: #0a0e17;
    --card: #111827;
    --border: #1e293b;
    --text: #e2e8f0;
    --dim: #64748b;
    --green: #10b981;
    --red: #ef4444;
    --gold: #f59e0b;
    --blue: #3b82f6;
    --purple: #8b5cf6;
    --cyan: #06b6d4;
}
* { margin:0; padding:0; box-sizing:border-box; }
body {
    font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
}
.header {
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
    border-bottom: 1px solid var(--border);
    padding: 16px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.header h1 {
    font-size: 18px;
    font-weight: 700;
    background: linear-gradient(90deg, var(--gold), var(--cyan));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.header .status {
    font-size: 12px;
    color: var(--dim);
}
.header .status .pulse {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--green);
    margin-right: 6px;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}

/* Summary cards */
.summary-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
    padding: 16px 24px;
}
.summary-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
    text-align: center;
}
.summary-card .label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--dim);
    margin-bottom: 6px;
}
.summary-card .value {
    font-size: 22px;
    font-weight: 700;
}
.summary-card .sub {
    font-size: 11px;
    color: var(--dim);
    margin-top: 4px;
}

/* Exchange breakdown */
.exchange-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    padding: 0 24px 16px;
}
.exchange-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px;
    display: flex;
    align-items: center;
    gap: 12px;
}
.exchange-card .icon {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    font-weight: 700;
}
.exchange-card .icon.kraken { background: #1a1443; color: #7b61ff; }
.exchange-card .icon.binance { background: #1a1a08; color: #f3ba2f; }
.exchange-card .icon.alpaca { background: #0a1a0a; color: #00c853; }
.exchange-card .info .name {
    font-size: 12px;
    color: var(--dim);
    text-transform: uppercase;
    letter-spacing: 1px;
}
.exchange-card .info .val {
    font-size: 18px;
    font-weight: 700;
}

/* Tabs */
.tabs {
    display: flex;
    gap: 0;
    padding: 0 24px;
    border-bottom: 1px solid var(--border);
}
.tab {
    padding: 10px 20px;
    font-size: 12px;
    color: var(--dim);
    cursor: pointer;
    border-bottom: 2px solid transparent;
    transition: all 0.2s;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.tab.active {
    color: var(--gold);
    border-bottom-color: var(--gold);
}
.tab:hover { color: var(--text); }

/* Table section */
.table-section {
    padding: 16px 24px;
    display: none;
}
.table-section.active { display: block; }
table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
}
th {
    text-align: left;
    padding: 8px 12px;
    color: var(--dim);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
    border-bottom: 1px solid var(--border);
    cursor: pointer;
    user-select: none;
}
th:hover { color: var(--text); }
th.sorted-asc::after { content: ' ▲'; }
th.sorted-desc::after { content: ' ▼'; }
td {
    padding: 8px 12px;
    border-bottom: 1px solid #0f1729;
    white-space: nowrap;
}
tr:hover { background: rgba(255,255,255,0.02); }
.pos { color: var(--green); }
.neg { color: var(--red); }
.neutral { color: var(--dim); }

/* Validation panel */
.validation-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px;
    margin-bottom: 8px;
}
.validation-card .v-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 6px;
}
.validation-card .v-symbol {
    font-weight: 700;
    color: var(--cyan);
}
.validation-card .v-status {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 4px;
}
.v-status.validated { background: #064e3b; color: #6ee7b7; }
.v-status.pending { background: #451a03; color: #fbbf24; }
.validation-card .v-details {
    font-size: 11px;
    color: var(--dim);
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 4px;
}

/* Footer */
.footer {
    text-align: center;
    padding: 16px;
    font-size: 10px;
    color: var(--dim);
    border-top: 1px solid var(--border);
}

/* Responsive */
@media (max-width: 768px) {
    .exchange-row { grid-template-columns: 1fr; }
    .summary-row { grid-template-columns: repeat(2, 1fr); }
    table { font-size: 11px; }
    td, th { padding: 6px 8px; }
}
</style>
</head>
<body>

<div class="header">
    <h1>AUREON LIVE MONITOR</h1>
    <div class="status">
        <span class="pulse"></span>
        <span id="last-update">Loading...</span>
        &nbsp;|&nbsp; Auto-refresh: 10s
    </div>
</div>

<!-- Summary Cards -->
<div class="summary-row" id="summary-row"></div>

<!-- Exchange Breakdown -->
<div class="exchange-row" id="exchange-row"></div>

<!-- Tabs -->
<div class="tabs" id="tabs">
    <div class="tab active" data-tab="positions">Positions</div>
    <div class="tab" data-tab="validations">Validations</div>
    <div class="tab" data-tab="plan">7-Day Plan</div>
</div>

<!-- Positions Table -->
<div class="table-section active" id="tab-positions">
    <table>
        <thead>
            <tr id="pos-headers"></tr>
        </thead>
        <tbody id="pos-body"></tbody>
    </table>
</div>

<!-- Validations -->
<div class="table-section" id="tab-validations">
    <div id="validations-container"></div>
</div>

<!-- 7-Day Plan -->
<div class="table-section" id="tab-plan">
    <pre id="plan-content" style="color:var(--dim);font-size:12px;white-space:pre-wrap;"></pre>
</div>

<div class="footer">
    Aureon Trading System &mdash; Gary Leckey &mdash; Prime Sentinel Decree
</div>

<script>
// ── State ──
let sortCol = 'current_value';
let sortDir = -1; // -1 = desc
let currentTab = 'positions';

// ── Tab switching ──
document.getElementById('tabs').addEventListener('click', e => {
    const tab = e.target.closest('.tab');
    if (!tab) return;
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.table-section').forEach(s => s.classList.remove('active'));
    tab.classList.add('active');
    currentTab = tab.dataset.tab;
    document.getElementById('tab-' + currentTab).classList.add('active');
});

// ── Format helpers ──
function fmtUSD(v) {
    v = parseFloat(v) || 0;
    if (Math.abs(v) >= 1) return '$' + v.toLocaleString('en-US', {minimumFractionDigits:2, maximumFractionDigits:2});
    if (Math.abs(v) >= 0.01) return '$' + v.toFixed(4);
    return '$' + v.toFixed(8);
}
function fmtPct(v) {
    v = parseFloat(v) || 0;
    return (v >= 0 ? '+' : '') + v.toFixed(2) + '%';
}
function fmtQty(v) {
    v = parseFloat(v) || 0;
    if (v >= 1000) return v.toLocaleString('en-US', {maximumFractionDigits:2});
    if (v >= 1) return v.toFixed(4);
    return v.toFixed(8);
}
function pnlClass(v) {
    v = parseFloat(v) || 0;
    return v > 0 ? 'pos' : v < 0 ? 'neg' : 'neutral';
}

// ── Render Summary ──
function renderSummary(data) {
    const s = data.summary || {};
    const t = data.totals || {};
    const cards = [
        { label: 'Grand Total', value: fmtUSD(t.grand_total || 0), sub: '', cls: '' },
        { label: 'Positions', value: s.total_positions || 0, sub: `${s.winners||0}W / ${s.losers||0}L`, cls: '' },
        { label: 'Win Rate', value: (parseFloat(s.win_rate)||0).toFixed(1)+'%', sub: '', cls: '' },
        { label: 'Total P&L', value: fmtUSD(s.total_pnl_usd||0), sub: '', cls: pnlClass(s.total_pnl_usd) },
        { label: 'Invested', value: fmtUSD(s.total_invested||0), sub: '', cls: '' },
        { label: 'Cash', value: fmtUSD(s.total_cash||0), sub: '', cls: '' },
    ];
    document.getElementById('summary-row').innerHTML = cards.map(c =>
        `<div class="summary-card">
            <div class="label">${c.label}</div>
            <div class="value ${c.cls}">${c.value}</div>
            ${c.sub ? `<div class="sub">${c.sub}</div>` : ''}
        </div>`
    ).join('');
}

// ── Render Exchanges ──
function renderExchanges(data) {
    const t = data.totals || {};
    const exchanges = [
        { name: 'Kraken', key: 'kraken', icon: 'K', cls: 'kraken' },
        { name: 'Binance', key: 'binance', icon: 'B', cls: 'binance' },
        { name: 'Alpaca', key: 'alpaca', icon: 'A', cls: 'alpaca' },
    ];
    document.getElementById('exchange-row').innerHTML = exchanges.map(ex =>
        `<div class="exchange-card">
            <div class="icon ${ex.cls}">${ex.icon}</div>
            <div class="info">
                <div class="name">${ex.name}</div>
                <div class="val">${fmtUSD(t[ex.key] || 0)}</div>
            </div>
        </div>`
    ).join('');
}

// ── Render Positions ──
const POS_COLS = [
    { key: 'exchange', label: 'Exchange' },
    { key: 'symbol', label: 'Symbol' },
    { key: 'quantity', label: 'Qty' },
    { key: 'entry_price', label: 'Entry' },
    { key: 'current_price', label: 'Price' },
    { key: 'current_value', label: 'Value' },
    { key: 'pnl_usd', label: 'P&L $' },
    { key: 'pnl_pct', label: 'P&L %' },
    { key: 'change_24h', label: '24h %' },
    { key: 'change_7d', label: '7d %' },
];

function renderPositions(positions) {
    // Headers
    document.getElementById('pos-headers').innerHTML = POS_COLS.map(c => {
        let cls = '';
        if (c.key === sortCol) cls = sortDir === 1 ? 'sorted-asc' : 'sorted-desc';
        return `<th class="${cls}" data-col="${c.key}">${c.label}</th>`;
    }).join('');

    // Sort
    const sorted = [...positions].sort((a, b) => {
        let av = a[sortCol], bv = b[sortCol];
        if (typeof av === 'string') return sortDir * av.localeCompare(bv);
        return sortDir * ((parseFloat(av)||0) - (parseFloat(bv)||0));
    });

    // Rows
    document.getElementById('pos-body').innerHTML = sorted.map(p => {
        const isCash = p.type === 'cash';
        return `<tr>
            <td>${p.exchange || ''}</td>
            <td style="font-weight:700;color:${isCash ? 'var(--gold)' : 'var(--cyan)'}">${p.symbol || ''}</td>
            <td>${fmtQty(p.quantity)}</td>
            <td>${fmtUSD(p.entry_price)}</td>
            <td>${fmtUSD(p.current_price)}</td>
            <td style="font-weight:600">${fmtUSD(p.current_value)}</td>
            <td class="${pnlClass(p.pnl_usd)}">${fmtUSD(p.pnl_usd)}</td>
            <td class="${pnlClass(p.pnl_pct)}">${fmtPct(p.pnl_pct)}</td>
            <td class="${pnlClass(p.change_24h)}">${fmtPct(p.change_24h)}</td>
            <td class="${pnlClass(p.change_7d)}">${fmtPct(p.change_7d)}</td>
        </tr>`;
    }).join('');

    // Sort click handlers
    document.querySelectorAll('#pos-headers th').forEach(th => {
        th.onclick = () => {
            const col = th.dataset.col;
            if (col === sortCol) sortDir *= -1;
            else { sortCol = col; sortDir = -1; }
            renderPositions(positions);
        };
    });
}

// ── Render Validations ──
function renderValidations(validations) {
    if (!validations || !validations.length) {
        document.getElementById('validations-container').innerHTML =
            '<div style="color:var(--dim);padding:20px;text-align:center;">No pending validations</div>';
        return;
    }
    document.getElementById('validations-container').innerHTML = validations.map(v =>
        `<div class="validation-card">
            <div class="v-header">
                <span class="v-symbol">${v.symbol || '?'}</span>
                <span class="v-status ${v.status === 'validated' ? 'validated' : 'pending'}">${v.status || 'unknown'}</span>
            </div>
            <div class="v-details">
                <span>Entry: ${fmtUSD(v.entry_price)}</span>
                <span>Exit: ${fmtUSD(v.exit_price)}</span>
                <span>Edge: ${fmtPct(v.actual_edge)}</span>
                <span>Confidence: ${((v.predicted_confidence||0)*100).toFixed(0)}%</span>
                <span>Direction: ${v.direction_correct ? '✓ Correct' : '✗ Wrong'}</span>
                <span>Timing: ${((v.timing_score||0)*100).toFixed(0)}%</span>
                <span>Time: ${(v.entry_time||'').slice(0,16)}</span>
            </div>
        </div>`
    ).join('');
}

// ── Render Plan ──
function renderPlan(plan) {
    const el = document.getElementById('plan-content');
    if (!plan || (typeof plan === 'object' && Object.keys(plan).length === 0)) {
        el.textContent = 'No active plan';
    } else {
        el.textContent = JSON.stringify(plan, null, 2);
    }
}

// ── Main fetch loop ──
let portfolioData = null;

async function refresh() {
    try {
        const [portRes, valRes, planRes] = await Promise.all([
            fetch('/api/portfolio'),
            fetch('/api/validations'),
            fetch('/api/plan'),
        ]);
        const port = await portRes.json();
        const val = await valRes.json();
        const plan = await planRes.json();

        portfolioData = port;
        renderSummary(port);
        renderExchanges(port);
        renderPositions(port.positions || []);
        renderValidations(val);
        renderPlan(plan);

        const ts = port.timestamp ? new Date(port.timestamp).toLocaleTimeString() : 'N/A';
        document.getElementById('last-update').textContent =
            `Data: ${ts} | Refreshed: ${new Date().toLocaleTimeString()}`;
    } catch (err) {
        document.getElementById('last-update').textContent = 'Error: ' + err.message;
    }
}

refresh();
setInterval(refresh, 10000);
</script>
</body>
</html>"""


# ── Async Web Server ──────────────────────────────────────────────
class AureonLiveMonitor:
    """Standalone live monitoring dashboard for the Aureon Trading System."""

    def __init__(self, port: int = 14000):
        self.port = port
        self.app = web.Application()
        self._setup_routes()

    def _setup_routes(self):
        self.app.router.add_get('/', self.handle_index)
        self.app.router.add_get('/health', self.handle_health)
        self.app.router.add_get('/api/portfolio', self.handle_portfolio)
        self.app.router.add_get('/api/validations', self.handle_validations)
        self.app.router.add_get('/api/plan', self.handle_plan)
        self.app.router.add_get('/api/state/{name}', self.handle_state)

    # ── Handlers ───────────────────────────────────────────────

    async def handle_index(self, request):
        return web.Response(text=DASHBOARD_HTML, content_type='text/html')

    async def handle_health(self, request):
        return web.json_response({
            'status': 'ok',
            'server': 'aureon_live_monitor',
            'timestamp': datetime.utcnow().isoformat(),
            'state_files': {k: v.exists() for k, v in STATE_FILES.items()},
        })

    async def handle_portfolio(self, request):
        """Serve portfolio intelligence snapshot."""
        data = safe_load_json(STATE_FILES['portfolio'], {})
        if not data:
            # Fallback: build from cost_basis_history
            cb = safe_load_json(STATE_FILES['cost_basis'], {})
            positions = []
            if isinstance(cb, dict):
                for sym, info in cb.items():
                    if isinstance(info, dict):
                        positions.append({
                            'exchange': info.get('exchange', '?'),
                            'symbol': sym,
                            'quantity': info.get('quantity', 0),
                            'entry_price': info.get('avg_cost', 0),
                            'current_price': info.get('current_price', 0),
                            'current_value': info.get('current_value', 0),
                            'pnl_usd': info.get('pnl_usd', 0),
                            'pnl_pct': info.get('pnl_pct', 0),
                            'type': 'position',
                        })
            data = {
                'timestamp': datetime.utcnow().isoformat(),
                'positions': positions,
                'totals': {},
                'summary': {'total_positions': len(positions)},
            }
        return web.json_response(data)

    async def handle_validations(self, request):
        """Serve 7-day pending validations."""
        data = safe_load_json(STATE_FILES['pending_validations'], [])
        return web.json_response(data)

    async def handle_plan(self, request):
        """Serve 7-day current plan."""
        data = safe_load_json(STATE_FILES['current_plan'], {})
        return web.json_response(data)

    async def handle_state(self, request):
        """Generic state file reader: /api/state/{name}"""
        name = request.match_info['name']
        if name not in STATE_FILES:
            return web.json_response({'error': f'Unknown state: {name}'}, status=404)
        data = safe_load_json(STATE_FILES[name], {})
        return web.json_response(data)

    # ── Run ────────────────────────────────────────────────────

    def run(self):
        logger.info(f"Starting Aureon Live Monitor on port {self.port}")
        logger.info(f"State files directory: {BASE_DIR}")
        for name, path in STATE_FILES.items():
            status = "OK" if path.exists() else "MISSING"
            logger.info(f"  {name}: {status}")
        logger.info(f"Dashboard URL: http://localhost:{self.port}")
        web.run_app(self.app, host='0.0.0.0', port=self.port, print=logger.info)


# ── Entry Point ────────────────────────────────────────────────────
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Aureon Live Monitor')
    parser.add_argument('--port', type=int, default=14000, help='Port (default: 14000)')
    args = parser.parse_args()

    monitor = AureonLiveMonitor(port=args.port)
    monitor.run()
