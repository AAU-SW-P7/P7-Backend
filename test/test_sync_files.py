"""Tests for syncing files from various services."""
import os
import sys
from pathlib import Path
from datetime import datetime

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
from helpers.sync_files import (
    assert_sync_files_invalid_auth,
    assert_sync_files_missing_internal_auth,
    assert_sync_files_missing_user_id,
    assert_sync_files_function_missing_user_id,
    create_service,
    read_json_file
)

from p7.sync_files.api import sync_files_router
from p7.create_user.api import create_user_router
from p7.create_service.api import create_service_router
from p7.get_dropbox_files.helper import (update_or_create_file as update_or_create_file_dropbox)
from p7.get_google_drive_files.helper import (update_or_create_file as update_or_create_file_google_drive)
from p7.get_onedrive_files.helper import (update_or_create_file as update_or_create_file_onedrive)

from repository.file import get_files_by_service
from repository.service import get_service

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

@pytest.fixture(name="sync_files_client_fixture", scope='module', autouse=True)
def sync_file_client():
    """Fixture for creating a test client for the save_file endpoint.
    Returns:
        TestClient: A test client for the save_file endpoint.
    """
    return TestClient(sync_files_router)

def test_create_user_success(user_client):
    """Test creating 3 users successfully.
    params:
        user_client: Fixture for creating a test client for the create_user endpoint.
    """
    for user_number in range(1, 3+1):  # 3 users
        assert_create_user_success(user_client, user_number)

def test_sync_files_missing_internal_auth(sync_files_client_fixture):
    """Test for trying to call sync_files endpoint without auth header"""
    assert_sync_files_missing_internal_auth(sync_files_client_fixture, 1)

def test_sync_files_missing_user_id(sync_files_client_fixture):
    """Test for calling sync_files endpoint without a user_id"""
    assert_sync_files_missing_user_id(sync_files_client_fixture)

def test_sync_files_invalid_internal_auth(sync_files_client_fixture):
    """Test for calling the sync_files endpoint with invalid auth"""
    assert_sync_files_invalid_auth(sync_files_client_fixture, 1)

def test_sync_files_functions():
    """Test for calling the sub functions of sync_files endpoint"""
    assert_sync_files_function_missing_user_id("dropbox")
    assert_sync_files_function_missing_user_id("google")
    assert_sync_files_function_missing_user_id("onedrive")

def test_sync_dropbox_files(
    service_client: TestClient,
    sync_files_client_fixture: TestClient,
    ):
    """Test syncing Dropbox files for a user."""
    user_id = 1
    create_service(service_client, "DROPBOX", user_id, 0)

    test_files = read_json_file("test/json/user_1_dropbox.json")
    service = get_service(user_id, "dropbox")
    service.indexedAt = datetime.fromisoformat("2025-10-22T08:42:44+00:00")
    service.save(update_fields=["indexedAt"])

    for file in test_files:
        update_or_create_file_dropbox(file, service)

    response = sync_files_client_fixture.get(
                f"/?user_id={user_id}",
                headers={"x-internal-auth": os.getenv("INTERNAL_API_KEY")},
                )

    check.equal(response.status_code, 200)

    files = get_files_by_service(service)

    #Check that file has been deleted
    check.equal(any(file.serviceFileId == test_files[2]["id"] for file in files), False)

    #Check that the 3 other files still exists
    check.equal(any(file.serviceFileId == test_files[0]["id"] for file in files), True)
    check.equal(any(file.serviceFileId == test_files[1]["id"] for file in files), True)
    check.equal(any(file.serviceFileId == test_files[3]["id"] for file in files), True)

    for file in files:
        #Check that name has been updated from simple.hs to simple2.hs
        if file.serviceFileId == test_files[3]["id"]:
            check.equal(file.name, "simple2.hs")
        #Check that other files are unchanged
        if file.serviceFileId == test_files[0]["id"]:
            check.equal(file.name, test_files[0]["name"])
        if file.serviceFileId == test_files[1]["id"]:
            check.equal(file.name, test_files[1]["name"])

def test_sync_google_drive_files(
    service_client: TestClient,
    sync_files_client_fixture: TestClient,
    ):
    """Test syncing google Drive files for a user."""
    user_id = 2
    create_service(service_client, "GOOGLE", user_id, 1)

    test_files = read_json_file("test/json/user_2_google_drive.json")

    service = get_service(user_id, "google")
    service.indexedAt = datetime.fromisoformat("2025-10-24T08:46:32.234+00:00")
    service.save(update_fields=["indexedAt"])

    file_by_id = {file["id"]: file for file in test_files}

    for file in test_files:
        # Skip non-files (folders, shortcuts, etc)
        mime_type = file.get("mimeType", "")
        mime_type_set = {
            "application/vnd.google-apps.folder",
            "application/vnd.google-apps.shortcut",
            "application/vnd.google-apps.drive-sdk"}
        if (mime_type in mime_type_set
        ):  # https://developers.google.com/workspace/drive/api/guides/mime-types
            continue
        update_or_create_file_google_drive(file, service, file_by_id)

    response = sync_files_client_fixture.get(
                f"/?user_id={user_id}",
                headers={"x-internal-auth": os.getenv("INTERNAL_API_KEY")},
                )

    check.equal(response.status_code, 200)

    files = get_files_by_service(service)

    #Check that file has been deleted
    check.equal(any(file.serviceFileId == test_files[3]["id"] for file in files), False)

    #Check that the 3 other files still exists
    check.equal(any(file.serviceFileId == test_files[0]["id"] for file in files), True)
    check.equal(any(file.serviceFileId == test_files[1]["id"] for file in files), True)
    check.equal(any(file.serviceFileId == test_files[2]["id"] for file in files), True)

    for file in files:
        #Check that name has been updated from Test Document 1 to Test Document 2
        if file.serviceFileId == test_files[0]["id"]:
            check.equal(file.name, "Test Document 2")
        #Check that other files are unchanged
        if file.serviceFileId == test_files[1]["id"]:
            check.equal(file.name, test_files[1]["name"])
        if file.serviceFileId == test_files[2]["id"]:
            check.equal(file.name, test_files[2]["name"])

def test_sync_onedrive_files(
    service_client: TestClient,
    sync_files_client_fixture: TestClient,
    ):
    """Test syncing onedrive files for a user."""
    user_id = 3
    create_service(service_client, "ONEDRIVE", 3, 2)

    test_files = read_json_file("test/json/user_3_onedrive.json")

    service = get_service(user_id, "microsoft-entra-id")
    service.indexedAt = datetime.fromisoformat("2025-10-24T08:46:32.234+00:00")
    service.save(update_fields=["indexedAt"])



    for file in test_files:
        update_or_create_file_onedrive(file, service)

    response = sync_files_client_fixture.get(
                f"/?user_id={user_id}",
                headers={"x-internal-auth": os.getenv("INTERNAL_API_KEY")},
                )

    check.equal(response.status_code, 200)

    files = get_files_by_service(service)

    #Check that file has been deleted
    check.equal(any(file.serviceFileId == test_files[1]["id"] for file in files), False)

    #Check that the 3 other files still exists
    check.equal(any(file.serviceFileId == test_files[0]["id"] for file in files), True)
    check.equal(any(file.serviceFileId == test_files[2]["id"] for file in files), True)

    for file in files:
        #Check that name has been updated from OneDrive 1.docx to OneDrive 2.docx
        if file.serviceFileId == test_files[0]["id"]:
            check.equal(file.name, "OneDrive 2.docx")
        #Check that other files are unchanged
        if file.serviceFileId == test_files[2]["id"]:
            check.equal(file.name, test_files[2]["name"])
