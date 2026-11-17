import uuid

from django.conf import settings
from django.core import signing
from django.db import models
from django.utils import timezone


class Claim(models.Model):
    """An NGO's claim on a donation."""
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'
        CANCELLED = 'cancelled', 'Cancelled'

    donation = models.ForeignKey('donations.Donation', on_delete=models.CASCADE, related_name='claims')
    ngo = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='claims_made')
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    servings_requested = models.PositiveIntegerField()
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['donation', 'status']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['donation'],
                condition=models.Q(status='accepted'),
                name='unique_accepted_claim_per_donation',
            )
        ]

    def __str__(self):
        return f'Claim by {self.ngo} on {self.donation} ({self.status})'


def _generate_qr_token():
    return signing.dumps({'token': uuid.uuid4().hex, 'ts': timezone.now().isoformat()})


class DeliveryTask(models.Model):
    """Tracks the pickup-to-delivery lifecycle."""
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending volunteer'
        ASSIGNED = 'assigned', 'Volunteer assigned'
        PICKED_UP = 'picked_up', 'Picked up'
        DELIVERED = 'delivered', 'Delivered'
        FAILED = 'failed', 'Failed'

    donation = models.ForeignKey('donations.Donation', on_delete=models.CASCADE, related_name='tasks')
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name='tasks')
    volunteer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='delivery_tasks',
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    pickup_qr_token = models.TextField(default=_generate_qr_token)
    delivery_qr_token = models.TextField(default=_generate_qr_token)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    distance_km = models.FloatField(null=True, blank=True)
    pickup_photo = models.ImageField(upload_to='task_photos/pickup/', blank=True)
    delivery_photo = models.ImageField(upload_to='task_photos/delivery/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['volunteer', 'status']),
        ]

    def __str__(self):
        return f'Task #{self.pk} — {self.donation.title} ({self.status})'


class StatusEvent(models.Model):
    """Immutable audit log for donation/task status changes."""
    donation = models.ForeignKey(
        'donations.Donation', on_delete=models.CASCADE,
        related_name='status_events', null=True, blank=True,
    )
    task = models.ForeignKey(
        DeliveryTask, on_delete=models.CASCADE,
        related_name='status_events', null=True, blank=True,
    )
    from_status = models.CharField(max_length=20)
    to_status = models.CharField(max_length=20)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['donation', 'timestamp']),
            models.Index(fields=['task', 'timestamp']),
        ]

    def __str__(self):
        return f'{self.from_status} → {self.to_status} at {self.timestamp}'


class FoodSafetyChecklist(models.Model):
    """Completed by volunteer at pickup to verify food safety."""
    task = models.OneToOneField(DeliveryTask, on_delete=models.CASCADE, related_name='safety_checklist')
    temperature_ok = models.BooleanField(default=False)
    packaging_ok = models.BooleanField(default=False)
    smell_ok = models.BooleanField(default=False)
    within_safe_time = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
    )
    completed_at = models.DateTimeField(auto_now_add=True)

    def is_all_ok(self):
        return all([self.temperature_ok, self.packaging_ok, self.smell_ok, self.within_safe_time])

    def __str__(self):
        status = 'PASS' if self.is_all_ok() else 'ISSUES'
        return f'Safety check for Task #{self.task_id}: {status}'
