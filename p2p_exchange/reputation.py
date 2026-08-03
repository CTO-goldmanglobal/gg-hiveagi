"""
Spam filter — the machine's only job is moving junk out of the human's way.

Like an email spam folder: the machine doesn't decide trust. It just
filters obvious junk so the human's inbox (appreciation board + contribution
board) only contains things worth looking at.

How it works:
  - New peer: passes filter (goes to inbox)
  - Invalid signature: spam (filtered)
  - Invalid signature again: spam (stays filtered)
  - Multiple rejected tags: maybe spam (flagged, human decides)
  - Valid signatures + accepted tags: stays in inbox (no action needed)

The machine NEVER decides "trusted." Only humans express trust (appreciation
board). The machine only decides "is this junk?"

The human can always check the spam folder — just like email, real
perspective data might occasionally end up filtered. The human is the
final arbiter, not the machine.
"""

import json
import time
from pathlib import Path
from typing import Any

# Spam detection thresholds (machine-operated, human-overridable)
SPAM_THRESHOLD = -3.0  # at or below → spam folder
FLAG_THRESHOLD = 0.0  # below 0 but above spam → flagged (check)
INVALID_SIG_PENALTY = -2.0  # each invalid signature
BAD_TAG_PENALTY = -0.5  # each rejected tag
SPAM_REPORT_PENALTY = -3.0  # explicit spam report (immediate spam)
GOOD_TAG_BONUS = 0.05  # each accepted tag (keeps healthy peers healthy)


class SpamFilter:
    """
    Machine-operated spam filter for incoming tags/Seed Packages.

    Like email spam: fast, automatic, imperfect, human-overridable.
    Stored locally per node (not shared — it's machine opinion, not human).
    """

    def __init__(self, store_path: Path):
        self.path = Path(store_path)
        self._scores: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self._scores = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._scores = {}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._scores, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _ensure_entry(self, peer_id: str) -> None:
        if peer_id not in self._scores:
            self._scores[peer_id] = {
                "score": 0.0,
                "events": [],
                "in_spam": False,
                "first_seen": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }

    def get_score(self, peer_id: str) -> float:
        entry = self._scores.get(peer_id)
        return entry["score"] if entry else 0.0

    def is_spam(self, peer_id: str) -> bool:
        """Should this peer's tags go to the spam folder?"""
        entry = self._scores.get(peer_id)
        if not entry:
            return False
        if entry.get("manually_kept"):
            return False
        return entry.get("in_spam", False) or entry["score"] <= SPAM_THRESHOLD

    def is_flagged(self, peer_id: str) -> bool:
        """Should the human be warned about this peer? (not full spam)"""
        if self.is_spam(peer_id):
            return False
        entry = self._scores.get(peer_id)
        if not entry:
            return False
        return entry["score"] < FLAG_THRESHOLD

    def should_show_in_inbox(self, peer_id: str) -> bool:
        """Should this peer's tags appear in the human's main view?"""
        return not self.is_spam(peer_id)

    def record_invalid_signature(self, peer_id: str) -> float:
        """Invalid signature detected — likely forgery or corruption."""
        self._ensure_entry(peer_id)
        entry = self._scores[peer_id]
        entry["score"] = round(entry["score"] + INVALID_SIG_PENALTY, 2)
        self._check_spam_status(peer_id)
        self._log_event(peer_id, "invalid_sig", INVALID_SIG_PENALTY)
        self._save()
        return entry["score"]

    def record_bad_tag(self, peer_id: str, reason: str = "") -> float:
        """A tag from this peer was rejected by the human or schema."""
        self._ensure_entry(peer_id)
        entry = self._scores[peer_id]
        entry["score"] = round(entry["score"] + BAD_TAG_PENALTY, 2)
        self._check_spam_status(peer_id)
        self._log_event(peer_id, "bad_tag", BAD_TAG_PENALTY, reason)
        self._save()
        return entry["score"]

    def record_spam_report(self, peer_id: str) -> float:
        """Explicit spam report from a human."""
        self._ensure_entry(peer_id)
        entry = self._scores[peer_id]
        entry["score"] = round(entry["score"] + SPAM_REPORT_PENALTY, 2)
        self._check_spam_status(peer_id)
        self._log_event(peer_id, "spam_report", SPAM_REPORT_PENALTY)
        self._save()
        return entry["score"]

    def record_good_tag(self, peer_id: str) -> float:
        """A tag from this peer was accepted (healthy signal)."""
        self._ensure_entry(peer_id)
        entry = self._scores[peer_id]
        entry["score"] = round(entry["score"] + GOOD_TAG_BONUS, 2)
        self._log_event(peer_id, "good_tag", GOOD_TAG_BONUS)
        self._save()
        return entry["score"]

    def manual_keep(self, peer_id: str) -> None:
        """Human overrides: 'this is NOT spam, keep it in my inbox.'"""
        self._ensure_entry(peer_id)
        self._scores[peer_id]["manually_kept"] = True
        self._scores[peer_id]["in_spam"] = False
        self._log_event(peer_id, "manual_keep", 0, "human override: not spam")
        self._save()

    def manual_spam(self, peer_id: str) -> None:
        """Human overrides: 'this IS spam, filter it.'"""
        self._ensure_entry(peer_id)
        self._scores[peer_id]["in_spam"] = True
        self._log_event(peer_id, "manual_spam", 0, "human override: is spam")
        self._save()

    def _check_spam_status(self, peer_id: str) -> None:
        """Update spam flag based on score (unless manually overridden)."""
        entry = self._scores[peer_id]
        if entry.get("manually_kept"):
            entry["in_spam"] = False
            return
        entry["in_spam"] = entry["score"] <= SPAM_THRESHOLD

    def _log_event(self, peer_id: str, event: str, delta: float, detail: str = "") -> None:
        entry = self._scores[peer_id]
        events = entry.get("events", [])
        events.append(
            {
                "event": event,
                "delta": delta,
                "detail": detail[:80],
                "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )
        entry["events"] = events[-20:]  # keep last 20
        entry["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def get_spam_list(self) -> list[str]:
        """Get all peer IDs currently in spam folder."""
        return [pid for pid, entry in self._scores.items() if self.is_spam(pid)]

    def get_flagged_list(self) -> list[str]:
        """Get all peer IDs flagged for human attention."""
        return [pid for pid in self._scores if self.is_flagged(pid)]

    def summary(self) -> dict[str, Any]:
        """Spam folder summary."""
        return {
            "total_peers_tracked": len(self._scores),
            "in_spam": len(self.get_spam_list()),
            "flagged": len(self.get_flagged_list()),
            "in_inbox": sum(1 for pid in self._scores if self.should_show_in_inbox(pid)),
        }

    def render_spam_report(self) -> str:
        """Human-readable spam folder status."""
        s = self.summary()
        lines = [
            f"  📧 Inbox: {s['in_inbox']} peers",
            f"  🚩 Flagged: {s['flagged']} peers (human should check)",
            f"  🗑️  Spam: {s['in_spam']} peers (auto-filtered)",
        ]
        spam_list = self.get_spam_list()
        if spam_list:
            lines.append(f"     {', '.join(spam_list[:5])}")
        return "\n".join(lines)
