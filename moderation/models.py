from django.conf import settings
from django.db import models


class Report(models.Model):
    """User-submitted report for abuse/fraud moderation."""
    class Reason(models.TextChoices):
        SPAM = 'spam', 'Spam or fake listing'
        UNSAFE_FOOD = 'unsafe_food', 'Unsafe food'
        NO_SHOW = 'no_show', 'No-show'
        HARASSMENT = 'harassment', 'Harassment'
        FRAUD = 'fraud', 'Fraud'
        OTHER = 'other', 'Other'

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        UNDER_REVIEW = 'under_review', 'Under review'
        RESOLVED = 'resolved', 'Resolved'
        DISMISSED = 'dismissed', 'Dismissed'

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports_filed',
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='reports_against', null=True, blank=True,
    )
    target_donation = models.ForeignKey(
        'donations.Donation', on_delete=models.CASCADE,
        related_name='reports', null=True, blank=True,
    )
    reason = models.CharField(max_length=20, choices=Reason.choices)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    resolution = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reports_resolved',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
        ]

    def __str__(self):
        target = self.target_user or self.target_donation
        return f'Report #{self.pk}: {self.reason} against {target}'
