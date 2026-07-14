"""
ApprovalEmail — the director's email loop: Aureon mails Gary each big play, and
reads his reply as the decision.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Gary runs the company as director from his inbox: when Aureon prepares a big play it
emails him a summary; he replies "approve" or "reject"; Aureon reads the reply and
records his decision on the approval queue. Strictly scoped and safe:

  • Sends ONLY to the one configured owner address (``AUREON_OWNER_EMAIL``) — never to
    a third party. It is a notification to the director, not autonomous correspondence.
  • Reads ONLY replies to its own tagged approval subjects, matches the item id, and
    records approve/reject on the queue. Ambiguous replies are left pending.
  • **Records the decision; never executes.** Approving flips the queue item to
    ``approved``; the irreversible move (the trade, the payment, the filing) stays
    Gary's deliberate hand. There is no "approved → fire the trade" path here.
  • Opt-in and offline-safe: does nothing unless ``AUREON_APPROVAL_EMAIL`` is set AND
    a transport is available; with no creds it is a no-op. The transport is injectable
    (duck-typed ``send`` / ``fetch_replies``) so it is fully testable with a stub and
    never touches the network in tests.

NOT here (the fixed line): no general inbox scanning, no replying to or emailing third
parties, no auto-execution of any live/outward action.

Gary Leckey · Aureon Institute
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Protocol

logger = logging.getLogger("aureon.operator.approval_email")

_SUBJECT_PREFIX = "[AUREON approval"
_ID_RE = re.compile(r"\[AUREON approval\s+([0-9a-f]{6,12})\]", re.IGNORECASE)
_APPROVE_WORDS = ("approve", "approved", "yes", "go", "ok", "okay", "proceed", "confirm")
_REJECT_WORDS = ("reject", "rejected", "no", "deny", "denied", "stop", "cancel", "hold")


def _truthy(name: str) -> bool:
    return str(os.environ.get(name, "") or "").strip().lower() in {"1", "true", "yes", "on"}


class EmailTransport(Protocol):
    """The minimal duck-typed transport the loop needs. A real SMTP/IMAP adapter or a
    test stub both satisfy it."""

    def send(self, to: str, subject: str, body: str) -> bool: ...

    def fetch_replies(self) -> list[dict[str, Any]]: ...  # [{subject, body, from}]


def _parse_decision(body: str) -> str | None:
    """Read a clear approve/reject from the first meaningful line of a reply; an
    ambiguous reply returns None (left pending — never guessed)."""
    for raw in str(body or "").splitlines():
        line = raw.strip().lower()
        if not line or line.startswith(">"):  # skip blanks + quoted original
            continue
        token = re.split(r"[\s,.!:;]", line, maxsplit=1)[0]
        if token in _APPROVE_WORDS or line in _APPROVE_WORDS:
            return "approve"
        if token in _REJECT_WORDS or line in _REJECT_WORDS:
            return "reject"
        return None  # first real line was neither → don't guess
    return None


class ApprovalEmail:
    """Owner-scoped notify + reply-capture for the approval queue. Records only."""

    def __init__(self, transport: EmailTransport | None = None,
                 owner_email: str | None = None) -> None:
        self._transport = transport
        self._owner = owner_email or os.environ.get("AUREON_OWNER_EMAIL", "")

    @property
    def enabled(self) -> bool:
        return _truthy("AUREON_APPROVAL_EMAIL") and bool(self._owner) and self._transport is not None

    # ── notify: mail the owner one summary of a prepared big play ───────────
    def notify(self, item: dict[str, Any]) -> bool:
        """Email the owner a prepared proposal. Owner-only; no-op unless enabled."""
        if not self.enabled or self._transport is None:
            return False
        try:
            item_id = str(item.get("id", ""))
            subject = f"{_SUBJECT_PREFIX} {item_id}] {item.get('kind', 'decision')} — needs your call"
            body = (f"Aureon has prepared a {item.get('kind')} and is holding it for you.\n\n"
                    f"{item.get('summary', '')}\n\n"
                    f"Risk: {item.get('risk')}\n\n"
                    f"Reply APPROVE or REJECT to record your decision. This records your "
                    f"decision only — the live move stays your deliberate step.")
            return bool(self._transport.send(self._owner, subject, body))
        except Exception as exc:  # noqa: BLE001 — a mail hiccup never crashes the organism
            logger.debug("approval notify skipped: %s", exc)
            return False

    def notify_pending(self) -> int:
        """Notify the owner of every pending item not yet mailed (best-effort)."""
        if not self.enabled:
            return 0
        try:
            from aureon.core.approval_queue import get_approval_queue

            sent = 0
            for item in get_approval_queue().pending():
                if self.notify(item):
                    sent += 1
            return sent
        except Exception as exc:  # noqa: BLE001
            logger.debug("notify_pending skipped: %s", exc)
            return 0

    # ── capture: read the owner's replies and record the decision ───────────
    def ingest_replies(self) -> list[dict[str, Any]]:
        """Read replies to our tagged subjects, match the id, and RECORD approve/reject
        on the queue. Never executes. Returns the decisions applied."""
        if not self.enabled or self._transport is None:
            return []
        applied: list[dict[str, Any]] = []
        try:
            from aureon.core.approval_queue import get_approval_queue

            q = get_approval_queue()
            for msg in self._transport.fetch_replies():
                m = _ID_RE.search(str(msg.get("subject", "")))
                if not m:
                    continue
                decision = _parse_decision(str(msg.get("body", "")))
                if decision is None:
                    continue
                item = q.decide(m.group(1), decision, approver="gary-email",
                                note="via email reply")
                if item is not None:
                    applied.append({"id": m.group(1), "decision": decision, "status": item.get("status")})
        except Exception as exc:  # noqa: BLE001
            logger.debug("ingest_replies skipped: %s", exc)
        return applied


_email: ApprovalEmail | None = None


def get_approval_email() -> ApprovalEmail:
    """Process-global approval-email singleton (owner-scoped, opt-in, records-only)."""
    global _email
    if _email is None:
        _email = ApprovalEmail()
    return _email


__all__ = ["ApprovalEmail", "EmailTransport", "get_approval_email"]
