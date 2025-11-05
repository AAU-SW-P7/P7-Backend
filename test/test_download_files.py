"""Tests for downloading files from various services."""
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
import pytest_check as check
from ninja.testing import TestClient
from helpers.create_user import (assert_create_user_success)
from helpers.create_service import (assert_create_service_success)
from helpers.fetch_service import (
    assert_fetch_dropbox_files_success,
    assert_fetch_google_files_success,
    assert_fetch_onedrive_files_success,
)
from helpers.download_file import (
    assert_download_file_success,
    assert_download_file_invalid_auth,
    assert_download_file_missing_header,
    assert_download_file_missing_user_id,
)

from p7.create_user.api import create_user_router
from p7.create_service.api import create_service_router
from p7.get_dropbox_files.api import fetch_dropbox_files_router
from p7.get_google_drive_files.api import fetch_google_drive_files_router
from p7.get_onedrive_files.api import fetch_onedrive_files_router
from p7.download_dropbox_files.api import download_dropbox_files_router

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

@pytest.fixture(name="download_dropbox_files_client_fixture", scope='module', autouse=True)
def download_dropbox_files_client():
    """Fixture for creating a test client for the download_dropbox_files endpoint.
    Returns:
        TestClient: A test client for the download_dropbox_files endpoint.
    """
    return TestClient(download_dropbox_files_router)

def test_create_user_success(user_client):
    """Test creating 3 users successfully.
    params:
        user_client: Fixture for creating a test client for the create_user endpoint.
    """
    for user_number in range(1, 3+1):  # 3 users
        assert_create_user_success(user_client, user_number)
        
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

def test_fetch_dropbox_files_success(fetch_dropbox_files_client):
    """Test fetching Dropbox files successfully for 3 users.
    params:
        fetch_dropbox_files_client:
            Fixture for creating a test client for the fetch_dropbox_files endpoint.
    """
    for user_number in range(1, 3+1):  # 3 users

        assert_fetch_dropbox_files_success(
            fetch_dropbox_files_client,
            user_number,
            "dropbox",
        )

def test_download_dropbox_file_success(download_dropbox_files_client_fixture):
    """Test downloading a Dropbox file."""

    for user_number in range(1, 3+1):  # 3 users

        assert_download_file_success(download_dropbox_files_client_fixture, user_number, 'dropbox')

def test_download_dropbox_file_invalid_auth(download_dropbox_files_client_fixture):
    """Test downloading a Dropbox file with invalid auth."""

    for user_number in range(1, 3+1):  # 3 users

        assert_download_file_invalid_auth(download_dropbox_files_client_fixture, user_number)

def test_download_dropbox_file_missing_header(download_dropbox_files_client_fixture):
    """Test downloading a Dropbox file with missing header."""

    for user_number in range(1, 3+1):  # 3 users

        assert_download_file_missing_header(download_dropbox_files_client_fixture, user_number)

def test_download_dropbox_file_missing_user_id(download_dropbox_files_client_fixture):
    """Test downloading a Dropbox file with missing user ID."""

    assert_download_file_missing_user_id(download_dropbox_files_client_fixture)