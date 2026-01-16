#!/usr/bin/env python3
"""
🪟💰 AUREON WINDOWS LAUNCHER 💰🪟
==================================

Safe launcher for Aureon Trading System on Windows 10/11.
Handles UTF-8 stream wrapping, asyncio event loop, and stderr closure issues.

Usage:
    python run_aureon_windows.py [arguments passed to micro_profit_labyrinth.py]

Examples:
    python run_aureon_windows.py --dry-run
    python run_aureon_windows.py --snowball
    python run_aureon_windows.py --multi-exchange
"""

import os
import sys
import subprocess
import platform

def main():
    """Launch Aureon Trading System with Windows-safe configuration."""
    
    # Verify Windows
    if sys.platform != 'win32':
        print("⚠️  This launcher is optimized for Windows. You may still use:")
        print("   python micro_profit_labyrinth.py [args]")
        print()
    
    # Set Windows-specific environment variables
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUNBUFFERED'] = '1'  # Unbuffered output
    
    # Build command
    cmd = [sys.executable, '-u', 'micro_profit_labyrinth.py'] + sys.argv[1:]
    
    print("🪟 AUREON WINDOWS LAUNCHER")
    print("=" * 60)
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Encoding: {sys.stdout.encoding}")
    print("=" * 60)
    print()
    
    try:
        # Run with proper error handling
        # Windows: Use CREATE_NEW_PROCESS_GROUP to isolate streams
        kwargs = {}
        if sys.platform == 'win32':
            kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP if hasattr(subprocess, 'CREATE_NEW_PROCESS_GROUP') else 0x00000200
        
        result = subprocess.run(cmd, capture_output=False, **kwargs)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user (Ctrl+C)")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error launching Aureon: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
