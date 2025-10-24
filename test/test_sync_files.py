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
    assert_sync_files_missing_user_id,
    assert_sync_files_function_missing_user_id
)

from p7.sync_files.api import sync_files_router
from p7.create_user.api import create_user_router
from p7.create_service.api import create_service_router
from p7.get_google_drive_files.helper import build_google_drive_path
from p7.get_dropbox_files.helper import (
    update_or_create_file as update_or_create_file_dropbox
    )
from p7.get_google_drive_files.helper import (
    update_or_create_file as update_or_create_file_google_drive)
from p7.get_onedrive_files.helper import (
    update_or_create_file as update_or_create_file_onedrive
    )

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
    provider = "ONEDRIVE"
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
    assert_create_service_success(service_client, payload, 2)

    test_files = [
        {
            "@microsoft.graph.downloadUrl": "https://my.microsoftpersonalcontent.com/personal/fea39108d8cadfbf/_layouts/15/download.aspx?UniqueId=3e5b5eab-6b34-4eca-89b1-30fe45a719c3&Translate=false&tempauth=v1e.eyJzaXRlaWQiOiIyM2RiYmFiYy04Mjg2LTRlYTktOWQ0OS1hNmNlMDY1N2MyZmQiLCJhcHBfZGlzcGxheW5hbWUiOiJQNyIsImFwcGlkIjoiOTE1NWYzZjQtOTE5NS00YWVkLWI4NWYtZTkzODNmNWE1YzI4IiwiYXVkIjoiMDAwMDAwMDMtMDAwMC0wZmYxLWNlMDAtMDAwMDAwMDAwMDAwL215Lm1pY3Jvc29mdHBlcnNvbmFsY29udGVudC5jb21AOTE4ODA0MGQtNmM2Ny00YzViLWIxMTItMzZhMzA0YjY2ZGFkIiwiZXhwIjoiMTc2MTMwNDc4MSJ9.BNMTCGmauD3YwSqe2hhNiVkMlE4lQSne7cdGLG0Q6VHEtXCj50YP4fdz7EDgIHYPCtnc0NV3_t47q6mnnfPlO2leMcUFkHRYkbw9ho0i6B9qFlwbXnXPrcbb21p7XNRMCjWC-EjCts3fjBAVpflaNZhJUu6uVi-9b_eY9MmEMq1MnsFc7wOk41RL8Peopgp9ai3adgvsUd573s2wC9SQZIDqnU4FNBdfF7OQwgOW6dVprnn4uwwCTgsGM1m8u59NrrC6I2UpvTKFqPpfH3-Gr2yy4uVY8xhOYFo89jfjPwmO217LCxEDZHSPjZP6dRTvehDAKLTimDTiLYPAtrPizUN4Mzw-03dT0k91S7iXkrlkQi4y3UuLC4unL-FR1d5VO0hNQE3UChTWGis32tNKcOa0MjPPWnF7VAHqieFHShELBZzM307X9j5oeJjDYFAe.UYLUmO_ecKGeM4bbtod331i1ma5Y2AgvfIEaqqegRbA&ApiVersion=2.0",
            "createdDateTime": "2025-10-24T10:14:02Z",
            "eTag": "\"{3E5B5EAB-6B34-4ECA-89B1-30FE45A719C3},4\"",
            "id": "FEA39108D8CADFBF!s3e5b5eab6b344eca89b130fe45a719c3",
            "lastModifiedDateTime": "2025-10-24T10:14:21Z",
            "name": "OneDrive 1.docx",
            "webUrl": "https://onedrive.live.com/personal/fea39108d8cadfbf/_layouts/15/doc.aspx?resid=3e5b5eab-6b34-4eca-89b1-30fe45a719c3&cid=fea39108d8cadfbf",
            "cTag": "\"c:{3E5B5EAB-6B34-4ECA-89B1-30FE45A719C3},3\"",
            "size": 10561,
            "createdBy": {
            "user": {
                "email": "p7swtest3@gmail.com",
                "id": "fea39108d8cadfbf",
                "displayName": "p7sw test3"
            }
            },
            "lastModifiedBy": {
            "user": {
                "email": "p7swtest3@gmail.com",
                "id": "fea39108d8cadfbf",
                "displayName": "p7sw test3"
            }
            },
            "parentReference": {
            "driveType": "personal",
            "driveId": "fea39108d8cadfbf",
            "id": "FEA39108D8CADFBF!sea8cc6beffdb43d7976fbc7da445c639",
            "name": "Documents",
            "path": "/drive/root:",
            "siteId": "23dbbabc-8286-4ea9-9d49-a6ce0657c2fd"
            },
            "file": {
            "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "hashes": {
                "quickXorHash": "ecyxrbaLVM5b54rNafRED0Ne53s=",
                "sha1Hash": "402099BD8E0FFA3F22B5BD328485BBE1DDB214D5",
                "sha256Hash": "6AB643135E5A05692FDBEC7FF531F640AF84276D132C4B35BCB4C713E0772066"
            }
            },
            "fileSystemInfo": {
            "createdDateTime": "2025-10-24T10:14:02Z",
            "lastModifiedDateTime": "2025-10-24T10:14:21Z"
            }
        },
        {
            "@microsoft.graph.downloadUrl": "https://my.microsoftpersonalcontent.com/personal/fea39108d8cadfbf/_layouts/15/download.aspx?UniqueId=3f1d91b5-e0f1-42b6-b4c3-e1a90d786dea&Translate=false&tempauth=v1e.eyJzaXRlaWQiOiIyM2RiYmFiYy04Mjg2LTRlYTktOWQ0OS1hNmNlMDY1N2MyZmQiLCJhcHBfZGlzcGxheW5hbWUiOiJQNyIsImFwcGlkIjoiOTE1NWYzZjQtOTE5NS00YWVkLWI4NWYtZTkzODNmNWE1YzI4IiwiYXVkIjoiMDAwMDAwMDMtMDAwMC0wZmYxLWNlMDAtMDAwMDAwMDAwMDAwL215Lm1pY3Jvc29mdHBlcnNvbmFsY29udGVudC5jb21AOTE4ODA0MGQtNmM2Ny00YzViLWIxMTItMzZhMzA0YjY2ZGFkIiwiZXhwIjoiMTc2MTMwNDc4MSJ9.AeW51MsYNYhTjCjakhYGJocwb4tqUtQ5qmBnAJFnkHmZyqiqjdTTP-bgzEh0NLQ48D_IN3ZXrJMYUpnM7xene00zxXQo3ksDH2RFqrDLh9OnbPADqQg5GQ9OG_Rda8YK3l9i1G_mbLsPjBEJTwH-hzvtPuQCLP0FwcJwaY0Eh6H6jJkTn3FO5mq_JRvHpu6LDGD2pyLp0kdPDh-Wpeg43wd85F92HaSquqOPWrVQW5ddYWvBVL2Xc4B0COpIEHFGGBkRYuI0YtjES-BzCO8pPNvPFVx0TqhNsyzJa15zO0gHzwFHNopG8qOl6wCPXhkFbGAJc0LoUgORusoM1lD7eIx532LGNtFxaN8FNn_faF9xwCLfCszzJigqbVzzMXOn0q_bDo6KBtCqB-M_3XXnH1XuCDPOnui-EC7kSSHtIXmcdrRbTTZQxLE9wcyE_UF0.pM1YktAode58iHtOkhGqLKzX-O9N-KrfLGoAEQQ09-8&ApiVersion=2.0",
            "createdDateTime": "2025-10-24T10:15:19Z",
            "eTag": "\"{3F1D91B5-E0F1-42B6-B4C3-E1A90D786DEA},1\"",
            "id": "FEA39108D8CADFBF!s3f1d91b5e0f142b6b4c3e1a90d786dea",
            "lastModifiedDateTime": "2025-10-24T10:15:19Z",
            "name": "Operating_Systems_three_easy_pieces.pdf",
            "webUrl": "https://onedrive.live.com?cid=fea39108d8cadfbf&id=FEA39108D8CADFBF!s3f1d91b5e0f142b6b4c3e1a90d786dea",
            "cTag": "\"c:{3F1D91B5-E0F1-42B6-B4C3-E1A90D786DEA},1\"",
            "size": 5658674,
            "createdBy": {
            "user": {
                "email": "p7swtest3@gmail.com",
                "id": "fea39108d8cadfbf",
                "displayName": "p7sw test3"
            }
            },
            "lastModifiedBy": {
            "user": {
                "email": "p7swtest3@gmail.com",
                "id": "fea39108d8cadfbf",
                "displayName": "p7sw test3"
            }
            },
            "parentReference": {
            "driveType": "personal",
            "driveId": "fea39108d8cadfbf",
            "id": "FEA39108D8CADFBF!sea8cc6beffdb43d7976fbc7da445c639",
            "name": "Documents",
            "path": "/drive/root:",
            "siteId": "23dbbabc-8286-4ea9-9d49-a6ce0657c2fd"
            },
            "file": {
            "mimeType": "application/pdf",
            "hashes": {
                "quickXorHash": "26eYa+eLOZsTePXPRVok27HPdnQ="
            }
            },
            "fileSystemInfo": {
            "createdDateTime": "2025-10-24T10:15:19Z",
            "lastModifiedDateTime": "2025-10-24T10:15:19Z"
            }
        },
        {
            "@microsoft.graph.downloadUrl": "https://my.microsoftpersonalcontent.com/personal/fea39108d8cadfbf/_layouts/15/download.aspx?UniqueId=b55e9505-f11a-44c2-9a63-e99e5bceeb5e&Translate=false&tempauth=v1e.eyJzaXRlaWQiOiIyM2RiYmFiYy04Mjg2LTRlYTktOWQ0OS1hNmNlMDY1N2MyZmQiLCJhcHBfZGlzcGxheW5hbWUiOiJQNyIsImFwcGlkIjoiOTE1NWYzZjQtOTE5NS00YWVkLWI4NWYtZTkzODNmNWE1YzI4IiwiYXVkIjoiMDAwMDAwMDMtMDAwMC0wZmYxLWNlMDAtMDAwMDAwMDAwMDAwL215Lm1pY3Jvc29mdHBlcnNvbmFsY29udGVudC5jb21AOTE4ODA0MGQtNmM2Ny00YzViLWIxMTItMzZhMzA0YjY2ZGFkIiwiZXhwIjoiMTc2MTMwNDc4MiJ9.bjw-UoPCW6dUoyYw0KHIqCXDTMOksXPU9FkoXtkT6apMvTTLtn4LDKdDuACDCgzGmHfgolqxm2NYg0zsAq9T5lvamREG4OLE6MmBEtFNemh1bOaTp3PPm2daBhpw7HjrybiXFCv0hEjRbVGLJKj7hjBfdv_b3kt7pDV0z4bAmPRHRsUDr_PYT4c9EO9IjVVrwhNQvZ7OoKHyf84S2QGCfInxNQbggl4pV1VPlMWj86voKFJGGrzpyN0Pbuea9wuMJZyHdZ2BrTNu28VzJZi9MOosXdoHTA5fi7HLGyrUr50lHQbftYmK7p2ZTwj9bxBl0cmrVHdjjZaiy0cPrKekuclvCKLvyhKhJIba26tL6YEFKd9XSr-s28DyKDSvv6bBYSFYnh_7TLNeybyjlS47ozRVUSB3vpIVjymBiQ718zu8hdlJCePtLQfz6sk8Swpg.NxjcQs7fo3HUMcbqkMTeW75uviMLC3fhGT6GWCQq_o8&ApiVersion=2.0",
            "createdDateTime": "2025-10-24T10:14:25Z",
            "eTag": "\"{B55E9505-F11A-44C2-9A63-E99E5BCEEB5E},4\"",
            "id": "FEA39108D8CADFBF!sb55e9505f11a44c29a63e99e5bceeb5e",
            "lastModifiedDateTime": "2025-10-24T10:14:46Z",
            "name": "Test Onedrive 1.docx",
            "webUrl": "https://onedrive.live.com/personal/fea39108d8cadfbf/_layouts/15/doc.aspx?resid=b55e9505-f11a-44c2-9a63-e99e5bceeb5e&cid=fea39108d8cadfbf",
            "cTag": "\"c:{B55E9505-F11A-44C2-9A63-E99E5BCEEB5E},3\"",
            "size": 10564,
            "createdBy": {
            "user": {
                "email": "p7swtest3@gmail.com",
                "id": "fea39108d8cadfbf",
                "displayName": "p7sw test3"
            }
            },
            "lastModifiedBy": {
            "user": {
                "email": "p7swtest3@gmail.com",
                "id": "fea39108d8cadfbf",
                "displayName": "p7sw test3"
            }
            },
            "parentReference": {
            "driveType": "personal",
            "driveId": "fea39108d8cadfbf",
            "id": "FEA39108D8CADFBF!sea8cc6beffdb43d7976fbc7da445c639",
            "name": "Documents",
            "path": "/drive/root:",
            "siteId": "23dbbabc-8286-4ea9-9d49-a6ce0657c2fd"
            },
            "file": {
            "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "hashes": {
                "quickXorHash": "FH1nVGDGf6m7ajtBebtJESJ8tU8=",
                "sha1Hash": "704531D9DF430B130A5276E3CA1036439882E109",
                "sha256Hash": "6592475FC94F3FE54851EA087B50AF64F8FA1B34F80A188BBF1D5D8AE40AAB8E"
            }
            },
            "fileSystemInfo": {
            "createdDateTime": "2025-10-24T10:14:25Z",
            "lastModifiedDateTime": "2025-10-24T10:14:46Z"
            }
        }
    ]

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
