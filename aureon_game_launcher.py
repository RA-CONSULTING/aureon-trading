#!/usr/bin/env python3
"""
🎮👑 AUREON GAME LAUNCHER 👑🎮
=================================

RED ALERT 2 STYLE UNIFIED LAUNCHER
Starts the Command Center + Trading Engine together!
"""

import sys, os, atexit

# SAFE PRINT WRAPPER FOR WINDOWS
def safe_print(*args, **kwargs):
    """Safe print that ignores I/O errors on Windows exit."""
    try:
        import builtins
        builtins.print(*args, **kwargs)
    except (ValueError, OSError):
        pass

if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUNBUFFERED'] = '1'
    try:
        import io
        def _is_utf8_wrapper(stream):
            """Check if stream is already a UTF-8 TextIOWrapper."""
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        # Only wrap stdout, NOT stderr (stderr causes shutdown errors)
        if hasattr(sys.stdout, 'buffer') and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass
    
    # Aggressive cleanup: redirect stderr to devnull on exit
    def _cleanup_stderr():
        try:
            sys.stderr = open(os.devnull, 'w')
        except Exception:
            pass
    atexit.register(_cleanup_stderr)

import argparse
import subprocess
import time
import webbrowser
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class GameModeConfig:
    start_trading: bool = True
    dry_run: bool = True
    command_center: bool = True
    queen_web_dashboard: bool = False
    queen_unified_dashboard: bool = False
    bot_hunter_dashboard: bool = False
    global_bot_map: bool = False
    telemetry: bool = False
    open_browser: bool = True


@dataclass
class ServiceProcess:
    name: str
    command: List[str]
    process: subprocess.Popen


def _build_python_command(script_name: str, args: Optional[List[str]] = None) -> List[str]:
    cmd = [sys.executable, script_name]
    if args:
        cmd.extend(args)
    return cmd


def _start_process(name: str, cmd: List[str]) -> ServiceProcess:
    safe_print(f"🚀 Starting {name} ...")
    process = subprocess.Popen(cmd)
    return ServiceProcess(name=name, command=cmd, process=process)


def _print_banner():
    safe_print("""
    
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║                                                                           ║
    ║     █████╗ ██╗   ██╗██████╗ ███████╗ ██████╗ ███╗   ██╗                   ║
    ║    ██╔══██╗██║   ██║██╔══██╗██╔════╝██╔═══██╗████╗  ██║                   ║
    ║    ███████║██║   ██║██████╔╝█████╗  ██║   ██║██╔██╗ ██║                   ║
    ║    ██╔══██║██║   ██║██╔══██╗██╔══╝  ██║   ██║██║╚██╗██║                   ║
    ║    ██║  ██║╚██████╔╝██║  ██║███████╗╚██████╔╝██║ ╚████║                   ║
    ║    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝                   ║
    ║                                                                           ║
    ║          🎮 GAME MODE LAUNCHER 🎮                                         ║
    ║                                                                           ║
    ║     "Construction complete. Building. Unit ready."                        ║
    ║                                                                           ║
    ╚═══════════════════════════════════════════════════════════════════════════╝
    
    """)


def _print_urls(config: GameModeConfig):
    safe_print("\n" + "=" * 80)
    safe_print("🌐 AUREON GAME MODE - DASHBOARD URLs")
    safe_print("=" * 80)
    if config.command_center:
        safe_print("🎮 COMMAND CENTER (MAIN)   → http://localhost:8888")
    if config.queen_web_dashboard:
        safe_print("👑 Queen Web Dashboard     → http://localhost:5000")
    if config.queen_unified_dashboard:
        safe_print("👑 Queen Unified Dashboard → http://localhost:13000")
    if config.bot_hunter_dashboard:
        safe_print("🤖 Bot Hunter Dashboard    → http://localhost:9999")
    if config.global_bot_map:
        safe_print("🗺️  Global Bot Map          → http://localhost:12000")
    safe_print("=" * 80 + "\n")


def _shutdown_processes(processes: List[ServiceProcess]):
    safe_print("\n🧯 Shutting down Aureon Game Mode...")
    for svc in processes:
        try:
            safe_print(f"⏹️  Stopping {svc.name} ...")
            svc.process.terminate()
        except Exception:
            pass
    # Give graceful time, then force kill
    time.sleep(2.0)
    for svc in processes:
        try:
            if svc.process.poll() is None:
                svc.process.kill()
        except Exception:
            pass
    safe_print("✅ All systems stopped.")


