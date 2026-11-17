from django.conf import settings
from django.db import models


class Badge(models.Model):
    """Achievement badge definition."""
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='award', help_text='Lucide icon name')
    color = models.CharField(max_length=7, default='#16A34A')
    criteria_type = models.CharField(max_length=50, help_text='e.g. deliveries_count, meals_rescued')
    criteria_value = models.IntegerField(default=1)
    points_reward = models.IntegerField(default=10)

    class Meta:
        ordering = ['criteria_value']

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    """Awarded badge instance."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='awards')
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'badge']
        ordering = ['-earned_at']

    def __str__(self):
        return f'{self.user} earned {self.badge}'


class PointsLedger(models.Model):
    """Points transaction log for gamification."""
    class Source(models.TextChoices):
        DELIVERY = 'delivery', 'Delivery completed'
        URGENT_DELIVERY = 'urgent_delivery', 'Urgent delivery'
        RATING_BONUS = 'rating_bonus', 'Rating bonus'
        BADGE_REWARD = 'badge_reward', 'Badge reward'
        STREAK = 'streak', 'Streak bonus'
        DONATION = 'donation', 'Donation posted'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='points_ledger')
    points = models.IntegerField()
    source = models.CharField(max_length=20, choices=Source.choices)
    description = models.CharField(max_length=200, blank=True)
    task = models.ForeignKey(
        'logistics.DeliveryTask', on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user}: +{self.points} ({self.source})'


class Rating(models.Model):
    """Post-delivery rating between users."""
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ratings_given',
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ratings_received',
    )
    task = models.ForeignKey(
        'logistics.DeliveryTask', on_delete=models.CASCADE, related_name='ratings',
    )
    score = models.PositiveSmallIntegerField()  # 1-5
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['from_user', 'task']
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.from_user} → {self.to_user}: {self.score}★'
