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
from helpers.save_file import (
    assert_save_file_success,
    assert_save_file_invalid_auth,
    assert_save_file_missing_header,
    assert_save_file_missing_user_id,
)
from helpers.general_helper_functions import (create_x_users, create_service)
from p7.get_dropbox_files.api import fetch_dropbox_files_router
from p7.get_google_drive_files.api import fetch_google_drive_files_router
from p7.get_onedrive_files.api import fetch_onedrive_files_router

pytestmark = pytest.mark.usefixtures("django_db_setup")
#pytestmark = pytest.mark.django_db

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

def test_create_user_success():
    """Create 3 users."""
    create_x_users(3)


def test_create_service_success(service_client):
    """Test creating 9 services successfully (3 each for Dropbox, Google, OneDrive).
    params:
        service_client: Fixture for creating a test client for the create_service endpoint.
    """
    for user_number in range(1, 3+1):  # 3 services
        for provider in ["DROPBOX", "GOOGLE", "ONEDRIVE"]:
            create_service(provider, user_number)

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
