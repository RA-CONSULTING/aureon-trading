#!/usr/bin/env python3
"""
🎮👑 AUREON GAME LAUNCHER 👑🎮
=================================

RED ALERT 2 STYLE UNIFIED LAUNCHER
Starts the Command Center + Trading Engine together!
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
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
import tempfile
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
    system_hub: bool = False  # 🌌 NEW: System Hub Mind Map
    telemetry: bool = False
    open_browser: bool = True


@dataclass
class ServiceProcess:
    name: str
    command: List[str]
    process: subprocess.Popen
    log_file: Optional[object] = None


def _build_python_command(script_name: str, args: Optional[List[str]] = None) -> List[str]:
    cmd = [sys.executable, script_name]
    if args:
        cmd.extend(args)
    return cmd


def _sanitize_name(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name).lower()


def _get_log_path(name: str) -> str:
    log_dir = os.path.join(tempfile.gettempdir(), "aureon_service_logs")
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, f"{_sanitize_name(name)}.log")


def _start_process(name: str, cmd: List[str], log_to_file: bool = False) -> ServiceProcess:
    safe_print(f"🚀 Starting {name} ...")
    safe_print(f"   Command: {' '.join(cmd)}")  # DEBUG: Show the exact command
    log_file = None
    
    # Always create a log file for trading engine to capture startup issues
    is_trading_engine = "micro_profit_labyrinth" in " ".join(cmd) or "orca_complete_kill_cycle" in " ".join(cmd)
    
    if log_to_file or is_trading_engine:
        log_path = _get_log_path(name)
        log_file = open(log_path, "a", encoding="utf-8", errors="replace")
        if is_trading_engine and not log_to_file:
            safe_print(f"   📝 Logging to: {log_path}")
        process = subprocess.Popen(cmd, stdout=log_file, stderr=log_file)
    else:
        process = subprocess.Popen(cmd)
    return ServiceProcess(name=name, command=cmd, process=process, log_file=log_file)


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
    if config.system_hub:
        safe_print("🌌 System Hub Mind Map     → http://localhost:13001")
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
        try:
            if svc.log_file:
                svc.log_file.close()
        except Exception:
            pass
    safe_print("✅ All systems stopped.")


def run_game_mode(config: GameModeConfig) -> int:
    processes: List[ServiceProcess] = []
    orca_warroom_mode = config.start_trading and not config.dry_run

    try:
        # PRIMARY: Command Center (the main dashboard)
        if config.command_center:
            processes.append(_start_process(
                "🎮 COMMAND CENTER",
                _build_python_command("aureon_command_center.py"),
                log_to_file=orca_warroom_mode
            ))
            time.sleep(2)  # Let it start up
        
        # Secondary dashboards (optional)
        if config.queen_web_dashboard:
            processes.append(_start_process(
                "Queen Web Dashboard",
                _build_python_command("queen_web_dashboard.py"),
                log_to_file=orca_warroom_mode
            ))

        if config.queen_unified_dashboard:
            processes.append(_start_process(
                "Queen Unified Dashboard",
                _build_python_command("aureon_queen_unified_dashboard.py"),
                log_to_file=orca_warroom_mode
            ))

        if config.bot_hunter_dashboard:
            processes.append(_start_process(
                "Bot Hunter Dashboard",
                _build_python_command("aureon_bot_hunter_dashboard.py"),
                log_to_file=orca_warroom_mode
            ))

        if config.global_bot_map:
            processes.append(_start_process(
                "Global Bot Map",
                _build_python_command("aureon_global_bot_map.py"),
                log_to_file=orca_warroom_mode
            ))

        # OPTIONAL: System Hub Mind Map (NEW)
        if config.system_hub:
            processes.append(_start_process(
                "🌌 SYSTEM HUB",
                _build_python_command("aureon_system_hub_dashboard.py"),
                log_to_file=orca_warroom_mode
            ))

        if config.telemetry:
            processes.append(_start_process(
                "Telemetry Server",
                _build_python_command("telemetry_server.py"),
                log_to_file=orca_warroom_mode
            ))

        # TRADING ENGINE
        if config.start_trading:
            if config.dry_run:
                # Run for 24 hours (86400 seconds) instead of forever to avoid Windows subprocess issues
                trade_args = ["--dry-run", "--multi-exchange", "--duration", "86400"]
                processes.append(_start_process(
                    "💰 TRADING ENGINE (DRY-RUN)",
                    _build_python_command("micro_profit_labyrinth.py", trade_args)
                ))
            else:
                processes.append(_start_process(
                    "🐋 ORCA COMPLETE KILL CYCLE",
                    _build_python_command("orca_complete_kill_cycle.py", ["--autonomous"])
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
                    exit_code = svc.process.returncode
                    safe_print(f"⚠️  {svc.name} exited (code {exit_code}).")
                    
                    # For trading engine, show where the log is
                    is_trading_engine = "micro_profit_labyrinth" in " ".join(svc.command) or "orca_complete_kill_cycle" in " ".join(svc.command)
                    if is_trading_engine and svc.log_file:
                        log_path = svc.log_file.name
                        safe_print(f"   📝 Check log file: {log_path}")
                        safe_print(f"   💡 Tip: The trading engine might have exited due to a configuration issue.")
                        safe_print(f"   💡 Try running 'python micro_profit_labyrinth.py --dry-run --multi-exchange' directly to see errors.")
                    
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
    parser.add_argument("--system-hub", action="store_true", help="Also start System Hub Mind Map 🌌")
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
            system_hub=True,
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
        system_hub=args.system_hub,
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
