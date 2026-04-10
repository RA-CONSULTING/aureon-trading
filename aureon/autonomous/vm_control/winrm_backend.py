"""
WinRMVMController — Real Windows VM via PowerShell Remoting
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Connects to a real Windows VM via WinRM (Windows Remote Management).

Requirements on target VM:
  - WinRM service enabled (Enable-PSRemoting)
  - User credentials with admin privileges
  - Port 5985 (HTTP) or 5986 (HTTPS) open

Requirements on host:
  - pip install pywinrm

Desktop actions (screenshot, click, type, key) are delivered by dropping a
small PowerShell + .NET Windows Forms snippet at the target and invoking it
via winrm. Shell execution is native.

If `pywinrm` is not installed, the controller transparently falls back to
"stub mode" where all actions return a descriptive error (safe for
development environments without real VMs).
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from aureon.autonomous.vm_control.base import VMController

logger = logging.getLogger("aureon.vm.winrm")

try:
    import winrm  # type: ignore

    HAS_WINRM = True
except ImportError:
    winrm = None  # type: ignore
    HAS_WINRM = False


# ─────────────────────────────────────────────────────────────────────────────
# PowerShell snippets for desktop actions
# ─────────────────────────────────────────────────────────────────────────────

PS_SCREENSHOT = r"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$screen = [System.Windows.Forms.Screen]::PrimaryScreen
$bounds = $screen.Bounds
$bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$stream = New-Object System.IO.MemoryStream
$bitmap.Save($stream, [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bitmap.Dispose()
$bytes = $stream.ToArray()
$stream.Dispose()
[Convert]::ToBase64String($bytes)
"""

PS_MOUSE_MOVE = r"""
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({x}, {y})
Write-Output ([System.Windows.Forms.Cursor]::Position.X, [System.Windows.Forms.Cursor]::Position.Y -join ',')
"""

PS_CLICK = r"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -Name U -Namespace W -MemberDefinition '
[DllImport("user32.dll")]
public static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint dwData, int dwExtraInfo);'
{move_snippet}
Start-Sleep -Milliseconds 50
[W.U]::mouse_event({down_flag}, 0, 0, 0, 0)
Start-Sleep -Milliseconds 50
[W.U]::mouse_event({up_flag}, 0, 0, 0, 0)
"""

PS_TYPE_TEXT = r"""
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.SendKeys]::SendWait({text_literal})
"""

PS_PRESS_KEY = r"""
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.SendKeys]::SendWait('{key}')
"""

PS_GET_CURSOR = r"""
Add-Type -AssemblyName System.Windows.Forms
$p = [System.Windows.Forms.Cursor]::Position
"$($p.X),$($p.Y)"
"""

PS_GET_SCREEN_SIZE = r"""
Add-Type -AssemblyName System.Windows.Forms
$s = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
"$($s.Width),$($s.Height)"
"""

PS_LIST_WINDOWS = r"""
Get-Process | Where-Object { $_.MainWindowTitle -ne '' } |
  Select-Object @{N='pid';E={$_.Id}}, @{N='title';E={$_.MainWindowTitle}}, @{N='name';E={$_.ProcessName}} |
  ConvertTo-Json -Compress
