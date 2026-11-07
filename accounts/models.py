from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        DONOR = "donor", "Donor"
        NGO = "ngo", "NGO"
        VOLUNTEER = "volunteer", "Volunteer"

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.DONOR)
    phone = models.CharField(max_length=15, blank=True)
    organization_name = models.CharField(max_length=150, blank=True)
    address = models.TextField(blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)   
    verification_doc = models.FileField(upload_to="verification/", blank=True)
    reliability_score = models.FloatField(default=5.0)