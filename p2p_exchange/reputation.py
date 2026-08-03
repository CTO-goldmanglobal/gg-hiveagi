"""
Reputation system — web-of-trust for P2P tag exchange.

Addresses DeepSeek's finding:
  "There is a real risk of malicious nodes publishing bad tags."

Design:
  - Each node maintains a local reputation score for every peer it has
    interacted with
  - Reputation starts at 0 (neutral)
  - Positive interactions (useful tags, valid signatures) increase score
  - Negative interactions (invalid signatures, rejected tags, spam) decrease
  - Tags from low-reputation peers are weighted lower or ignored
  - No central authority — reputation is local to each node

The reputation data is private to each node (not shared via IPFS).
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional


# Reputation thresholds
REPUTATION_NEUTRAL = 0.0       # default for new peers
REPUTATION_TRUSTED = 5.0       # tags accepted by default
REPUTATION_UNTRUSTED = -5.0    # tags ignored
PUBLISH_GATE = 1.0             # minimum reputation to publish tags

# Score changes
SCORE_GOOD_TAG = 0.1           # tag accepted by another node
SCORE_BAD_TAG = -0.5           # tag rejected / flagged
SCORE_VALID_SIGNATURE = 0.05   # valid signed package received
SCORE_INVALID_SIGNATURE = -5.0 # invalid signature (serious — possible forgery)
SCORE_SPAM = -5.0              # spam detected
SCORE_USEFUL_OVERRIDE = 0.2    # human found peer's override useful


class ReputationStore:
    """
    Local reputation store for peers.

    Stored as JSON in the node's local data (not shared via IPFS).
    Each entry: peer_id → {score, interactions, last_updated}
    """

    def __init__(self, store_path: Path):
        self.path = Path(store_path)
        self._store: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        """Load reputation from disk."""
        if self.path.exists():
            try:
                self._store = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._store = {}

    def _save(self) -> None:
        """Save reputation to disk."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._store, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def get_score(self, peer_id: str) -> float:
        """Get reputation score for a peer (default: neutral)."""
        entry = self._store.get(peer_id)
        if entry is None:
            return REPUTATION_NEUTRAL
        return entry.get("score", REPUTATION_NEUTRAL)

    def get_status(self, peer_id: str) -> str:
        """Get reputation status: trusted / neutral / untrusted."""
        score = self.get_score(peer_id)
        if score >= REPUTATION_TRUSTED:
            return "trusted"
        if score <= REPUTATION_UNTRUSTED:
            return "untrusted"
        return "neutral"

    def can_publish(self, peer_id: str) -> bool:
        """Check if a peer has enough reputation to publish tags."""
        return self.get_score(peer_id) >= PUBLISH_GATE

    def should_accept_tags(self, peer_id: str) -> bool:
        """Check if tags from this peer should be accepted (not ignored)."""
        return self.get_score(peer_id) > REPUTATION_UNTRUSTED

    def record_interaction(
        self,
        peer_id: str,
        event: str,
        score_delta: float,
        detail: str = "",
    ) -> float:
        """
        Record a reputation event for a peer.

        Args:
            peer_id: the peer's identity
            event: what happened (e.g., "good_tag", "invalid_sig")
            score_delta: how much to adjust score
            detail: optional context

        Returns:
            The peer's new score.
        """
        if peer_id not in self._store:
            self._store[peer_id] = {
                "score": REPUTATION_NEUTRAL,
                "interactions": 0,
                "events": [],
                "first_seen": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }

        entry = self._store[peer_id]
        entry["score"] = round(entry["score"] + score_delta, 2)
        entry["interactions"] = entry.get("interactions", 0) + 1
        entry["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Keep last 20 events (prevent unbounded growth)
        events = entry.get("events", [])
        events.append({
            "event": event,
            "delta": score_delta,
            "detail": detail[:100],
            "at": entry["last_updated"],
        })
        entry["events"] = events[-20:]

        self._save()
        return entry["score"]

    def record_good_tag(self, peer_id: str, detail: str = "") -> float:
        """A tag from this peer was accepted (useful)."""
        return self.record_interaction(peer_id, "good_tag", SCORE_GOOD_TAG, detail)

    def record_bad_tag(self, peer_id: str, detail: str = "") -> float:
        """A tag from this peer was rejected (not useful)."""
        return self.record_interaction(peer_id, "bad_tag", SCORE_BAD_TAG, detail)

    def record_valid_signature(self, peer_id: str) -> float:
        """Received a valid signed package from this peer."""
        return self.record_interaction(peer_id, "valid_sig", SCORE_VALID_SIGNATURE)

    def record_invalid_signature(self, peer_id: str) -> float:
        """Received an invalid signature (serious — possible forgery)."""
        return self.record_interaction(peer_id, "invalid_sig", SCORE_INVALID_SIGNATURE)

    def record_spam(self, peer_id: str) -> float:
        """Spam detected from this peer."""
        return self.record_interaction(peer_id, "spam", SCORE_SPAM)

    def summary(self) -> Dict[str, Any]:
        """Get a summary of all tracked peers."""
        return {
            "total_peers": len(self._store),
            "trusted": sum(1 for p in self._store.values()
                          if p.get("score", 0) >= REPUTATION_TRUSTED),
            "neutral": sum(1 for p in self._store.values()
                          if REPUTATION_UNTRUSTED < p.get("score", 0) < REPUTATION_TRUSTED),
            "untrusted": sum(1 for p in self._store.values()
                             if p.get("score", 0) <= REPUTATION_UNTRUSTED),
        }
