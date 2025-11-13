"""Tests for the find_user_by_email endpoint."""
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
from helpers.find_service import (
    assert_find_service_success,
    assert_find_service_invalid_auth,
    assert_find_service_missing_header,
    assert_find_service_missing_user_id,
)
from helpers.general_helper_functions import (create_x_users, create_service)
from p7.find_services.api import find_services_router

pytestmark = pytest.mark.usefixtures("django_db_setup")
#pytestmark = pytest.mark.django_db

@pytest.fixture(name="find_service_client_fixture", scope='module', autouse=True)
def find_service_client():
    """Fixture for creating a test client for the find_service endpoint.
    Returns:
        TestClient: A test client for the find_service endpoint.
    """
    return TestClient(find_services_router)

def test_create_user_success():
    """Create 3 users."""
    create_x_users(3)


def test_create_service_success():
    """Create 9 services (3 each for Dropbox, Google, OneDrive)."""
    for user_number in range(1, 3+1):  # 3 services
        for provider in ["DROPBOX", "GOOGLE", "ONEDRIVE"]:
            create_service(provider, user_number)

def test_find_service_success(find_service_client_fixture):
    """Test finding services successfully.
    params:
        find_service_client_fixture: Fixture for creating a test for the find_service endpoint.
    """
    for user_number in range(1, 3+1): # 3 users
        email = f"p7swtest{user_number}@gmail.com"
        assert_find_service_success(find_service_client_fixture, user_number, email)

def test_find_service_invalid_auth(find_service_client_fixture):
    """Test finding a service with invalid auth token.
    params:
        find_service_client_fixture: Fixture for creating a test for the find_service endpoint.
    """
    for user_number in range(1, 3+1): # 3 users
        assert_find_service_invalid_auth(find_service_client_fixture, user_number)

def test_find_service_missing_header(find_service_client_fixture):
    """Test finding a service with missing auth header.
    params:
        find_service_client_fixture: Fixture for creating a test for the find_service endpoint.
    """
    for user_number in range(1, 3+1): # 3 users

        assert_find_service_missing_header(find_service_client_fixture, user_number)

def test_find_service_missing_user_id(find_service_client_fixture):
    """Test finding a service with missing user_id parameter.
    params:
        find_service_client_fixture: Fixture for creating a test for the find_service endpoint.
    """
    assert_find_service_missing_user_id(find_service_client_fixture)
