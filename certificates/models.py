import uuid

from django.conf import settings
from django.db import models


class Certificate(models.Model):
    """Donor certificate for CSR reporting."""
    class CertType(models.TextChoices):
        MONTHLY = 'monthly', 'Monthly summary'
        PER_DONATION = 'per_donation', 'Per donation'

    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certificates')
    cert_type = models.CharField(max_length=15, choices=CertType.choices)
    serial_number = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    donation = models.ForeignKey(
        'donations.Donation', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='certificates',
    )
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    total_servings = models.PositiveIntegerField(default=0)
    total_kg = models.FloatField(default=0)
    co2_avoided_kg = models.FloatField(default=0)
    pdf_file = models.FileField(upload_to='certificates/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Certificate {self.serial_number} for {self.donor}'
