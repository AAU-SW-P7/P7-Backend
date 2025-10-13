import os
import sys
from pathlib import Path

# Make the local backend package importable so `from p7...` works under pytest
repo_backend = Path(__file__).resolve().parents[1]  # backend/
sys.path.insert(0, str(repo_backend))
# Make the backend/test dir importable so you can use test_settings.py directly
sys.path.insert(0, str(repo_backend / "test"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_settings")

import django
django.setup()

import pytest
from ninja.testing import TestClient
from p7.create_user.api import create_user_router
from repository.models import User

# Use the test settings module instead of manual configure

@pytest.fixture
def client():
    return TestClient(create_user_router)

def test_create_user_success(client):
    # Get initial user count
    initial_count = User.objects.count()
    
    response = client.post("/", headers={"x-internal-auth": os.getenv("INTERNAL_API_KEY")})
    
    data = response.json()
    
    assert response.status_code == 200
    assert "id" in data
    assert type(data["id"]) is int
    
    # Assert that a new user was created in the database
    assert User.objects.count() == initial_count + 1
    
    # Assert that the user with the returned ID actually exists
    created_user = User.objects.get(id=data["id"])
    assert created_user is not None
    assert created_user.id == data["id"]
    

"""
def test_create_user_invalid_auth(mocker, client):
    # Mock internal auth validation to return error response
    mocker.patch("p7.create_user.api.validate_internal_auth", return_value={"error": "invalid auth"})
    # Ensure save_user is not called when auth fails
    mock_save = mocker.patch("p7.create_user.api.save_user", side_effect=AssertionError("should not be called"))

    headers = {"x-internal-auth": "invalid_token"}
    response = client.post("/", headers=headers, json={})
    assert response.status_code == 200
    assert response.json() == {"error": "invalid auth"}

def test_create_user_missing_header_returns_422(mocker, client):
    # Missing required header should yield 422
    mocker.patch("p7.create_user.api.validate_internal_auth", return_value=None)
    response = client.post("/", json={})  # no header
    assert response.status_code == 422
"""