import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import User


@pytest.mark.django_db
def test_jwt_auth_and_donation_api():
    client = APIClient()
    User.objects.create_user(
        username="api_user",
        password="securepass123",
        role=User.Role.DONOR,
        is_verified=True,
    )

    # 1. Obtain JWT token
    token_url = reverse("token_obtain_pair")
    res = client.post(token_url, {"username": "api_user", "password": "securepass123"})
    assert res.status_code == 200
    access_token = res.data["access"]
    assert access_token is not None

    # 2. Authenticated request to /api/v1/users/me/
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    me_res = client.get("/api/v1/users/me/")
    assert me_res.status_code == 200
    assert me_res.data["username"] == "api_user"

    # 3. Create donation via API
    create_res = client.post("/api/v1/donations/", {
        "title": "API Food Rescue Batch",
        "food_type": "veg",
        "quantity_servings": 75,
        "pickup_address": "Bareilly Road",
        "pickup_from": "2026-11-17T14:00:00Z",
        "safe_until": "2026-11-17T20:00:00Z",
    })
    assert create_res.status_code == 201
    assert create_res.data["quantity_servings"] == 75

    # 4. Swagger Schema & UI
    schema_res = client.get("/api/v1/schema/")
    assert schema_res.status_code == 200
