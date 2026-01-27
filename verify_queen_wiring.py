from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import logging
import os

# Ensure we are in the workspace
sys.path.append(os.getcwd())

logging.basicConfig(level=logging.INFO)

print("--- VERIFYING QUEEN FULLY ONLINE (IN VENV) ---")
try:
    from queen_fully_online import QueenFullyOnline
    q = QueenFullyOnline(use_voice=False, use_bus=False)
    print("✅ Queen instantiated successfully.")
    print("   Systems Wired:")
    for sys_name in q.systems:
        print(f"   - {sys_name}")
except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)
print("--- VERIFICATION COMPLETE ---")