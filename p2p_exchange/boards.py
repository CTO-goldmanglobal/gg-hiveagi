"""
Contribution Board + Improvement Board — the two missing trust layers.

Three boards form a hybrid trust system:

  Layer 1: MACHINE SCORE (reputation.py)
           Fast, automatic. "Is this peer active and not flagged?"
           Score from interactions (good/bad tags, valid/invalid signatures).

  Layer 2: HUMAN APPRECIATION (appreciation.py)
           Slow, real. "Do other humans vouch for this person?"
           Star ratings + written reviews (Google Places style).

  Layer 3: CONTRIBUTION BOARD (this module)
           What has each person actually done?
           Tags shared, judgments made, domains covered, activity timeline.
           Like a GitHub contribution graph.

  Layer 4: IMPROVEMENT BOARD (this module)
           How are contributors growing over time, compared to each other?
           "Finn's contribution rate increased 40% this month.
            He's now #2 in tourism tags, up from #5."
           Long-term view — contribution delta, ranking changes, momentum.

Layer 1 is the first filter (machine).
Layer 2 is the real trust (human).
Layer 3 is the evidence (what have you done).
Layer 4 is the trajectory (are you growing?).
"""


import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


# ============================================================
# CONTRIBUTION BOARD — per-contributor stats
# ============================================================

