#!/usr/bin/env python3
"""
tests/vault/test_white_cell.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

White cell agent tests:
  • engages a failed_skill threat end-to-end
  • authors + executes a recovery compound skill via the CodeArchitect
  • reports outcome through ThoughtBus
  • detect_threats() finds seeded failures in the vault
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from aureon.vault import (
    AureonVault,
    WhiteCellAgent,
    ThreatReport,
    detect_threats,
)
from aureon.code_architect import CodeArchitect, SkillLibrary
from aureon.autonomous.vm_control import VMControlDispatcher


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


def _build_architect():
    tmp = Path(tempfile.mkdtemp(prefix="aureon_vault_wc_"))
    lib = SkillLibrary(storage_dir=tmp)
    dispatcher = VMControlDispatcher()
    sid = dispatcher.create_session(backend="simulated", name="wc-vm", make_default=True)
    dispatcher.get_session(sid).arm(dry_run=False)
    arch = CodeArchitect(library=lib, dispatcher=dispatcher)
    arch.bootstrap_atomics()
    return arch, dispatcher, tmp


def test_engage_failed_skill():
    print("\n[A] WhiteCellAgent engages a failed_skill threat")
    arch, dispatcher, tmp = _build_architect()
    try:
        cell = WhiteCellAgent(architect=arch)
        threat = ThreatReport(
            threat_id="fs_001",
            kind="failed_skill",
            description="synthetic failure",
            severity=0.7,
        )

        outcome = cell.engage(threat)

        check(outcome.threat_id == "fs_001", "outcome references the threat")
        check(outcome.recovery_skill_name is not None, "recovery skill authored")
        check(
            outcome.recovery_skill_name in arch.library,
            f"recovery skill stored in library ({outcome.recovery_skill_name})",
        )
        check(outcome.duration_s > 0, "duration measured")
        check(outcome.success, f"engagement succeeded (reasoning: {outcome.reasoning[:80]})")
    finally:
        dispatcher.destroy_all()
        shutil.rmtree(tmp, ignore_errors=True)


def test_engage_casimir_drift():
    print("\n[B] WhiteCellAgent engages a casimir_drift threat")
    arch, dispatcher, tmp = _build_architect()
    try:
        cell = WhiteCellAgent(architect=arch)
        threat = ThreatReport(
            threat_id="cd_001",
            kind="casimir_drift",
            description="drift force 7.0",
            severity=0.9,
        )
        outcome = cell.engage(threat)
        check(outcome.success, "casimir_drift recovery succeeded")
        check("recover_casimir_drift" in outcome.recovery_skill_name,
              f"recovery named correctly ({outcome.recovery_skill_name})")
    finally:
        dispatcher.destroy_all()
        shutil.rmtree(tmp, ignore_errors=True)


def test_detect_threats_from_vault():
    print("\n[C] detect_threats finds threats seeded in the vault")
    vault = AureonVault()

    # Seed a failed skill execution
    vault.ingest(
        topic="skill.executed.fail",
        payload={"ok": False, "skill_name": "broken_thing", "error": "timeout"},
        category="skill_execution",
    )
    # Seed a high Casimir force
    vault.last_casimir_force = 5.5
    # Seed a gamma spike
    vault.cortex_snapshot["gamma"] = 0.6
    # Seed low gratitude
    vault.gratitude_score = 0.2

    threats = detect_threats(vault, max_threats=10)

    kinds = {t.kind for t in threats}
    check(
        "casimir_drift" in kinds,
        f"casimir_drift detected (kinds: {kinds})",
    )
    check("low_gratitude" in kinds, "low_gratitude detected")
    check("gamma_spike" in kinds, "gamma_spike detected")
    check("failed_skill" in kinds, "failed_skill detected")
    check(len(threats) <= 10, "threat count respects max_threats")


def main():
    print("=" * 80)
    print("  WHITE CELL TEST SUITE")
    print("=" * 80)

    test_engage_failed_skill()
    test_engage_casimir_drift()
    test_detect_threats_from_vault()

    print()
    print("=" * 80)
    print(f"  RESULT: {PASS} passed, {FAIL} failed")
    print("=" * 80)
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
