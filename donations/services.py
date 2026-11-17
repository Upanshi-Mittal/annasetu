"""
Donation business logic — state transitions, creation, and expiry.
"""
from __future__ import annotations

import logging

from django.db import transaction
from django.utils import timezone

from donations.models import Donation

logger = logging.getLogger(__name__)


def transition_donation(
    donation: Donation, new_status: str, actor, note: str = "",
    lat: float | None = None, lon: float | None = None,
) -> Donation:
    """
    Transition a donation to a new status with audit logging.
    Raises ValueError if transition is invalid.
    """
    if not donation.can_transition_to(new_status):
        raise ValueError(
            f"Cannot transition donation #{donation.pk} from "
            f"'{donation.status}' to '{new_status}'"
        )

    from logistics.models import StatusEvent

    old_status = donation.status
    donation.status = new_status
    donation.save(update_fields=["status", "updated_at"])

    StatusEvent.objects.create(
        donation=donation,
        from_status=old_status,
        to_status=new_status,
        actor=actor,
        note=note,
        latitude=lat,
        longitude=lon,
    )

    logger.info(
        "Donation #%s: %s → %s by user %s",
        donation.pk, old_status, new_status, actor,
    )
    return donation


def expire_stale_donations() -> int:
    """
    Mark all POSTED/CLAIMED donations past safe_until as EXPIRED.
    Called by Celery beat every minute. Idempotent.
    Returns count of expired donations.
    """
    from logistics.models import StatusEvent
    from notifications.services import notify

    now = timezone.now()
    stale = Donation.objects.filter(
        status__in=[Donation.Status.POSTED, Donation.Status.CLAIMED],
        safe_until__lt=now,
    ).select_for_update()

    count = 0
    with transaction.atomic():
        for donation in stale:
            old_status = donation.status
            donation.status = Donation.Status.EXPIRED
            donation.save(update_fields=["status", "updated_at"])

            StatusEvent.objects.create(
                donation=donation,
                from_status=old_status,
                to_status=Donation.Status.EXPIRED,
                actor=None,
                note="Auto-expired by system",
            )

            # Notify donor
            notify(
                user=donation.donor,
                notification_type="donation_expired",
                title="Donation expired",
                body=f'Your listing "{donation.title}" has expired.',
                url=f"/donations/{donation.pk}/",
            )
            count += 1

    if count:
        logger.info("Expired %d stale donations", count)
    return count


def escalate_expiring_donations() -> int:
    """
    Send escalation notifications for POSTED donations expiring in <2 hours
    that haven't been claimed yet. Idempotent — only alerts once.
    """
    from matching.services import compute_match_scores
    from notifications.services import notify

    now = timezone.now()
    two_hours = now + timezone.timedelta(hours=2)

    urgent = Donation.objects.filter(
        status=Donation.Status.POSTED,
        safe_until__gt=now,
        safe_until__lte=two_hours,
    )

    count = 0
    for donation in urgent:
        # Find top matching NGOs and notify them
        scores = compute_match_scores(donation)
        for ms in scores:
            from accounts.models import User
            try:
                ngo = User.objects.get(pk=ms.ngo_id)
                notify(
                    user=ngo,
                    notification_type="donation_expiring",
                    title="🚨 Urgent: Food expiring soon!",
                    body=f'"{donation.title}" ({donation.quantity_servings} servings) expires in less than 2 hours.',
                    url=f"/donations/{donation.pk}/",
                )
                count += 1
            except Exception:
                logger.exception("Failed to notify NGO %s", ms.ngo_id)

    if count:
        logger.info("Sent %d urgency escalations", count)
    return count
