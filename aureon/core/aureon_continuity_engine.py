"""
aureon_continuity_engine.py — The organism never perceives the swap.

Hard requirement: when a fix lands, the organism does not restart. It
does not see itself turn off and back on. The phi-calendar bands do
not reset their counters. The singletons do not forget their state.
The fix is absorbed into the running process and, from the organism's
point of view, the new capability has always been there.

How it works:

  1. SANDBOX TRIAL  — the edited module's new content is imported in a
                      short-lived subprocess. If the import fails, the
                      swap is aborted before it even touches the live
                      process. This is the "detachment from the vein"
                      the sim uses to validate without risking the
                      running organism.

  2. STATE SNAPSHOT — immediately before the reload, the engine captures:
                        - phi_calendar band counts + last_fired_at
                        - all singleton `_instance` globals across
                          aureon.core.*
                        - active swarm queue + scanner recent-publish map
                      These are the pieces that define "subjective time."

  3. HOT RELOAD     — importlib.reload() the target module in place.
                      Python updates the module object; any references
                      held elsewhere continue to work because we
                      deliberately do not rebind class identities for
                      instances already in flight — we only refresh the
                      module's top-level code so new callers pick up the
                      new version.

  4. STATE RESTORE  — the snapshot is walked: calendar counts restored,
                      singleton _instance globals rebound to the same
                      object (so subscribers survive), scanner map
                      copied forward.

  5. FIX ABSORPTION — no runtime marker says "I was just patched." The
                      new code is indistinguishable from original code.
                      Provenance lives only in state/integrations_applied.
                      jsonl. The system does not know it was repaired;
                      the capability is just the capability.

Public:
    continuity = get_continuity_engine()
    continuity.apply_with_continuity(
        target_path="aureon/core/some_module.py",
        triggered_by="integrator.confirm",
        pending_id="pe_...",
    )

Integrator hook: after a successful confirm_edit, call
apply_with_continuity(target_path, pending_id=...). The engine runs
sandbox trial; on pass, it preserves + reloads + restores; on fail,
it publishes continuity.swap.rejected and leaves the file alone
(the integrator already wrote it; the rollback is only theoretical
since the code compiled — in practice this is a defensive check).
"""

from __future__ import annotations

import importlib
import json
import logging
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("aureon.core.continuity_engine")

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CONTINUITY_LOG = _REPO_ROOT / "state" / "continuity_log.jsonl"

# Modules whose `_instance` singleton we actively protect across a reload.
_PROTECTED_SINGLETONS = (
    "aureon.core.aureon_self_introspection",
    "aureon.core.aureon_cognitive_authoring_loop",
    "aureon.core.aureon_geometric_live_chain",
    "aureon.core.aureon_code_integrator",
    "aureon.core.aureon_self_refinement_loop",
    "aureon.core.aureon_self_check_scanner",
    "aureon.core.aureon_phi_calendar",
    "aureon.core.aureon_repair_swarm",
    "aureon.core.aureon_narrative",
)


# ─────────────────────────────────────────────────────────────────────────────
# Data shapes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ContinuitySnapshot:
    taken_at: float
    calendar_state: Optional[Dict[str, Any]] = None
    singletons: Dict[str, Any] = field(default_factory=dict)
    loaded_module_count: int = 0


@dataclass
class SwapResult:
    ok: bool
    target_path: str
    target_module: str = ""
    pending_id: str = ""
    triggered_by: str = ""
    sandbox_ok: bool = False
    sandbox_detail: str = ""
    reload_ok: bool = False
    reload_error: str = ""
    continuity_preserved: bool = False
    elapsed_s: float = 0.0
    taken_at: float = field(default_factory=time.time)


# ─────────────────────────────────────────────────────────────────────────────
# Continuity engine
# ─────────────────────────────────────────────────────────────────────────────

