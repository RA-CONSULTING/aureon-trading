#!/usr/bin/env python3
"""
aureon_instruction_parser.py -- The Instruction Brain

Converts ANY natural language instruction into executable steps.  Pure
pattern-matching + keyword scoring -- no LLM required.  Handles typos,
slang, abbreviations, compound instructions, and contextual references
("do it again", "close it", etc.).

Each parsed step is a dict:
    {"tool": str, "method": str, "params": dict, "description": str}

Tools:
    "laptop"  -> LaptopControl methods
    "agent"   -> AureonAgentCore methods
    "shell"   -> direct shell commands
"""

from __future__ import annotations

import re
import sys
import logging
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Repo root & sys.path bootstrap
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in [str(REPO_ROOT), str(REPO_ROOT / "aureon"), str(REPO_ROOT / "aureon" / "core")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

logger = logging.getLogger("aureon.instruction_parser")

# ============================================================================
#  CONSTANTS
# ============================================================================

APP_ALIASES: Dict[str, List[str]] = {
    "chrome": ["chrome", "google chrome", "browser", "web browser", "google"],
    "firefox": ["firefox", "mozilla"],
    "edge": ["edge", "microsoft edge"],
    "notepad": ["notepad", "text editor", "editor"],
    "vscode": ["vscode", "vs code", "visual studio code", "code editor"],
    "explorer": ["explorer", "file explorer", "files", "my computer", "this pc"],
    "terminal": ["terminal", "cmd", "command prompt", "command line", "console", "powershell", "shell"],
    "calculator": ["calculator", "calc"],
    "spotify": ["spotify", "music"],
    "task manager": ["task manager", "tasks"],
    "settings": ["settings", "system settings", "preferences", "control panel"],
    "paint": ["paint", "drawing"],
    "word": ["word", "microsoft word", "document"],
    "excel": ["excel", "spreadsheet"],
    "outlook": ["outlook", "email", "mail"],
    "teams": ["teams", "microsoft teams"],
    "discord": ["discord"],
    "slack": ["slack"],
    "zoom": ["zoom", "video call"],
    "snipping tool": ["snipping", "snip", "screen snip"],
}

# Reverse lookup: alias -> canonical app name
_ALIAS_TO_APP: Dict[str, str] = {}
for _app, _aliases in APP_ALIASES.items():
    for _a in _aliases:
        _ALIAS_TO_APP[_a.lower()] = _app

# ---------------------------------------------------------------------------
#  TYPO MAP  (applied before any pattern matching)
# ---------------------------------------------------------------------------
TYPO_MAP: Dict[str, str] = {
    "screesnhot": "screenshot", "screnshot": "screenshot", "screenhsot": "screenshot",
    "scrennshot": "screenshot", "screensht": "screenshot", "screensho": "screenshot",
    "opne": "open", "oepn": "open", "oen": "open", "opn": "open",
    "colse": "close", "clsoe": "close", "cloes": "close", "closee": "close",
    "voulme": "volume", "volmue": "volume", "vlume": "volume", "volme": "volume",
    "brigtness": "brightness", "brighntess": "brightness", "brighness": "brightness",
    "brightnes": "brightness", "brigtnes": "brightness", "birightness": "brightness",
    "camrea": "camera", "camear": "camera", "carmea": "camera", "caemra": "camera",
    "keyboad": "keyboard", "keybaord": "keyboard", "keybord": "keyboard",
    "bluethooth": "bluetooth", "blutooth": "bluetooth", "bluetoth": "bluetooth",
    "bluetooh": "bluetooth", "blueetooth": "bluetooth",
    "downlods": "downloads", "donwloads": "downloads", "downlaods": "downloads",
    "serach": "search", "searhc": "search", "saerch": "search", "searh": "search",
    "scrol": "scroll", "scrool": "scroll", "scoll": "scroll",
    "clikc": "click", "clcik": "click", "cick": "click",
    "widnow": "window", "windwo": "window", "wndow": "window",
    "minimze": "minimize", "minimise": "minimize", "minimzie": "minimize",
    "maximze": "maximize", "maximise": "maximize", "maximzie": "maximize",
    "conenct": "connect", "conect": "connect", "connetc": "connect",
    "passwrod": "password", "pasword": "password", "passowrd": "password",
    "compuetr": "computer", "computre": "computer", "comupter": "computer",
    "docuemnt": "document", "documnet": "document", "dcoument": "document",
    "delte": "delete", "dleet": "delete", "deleet": "delete",
    "foldr": "folder", "fodler": "folder", "floder": "folder",
    "tpye": "type", "tyep": "type", "tye": "type",
    "wirte": "write", "wrtie": "write", "wriet": "write",
    "reade": "read", "raed": "read",
    "psate": "paste", "pase": "paste", "patse": "paste",
    "cpoy": "copy", "coyp": "copy", "ocpy": "copy",
    "unod": "undo", "udno": "undo",
    "rdeo": "redo", "reod": "redo",
    "asve": "save", "svae": "save", "saev": "save",
    "batteyr": "battery", "batery": "battery", "battrey": "battery",
    "notifcation": "notification", "notificaiton": "notification",
    "appilcation": "application", "applicaiton": "application",
    "settigns": "settings", "setings": "settings", "settnigs": "settings",
}

# ============================================================================
#  PATTERN DEFINITIONS
# ============================================================================
# Each entry: (compiled_regex, tool, method, param_extractor_or_dict, description_template)
# param_extractor is either a static dict or a callable(match) -> dict

def _no_params(_m: re.Match) -> dict:
    return {}


def _extract_text(m: re.Match) -> dict:
    """Pull the first non-None group as 'text'."""
    for g in m.groups():
        if g is not None:
            return {"text": g.strip()}
    return {}


def _extract_level(m: re.Match) -> dict:
    for g in m.groups():
        if g is not None and g.isdigit():
            return {"level": int(g)}
    return {}


def _extract_path(m: re.Match) -> dict:
    for g in m.groups():
        if g is not None:
            return {"path": g.strip()}
    return {}


def _extract_app(m: re.Match) -> dict:
    for g in m.groups():
        if g is not None:
            raw = g.strip().lower()
            resolved = _ALIAS_TO_APP.get(raw, raw)
            return {"app_name": resolved}
    return {}


def _extract_coords(m: re.Match) -> dict:
    groups = [g for g in m.groups() if g is not None]
    if len(groups) >= 2:
        try:
            return {"x": int(groups[0]), "y": int(groups[1])}
        except ValueError:
            pass
    return {}


def _extract_key(m: re.Match) -> dict:
    for g in m.groups():
        if g is not None:
            return {"key": g.strip().lower()}
    return {}


def _extract_url(m: re.Match) -> dict:
    for g in m.groups():
        if g is not None:
            url = g.strip()
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            return {"url": url}
    return {}


def _extract_drag(m: re.Match) -> dict:
    groups = [g for g in m.groups() if g is not None]
    if len(groups) >= 4:
        try:
            return {"x1": int(groups[0]), "y1": int(groups[1]),
                    "x2": int(groups[2]), "y2": int(groups[3])}
        except ValueError:
            pass
    return {}


def _extract_scroll(m: re.Match) -> dict:
    for g in m.groups():
        if g is not None:
            direction = g.strip().lower()
            clicks = 3
            if "up" in direction:
                clicks = 3
            elif "down" in direction:
                clicks = -3
            return {"clicks": clicks}
    return {"clicks": -3}


# ---- Category builders ----

_I = re.IGNORECASE


def _build_screen_patterns() -> list:
    return [
        (re.compile(r"\b(?:screenshot|screen\s*shot|capture\s*screen|snap\s*screen|print\s*screen|grab\s*screen|screen\s*capture|take\s*a\s*screen)\b", _I),
         "laptop", "screenshot", _no_params, "Take screenshot"),
        (re.compile(r"\b(?:what'?s?\s+on\s+(?:my\s+)?screen|read\s*(?:my\s+)?screen|what\s+do\s+you\s+see|look\s+at\s+(?:my\s+)?screen|read\s+what'?s?\s+on|what\s+(?:does|is)\s+(?:my\s+)?screen\s+say|describe\s+(?:my\s+)?screen|what\s+(?:am\s+i|is)\s+look(?:ing|s)\s+at)\b", _I),
         "laptop", "read_screen", _no_params, "Read screen text via OCR"),
        (re.compile(r"\bfind\s+(.+?)\s+on\s+(?:my\s+)?screen\b", _I),
         "laptop", "find_on_screen", _extract_text, "Find element on screen"),
        (re.compile(r"\bwhere\s+is\s+(.+?)\s+on\s+(?:my\s+)?screen\b", _I),
         "laptop", "find_on_screen", _extract_text, "Locate element on screen"),
        (re.compile(r"\blocate\s+(.+?)\s+on\s+(?:my\s+)?screen\b", _I),
         "laptop", "find_on_screen", _extract_text, "Locate element on screen"),
        (re.compile(r"\bcan\s+you\s+see\s+(.+?)\s*(?:\?|$)", _I),
         "laptop", "find_on_screen", _extract_text, "Find element on screen"),
        (re.compile(r"\b(?:what\s+color|pixel\s+color|color\s+at)\b", _I),
         "laptop", "get_pixel_color", _no_params, "Get pixel color"),
        (re.compile(r"\b(?:screen\s+size|resolution|display\s+size|monitor\s+size)\b", _I),
         "laptop", "get_screen_size", _no_params, "Get screen size"),
    ]


def _build_mouse_patterns() -> list:
    return [
        # click on text (OCR-based) -- must be before generic click
        (re.compile(r"\bclick\s+(?:on\s+)?[\"'](.+?)[\"']", _I),
         "laptop", "click_text", _extract_text, "Click on text"),
        (re.compile(r"\bclick\s+(?:on\s+)?(?:the\s+)?(?:button\s+)?(?:that\s+says?\s+)?[\"']?(.+?)[\"']?\s*$", _I),
         "laptop", "click_text", _extract_text, "Click on text element"),
        # click at coordinates
        (re.compile(r"\bclick\s+(?:at\s+)?(\d+)\s*[,x]\s*(\d+)", _I),
         "laptop", "mouse_click", _extract_coords, "Click at coordinates"),
        (re.compile(r"\bclick\s+(?:position|coordinates?)\s+(\d+)\s*[,x]\s*(\d+)", _I),
         "laptop", "mouse_click", _extract_coords, "Click at coordinates"),
        # double click
        (re.compile(r"\b(?:double[\s-]?click|dbl[\s-]?click)\b", _I),
         "laptop", "mouse_double_click", _no_params, "Double click"),
        # right click
        (re.compile(r"\b(?:right[\s-]?click|context\s+menu|secondary\s+click)\b", _I),
         "laptop", "mouse_right_click", _no_params, "Right click"),
        # drag
        (re.compile(r"\bdrag\s+(?:from\s+)?(\d+)\s*[,x]\s*(\d+)\s+to\s+(\d+)\s*[,x]\s*(\d+)", _I),
         "laptop", "mouse_drag", _extract_drag, "Drag mouse"),
        # scroll
        (re.compile(r"\bscroll\s+(up|down)\b", _I),
         "laptop", "mouse_scroll", _extract_scroll, "Scroll"),
        (re.compile(r"\bscroll\b", _I),
         "laptop", "mouse_scroll", lambda _m: {"clicks": -3}, "Scroll down"),
        # mouse position
        (re.compile(r"\b(?:where\s+is\s+(?:the\s+)?mouse|mouse\s+position|cursor\s+position|where'?s?\s+(?:the\s+)?cursor)\b", _I),
         "laptop", "mouse_position", _no_params, "Get mouse position"),
        # move mouse
        (re.compile(r"\b(?:move\s+(?:the\s+)?(?:mouse|cursor)\s+(?:to\s+)?(\d+)\s*[,x]\s*(\d+))", _I),
         "laptop", "mouse_move", _extract_coords, "Move mouse"),
    ]


def _build_keyboard_patterns() -> list:
    return [
        # Type text -- keep near top so it catches "type hello"
        (re.compile(r"\b(?:type|write|input|enter)\s+[\"'](.+?)[\"']", _I),
         "laptop", "type_text", _extract_text, "Type text"),
        (re.compile(r"\b(?:type|write|input)\s+(.+?)$", _I),
         "laptop", "type_text", _extract_text, "Type text"),
        # Named keys
        (re.compile(r"\b(?:press|hit|tap)\s+enter\b|press\s+return\b", _I),
         "laptop", "press_key", lambda _m: {"key": "enter"}, "Press Enter"),
        (re.compile(r"\b(?:press|hit|tap)\s+(?:escape|esc)\b", _I),
         "laptop", "press_key", lambda _m: {"key": "escape"}, "Press Escape"),
        (re.compile(r"\b(?:press|hit|tap)\s+tab\b|next\s+field\b", _I),
         "laptop", "press_key", lambda _m: {"key": "tab"}, "Press Tab"),
        (re.compile(r"\b(?:press|hit|tap)\s+space\b", _I),
         "laptop", "press_key", lambda _m: {"key": "space"}, "Press Space"),
        (re.compile(r"\b(?:press|hit|tap)\s+(?:backspace|back\s+space)\b|delete\s+(?:that|character|char)\b|\bbackspace\b", _I),
         "laptop", "press_key", lambda _m: {"key": "backspace"}, "Press Backspace"),
        (re.compile(r"\b(?:press|hit|tap)\s+delete\b", _I),
         "laptop", "press_key", lambda _m: {"key": "delete"}, "Press Delete"),
        (re.compile(r"\b(?:press|hit|tap)\s+(f\d{1,2})\b", _I),
         "laptop", "press_key", _extract_key, "Press function key"),
        # Hotkeys
        (re.compile(r"\b(?:copy|ctrl[\s+]?c)\b", _I),
         "laptop", "hotkey", lambda _m: {"keys": ["ctrl", "c"]}, "Copy"),
        (re.compile(r"\b(?:paste|ctrl[\s+]?v)\b", _I),
         "laptop", "hotkey", lambda _m: {"keys": ["ctrl", "v"]}, "Paste"),
        (re.compile(r"\b(?:cut|ctrl[\s+]?x)\b", _I),
         "laptop", "hotkey", lambda _m: {"keys": ["ctrl", "x"]}, "Cut"),
        (re.compile(r"\b(?:undo|ctrl[\s+]?z)\b", _I),
         "laptop", "hotkey", lambda _m: {"keys": ["ctrl", "z"]}, "Undo"),
        (re.compile(r"\b(?:redo|ctrl[\s+]?y)\b", _I),
         "laptop", "hotkey", lambda _m: {"keys": ["ctrl", "y"]}, "Redo"),
        (re.compile(r"\b(?:save|ctrl[\s+]?s)\b", _I),
         "laptop", "hotkey", lambda _m: {"keys": ["ctrl", "s"]}, "Save"),
        (re.compile(r"\bselect\s+all\b", _I),
         "laptop", "hotkey", lambda _m: {"keys": ["ctrl", "a"]}, "Select all"),
        (re.compile(r"\b(?:find|search|ctrl[\s+]?f)\b(?!\s+(?:file|on\s+screen|in|for))", _I),
         "laptop", "hotkey", lambda _m: {"keys": ["ctrl", "f"]}, "Find / search (Ctrl+F)"),
        (re.compile(r"\bnew\s+tab\b", _I),
         "laptop", "hotkey", lambda _m: {"keys": ["ctrl", "t"]}, "New tab"),
        (re.compile(r"\bclose\s+tab\b", _I),
         "laptop", "hotkey", lambda _m: {"keys": ["ctrl", "w"]}, "Close tab"),
        (re.compile(r"\b(?:switch\s+window|alt[\s+]?tab)\b", _I),
         "laptop", "hotkey", lambda _m: {"keys": ["alt", "tab"]}, "Switch window"),
        (re.compile(r"\b(?:minimize\s+all|show\s+desktop|win[\s+]?d)\b", _I),
         "laptop", "hotkey", lambda _m: {"keys": ["win", "d"]}, "Minimize all / show desktop"),
        (re.compile(r"\b(?:refresh|reload|ctrl[\s+]?r|f5)\b", _I),
         "laptop", "hotkey", lambda _m: {"keys": ["ctrl", "r"]}, "Refresh"),
        (re.compile(r"\bprint\b(?!\s+screen)", _I),
         "laptop", "hotkey", lambda _m: {"keys": ["ctrl", "p"]}, "Print"),
        (re.compile(r"\b(?:zoom\s+in|ctrl[\s+]?\+)\b", _I),
         "laptop", "hotkey", lambda _m: {"keys": ["ctrl", "plus"]}, "Zoom in"),
        (re.compile(r"\b(?:zoom\s+out|ctrl[\s+]?-)\b", _I),
         "laptop", "hotkey", lambda _m: {"keys": ["ctrl", "minus"]}, "Zoom out"),
    ]


def _build_app_patterns() -> list:
    return [
        # Open app
        (re.compile(r"\b(?:open|launch|start|run)\s+(.+?)$", _I),
         "agent", "open_app", _extract_app, "Open application"),
        # Close / quit app
        (re.compile(r"\b(?:close|quit|exit|terminate|kill)\s+(.+?)$", _I),
         "agent", "close_app", _extract_app, "Close application"),
        # Switch / focus
        (re.compile(r"\b(?:switch\s+to|go\s+to|focus(?:\s+on)?|bring\s+up)\s+(.+?)$", _I),
         "agent", "window_focus", _extract_app, "Focus window"),
        # Minimize / maximize
        (re.compile(r"\bminimize\s+(.+?)$", _I),
         "agent", "window_minimize", _extract_app, "Minimize window"),
        (re.compile(r"\bmaximize\s+(.+?)$", _I),
         "agent", "window_maximize", _extract_app, "Maximize window"),
        # List windows
        (re.compile(r"\b(?:what\s+windows\s+are\s+open|list\s+windows|show\s+windows|open\s+windows)\b", _I),
         "agent", "window_list", _no_params, "List open windows"),
        # Active window
        (re.compile(r"\b(?:what\s+app\s+is\s+this|what'?s?\s+focused|active\s+window|current\s+window|what\s+am\s+i\s+(?:in|using))\b", _I),
         "agent", "window_get_active", _no_params, "Get active window"),
    ]


def _build_audio_patterns() -> list:
    return [
        # Volume up
        (re.compile(r"\b(?:volume\s+up|louder|turn\s+(?:it\s+)?up|increase\s+volume|raise\s+volume)\b", _I),
         "laptop", "volume_set", lambda _m: {"level": "+10"}, "Increase volume"),
        # Volume down
        (re.compile(r"\b(?:volume\s+down|quieter|turn\s+(?:it\s+)?down|lower\s+(?:the\s+)?volume|decrease\s+volume|softer)\b", _I),
         "laptop", "volume_set", lambda _m: {"level": "-10"}, "Decrease volume"),
        # Mute / unmute
        (re.compile(r"\b(?:mute|silence|shut\s+up\s+audio|mute\s+sound)\b", _I),
         "laptop", "volume_mute", _no_params, "Mute audio"),
        (re.compile(r"\b(?:unmute|turn\s+sound\s+on|sound\s+on)\b", _I),
         "laptop", "volume_unmute", _no_params, "Unmute audio"),
        # Set volume to N
        (re.compile(r"\bvolume\s+(?:to\s+)?(\d+)\b", _I),
         "laptop", "volume_set", _extract_level, "Set volume"),
        (re.compile(r"\bset\s+volume\s+(?:to\s+)?(\d+)\b", _I),
         "laptop", "volume_set", _extract_level, "Set volume"),
        # Get volume
        (re.compile(r"\b(?:what'?s?\s+the\s+volume|volume\s+level|current\s+volume|how\s+loud)\b", _I),
         "laptop", "volume_get", _no_params, "Get volume level"),
        # Play sound
        (re.compile(r"\b(?:play\s+a\s+sound|beep|alert\s+sound|notification\s+sound)\b", _I),
         "laptop", "play_sound", _no_params, "Play alert sound"),
    ]


def _build_camera_patterns() -> list:
    return [
        (re.compile(r"\b(?:take\s+a\s+photo|take\s+a\s+picture|capture\s+(?:from\s+)?camera|selfie|webcam\s+(?:capture|photo|shot)|use\s+(?:the\s+)?camera)\b", _I),
         "laptop", "camera_capture", _no_params, "Capture from camera"),
        (re.compile(r"\b(?:what\s+cameras|list\s+cameras|available\s+cameras|show\s+cameras)\b", _I),
         "laptop", "camera_list", _no_params, "List cameras"),
        (re.compile(r"\b(?:read\s+(?:from\s+)?camera|camera\s+ocr|what\s+does\s+(?:the\s+)?camera\s+see)\b", _I),
         "laptop", "camera_read_text", _no_params, "Read text from camera"),
    ]


def _build_clipboard_patterns() -> list:
    return [
        (re.compile(r"\bcopy\s+(?:this|(?:the\s+)?selection|what'?s?\s+selected|selected\s+text)\b", _I),
         "laptop", "clipboard_copy_selection", _no_params, "Copy selection"),
        (re.compile(r"\bpaste\s*(?:this|it|here|that)?\b", _I),
         "laptop", "clipboard_paste", _no_params, "Paste from clipboard"),
        (re.compile(r"\b(?:what'?s?\s+in\s+(?:the\s+)?clipboard|clipboard\s+contents|what\s+did\s+i\s+copy|show\s+clipboard)\b", _I),
         "laptop", "clipboard_read", _no_params, "Read clipboard"),
        (re.compile(r"\bcopy\s+(?:the\s+)?text\s+(.+?)$", _I),
         "laptop", "clipboard_copy", _extract_text, "Copy text to clipboard"),
    ]


def _build_file_patterns() -> list:
    return [
        (re.compile(r"\bopen\s+(?:the\s+)?file\s+(.+?)$", _I),
         "laptop", "open_file", _extract_path, "Open file"),
        (re.compile(r"\bopen\s+(?:the\s+)?folder\s+(.+?)$", _I),
         "laptop", "open_folder", _extract_path, "Open folder"),
        (re.compile(r"\bshow\s+(.+?)\s+in\s+explorer\b", _I),
         "laptop", "open_folder", _extract_path, "Open folder in explorer"),
        (re.compile(r"\b(?:what'?s?\s+on\s+(?:my\s+)?desktop|desktop\s+files|show\s+desktop\s+files|list\s+desktop)\b", _I),
         "laptop", "get_desktop_files", _no_params, "List desktop files"),
        (re.compile(r"\b(?:recent\s+downloads|show\s+downloads|what\s+did\s+i\s+download|list\s+downloads|my\s+downloads)\b", _I),
         "laptop", "get_downloads", _no_params, "List recent downloads"),
        (re.compile(r"\b(?:find|search\s+for)\s+file\s+(.+?)$", _I),
         "laptop", "search_files", _extract_text, "Search for file"),
        (re.compile(r"\bwhere\s+is\s+(?:the\s+)?file\s+(.+?)$", _I),
         "laptop", "search_files", _extract_text, "Search for file"),
        (re.compile(r"\bcreate\s+(?:a\s+)?folder\s+(.+?)$", _I),
         "laptop", "create_dir", _extract_path, "Create folder"),
        (re.compile(r"\b(?:make|new)\s+folder\s+(.+?)$", _I),
         "laptop", "create_dir", _extract_path, "Create folder"),
        (re.compile(r"\bread\s+(?:the\s+)?(?:file\s+)?(.+?\.\w{1,5})$", _I),
         "laptop", "read_file", _extract_path, "Read file"),
        (re.compile(r"\bshow\s+me\s+(?:the\s+)?(.+?\.\w{1,5})\s+file$", _I),
         "laptop", "read_file", _extract_path, "Read file"),
        (re.compile(r"\b(?:delete|remove)\s+(?:the\s+)?(?:file\s+)?(.+?\.\w{1,5})$", _I),
         "laptop", "delete_file", _extract_path, "Delete file"),
    ]


def _build_system_patterns() -> list:
    return [
        (re.compile(r"\b(?:battery|battery\s+level|how\s+much\s+battery|power\s+level|battery\s+status|charge\s+level)\b", _I),
         "laptop", "battery_status", _no_params, "Check battery status"),
        (re.compile(r"\b(?:brightness\s+up|brighter|increase\s+brightness|raise\s+brightness)\b", _I),
         "laptop", "brightness_set", lambda _m: {"level": "+20"}, "Increase brightness"),
        (re.compile(r"\b(?:brightness\s+down|dimmer|dim\s+(?:the\s+)?screen|decrease\s+brightness|lower\s+brightness)\b", _I),
         "laptop", "brightness_set", lambda _m: {"level": "-20"}, "Decrease brightness"),
        (re.compile(r"\bbrightness\s+(?:to\s+)?(\d+)\b", _I),
         "laptop", "brightness_set", _extract_level, "Set brightness"),
        (re.compile(r"\bset\s+brightness\s+(?:to\s+)?(\d+)\b", _I),
         "laptop", "brightness_set", _extract_level, "Set brightness"),
        (re.compile(r"\b(?:lock\s+(?:the\s+)?(?:screen|computer|pc)|lock\s+it)\b", _I),
         "laptop", "lock_screen", _no_params, "Lock screen"),
        (re.compile(r"\b(?:sleep|put\s+(?:it\s+)?to\s+sleep|hibernate|standby)\b", _I),
         "laptop", "sleep_computer", _no_params, "Put computer to sleep"),
        (re.compile(r"\b(?:installed\s+apps|what\s+apps\s+do\s+i\s+have|list\s+(?:installed\s+)?programs|show\s+(?:all\s+)?apps)\b", _I),
         "laptop", "installed_apps", _no_params, "List installed applications"),
        (re.compile(r"\b(?:kill|force\s+close|end\s+task)\s+(.+?)$", _I),
         "agent", "kill_process", _extract_app, "Kill process"),
        (re.compile(r"\b(?:restart|reboot)\s+(?:the\s+)?computer\b", _I),
         "laptop", "restart_computer", _no_params, "Restart computer"),
        (re.compile(r"\b(?:shut\s*down|power\s+off|turn\s+off)\s+(?:the\s+)?computer\b", _I),
         "laptop", "shutdown_computer", _no_params, "Shut down computer"),
        (re.compile(r"\b(?:system\s+info|system\s+information|pc\s+info|computer\s+info|about\s+(?:this\s+)?computer)\b", _I),
         "laptop", "system_info", _no_params, "Get system information"),
        (re.compile(r"\b(?:cpu\s+usage|cpu\s+load|processor\s+usage)\b", _I),
         "laptop", "cpu_usage", _no_params, "Get CPU usage"),
        (re.compile(r"\b(?:memory\s+usage|ram\s+usage|how\s+much\s+ram)\b", _I),
         "laptop", "memory_usage", _no_params, "Get memory usage"),
        (re.compile(r"\b(?:disk\s+space|storage\s+space|how\s+much\s+(?:disk|storage))\b", _I),
         "laptop", "disk_usage", _no_params, "Get disk usage"),
    ]


def _build_network_patterns() -> list:
    return [
        (re.compile(r"\b(?:wifi\s+status|am\s+i\s+connected|internet\s+status|connection\s+status|network\s+status)\b", _I),
         "laptop", "wifi_status", _no_params, "Check Wi-Fi status"),
        (re.compile(r"\b(?:wifi\s+networks|available\s+networks|show\s+wifi|scan\s+(?:for\s+)?wifi|nearby\s+networks)\b", _I),
         "laptop", "wifi_networks", _no_params, "List available Wi-Fi networks"),
        (re.compile(r"\bconnect\s+(?:to\s+)?(.+?)\s+wifi\b", _I),
         "laptop", "wifi_connect", _extract_text, "Connect to Wi-Fi"),
        (re.compile(r"\bjoin\s+(.+?)\s+network\b", _I),
         "laptop", "wifi_connect", _extract_text, "Connect to network"),
        (re.compile(r"\b(?:disconnect\s+wifi|turn\s+off\s+wifi|disable\s+wifi)\b", _I),
         "laptop", "wifi_disconnect", _no_params, "Disconnect Wi-Fi"),
        (re.compile(r"\b(?:bluetooth\s+status|is\s+bluetooth\s+on)\b", _I),
         "laptop", "bluetooth_status", _no_params, "Check Bluetooth status"),
        (re.compile(r"\b(?:bluetooth\s+(?:on|enable)|turn\s+on\s+bluetooth|enable\s+bluetooth)\b", _I),
         "laptop", "bluetooth_enable", _no_params, "Enable Bluetooth"),
        (re.compile(r"\b(?:bluetooth\s+(?:off|disable)|turn\s+off\s+bluetooth|disable\s+bluetooth)\b", _I),
         "laptop", "bluetooth_disable", _no_params, "Disable Bluetooth"),
        (re.compile(r"\b(?:bluetooth\s+devices|paired\s+devices|list\s+bluetooth|show\s+bluetooth)\b", _I),
         "laptop", "bluetooth_devices", _no_params, "List Bluetooth devices"),
        (re.compile(r"\b(?:my\s+ip|ip\s+address|what'?s?\s+my\s+ip)\b", _I),
         "laptop", "get_ip_address", _no_params, "Get IP address"),
    ]


def _build_notification_patterns() -> list:
    return [
        (re.compile(r"\b(?:notify\s+(?:me)?|send\s+(?:a\s+)?notification|remind\s+me|alert\s+me)\b", _I),
         "laptop", "notify", _extract_text, "Send notification"),
        (re.compile(r"\b(?:show\s+(?:a\s+)?message|popup|alert|toast)\b", _I),
         "laptop", "alert", _extract_text, "Show alert message"),
    ]


def _build_web_patterns() -> list:
    return [
        # Search
        (re.compile(r"\b(?:search\s+(?:for|the\s+web\s+for)\s+(.+)|google\s+(.+)|look\s+up\s+(.+)|search\s+the\s+web\s+for\s+(.+))\b", _I),
         "agent", "web_search", _extract_text, "Web search"),
        (re.compile(r"\b(?:what\s+is|who\s+is|tell\s+me\s+about|what\s+are|how\s+(?:do|does|to))\s+(.+?)(?:\?|$)", _I),
         "agent", "web_search", _extract_text, "Search for information"),
        # URL navigation
        (re.compile(r"\bgo\s+to\s+((?:https?://)?[\w.-]+\.(?:com|org|io|net|dev|co|edu|gov|app|xyz)[\w/.-]*)\b", _I),
         "agent", "open_url", _extract_url, "Open URL"),
        (re.compile(r"\bopen\s+((?:https?://)?[\w.-]+\.(?:com|org|io|net|dev|co|edu|gov|app|xyz)[\w/.-]*)\b", _I),
         "agent", "open_url", _extract_url, "Open URL"),
        # Fetch
        (re.compile(r"\b(?:fetch|get\s+page|download\s+page)\s+(.+?)$", _I),
         "agent", "web_fetch", _extract_url, "Fetch web page"),
    ]


def _build_trading_patterns() -> list:
    return [
        (re.compile(r"\b(?:balance|balances|how\s+much\s+do\s+i\s+have|my\s+funds|account\s+balance)\b", _I),
         "agent", "get_balances", _no_params, "Get account balances"),
        (re.compile(r"\b(?:positions|what\s+am\s+i\s+holding|my\s+trades|open\s+positions|current\s+positions)\b", _I),
         "agent", "get_positions", _no_params, "Get open positions"),
        (re.compile(r"\bbuy\s+(.+?)$", _I),
         "agent", "place_order", lambda m: {"side": "buy", "details": m.group(1).strip()}, "Place buy order"),
        (re.compile(r"\bsell\s+(.+?)$", _I),
         "agent", "place_order", lambda m: {"side": "sell", "details": m.group(1).strip()}, "Place sell order"),
        (re.compile(r"\bplace\s+(?:a\s+)?(?:buy|sell)?\s*order\b", _I),
         "agent", "place_order", _no_params, "Place order"),
        (re.compile(r"\b(?:market\s+summary|market\s+status|how'?s?\s+the\s+market|market\s+overview)\b", _I),
         "agent", "market_summary", _no_params, "Get market summary"),
        (re.compile(r"\b(?:portfolio|portfolio\s+value|net\s+worth|total\s+value|my\s+portfolio)\b", _I),
         "agent", "portfolio", _no_params, "Get portfolio value"),
        (re.compile(r"\b(?:price\s+of|what'?s?\s+(?:the\s+)?price\s+of|how\s+much\s+is)\s+(.+?)(?:\?|$)", _I),
         "agent", "get_price", _extract_text, "Get asset price"),
        (re.compile(r"\b(?:order\s+history|past\s+orders|my\s+orders|trade\s+history)\b", _I),
         "agent", "order_history", _no_params, "Get order history"),
        (re.compile(r"\b(?:cancel\s+(?:all\s+)?orders?|cancel\s+(?:my\s+)?orders?)\b", _I),
         "agent", "cancel_orders", _no_params, "Cancel orders"),
    ]


def _build_communication_patterns() -> list:
    return [
        (re.compile(r"\b(?:say|speak|read\s+(?:this\s+)?(?:out\s+)?(?:loud)?|announce)\s+(.+?)$", _I),
         "agent", "speak", _extract_text, "Speak text aloud"),
        (re.compile(r"\b(?:listen|hear\s+me|voice\s+input|start\s+listening)\b", _I),
         "agent", "listen", _no_params, "Listen for voice input"),
        (re.compile(r"\b(?:what\s+do\s+you\s+think|your\s+thoughts?\s+(?:on|about)?|think\s+about|analyze)\s+(.+?)$", _I),
         "agent", "think", _extract_text, "Think / analyze"),
        (re.compile(r"\b(?:what\s+do\s+you\s+think|your\s+opinion|thoughts\s*\??)\b", _I),
         "agent", "think", _no_params, "Share thoughts"),
    ]


# ============================================================================
#  COMPOUND INSTRUCTION SPLITTING
# ============================================================================

_SPLIT_PATTERNS = [
    re.compile(r"\b(?:and\s+then|then|after\s+that|next|afterwards)\b", _I),
    re.compile(r"\s*,\s+(?:and\s+)?then\s+", _I),
    re.compile(r"\s*,\s+(?:and\s+)(?!.*\b(?:and|then)\b)", _I),
]

_ORDERED_SPLIT = re.compile(
    r"\b(?:first|1st|step\s*1)\b(.+?)"
    r"\b(?:then|second|2nd|step\s*2|next)\b(.+?)"
    r"(?:\b(?:finally|third|3rd|step\s*3|last|lastly)\b(.+))?$",
    _I,
)

# ============================================================================
#  CONTEXT-AWARE REFERENCES
# ============================================================================

_REPEAT_PATTERNS = [
    re.compile(r"\b(?:do\s+(?:that|it)\s+again|repeat\s+(?:that|last|it)|again|same\s+thing|one\s+more\s+time)\b", _I),
]

_MODIFY_PATTERNS = [
    re.compile(r"\b(?:same\s+thing\s+but|the\s+same\s+but|but\s+this\s+time)\s+(.+?)$", _I),
]

_PRONOUN_PATTERNS = [
    re.compile(r"\b(?:close|minimize|maximize|quit|exit|kill)\s+(?:it|that)\b", _I),
    re.compile(r"\bpaste\s+(?:it|that)\s+(?:there|here|in|into)\b", _I),
]

# ============================================================================
#  INSTRUCTION PARSER
# ============================================================================


class InstructionParser:
    """
    The Brain -- converts any natural language instruction into executable
    steps.  Pure pattern matching + keyword scoring, no LLM required.
    """

    def __init__(self) -> None:
        self._last_instructions: deque = deque(maxlen=5)
        self._last_results: deque = deque(maxlen=5)
        self._context: Dict[str, Any] = {}  # active_app, last_file, etc.

        # Build the full pattern library (order matters -- first match wins
        # within a category, but categories are scored by specificity).
        self._pattern_groups: List[Tuple[str, list]] = [
            ("screen", _build_screen_patterns()),
            ("mouse", _build_mouse_patterns()),
            ("keyboard", _build_keyboard_patterns()),
            ("clipboard", _build_clipboard_patterns()),
            ("camera", _build_camera_patterns()),
            ("audio", _build_audio_patterns()),
            ("system", _build_system_patterns()),
            ("network", _build_network_patterns()),
            ("notification", _build_notification_patterns()),
            ("file", _build_file_patterns()),
            ("trading", _build_trading_patterns()),
            ("communication", _build_communication_patterns()),
            ("web", _build_web_patterns()),
            ("app", _build_app_patterns()),  # app last -- very broad patterns
        ]

        logger.debug("InstructionParser initialised with %d pattern groups",
                      len(self._pattern_groups))

    # ------------------------------------------------------------------
    #  PUBLIC API
    # ------------------------------------------------------------------

    def parse(self, instruction: str) -> List[Dict[str, Any]]:
        """
        Parse any natural language instruction into executable steps.

        Returns
        -------
        list[dict]
            Each dict has keys: tool, method, params, description.
        """
        if not instruction or not instruction.strip():
            return []

        instruction = instruction.strip()

        # 1. Context-aware shortcuts (repeat, pronoun resolution)
        ctx_result = self._resolve_context(instruction)
        if ctx_result is not None:
            return ctx_result

        # 2. Typo correction
        cleaned = self._fix_typos(instruction)

        # 3. Try splitting into compound sub-instructions
        sub_instructions = self._split_compound(cleaned)
        if len(sub_instructions) > 1:
            steps: List[Dict[str, Any]] = []
            for sub in sub_instructions:
                sub = sub.strip()
                if sub:
                    steps.extend(self._parse_single(sub))
            if steps:
                self._record(instruction, steps)
                return steps

        # 4. Single instruction
        steps = self._parse_single(cleaned)
        self._record(instruction, steps)
        return steps

    def explain(self, instruction: str) -> str:
        """
        Return a human-readable explanation of what Aureon thinks the
        instruction means, without executing anything.
        """
        steps = self.parse(instruction)
        if not steps:
            return f"I don't understand the instruction: \"{instruction}\""

        parts: list = []
        for i, step in enumerate(steps, 1):
            desc = step.get("description", step.get("method", "unknown action"))
            params = step.get("params", {})
            param_str = ""
            if params:
                param_str = " with " + ", ".join(
                    f"{k}={v!r}" for k, v in params.items()
                )
            prefix = f"Step {i}: " if len(steps) > 1 else ""
            parts.append(f"{prefix}{desc}{param_str}")

        return " -> ".join(parts) if len(parts) <= 3 else "\n".join(parts)

    def can_do(self, instruction: str) -> Tuple[bool, float]:
        """
        Return (can_handle, confidence) for the given instruction.

        confidence is in [0.0, 1.0].
        """
        if not instruction or not instruction.strip():
            return False, 0.0

        cleaned = self._fix_typos(instruction.strip())
        matches = self._collect_matches(cleaned)
        if not matches:
            return False, 0.0

        best_score = max(m[0] for m in matches)
        # Normalise score to 0-1 range (scores are typically 1-10)
        confidence = min(1.0, best_score / 5.0)
        return True, round(confidence, 2)

    def update_context(self, key: str, value: Any) -> None:
        """Update the parser's context (e.g. after an action completes)."""
        self._context[key] = value

    # ------------------------------------------------------------------
    #  INTERNAL -- typo fixing
    # ------------------------------------------------------------------

    def _fix_typos(self, text: str) -> str:
        """Apply typo corrections word-by-word."""
        words = text.split()
        corrected = []
        for w in words:
            low = w.lower()
            replacement = TYPO_MAP.get(low)
            if replacement:
                # Preserve original casing style (all-caps, title, lower)
                if w.isupper():
                    corrected.append(replacement.upper())
                elif w[0].isupper():
                    corrected.append(replacement.capitalize())
                else:
                    corrected.append(replacement)
            else:
                corrected.append(w)
        return " ".join(corrected)

    # ------------------------------------------------------------------
    #  INTERNAL -- pattern matching
    # ------------------------------------------------------------------

    def _collect_matches(self, text: str) -> List[Tuple[float, str, str, dict, str]]:
        """
        Run all patterns against *text* and return scored matches.

        Returns list of (score, tool, method, params, description).
        """
        matches: List[Tuple[float, str, str, dict, str]] = []
        text_lower = text.lower()

        for group_name, patterns in self._pattern_groups:
            for pattern_tuple in patterns:
                regex, tool, method, param_fn, desc = pattern_tuple
                m = regex.search(text)
                if m:
                    # Score: longer match => higher specificity
                    match_len = m.end() - m.start()
                    specificity = match_len / max(len(text), 1)
                    # Bonus for early groups (more specific categories)
                    group_bonus = 0.5  # flat bonus for matching at all
                    score = specificity * 5.0 + group_bonus

                    if callable(param_fn):
                        params = param_fn(m)
                    else:
                        params = dict(param_fn) if isinstance(param_fn, dict) else {}

                    matches.append((score, tool, method, params, desc))
                    break  # first match per group wins

        return matches

    def _parse_single(self, text: str) -> List[Dict[str, Any]]:
        """Parse a single (non-compound) instruction."""
        matches = self._collect_matches(text)

        if not matches:
            # Fallback: treat as a general agent query
            return [{
                "tool": "agent",
                "method": "think",
                "params": {"text": text},
                "description": f"Process: {text[:80]}",
            }]

        # Pick the best match
        matches.sort(key=lambda x: x[0], reverse=True)
        _, tool, method, params, desc = matches[0]

        return [{"tool": tool, "method": method, "params": params, "description": desc}]

    # ------------------------------------------------------------------
    #  INTERNAL -- compound instruction splitting
    # ------------------------------------------------------------------

    def _split_compound(self, text: str) -> List[str]:
        """Split compound instructions into sub-instructions."""
        # Try ordered split first ("first X, then Y, finally Z")
        m = _ORDERED_SPLIT.search(text)
        if m:
            parts = [g.strip() for g in m.groups() if g]
            if len(parts) >= 2:
                return parts

        # Try splitting on connectors
        for pat in _SPLIT_PATTERNS:
            parts = pat.split(text)
            if len(parts) >= 2:
                cleaned = [p.strip() for p in parts if p.strip()]
                if len(cleaned) >= 2:
                    return cleaned

        return [text]

    # ------------------------------------------------------------------
    #  INTERNAL -- context resolution
    # ------------------------------------------------------------------

    def _resolve_context(self, instruction: str) -> Optional[List[Dict[str, Any]]]:
        """Handle context-aware references like 'do it again' or 'close it'."""
        # "do it again" / "repeat"
        for pat in _REPEAT_PATTERNS:
            if pat.search(instruction):
                if self._last_results:
                    return list(self._last_results[-1])
                return [{"tool": "agent", "method": "think",
                         "params": {"text": "Nothing to repeat"},
                         "description": "Nothing to repeat"}]

        # "same thing but louder" -- repeat with modification
        for pat in _MODIFY_PATTERNS:
            m = pat.search(instruction)
            if m and self._last_results:
                modifier = m.group(1).strip()
                prev_steps = list(self._last_results[-1])
                # Apply modifier as extra context
                for step in prev_steps:
                    step["params"]["_modifier"] = modifier
                    step["description"] += f" (modified: {modifier})"
                return prev_steps

        # "close it" / "minimize it" -- resolve pronoun
        for pat in _PRONOUN_PATTERNS:
            if pat.search(instruction):
                last_app = self._context.get("last_app")
                if last_app:
                    resolved = instruction.replace(" it", f" {last_app}")
                    resolved = resolved.replace(" that", f" {last_app}")
                    return self._parse_single(self._fix_typos(resolved))

        return None

    # ------------------------------------------------------------------
    #  INTERNAL -- history recording
    # ------------------------------------------------------------------

    def _record(self, instruction: str, steps: List[Dict[str, Any]]) -> None:
        """Record instruction and result for context-aware follow-ups."""
        self._last_instructions.append(instruction)
        self._last_results.append(steps)

        # Update context with useful info
        for step in steps:
            method = step.get("method", "")
            params = step.get("params", {})
            if method in ("open_app", "window_focus", "close_app"):
                app = params.get("app_name", "")
                if app:
                    self._context["last_app"] = app
            if method in ("open_file", "read_file", "write_file"):
                path = params.get("path", "")
                if path:
                    self._context["last_file"] = path

    # ------------------------------------------------------------------
    #  FUZZY MATCHING (utility)
    # ------------------------------------------------------------------

    @staticmethod
    def _fuzzy_match(input_text: str, candidates: List[str],
                     threshold: float = 0.6) -> Optional[str]:
        """
        Find best fuzzy match using character bigram overlap (Dice coefficient).
        Returns the best candidate or None if nothing meets the threshold.
        """
        if not input_text or not candidates:
            return None

        def _bigrams(s: str) -> set:
            s = s.lower().strip()
            return {s[i:i+2] for i in range(len(s) - 1)} if len(s) > 1 else {s}

        input_bi = _bigrams(input_text)
        best_score = 0.0
        best_candidate = None

        for candidate in candidates:
            cand_bi = _bigrams(candidate)
            if not input_bi or not cand_bi:
                continue
            overlap = len(input_bi & cand_bi)
            score = (2.0 * overlap) / (len(input_bi) + len(cand_bi))
            if score > best_score:
                best_score = score
                best_candidate = candidate

        if best_score >= threshold:
            return best_candidate
        return None

    def resolve_app_name(self, raw: str) -> str:
        """
        Resolve a raw app reference to a canonical app name using exact
        lookup then fuzzy matching.
        """
        low = raw.lower().strip()

        # Exact match in alias table
        if low in _ALIAS_TO_APP:
            return _ALIAS_TO_APP[low]

        # Fuzzy match against all aliases
        all_aliases = list(_ALIAS_TO_APP.keys())
        match = self._fuzzy_match(low, all_aliases, threshold=0.55)
        if match:
            return _ALIAS_TO_APP[match]

        # Return as-is
        return raw


# ============================================================================
#  MODULE-LEVEL CONVENIENCE
# ============================================================================

_default_parser: Optional[InstructionParser] = None


def get_instruction_parser() -> InstructionParser:
    """Return (or create) the module-level singleton parser."""
    global _default_parser
    if _default_parser is None:
        _default_parser = InstructionParser()
    return _default_parser


def parse_instruction(instruction: str) -> List[Dict[str, Any]]:
    """Convenience: parse an instruction using the default parser."""
    return get_instruction_parser().parse(instruction)


def explain_instruction(instruction: str) -> str:
    """Convenience: explain an instruction using the default parser."""
    return get_instruction_parser().explain(instruction)


def can_do_instruction(instruction: str) -> Tuple[bool, float]:
    """Convenience: check if the parser can handle an instruction."""
    return get_instruction_parser().can_do(instruction)


# ============================================================================
#  SELF-TEST
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = InstructionParser()

    test_cases = [
        "open chrome",
        "take a screenshot",
        "what does my screen say",
        "turn the volume down",
        "click on 'Submit'",
        "type hello world",
        "press enter",
        "copy this and paste it into notepad",
        "scroll down",
        "what's my battery level?",
        "search for python tutorials",
        "go to github.com",
        "close it",
        "do it again",
        "screesnhot",
        "opne calculator",
        "brightness 50",
        "balance",
        "what windows are open",
        "first open chrome, then go to google.com, finally search for weather",
        "mute",
        "where is the mouse",
        "take a photo",
        "wifi status",
        "bluetooth devices",
        "find file report.docx",
        "say hello world",
        "double click",
        "right click",
        "new tab",
        "select all",
        "drag from 100,200 to 300,400",
        "what's in the clipboard",
    ]

    print("=" * 70)
    print("  INSTRUCTION PARSER -- SELF-TEST")
    print("=" * 70)

    for tc in test_cases:
        steps = parser.parse(tc)
        can, conf = parser.can_do(tc)
        explanation = parser.explain(tc)
        print(f"\n  Input:  \"{tc}\"")
        print(f"  Can do: {can}  (confidence {conf})")
        print(f"  Explain: {explanation}")
        for s in steps:
            print(f"    -> {s['tool']}.{s['method']}({s['params']})  [{s['description']}]")

    print("\n" + "=" * 70)
    print("  ALL TESTS COMPLETE")
    print("=" * 70)
