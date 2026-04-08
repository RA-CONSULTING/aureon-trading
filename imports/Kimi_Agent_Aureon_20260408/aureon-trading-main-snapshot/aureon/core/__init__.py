"""aureon.core — Central nervous system of the Aureon platform.

Houses the ThoughtBus event system, Nexus core orchestrator, and Mycelium
network for inter-module communication. ChirpBus and health-check services
ensure liveness across the stack. Connects to all other aureon domains as
the foundational messaging and coordination layer.
"""
