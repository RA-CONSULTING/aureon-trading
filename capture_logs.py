#!/usr/bin/env python3
"""
Capture detailed error logs from ecosystem startup
"""
import subprocess
import sys
import os

print("🔍 Capturing ecosystem startup logs...\n")

# Run ecosystem and capture all output
result = subprocess.run(
    [sys.executable, '/workspaces/aureon-trading/aureon_unified_ecosystem.py'],
    cwd='/workspaces/aureon-trading',
    capture_output=True,
    text=True,
    timeout=10
)

print("STDOUT:")
print("="*70)
print(result.stdout if result.stdout else "(empty)")
print("\nSTDERR:")
print("="*70)
print(result.stderr if result.stderr else "(empty)")
print("\nReturn Code:", result.returncode)

# Also try importing directly to see the error
print("\n" + "="*70)
print("Direct Import Test:")
print("="*70)

sys.path.insert(0, '/workspaces/aureon-trading')

try:
    from aureon_unified_ecosystem import AureonKrakenEcosystem
    print("✅ Import successful")
    
    # Try to initialize
    ecosystem = AureonKrakenEcosystem(initial_balance=100.0, dry_run=True)
    print("✅ Initialization successful")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
