"""
ObsidianSink — Mirror the Vault's Self-Dialogue into an Obsidian Vault
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The sink is a thin write-only observer over the recent cognitive loops
(SelfFeedbackLoop, SelfDialogueEngine, ThoughtStreamLoop). Each event
becomes a markdown note in the configured Obsidian vault:

  daily/YYYY-MM-DD.md              — one note per day; all utterances,
                                      ticks, and integrations append here
  voices/{speaker}/{utterance}.md  — one note per utterance, tagged with
                                      the speaker persona
  loops/self_feedback_loop.md      — rolling log of tick telemetry
  integrations/audit_trail.md      — audit-trail snapshots

Everything routes through an ObsidianBridge so the sink works whether
Obsidian is running its Local REST plugin OR whether we're just writing
to a filesystem vault directory.

Usage:

    from aureon.integrations.obsidian import ObsidianBridge, ObsidianSink
    from aureon.vault.voice import SelfDialogueEngine

    sink = ObsidianSink(ObsidianBridge())
    engine = SelfDialogueEngine(vault=my_vault, on_utterance=sink.on_utterance)
    ...
"""

from __future__ import annotations

import datetime as _dt
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from aureon.integrations.obsidian.obsidian_bridge import ObsidianBridge

logger = logging.getLogger("aureon.integrations.obsidian.sink")


@dataclass
class ObsidianSinkConfig:
    """Controls how the sink writes into the Obsidian vault."""

    write_daily_journal: bool = True
    write_per_voice_notes: bool = True
    write_loop_log: bool = True
    write_audit_trail: bool = True
    # Folder roots — relative to the Obsidian vault
    daily_folder: str = "daily"
    voices_folder: str = "voices"
    loops_folder: str = "loops"
    integrations_folder: str = "integrations"
    # Limits
    max_utterance_chars: int = 4000
    max_tick_lines_per_day: int = 2000
    # Tags
    default_tags: tuple = ("aureon", "vault", "hnc")


