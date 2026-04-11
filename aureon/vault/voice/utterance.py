"""
Utterance — The Vault's Self-Authored Thought Unit
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

A `VoiceStatement` is one thing one voice says.
An `Utterance` is a statement + its response paired together — a single
exchange in the vault's conversation with itself.

Neither is scripted. The statement text is composed by a VaultVoice
from the live vault state and then passed through the in-house AI
adapter to produce a response. The vault fingerprint stamps each
statement with the exact state that produced it, so the history can
be replayed and reasoned about.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class VoiceStatement:
    """One statement from one voice, composed from the vault state."""
    voice: str
    text: str
    timestamp: float = field(default_factory=time.time)
    vault_fingerprint: str = ""
    prompt_used: str = ""           # the self-authored prompt (input to the adapter)
    system_prompt: str = ""         # the persona's identity
    model: str = ""
    tokens: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "voice": self.voice,
            "text": self.text,
            "timestamp": self.timestamp,
            "vault_fingerprint": self.vault_fingerprint,
            "prompt_used": self.prompt_used,
            "system_prompt": self.system_prompt[:200],
            "model": self.model,
            "tokens": self.tokens,
        }


@dataclass
class Utterance:
    """A single exchange in the vault's self-dialogue."""
    utterance_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    timestamp: float = field(default_factory=time.time)
    speaker: str = ""
    listener: str = ""
    statement: Optional[VoiceStatement] = None
    response: Optional[VoiceStatement] = None
    chosen: bool = True
    reasoning: str = ""                 # why the choice gate let this fire
    urgency: float = 0.0                # choice gate urgency [0, 1]
    vault_fingerprint_before: str = ""
    vault_fingerprint_after: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "utterance_id": self.utterance_id,
            "timestamp": self.timestamp,
            "speaker": self.speaker,
            "listener": self.listener,
            "statement": self.statement.to_dict() if self.statement else None,
            "response": self.response.to_dict() if self.response else None,
            "chosen": self.chosen,
            "reasoning": self.reasoning,
            "urgency": round(self.urgency, 4),
            "vault_fingerprint_before": self.vault_fingerprint_before,
            "vault_fingerprint_after": self.vault_fingerprint_after,
        }

    @property
    def full_text(self) -> str:
        """Render the exchange as a single conversation block."""
        parts = []
        if self.statement:
            parts.append(f"[{self.speaker}] {self.statement.text}")
        if self.response:
            parts.append(f"[{self.listener}] {self.response.text}")
        return "\n".join(parts)
