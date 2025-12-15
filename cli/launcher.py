from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from threading import Thread
from typing import Optional

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from cli.config_manager import (  # type: ignore
        TradingConfig,
        config_exists,
        load_config,
        save_config,
    )
    from cli.dashboard import create_app  # type: ignore
    from cli.setup_wizard import run_setup_wizard  # type: ignore
    from cli.trading_runtime import TradingService  # type: ignore
else:
    from .config_manager import (
        TradingConfig,
        config_exists,
        load_config,
        save_config,
    )
    from .dashboard import create_app
    from .setup_wizard import run_setup_wizard
    from .trading_runtime import TradingService
from werkzeug.serving import make_server


def _start_dashboard(service: TradingService, host: str = "127.0.0.1", port: int = 8000) -> Thread:
    app = create_app(service)
    server = make_server(host, port, app)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return thread


def _register_autostart(script_path: Path, config: TradingConfig) -> None:
    """Attempt to register the launcher as a scheduled task (Windows) or document a shortcut."""

    if os.name == "nt":
        task_name = "AureonAutoStart"
        command = f'schtasks /Create /SC ONLOGON /TN {task_name} /TR "{sys.executable} {script_path} --start" /F'
        try:
            subprocess.run(command, check=True, shell=True)
            print(f"Registered Windows scheduled task: {task_name}")
        except subprocess.CalledProcessError as exc:
            print(f"Failed to register scheduled task: {exc}")
    else:
        note_path = Path.home() / "aureon_autostart.txt"
        note_path.write_text(
            "Create a desktop shortcut or cron entry to run:\n"
            f"python {script_path} --start\n"
            "Auto-start is disabled by default; update config to enable.\n"
        )
        print(f"Saved auto-start instructions to {note_path}")

    config.auto_start = True
    save_config(config)


def ensure_config(force_plaintext: bool = False) -> TradingConfig:
    if config_exists():
        return load_config()
    return run_setup_wizard(force_plaintext=force_plaintext)


def start_trading(open_dashboard: bool = True, port: int = 8000) -> None:
    config = ensure_config()
    service = TradingService(config)
    service.start()

    dashboard_thread: Optional[Thread] = None
    if open_dashboard:
        dashboard_thread = _start_dashboard(service, port=port)
        webbrowser.open(f"http://127.0.0.1:{port}")
        print(f"Dashboard available at http://127.0.0.1:{port}")

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        service.stop()
        if dashboard_thread and dashboard_thread.is_alive():
            print("Dashboard thread stopping...")


def main() -> None:
    parser = argparse.ArgumentParser(description="Aureon launcher")
    parser.add_argument("--start", action="store_true", help="Start trading and the local dashboard")
    parser.add_argument("--stop", action="store_true", help="Reserved for future orchestrated stop")
    parser.add_argument("--run-wizard", action="store_true", help="Launch the setup wizard")
    parser.add_argument("--dev-plaintext", action="store_true", help="Save config in plaintext (dev only)")
    parser.add_argument("--register-autostart", action="store_true", help="Register OS auto-start task")
    parser.add_argument("--no-dashboard", action="store_true", help="Do not open the local dashboard")
    parser.add_argument("--dashboard-port", type=int, default=8000, help="Dashboard port")
    args = parser.parse_args()

    if args.run_wizard:
        run_setup_wizard(force_plaintext=args.dev_plaintext)
        return

    config = ensure_config(force_plaintext=args.dev_plaintext)

    if args.register_autostart:
        _register_autostart(Path(__file__).resolve(), config)
        return

    if args.start:
        start_trading(open_dashboard=not args.no_dashboard, port=args.dashboard_port)
        return

    if args.stop:
        print("Stop flag acknowledged. Implement remote stop logic here.")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
