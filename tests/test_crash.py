
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys

def guarded_exit(*args):
    print(f"BLOCKED EXIT: {args}")
    import traceback
    traceback.print_stack()

sys.exit = guarded_exit

print("Debugging start...")
try:
    import harmonic_wave_simulation
    print("Import success!")
except Exception as e:
    print(f"Import failed: {e}")
except SystemExit as e:
    print(f"System Exit encountered: {e}")
