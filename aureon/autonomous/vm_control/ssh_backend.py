"""
SSHVMController — Cross-Platform VM via SSH + Deployed Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Connects to any VM (Windows with OpenSSH, Linux, macOS) via SSH and invokes
pre-deployed helper scripts to perform desktop actions.

On Windows the deployed agent can be:
  - The same PowerShell snippets used by WinRMVMController (via pwsh.exe)
  - A small Python helper using pyautogui running on the VM

This backend is best for:
  - Linux/macOS VMs
  - Windows VMs with OpenSSH Server enabled (Windows 10+)
  - Cross-platform homogeneous fleets

Requirements on host:
  pip install paramiko

If `paramiko` is not installed, the controller transparently falls back to
"stub mode" where all actions return a descriptive error.
"""

from __future__ import annotations

import base64
import logging
import shlex
from typing import Any, Dict, List, Optional

from aureon.autonomous.vm_control.base import VMController

logger = logging.getLogger("aureon.vm.ssh")

try:
    import paramiko  # type: ignore

    HAS_PARAMIKO = True
except ImportError:
    paramiko = None  # type: ignore
    HAS_PARAMIKO = False


class SSHVMController(VMController):
    """Connects to a VM via SSH."""

    def __init__(
        self,
        session_id: Optional[str] = None,
        name: str = "",
        host: str = "",
        username: str = "",
        password: Optional[str] = None,
        key_filename: Optional[str] = None,
        port: int = 22,
        platform: str = "windows",  # windows | linux | macos
    ):
        super().__init__(session_id=session_id, name=name, host=host, dry_run=True)
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.port = port
        self.platform = platform
        self._client: Optional[Any] = None
        self._available = HAS_PARAMIKO

    def _backend_name(self) -> str:
        return "ssh"

    def connect(self) -> bool:
        if not HAS_PARAMIKO:
            logger.warning("paramiko not installed — SSH backend in stub mode")
            return False
        try:
            self._client = paramiko.SSHClient()
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            kwargs: Dict[str, Any] = {
                "hostname": self.host,
                "port": self.port,
                "username": self.username,
                "timeout": 15,
            }
            if self.key_filename:
                kwargs["key_filename"] = self.key_filename
            if self.password:
                kwargs["password"] = self.password
            self._client.connect(**kwargs)
            logger.info("SSH connected: %s@%s:%d", self.username, self.host, self.port)
            return True
        except Exception as e:
            logger.error("SSH connect failed: %s", e)
            self._client = None
            return False

    def disconnect(self) -> None:
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None

    def health_check(self) -> bool:
        if not self._client:
            return False
        try:
            result = self._run("echo ok")
            return "ok" in result.get("stdout", "")
        except Exception:
            return False

    # ─────────────────────────────────────────────────────────────────────
    # Low-level run
    # ─────────────────────────────────────────────────────────────────────

    def _run(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        if not self._client:
            return {"error": "not_connected"}
        try:
            stdin, stdout, stderr = self._client.exec_command(command, timeout=timeout)
            out = stdout.read().decode("utf-8", errors="replace")
            err = stderr.read().decode("utf-8", errors="replace")
            rc = stdout.channel.recv_exit_status()
            return {"stdout": out.strip(), "stderr": err.strip(), "returncode": rc}
        except Exception as e:
            return {"error": str(e)}

    def _run_ps(self, script: str, timeout: int = 30) -> Dict[str, Any]:
        """Run a PowerShell script on a Windows target over SSH."""
        encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
        cmd = f"powershell.exe -NoProfile -NonInteractive -EncodedCommand {encoded}"
        return self._run(cmd, timeout=timeout)

    # ─────────────────────────────────────────────────────────────────────
    # Action implementations (Windows via PS, Linux via xdotool/scrot)
    # ─────────────────────────────────────────────────────────────────────

    def _do_screenshot(self, **kwargs) -> Dict[str, Any]:
        if self.platform == "windows":
            # Reuse the PS screenshot snippet
            from aureon.autonomous.vm_control.winrm_backend import PS_SCREENSHOT
            result = self._run_ps(PS_SCREENSHOT)
            return {"image_b64": result.get("stdout", ""), "format": "png"}
        else:
            # Linux: scrot + base64
            cmd = "scrot -o /tmp/aureon_ss.png && base64 -w 0 /tmp/aureon_ss.png && rm /tmp/aureon_ss.png"
            result = self._run(cmd)
            return {"image_b64": result.get("stdout", ""), "format": "png"}

    def _do_mouse_move(self, x: int, y: int, **kwargs) -> Dict[str, Any]:
        if self.platform == "windows":
            from aureon.autonomous.vm_control.winrm_backend import PS_MOUSE_MOVE
            self._run_ps(PS_MOUSE_MOVE.format(x=int(x), y=int(y)))
        else:
            self._run(f"xdotool mousemove {int(x)} {int(y)}")
        return {"x": int(x), "y": int(y)}

    def _click_unix(self, button: int, x: Optional[int], y: Optional[int]) -> Dict[str, Any]:
        if x is not None and y is not None:
            self._run(f"xdotool mousemove {int(x)} {int(y)}")
        self._run(f"xdotool click {button}")
        return {"button": button, "x": x, "y": y}

    def _do_left_click(self, x=None, y=None, **kwargs) -> Dict[str, Any]:
        if self.platform == "windows":
            from aureon.autonomous.vm_control.winrm_backend import WinRMVMController
            return WinRMVMController._click(self, "left", x, y)  # type: ignore
        return self._click_unix(1, x, y)

    def _do_right_click(self, x=None, y=None, **kwargs) -> Dict[str, Any]:
        if self.platform == "windows":
            from aureon.autonomous.vm_control.winrm_backend import WinRMVMController
            return WinRMVMController._click(self, "right", x, y)  # type: ignore
        return self._click_unix(3, x, y)

    def _do_middle_click(self, x=None, y=None, **kwargs) -> Dict[str, Any]:
        if self.platform == "windows":
            from aureon.autonomous.vm_control.winrm_backend import WinRMVMController
            return WinRMVMController._click(self, "middle", x, y)  # type: ignore
        return self._click_unix(2, x, y)

    def _do_double_click(self, x=None, y=None, **kwargs) -> Dict[str, Any]:
        self._do_left_click(x=x, y=y)
        return self._do_left_click(x=x, y=y)

    def _do_triple_click(self, x=None, y=None, **kwargs) -> Dict[str, Any]:
        self._do_left_click(x=x, y=y)
        self._do_left_click(x=x, y=y)
        return self._do_left_click(x=x, y=y)

    def _do_left_click_drag(self, start_x: int, start_y: int, end_x: int, end_y: int, **kwargs) -> Dict[str, Any]:
        if self.platform == "windows":
            from aureon.autonomous.vm_control.winrm_backend import WinRMVMController
            return WinRMVMController._do_left_click_drag(self, start_x, start_y, end_x, end_y)  # type: ignore
        self._run(f"xdotool mousemove {start_x} {start_y} mousedown 1 mousemove {end_x} {end_y} mouseup 1")
        return {"start": [start_x, start_y], "end": [end_x, end_y]}

    def _do_scroll(self, x: int, y: int, direction: str = "down", amount: int = 3, **kwargs) -> Dict[str, Any]:
        if self.platform == "windows":
            from aureon.autonomous.vm_control.winrm_backend import WinRMVMController
            return WinRMVMController._do_scroll(self, x, y, direction=direction, amount=amount)  # type: ignore
        button = 5 if direction == "down" else 4 if direction == "up" else 7 if direction == "right" else 6
        self._run(f"xdotool mousemove {x} {y}")
        for _ in range(int(amount)):
            self._run(f"xdotool click {button}")
        return {"x": x, "y": y, "direction": direction, "amount": amount}

    def _do_type_text(self, text: str, **kwargs) -> Dict[str, Any]:
        if self.platform == "windows":
            from aureon.autonomous.vm_control.winrm_backend import WinRMVMController
            return WinRMVMController._do_type_text(self, text)  # type: ignore
        escaped = shlex.quote(str(text))
        self._run(f"xdotool type --delay 20 {escaped}")
        return {"chars_typed": len(text)}

    def _do_press_key(self, key: str, **kwargs) -> Dict[str, Any]:
        if self.platform == "windows":
            from aureon.autonomous.vm_control.winrm_backend import WinRMVMController
            return WinRMVMController._do_press_key(self, key)  # type: ignore
        self._run(f"xdotool key {shlex.quote(str(key))}")
        return {"key": key}

    def _do_hotkey(self, keys: List[str], **kwargs) -> Dict[str, Any]:
        if self.platform == "windows":
            from aureon.autonomous.vm_control.winrm_backend import WinRMVMController
            return WinRMVMController._do_hotkey(self, keys)  # type: ignore
        combo = "+".join(str(k) for k in keys)
        self._run(f"xdotool key {shlex.quote(combo)}")
        return {"keys": keys, "combo": combo}

    def _do_get_cursor_position(self, **kwargs) -> Dict[str, Any]:
        if self.platform == "windows":
            from aureon.autonomous.vm_control.winrm_backend import WinRMVMController
            return WinRMVMController._do_get_cursor_position(self)  # type: ignore
        result = self._run("xdotool getmouselocation --shell")
        data = {}
        for line in result.get("stdout", "").splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                try:
                    data[k.lower()] = int(v)
                except ValueError:
                    data[k.lower()] = v
        return {"x": data.get("x", 0), "y": data.get("y", 0)}

    def _do_get_screen_size(self, **kwargs) -> Dict[str, Any]:
        if self.platform == "windows":
            from aureon.autonomous.vm_control.winrm_backend import WinRMVMController
            return WinRMVMController._do_get_screen_size(self)  # type: ignore
        result = self._run("xdpyinfo | grep dimensions")
        # dimensions: 1920x1080 pixels (508x285 millimeters)
        try:
            part = result["stdout"].split()[1]
            w, h = part.split("x")
            return {"width": int(w), "height": int(h)}
        except Exception:
            return {"width": 0, "height": 0}

    def _do_list_windows(self, **kwargs) -> Dict[str, Any]:
        if self.platform == "windows":
            from aureon.autonomous.vm_control.winrm_backend import WinRMVMController
            return WinRMVMController._do_list_windows(self)  # type: ignore
        result = self._run("wmctrl -l")
        windows = []
        for line in result.get("stdout", "").splitlines():
            parts = line.split(None, 3)
            if len(parts) >= 4:
                windows.append({"id": parts[0], "title": parts[3]})
        return {"windows": windows, "count": len(windows)}

    def _do_get_active_window(self, **kwargs) -> Dict[str, Any]:
        if self.platform == "windows":
            from aureon.autonomous.vm_control.winrm_backend import WinRMVMController
            return WinRMVMController._do_get_active_window(self)  # type: ignore
        result = self._run("xdotool getactivewindow getwindowname")
        return {"window": {"title": result.get("stdout", "")}}

    def _do_focus_window(self, title: str, **kwargs) -> Dict[str, Any]:
        if self.platform == "windows":
            from aureon.autonomous.vm_control.winrm_backend import WinRMVMController
            return WinRMVMController._do_focus_window(self, title)  # type: ignore
        self._run(f"wmctrl -a {shlex.quote(str(title))}")
        return {"focused": True, "title": title}

    def _do_execute_shell(self, command: str, timeout: int = 30, **kwargs) -> Dict[str, Any]:
        return self._run(str(command), timeout=timeout)

    def _do_execute_powershell(self, command: str, timeout: int = 30, **kwargs) -> Dict[str, Any]:
        if self.platform == "windows":
            return self._run_ps(str(command), timeout=timeout)
        # On non-Windows try pwsh
        return self._run(f"pwsh -Command {shlex.quote(str(command))}", timeout=timeout)
