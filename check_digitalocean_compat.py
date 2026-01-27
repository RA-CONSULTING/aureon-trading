#!/usr/bin/env python3
"""
🔍 DigitalOcean Compatibility Checker
======================================
Validates that the Aureon system can run on DigitalOcean.
Checks paths, permissions, dependencies, network access.
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import json
from pathlib import Path
from typing import List, Tuple

def check_mark(passed: bool) -> str:
    return "✅" if passed else "❌"

def check_python_version() -> Tuple[bool, str]:
    """Check Python version >= 3.10"""
    major, minor = sys.version_info[:2]
    passed = major == 3 and minor >= 10
    return passed, f"Python {major}.{minor} ({'OK' if passed else 'Need 3.10+'})"

def check_dependencies() -> Tuple[bool, List[str]]:
    """Check if required Python packages are available"""
    required = [
        ("websockets", "WebSocket support"),
        ("asyncio", "Async I/O"),
        ("json", "JSON parsing"),
        ("pathlib", "Path handling"),
    ]
    
    results = []
    all_ok = True
    
    for module, desc in required:
        try:
            __import__(module)
            results.append(f"  {check_mark(True)} {module:15} - {desc}")
        except ImportError:
            results.append(f"  {check_mark(False)} {module:15} - {desc} [MISSING]")
            all_ok = False
    
    return all_ok, results

def check_paths() -> Tuple[bool, List[str]]:
    """Check that required directories exist or can be created"""
    paths_to_check = [
        ("ws_cache", "WebSocket data cache"),
        ("logs", "Log files"),
        (".", "Current directory (writable)"),
    ]
    
    results = []
    all_ok = True
    
    for path_str, desc in paths_to_check:
        path = Path(path_str)
        
        # Try to create if doesn't exist
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
                results.append(f"  {check_mark(True)} {str(path):20} - {desc} [CREATED]")
            except Exception as e:
                results.append(f"  {check_mark(False)} {str(path):20} - {desc} [CANNOT CREATE: {e}]")
                all_ok = False
        else:
            # Check if writable
            test_file = path / ".write_test"
            try:
                test_file.write_text("test")
                test_file.unlink()
                results.append(f"  {check_mark(True)} {str(path):20} - {desc} [WRITABLE]")
            except Exception as e:
                results.append(f"  {check_mark(False)} {str(path):20} - {desc} [NOT WRITABLE: {e}]")
                all_ok = False
    
    return all_ok, results

def check_state_files() -> Tuple[bool, List[str]]:
    """Check that state files can be created/read"""
    state_files = [
        "aureon_truth_prediction_state.json",
        "live_tv_stream.jsonl",
    ]
    
    results = []
    all_ok = True
    
    for filename in state_files:
        path = Path(filename)
        
        try:
            # Try to write
            if not path.exists():
                path.write_text(json.dumps({"test": True}))
                created = True
            else:
                created = False
            
            # Try to read
            content = path.read_text()
            
            # Clean up test file if we created it
            if created:
                path.unlink()
            
            results.append(f"  {check_mark(True)} {filename:40} - OK")
            
        except Exception as e:
            results.append(f"  {check_mark(False)} {filename:40} - ERROR: {e}")
            all_ok = False
    
    return all_ok, results

def check_network() -> Tuple[bool, List[str]]:
    """Check network connectivity"""
    results = []
    all_ok = True
    
    # Check internet connectivity
    import socket
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        results.append(f"  {check_mark(True)} Internet connectivity")
    except Exception as e:
        results.append(f"  {check_mark(False)} Internet connectivity [FAILED: {e}]")
        all_ok = False
    
    # Check DNS resolution
    try:
        socket.gethostbyname("binance.com")
        results.append(f"  {check_mark(True)} DNS resolution (binance.com)")
    except Exception as e:
        results.append(f"  {check_mark(False)} DNS resolution [FAILED: {e}]")
        all_ok = False
    
    return all_ok, results

def check_env_vars() -> Tuple[bool, List[str]]:
    """Check environment variables and .env file"""
    results = []
    warnings = 0
    
    # Check for .env file
    env_path = Path(".env")
    if env_path.exists():
        results.append(f"  {check_mark(True)} .env file exists")
        
        # Check if it contains placeholder keys
        env_content = env_path.read_text()
        if "your_" in env_content or "_here" in env_content:
            results.append(f"  ⚠️  .env contains placeholder keys (need real API keys)")
            warnings += 1
    else:
        results.append(f"  {check_mark(False)} .env file NOT FOUND (will use environment variables)")
        warnings += 1
    
    # Check critical environment variables
    critical_vars = [
        "WS_PRICE_CACHE_PATH",
    ]
    
    for var in critical_vars:
        if os.getenv(var):
            results.append(f"  {check_mark(True)} {var} is set")
        else:
            results.append(f"  ⚠️  {var} not set (will use default)")
            warnings += 1
    
    return warnings == 0, results

def main():
    print("🔍 AUREON DIGITALOCEAN COMPATIBILITY CHECK")
    print("=" * 60)
    print()
    
    all_checks_passed = True
    
    # Python version
    print("🐍 Python Version:")
    passed, msg = check_python_version()
    print(f"  {check_mark(passed)} {msg}")
    all_checks_passed &= passed
    print()
    
    # Dependencies
    print("📦 Python Dependencies:")
    passed, results = check_dependencies()
    for line in results:
        print(line)
    all_checks_passed &= passed
    print()
    
    # Paths
    print("📂 Directory Permissions:")
    passed, results = check_paths()
    for line in results:
        print(line)
    all_checks_passed &= passed
    print()
    
    # State files
    print("💾 State Files:")
    passed, results = check_state_files()
    for line in results:
        print(line)
    all_checks_passed &= passed
    print()
    
    # Network
    print("🌐 Network Connectivity:")
    passed, results = check_network()
    for line in results:
        print(line)
    all_checks_passed &= passed
    print()
    
    # Environment
    print("🔐 Environment Configuration:")
    passed, results = check_env_vars()
    for line in results:
        print(line)
    all_checks_passed &= passed
    print()
    
    # Summary
    print("=" * 60)
    if all_checks_passed:
        print("✅ ALL CHECKS PASSED - Ready for DigitalOcean deployment!")
        print()
        print("Next steps:")
        print("  1. Run: ./deploy_digitalocean.sh")
        print("  2. Configure API keys in .env")
        print("  3. Start services: sudo systemctl start aureon-ws-feeder")
        sys.exit(0)
    else:
        print("❌ SOME CHECKS FAILED - Review errors above")
        print()
        print("Common fixes:")
        print("  - Install missing packages: pip install websockets")
        print("  - Fix permissions: chmod 755 ws_cache logs")
        print("  - Check network: ping binance.com")
        print("  - Create .env: cp .env.example .env")
        sys.exit(1)

if __name__ == "__main__":
    main()
