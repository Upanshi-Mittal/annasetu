import pytest
from django.utils import timezone

from accounts.models import User
from donations.models import Donation
from donations.services import transition_donation
from logistics.models import StatusEvent


@pytest.mark.django_db
def test_donation_state_transitions():
    donor = User.objects.create_user(username="test_donor", role=User.Role.DONOR)
    now = timezone.now()
    donation = Donation.objects.create(
        donor=donor,
        title="50 Servings Dal Rice",
        food_type=Donation.FoodType.VEG,
        quantity_servings=50,
        pickup_address="Delhi",
        pickup_from=now,
        safe_until=now + timezone.timedelta(hours=4),
        status=Donation.Status.POSTED,
    )

    # Valid transition: POSTED -> CLAIMED
    transition_donation(donation, Donation.Status.CLAIMED, actor=donor)
    assert donation.status == Donation.Status.CLAIMED
    assert StatusEvent.objects.filter(donation=donation, to_status=Donation.Status.CLAIMED).exists()

    # Valid transition: CLAIMED -> ASSIGNED
    transition_donation(donation, Donation.Status.ASSIGNED, actor=donor)
    assert donation.status == Donation.Status.ASSIGNED

    # Invalid transition: ASSIGNED -> POSTED (not in allowed map)
    with pytest.raises(ValueError):
        transition_donation(donation, Donation.Status.POSTED, actor=donor)


@pytest.mark.django_db
def test_donation_urgent_and_expired_properties():
    donor = User.objects.create_user(username="prop_donor", role=User.Role.DONOR)
    now = timezone.now()

    # Urgent donation (expires in 1 hour)
    d_urgent = Donation.objects.create(
        donor=donor,
        title="Urgent Food",
        food_type=Donation.FoodType.VEG,
        quantity_servings=30,
        pickup_address="Delhi",
        pickup_from=now,
        safe_until=now + timezone.timedelta(hours=1),
        status=Donation.Status.POSTED,
    )
    assert d_urgent.is_urgent is True
    assert d_urgent.is_expired is False

    # Expired donation
    d_expired = Donation.objects.create(
        donor=donor,
        title="Expired Food",
        food_type=Donation.FoodType.VEG,
        quantity_servings=30,
        pickup_address="Delhi",
        pickup_from=now - timezone.timedelta(hours=5),
        safe_until=now - timezone.timedelta(hours=1),
        status=Donation.Status.POSTED,
    )
    assert d_expired.is_expired is True
    assert d_expired.is_urgent is False
