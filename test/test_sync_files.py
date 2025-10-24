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
from helpers.create_service import (assert_create_service_success)
from helpers.sync_files import (
    assert_sync_files_invalid_auth,
    assert_sync_files_missing_internal_auth,
    assert_sync_files_missing_user_id
)

from p7.sync_files.api import sync_files_router
from p7.create_user.api import create_user_router
from p7.create_service.api import create_service_router
from p7.get_google_drive_files.helper import build_google_drive_path

from repository.file import save_file, get_files_by_service
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

def test_sync_dropbox_files(
    service_client: TestClient,
    sync_files_client_fixture: TestClient,
    ):
    """Test syncing Dropbox files for a user."""
    user_id = 1
    provider = "DROPBOX"
    payload = {
                "userId": os.getenv(f"TEST_USER_{provider}_ID_{user_id}"),
                "oauthType": os.getenv(f"TEST_USER_{provider}_OAUTHTYPE_{user_id}"),
                "oauthToken": os.getenv(f"TEST_USER_{provider}_OAUTHTOKEN_{user_id}"),
                "accessToken": os.getenv(f"TEST_USER_{provider}_ACCESSTOKEN_{user_id}"),
                "accessTokenExpiration": os.getenv(
                    f"TEST_USER_{provider}_ACCESSTOKENEXPIRATION_{user_id}"
                ),
                "refreshToken": os.getenv(f"TEST_USER_{provider}_REFRESHTOKEN_{user_id}"),
                "name": os.getenv(f"TEST_USER_{provider}_NAME_{user_id}"),
                "accountId": os.getenv(f"TEST_USER_{provider}_ACCOUNTID_{user_id}"),
                "email": os.getenv(f"TEST_USER_{provider}_EMAIL_{user_id}"),
                "scopeName": os.getenv(f"TEST_USER_{provider}_SCOPENAME_{user_id}"),
            }
    assert_create_service_success(service_client, payload, 0)

    test_files = [
        {
        ".tag": "file",
        "name": "Random facts.docx",
        "path_lower": "/random facts.docx",
        "path_display": "/Random facts.docx",
        "id": "id:8WGkOhP6AoYAAAAAAAAABw",
        "client_modified": "2025-10-10T11:51:37Z",
        "server_modified": "2025-10-10T11:51:37Z",
        "rev": "01640cc8a4615360000000301ba7c31",
        "size": 12290,
        "is_downloadable": True,
        "content_hash": "a76ce290f354df2d69e3a554a2a0fd329f48700d154f5efe26fcf405628a9022"
        },
        {
        ".tag": "file",
        "name": "Distributed Systems - Concepts and Design, Coulouris et al., Fifth edition, Addison Wesley, 2015.pdf",
        "path_lower": "/distributed systems - concepts and design, coulouris et al., fifth edition, addison wesley, 2015.pdf",
        "path_display": "/Distributed Systems - Concepts and Design, Coulouris et al., Fifth edition, Addison Wesley, 2015.pdf",
        "id": "id:8WGkOhP6AoYAAAAAAAAACg",
        "client_modified": "2025-10-17T11:53:08Z",
        "server_modified": "2025-10-17T12:03:00Z",
        "rev": "016415983d7dc1e0000000301ba7c31",
        "size": 10169495,
        "is_downloadable": True,
        "content_hash": "72d351c72e0540815b3009b427ecffed39b20c5f4ca90f94e690c74b147a5a99"
        },
        {
        ".tag": "file",
        "name": "Graham Hutton - Programming in Haskell - 2nd Edition.pdf",
        "path_lower": "/graham hutton - programming in haskell - 2nd edition.pdf",
        "path_display": "/Graham Hutton - Programming in Haskell - 2nd Edition.pdf",
        "id": "id:8WGkOhP6AoYAAAAAAAAADA",
        "client_modified": "2025-10-22T08:42:31Z",
        "server_modified": "2025-10-22T08:42:31Z",
        "rev": "01641bb4c1540eb0000000301ba7c31",
        "size": 2101585,
        "is_downloadable": True,
        "content_hash": "eddc2beffb09a2425f299ce11df9ad4e686bcfd9a253d295eead88b3c7d964b4"
        },
        {
        ".tag": "file",
        "name": "simple.hs",
        "path_lower": "/simple.hs",
        "path_display": "/simple.hs",
        "id": "id:8WGkOhP6AoYAAAAAAAAADQ",
        "client_modified": "2025-10-22T08:42:44Z",
        "server_modified": "2025-10-22T08:42:44Z",
        "rev": "01641bb4ce34cf00000000301ba7c31",
        "size": 1111,
        "is_downloadable": True,
        "content_hash": "e31cb829ff236505b70699c9717b029e988875967c7f7c19a40a859f34026d1f"
        }
    ]
    service = get_service(user_id, "dropbox")
    service.indexedAt = datetime.fromisoformat("2025-10-22T08:42:44+00:00")
    service.save(update_fields=["indexedAt"])

    for file in test_files:
        extension = os.path.splitext(file["name"])[1]
        path = file["path_display"]
        link = "https://www.dropbox.com/preview" + path

        save_file(
            service,
            file["id"],
            file["name"],
            extension,
            file["is_downloadable"],
            path,
            link,
            file["size"],
            file["client_modified"],
            file["server_modified"],
            None,
            None,
            None,
        )
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

    #Check that name has been updated from simple.hs to simple2.hs
    for file in files:
        if file.serviceFileId == test_files[3]["id"]:
            check.equal(file.name, "simple2.hs")

    #Check that other files are unchanged
    for file in files:
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
    provider = "GOOGLE"
    payload = {
                "userId": os.getenv(f"TEST_USER_{provider}_ID_{user_id}"),
                "oauthType": os.getenv(f"TEST_USER_{provider}_OAUTHTYPE_{user_id}"),
                "oauthToken": os.getenv(f"TEST_USER_{provider}_OAUTHTOKEN_{user_id}"),
                "accessToken": os.getenv(f"TEST_USER_{provider}_ACCESSTOKEN_{user_id}"),
                "accessTokenExpiration": os.getenv(
                    f"TEST_USER_{provider}_ACCESSTOKENEXPIRATION_{user_id}"
                ),
                "refreshToken": os.getenv(f"TEST_USER_{provider}_REFRESHTOKEN_{user_id}"),
                "name": os.getenv(f"TEST_USER_{provider}_NAME_{user_id}"),
                "accountId": os.getenv(f"TEST_USER_{provider}_ACCOUNTID_{user_id}"),
                "email": os.getenv(f"TEST_USER_{provider}_EMAIL_{user_id}"),
                "scopeName": os.getenv(f"TEST_USER_{provider}_SCOPENAME_{user_id}"),
            }
    assert_create_service_success(service_client, payload, 1)

    test_files = [
        {
            "parents": [
            "0AL_qu-H6dCg9Uk9PVA"
            ],
            "capabilities": {
            "canCopy": True,
            "canDownload": True
            },
            "downloadRestrictions": {
            "itemDownloadRestriction": {
                "restrictedForReaders": False,
                "restrictedForWriters": False
            },
            "effectiveDownloadRestrictionWithContext": {
                "restrictedForReaders": False,
                "restrictedForWriters": False
            }
            },
            "kind": "drive#file",
            "id": "1rc-a6RDDLbwSJjZwjgUv7Sxg4Wx-Xdut8FNv29IS8cc",
            "name": "Test Document 1",
            "mimeType": "application/vnd.google-apps.document",
            "starred": False,
            "trashed": False,
            "webViewLink": "https://docs.google.com/document/d/1rc-a6RDDLbwSJjZwjgUv7Sxg4Wx-Xdut8FNv29IS8cc/edit?usp=drivesdk",
            "iconLink": "https://drive-thirdparty.googleusercontent.com/16/type/application/vnd.google-apps.document",
            "hasThumbnail": False,
            "viewedByMeTime": "2025-10-23T09:56:54.708Z",
            "createdTime": "2025-10-23T08:35:56.013Z",
            "modifiedTime": "2025-10-24T08:46:43.793Z",
            "shared": False,
            "ownedByMe": True,
            "size": "1024"
        },
        {
            "parents": [
            "0AL_qu-H6dCg9Uk9PVA"
            ],
            "capabilities": {
            "canCopy": True,
            "canDownload": True
            },
            "downloadRestrictions": {
            "itemDownloadRestriction": {
                "restrictedForReaders": False,
                "restrictedForWriters": False
            },
            "effectiveDownloadRestrictionWithContext": {
                "restrictedForReaders": False,
                "restrictedForWriters": False
            }
            },
            "kind": "drive#file",
            "id": "1X4UPbao_Y4gJzYmxAOHXDQiHHO5ip5p4EOaZP924iCU",
            "name": "Random Document 2",
            "mimeType": "application/vnd.google-apps.document",
            "starred": False,
            "trashed": False,
            "webViewLink": "https://docs.google.com/document/d/1X4UPbao_Y4gJzYmxAOHXDQiHHO5ip5p4EOaZP924iCU/edit?usp=drivesdk",
            "iconLink": "https://drive-thirdparty.googleusercontent.com/16/type/application/vnd.google-apps.document",
            "hasThumbnail": False,
            "viewedByMeTime": "2025-10-17T12:19:47.832Z",
            "createdTime": "2025-10-17T12:19:34.265Z",
            "modifiedTime": "2025-10-17T12:19:47.832Z",
            "shared": False,
            "ownedByMe": True,
            "size": "1024"
        },
        {
            "parents": [
            "0AL_qu-H6dCg9Uk9PVA"
            ],
            "capabilities": {
            "canCopy": True,
            "canDownload": True
            },
            "downloadRestrictions": {
            "itemDownloadRestriction": {
                "restrictedForReaders": False,
                "restrictedForWriters": False
            },
            "effectiveDownloadRestrictionWithContext": {
                "restrictedForReaders": False,
                "restrictedForWriters": False
            }
            },
            "kind": "drive#file",
            "id": "1HNE6QHh7ZvFU1sc1XjPDlFleDQXExx0Ek2XpbZnpkSU",
            "name": "Random document",
            "mimeType": "application/vnd.google-apps.document",
            "starred": False,
            "trashed": False,
            "webViewLink": "https://docs.google.com/document/d/1HNE6QHh7ZvFU1sc1XjPDlFleDQXExx0Ek2XpbZnpkSU/edit?usp=drivesdk",
            "iconLink": "https://drive-thirdparty.googleusercontent.com/16/type/application/vnd.google-apps.document",
            "hasThumbnail": False,
            "viewedByMeTime": "2025-10-17T12:16:47.092Z",
            "createdTime": "2025-10-17T12:16:35.964Z",
            "modifiedTime": "2025-10-17T12:16:47.092Z",
            "shared": False,
            "ownedByMe": True,
            "size": "1024"
        },
        {
            "parents": [
            "0AL_qu-H6dCg9Uk9PVA"
            ],
            "capabilities": {
            "canCopy": True,
            "canDownload": True
            },
            "downloadRestrictions": {
            "itemDownloadRestriction": {
                "restrictedForReaders": False,
                "restrictedForWriters": False
            },
            "effectiveDownloadRestrictionWithContext": {
                "restrictedForReaders": False,
                "restrictedForWriters": False
            }
            },
            "kind": "drive#file",
            "id": "1_0vL7bXnQK-sEIM9InL2pK0hEOlya8nN",
            "name": "Introduction to Compiler Design.pdf",
            "mimeType": "application/pdf",
            "starred": False,
            "trashed": False,
            "webContentLink": "https://drive.google.com/uc?id=1_0vL7bXnQK-sEIM9InL2pK0hEOlya8nN&export=download",
            "webViewLink": "https://drive.google.com/file/d/1_0vL7bXnQK-sEIM9InL2pK0hEOlya8nN/view?usp=drivesdk",
            "iconLink": "https://drive-thirdparty.googleusercontent.com/16/type/application/pdf",
            "hasThumbnail": True,
            "viewedByMeTime": "2025-10-24T08:46:32.234Z",
            "createdTime": "2025-10-24T08:46:32.234Z",
            "modifiedTime": "2024-02-07T11:58:07.000Z",
            "shared": False,
            "ownedByMe": True,
            "originalFilename": "Introduction to Compiler Design.pdf",
            "size": "7933431"
        }
    ]

    service = get_service(user_id, "google")
    service.indexedAt = datetime.fromisoformat("2025-10-24T08:46:32.234+00:00")
    service.save(update_fields=["indexedAt"])

    file_by_id = {file["id"]: file for file in test_files}

    for file in test_files:
        # Skip non-files (folders, shortcuts, etc)
        mime_type = file.get("mimeType", "")
        if (
            mime_type == "application/vnd.google-apps.folder"
            or mime_type == "application/vnd.google-apps.shortcut"
            or mime_type == "application/vnd.google-apps.drive-sdk"
        ):  # https://developers.google.com/workspace/drive/api/guides/mime-types
            continue
        extension = os.path.splitext(file.get("name", ""))[1]
        downloadable = file.get("capabilities", {}).get("canDownload")
        path = build_google_drive_path(file, file_by_id)

        save_file(
            service,
            file["id"],
            file["name"],
            extension,
            downloadable,
            path,
            file["webViewLink"],
            file.get("size", 0), # Can be empty
            file["createdTime"],
            file["modifiedTime"],
            None,
            None,
            None,
        )

    response = sync_files_client_fixture.get(
                f"/?user_id={user_id}",
                headers={"x-internal-auth": os.getenv("INTERNAL_API_KEY")},
                )

    check.equal(response.status_code, 200)

    files = get_files_by_service(service)
    print("Test files:")
    print(test_files)

    print("Files:")
    for file in files:
        print(file.serviceFileId)
    #Check that file has been deleted
    check.equal(any(file.serviceFileId == test_files[3]["id"] for file in files), False)

    #Check that the 3 other files still exists
    check.equal(any(file.serviceFileId == test_files[0]["id"] for file in files), True)
    check.equal(any(file.serviceFileId == test_files[1]["id"] for file in files), True)
    check.equal(any(file.serviceFileId == test_files[2]["id"] for file in files), True)

    #Check that name has been updated from Test Document 1 to Test Document 2
    #Check that other files are unchanged
    for file in files:
        if file.serviceFileId == test_files[0]["id"]:
            check.equal(file.name, "Test Document 2")
        if file.serviceFileId == test_files[1]["id"]:
            check.equal(file.name, test_files[1]["name"])
        if file.serviceFileId == test_files[2]["id"]:
            check.equal(file.name, test_files[2]["name"])
