from django.conf import settings
from django.db import models
from django.utils import timezone

class Donation(models.Model):
    class FoodType(models.TextChoices):
        VEG = "veg", "Vegetarian"
        NONVEG = "nonveg", "Non-vegetarian"

    class Status(models.TextChoices):
        POSTED = "posted", "Posted"
        CLAIMED = "claimed", "Claimed"
        ASSIGNED = "assigned", "Volunteer assigned"
        PICKED_UP = "picked_up", "Picked up"
        DELIVERED = "delivered", "Delivered"
        EXPIRED = "expired", "Expired"

    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="donations")
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
    safe_until = models.DateTimeField()          # expiry-aware listings
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.POSTED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_expired(self):
        return timezone.now() > self.safe_until

    @property
    def is_urgent(self):
        return (self.safe_until - timezone.now()).total_seconds() < 7200  # < 2 hours

    def __str__(self):
        return f"{self.title} ({self.quantity_servings} servings)"