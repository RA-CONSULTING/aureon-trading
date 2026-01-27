#!/usr/bin/env python3
"""
🦈⚔️ ORCA LAUNCHER - START EVERYTHING AT ONCE ⚔️🦈
═══════════════════════════════════════════════════════════════════════════════

Launches ALL systems in parallel:
  1. 🌐 PARALLEL ORCHESTRATOR - All Intelligence Systems
  2. 🌐 Orca Command Center (Web Dashboard) - http://localhost:8888
  3. 🔪 Orca Kill Cycle (Autonomous Trading)

The Parallel Orchestrator starts FIRST, ensuring:
  • ThoughtBus (Central Nervous System)
  • Queen Hive Mind (Central Consciousness)
  • Probability Nexus (9-Factor Validation)
  • Global Wave Scanner (A-Z Market Coverage)
  • Miner Brain (Critical Thinking)
  • Mycelium Network (Distributed Intelligence)
  • Timeline Oracle (7-Day Predictions)
  • Quantum Mirror (Branch Coherence)
  • Whale Sonar (Subsystem Health)
  • Avalanche Harvester (Profit Scraping)

Just run: python orca_launcher.py

Gary Leckey | January 2026 | THE HUNT BEGINS!
═══════════════════════════════════════════════════════════════════════════════
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
import subprocess
import time
import threading
import signal

# Windows UTF-8 fix (MANDATORY)
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        if hasattr(sys.stdout, 'buffer') and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if hasattr(sys.stderr, 'buffer') and not _is_utf8_wrapper(sys.stderr):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass


# Global orchestrator reference
_orchestrator = None


def print_banner():
    """Print the epic launch banner."""
    print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   🦈⚔️  ORCA UNIFIED LAUNCHER  ⚔️🦈                                            ║
║                                                                               ║
║   Starting ALL systems in parallel:                                           ║
║                                                                               ║
║   PHASE 1: 🌐 PARALLEL ORCHESTRATOR                                           ║
║      → ThoughtBus, Queen, Validators, Scanners                               ║
║      → Miner Brain, Mycelium, Timeline Oracle                                ║
║      → All intelligence feeds warming up                                      ║
║                                                                               ║
║   PHASE 2: 🌐 COMMAND CENTER (Web Dashboard)                                  ║
║      → http://localhost:8888                                                  ║
║      → Real-time positions, kills, intelligence                              ║
║                                                                               ║
║   PHASE 3: 🔪 KILL CYCLE (Autonomous Trading)                                 ║
║      → War Room terminal display                                              ║
║      → Multi-exchange hunting with full intel                                ║
║                                                                               ║
║   Press Ctrl+C to stop all systems                                            ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """)


def start_parallel_orchestrator():
    """
    Start the Parallel Orchestrator to initialize all intelligence systems.
    This MUST run before the Kill Cycle to ensure all feeds are warm.
    """
    global _orchestrator
    
    print("\n" + "🌐" * 30)
    print("  PHASE 1: PARALLEL ORCHESTRATOR - INITIALIZING ALL SYSTEMS")
    print("🌐" * 30 + "\n")
    
    try:
        from aureon_parallel_orchestrator import get_orchestrator, start_all_parallel_systems
        
        # Get the orchestrator singleton
        _orchestrator = get_orchestrator()
        
        # Start all systems with a 15-second warm-up
        results = start_all_parallel_systems(skip_warmup=False)
        
        # Check if critical systems are online
        if _orchestrator.is_ready():
            print("\n✅ PARALLEL ORCHESTRATOR: ALL CRITICAL SYSTEMS ONLINE")
            
            # Count successes
            success_count = sum(1 for v in results.values() if v)
            total = len(results)
            print(f"   {success_count}/{total} systems initialized successfully")
            
            return True
        else:
            print("\n⚠️ PARALLEL ORCHESTRATOR: Some systems failed to start")
            print("   Continuing anyway - Orca will use available systems")
            return True
            
    except ImportError as e:
        print(f"⚠️ Parallel Orchestrator not available: {e}")
        print("   Continuing without parallel intelligence - Orca will initialize systems itself")
        return False
    except Exception as e:
        print(f"❌ Error starting Parallel Orchestrator: {e}")
        print("   Continuing without parallel intelligence")
        return False