class ObsidianSink:
    """Write-only observer that renders vault events as markdown notes."""

    def __init__(
        self,
        bridge: Optional[ObsidianBridge] = None,
        config: Optional[ObsidianSinkConfig] = None,
    ):
        self.bridge = bridge or ObsidianBridge()
        self.config = config or ObsidianSinkConfig()
        self._utterances_written = 0
        self._ticks_written = 0
        self._audits_written = 0

    # ─────────────────────────────────────────────────────────────────────
    # Event handlers (wire these as callbacks)
    # ─────────────────────────────────────────────────────────────────────

    def on_utterance(self, utterance: Any) -> None:
        """
        Callback for SelfDialogueEngine / ThoughtStreamLoop.on_utterance.
        Writes the utterance into the daily journal AND a per-voice note.
        """
        if utterance is None or not self.bridge.health_check():
            return
        try:
            speaker = getattr(utterance, "speaker", "vault") or "vault"
            listener = getattr(utterance, "listener", "") or ""
            uid = getattr(utterance, "utterance_id", "") or ""
            statement = getattr(utterance, "statement", None)
            response = getattr(utterance, "response", None)
            urgency = float(getattr(utterance, "urgency", 0.0) or 0.0)
            reasoning = getattr(utterance, "reasoning", "") or ""
            fp_before = getattr(utterance, "vault_fingerprint_before", "") or ""
            fp_after = getattr(utterance, "vault_fingerprint_after", "") or ""
            ts = float(getattr(utterance, "timestamp", 0.0) or 0.0)

            when = _dt.datetime.utcfromtimestamp(ts) if ts else _dt.datetime.utcnow()
            statement_text = self._trim(self._extract_text(statement))
            response_text = self._trim(self._extract_text(response))

            # 1) daily journal entry
            if self.config.write_daily_journal:
                daily_path = self._daily_path(when)
                line = (
                    f"\n## {when.strftime('%H:%M:%S')} · {speaker} → {listener}  "
                    f"_(urgency={urgency:.2f})_\n"
                    f"- id: `{uid}`\n"
                    f"- reasoning: {reasoning or '_(none)_'}\n"
                    f"- fingerprint: `{fp_before[:8]}` → `{fp_after[:8]}`\n\n"
                    f"**{speaker}** says:\n\n> {statement_text or '_(silent)_'}\n\n"
                )
                if response_text:
                    line += f"**{listener}** responds:\n\n> {response_text}\n\n"
                self._ensure_daily_header(daily_path, when)
                self.bridge.append_note(daily_path, line)

            # 2) per-voice note
            if self.config.write_per_voice_notes:
                voice_path = (
                    f"{self.config.voices_folder}/{speaker}/"
                    f"{when.strftime('%Y%m%dT%H%M%S')}_{uid}.md"
                )
                tags = " ".join(f"#{t}" for t in self.config.default_tags) + f" #voice/{speaker}"
                body = (
                    f"---\n"
                    f"aureon_voice: {speaker}\n"
                    f"listener: {listener}\n"
                    f"timestamp: {when.isoformat()}Z\n"
                    f"urgency: {urgency:.3f}\n"
                    f"reasoning: {reasoning}\n"
                    f"fingerprint_before: {fp_before}\n"
                    f"fingerprint_after: {fp_after}\n"
                    f"---\n\n"
                    f"# {speaker.title()} · {when.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    f"{tags}\n\n"
                    f"## Statement\n\n{statement_text or '_(silent)_'}\n\n"
                )
                if response_text:
                    body += f"## Response from {listener}\n\n{response_text}\n"
                self.bridge.write_note(voice_path, body, overwrite=False)

            self._utterances_written += 1
        except Exception as e:
            logger.debug("obsidian sink on_utterance failed: %s", e)

    def on_tick(self, tick: Any) -> None:
        """Append one tick's telemetry to the rolling loop log."""
        if tick is None or not self.bridge.health_check():
            return
        if not self.config.write_loop_log:
            return
        try:
            d = tick.to_dict() if hasattr(tick, "to_dict") else dict(tick)
            when = _dt.datetime.utcfromtimestamp(float(d.get("timestamp", 0) or 0))
            line = (
                f"- `{when.strftime('%Y-%m-%dT%H:%M:%SZ')}` "
                f"cycle={d.get('cycle')} "
                f"vault={d.get('vault_size')} "
                f"casimir={d.get('casimir_force')} "
                f"auris={d.get('auris_consensus')}/{d.get('auris_agreeing')} "
                f"cells={d.get('cells_deployed')}✓{d.get('cells_success')} "
                f"Λ={d.get('dominant_frequency_hz')}Hz "
                f"love={d.get('love_amplitude')} "
                f"gratitude={d.get('gratitude_score')}"
            )
            if d.get("spoke"):
                preview = str(d.get("utterance_preview", "")).replace("\n", " ")
                line += f" · {d.get('speaker')}→{d.get('listener')}: {preview}"
            line += "\n"

            path = f"{self.config.loops_folder}/self_feedback_loop.md"
            self._ensure_loop_header(path)
            self.bridge.append_note(path, line)
            self._ticks_written += 1
        except Exception as e:
            logger.debug("obsidian sink on_tick failed: %s", e)

    def on_audit(self, audit: Any) -> None:
        """Dump an integration audit snapshot into integrations/audit_trail.md."""
        if audit is None or not self.bridge.health_check():
            return
        if not self.config.write_audit_trail:
            return
        try:
            snapshot = audit if isinstance(audit, dict) else getattr(audit, "to_dict", lambda: {})()
            when = _dt.datetime.utcnow()
            tags = " ".join(f"#{t}" for t in self.config.default_tags) + " #audit"
            lines = [
                "",
                f"## {when.strftime('%Y-%m-%d %H:%M:%S')}Z — Integration Audit",
                "",
                tags,
                "",
            ]
            for key, val in snapshot.items():
                if isinstance(val, dict):
                    lines.append(f"### {key}")
                    for k2, v2 in val.items():
                        lines.append(f"- **{k2}**: `{v2}`")
                elif isinstance(val, list):
                    lines.append(f"### {key}")
                    for item in val:
                        lines.append(f"- {item}")
                else:
                    lines.append(f"- **{key}**: `{val}`")
            lines.append("")

            path = f"{self.config.integrations_folder}/audit_trail.md"
            self._ensure_audit_header(path)
            self.bridge.append_note(path, "\n".join(lines))
            self._audits_written += 1
        except Exception as e:
            logger.debug("obsidian sink on_audit failed: %s", e)

    # ─────────────────────────────────────────────────────────────────────
    # Header seeding
    # ─────────────────────────────────────────────────────────────────────

    def _daily_path(self, when: _dt.datetime) -> str:
        return f"{self.config.daily_folder}/{when.strftime('%Y-%m-%d')}.md"

    def _ensure_daily_header(self, path: str, when: _dt.datetime) -> None:
        existing = self.bridge.read_note(path)
        if existing is not None and existing.content.strip():
            return
        tags = " ".join(f"#{t}" for t in self.config.default_tags) + " #daily"
        header = (
            f"---\n"
            f"aureon_daily: {when.strftime('%Y-%m-%d')}\n"
            f"---\n\n"
            f"# Aureon Daily Journal — {when.strftime('%Y-%m-%d')}\n\n"
            f"{tags}\n\n"
            f"All self-authored utterances from the vault's voices on this day.\n"
        )
        self.bridge.write_note(path, header, overwrite=True)

    def _ensure_loop_header(self, path: str) -> None:
        existing = self.bridge.read_note(path)
        if existing is not None and existing.content.strip():
            return
        tags = " ".join(f"#{t}" for t in self.config.default_tags) + " #loop"
        header = (
            f"# Self-Feedback Loop — Tick Log\n\n"
            f"{tags}\n\n"
            f"One line per tick emitted by `AureonSelfFeedbackLoop.tick()`.\n\n"
        )
        self.bridge.write_note(path, header, overwrite=True)

    def _ensure_audit_header(self, path: str) -> None:
        existing = self.bridge.read_note(path)
        if existing is not None and existing.content.strip():
            return
        tags = " ".join(f"#{t}" for t in self.config.default_tags) + " #audit"
        header = (
            f"# Integration Audit Trail\n\n"
            f"{tags}\n\n"
            f"Snapshots of the Ollama + Obsidian bridges, emitted by "
            f"`IntegrationAuditTrail.run_full_audit()`.\n"
        )
        self.bridge.write_note(path, header, overwrite=True)

    # ─────────────────────────────────────────────────────────────────────
    # Utility
    # ─────────────────────────────────────────────────────────────────────

    def _extract_text(self, stmt: Any) -> str:
        if stmt is None:
            return ""
        if isinstance(stmt, str):
            return stmt
        text = getattr(stmt, "text", "")
        return str(text or "")

    def _trim(self, s: str) -> str:
        if len(s) > self.config.max_utterance_chars:
            return s[: self.config.max_utterance_chars] + "…"
        return s

    def get_status(self) -> Dict[str, Any]:
        return {
            "bridge_mode": self.bridge.mode.value,
            "reachable": self.bridge.health_check(),
            "utterances_written": self._utterances_written,
            "ticks_written": self._ticks_written,
            "audits_written": self._audits_written,
        }
