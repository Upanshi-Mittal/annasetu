from django.conf import settings
from django.db import models


class Notification(models.Model):
    """In-app notification for a user."""
    class Type(models.TextChoices):
        DONATION_NEW = 'donation_new', 'New donation nearby'
        CLAIM_RECEIVED = 'claim_received', 'Claim received'
        CLAIM_ACCEPTED = 'claim_accepted', 'Claim accepted'
        CLAIM_REJECTED = 'claim_rejected', 'Claim rejected'
        TASK_ASSIGNED = 'task_assigned', 'Task assigned'
        TASK_PICKED_UP = 'task_picked_up', 'Picked up'
        TASK_DELIVERED = 'task_delivered', 'Delivered'
        DONATION_EXPIRING = 'donation_expiring', 'Donation expiring soon'
        DONATION_EXPIRED = 'donation_expired', 'Donation expired'
        VERIFICATION = 'verification', 'Verification update'
        BADGE_EARNED = 'badge_earned', 'Badge earned'
        RATING_RECEIVED = 'rating_received', 'Rating received'
        SYSTEM = 'system', 'System message'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=30, choices=Type.choices, default=Type.SYSTEM)
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    url = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f'{self.title} → {self.user}'
