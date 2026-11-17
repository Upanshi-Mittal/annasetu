import pytest
from django.utils import timezone

from accounts.models import User
from donations.models import Donation
from logistics.models import Claim
from logistics.services import create_claim


@pytest.mark.django_db(transaction=True)
def test_double_claim_race_prevention():
    """
    Verify that when an accepted claim is created, a second claim on the same
    donation will fail to claim or raise an error, preserving the unique accepted claim invariant.
    """
    donor = User.objects.create_user(username="donor_race", role=User.Role.DONOR)
    ngo1 = User.objects.create_user(username="ngo_one", role=User.Role.NGO, is_verified=True, reliability_score=4.8)
    ngo2 = User.objects.create_user(username="ngo_two", role=User.Role.NGO, is_verified=True, reliability_score=4.8)

    now = timezone.now()
    donation = Donation.objects.create(
        donor=donor,
        title="100 Servings Biryani",
        food_type=Donation.FoodType.NONVEG,
        quantity_servings=100,
        pickup_address="Noida",
        pickup_from=now,
        safe_until=now + timezone.timedelta(hours=5),
        status=Donation.Status.POSTED,
    )

    # First NGO claims (auto-accepted because reliability >= 4.5)
    claim1, task1 = create_claim(donation, ngo1, servings_requested=100)
    assert claim1.status == Claim.Status.ACCEPTED
    donation.refresh_from_db()
    assert donation.status == Donation.Status.CLAIMED

    # Second NGO attempts to claim the same donation
    with pytest.raises(ValueError) as excinfo:
        create_claim(donation, ngo2, servings_requested=100)
    assert "not available for claiming" in str(excinfo.value) or "already has an accepted claim" in str(excinfo.value)

    # Exactly one accepted claim exists
    assert Claim.objects.filter(donation=donation, status=Claim.Status.ACCEPTED).count() == 1