def run_game_mode(config: GameModeConfig) -> int:
    processes: List[ServiceProcess] = []

    try:
        # PRIMARY: Command Center (the main dashboard)
        if config.command_center:
            processes.append(_start_process(
                "🎮 COMMAND CENTER",
                _build_python_command("aureon_command_center.py")
            ))
            time.sleep(2)  # Let it start up
        
        # Secondary dashboards (optional)
        if config.queen_web_dashboard:
            processes.append(_start_process(
                "Queen Web Dashboard",
                _build_python_command("queen_web_dashboard.py")
            ))

        if config.queen_unified_dashboard:
            processes.append(_start_process(
                "Queen Unified Dashboard",
                _build_python_command("aureon_queen_unified_dashboard.py")
            ))

        if config.bot_hunter_dashboard:
            processes.append(_start_process(
                "Bot Hunter Dashboard",
                _build_python_command("aureon_bot_hunter_dashboard.py")
            ))

        if config.global_bot_map:
            processes.append(_start_process(
                "Global Bot Map",
                _build_python_command("aureon_global_bot_map.py")
            ))

        if config.telemetry:
            processes.append(_start_process(
                "Telemetry Server",
                _build_python_command("telemetry_server.py")
            ))

        # TRADING ENGINE
        if config.start_trading:
            trade_args = ["--dry-run"] if config.dry_run else []
            processes.append(_start_process(
                "💰 TRADING ENGINE",
                _build_python_command("micro_profit_labyrinth.py", trade_args)
            ))

        _print_urls(config)

        # Open browser automatically
        if config.open_browser and config.command_center:
            time.sleep(2)
            safe_print("🌐 Opening Command Center in browser...")
            try:
                webbrowser.open("http://localhost:8888")
            except Exception:
                pass

        safe_print("🎮 Aureon Game Mode is LIVE!")
        safe_print("   Press Ctrl+C to stop all systems.")
        safe_print("")

        while True:
            # Keep main process alive while children run
            time.sleep(1.0)
            # If any child exits, keep running but warn
            for svc in list(processes):
                if svc.process.poll() is not None:
                    safe_print(f"⚠️  {svc.name} exited (code {svc.process.returncode}).")
                    processes.remove(svc)
            if not processes:
                safe_print("✅ All services stopped.")
                return 0

    except KeyboardInterrupt:
        safe_print("\n🧠 Command received: STOP")
        _shutdown_processes(processes)
        return 0
    except Exception as e:
        safe_print(f"\n❌ Game Mode error: {e}")
        _shutdown_processes(processes)
        return 1


def parse_args() -> GameModeConfig:
    parser = argparse.ArgumentParser(
        description="🎮 Aureon Game Mode Launcher - Red Alert 2 Style!",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python aureon_game_launcher.py              # Start Command Center + Trading (dry-run)
  python aureon_game_launcher.py --live       # Start with LIVE trading
  python aureon_game_launcher.py --no-trading # Dashboard only, no trading
  python aureon_game_launcher.py --all        # Start ALL dashboards
        """
    )
    parser.add_argument("--live", action="store_true", help="Enable LIVE trading (use with caution!)")
    parser.add_argument("--no-trading", action="store_true", help="Disable trading engine (dashboard only)")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    parser.add_argument("--all", action="store_true", help="Start ALL dashboards")
    parser.add_argument("--no-command-center", action="store_true", help="Disable main Command Center")
    parser.add_argument("--queen-web", action="store_true", help="Also start Queen Web Dashboard")
    parser.add_argument("--queen-unified", action="store_true", help="Also start Queen Unified Dashboard")
    parser.add_argument("--bot-hunter", action="store_true", help="Also start Bot Hunter Dashboard")
    parser.add_argument("--bot-map", action="store_true", help="Also start Global Bot Map")
    parser.add_argument("--telemetry", action="store_true", help="Start telemetry server")

    args = parser.parse_args()

    # --all enables everything
    if args.all:
        return GameModeConfig(
            start_trading=not args.no_trading,
            dry_run=not args.live,
            command_center=True,
            queen_web_dashboard=True,
            queen_unified_dashboard=True,
            bot_hunter_dashboard=True,
            global_bot_map=True,
            telemetry=True,
            open_browser=not args.no_browser,
        )

    return GameModeConfig(
        start_trading=not args.no_trading,
        dry_run=not args.live,
        command_center=not args.no_command_center,
        queen_web_dashboard=args.queen_web,
        queen_unified_dashboard=args.queen_unified,
        bot_hunter_dashboard=args.bot_hunter,
        global_bot_map=args.bot_map,
        telemetry=args.telemetry,
        open_browser=not args.no_browser,
    )


def main():
    _print_banner()
    config = parse_args()

    safe_print("=" * 80)
    if config.dry_run and config.start_trading:
        safe_print("🧪 Trading Mode: DRY-RUN (safe simulation)")
    elif config.start_trading:
        safe_print("⚠️  Trading Mode: LIVE (real money!)")
    else:
        safe_print("🛑 Trading Engine: DISABLED (dashboard only)")
    safe_print("=" * 80 + "\n")

    return_code = run_game_mode(config)
    sys.exit(return_code)


if __name__ == "__main__":
    main()
