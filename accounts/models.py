from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user with role-based access and profile fields."""

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

    # Extended profile fields
    avatar = models.ImageField(upload_to="avatars/", blank=True)
    capacity_servings_per_day = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Max servings this NGO can handle per day",
    )
    accepts_veg_only = models.BooleanField(default=False)
    service_radius_km = models.FloatField(
        default=10.0,
        help_text="Preferred service radius in km",
    )
    preferred_language = models.CharField(
        max_length=5, default="en",
        choices=[("en", "English"), ("hi", "Hindi")],
    )

    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["is_verified"]),
            models.Index(fields=["latitude", "longitude"]),
        ]

    @property
    def is_donor(self) -> bool:
        return self.role == self.Role.DONOR

    @property
    def is_ngo(self) -> bool:
        return self.role == self.Role.NGO

    @property
    def is_volunteer(self) -> bool:
        return self.role == self.Role.VOLUNTEER

    @property
    def display_name(self) -> str:
        if self.organization_name:
            return self.organization_name
        return self.get_full_name() or self.username

    @property
    def total_points(self) -> int:
        return self.points_ledger.aggregate(
            total=models.Sum("points")
        )["total"] or 0

    def __str__(self):
        return f"{self.display_name} ({self.get_role_display()})"