"""

PS_FOCUS_WINDOW = r"""
Add-Type -Name W -Namespace U -MemberDefinition '
[DllImport("user32.dll")]
public static extern bool SetForegroundWindow(IntPtr hWnd);'
$p = Get-Process | Where-Object { $_.MainWindowTitle -like "*{title}*" } | Select-Object -First 1
if ($p) {{ [U.W]::SetForegroundWindow($p.MainWindowHandle) | Out-Null; "ok" }} else {{ "not_found" }}
"""


# Mouse event flags
MOUSEEVENTF = {
    "LEFTDOWN": 0x0002,
    "LEFTUP": 0x0004,
    "RIGHTDOWN": 0x0008,
    "RIGHTUP": 0x0010,
    "MIDDLEDOWN": 0x0020,
    "MIDDLEUP": 0x0040,
}


class WinRMVMController(VMController):
    """Connects to a Windows VM via WinRM + PowerShell remoting."""

    def __init__(
        self,
        session_id: Optional[str] = None,
        name: str = "",
        host: str = "",
        username: str = "",
        password: str = "",
        port: int = 5985,
        transport: str = "ntlm",
        use_ssl: bool = False,
    ):
        super().__init__(session_id=session_id, name=name, host=host, dry_run=True)
        self.username = username
        self.password = password
        self.port = port
        self.transport = transport
        self.use_ssl = use_ssl
        self._session = None
        self._available = HAS_WINRM

    def _backend_name(self) -> str:
        return "winrm"

    def connect(self) -> bool:
        if not HAS_WINRM:
            logger.warning("pywinrm not installed — WinRM backend in stub mode")
            return False
        try:
            scheme = "https" if self.use_ssl else "http"
            endpoint = f"{scheme}://{self.host}:{self.port}/wsman"
            self._session = winrm.Session(
                endpoint,
                auth=(self.username, self.password),
                transport=self.transport,
            )
            logger.info("WinRM connected: %s", endpoint)
            return True
        except Exception as e:
            logger.error("WinRM connect failed: %s", e)
            self._session = None
            return False

    def disconnect(self) -> None:
        self._session = None

    def health_check(self) -> bool:
        if not self._session:
            return False
        try:
            result = self._session.run_cmd("echo ok")
            return result.status_code == 0
        except Exception:
            return False

    # ─────────────────────────────────────────────────────────────────────
    # Low-level runners
    # ─────────────────────────────────────────────────────────────────────

    def _run_ps(self, script: str, timeout: int = 30) -> Dict[str, Any]:
        if not self._session:
            return {"error": "not_connected"}
        try:
            result = self._session.run_ps(script)
            return {
                "stdout": result.std_out.decode("utf-8", errors="replace").strip(),
                "stderr": result.std_err.decode("utf-8", errors="replace").strip(),
                "returncode": result.status_code,
            }
        except Exception as e:
            return {"error": str(e)}

    def _run_cmd(self, cmd: str, timeout: int = 30) -> Dict[str, Any]:
        if not self._session:
            return {"error": "not_connected"}
        try:
            result = self._session.run_cmd(cmd)
            return {
                "stdout": result.std_out.decode("utf-8", errors="replace").strip(),
                "stderr": result.std_err.decode("utf-8", errors="replace").strip(),
                "returncode": result.status_code,
            }
        except Exception as e:
            return {"error": str(e)}

    # ─────────────────────────────────────────────────────────────────────
    # Screen / cursor
    # ─────────────────────────────────────────────────────────────────────

    def _do_screenshot(self, **kwargs) -> Dict[str, Any]:
        result = self._run_ps(PS_SCREENSHOT)
        if "error" in result or result.get("returncode") != 0:
            return {"error": result.get("error") or result.get("stderr", "unknown")}
        image_b64 = result["stdout"].strip()
        # Determine dimensions via a second call
        size = self._run_ps(PS_GET_SCREEN_SIZE)
        w, h = 0, 0
        try:
            if size.get("stdout"):
                w, h = [int(x) for x in size["stdout"].split(",")]
        except Exception:
            pass
        return {"image_b64": image_b64, "format": "png", "width": w, "height": h}

    def _do_mouse_move(self, x: int, y: int, **kwargs) -> Dict[str, Any]:
        script = PS_MOUSE_MOVE.format(x=int(x), y=int(y))
        result = self._run_ps(script)
        return {"x": int(x), "y": int(y), "result": result.get("stdout")}

    def _click(self, kind: str, x: Optional[int], y: Optional[int]) -> Dict[str, Any]:
        flags = {
            "left":   (MOUSEEVENTF["LEFTDOWN"],   MOUSEEVENTF["LEFTUP"]),
            "right":  (MOUSEEVENTF["RIGHTDOWN"],  MOUSEEVENTF["RIGHTUP"]),
            "middle": (MOUSEEVENTF["MIDDLEDOWN"], MOUSEEVENTF["MIDDLEUP"]),
        }
        down, up = flags.get(kind, flags["left"])
        move = ""
        if x is not None and y is not None:
            move = f"[System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({int(x)}, {int(y)})"
        script = PS_CLICK.format(move_snippet=move, down_flag=down, up_flag=up)
        result = self._run_ps(script)
        return {"kind": kind, "x": x, "y": y, "stdout": result.get("stdout")}

    def _do_left_click(self, x=None, y=None, **kwargs) -> Dict[str, Any]:
        return self._click("left", x, y)

    def _do_right_click(self, x=None, y=None, **kwargs) -> Dict[str, Any]:
        return self._click("right", x, y)

    def _do_middle_click(self, x=None, y=None, **kwargs) -> Dict[str, Any]:
        return self._click("middle", x, y)

    def _do_double_click(self, x=None, y=None, **kwargs) -> Dict[str, Any]:
        self._click("left", x, y)
        time.sleep(0.05)
        return self._click("left", x, y)

    def _do_triple_click(self, x=None, y=None, **kwargs) -> Dict[str, Any]:
        self._click("left", x, y)
        time.sleep(0.05)
        self._click("left", x, y)
        time.sleep(0.05)
        return self._click("left", x, y)

    def _do_left_click_drag(self, start_x: int, start_y: int, end_x: int, end_y: int, **kwargs) -> Dict[str, Any]:
        # Move, press left, move to end, release left
        move_start = PS_MOUSE_MOVE.format(x=int(start_x), y=int(start_y))
        move_end = PS_MOUSE_MOVE.format(x=int(end_x), y=int(end_y))
        script = f"""
{move_start}
Add-Type -Name U -Namespace W -MemberDefinition '
[DllImport("user32.dll")]
public static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint dwData, int dwExtraInfo);'
[W.U]::mouse_event({MOUSEEVENTF['LEFTDOWN']}, 0, 0, 0, 0)
Start-Sleep -Milliseconds 50
{move_end}
Start-Sleep -Milliseconds 50
[W.U]::mouse_event({MOUSEEVENTF['LEFTUP']}, 0, 0, 0, 0)
"""
        self._run_ps(script)
        return {"start": [start_x, start_y], "end": [end_x, end_y]}

    def _do_scroll(self, x: int, y: int, direction: str = "down", amount: int = 3, **kwargs) -> Dict[str, Any]:
        # WHEEL delta: 120 per notch. Negative for down/right.
        delta = -120 * amount if direction in ("down", "right") else 120 * amount
        script = f"""
