"""
Logistics business logic — claims, delivery tasks, QR verification.
"""
from __future__ import annotations

import logging

from django.conf import settings
from django.core import signing
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


def create_claim(donation, ngo, servings_requested: int, note: str = ""):
    """
    Create a claim on a donation. Uses select_for_update to prevent double-claims.
    Auto-accepts if NGO reliability is above threshold.
    """
    from donations.models import Donation
    from donations.services import transition_donation
    from logistics.models import Claim
    from notifications.services import notify

    with transaction.atomic():
        # Lock the donation row
        donation = Donation.objects.select_for_update().get(pk=donation.pk)

        if donation.status != Donation.Status.POSTED:
            raise ValueError(f"Donation #{donation.pk} is not available for claiming (status: {donation.status})")

        # Check no existing accepted claim
        existing = Claim.objects.filter(
            donation=donation, status=Claim.Status.ACCEPTED
        ).exists()
        if existing:
            raise ValueError("This donation already has an accepted claim")

        claim = Claim.objects.create(
            donation=donation,
            ngo=ngo,
            servings_requested=servings_requested,
            note=note,
        )

        # Auto-accept if NGO reliability is high enough
        threshold = settings.AUTO_ACCEPT_RELIABILITY_THRESHOLD
        if ngo.reliability_score >= threshold:
            claim.status = Claim.Status.ACCEPTED
            claim.save(update_fields=["status", "updated_at"])
            transition_donation(donation, Donation.Status.CLAIMED, actor=ngo, note=f"Auto-accepted claim from {ngo.display_name}")

            # Create delivery task
            task = create_delivery_task(donation, claim)

            notify(
                user=donation.donor,
                notification_type="claim_accepted",
                title="Claim auto-accepted!",
                body=f'{ngo.display_name} has claimed your "{donation.title}" ({servings_requested} servings).',
                url=f"/donations/{donation.pk}/",
            )

            return claim, task
        else:
            # Notify donor to review claim
            notify(
                user=donation.donor,
                notification_type="claim_received",
                title="New claim on your donation",
                body=f'{ngo.display_name} wants to claim "{donation.title}" ({servings_requested} servings).',
                url=f"/donations/{donation.pk}/",
            )

            return claim, None


def accept_claim(claim, actor):
    """Accept a pending claim and transition the donation."""
    from donations.models import Donation
    from donations.services import transition_donation
    from logistics.models import Claim
    from notifications.services import notify

    with transaction.atomic():
        claim = Claim.objects.select_for_update().get(pk=claim.pk)

        if claim.status != Claim.Status.PENDING:
            raise ValueError(f"Claim #{claim.pk} is not pending")

        # Reject other pending claims
        Claim.objects.filter(
            donation=claim.donation, status=Claim.Status.PENDING,
        ).exclude(pk=claim.pk).update(status=Claim.Status.REJECTED)

        claim.status = Claim.Status.ACCEPTED
        claim.save(update_fields=["status", "updated_at"])

        transition_donation(
            claim.donation, Donation.Status.CLAIMED, actor=actor,
            note=f"Claim by {claim.ngo.display_name} accepted",
        )

        task = create_delivery_task(claim.donation, claim)

        notify(
            user=claim.ngo,
            notification_type="claim_accepted",
            title="Your claim was accepted!",
            body=f'Your claim on "{claim.donation.title}" has been accepted.',
            url=f"/logistics/tasks/{task.pk}/",
        )

        return task


def create_delivery_task(donation, claim):
    """Create a delivery task after a claim is accepted."""
    from logistics.models import DeliveryTask
    from matching.geo import get_nearby_users
    from notifications.services import notify

    task = DeliveryTask.objects.create(
        donation=donation,
        claim=claim,
    )

    # Alert nearby volunteers
    if donation.latitude and donation.longitude:
        nearby_volunteers = get_nearby_users(
            lat=donation.latitude,
            lon=donation.longitude,
            radius_km=settings.MATCHING_RADIUS_KM,
            role="volunteer",
        )
        for volunteer, dist in nearby_volunteers[:10]:
            notify(
                user=volunteer,
                notification_type="task_assigned",
                title="🚗 New pickup task nearby!",
                body=f'"{donation.title}" needs pickup ({dist:.1f} km away).',
                url=f"/logistics/tasks/{task.pk}/",
            )

    return task


