"""Tests for saving files from various services."""
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
from helpers.create_user import (
    assert_create_user_success,
    assert_create_user_invalid_auth,
    assert_create_user_missing_header,
)
from helpers.create_service import (
    assert_create_service_success,
    assert_create_service_invalid_auth,
    assert_create_service_missing_header,
    assert_create_service_missing_payload,
)
from helpers.save_file import (
    assert_save_file_success,
    assert_save_file_invalid_auth,
    assert_save_file_missing_header,
    assert_save_file_missing_user_id,
)
from p7.get_dropbox_files.api import fetch_dropbox_files_router
from p7.get_google_drive_files.api import fetch_google_drive_files_router
from p7.get_onedrive_files.api import fetch_onedrive_files_router
from p7.create_user.api import create_user_router
from p7.create_service.api import create_service_router

pytestmark = pytest.mark.usefixtures("django_db_setup")
#pytestmark = pytest.mark.django_db

@pytest.fixture(name="user_client", scope='module', autouse=True)
def create_user_client():
    """Fixture for creating a test client for the create_user endpoint.
     Returns:
         TestClient: A test client for the create_user endpoint.
     """
    return TestClient(create_user_router)

@pytest.fixture(name="service_client", scope='module', autouse=True)
def create_service_client():
    """Fixture for creating a test client for the create_service endpoint.
    Returns:
        TestClient: A test client for the create_service endpoint.
    """
    return TestClient(create_service_router)

@pytest.fixture(name="save_dropbox_file_client_fixture", scope='module', autouse=True)
def save_dropbox_file_client():
    """Fixture for creating a test client for the save_file endpoint.
    Returns:
        TestClient: A test client for the save_file endpoint.
    """
    return TestClient(fetch_dropbox_files_router)

@pytest.fixture(name="save_google_drive_file_client_fixture", scope='module', autouse=True)
def save_google_drive_file_client():
    """Fixture for creating a test client for the save_file endpoint.
    Returns:
        TestClient: A test client for the save_file endpoint.
    """
    return TestClient(fetch_google_drive_files_router)

@pytest.fixture(name="save_onedrive_file_client_fixture", scope='module', autouse=True)
def save_onedrive_file_client():
    """Fixture for creating a test client for the save_file endpoint.
    Returns:
        TestClient: A test client for the save_file endpoint.
    """
    return TestClient(fetch_onedrive_files_router)

def test_create_user_success(user_client):
    """Test creating 3 users successfully.
    params:
        user_client: Fixture for creating a test client for the create_user endpoint.
    """
    for user_number in range(1, 3+1):  # 3 users
        assert_create_user_success(user_client, user_number)

def test_create_user_invalid_auth(user_client):
    """Test creating a user with invalid auth token.
    params:
        user_client: Fixture for creating a test client for the create_user endpoint.
    """
    assert_create_user_invalid_auth(user_client)

def test_create_user_missing_header(user_client):
    """Test creating a user with missing auth header.
    params:
        user_client: Fixture for creating a test client for the create_user endpoint.
    """
    assert_create_user_missing_header(user_client)

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


def test_save_dropbox_file_success(save_dropbox_file_client_fixture):
    """Test saving a Dropbox file."""

    for user_number in range(1, 3+1):  # 3 users

        assert_save_file_success(save_dropbox_file_client_fixture, user_number, 'dropbox')

def test_save_dropbox_file_invalid_auth(save_dropbox_file_client_fixture):
    """Test saving a Dropbox file."""

    for user_number in range(1, 3+1):  # 3 users

        assert_save_file_invalid_auth(save_dropbox_file_client_fixture, user_number)

def test_save_dropbox_file_missing_header(save_dropbox_file_client_fixture):
    """Test saving a Dropbox file."""

    for user_number in range(1, 3+1):  # 3 users

        assert_save_file_missing_header(save_dropbox_file_client_fixture, user_number)

def test_save_dropbox_file_missing_user_id(save_dropbox_file_client_fixture):
    """Test saving a Dropbox file."""

    assert_save_file_missing_user_id(save_dropbox_file_client_fixture)

def test_save_google_drive_file_success(save_google_drive_file_client_fixture):
    """Test saving a Google Drive file."""

    for user_number in range(1, 3+1):  # 3 users

        assert_save_file_success(save_google_drive_file_client_fixture, user_number, 'google')

def test_save_google_drive_file_invalid_auth(save_google_drive_file_client_fixture):
    """Test saving a Google Drive file."""

    for user_number in range(1, 3+1):  # 3 users

        assert_save_file_invalid_auth(save_google_drive_file_client_fixture, user_number)

def test_save_google_drive_file_missing_header(save_google_drive_file_client_fixture):
    """Test saving a Google Drive file."""

    for user_number in range(1, 3+1):  # 3 users

        assert_save_file_missing_header(save_google_drive_file_client_fixture, user_number)

def test_save_google_drive_file_missing_user_id(save_google_drive_file_client_fixture):
    """Test saving a Google Drive file."""

    assert_save_file_missing_user_id(save_google_drive_file_client_fixture)

def test_save_onedrive_file_success(save_onedrive_file_client_fixture):
    """Test saving a OneDrive file."""

    for user_number in range(1, 3+1):  # 3 users

        assert_save_file_success(
            save_onedrive_file_client_fixture,
            user_number,
            'onedrive',
        )

def test_save_onedrive_file_invalid_auth(save_onedrive_file_client_fixture):
    """Test saving a OneDrive file."""

    for user_number in range(1, 3+1):  # 3 users

        assert_save_file_invalid_auth(save_onedrive_file_client_fixture, user_number)

def test_save_onedrive_file_missing_header(save_onedrive_file_client_fixture):
    """Test saving a OneDrive file."""

    for user_number in range(1, 3+1):  # 3 users

        assert_save_file_missing_header(save_onedrive_file_client_fixture, user_number)

def test_save_onedrive_file_missing_user_id(save_onedrive_file_client_fixture):
    """Test saving a OneDrive file."""

    assert_save_file_missing_user_id(save_onedrive_file_client_fixture)
