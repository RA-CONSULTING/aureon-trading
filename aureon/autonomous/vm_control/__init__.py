"""
Aureon VM Control — Windows Desktop Control for Agents
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Provides a Claude-style "computer use" tool dispatch layer for controlling
Windows virtual machines from in-house AI agents.

Architecture:
  ┌─────────────┐     ┌──────────────┐     ┌──────────────┐
  │   Agent     │────▶│ ToolRegistry │────▶│  Dispatcher  │
  └─────────────┘     └──────────────┘     └──────────────┘
                                                   │
                           ┌───────────────────────┼─────────────────┐
                           ▼                       ▼                 ▼
                    ┌──────────────┐      ┌──────────────┐   ┌──────────────┐
                    │  Simulated   │      │    WinRM     │   │     SSH      │
                    │  Controller  │      │  Controller  │   │  Controller  │
                    └──────────────┘      └──────────────┘   └──────────────┘

Components:
  - VMController       : abstract base with 15+ action methods
  - SimulatedVMController : in-memory simulation (no real VM, for testing)
  - WinRMVMController  : real Windows via PowerShell remoting (pywinrm)
  - SSHVMController    : cross-platform via SSH + deployed agent
  - VMControlDispatcher: manages sessions, routes actions, enforces safety
  - register_vm_tools(): adds 15 VM tools to an in-house AI ToolRegistry

Tool dispatch matches the in-house AI framework's Claude-compatible pattern:
agents receive tool definitions, emit tool_use blocks, and receive
tool_result blocks back — same loop as the built-in tools.

Gary Leckey / Aureon Institute — 2026
"""

from aureon.autonomous.vm_control.base import (
    VMController,
    VMAction,
    VMActionResult,
    VMSessionState,
    ActionRisk,
)
from aureon.autonomous.vm_control.simulated import SimulatedVMController
from aureon.autonomous.vm_control.winrm_backend import WinRMVMController
from aureon.autonomous.vm_control.ssh_backend import SSHVMController
from aureon.autonomous.vm_control.dispatcher import (
    VMControlDispatcher,
    get_vm_dispatcher,
)
from aureon.autonomous.vm_control.tools import register_vm_tools, VM_TOOL_NAMES

__all__ = [
    "VMController",
    "VMAction",
    "VMActionResult",
    "VMSessionState",
    "ActionRisk",
    "SimulatedVMController",
    "WinRMVMController",
    "SSHVMController",
    "VMControlDispatcher",
    "get_vm_dispatcher",
    "register_vm_tools",
    "VM_TOOL_NAMES",
]
