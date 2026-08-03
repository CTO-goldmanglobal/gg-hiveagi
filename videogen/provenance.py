"""
Provenance gate — the seam that keeps the Labs human-perspective thesis honest.

This is the one place in the whole project where the core thesis can be
silently corrupted, so it is enforced in CODE, not policy.

(Note: the PII blur layer uses a different model — it is a human-controlled
layer with a default-ON safety position and a human toggle with reason
logging. The provenance gate has no toggle — stock is always blocked from
Labs. See docs/HYBRID-EDGE-ARCHITECTURE.md § Layer 0.5.)

The rule:
  - Stock footage (professional content optimized for an audience) is FINE for
    Forge commercial deliverables. A tour Reel cut from Pexels is normal video
    production.
  - Stock footage is FORBIDDEN from Labs Seed packages. The human-perspective
    network requires material a human *naturally noticed*, not what a
    production department *staged to be noticed*. Feeding stock pixels into
    Labs would teach the model "what production finds beautiful," not "what a
    human finds beautiful" — and the entire AGI argument collapses.
  - Human JUDGMENT (accept/reject + reason + cut point) is Labs-eligible
    REGARDLESS of what it was judged against — because human taste IS human
    perspective. But it is always tagged with `source_type`, so Labs can
    distinguish "editor taste on stock footage" from "editor taste on their own
    capture."

See docs/LOOP-STRATEGY.md § "The hybrid seed" for the full reasoning.
"""

from typing import Any, Dict, List, Tuple


# Source-type prefixes. A full source_type looks like "<prefix>:<detail>"
# e.g. "stock:pexels", "stock:pixabay", "human_capture:glasses",
# "human_capture:phone", "human_capture:eyeball".
SOURCE_STOCK = "stock"
SOURCE_HUMAN = "human_capture"


# Area: which domain a model/tag/seed belongs to.
# OPEN (Labs)      — open source, AGPL, shared freely via IPFS
# COMMERCIAL (Forge) — business asset (client or personal), sharing is a
#                      human decision, always ask. Includes bloggers whose
#                      personal taste model is their own asset.
AREA_OPEN = "open"
AREA_COMMERCIAL = "commercial"


class ProvenanceViolation(Exception):
    """Raised when stock/unprovenanced material would reach Labs Seed publish."""
    pass


class ShareConsentViolation(Exception):
    """Raised when a commercial item would be published without owner consent."""
    pass


def is_stock(source_type: str) -> bool:
    """True if the material originated from a stock library (professional content)."""
    if not source_type:
        return False
    return source_type.split(":", 1)[0] == SOURCE_STOCK


def is_human_capture(source_type: str) -> bool:
    """True if the material was captured by a human's own device (glasses/phone)."""
    if not source_type:
        return False
    return source_type.split(":", 1)[0] == SOURCE_HUMAN


# ============================================================
# Area gate — who owns the model/tag/seed, and can it be shared?
# ============================================================
#
# Two areas:
#   OPEN (Labs)       — shared freely. Tags, seeds, patterns published
#                       to IPFS by default. This is the research network.
#
#   COMMERCIAL (Forge) — business asset. This includes:
#                        - Client work (ECH tour videos, real-estate, etc.)
#                        - Blogger personal taste models (their learned
#                          preferences are THEIR asset)
#                        Sharing is NEVER automatic. The human must be asked.
#                        "Provenance tracked, but sharing decided by the owner."
#
# The gate is simple: OPEN shares by default. COMMERCIAL does not.
# Every COMMERCIAL item that enters IPFS must carry an explicit
# share_consent field with a timestamp and reason.


def can_share_to_labs(area: str, share_consent: bool = False) -> bool:
    """
    Can this tag/seed/pattern be published to the open IPFS network?

    Args:
        area: "open" or "commercial"
        share_consent: for commercial items, did the owner explicitly consent?

    Returns:
        True if the item can be shared to the Labs network.
    """
    if area == AREA_OPEN:
        return True
    if area == AREA_COMMERCIAL:
        return share_consent  # must be explicitly asked + answered
    # Unknown area → fail closed
    return False


