# aureon_hive_state.py
# 🐝 State of the Hive - Live Status Publisher & Queen's Voice Hook

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

@dataclass
class HiveState:
    timestamp: str
    mood: str
    active_scanner: str
    veto_count: int
    last_veto_reason: str
    coherence_score: float
    message_log: List[str] = field(default_factory=list)

class QueenVoiceBridge:
    """Simple persona generator for console/logs."""
    
    def __init__(self):
        self.last_message = ""

    def speak(self, code: str, context: str = "") -> str:
        """Translate execution codes to Queen's voice."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = f"👑 [QUEEN {timestamp}]"
        
        msg = ""
        if code == "VETO":
            msg = f"{prefix} I am vetoing this action. {context}"
        elif code == "EXECUTE":
            msg = f"{prefix} The path is clear. Proceed. {context}"
        elif code == "WAIT":
            msg = f"{prefix} The mists are thick. We wait. {context}"
        elif code == "SCAN":
            msg = f"{prefix} Watching the {context} closely..."
        elif code == "STARTUP":
            msg = f"{prefix} I am awake. The hive is listening."
        else:
            msg = f"{prefix} {context}"
            
        self.last_message = msg
        print(msg)  # Direct to console
        return msg

class HiveStatePublisher:
    """Manages the hive_state.md status file."""
    
    def __init__(self, filename="hive_state.md"):
        self.filename = filename
        self.voice = QueenVoiceBridge()
        self.state = HiveState(
            timestamp=datetime.now().isoformat(),
            mood="Neutral",
            active_scanner="Initializing",
            veto_count=0,
            last_veto_reason="None",
            coherence_score=0.0
        )

    def update(self, mood: str = None, scanner: str = None, 
               veto_reason: str = None, coherence: float = None):
        """Update state fields."""
        self.state.timestamp = datetime.now().isoformat()
        
        if mood: self.state.mood = mood
        if scanner: self.state.active_scanner = scanner
        if coherence is not None: self.state.coherence_score = coherence
        
        if veto_reason:
            self.state.veto_count += 1
            self.state.last_veto_reason = veto_reason
            self.voice.speak("VETO", f"Reason: {veto_reason}")

        self._publish()

    def log_message(self, message: str):
        """Add a voice message to the log (keeps last 5)."""
        self.state.message_log.append(message)
        if len(self.state.message_log) > 5:
            self.state.message_log.pop(0)
        self._publish()

    def _publish(self):
        """Write the markdown state file."""
        try:
            timestamp = datetime.now()
            content = f"""# 🐝 AUREON HIVE STATE
*Last Updated: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}*

## 🧠 Queen's Mind
- **Mood:** `{self.state.mood}`
- **Active Scanner:** `{self.state.active_scanner}`
- **Coherence:** `{self.state.coherence_score:.3f}` 
- **Veto Count:** `{self.state.veto_count}`

## 🚫 Last Veto
> "{self.state.last_veto_reason}"

## 📜 Voice Log
"""
            for msg in reversed(self.state.message_log):
                content += f"- {msg}\n"

            with open(self.filename, 'w', encoding='utf-8') as f:
                f.write(content)

            # Also publish JSON for dashboards / UI
            public_dir = Path(__file__).resolve().parent / "public"
            public_dir.mkdir(parents=True, exist_ok=True)
            json_path = public_dir / "hive_state.json"
            json_payload = {
                "updated_at": timestamp.isoformat(),
                "mood": self.state.mood,
                "active_scanner": self.state.active_scanner,
                "coherence_score": self.state.coherence_score,
                "veto_count": self.state.veto_count,
                "last_veto_reason": self.state.last_veto_reason,
                "message_log": list(self.state.message_log),
            }
            with open(json_path, 'w', encoding='utf-8') as jf:
                json.dump(json_payload, jf, indent=2)
                
        except Exception as e:
            print(f"⚠️ Failed to publish hive state: {e}")

# Global instance for easy import
_hive = None

def get_hive() -> HiveStatePublisher:
    global _hive
    if _hive is None:
        _hive = HiveStatePublisher()
    return _hive
