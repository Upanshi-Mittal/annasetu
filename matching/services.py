"""
Smart matching engine — scores NGOs for a given donation.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from django.conf import settings
from django.utils import timezone

from matching.geo import get_nearby_users

logger = logging.getLogger(__name__)


@dataclass
class MatchScore:
    """Breakdown of an NGO's match score for a donation."""
    ngo_id: int
    ngo_name: str
    total_score: float = 0.0
    distance_km: float = 0.0
    distance_score: float = 0.0
    capacity_score: float = 0.0
    food_type_score: float = 0.0
    reliability_score: float = 0.0
    response_rate_score: float = 0.0
    urgency_bonus: float = 0.0
    reasons: list[str] = field(default_factory=list)


def compute_match_scores(
    donation,
    radius_km: Optional[float] = None,
    top_n: Optional[int] = None,
) -> list[MatchScore]:
    """
    Compute ranked match scores for NGOs near a donation.

    Scoring weights:
    - Distance (30%): closer is better, exponential decay
    - Capacity remaining (20%): NGOs with more capacity today score higher
    - Food type compatibility (15%): veg-only NGOs penalised for non-veg
    - Reliability (20%): based on reliability_score (1-5)
    - Response rate (10%): based on past claim acceptance ratio
    - Urgency bonus (5%): extra points if donation is urgent

    Returns sorted list of MatchScore, highest first.
    """
    if radius_km is None:
        radius_km = settings.MATCHING_RADIUS_KM
    if top_n is None:
        top_n = settings.MATCHING_TOP_N

    if donation.latitude is None or donation.longitude is None:
        logger.warning("Donation %s has no location, cannot match", donation.pk)
        return []

    nearby_ngos = get_nearby_users(
        lat=donation.latitude,
        lon=donation.longitude,
        radius_km=radius_km,
        role="ngo",
        verified_only=True,
    )

    if not nearby_ngos:
        return []

    scores: list[MatchScore] = []
    now = timezone.now()
    today = now.date()

    for ngo, dist in nearby_ngos:
        ms = MatchScore(
            ngo_id=ngo.pk,
            ngo_name=ngo.display_name,
            distance_km=dist,
        )

        # --- Distance score (30%) — exponential decay ---
        max_dist = radius_km
        ms.distance_score = max(0, 30.0 * (1 - (dist / max_dist) ** 0.5))
        ms.reasons.append(f"Distance: {dist:.1f} km")

        # --- Capacity score (20%) ---
        if ngo.capacity_servings_per_day:
            from logistics.models import Claim
            claimed_today = Claim.objects.filter(
                ngo=ngo,
                status__in=["accepted", "pending"],
                created_at__date=today,
            ).count()
            # Rough capacity usage
            capacity_used = claimed_today * 50  # estimate
            remaining = max(0, ngo.capacity_servings_per_day - capacity_used)
            if remaining >= donation.quantity_servings:
                ms.capacity_score = 20.0
                ms.reasons.append("Has capacity")
            elif remaining > 0:
                ms.capacity_score = 10.0
                ms.reasons.append("Partial capacity")
            else:
                ms.capacity_score = 0.0
                ms.reasons.append("At capacity")
        else:
            ms.capacity_score = 15.0  # Unknown capacity, assume ok
            ms.reasons.append("Capacity unknown")

        # --- Food type compatibility (15%) ---
        if ngo.accepts_veg_only and donation.food_type != "veg":
            ms.food_type_score = 0.0
            ms.reasons.append("Veg-only NGO, donation is non-veg")
        else:
            ms.food_type_score = 15.0
            ms.reasons.append("Food type compatible")

        # --- Reliability (20%) ---
        ms.reliability_score = (ngo.reliability_score / 5.0) * 20.0
        ms.reasons.append(f"Reliability: {ngo.reliability_score:.1f}/5")

        # --- Response rate (10%) ---
        from logistics.models import Claim
        total_claims = Claim.objects.filter(ngo=ngo).count()
        if total_claims > 0:
            accepted = Claim.objects.filter(ngo=ngo, status="accepted").count()
            rate = accepted / total_claims
            ms.response_rate_score = rate * 10.0
            ms.reasons.append(f"Response rate: {rate:.0%}")
        else:
            ms.response_rate_score = 5.0
            ms.reasons.append("New NGO, no history")

        # --- Urgency bonus (5%) ---
        if donation.is_urgent:
            ms.urgency_bonus = 5.0
            ms.reasons.append("Urgency bonus applied")

        # --- Total ---
        ms.total_score = (
            ms.distance_score
            + ms.capacity_score
            + ms.food_type_score
            + ms.reliability_score
            + ms.response_rate_score
            + ms.urgency_bonus
        )

        scores.append(ms)

    scores.sort(key=lambda s: s.total_score, reverse=True)
    return scores[:top_n]