def accept_task(task, volunteer):
    """Volunteer accepts a delivery task (atomic — first come, first served)."""
    from donations.models import Donation
    from donations.services import transition_donation
    from logistics.models import DeliveryTask
    from notifications.services import notify

    with transaction.atomic():
        task = DeliveryTask.objects.select_for_update().get(pk=task.pk)

        if task.status != DeliveryTask.Status.PENDING:
            raise ValueError("This task has already been assigned")

        task.volunteer = volunteer
        task.status = DeliveryTask.Status.ASSIGNED
        task.save(update_fields=["volunteer", "status", "updated_at"])

        transition_donation(
            task.donation, Donation.Status.ASSIGNED, actor=volunteer,
            note=f"Volunteer {volunteer.display_name} assigned",
        )

        # Notify donor and NGO
        for user in [task.donation.donor, task.claim.ngo]:
            notify(
                user=user,
                notification_type="task_assigned",
                title="Volunteer assigned!",
                body=f'{volunteer.display_name} will pick up "{task.donation.title}".',
                url=f"/logistics/tasks/{task.pk}/",
            )

    return task


def verify_qr_scan(token: str, expected_type: str = "pickup") -> dict | None:
    """
    Verify a QR token using Django signing.
    Returns the token data if valid, None if expired/invalid.
    """
    try:
        data = signing.loads(token, max_age=settings.QR_TOKEN_MAX_AGE)
        return data
    except signing.BadSignature:
        return None


def confirm_pickup(task, actor, lat: float | None = None, lon: float | None = None):
    """Confirm food pickup via QR scan."""
    from donations.models import Donation
    from donations.services import transition_donation
    from logistics.models import DeliveryTask, StatusEvent
    from notifications.services import broadcast_task_update, notify

    with transaction.atomic():
        task = DeliveryTask.objects.select_for_update().get(pk=task.pk)

        if task.status != DeliveryTask.Status.ASSIGNED:
            raise ValueError("Task is not in ASSIGNED state")

        # Verify food safety checklist exists
        if not hasattr(task, "safety_checklist"):
            raise ValueError("Food safety checklist must be completed before pickup")

        task.status = DeliveryTask.Status.PICKED_UP
        task.picked_up_at = timezone.now()
        task.save(update_fields=["status", "picked_up_at", "updated_at"])

        transition_donation(
            task.donation, Donation.Status.PICKED_UP, actor=actor,
            note="Picked up", lat=lat, lon=lon,
        )

        StatusEvent.objects.create(
            task=task,
            from_status=DeliveryTask.Status.ASSIGNED,
            to_status=DeliveryTask.Status.PICKED_UP,
            actor=actor,
            latitude=lat,
            longitude=lon,
        )

        broadcast_task_update(task.pk, {
            "status": "picked_up",
            "picked_up_at": task.picked_up_at.isoformat(),
        })

        notify(
            user=task.claim.ngo,
            notification_type="task_picked_up",
            title="Food picked up!",
            body=f'"{task.donation.title}" has been picked up and is on the way.',
            url=f"/logistics/tasks/{task.pk}/",
        )

    return task


def confirm_delivery(task, actor, lat: float | None = None, lon: float | None = None):
    """Confirm food delivery via QR scan."""
    from donations.models import Donation
    from donations.services import transition_donation
    from logistics.models import DeliveryTask, StatusEvent
    from notifications.services import broadcast_task_update, notify

    with transaction.atomic():
        task = DeliveryTask.objects.select_for_update().get(pk=task.pk)

        if task.status != DeliveryTask.Status.PICKED_UP:
            raise ValueError("Task is not in PICKED_UP state")

        task.status = DeliveryTask.Status.DELIVERED
        task.delivered_at = timezone.now()
        task.save(update_fields=["status", "delivered_at", "updated_at"])

        transition_donation(
            task.donation, Donation.Status.DELIVERED, actor=actor,
            note="Delivered", lat=lat, lon=lon,
        )

        StatusEvent.objects.create(
            task=task,
            from_status=DeliveryTask.Status.PICKED_UP,
            to_status=DeliveryTask.Status.DELIVERED,
            actor=actor,
            latitude=lat,
            longitude=lon,
        )

        broadcast_task_update(task.pk, {
            "status": "delivered",
            "delivered_at": task.delivered_at.isoformat(),
        })

        # Notify all parties
        for user in [task.donation.donor, task.claim.ngo]:
            notify(
                user=user,
                notification_type="task_delivered",
                title="🎉 Food delivered!",
                body=f'"{task.donation.title}" has been delivered successfully.',
                url=f"/logistics/tasks/{task.pk}/",
            )

        # Award points to volunteer
        _award_delivery_points(task)

    return task


def _award_delivery_points(task):
    """Award gamification points for a completed delivery."""
    from gamification.models import PointsLedger

    base_points = 10
    if task.donation.is_urgent:
        base_points = 20  # Double for urgent

    if task.distance_km and task.distance_km > 10:
        base_points += 5  # Bonus for long distance

    if task.volunteer:
        PointsLedger.objects.create(
            user=task.volunteer,
            points=base_points,
            source=PointsLedger.Source.DELIVERY if not task.donation.is_urgent else PointsLedger.Source.URGENT_DELIVERY,
            description=f'Delivered "{task.donation.title}"',
            task=task,
        )
