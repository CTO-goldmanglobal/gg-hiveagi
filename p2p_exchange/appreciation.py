"""
Human Appreciation Board — Google Places style reviews for peers.

Replaces the machine-computed reputation system. Trust is expressed by
HUMANS, not calculated by algorithms. Same principle as the whole project:
the human decides, the machine executes.

How it works:
  - After interacting with a peer's tags/judgments, a human writes appreciation
  - Appreciation = star rating + written feedback (like a Google review)
  - The appreciation is signed by the reviewer (Ed25519)
  - Shared via IPFS (it's human perspective about human perspective)
  - Other humans read the board and decide for themselves who to trust

This is NOT a machine reputation score. It is human testimony.

Schema (one appreciation entry):
{
  "schema_version": 1,
  "reviewer_peer_id": "hive_a1b2...",
  "reviewed_peer_id": "hive_c3d4...",
  "rating": 5,                      # 1-5 stars
  "domain": "tourism",              # what domain they interacted in
  "headline": "Best Warriors tags I've seen",
  "body": "Finn's tags on the Terracotta Warriors were the most
           accurate I've encountered. His dawn lighting calls are
           consistently spot on.",
  "interactions": 12,               # how many tags/judgments reviewed
  "signed_at": "2026-07-30T...",
  "signature": "ed25519_signature"
}
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from .identity import sign_manifest, verify_manifest, peer_id_from_public_key


def create_appreciation(
    reviewer_peer_id: str,
    reviewed_peer_id: str,
    rating: int,
    domain: str = "",
    headline: str = "",
    body: str = "",
    interactions: int = 0,
) -> Dict[str, Any]:
    """
    Create an appreciation entry (before signing).

    Args:
        reviewer_peer_id: the peer writing the appreciation
        reviewed_peer_id: the peer being appreciated
        rating: 1-5 stars (5 = excellent)
        domain: what domain (tourism, food, architecture, etc.)
        headline: short summary (like a Google review title)
        body: written feedback (free text — this is the real value)
        interactions: how many of their tags/judgments the reviewer has seen

    Returns:
        Unsigned appreciation dict.
    """
    if not 1 <= rating <= 5:
        raise ValueError("rating must be 1-5")

    return {
        "schema_version": 1,
        "type": "appreciation",
        "reviewer_peer_id": reviewer_peer_id,
        "reviewed_peer_id": reviewed_peer_id,
        "rating": rating,
        "domain": domain,
        "headline": headline[:120],  # keep headlines short
        "body": body[:2000],         # reasonable limit for feedback
        "interactions": interactions,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def sign_appreciation(
    appreciation: Dict[str, Any],
    private_key_pem: bytes,
) -> Dict[str, Any]:
    """
    Sign an appreciation entry with the reviewer's private key.

    This binds the appreciation to the reviewer's identity.
    The reviewed peer (and anyone) can verify it was really written
    by the claimed reviewer.
    """
    return sign_manifest(appreciation, private_key_pem, embed_key=False)


def verify_appreciation(
    appreciation: Dict[str, Any],
    reviewer_public_key_pem: bytes,
) -> tuple:
    """
    Verify an appreciation entry's signature.

    Returns:
        (valid: bool, message: str)
    """
    return verify_manifest(appreciation, reviewer_public_key_pem)


# ============================================================
# Appreciation Board — aggregate + display
# ============================================================

class AppreciationBoard:
    """
    A local collection of appreciation entries.

    Stores appreciations the node has received or fetched from IPFS.
    Can be queried by peer, by domain, by rating.
    """

    def __init__(self, board_path: Path):
        self.path = Path(board_path)
        self._entries: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        """Load appreciations from disk."""
        if self.path.exists():
            try:
                self._entries = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._entries = []

    def _save(self) -> None:
        """Save to disk."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._entries, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def add(self, appreciation: Dict[str, Any]) -> None:
        """Add an appreciation entry to the board."""
        # Check if updating an existing review from same reviewer → same peer
        reviewer = appreciation.get("reviewer_peer_id")
        reviewed = appreciation.get("reviewed_peer_id")
        domain = appreciation.get("domain", "")

        # Replace existing appreciation from same reviewer for same peer+domain
        self._entries = [
            e for e in self._entries
            if not (e.get("reviewer_peer_id") == reviewer
                    and e.get("reviewed_peer_id") == reviewed
                    and e.get("domain", "") == domain)
        ]
        self._entries.append(appreciation)
        self._save()

    def for_peer(self, peer_id: str) -> List[Dict[str, Any]]:
        """Get all appreciations about a specific peer."""
        return [e for e in self._entries if e.get("reviewed_peer_id") == peer_id]

    def by_reviewer(self, reviewer_id: str) -> List[Dict[str, Any]]:
        """Get all appreciations written by a specific reviewer."""
        return [e for e in self._entries if e.get("reviewer_peer_id") == reviewer_id]

    def average_rating(self, peer_id: str) -> Optional[float]:
        """Get average star rating for a peer (None if no appreciations)."""
        entries = self.for_peer(peer_id)
        if not entries:
            return None
        return sum(e["rating"] for e in entries) / len(entries)

    def summary(self, peer_id: str) -> Dict[str, Any]:
        """Get a summary card for a peer (like a Google Places summary)."""
        entries = self.for_peer(peer_id)
        if not entries:
            return {
                "peer_id": peer_id,
                "total_reviews": 0,
                "average": None,
                "stars": {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0},
            }

        avg = sum(e["rating"] for e in entries) / len(entries)
        stars = {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0}
        for e in entries:
            stars[str(e["rating"])] = stars.get(str(e["rating"]), 0) + 1

        # Top domains
        domains = {}
        for e in entries:
            d = e.get("domain", "general")
            domains[d] = domains.get(d, 0) + 1

        return {
            "peer_id": peer_id,
            "total_reviews": len(entries),
            "average": round(avg, 1),
            "stars": stars,
            "top_domains": sorted(domains.items(), key=lambda x: -x[1])[:3],
            "latest_headline": entries[-1].get("headline", "") if entries else "",
        }

    def render_card(self, peer_id: str) -> str:
        """Render a human-readable appreciation card for display."""
        s = self.summary(peer_id)
        avg = s["average"]
        if avg is None:
            return f"  {peer_id}\n    No appreciations yet."

        stars = "★" * round(avg) + "☆" * (5 - round(avg))
        lines = [
            f"  {peer_id}",
            f"    {stars} {avg:.1f} ({s['total_reviews']} review{'s' if s['total_reviews'] != 1 else ''})",
        ]
        if s.get("latest_headline"):
            lines.append(f"    \"{s['latest_headline']}\"")
        if s.get("top_domains"):
            domains_str = ", ".join(f"{d} ({n})" for d, n in s["top_domains"])
            lines.append(f"    Domains: {domains_str}")
        star_dist = s["stars"]
        lines.append(f"    5★:{star_dist['5']} 4★:{star_dist['4']} 3★:{star_dist['3']} 2★:{star_dist['2']} 1★:{star_dist['1']}")
        return "\n".join(lines)

    def all_summaries(self) -> List[Dict[str, Any]]:
        """Get summary cards for all reviewed peers."""
        peer_ids = set(e.get("reviewed_peer_id") for e in self._entries)
        return [self.summary(pid) for pid in peer_ids if pid]
