"""Tests for syncing files from all 3 services."""
import os
import sys
from pathlib import Path
from datetime import datetime
import pytest
import pytest_check as check

# Make the local backend package importable so `from p7...` works under pytest
repo_backend = Path(__file__).resolve().parents[1]  # backend/
sys.path.insert(0, str(repo_backend))
# Make the backend/test dir importable so you can use test_settings.py directly
sys.path.insert(0, str(repo_backend / "test"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_settings")

import django
django.setup()

from ninja.testing import TestClient
from helpers.sync_files import read_json_file
from helpers.general_helper_functions import (create_x_users, create_service)

from p7.sync_files.api import sync_files_router
from p7.get_dropbox_files.helper import (update_or_create_file as update_or_create_file_dropbox)
from p7.get_google_drive_files.helper import (
    update_or_create_file as update_or_create_file_google_drive
    )
from p7.get_onedrive_files.helper import (update_or_create_file as update_or_create_file_onedrive)

from repository.file import get_files_by_service
from repository.service import get_service

pytestmark = pytest.mark.usefixtures("django_db_setup")
#pytestmark = pytest.mark.django_db

@pytest.fixture(name="sync_files_client_fixture", scope='module', autouse=True)
def sync_file_client():
    """Fixture for creating a test client for the save_file endpoint.
    Returns:
        TestClient: A test client for the save_file endpoint.
    """
    return TestClient(sync_files_router)

def test_create_user_success():
    """Test creating a users successfully."""
    create_x_users(1)

def test_sync_files_all(
    sync_files_client_fixture: TestClient,
    ):
    """Test syncing files for all services for a user."""
    user_id = 1
    create_service("DROPBOX", user_id)
    create_service("GOOGLE", user_id)
    create_service("ONEDRIVE", user_id)

    # Setting a specific last index time, in order to ensure that everything looks new/updated
    index_time = "2025-10-22T08:42:44+00:00"
    #Get Dropbox service and set index time
    service_dropbox = get_service(user_id, "dropbox")
    service_dropbox.indexedAt = datetime.fromisoformat(index_time)
    service_dropbox.save(update_fields=["indexedAt"])

    #Get Google Drive service and set index time
    service_google_drive = get_service(user_id, "google")
    service_google_drive.indexedAt = datetime.fromisoformat(index_time)
    service_google_drive.save(update_fields=["indexedAt"])

    #Get Onedrive service and set index time
    service_onedrive = get_service(user_id, "onedrive")
    service_onedrive.indexedAt = datetime.fromisoformat(index_time)
    service_onedrive.save(update_fields=["indexedAt"])

    dropbox_test_files = read_json_file("test/json/user_1_dropbox.json")

    google_drive_test_files = read_json_file("test/json/user_1_google_drive.json")

    onedrive_test_files = read_json_file("test/json/user_1_onedrive.json")

    for file in dropbox_test_files:
        update_or_create_file_dropbox(file, service_dropbox)

    file_by_id = {file["id"]: file for file in google_drive_test_files}

    for file in google_drive_test_files:
        # Skip non-files (folders, shortcuts, etc)
        mime_type = file.get("mimeType", "")
        mime_type_set = {
            "application/vnd.google-apps.folder",
            "application/vnd.google-apps.shortcut",
            "application/vnd.google-apps.drive-sdk"}
        if (mime_type in mime_type_set
        ):  # https://developers.google.com/workspace/drive/api/guides/mime-types
            continue
        update_or_create_file_google_drive(file, service_google_drive, file_by_id)

    for file in onedrive_test_files:
        update_or_create_file_onedrive(file, service_onedrive)

    response = sync_files_client_fixture.get(
                f"/?user_id={user_id}",
                headers={"x-internal-auth": os.getenv("INTERNAL_API_KEY")},
                )

    check.equal(response.status_code, 202)

    dropbox_files = get_files_by_service(service_dropbox)
    google_drive_files = get_files_by_service(service_google_drive)
    onedrive_files = get_files_by_service(service_onedrive)

    #Check correct update Dropbox
    #Check that file has been deleted
    check.equal(
        any(file.serviceFileId == dropbox_test_files[2]["id"] for file in dropbox_files), False
        )

    #Check that the 3 other files still exists
    check.equal(
        any(file.serviceFileId == dropbox_test_files[0]["id"] for file in dropbox_files), True
        )
    check.equal(
        any(file.serviceFileId == dropbox_test_files[1]["id"] for file in dropbox_files), True
        )
    check.equal(
        any(file.serviceFileId == dropbox_test_files[3]["id"] for file in dropbox_files), True
        )

    for file in dropbox_files:
        #Check that name has been updated from simple.hs to simple2.hs
        if file.serviceFileId == dropbox_test_files[3]["id"]:
            check.equal(file.name, "simple2.hs")
        #Check that other files are unchanged
        if file.serviceFileId == dropbox_test_files[0]["id"]:
            check.equal(file.name, dropbox_test_files[0]["name"])
        if file.serviceFileId == dropbox_test_files[1]["id"]:
            check.equal(file.name, dropbox_test_files[1]["name"])

    #Check correct update Google Drive
    #Check that file has been deleted
    check.equal(
        any(file.serviceFileId == google_drive_test_files[5]["id"] for file in google_drive_files),
        False
        )

    #Check that the 3 other files still exists
    check.equal(
        any(file.serviceFileId == google_drive_test_files[0]["id"] for file in google_drive_files),
        True
        )
    check.equal(
        any(file.serviceFileId == google_drive_test_files[3]["id"] for file in google_drive_files),
        True
        )
    check.equal(any(
        file.serviceFileId == google_drive_test_files[4]["id"] for file in google_drive_files),
        True
        )

    for file in google_drive_files:
        #Check that name has been updated from Test Document 1 to Test Document 2
        if file.serviceFileId == google_drive_test_files[0]["id"]:
            check.equal(file.name, "Test document 2")
        #Check that other files are unchanged
        if file.serviceFileId == google_drive_test_files[3]["id"]:
            check.equal(file.name, google_drive_test_files[3]["name"])
        if file.serviceFileId == google_drive_test_files[4]["id"]:
            check.equal(file.name, google_drive_test_files[4]["name"])

    #Check correct update Onedrive
    # 4 ændret navn
    # 5 slettes
    # 6 + 7 forbliver
    #Check that file has been deleted
    check.equal(
        any(file.serviceFileId == onedrive_test_files[4]["id"] for file in onedrive_files), False
        )

    #Check that the 3 other files still exists
    check.equal(
        any(file.serviceFileId == onedrive_test_files[3]["id"] for file in onedrive_files), True
        )
    check.equal(
        any(file.serviceFileId == onedrive_test_files[5]["id"] for file in onedrive_files), True
        )
    check.equal(
        any(file.serviceFileId == onedrive_test_files[6]["id"] for file in onedrive_files), True
        )

    for file in onedrive_files:
        #Check that name has been updated from OneDrive 1.docx to OneDrive 2.docx
        if file.serviceFileId == onedrive_test_files[3]["id"]:
            check.equal(file.name, "Onedrive test 2.docx")
        #Check that other files are unchanged
        if file.serviceFileId == onedrive_test_files[5]["id"]:
            check.equal(file.name, onedrive_test_files[5]["name"])
        if file.serviceFileId == onedrive_test_files[6]["id"]:
            check.equal(file.name, onedrive_test_files[6]["name"])