class ContributionBoard:
    """
    Tracks what each contributor has contributed over time.

    Like a GitHub contribution graph — shows activity, not opinion.
    Fed by events from the pipeline (tag published, judgment made, etc.)

    Stored locally per node. Updated automatically as the node processes
    its own work and imports others' Seed Packages.
    """

    def __init__(self, board_path: Path):
        self.path = Path(board_path)
        self._contributors: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self._contributors = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._contributors = {}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._contributors, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def record_event(
        self,
        peer_id: str,
        event_type: str,
        domain: str = "",
        detail: str = "",
    ) -> None:
        """
        Record a contribution event for a peer.

        Event types: tag_published, judgment_made, override_applied,
                     appreciation_given, appreciation_received, seed_shared,
                     clip_adapted, script_written, qa_audit
        """
        if peer_id not in self._contributors:
            self._contributors[peer_id] = {
                "peer_id": peer_id,
                "first_seen": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "last_active": "",
                "total_events": 0,
                "event_counts": {},
                "domains": {},
                "timeline": [],
            }

        c = self._contributors[peer_id]
        c["last_active"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        c["total_events"] = c.get("total_events", 0) + 1
        c["event_counts"][event_type] = c["event_counts"].get(event_type, 0) + 1

        if domain:
            c["domains"][domain] = c["domains"].get(domain, 0) + 1

        # Keep timeline to last 100 events
        timeline = c.get("timeline", [])
        timeline.append({
            "type": event_type,
            "domain": domain,
            "at": c["last_active"],
            "detail": detail[:80],
        })
        c["timeline"] = timeline[-100:]

        self._save()

    def record_tag_published(self, peer_id: str, domain: str = "") -> None:
        self.record_event(peer_id, "tag_published", domain)

    def record_judgment_made(self, peer_id: str, domain: str = "") -> None:
        self.record_event(peer_id, "judgment_made", domain)

    def record_override(self, peer_id: str, domain: str = "") -> None:
        self.record_event(peer_id, "override_applied", domain)

    def record_seed_shared(self, peer_id: str) -> None:
        self.record_event(peer_id, "seed_shared")

    def get_profile(self, peer_id: str) -> Dict[str, Any]:
        """Get a contribution profile for a peer (like a GitHub profile)."""
        c = self._contributors.get(peer_id)
        if c is None:
            return {
                "peer_id": peer_id,
                "first_seen": None,
                "last_active": None,
                "total_events": 0,
                "event_counts": {},
                "domains": {},
                "tags_published": 0,
                "judgments_made": 0,
                "overrides": 0,
                "seeds_shared": 0,
            }

        ec = c.get("event_counts", {})
        return {
            "peer_id": peer_id,
            "first_seen": c.get("first_seen"),
            "last_active": c.get("last_active"),
            "total_events": c.get("total_events", 0),
            "event_counts": ec,
            "domains": c.get("domains", {}),
            "tags_published": ec.get("tag_published", 0),
            "judgments_made": ec.get("judgment_made", 0),
            "overrides": ec.get("override_applied", 0),
            "seeds_shared": ec.get("seed_shared", 0),
        }

    def render_profile(self, peer_id: str) -> str:
        """Render a human-readable contribution profile."""
        p = self.get_profile(peer_id)
        if p["total_events"] == 0:
            return f"  {peer_id}\n    No contributions yet."

        lines = [f"  {peer_id}"]
        lines.append(f"    Active: {p['first_seen'][:10]} → {p['last_active'][:10] if p['last_active'] else '?'}")
        lines.append(f"    Total events: {p['total_events']}")
        lines.append(f"    Tags published:  {p['tags_published']}")
        lines.append(f"    Judgments made:  {p['judgments_made']}")
        lines.append(f"    Overrides:       {p['overrides']}")
        lines.append(f"    Seeds shared:    {p['seeds_shared']}")

        domains = p.get("domains", {})
        if domains:
            sorted_d = sorted(domains.items(), key=lambda x: -x[1])
            dom_str = ", ".join(f"{d} ({n})" for d, n in sorted_d)
            lines.append(f"    Domains: {dom_str}")

        return "\n".join(lines)

    def leaderboard(self, metric: str = "total_events", limit: int = 10) -> List[Dict[str, Any]]:
        """Get top contributors by a metric."""
        profiles = [self.get_profile(pid) for pid in self._contributors]
        profiles.sort(key=lambda x: -x.get(metric, 0))
        return profiles[:limit]

    def render_leaderboard(self, metric: str = "total_events", limit: int = 10) -> str:
        """Render a leaderboard."""
        entries = self.leaderboard(metric, limit)
        if not entries:
            return "  No contributors yet."

        lines = [f"  🏆 Leaderboard ({metric})"]
        for i, p in enumerate(entries, 1):
            val = p.get(metric, 0)
            lines.append(f"    {i}. {p['peer_id']:<22} {val:>6}  ({p['tags_published']} tags, {p['judgments_made']} judgments)")
        return "\n".join(lines)

    def all_profiles(self) -> List[Dict[str, Any]]:
        """Get profiles for all contributors."""
        return [self.get_profile(pid) for pid in self._contributors]


# ============================================================
# IMPROVEMENT BOARD — growth + comparison over time
# ============================================================

class ImprovementBoard:
    """
    Tracks how contributors grow and compare over time.

    Snapshot-based: takes periodic snapshots of the contribution board
    and computes deltas (growth rates, ranking changes, momentum).

    Like comparing GitHub contribution graphs between months:
      "Finn went from #5 to #2 in tourism tags this quarter.
       His contribution rate increased 40%.
       New contributor hive_x9 is rising fast (+200% in 2 weeks)."
    """

    def __init__(self, board_path: Path):
        self.path = Path(board_path)
        self._snapshots: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self._snapshots = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._snapshots = []

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._snapshots, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def take_snapshot(self, contribution_board: ContributionBoard, label: str = "") -> Dict[str, Any]:
        """
        Take a snapshot of all contributor stats at this moment.
        Call this periodically (daily, weekly, per-circle).
        """
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        snapshot = {
            "timestamp": timestamp,
            "label": label,
            "contributors": {},
        }

        for profile in contribution_board.all_profiles():
            pid = profile["peer_id"]
            snapshot["contributors"][pid] = {
                "total_events": profile["total_events"],
                "tags_published": profile["tags_published"],
                "judgments_made": profile["judgments_made"],
                "overrides": profile["overrides"],
                "seeds_shared": profile["seeds_shared"],
                "domains": profile.get("domains", {}),
            }

        self._snapshots.append(snapshot)
        self._save()
        return snapshot

    def get_growth(
        self,
        peer_id: str,
        metric: str = "total_events",
        periods: int = 2,
    ) -> Dict[str, Any]:
        """
        Get growth data for a contributor over the last N snapshots.

        Returns: current value, previous value, delta, percentage change,
                 trend (up/down/stable).
        """
        if len(self._snapshots) < 2:
            return {"peer_id": peer_id, "metric": metric, "current": 0, "previous": 0,
                    "delta": 0, "pct_change": 0, "trend": "no_data"}

        latest = self._snapshots[-1]
        prev_idx = max(0, len(self._snapshots) - periods)
        previous = self._snapshots[prev_idx]

        curr_val = latest.get("contributors", {}).get(peer_id, {}).get(metric, 0)
        prev_val = previous.get("contributors", {}).get(peer_id, {}).get(metric, 0)
        delta = curr_val - prev_val

        if prev_val > 0:
            pct = round((delta / prev_val) * 100, 1)
        elif curr_val > 0:
            pct = 100.0  # new contributor
        else:
            pct = 0.0

        if delta > 0:
            trend = "↗"
        elif delta < 0:
            trend = "↘"
        else:
            trend = "→"

        return {
            "peer_id": peer_id,
            "metric": metric,
            "current": curr_val,
            "previous": prev_val,
            "delta": delta,
            "pct_change": pct,
            "trend": trend,
        }

    def get_ranking_changes(
        self,
        metric: str = "total_events",
    ) -> List[Dict[str, Any]]:
        """
        Compare rankings between the two most recent snapshots.

        Shows who moved up, who moved down, who's new.
        """
        if len(self._snapshots) < 2:
            return []

        latest = self._snapshots[-1]
        previous = self._snapshots[-2]

        # Rank contributors by metric in each snapshot
        def rank(snapshot):
            contribs = snapshot.get("contributors", {})
            ranked = sorted(contribs.items(), key=lambda x: -x[1].get(metric, 0))
            return {pid: i + 1 for i, (pid, _) in enumerate(ranked)}

        latest_rank = rank(latest)
        prev_rank = rank(previous)

        all_pids = set(latest_rank.keys()) | set(prev_rank.keys())
        changes = []
        for pid in all_pids:
            curr = latest_rank.get(pid)
            prev = prev_rank.get(pid)

            if curr and prev:
                change = prev - curr  # positive = moved up
                if change != 0:
                    changes.append({
                        "peer_id": pid,
                        "current_rank": curr,
                        "previous_rank": prev,
                        "change": change,
                        "direction": "↑" if change > 0 else "↓",
                    })
            elif curr and not prev:
                changes.append({
                    "peer_id": pid,
                    "current_rank": curr,
                    "previous_rank": None,
                    "change": "NEW",
                    "direction": "★",
                })

        # Sort by biggest movers first
        changes.sort(key=lambda x: -(x["change"] if isinstance(x["change"], int) else 0))
        return changes

    def network_growth(self) -> Dict[str, Any]:
        """
        Get overall network growth between last two snapshots.

        Total contributors, total events, total tags — and how they changed.
        """
        if len(self._snapshots) < 2:
            latest = self._snapshots[-1] if self._snapshots else {"contributors": {}}
            contribs = latest.get("contributors", {})
            return {
                "contributors": len(contribs),
                "total_events": sum(c.get("total_events", 0) for c in contribs.values()),
                "total_tags": sum(c.get("tags_published", 0) for c in contribs.values()),
                "total_judgments": sum(c.get("judgments_made", 0) for c in contribs.values()),
                "previous": None,
            }

        latest = self._snapshots[-1]
        previous = self._snapshots[-2]

        def totals(snapshot):
            contribs = snapshot.get("contributors", {})
            return {
                "contributors": len(contribs),
                "total_events": sum(c.get("total_events", 0) for c in contribs.values()),
                "total_tags": sum(c.get("tags_published", 0) for c in contribs.values()),
                "total_judgments": sum(c.get("judgments_made", 0) for c in contribs.values()),
            }

        curr = totals(latest)
        prev = totals(previous)

        deltas = {}
        for k in curr:
            deltas[k] = curr[k] - prev[k]

        return {"current": curr, "previous": prev, "deltas": deltas}

    def render_improvement(self, metric: str = "total_events") -> str:
        """Render a human-readable improvement report."""
        lines = ["  📈 Improvement Board"]

        # Network growth
        growth = self.network_growth()
        if growth.get("previous"):
            curr = growth["current"]
            prev = growth["previous"]
            deltas = growth["deltas"]
            lines.append("")
            lines.append(f"    Network: {curr['contributors']} contributors ({'+' if deltas['contributors'] >= 0 else ''}{deltas['contributors']})")
            lines.append(f"    Tags:    {curr['total_tags']} ({'+' if deltas['total_tags'] >= 0 else ''}{deltas['total_tags']})")
            lines.append(f"    Events:  {curr['total_events']} ({'+' if deltas['total_events'] >= 0 else ''}{deltas['total_events']})")

        # Ranking changes
        changes = self.get_ranking_changes(metric)
        if changes:
            lines.append("")
            lines.append("    Ranking changes:")
            for c in changes[:10]:
                if c["direction"] == "★":
                    lines.append(f"      {c['direction']} {c['peer_id']:<22} NEW (#{c['current_rank']})")
                else:
                    lines.append(f"      {c['direction']} {c['peer_id']:<22} #{c['previous_rank']} → #{c['current_rank']} ({'+' if c['change'] > 0 else ''}{c['change']})")

        return "\n".join(lines)
