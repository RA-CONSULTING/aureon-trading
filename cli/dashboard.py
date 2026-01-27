from __future__ import annotations
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)

from flask import Flask, jsonify, redirect, render_template_string, request, url_for

from .trading_runtime import TradingService


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Aureon Dashboard</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 2rem; background: #0f172a; color: #e2e8f0; }
    .card { background: #1e293b; padding: 1rem 1.5rem; border-radius: 12px; margin-bottom: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.35); }
    button { padding: 0.6rem 1rem; border-radius: 8px; border: none; cursor: pointer; }
    .primary { background: #2563eb; color: white; }
    .danger { background: #ef4444; color: white; }
    h1 { margin-bottom: 0.5rem; }
    pre { background: #0b1220; padding: 1rem; border-radius: 8px; overflow: auto; }
  </style>
</head>
<body>
  <h1>Aureon Local Dashboard</h1>
  <p>Connection Status: <strong>{{ 'Running' if running else 'Stopped' }}</strong></p>
  <div class="card">
    <h3>Controls</h3>
    <form method="post" action="{{ url_for('toggle') }}">
      {% if running %}
      <button class="danger" name="action" value="stop">Stop Trading</button>
      {% else %}
      <button class="primary" name="action" value="start">Start Trading</button>
      {% endif %}
    </form>
  </div>
  <div class="card">
    <h3>Session</h3>
    <p>Exchange: <strong>{{ config.exchange }}</strong></p>
    <p>Pair: <strong>{{ config.base_asset }}/{{ config.quote_asset }}</strong></p>
    <p>Mode: <strong>{{ config.mode }}</strong> | Trade size: <strong>{{ config.trade_size }}</strong></p>
  </div>
  <div class="card">
    <h3>P&L</h3>
    <p><strong>{{ pnl }}</strong></p>
  </div>
  <div class="card">
    <h3>Positions</h3>
    {% if positions %}
      <ul>
      {% for pos in positions %}
        <li>{{ pos.symbol }} — {{ pos.size }} @ {{ pos.entry_price }}</li>
      {% endfor %}
      </ul>
    {% else %}
      <p>No open positions.</p>
    {% endif %}
  </div>
  <div class="card">
    <h3>Logs</h3>
    <pre>{{ logs }}</pre>
  </div>
</body>
</html>
"""


def create_app(service: TradingService) -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def index():
        state = service.state
        return render_template_string(
            HTML_TEMPLATE,
            running=state.running,
            pnl=round(state.pnl, 2),
            positions=state.positions,
            logs="\n".join(state.logs[-20:]),
            config=service.config,
        )

    @app.route("/toggle", methods=["POST"])
    def toggle():
        action = request.form.get("action", "")
        if action == "start":
            service.start()
        elif action == "stop":
            service.stop()
        return redirect(url_for("index"))

    @app.route("/api/status")
    def api_status():
        state = service.state
        return jsonify(
            {
                "running": state.running,
                "pnl": round(state.pnl, 2),
                "positions": [pos.__dict__ for pos in state.positions],
                "logs": state.logs[-50:],
                "config": {
                    "exchange": service.config.exchange,
                    "pair": f"{service.config.base_asset}/{service.config.quote_asset}",
                    "mode": service.config.mode,
                    "trade_size": service.config.trade_size,
                },
            }
        )

    return app


__all__ = ["create_app"]
