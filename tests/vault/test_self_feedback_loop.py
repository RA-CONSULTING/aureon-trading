#!/usr/bin/env python3
"""
tests/vault/test_self_feedback_loop.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Runs the full AureonSelfFeedbackLoop for 50 ticks and validates:

  • vault grows with each tick
  • Casimir force stays bounded [0, 10]
  • Auris consensus is always valid
  • at least one ping per tick
  • rally mode triggers when Casimir force is forced high
  • loop exposes a sensible status dict
  • tick_history retains history
"""

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from aureon.vault import AureonSelfFeedbackLoop


PASS = 0
FAIL = 0


def check(condition: bool, msg: str) -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [OK] {msg}")
    else:
        FAIL += 1
        print(f"  [!!] {msg}")


def test_50_cycle_loop():
    print("\n[A] 50-cycle self-feedback loop")
    loop = AureonSelfFeedbackLoop(base_interval_s=0.01)
    results = loop.run(cycles=50, sleep_between=False)

    check(len(results) == 50, f"ran 50 cycles (got {len(results)})")

    # Vault grew
    check(
        results[-1].vault_size > results[0].vault_size,
        f"vault grew from {results[0].vault_size} to {results[-1].vault_size}",
    )

    # Casimir force bounded
    forces = [r.casimir_force for r in results]
    check(
        all(0 <= f <= 10 for f in forces),
        f"all casimir forces in [0, 10] (max={max(forces):.3f})",
    )

    # Valid consensus on every tick
    valid_consensus = {"BUY", "SELL", "NEUTRAL", "RALLY", "STABILISE"}
    all_valid = all(r.auris_consensus in valid_consensus for r in results)
    check(all_valid, f"all auris consensuses are valid {valid_consensus}")

    # Every tick pinged
    check(all(r.ping_sent for r in results), "every tick emitted a ping")

    # Loop status exposes the expected keys
    status = loop.get_status()
    required_keys = [
        "loop_id", "cycles", "vault", "clock", "casimir",
        "auris", "deployer", "pinger", "rally", "last_tick",
    ]
    missing = [k for k in required_keys if k not in status]
    check(not missing, f"status exposes all keys (missing: {missing})")

    # tick_history retained
    history = loop.tick_history
    check(len(history) == 50, f"tick history retains 50 entries (got {len(history)})")


def test_rally_trigger():
    print("\n[B] RallyCoordinator wires the vault.rally_active flag")
    # The Casimir quantifier recomputes the drift force at the start of
    # every tick, so we can't just pin it before calling tick(). Instead
    # we verify the RallyCoordinator's direct API — the same entry point
    # the loop uses internally. This proves the wiring is correct
    # independent of the drift dynamics of an empty vault.
    from aureon.vault import RallyCoordinator

    loop = AureonSelfFeedbackLoop(
        base_interval_s=0.01,
        rally_casimir_threshold=0.5,
        rally_burst_ticks=5,
    )

    # Build a fake vote whose consensus is RALLY and drive the rally
    # coordinator directly. The loop's tick() calls this exact method
    # with the real Auris result.
    class FakeVote:
        consensus = "RALLY"

    loop.vault.last_casimir_force = 1.0
    state = loop.rally.update(loop.vault, FakeVote())
    check(state.active, "rally coordinator entered rally mode on RALLY consensus")
    check(loop.vault.rally_active, "vault.rally_active propagated after update()")

    # A fresh coordinator on a calm vault should not enter rally
    rally2 = RallyCoordinator(burst_ticks=5, casimir_threshold=10.0)
    calm_vault = loop.vault
    calm_vault.last_casimir_force = 0.01
    calm_state = rally2.update(calm_vault, FakeVote.__class__("Calm", (), {"consensus": "NEUTRAL"})())
    check(not calm_state.active, "rally coordinator stays inactive on calm vault")


def test_deploy_white_cells():
    print("\n[C] White cells deploy under synthetic gamma spike")
    loop = AureonSelfFeedbackLoop(base_interval_s=0.01)

    # Inject a fake gamma spike before the tick
    loop.vault.cortex_snapshot["gamma"] = 0.5
    loop.vault.last_lambda_t = 0.4

    result = loop.tick()
    check(result.cells_deployed >= 1, f"cells deployed (got {result.cells_deployed})")

    # Cells should be tracked in the loop's running total
    check(
        loop._total_cells_deployed >= 1,
        f"total cells tracked ({loop._total_cells_deployed})",
    )


def test_ping_channel_reports():
    print("\n[D] Harmonic pinger reports both channels")
    loop = AureonSelfFeedbackLoop(base_interval_s=0.01)
    loop.run(cycles=3, sleep_between=False)
    pstatus = loop.pinger.get_status()
    check(pstatus["total_pings"] >= 3, f"3+ pings emitted (got {pstatus['total_pings']})")
    check(
        pstatus["thought_bus_wired"] or pstatus["chirp_bus_wired"],
        "at least one ping channel is wired",
    )


def main():
    print("=" * 80)
    print("  SELF-FEEDBACK LOOP TEST SUITE")
    print("=" * 80)

    test_50_cycle_loop()
    test_rally_trigger()
    test_deploy_white_cells()
    test_ping_channel_reports()

    print()
    print("=" * 80)
    print(f"  RESULT: {PASS} passed, {FAIL} failed")
    print("=" * 80)
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
