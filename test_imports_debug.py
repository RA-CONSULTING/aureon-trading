from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
print("--- TESTING IMPORTS ---")

try:
    import aureon_stargate_protocol
    print("✅ aureon_stargate_protocol imported")
except ImportError as e:
    print(f"❌ aureon_stargate_protocol FAILED: {e}")

try:
    import queen_neuron
    print("✅ queen_neuron imported")
except ImportError as e:
    print(f"❌ queen_neuron FAILED: {e}")

try:
    import mycelium_whale_sonar
    print("✅ mycelium_whale_sonar imported")
except ImportError as e:
    print(f"❌ mycelium_whale_sonar FAILED: {e}")
