"""Tests for the fetch service endpoints."""
import os
import sys
from pathlib import Path
import pytest

# Make the local backend package importable so `from p7...` works under pytest
repo_backend = Path(__file__).resolve().parents[1]  # backend/
sys.path.insert(0, str(repo_backend))
# Make the backend/test dir importable so you can use test_settings.py directly
sys.path.insert(0, str(repo_backend / "test"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_settings")

import django
django.setup()

from ninja.testing import TestClient
from helpers.create_user import (
    assert_create_user_success,
    assert_create_user_invalid_auth,
    assert_create_user_missing_header,
)
from helpers.create_service import (
    assert_create_service_invalid_auth,
    assert_create_service_missing_header,
    assert_create_service_missing_payload,
)
from helpers.fetch_service import (
    assert_fetch_dropbox_files_success,
    assert_fetch_dropbox_files_invalid_auth,
    assert_fetch_dropbox_files_missing_header,
    assert_fetch_dropbox_files_missing_userid,
    assert_fetch_google_files_success,
    assert_fetch_google_files_invalid_auth,
    assert_fetch_google_files_missing_header,
    assert_fetch_google_files_missing_userid,
    assert_fetch_onedrive_files_success,
    assert_fetch_onedrive_files_invalid_auth,
    assert_fetch_onedrive_files_missing_header,
    assert_fetch_onedrive_files_missing_userid,
)
from p7.create_user.api import create_user_router
from p7.create_service.api import create_service_router
from p7.get_dropbox_files.api import fetch_dropbox_files_router
from p7.get_google_drive_files.api import fetch_google_drive_files_router
from p7.get_onedrive_files.api import fetch_onedrive_files_router
from test.helpers.sync_files import create_service

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

@pytest.fixture(name="fetch_dropbox_files_client", scope='module', autouse=True)
def create_fetch_dropbox_files_client():
    """Fixture for creating a test client for the fetch_dropbox_files endpoint.
    Returns:
        TestClient: A test client for the fetch_dropbox_files endpoint.
    """
    return TestClient(fetch_dropbox_files_router)

@pytest.fixture(name="fetch_google_files_client", scope='module', autouse=True)
def create_fetch_google_files_client():
    """Fixture for creating a test client for the fetch_google_files endpoint.
    Returns:
        TestClient: A test client for the fetch_google_files endpoint.
    """
    return TestClient(fetch_google_drive_files_router)

@pytest.fixture(name="fetch_onedrive_files_client", scope='module', autouse=True)
def create_fetch_onedrive_files_client():
    """Fixture for creating a test client for the fetch_onedrive_files endpoint.
    Returns:
        TestClient: A test client for the fetch_onedrive_files endpoint.
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
    """Test creating a user with missing headers.
    params:
        user_client: Fixture for creating a test client for the create_user endpoint.
    """
    assert_create_user_missing_header(user_client)

def test_create_service_success():
    """Test creating 9 services successfully (3 each for Dropbox, Google, OneDrive).
    """
    for service_number in range(1, 3+1):  # 3 services
        for provider in ["DROPBOX", "GOOGLE", "ONEDRIVE"]:
            create_service(provider, service_number)

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
    for user_number in range(1, 3+1):  # 3 users
        for provider in ["DROPBOX", "GOOGLE", "ONEDRIVE"]:
            payload = {
                "userId": os.getenv(f"TEST_USER_{provider}_ID_{user_number}"),
                "oauthType": os.getenv(f"TEST_USER_{provider}_OAUTHTYPE_{user_number}"),
                "oauthToken": os.getenv(f"TEST_USER_{provider}_OAUTHTOKEN_{user_number}"),
                "accessToken": os.getenv(f"TEST_USER_{provider}_ACCESSTOKEN_{user_number}"),
                "accessTokenExpiration": os.getenv(
                    f"TEST_USER_{provider}_ACCESSTOKENEXPIRATION_{user_number}"
                ),
                "refreshToken": os.getenv(f"TEST_USER_{provider}_REFRESHTOKEN_{user_number}"),
                "name": os.getenv(f"TEST_USER_{provider}_NAME_{user_number}"),
                "accountId": os.getenv(f"TEST_USER_{provider}_ACCOUNTID_{user_number}"),
                "email": os.getenv(f"TEST_USER_{provider}_EMAIL_{user_number}"),
                "scopeName": os.getenv(f"TEST_USER_{provider}_SCOPENAME_{user_number}"),
            }

            assert_create_service_missing_header(service_client, payload)

def test_create_service_missing_payload(service_client):
    """Test creating a service with missing payload.
    params:
        service_client:
            Fixture for creating a test client for the create_service endpoint.
    """

    assert_create_service_missing_payload(service_client)

def test_fetch_dropbox_files_success(fetch_dropbox_files_client):
    """Test fetching Dropbox files successfully for 3 users.
    params:
        fetch_dropbox_files_client:
            Fixture for creating a test client for the fetch_dropbox_files endpoint.
    """
    for user_number in range(1, 3+1):  # 3 users

        assert_fetch_dropbox_files_success(fetch_dropbox_files_client, user_number, "dropbox")

def test_fetch_dropbox_files_invalid_auth(fetch_dropbox_files_client):
    """Test fetching Dropbox files with invalid auth token.
    params:
        fetch_dropbox_files_client:
            Fixture for creating a test client for the fetch_dropbox_files endpoint.
    """
    for user_number in range(1, 3+1):  # 3 users

        assert_fetch_dropbox_files_invalid_auth(fetch_dropbox_files_client, user_number)

def test_fetch_dropbox_files_missing_header(fetch_dropbox_files_client):
    """Test fetching Dropbox files with missing auth header.
    params:
        fetch_dropbox_files_client:
            Fixture for creating a test client for the fetch_dropbox_files endpoint.
    """
    for user_number in range(1, 3+1):  # 3 users

        assert_fetch_dropbox_files_missing_header(fetch_dropbox_files_client, user_number)

def test_fetch_dropbox_files_missing_userid(fetch_dropbox_files_client):
    """Test fetching Dropbox files with missing userId query parameter.
    params:
        fetch_dropbox_files_client: 
            Fixture for creating a test client for the fetch_dropbox_files endpoint.
    """
    for _ in range(1, 3+1):  # 3 users

        assert_fetch_dropbox_files_missing_userid(fetch_dropbox_files_client)

def test_fetch_google_files_success(fetch_google_files_client):
    """Test fetching Google files successfully for 3 users.
    params:
        fetch_google_files_client: 
            Fixture for creating a test client for the fetch_google_files endpoint.
    """
    for user_number in range(1, 3+1):  # 3 users

        assert_fetch_google_files_success(fetch_google_files_client, user_number, "google")

def test_fetch_google_files_invalid_auth(fetch_google_files_client):
    """Test fetching Google files with invalid auth token.
    params:
        fetch_google_files_client: 
            Fixture for creating a test client for the fetch_google_files endpoint.
    """
    for user_number in range(1, 3+1):  # 3 users

        assert_fetch_google_files_invalid_auth(fetch_google_files_client, user_number)

def test_fetch_google_files_missing_header(fetch_google_files_client):
    """Test fetching Google files with missing auth header.
    params:
        fetch_google_files_client: 
            Fixture for creating a test client for the fetch_google_files endpoint.
    """
    for user_number in range(1, 3+1):  # 3 users

        assert_fetch_google_files_missing_header(fetch_google_files_client, user_number)

def test_fetch_google_files_missing_userid(fetch_google_files_client):
    """Test fetching Google files with missing userId query parameter.
    params:
        fetch_google_files_client:
            Fixture for creating a test client for the fetch_google_files endpoint.
    """
    for _ in range(1, 3+1):  # 3 users

        assert_fetch_google_files_missing_userid(fetch_google_files_client)

def test_fetch_onedrive_files_success(fetch_onedrive_files_client):
    """Test fetching OneDrive files successfully for 3 users.
    params:
        fetch_onedrive_files_client:
            Fixture for creating a test client for the fetch_onedrive_files endpoint.
    """
    for user_number in range(1, 3+1):  # 3 users

        assert_fetch_onedrive_files_success(
            fetch_onedrive_files_client,
            user_number,
            "onedrive"
        )

def test_fetch_onedrive_files_invalid_auth(fetch_onedrive_files_client):
    """Test fetching OneDrive files with invalid auth token.
    params:
        fetch_onedrive_files_client:
            Fixture for creating a test client for the fetch_onedrive_files endpoint.
    """
    for user_number in range(1, 3+1):  # 3 users

        assert_fetch_onedrive_files_invalid_auth(fetch_onedrive_files_client, user_number)

def test_fetch_onedrive_files_missing_header(fetch_onedrive_files_client):
    """Test fetching OneDrive files with missing auth header.
    params:
        fetch_onedrive_files_client:
            Fixture for creating a test client for the fetch_onedrive_files endpoint.
    """
    for user_number in range(1, 3+1):  # 3 users

        assert_fetch_onedrive_files_missing_header(fetch_onedrive_files_client, user_number)

def test_fetch_onedrive_files_missing_userid(fetch_onedrive_files_client):
    """Test fetching OneDrive files with missing userId query parameter.
    params:
        fetch_onedrive_files_client:
            Fixture for creating a test client for the fetch_onedrive_files endpoint.
    """

    for _ in range(1, 3+1):  # 3 users

        assert_fetch_onedrive_files_missing_userid(fetch_onedrive_files_client)
