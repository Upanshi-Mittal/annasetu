import pytest
from django.utils import timezone

from accounts.models import User
from certificates.models import Certificate
from certificates.views import generate_pdf_certificate
from donations.models import Donation
from logistics.models import Claim, DeliveryTask
from logistics.services import verify_qr_scan


@pytest.mark.django_db
def test_qr_signing_and_verification():
    donor = User.objects.create_user(username="donor_qr", role=User.Role.DONOR)
    ngo = User.objects.create_user(username="ngo_qr", role=User.Role.NGO)
    now = timezone.now()
    donation = Donation.objects.create(
        donor=donor,
        title="Food for QR test",
        food_type=Donation.FoodType.VEG,
        quantity_servings=40,
        pickup_address="Delhi",
        pickup_from=now,
        safe_until=now + timezone.timedelta(hours=4),
    )
    claim = Claim.objects.create(donation=donation, ngo=ngo, servings_requested=40)
    task = DeliveryTask.objects.create(donation=donation, claim=claim)

    # Valid token
    assert task.pickup_qr_token is not None
    verified_data = verify_qr_scan(task.pickup_qr_token)
    assert verified_data is not None
    assert "token" in verified_data

    # Tampered or invalid token
    tampered_token = task.pickup_qr_token + "tampered"
    assert verify_qr_scan(tampered_token) is None


@pytest.mark.django_db
def test_pdf_certificate_generation():
    donor = User.objects.create_user(
        username="donor_cert",
        role=User.Role.DONOR,
        organization_name="Taj Luxury Kitchens"
    )
    cert = Certificate.objects.create(
        donor=donor,
        cert_type=Certificate.CertType.PER_DONATION,
        total_servings=150,
        total_kg=60.0,
        co2_avoided_kg=150.0,
    )
    buffer = generate_pdf_certificate(cert)
    pdf_bytes = buffer.getvalue()
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1000
