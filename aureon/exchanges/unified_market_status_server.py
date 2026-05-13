"""Read-only local status API for the unified market runtime.

This server starts before the heavy trading/cognitive runtime. It gives the
frontend a stable heartbeat while the full trader imports, wires cognition, and
connects exchanges. The trader keeps writing state/unified_runtime_status.json;
this process only serves that file and never places orders.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_ROOT = REPO_ROOT / "state"
STATUS_PATH = REPO_ROOT / "state" / "unified_runtime_status.json"
MARKET_INTENT_PATH = STATE_ROOT / "aureon_market_reboot_intent.json"
HOST = "127.0.0.1"
STATUS_FILE_STALE_AFTER_SEC = float(os.getenv("UNIFIED_STATUS_FILE_STALE_AFTER_SEC", "60") or 60)
TICK_STALE_AFTER_SEC = float(os.getenv("UNIFIED_READY_STALE_AFTER_SEC", "45") or 45)


def _parse_iso_timestamp(value: Any) -> float:
    if not value:
        return 0.0
    try:
        text = str(value).strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        return datetime.fromisoformat(text).timestamp()
    except Exception:
        return 0.0


def _runtime_watchdog(payload: dict[str, Any], status_file_age_sec: float | None = None) -> dict[str, Any]:
    existing = payload.get("runtime_watchdog")
    if isinstance(existing, dict):
        watchdog = dict(existing)
    else:
        watchdog = {}

    now = time.time()
    last_completed_ts = _parse_iso_timestamp(payload.get("last_tick_completed_at"))
    last_started_ts = _parse_iso_timestamp(payload.get("last_tick_started_at"))
    last_tick_age_sec = payload.get("last_tick_age_sec")
    try:
        last_tick_age = float(last_tick_age_sec) if last_tick_age_sec is not None else (now - last_completed_ts if last_completed_ts else None)
    except Exception:
        last_tick_age = None
    tick_running_sec = max(0.0, now - last_started_ts) if last_started_ts > last_completed_ts else 0.0

    stale_reason = str(payload.get("stale_reason") or watchdog.get("tick_stale_reason") or "")
    tick_stale = bool(payload.get("stale") or watchdog.get("tick_stale"))
    if last_tick_age is not None and last_tick_age > TICK_STALE_AFTER_SEC:
        tick_stale = True
        stale_reason = stale_reason or "last_tick_age_exceeded"
    if tick_running_sec > TICK_STALE_AFTER_SEC:
        tick_stale = True
        stale_reason = "tick_in_progress_stalled"

    status_file_fresh = status_file_age_sec is None or status_file_age_sec <= STATUS_FILE_STALE_AFTER_SEC
    open_positions = _has_open_positions(payload)
    severity = "critical" if tick_stale and open_positions else "degraded" if tick_stale else "healthy"
    recovery_action = (
        "preserve_position_monitoring_and_defer_restart_until_flat_downtime"
        if tick_stale and open_positions
        else "restart_in_downtime_window"
        if tick_stale
        else "none"
    )

    watchdog.update(
        {
            "status_file_fresh": status_file_fresh,
            "status_file_age_sec": round(float(status_file_age_sec), 3) if status_file_age_sec is not None else None,
            "heartbeat_fresh_but_tick_stale": bool(status_file_fresh and tick_stale),
            "tick_stale": tick_stale,
            "tick_stale_reason": stale_reason,
            "tick_stale_after_sec": TICK_STALE_AFTER_SEC,
            "last_tick_age_sec": round(float(last_tick_age), 3) if last_tick_age is not None else None,
            "last_tick_running_sec": round(float(tick_running_sec), 3) if tick_running_sec > 0 else 0.0,
            "open_positions": open_positions,
            "severity": severity,
            "recovery_action": recovery_action,
        }
    )
    return watchdog


def _read_status() -> dict[str, Any]:
    if STATUS_PATH.exists():
        try:
            with STATUS_PATH.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if isinstance(payload, dict):
                stat = STATUS_PATH.stat()
                age_sec = max(0.0, time.time() - stat.st_mtime)
                payload.setdefault("ok", True)
                payload.setdefault("source", "unified-market-status-server")
                payload["status_file"] = str(STATUS_PATH)
                payload["status_file_mtime"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
                payload["status_file_age_sec"] = round(age_sec, 3)
                payload["runtime_watchdog"] = _runtime_watchdog(payload, age_sec)
                if payload["runtime_watchdog"].get("tick_stale"):
                    payload["stale"] = True
                    payload["stale_reason"] = payload["runtime_watchdog"].get("tick_stale_reason")
                if age_sec > STATUS_FILE_STALE_AFTER_SEC:
                    payload["stale"] = True
                    payload.setdefault("warnings", [])
                    if isinstance(payload["warnings"], list):
                        payload["warnings"].append("runtime_status_file_stale")
                return payload
        except Exception as exc:
            return {
                "ok": False,
                "source": "unified-market-status-server",
                "error": f"status_file_read_failed: {exc}",
                "status_file": str(STATUS_PATH),
                "generated_at": datetime.now().isoformat(),
            }

    return {
        "ok": True,
        "source": "unified-market-status-server",
        "generated_at": datetime.now().isoformat(),
        "service": "unified-market-trader",
        "trading_ready": False,
        "data_ready": False,
        "stale": True,
        "lines": "UNIFIED MARKET STATUS | Runtime status server is awake. Trader is still booting.",
        "terminal_lines": [
            "UNIFIED MARKET STATUS",
            "Runtime status server is awake.",
            "Trader is still booting and wiring exchange/cognitive systems.",
        ],
        "status_file": str(STATUS_PATH),
        "combined": {
            "open_positions": 0,
            "kraken_equity": 0.0,
            "capital_equity_gbp": 0.0,
        },
        "exchanges": {
            "kraken_ready": False,
            "capital_ready": False,
            "alpaca_ready": False,
            "binance_ready": False,
        },
    }


def _day_allowed(day_name: str, allowed_days: str | None) -> bool:
    raw = (allowed_days or "Sun").strip().lower()
    if raw in {"*", "all", "daily", "everyday"}:
        return True
    names = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    current = day_name[:3].lower()
    for part in raw.replace(";", ",").split(","):
        item = part.strip()
        if not item:
            continue
        if item == current or item == day_name.lower():
            return True
        if "-" in item:
            start_raw, end_raw = [piece.strip()[:3].lower() for piece in item.split("-", 1)]
            if start_raw in names and end_raw in names and current in names:
                start = names.index(start_raw)
                end = names.index(end_raw)
                now = names.index(current)
                if start <= end and start <= now <= end:
                    return True
                if start > end and (now >= start or now <= end):
                    return True
    return False


def _parse_clock(value: str | None, fallback: str) -> tuple[int, int]:
    raw = value or fallback
    try:
        hour_raw, minute_raw = raw.split(":", 1)
        return max(0, min(23, int(hour_raw))), max(0, min(59, int(minute_raw)))
    except Exception:
        hour_raw, minute_raw = fallback.split(":", 1)
        return int(hour_raw), int(minute_raw)


def _market_downtime_window() -> bool:
    days = os.getenv("AUREON_MARKET_DOWNTIME_DAYS") or os.getenv("AUREON_MIND_DOWNTIME_DAYS") or "Sun"
    start_h, start_m = _parse_clock(
        os.getenv("AUREON_MARKET_DOWNTIME_START_LOCAL") or os.getenv("AUREON_MIND_DOWNTIME_START_LOCAL"),
        "03:00",
    )
    end_h, end_m = _parse_clock(
        os.getenv("AUREON_MARKET_DOWNTIME_END_LOCAL") or os.getenv("AUREON_MIND_DOWNTIME_END_LOCAL"),
        "03:15",
    )
    now = datetime.now()
    start = now.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
    end = now.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
    if end <= start:
        end += timedelta(days=1)
    if _day_allowed(now.strftime("%A"), days) and start <= now < end:
        return True
    if end_h < start_h or (end_h == start_h and end_m <= start_m):
        yesterday = now - timedelta(days=1)
        previous_start = start - timedelta(days=1)
        previous_end = end - timedelta(days=1)
        if _day_allowed(yesterday.strftime("%A"), days) and previous_start <= now < previous_end:
            return True
    return False


def _read_market_intent() -> dict[str, Any] | None:
    try:
        if not MARKET_INTENT_PATH.exists():
            return None
        payload = json.loads(MARKET_INTENT_PATH.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload
    except Exception:
        return None
    return None


def _has_open_positions(payload: dict[str, Any]) -> bool:
    combined = payload.get("combined")
    if isinstance(combined, dict):
        try:
            return int(combined.get("open_positions", 0) or 0) > 0
        except Exception:
            return True
    positions = payload.get("positions")
    if isinstance(positions, list):
        return len(positions) > 0
    return True


def _flight_test() -> dict[str, Any]:
    status = _read_status()
    intent = _read_market_intent()
    pending_restart = bool(intent and intent.get("status") == "pending")
    watchdog = status.get("runtime_watchdog") if isinstance(status.get("runtime_watchdog"), dict) else _runtime_watchdog(status)
    stale = bool(status.get("stale") or watchdog.get("tick_stale"))
    open_positions = _has_open_positions(status)
    downtime = _market_downtime_window()
    should_reboot = pending_restart or stale
    can_reboot_now = bool(should_reboot and downtime and not open_positions)
    if can_reboot_now:
        reason = "downtime_window_active_and_no_open_positions"
    elif stale and open_positions:
        reason = "runtime_tick_stale_with_open_positions"
    elif open_positions:
        reason = "open_positions_reported"
    elif not downtime:
        reason = "outside_market_downtime_window"
    elif stale:
        reason = "runtime_tick_stale"
    else:
        reason = "no_restart_needed"

    return {
        "ok": bool(status.get("ok")) and not stale,
        "service": "unified-market-status-server",
        "generated_at": datetime.now().isoformat(),
        "checks": {
            "status_file_exists": STATUS_PATH.exists(),
            "runtime_ok": bool(status.get("ok")),
            "trading_ready": bool(status.get("trading_ready")),
            "data_ready": bool(status.get("data_ready")),
            "tick_fresh": not stale,
            "heartbeat_fresh_but_tick_stale": bool(watchdog.get("heartbeat_fresh_but_tick_stale")),
            "open_positions": open_positions,
            "downtime_window": downtime,
            "pending_restart": pending_restart,
        },
        "reboot_advice": {
            "surface": "market",
            "should_reboot": should_reboot,
            "can_reboot_now": can_reboot_now,
            "decision": (
                "reboot_now"
                if can_reboot_now
                else "hold_monitor_positions"
                if stale and open_positions
                else ("hold" if should_reboot else "none")
            ),
            "reason": reason,
            "recovery_action": watchdog.get("recovery_action"),
        },
        "intent": intent,
        "runtime": {
            "last_tick_started_at": status.get("last_tick_started_at"),
            "last_tick_completed_at": status.get("last_tick_completed_at"),
            "last_tick_age_sec": status.get("last_tick_age_sec"),
            "last_tick_running_sec": status.get("last_tick_running_sec"),
            "runtime_watchdog": watchdog,
            "combined": status.get("combined"),
            "exchanges": status.get("exchanges"),
        },
    }


class StatusHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self) -> None:
        if self.path in {"/", "/health", "/api/terminal-state", "/api/flight-test", "/api/reboot-advice"}:
            if self.path in {"/api/flight-test", "/api/reboot-advice"}:
                self._json(200, _flight_test())
                return
            payload = _read_status()
            if self.path == "/health":
                payload = {
                    "ok": True,
                    "service": "unified-market-status-server",
                    "generated_at": datetime.now().isoformat(),
                    "status_file": str(STATUS_PATH),
                    "status_file_exists": STATUS_PATH.exists(),
                    "served_status_ok": bool(payload.get("ok", False)),
                }
            self._json(200, payload)
            return
        self._json(404, {"ok": False, "error": "not_found"})

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only unified market status server")
    parser.add_argument("--port", type=int, default=8790)
    args = parser.parse_args()

    server = ThreadingHTTPServer((HOST, int(args.port)), StatusHandler)
    print(
        f"[{datetime.now().isoformat()}] unified market status server online: "
        f"http://{HOST}:{args.port}/api/terminal-state",
        flush=True,
    )
    try:
        while True:
            server.handle_request()
            time.sleep(0.001)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