def run_command_center():
    """Run the Command Center in a subprocess."""
    print("\n" + "🌐" * 30)
    print("  PHASE 2: COMMAND CENTER - WEB DASHBOARD")
    print("🌐" * 30 + "\n")
    
    print("🌐 Starting Command Center...")
    
    # Get the Python executable
    python = sys.executable
    script_dir = os.path.dirname(os.path.abspath(__file__))
    center_script = os.path.join(script_dir, 'orca_command_center.py')
    
    # Start the process with UTF-8 encoding for Windows compatibility
    process = subprocess.Popen(
        [python, center_script],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        cwd=script_dir,
        encoding='utf-8',
        errors='replace'
    )
    
    # Stream output (look for the "ONLINE" message)
    try:
        for line in iter(process.stdout.readline, ''):
            if 'ONLINE' in line or 'localhost:8888' in line:
                print(f"✅ Command Center: {line.strip()}")
                break
            elif 'Error' in line or 'error' in line:
                print(f"⚠️  Command Center: {line.strip()}")
    except UnicodeDecodeError:
        print("✅ Command Center starting...")
    
    return process


def run_kill_cycle():
    """Run the Kill Cycle in a subprocess."""
    print("\n" + "🔪" * 30)
    print("  PHASE 3: KILL CYCLE - AUTONOMOUS TRADING")
    print("🔪" * 30 + "\n")
    
    print("🔪 Starting Kill Cycle...")
    
    # Get the Python executable
    python = sys.executable
    script_dir = os.path.dirname(os.path.abspath(__file__))
    kill_script = os.path.join(script_dir, 'orca_complete_kill_cycle.py')
    
    # Start the process with --autonomous flag
    process = subprocess.Popen(
        [python, kill_script, '--autonomous'],
        stdout=None,  # Let it print to console
        stderr=None,
        cwd=script_dir
    )
    
    return process


def open_browser():
    """Open the dashboard in the default browser."""
    time.sleep(3)  # Wait for server to start
    
    url = "http://localhost:8888"
    
    try:
        if sys.platform == 'win32':
            os.startfile(url)
        elif sys.platform == 'darwin':
            subprocess.run(['open', url])
        else:
            # Linux - try xdg-open or use $BROWSER env var
            browser = os.environ.get('BROWSER')
            if browser:
                subprocess.run([browser, url])
            else:
                subprocess.run(['xdg-open', url], stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"📎 Open dashboard manually: {url}")


def main():
    """Launch everything!"""
    global _orchestrator
    
    print_banner()
    
    processes = []
    
    try:
        # PHASE 1: Start Parallel Orchestrator FIRST
        orchestrator_ready = start_parallel_orchestrator()
        
        # PHASE 2: Start Command Center (background)
        center_process = run_command_center()
        processes.append(('Command Center', center_process))
        
        # Open browser in background thread
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # Give Command Center time to start
        time.sleep(2)
        
        print("\n" + "="*80)
        print("🌐 Command Center running at: http://localhost:8888")
        if orchestrator_ready:
            print("🧠 Parallel Intelligence: ACTIVE (All systems feeding Queen)")
        print("="*80 + "\n")
        
        # PHASE 3: Start Kill Cycle (this will take over the terminal)
        kill_process = run_kill_cycle()
        processes.append(('Kill Cycle', kill_process))
        
        # Wait for Kill Cycle to finish (it won't unless stopped)
        kill_process.wait()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping all Orca systems...")
        
    finally:
        # Shutdown orchestrator first
        if _orchestrator:
            print("   Stopping Parallel Orchestrator...")
            try:
                _orchestrator.shutdown()
            except Exception:
                pass
        
        # Clean up all processes
        for name, proc in processes:
            if proc and proc.poll() is None:
                print(f"   Stopping {name}...")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
        
        print("\n🦈 All systems stopped. The hunt is over.")


if __name__ == '__main__':
    main()
