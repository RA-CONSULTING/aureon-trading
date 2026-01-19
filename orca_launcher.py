#!/usr/bin/env python3
"""
🦈⚔️ ORCA LAUNCHER - START EVERYTHING AT ONCE ⚔️🦈
═══════════════════════════════════════════════════════════════════════════════

Launches BOTH:
  1. 🌐 Orca Command Center (Web Dashboard) - http://localhost:8888
  2. 🔪 Orca Kill Cycle (Autonomous Trading)

Just run: python orca_launcher.py

Gary Leckey | January 2026 | THE HUNT BEGINS!
═══════════════════════════════════════════════════════════════════════════════
"""

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


def print_banner():
    """Print the epic launch banner."""
    print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   🦈⚔️  ORCA UNIFIED LAUNCHER  ⚔️🦈                                            ║
║                                                                               ║
║   Starting ALL systems:                                                       ║
║                                                                               ║
║   1. 🌐 COMMAND CENTER (Web Dashboard)                                        ║
║      → http://localhost:8888                                                  ║
║      → Real-time positions, kills, predator detection                         ║
║                                                                               ║
║   2. 🔪 KILL CYCLE (Autonomous Trading)                                       ║
║      → War Room terminal display                                              ║
║      → Multi-exchange hunting                                                 ║
║                                                                               ║
║   Press Ctrl+C to stop all systems                                            ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """)


def run_command_center():
    """Run the Command Center in a subprocess."""
    print("🌐 Starting Command Center...")
    
    # Get the Python executable
    python = sys.executable
    script_dir = os.path.dirname(os.path.abspath(__file__))
    center_script = os.path.join(script_dir, 'orca_command_center.py')
    
    # Start the process
    process = subprocess.Popen(
        [python, center_script],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        cwd=script_dir
    )
    
    # Stream output (look for the "ONLINE" message)
    for line in iter(process.stdout.readline, ''):
        if 'ONLINE' in line or 'localhost:8888' in line:
            print(f"✅ Command Center: {line.strip()}")
            break
        elif 'Error' in line or 'error' in line:
            print(f"⚠️  Command Center: {line.strip()}")
    
    return process


def run_kill_cycle():
    """Run the Kill Cycle in a subprocess."""
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
    print_banner()
    
    processes = []
    
    try:
        # 1. Start Command Center first (background)
        center_process = run_command_center()
        processes.append(('Command Center', center_process))
        
        # 2. Open browser in background thread
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # Give Command Center time to start
        time.sleep(2)
        
        print("\n" + "="*80)
        print("🌐 Command Center running at: http://localhost:8888")
        print("="*80 + "\n")
        
        # 3. Start Kill Cycle (this will take over the terminal)
        kill_process = run_kill_cycle()
        processes.append(('Kill Cycle', kill_process))
        
        # Wait for Kill Cycle to finish (it won't unless stopped)
        kill_process.wait()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping all Orca systems...")
        
    finally:
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