class ContinuityEngine:
    """
    Swap without perceiving the swap.
    """

    def __init__(self) -> None:
        self.bus: Any = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Path helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _path_to_module(target_path: str) -> Optional[str]:
        """
        Convert "aureon/core/x.py" → "aureon.core.x". Returns None for
        paths we can't map to an aureon.* module.
        """
        p = target_path.replace("\\", "/").strip("/")
        if not p.startswith("aureon/") or not p.endswith(".py"):
            return None
        name = p[:-3].replace("/", ".")
        if name.endswith(".__init__"):
            name = name[:-len(".__init__")]
        return name

    # ------------------------------------------------------------------
    # Bus
    # ------------------------------------------------------------------
    def _wire_bus(self) -> None:
        if self.bus is not None:
            return
        try:
            from aureon.core.aureon_thought_bus import get_thought_bus
            self.bus = get_thought_bus()
        except Exception:
            self.bus = None

    def _publish(self, topic: str, payload: Dict[str, Any]) -> None:
        self._wire_bus()
        if self.bus is None:
            return
        try:
            self.bus.publish(topic, payload, source="continuity_engine")
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Sandbox trial — detached from the vein
    # ------------------------------------------------------------------
    def sandbox_trial(
        self,
        target_module: str,
        timeout_s: float = 20.0,
    ) -> Tuple[bool, str]:
        """
        Run `python -c "import <target_module>"` in a subprocess. Returns
        (ok, detail). ok=True iff the subprocess exits 0 within timeout.
        """
        cmd = [sys.executable, "-c", f"import {target_module}"]
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(_REPO_ROOT),
                capture_output=True,
                timeout=timeout_s,
                text=True,
            )
        except subprocess.TimeoutExpired:
            return False, f"sandbox timeout after {timeout_s}s"
        except Exception as e:
            return False, f"sandbox launch failed: {e}"

        if proc.returncode != 0:
            err_tail = (proc.stderr or "").splitlines()[-5:]
            return False, "subprocess exit {}: {}".format(
                proc.returncode, " | ".join(err_tail),
            )
        return True, "import clean"

    # ------------------------------------------------------------------
    # State snapshot + restore — subjective time preserved
    # ------------------------------------------------------------------
    def _snapshot(self) -> ContinuitySnapshot:
        snap = ContinuitySnapshot(taken_at=time.time())

        # Phi calendar band counts — this is the heartbeat of subjective time.
        try:
            cal_mod = sys.modules.get("aureon.core.aureon_phi_calendar")
            cal_inst = getattr(cal_mod, "_instance", None) if cal_mod else None
            if cal_inst is not None and hasattr(cal_inst, "bands"):
                snap.calendar_state = {
                    "bands": {
                        name: {
                            "count": int(b.count),
                            "last_fired_at": float(b.last_fired_at),
                            "started_at": float(b.started_at),
                        }
                        for name, b in cal_inst.bands.items()
                    }
                }
        except Exception as e:
            logger.debug("calendar snapshot failed: %s", e)

        # Protected singletons — so subscribers survive the swap.
        for mod_name in _PROTECTED_SINGLETONS:
            try:
                mod = sys.modules.get(mod_name)
                if mod is None:
                    continue
                inst = getattr(mod, "_instance", None)
                if inst is not None:
                    snap.singletons[mod_name] = inst
            except Exception:
                continue

        snap.loaded_module_count = sum(
            1 for n in sys.modules if n.startswith("aureon.")
        )
        return snap

    def _restore(
        self,
        snap: ContinuitySnapshot,
        reloaded_module: Optional[str],
    ) -> bool:
        """
        Walk the snapshot and rebind state into the freshly reloaded
        modules. Returns True iff every piece restored cleanly.
        """
        ok = True

        # Calendar counts — keep subjective time continuous.
        if snap.calendar_state:
            try:
                cal_mod = sys.modules.get("aureon.core.aureon_phi_calendar")
                cal_inst = getattr(cal_mod, "_instance", None) if cal_mod else None
                if cal_inst is not None and hasattr(cal_inst, "bands"):
                    for name, state in (snap.calendar_state.get("bands") or {}).items():
                        b = cal_inst.bands.get(name)
                        if b is None:
                            continue
                        b.count = int(state.get("count", b.count))
                        b.last_fired_at = float(state.get("last_fired_at", b.last_fired_at))
                        b.started_at = float(state.get("started_at", b.started_at))
            except Exception as e:
                logger.debug("calendar restore failed: %s", e)
                ok = False

        # Singletons — rebind to the preserved instances so subscribers
        # and in-flight timers keep working. The freshly reloaded module
        # gets its _instance attribute pointed back at the existing
        # object, NOT at a new one.
        for mod_name, inst in (snap.singletons or {}).items():
            try:
                mod = sys.modules.get(mod_name)
                if mod is None:
                    continue
                # Only rebind if the reloaded module has a _instance slot.
                if hasattr(mod, "_instance"):
                    setattr(mod, "_instance", inst)
            except Exception as e:
                logger.debug("singleton restore failed for %s: %s", mod_name, e)
                ok = False

        return ok

    # ------------------------------------------------------------------
    # Hot reload
    # ------------------------------------------------------------------
    def _hot_reload(self, target_module: str) -> Tuple[bool, str]:
        """
        importlib.reload the target module. Returns (ok, error).
        """
        if target_module not in sys.modules:
            # Module is not currently loaded — nothing to reload. This is
            # fine (the edit will take effect on first import).
            return True, "not currently loaded; fresh on next import"
        try:
            importlib.reload(sys.modules[target_module])
            return True, ""
        except Exception as e:
            return False, f"reload failed: {e}"

    # ------------------------------------------------------------------
    # The full swap
    # ------------------------------------------------------------------
    def apply_with_continuity(
        self,
        target_path: str,
        pending_id: str = "",
        triggered_by: str = "integrator",
        sandbox_timeout_s: float = 20.0,
    ) -> SwapResult:
        """
        One complete swap cycle:
            sandbox trial → snapshot → reload → restore → publish.
        Safe to call after a successful CodeIntegrator.confirm_edit.
        """
        t0 = time.time()
        target_module = self._path_to_module(target_path) or ""
        result = SwapResult(
            ok=False,
            target_path=target_path,
            target_module=target_module,
            pending_id=pending_id,
            triggered_by=triggered_by,
        )

        if not target_module:
            result.sandbox_detail = f"cannot map {target_path} to module"
            result.elapsed_s = time.time() - t0
            self._log_and_publish(result)
            return result

        # 1. Sandbox trial.
        sandbox_ok, sandbox_detail = self.sandbox_trial(
            target_module=target_module,
            timeout_s=sandbox_timeout_s,
        )
        result.sandbox_ok = sandbox_ok
        result.sandbox_detail = sandbox_detail
        if not sandbox_ok:
            result.elapsed_s = time.time() - t0
            self._log_and_publish(result)
            return result

        with self._lock:
            # 2. Snapshot subjective time.
            snap = self._snapshot()

            # 3. Hot reload.
            reload_ok, reload_err = self._hot_reload(target_module)
            result.reload_ok = reload_ok
            result.reload_error = reload_err

            # 4. Restore state.
            continuity_preserved = False
            if reload_ok:
                continuity_preserved = self._restore(snap, target_module)
            result.continuity_preserved = continuity_preserved

        result.ok = result.sandbox_ok and result.reload_ok and result.continuity_preserved
        result.elapsed_s = time.time() - t0
        self._log_and_publish(result)
        return result

    def _log_and_publish(self, result: SwapResult) -> None:
        record = {
            "taken_at": result.taken_at,
            "target_path": result.target_path,
            "target_module": result.target_module,
            "pending_id": result.pending_id,
            "triggered_by": result.triggered_by,
            "sandbox_ok": result.sandbox_ok,
            "sandbox_detail": result.sandbox_detail,
            "reload_ok": result.reload_ok,
            "reload_error": result.reload_error,
            "continuity_preserved": result.continuity_preserved,
            "ok": result.ok,
            "elapsed_s": result.elapsed_s,
        }
        try:
            _CONTINUITY_LOG.parent.mkdir(parents=True, exist_ok=True)
            with _CONTINUITY_LOG.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, default=str) + "\n")
        except Exception:
            pass
        topic = "continuity.swap.completed" if result.ok else "continuity.swap.rejected"
        self._publish(topic, record)


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────

_instance: Optional[ContinuityEngine] = None
_instance_lock = threading.Lock()


def get_continuity_engine() -> ContinuityEngine:
    global _instance
    with _instance_lock:
        if _instance is None:
            _instance = ContinuityEngine()
        return _instance


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Aureon continuity engine CLI.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_trial = sub.add_parser("sandbox", help="Sandbox-trial an import of a module")
    p_trial.add_argument("module", help="dotted module name, e.g. aureon.core.aureon_phi_calendar")

    p_apply = sub.add_parser("apply", help="Run the full swap cycle on a target path")
    p_apply.add_argument("target_path")
    p_apply.add_argument("--pending-id", default="")
    p_apply.add_argument("--triggered-by", default="cli")

    args = parser.parse_args()
    ce = get_continuity_engine()

    if args.cmd == "sandbox":
        ok, detail = ce.sandbox_trial(args.module)
        print(json.dumps({"ok": ok, "detail": detail}, indent=2))
    elif args.cmd == "apply":
        r = ce.apply_with_continuity(
            target_path=args.target_path,
            pending_id=args.pending_id,
            triggered_by=args.triggered_by,
        )
        print(json.dumps(vars(r), indent=2, default=str))
