#!/usr/bin/env python3
"""
Aureon Boot Diagnostic
======================
Boots the Integrated Cognitive System and prints the live status
of every subsystem — vault, mycelium, thought bus, goal engine, etc.
"""
import io, sys, os, time, logging

# Force unbuffered UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)

# Suppress all internal logging — we control what prints
logging.disable(logging.CRITICAL)

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PHASE_LABELS = {
    "thought_bus":        "ThoughtBus      (neural signal highway)",
    "vault":              "AureonVault     (memory + knowledge store)",
    "temporal_knowledge": "TemporalKnowledge (time-aware memory)",
    "temporal_dialer":    "TemporalDialer  (HNC frequency tuner)",
    "self_dialogue":      "SelfDialogue    (inner voice engine)",
    "lambda_engine":      "LambdaEngine    (HNC master formula)",
    "cortex":             "QueenCortex     (decision + veto layer)",
    "feedback_loop":      "FeedbackLoop    (self-improvement loop)",
    "sentient_loop":      "SentientLoop    (consciousness cycle)",
    "mycelium_mind":      "MyceliumMind    (thought propagation mesh)",
    "metacognition":      "Metacognition   (5W self-reflection)",
    "love_stream":        "LoveStream      (standing wave coherence)",
    "conscience":         "QueenConscience (ethical substrate)",
    "source_law":         "SourceLaw       (coherence gate)",
    "mirror":             "NarratorMirror  (self-awareness)",
    "agent_core":         "AgentCore       (autonomous action)",
    "action_bridge":      "ActionBridge    (goal -> real-world act)",
    "being_model":        "BeingModel      (identity + continuity)",
    "elephant_memory":    "ElephantMemory  (cross-session recall)",
    "swarm":              "SwarmMotion     (multi-agent mesh)",
    "temporal_ground":    "TemporalGround  (time anchor)",
    "nexus":              "AureonNexus     (central nervous system)",
    "knowledge_dataset":  "KnowledgeDataset (queen knowledge base)",
    "knowledge_interpreter": "KnowledgeInterpreter (semantic parser)",
    "stash_pockets":      "StashPockets    (queen working memory)",
    "goal_engine":        "GoalEngine      (think -> act -> achieve)",
    "dashboard":          "CognitiveDashboard (live cognitive HUD)",
    "auris":              "AurisMetacognition (perception layer)",
    "phi_bridge":         "PhiBridge       (device mesh gateway)",
    "vault_ui":           "VaultUI         (web interface)",
    "world_data":         "WorldDataIngester (live market feed)",
    "self_research":      "SelfResearchLoop (autonomous learning)",
    "vault_bridge":       "VaultKnowledgeBridge (vault <-> queen)",
    "integrations":       "Integrations    (external wiring)",
    "prose_composer":     "ProseComposer   (natural language output)",
}

print()
print("=" * 65)
print("  AUREON INTEGRATED COGNITIVE SYSTEM — BOOT DIAGNOSTIC")
print("=" * 65)
print()

t0 = time.time()

print("  Importing subsystems...", flush=True)
from aureon.core.integrated_cognitive_system import IntegratedCognitiveSystem
print(f"  ICS loaded in {time.time()-t0:.1f}s")
print()
print("  Booting all phases...")
print()

ics = IntegratedCognitiveSystem()
boot_t0 = time.time()
status = ics.boot()
elapsed = time.time() - boot_t0

# Print results
alive, failed, skipped = [], [], []
for key, state in status.items():
    label = PHASE_LABELS.get(key, key)
    if state == "alive":
        print(f"  [LIVE]   {label}")
        alive.append(key)
    elif state.startswith("failed"):
        reason = state.replace("failed: ", "")
        print(f"  [FAIL]   {label}")
        print(f"           -> {reason[:80]}")
        failed.append(key)
    else:
        print(f"  [SKIP]   {label}")
        skipped.append(key)

print()
print("=" * 65)
print(f"  BOOT COMPLETE in {elapsed:.1f}s")
print(f"  LIVE:    {len(alive)}")
print(f"  FAILED:  {len(failed)}")
print(f"  SKIPPED: {len(skipped)}")
print("=" * 65)
print()

if failed:
    print("  FAILED SUBSYSTEMS:")
    for k in failed:
        print(f"    - {PHASE_LABELS.get(k, k)}: {status[k]}")
    print()