def assert_share_consent(area: str, share_consent: bool, item_id: str = "") -> None:
    """
    Hard assertion for IPFS publish path.

    Raises ShareConsentViolation if a commercial item is being published
    without explicit consent. This is the "always ask the human" rule,
    enforced in code. Unknown areas also fail closed.
    """
    if area not in (AREA_OPEN, AREA_COMMERCIAL):
        raise ShareConsentViolation(
            f"Unknown area '{area}' for item{f' ({item_id})' if item_id else ''}. "
            f"Must be '{AREA_OPEN}' or '{AREA_COMMERCIAL}'. Fail closed."
        )
    if area == AREA_COMMERCIAL and not share_consent:
        raise ShareConsentViolation(
            f"Cannot publish commercial item{f' ({item_id})' if item_id else ''} "
            f"to open network without explicit consent. "
            f"The owner must be asked. See provenance.py § area gate."
        )


def is_labs_eligible(source_type: str) -> bool:
    """
    The gate. Returns True only if the material may enter a Labs Seed package.

    Stock → False. Human capture → True. Unknown/empty → False (fail closed;
    absence of a source_type tag means unprovenanced, and unprovenanced data
    does not enter Labs).

    Note: this gates RAW MATERIAL (pixels/frames), not judgments. The human
    judgment layer is always Labs-eligible; it carries its own source_type so
    Labs knows what it was judged against. Use is_judgment_labs_eligible() for
    judgment rows, or attach the judged-against source_type to the judgment row
    and let the Labs consumer decide.
    """
    if is_human_capture(source_type):
        return True
    # Stock or unknown → blocked
    return False


def is_judgment_labs_eligible(judgment_row: Dict[str, Any]) -> bool:
    """
    Gate for human-JUDGMENT rows (accept/reject + reason on a candidate).

    Human judgment is always Labs-eligible in principle — it is human
    perspective. But the row MUST carry a `source_type` so Labs knows what it
    was judged against. A judgment row without provenance is rejected (fail
    closed), same discipline as raw material.
    """
    if not judgment_row.get("source_type"):
        return False
    # A judgment row is eligible as long as it is tagged. Labs consumers use
    # source_type to bucket "taste on stock" vs "taste on human capture."
    return True


def filter_for_labs(
    entries: List[Dict[str, Any]],
    source_type_field: str = "source_type",
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Split a list of entries into (labs_eligible, rejected).

    Used by ANY export path that feeds p2p_exchange / Seed Packages. This is
    the hard gate: call it before publishing anything to Labs. It logs the
    rejection count so silent provenance drift is visible.

    Args:
        entries: list of dicts (raw-material rows OR judgment rows). For
                 judgment rows, the presence of a source_type makes them
                 eligible; for raw-material rows, only human_capture passes.
        source_type_field: which key holds the source_type (default "source_type").

    Returns:
        (eligible, rejected) — two lists. Same ordering as input.
    """
    eligible: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    for e in entries:
        st = e.get(source_type_field, "")
        if is_labs_eligible(st):
            eligible.append(e)
        else:
            rejected.append(e)
    if rejected:
        # Visible in logs — silent provenance drift is the failure mode this
        # module exists to prevent.
        print(f"  [provenance] blocked {len(rejected)} stock/unprovenanced "
              f"entries from Labs (of {len(entries)} total)")
    return eligible, rejected


def assert_labs_safe(entries: List[Dict[str, Any]]) -> None:
    """
    Hard-fail variant for export paths that must NEVER ship stock.

    Raises ProvenanceViolation if any entry is not Labs-eligible. Use this in
    the Seed Package publisher (p2p_exchange) where a silent block is not
    enough — the publish should fail loudly.
    """
    _, rejected = filter_for_labs(entries)
    if rejected:
        sample = rejected[0].get("source_type", "<missing>")
        raise ProvenanceViolation(
            f"{len(rejected)} entries blocked from Labs Seed publish. "
            f"First rejected source_type: {sample}. "
            f"Stock/unprovenanced material cannot enter the Labs network. "
            f"See docs/LOOP-STRATEGY.md § The hybrid seed."
        )
