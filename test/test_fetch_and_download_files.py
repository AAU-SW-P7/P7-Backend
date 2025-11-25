"""Tests for the fetch service endpoints."""
import os
import sys
from pathlib import Path

<<<<<<< HEAD:test/test_fetch_service.py
=======

>>>>>>> 8d795025b25bdc015ae9d6662b9418f7d644124e:test/test_fetch_and_download_files.py
# Make the local backend package importable so `from p7...` works under pytest
repo_backend = Path(__file__).resolve().parents[1]  # backend/
sys.path.insert(0, str(repo_backend))
# Make the backend/test dir importable so you can use test_settings.py directly
sys.path.insert(0, str(repo_backend / "test"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_settings")

import pytest

import django
django.setup()
<<<<<<< HEAD:test/test_fetch_service.py
=======
from ninja.testing import TestClient
>>>>>>> 8d795025b25bdc015ae9d6662b9418f7d644124e:test/test_fetch_and_download_files.py

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
from helpers.download_file import (
    assert_download_file_success,
    assert_download_file_invalid_auth,
    assert_download_file_missing_header,
    assert_download_file_missing_user_id,
)
from helpers.general_helper_functions import (create_x_users, create_service)
<<<<<<< HEAD:test/test_fetch_service.py
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






from p7.create_user.api import create_user_router
from p7.create_service.api import create_service_router
=======
>>>>>>> 8d795025b25bdc015ae9d6662b9418f7d644124e:test/test_fetch_and_download_files.py
from p7.get_dropbox_files.api import fetch_dropbox_files_router
from p7.get_google_drive_files.api import fetch_google_drive_files_router
from p7.get_onedrive_files.api import fetch_onedrive_files_router
from p7.download_dropbox_files.api import download_dropbox_files_router
from p7.download_google_drive_files.api import download_google_drive_files_router
from p7.download_onedrive_files.api import download_onedrive_files_router


pytestmark = pytest.mark.usefixtures("django_db_setup")
#pytestmark = pytest.mark.django_db

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

@pytest.fixture(
    name="download_dropbox_files_client_fixture", scope="module", autouse=True
)
def download_dropbox_files_client():
    """Fixture for creating a test client for the download_dropbox_files endpoint.
    Returns:
        TestClient: A test client for the download_dropbox_files endpoint.
    """
    return TestClient(download_dropbox_files_router)


@pytest.fixture(
    name="download_google_drive_files_client_fixture", scope="module", autouse=True
)
def download_google_files_client():
    """Fixture for creating a test client for the download_google_drive_files endpoint.
    Returns:
        TestClient: A test client for the download_google_drive_files endpoint.
    """
    return TestClient(download_google_drive_files_router)

@pytest.fixture(
    name="download_onedrive_files_client_fixture", scope="module", autouse=True
)
def download_onedrive_files_client():
    """Fixture for creating a test client for the download_onedrive_files endpoint.
    Returns:
        TestClient: A test client for the download_onedrive_files endpoint.
    """
    return TestClient(download_onedrive_files_router)


def test_create_user_success():
    """Create 3 users."""
    create_x_users(3)

def test_create_service_success():
    """Creating 9 services (3 each for Dropbox, Google, OneDrive)."""
    for user_number in range(1, 3+1):  # 3 users
        for provider in ["DROPBOX", "GOOGLE", "ONEDRIVE"]:
            create_service(provider, user_number)

# --- TESTS FOR DROPBOX ---
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

def test_download_dropbox_file_success(download_dropbox_files_client_fixture):
    """Test downloading a Dropbox file."""

    for user_number in range(1, 3 + 1):  # 3 users

        assert_download_file_success(
            download_dropbox_files_client_fixture, user_number, "dropbox"
        )


def test_download_dropbox_file_invalid_auth(download_dropbox_files_client_fixture):
    """Test downloading a Dropbox file with invalid auth."""

    for user_number in range(1, 3 + 1):  # 3 users

        assert_download_file_invalid_auth(
            download_dropbox_files_client_fixture, user_number
        )


def test_download_dropbox_file_missing_header(download_dropbox_files_client_fixture):
    """Test downloading a Dropbox file with missing header."""

    for user_number in range(1, 3 + 1):  # 3 users

        assert_download_file_missing_header(
            download_dropbox_files_client_fixture, user_number
        )


def test_download_dropbox_file_missing_user_id(download_dropbox_files_client_fixture):
    """Test downloading a Dropbox file with missing user ID."""

    assert_download_file_missing_user_id(download_dropbox_files_client_fixture)

# --- TESTS FOR GOOGLE DRIVE ---

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

def test_download_google_drive_file_success(download_google_drive_files_client_fixture):
    """Test downloading a Google Drive file."""

    for user_number in range(1, 3 + 1):  # 3 users

        assert_download_file_success(
            download_google_drive_files_client_fixture,
            user_number,
            'google',
        )

def test_download_google_drive_file_invalid_auth(
    download_google_drive_files_client_fixture,
):
    """Test downloading a Google Drive file with invalid auth."""

    for user_number in range(1, 3 + 1):  # 3 users

        assert_download_file_invalid_auth(
            download_google_drive_files_client_fixture, user_number
        )


def test_download_google_drive_file_missing_header(
    download_google_drive_files_client_fixture,
):
    """Test downloading a Google Drive file with missing header."""

    for user_number in range(1, 3 + 1):  # 3 users

        assert_download_file_missing_header(
            download_google_drive_files_client_fixture, user_number
        )


def test_download_google_drive_file_missing_user_id(
    download_google_drive_files_client_fixture,
):
    """Test downloading a Google Drive file with missing user ID."""

    assert_download_file_missing_user_id(download_google_drive_files_client_fixture)

# --- TESTS FOR ONEDRIVE ---
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

def test_download_onedrive_file_success(download_onedrive_files_client_fixture):
    """Test downloading a OneDrive file."""

    for user_number in range(1, 3 + 1):  # 3 users

        assert_download_file_success(
            download_onedrive_files_client_fixture, user_number, "onedrive"
        )


def test_download_onedrive_file_invalid_auth(download_onedrive_files_client_fixture):
    """Test downloading a OneDrive file with invalid auth."""

    for user_number in range(1, 3 + 1):  # 3 users

        assert_download_file_invalid_auth(
            download_onedrive_files_client_fixture, user_number
        )


def test_download_onedrive_file_missing_header(download_onedrive_files_client_fixture):
    """Test downloading a OneDrive file with missing header."""

    for user_number in range(1, 3 + 1):  # 3 users

        assert_download_file_missing_header(
            download_onedrive_files_client_fixture, user_number
        )


def test_download_onedrive_file_missing_user_id(
    download_onedrive_files_client_fixture,
):
    """Test downloading a Google Drive file with missing user ID."""

    assert_download_file_missing_user_id(download_onedrive_files_client_fixture)
