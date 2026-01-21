#!/usr/bin/env python3
"""
Test script to diagnose Windows startup issues for Orca autonomous mode.
Run this on Windows to see where the crash occurs.
"""

import sys
import os

# Windows UTF-8 fix (MUST BE FIRST)
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        def _is_buffer_valid(stream):
            if not hasattr(stream, 'buffer'):
                return False
            try:
                return stream.buffer is not None and not stream.buffer.closed
            except (ValueError, AttributeError):
                return False
        if _is_buffer_valid(sys.stdout) and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if _is_buffer_valid(sys.stderr) and not _is_utf8_wrapper(sys.stderr):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception as e:
        pass  # Silent fail - continue anyway

def _safe_print(*args, **kwargs):
    """Print that won't crash if stdout is closed."""
    try:
        import builtins
        builtins.print(*args, **kwargs)
    except (ValueError, OSError, IOError):
        return

print = _safe_print

def test_step(step_name):
    """Test a step and report success/failure."""
    print(f"✓ {step_name}")
    return True

# Test each import step-by-step
try:
    test_step("Step 1: Basic imports")
    import time
    import logging
    
    test_step("Step 2: Logging configuration")
    logging.basicConfig(level=logging.WARNING)
    
    test_step("Step 3: Import OrcaKillCycle class")
    from orca_complete_kill_cycle import OrcaKillCycle
    
    test_step("Step 4: Create OrcaKillCycle instance")
    orca = OrcaKillCycle()
    
    test_step("Step 5: Check exchange connections")
    print(f"   Exchanges available: {list(orca.clients.keys())}")
    
    test_step("✅ ALL TESTS PASSED - System should work on Windows!")
    
except Exception as e:
    print(f"❌ FAILED at current step: {e}")
    import traceback
    traceback.print_exc()
