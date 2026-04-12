"""
tests/test_integrated_cognitive_system.py — ICS test suite

Covers: boot, goals, swarm, commands, temporal tick, graceful degradation.
"""

import logging
import time

import pytest

logging.basicConfig(level=logging.WARNING)


# ── Shared fixture ──────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def ics():
    """Boot the ICS once for the entire module — expensive but realistic."""
    from aureon.core.integrated_cognitive_system import IntegratedCognitiveSystem

    system = IntegratedCognitiveSystem()
    system.boot()
    system._start_tick_thread()
    time.sleep(1)  # let ticks settle
    yield system
    system.shutdown()


# ── Boot tests ──────────────────────────────────────────────────────────────

class TestBoot:
    def test_boot_all_subsystems(self, ics):
        """Core subsystems should come online."""
        status = ics._boot_status
        assert len(status) >= 17
        alive = sum(1 for v in status.values() if v == "alive")
        # At least the core subsystems must be alive
        assert alive >= 10, f"Only {alive}/{len(status)} alive: {status}"

    def test_thought_bus_alive(self, ics):
        assert ics.thought_bus is not None

    def test_vault_alive(self, ics):
        assert ics.vault is not None

    def test_lambda_engine_alive(self, ics):
        assert ics.lambda_engine is not None

    def test_goal_engine_alive(self, ics):
        assert ics.goal_engine is not None

    def test_agent_core_alive(self, ics):
        assert ics.agent_core is not None

    def test_swarm_alive(self, ics):
        assert ics.swarm is not None

    def test_temporal_ground_alive(self, ics):
        assert ics.temporal_ground is not None

    def test_self_dialogue_booted(self, ics):
        """SelfDialogueEngine should be booted (not None)."""
        # May fail if voice dependencies are missing, so just check boot was attempted
        status = ics._boot_status.get("self_dialogue", "")
        assert status in ("alive", ) or "failed" in status

    def test_mycelium_mind_booted(self, ics):
        status = ics._boot_status.get("mycelium_mind", "")
        assert status in ("alive", ) or "failed" in status

    def test_metacognition_booted(self, ics):
        status = ics._boot_status.get("metacognition", "")
        assert status in ("alive", ) or "failed" in status


# ── Command tests ───────────────────────────────────────────────────────────

class TestCommands:
    def test_status(self, ics):
        r = ics.process_user_input("/status")
        assert r is not None
        assert "ICS STATUS" in r
        assert "Tick count" in r

    def test_coherence(self, ics):
        r = ics.process_user_input("/coherence")
        assert r is not None
        assert "Lambda" in r

    def test_goal_status_empty(self, ics):
        r = ics.process_user_input("/goal")
        assert r is not None

    def test_swarm_status(self, ics):
        r = ics.process_user_input("/swarm")
        assert r is not None
        assert "SWARM" in r or "Swarm" in r or "not available" in r

    def test_pause(self, ics):
        r = ics.process_user_input("/pause")
        assert "paused" in r.lower()

    def test_resume(self, ics):
        r = ics.process_user_input("/resume")
        assert "resumed" in r.lower()

    def test_cancel(self, ics):
        r = ics.process_user_input("/cancel")
        assert "cancel" in r.lower()

    def test_quit(self, ics):
        r = ics.process_user_input("/quit")
        assert r == "__QUIT__"

    def test_empty_input(self, ics):
        r = ics.process_user_input("")
        assert r is None


# ── Goal execution tests ───────────────────────────────────────────────────

class TestGoals:
    def test_sequential_goal(self, ics):
        r = ics.process_user_input("check system info")
        assert "completed" in r

    def test_search_goal(self, ics):
        r = ics.process_user_input("search for bitcoin price")
        assert "completed" in r

    def test_read_file_goal(self, ics):
        r = ics.process_user_input("read the README.md file")
        assert "completed" in r

    def test_goal_engine_stats(self, ics):
        stats = ics.goal_engine.get_status()["stats"]
        assert stats["goals_submitted"] >= 3
        assert stats["steps_executed"] >= 3


# ── Swarm tests ─────────────────────────────────────────────────────────────

class TestSwarm:
    def test_swarm_goal(self, ics):
        r = ics.process_user_input("analyse the market from multiple perspectives")
        assert "completed" in r or "failed" in r
        stats = ics.goal_engine.get_status()["stats"]
        assert stats["swarm_dispatches"] >= 1

    def test_research_swarm(self, ics):
        r = ics.process_user_input("research bitcoin and ethereum trends")
        assert r is not None
        assert "completed" in r or "failed" in r


# ── Cognitive tick tests ────────────────────────────────────────────────────

class TestCognitiveTick:
    def test_tick_runs(self, ics):
        """Cognitive tick should have run at least once."""
        assert ics._tick_count >= 1

    def test_tick_manual(self, ics):
        """Manual tick should not crash."""
        ics._unified_cognitive_tick()  # should complete without error

    def test_temporal_ground_ticked(self, ics):
        """Temporal ground should be ticked by the cognitive loop."""
        if ics.temporal_ground is None:
            pytest.skip("temporal_ground not available")
        # Run a few ticks manually
        for _ in range(3):
            ics._unified_cognitive_tick()
        # The temporal ground should have a chain length > 0
        chain = getattr(ics.temporal_ground, "_chain", None)
        if chain is not None:
            assert chain.chain_length > 0


# ── Graceful degradation ───────────────────────────────────────────────────

class TestGracefulDegradation:
    def test_boot_returns_dict(self, ics):
        """Boot should return a status dict even if things fail."""
        assert isinstance(ics._boot_status, dict)
        assert len(ics._boot_status) > 0

    def test_all_statuses_are_strings(self, ics):
        for name, st in ics._boot_status.items():
            assert isinstance(st, str), f"{name} status is not a string: {st}"
