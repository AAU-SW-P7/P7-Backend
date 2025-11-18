"""Tests for the create_service endpoint."""
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
from helpers.create_service import (
    assert_create_service_success,
    assert_create_service_invalid_auth,
    assert_create_service_missing_header,
    assert_create_service_missing_payload,
)
from helpers.general_helper_functions import create_x_users
from p7.create_service.api import create_service_router

pytestmark = pytest.mark.usefixtures("django_db_setup")
#pytestmark = pytest.mark.django_db

@pytest.fixture(name="service_client", scope='module', autouse=True)
def create_service_client():
    """Fixture for creating a test client for the create_service endpoint.
    Returns:
        TestClient: A test client for the create_service endpoint.
    """
    return TestClient(create_service_router)

def test_create_user_success():
    """Create 3 users."""
    create_x_users(3)

def test_create_service_success(service_client):
    """Test creating 9 services successfully (3 each for Dropbox, Google, OneDrive).
    params:
        service_client: Fixture for creating a test client for the create_service endpoint.
    """
    service_count = 0
    for service_number in range(1, 3+1):  # 3 services
        for provider in ["DROPBOX", "GOOGLE", "ONEDRIVE"]:
            payload = {
                "userId": os.getenv(f"TEST_USER_{provider}_ID_{service_number}"),
                "oauthType": os.getenv(f"TEST_USER_{provider}_OAUTHTYPE_{service_number}"),
                "oauthToken": os.getenv(f"TEST_USER_{provider}_OAUTHTOKEN_{service_number}"),
                "accessToken": os.getenv(f"TEST_USER_{provider}_ACCESSTOKEN_{service_number}"),
                "accessTokenExpiration": os.getenv(
                    f"TEST_USER_{provider}_ACCESSTOKENEXPIRATION_{service_number}"
                ),
                "refreshToken": os.getenv(f"TEST_USER_{provider}_REFRESHTOKEN_{service_number}"),
                "name": os.getenv(f"TEST_USER_{provider}_NAME_{service_number}"),
                "accountId": os.getenv(f"TEST_USER_{provider}_ACCOUNTID_{service_number}"),
                "email": os.getenv(f"TEST_USER_{provider}_EMAIL_{service_number}"),
                "scopeName": os.getenv(f"TEST_USER_{provider}_SCOPENAME_{service_number}"),
            }

            assert_create_service_success(service_client, payload, service_count)

            service_count += 1

def test_create_service_invalid_auth(service_client):
    """Test creating a service with invalid auth token.
    params:
        service_client: Fixture for creating a test client for the create_service endpoint.
    """
    service_count = 0
    for i in range(1, 3+1):  # 3 users
        for provider in ["DROPBOX", "GOOGLE", "ONEDRIVE"]:

            service_count += 1

            payload = {
                "userId": os.getenv(f"TEST_USER_{provider}_ID_{i}"),
                "oauthType": os.getenv(f"TEST_USER_{provider}_OAUTHTYPE_{i}"),
                "oauthToken": os.getenv(f"TEST_USER_{provider}_OAUTHTOKEN_{i}"),
                "accessToken": os.getenv(f"TEST_USER_{provider}_ACCESSTOKEN_{i}"),
                "accessTokenExpiration": os.getenv(
                    f"TEST_USER_{provider}_ACCESSTOKENEXPIRATION_{i}"
                ),
                "refreshToken": os.getenv(f"TEST_USER_{provider}_REFRESHTOKEN_{i}"),
                "name": os.getenv(f"TEST_USER_{provider}_NAME_{i}"),
                "accountId": os.getenv(f"TEST_USER_{provider}_ACCOUNTID_{i}"),
                "email": os.getenv(f"TEST_USER_{provider}_EMAIL_{i}"),
                "scopeName": os.getenv(f"TEST_USER_{provider}_SCOPENAME_{i}"),
            }

            assert_create_service_invalid_auth(service_client, payload)

def test_create_service_missing_header(service_client):
    """Test creating a service with missing auth header.
    params:
        service_client: Fixture for creating a test client for the create_service endpoint.
    """
    for i in range(1, 3+1):  # 3 users
        for provider in ["dropbox", "google", "onedrive"]:
            payload = {
                "userId": os.getenv(f"TEST_USER_{provider}_ID_{i}"),
                "oauthType": os.getenv(f"TEST_USER_{provider}_OAUTHTYPE_{i}"),
                "oauthToken": os.getenv(f"TEST_USER_{provider}_OAUTHTOKEN_{i}"),
                "accessToken": os.getenv(f"TEST_USER_{provider}_ACCESSTOKEN_{i}"),
                "accessTokenExpiration": os.getenv(
                    f"TEST_USER_{provider}_ACCESSTOKENEXPIRATION_{i}"
                ),
                "refreshToken": os.getenv(f"TEST_USER_{provider}_REFRESHTOKEN_{i}"),
                "name": os.getenv(f"TEST_USER_{provider}_NAME_{i}"),
                "accountId": os.getenv(f"TEST_USER_{provider}_ACCOUNTID_{i}"),
                "email": os.getenv(f"TEST_USER_{provider}_EMAIL_{i}"),
                "scopeName": os.getenv(f"TEST_USER_{provider}_SCOPENAME_{i}"),
            }

            assert_create_service_missing_header(service_client, payload)

def test_create_service_missing_payload(service_client):
    """Test creating a service with missing payload.
    params:
        service_client: Fixture for creating a test client for the create_service endpoint.
    """
    assert_create_service_missing_payload(service_client)