Add-Type -Name U -Namespace W -MemberDefinition '
[DllImport("user32.dll")]
public static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint dwData, int dwExtraInfo);'
[System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({int(x)}, {int(y)})
[W.U]::mouse_event(0x0800, 0, 0, {delta}, 0)
"""
        self._run_ps(script)
        return {"x": x, "y": y, "direction": direction, "amount": amount}

    # ─────────────────────────────────────────────────────────────────────
    # Keyboard
    # ─────────────────────────────────────────────────────────────────────

    def _do_type_text(self, text: str, **kwargs) -> Dict[str, Any]:
        # SendKeys needs escaping of: + ^ % ~ ( ) { } [ ]
        escaped = str(text)
        for ch in "+^%~(){}[]":
            escaped = escaped.replace(ch, "{" + ch + "}")
        # Wrap in single quotes, escaping any single quotes inside
        escaped = escaped.replace("'", "''")
        script = PS_TYPE_TEXT.format(text_literal=f"'{escaped}'")
        self._run_ps(script)
        return {"chars_typed": len(text)}

    KEY_MAP = {
        "enter": "{ENTER}",
        "return": "{ENTER}",
        "tab": "{TAB}",
        "escape": "{ESC}",
        "esc": "{ESC}",
        "backspace": "{BS}",
        "delete": "{DEL}",
        "home": "{HOME}",
        "end": "{END}",
        "pageup": "{PGUP}",
        "pagedown": "{PGDN}",
        "up": "{UP}",
        "down": "{DOWN}",
        "left": "{LEFT}",
        "right": "{RIGHT}",
        "space": " ",
        "f1": "{F1}", "f2": "{F2}", "f3": "{F3}", "f4": "{F4}",
        "f5": "{F5}", "f6": "{F6}", "f7": "{F7}", "f8": "{F8}",
        "f9": "{F9}", "f10": "{F10}", "f11": "{F11}", "f12": "{F12}",
    }

    def _do_press_key(self, key: str, **kwargs) -> Dict[str, Any]:
        mapped = self.KEY_MAP.get(str(key).lower(), str(key))
        script = PS_PRESS_KEY.format(key=mapped.replace("'", "''"))
        self._run_ps(script)
        return {"key": key, "sent": mapped}

    def _do_hotkey(self, keys: List[str], **kwargs) -> Dict[str, Any]:
        modifiers = {"ctrl": "^", "control": "^", "alt": "%", "shift": "+", "win": "^{ESC}"}
        parts = []
        target = None
        for k in keys:
            kl = k.lower()
            if kl in modifiers:
                parts.append(modifiers[kl])
            else:
                target = self.KEY_MAP.get(kl, k)
        combo = "".join(parts) + (target or "")
        combo_escaped = combo.replace("'", "''")
        script = PS_PRESS_KEY.format(key=combo_escaped)
        self._run_ps(script)
        return {"keys": list(keys), "combo": combo}

    # ─────────────────────────────────────────────────────────────────────
    # Introspection
    # ─────────────────────────────────────────────────────────────────────

    def _do_get_cursor_position(self, **kwargs) -> Dict[str, Any]:
        result = self._run_ps(PS_GET_CURSOR)
        try:
            x, y = result["stdout"].split(",")
            return {"x": int(x), "y": int(y)}
        except Exception:
            return {"error": result.get("stdout") or result.get("error")}

    def _do_get_screen_size(self, **kwargs) -> Dict[str, Any]:
        result = self._run_ps(PS_GET_SCREEN_SIZE)
        try:
            w, h = result["stdout"].split(",")
            return {"width": int(w), "height": int(h)}
        except Exception:
            return {"error": result.get("stdout") or result.get("error")}

    # ─────────────────────────────────────────────────────────────────────
    # Window management
    # ─────────────────────────────────────────────────────────────────────

    def _do_list_windows(self, **kwargs) -> Dict[str, Any]:
        import json
        result = self._run_ps(PS_LIST_WINDOWS)
        try:
            data = json.loads(result["stdout"] or "[]")
            if isinstance(data, dict):
                data = [data]
            return {"windows": data, "count": len(data)}
        except Exception:
            return {"windows": [], "count": 0, "raw": result.get("stdout")}

    def _do_get_active_window(self, **kwargs) -> Dict[str, Any]:
        script = r"""
Add-Type -Name W -Namespace U -MemberDefinition '
[DllImport("user32.dll")]
public static extern IntPtr GetForegroundWindow();
[DllImport("user32.dll")]
public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder lpString, int nMaxCount);'
$h = [U.W]::GetForegroundWindow()
$sb = New-Object System.Text.StringBuilder 256
[U.W]::GetWindowText($h, $sb, 256) | Out-Null
$sb.ToString()
"""
        result = self._run_ps(script)
        return {"window": {"title": result.get("stdout", "")}}

    def _do_focus_window(self, title: str, **kwargs) -> Dict[str, Any]:
        script = PS_FOCUS_WINDOW.format(title=str(title).replace("'", "''"))
        result = self._run_ps(script)
        return {"focused": result.get("stdout") == "ok", "title": title}

    # ─────────────────────────────────────────────────────────────────────
    # Shell execution
    # ─────────────────────────────────────────────────────────────────────

    def _do_execute_shell(self, command: str, timeout: int = 30, **kwargs) -> Dict[str, Any]:
        return self._run_cmd(str(command), timeout=timeout)

    def _do_execute_powershell(self, command: str, timeout: int = 30, **kwargs) -> Dict[str, Any]:
        return self._run_ps(str(command), timeout=timeout)
