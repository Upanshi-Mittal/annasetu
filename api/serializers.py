from rest_framework import serializers

from accounts.models import User
from certificates.models import Certificate
from donations.models import Donation
from gamification.models import Rating
from logistics.models import Claim, DeliveryTask, StatusEvent
from notifications.models import Notification


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'role', 'phone', 'organization_name',
            'address', 'latitude', 'longitude', 'is_verified', 'reliability_score',
            'capacity_servings_per_day', 'accepts_veg_only', 'service_radius_km',
            'preferred_language', 'total_points'
        ]
        read_only_fields = ['id', 'is_verified', 'reliability_score', 'total_points']


class DonationSerializer(serializers.ModelSerializer):
    donor_name = serializers.ReadOnlyField(source='donor.display_name')
    is_urgent = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    kg_estimate = serializers.ReadOnlyField()
    co2_avoided = serializers.ReadOnlyField()

    class Meta:
        model = Donation
        fields = [
            'id', 'donor', 'donor_name', 'title', 'description', 'food_type',
            'is_cooked', 'quantity_servings', 'photo', 'pickup_address',
            'latitude', 'longitude', 'pickup_from', 'safe_until', 'status',
            'is_urgent', 'is_expired', 'kg_estimate', 'co2_avoided',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'donor', 'status', 'created_at', 'updated_at']


class ClaimSerializer(serializers.ModelSerializer):
    ngo_name = serializers.ReadOnlyField(source='ngo.display_name')

    class Meta:
        model = Claim
        fields = [
            'id', 'donation', 'ngo', 'ngo_name', 'status',
            'servings_requested', 'note', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'ngo', 'status', 'created_at', 'updated_at']


class DeliveryTaskSerializer(serializers.ModelSerializer):
    volunteer_name = serializers.ReadOnlyField(source='volunteer.display_name')
    donation_title = serializers.ReadOnlyField(source='donation.title')

    class Meta:
        model = DeliveryTask
        fields = [
            'id', 'donation', 'donation_title', 'claim', 'volunteer',
            'volunteer_name', 'status', 'picked_up_at', 'delivered_at',
            'distance_km', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'picked_up_at', 'delivered_at', 'created_at', 'updated_at']


class StatusEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.ReadOnlyField(source='actor.display_name')

    class Meta:
        model = StatusEvent
        fields = [
            'id', 'donation', 'task', 'from_status', 'to_status',
            'actor', 'actor_name', 'timestamp', 'note', 'latitude', 'longitude'
        ]
        read_only_fields = ['id', 'timestamp']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'type', 'title', 'body', 'url', 'is_read', 'created_at']
        read_only_fields = ['id', 'created_at']


class RatingSerializer(serializers.ModelSerializer):
    from_user_name = serializers.ReadOnlyField(source='from_user.display_name')
    to_user_name = serializers.ReadOnlyField(source='to_user.display_name')

    class Meta:
        model = Rating
        fields = ['id', 'from_user', 'from_user_name', 'to_user', 'to_user_name', 'task', 'score', 'comment', 'created_at']
        read_only_fields = ['id', 'from_user', 'created_at']


class CertificateSerializer(serializers.ModelSerializer):
    donor_name = serializers.ReadOnlyField(source='donor.display_name')

    class Meta:
        model = Certificate
        fields = [
            'id', 'donor', 'donor_name', 'cert_type', 'serial_number',
            'donation', 'period_start', 'period_end', 'total_servings',
            'total_kg', 'co2_avoided_kg', 'pdf_file', 'created_at'
        ]
        read_only_fields = ['id', 'serial_number', 'pdf_file', 'created_at']
