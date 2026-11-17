import pytest
from django.utils import timezone

from accounts.models import User
from donations.models import Donation
from matching.geo import haversine_distance
from matching.services import compute_match_scores


def test_haversine_distance():
    # Distance between Connaught Place (28.6304, 77.2177) and Noida Sec 62 (28.6280, 77.3649) ~ 14.4 km
    dist = haversine_distance(28.6304, 77.2177, 28.6280, 77.3649)
    assert 13.0 <= dist <= 16.0

    # Same location = 0 distance
    assert haversine_distance(28.0, 77.0, 28.0, 77.0) == 0.0


@pytest.mark.django_db
def test_matching_score_calculation():
    donor = User.objects.create_user(
        username="donor_match", role=User.Role.DONOR,
        latitude=28.6139, longitude=77.2090
    )
    # Nearby compatible NGO
    ngo_close = User.objects.create_user(
        username="ngo_close", role=User.Role.NGO,
        organization_name="Close Food Kitchen",
        is_verified=True,
        latitude=28.6200, longitude=77.2150,
        capacity_servings_per_day=300,
        accepts_veg_only=False,
        reliability_score=4.9,
    )
    # Farther veg-only NGO
    User.objects.create_user(
        username="ngo_far", role=User.Role.NGO,
        organization_name="Far Veg Kitchen",
        is_verified=True,
        latitude=28.7500, longitude=77.1000,
        capacity_servings_per_day=50,
        accepts_veg_only=True,
        reliability_score=3.5,
    )

    now = timezone.now()
    donation = Donation.objects.create(
        donor=donor,
        title="50 Servings Chicken Rice",
        food_type=Donation.FoodType.NONVEG,
        quantity_servings=50,
        pickup_address="Delhi",
        latitude=28.6139,
        longitude=77.2090,
        pickup_from=now,
        safe_until=now + timezone.timedelta(hours=3),
        status=Donation.Status.POSTED,
    )

    scores = compute_match_scores(donation, radius_km=30, top_n=5)
    assert len(scores) >= 1
    top = scores[0]
    assert top.ngo_id == ngo_close.id
    assert top.distance_score > 0
    assert top.capacity_score > 0
    assert len(top.reasons) > 0
