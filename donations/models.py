from django.conf import settings
from django.db import models
from django.utils import timezone


class Donation(models.Model):
    """A food donation listing posted by a donor."""

    class FoodType(models.TextChoices):
        VEG = "veg", "Vegetarian"
        NONVEG = "nonveg", "Non-vegetarian"
        JAIN = "jain", "Jain"

    class Status(models.TextChoices):
        POSTED = "posted", "Posted"
        CLAIMED = "claimed", "Claimed"
        ASSIGNED = "assigned", "Volunteer assigned"
        PICKED_UP = "picked_up", "Picked up"
        DELIVERED = "delivered", "Delivered"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"

    # Allowed state transitions
    TRANSITIONS = {
        "posted": ["claimed", "expired", "cancelled"],
        "claimed": ["assigned", "posted", "expired", "cancelled"],
        "assigned": ["picked_up", "claimed", "expired", "cancelled"],
        "picked_up": ["delivered", "cancelled"],
        "delivered": [],
        "expired": [],
        "cancelled": [],
    }

    donor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="donations",
    )
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    food_type = models.CharField(max_length=10, choices=FoodType.choices)
    is_cooked = models.BooleanField(default=True)
    quantity_servings = models.PositiveIntegerField()
    photo = models.ImageField(upload_to="donations/", blank=True)
    pickup_address = models.TextField()
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    pickup_from = models.DateTimeField()
    safe_until = models.DateTimeField()
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.POSTED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["safe_until"]),
            models.Index(fields=["latitude", "longitude"]),
            models.Index(fields=["status", "safe_until"]),
            models.Index(fields=["donor", "status"]),
        ]

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.safe_until

    @property
    def is_urgent(self) -> bool:
        if self.is_expired:
            return False
        return (self.safe_until - timezone.now()).total_seconds() < 7200

    @property
    def time_left_seconds(self) -> int:
        delta = (self.safe_until - timezone.now()).total_seconds()
        return max(0, int(delta))

    @property
    def kg_estimate(self) -> float:
        """~0.4 kg per serving assumption."""
        return round(self.quantity_servings * settings.KG_PER_SERVING, 1)

    @property
    def co2_avoided(self) -> float:
        """CO₂ avoided if this food is rescued (kg CO₂e)."""
        return round(self.kg_estimate * settings.CO2_PER_KG_FOOD, 1)

    @property
    def meals_equivalent(self) -> int:
        return self.quantity_servings

    def can_transition_to(self, new_status: str) -> bool:
        return new_status in self.TRANSITIONS.get(self.status, [])

    def __str__(self):
        return f"{self.title} ({self.quantity_servings} servings)"
