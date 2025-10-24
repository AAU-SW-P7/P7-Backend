"""Tests for syncing files from all 3 services."""
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
    assert_sync_files_function_missing_user_id,
    create_service
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
    """Test creating a users successfully.
    params:
        user_client: Fixture for creating a test client for the create_user endpoint.
    """
    assert_create_user_success(user_client, 1)

def test_sync_files_all(
    service_client: TestClient,
    sync_files_client_fixture: TestClient,
    ):
    user_id = 1
    """Test syncing files for all services for a user."""
    create_service(service_client, "DROPBOX", user_id, 0)
    create_service(service_client, "GOOGLE", user_id, 1)
    create_service(service_client, "ONEDRIVE", user_id, 2)

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
    service_onedrive = get_service(user_id, "microsoft-entra-id")
    service_onedrive.indexedAt = datetime.fromisoformat(index_time)
    service_onedrive.save(update_fields=["indexedAt"])

    dropbox_test_files = [
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

    google_drive_test_files = [
    {
        "parents": [
        "0AJl3zNrPbzEFUk9PVA"
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
        "id": "1wbJS22Bzjhz_8kwQhm2l3i5DNdfSY6xBO2aBENSHme0",
        "name": "Test document 1",
        "mimeType": "application/vnd.google-apps.document",
        "starred": False,
        "trashed": False,
        "webViewLink": "https://docs.google.com/document/d/1wbJS22Bzjhz_8kwQhm2l3i5DNdfSY6xBO2aBENSHme0/edit?usp=drivesdk",
        "iconLink": "https://drive-thirdparty.googleusercontent.com/16/type/application/vnd.google-apps.document",
        "hasThumbnail": False,
        "viewedByMeTime": "2025-10-24T12:15:40.463Z",
        "createdTime": "2025-10-24T12:15:25.189Z",
        "modifiedTime": "2025-10-24T12:15:40.463Z",
        "shared": False,
        "ownedByMe": True,
        "size": "1024"
    },
    {
        "parents": [
        "0AJl3zNrPbzEFUk9PVA"
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
        "id": "1Ne-PlcYM4jLQDhoQPTt5e-P2WaiOHfMH4Nd6Mx10ipA",
        "name": "RANDOM ASS FILE TO CHECK IF TEST DIES",
        "mimeType": "application/vnd.google-apps.document",
        "starred": False,
        "trashed": True,
        "webViewLink": "https://docs.google.com/document/d/1Ne-PlcYM4jLQDhoQPTt5e-P2WaiOHfMH4Nd6Mx10ipA/edit?usp=drivesdk",
        "iconLink": "https://drive-thirdparty.googleusercontent.com/16/type/application/vnd.google-apps.document",
        "hasThumbnail": True,
        "viewedByMeTime": "2025-10-17T12:29:30.664Z",
        "createdTime": "2025-10-17T12:29:17.251Z",
        "modifiedTime": "2025-10-17T12:29:30.664Z",
        "shared": False,
        "ownedByMe": True,
        "size": "1024"
    },
    {
        "parents": [
        "0AJl3zNrPbzEFUk9PVA"
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
        "id": "1fzC8GiJ-xHxMsD0W94TZSK8BIn3nX7uYAXtGACUwHeI",
        "name": "Random fil",
        "mimeType": "application/vnd.google-apps.document",
        "starred": False,
        "trashed": True,
        "webViewLink": "https://docs.google.com/document/d/1fzC8GiJ-xHxMsD0W94TZSK8BIn3nX7uYAXtGACUwHeI/edit?usp=drivesdk",
        "iconLink": "https://drive-thirdparty.googleusercontent.com/16/type/application/vnd.google-apps.document",
        "hasThumbnail": False,
        "viewedByMeTime": "2025-10-21T09:49:35.281Z",
        "createdTime": "2025-10-17T12:12:57.272Z",
        "modifiedTime": "2025-10-17T12:13:09.196Z",
        "shared": False,
        "ownedByMe": True,
        "size": "1024"
    },
    {
        "parents": [
        "1BZ18zfDtsNJ4MdQR1A_4nJWZEY7Hptgu"
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
        "id": "1gTqrVSLkpeduRrXi0o0Hwfgx5zCLVr0p8p27dQDGGOo",
        "name": "Test File Do Not Remove",
        "mimeType": "application/vnd.google-apps.document",
        "starred": False,
        "trashed": False,
        "webViewLink": "https://docs.google.com/document/d/1gTqrVSLkpeduRrXi0o0Hwfgx5zCLVr0p8p27dQDGGOo/edit?usp=drivesdk",
        "iconLink": "https://drive-thirdparty.googleusercontent.com/16/type/application/vnd.google-apps.document",
        "hasThumbnail": True,
        "viewedByMeTime": "2025-10-16T09:52:45.636Z",
        "createdTime": "2025-10-10T12:30:51.862Z",
        "modifiedTime": "2025-10-16T10:08:16.086Z",
        "shared": False,
        "ownedByMe": True,
        "size": "1024"
    },
    {
        "parents": [
        "1BZ18zfDtsNJ4MdQR1A_4nJWZEY7Hptgu"
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
        "id": "19AU7fYJKCjV7jiStr8-QsDE0jVPvBP6h_3OQ-9KQESk",
        "name": "Test File Do Not Remove 2",
        "mimeType": "application/vnd.google-apps.document",
        "starred": False,
        "trashed": False,
        "webViewLink": "https://docs.google.com/document/d/19AU7fYJKCjV7jiStr8-QsDE0jVPvBP6h_3OQ-9KQESk/edit?usp=drivesdk",
        "iconLink": "https://drive-thirdparty.googleusercontent.com/16/type/application/vnd.google-apps.document",
        "hasThumbnail": True,
        "viewedByMeTime": "2025-10-16T10:07:23.903Z",
        "createdTime": "2025-10-16T10:05:31.493Z",
        "modifiedTime": "2025-10-16T10:05:43.287Z",
        "shared": False,
        "ownedByMe": True,
        "size": "1673"
    },
    {
        "parents": [
        "0AJl3zNrPbzEFUk9PVA"
        ],
        "capabilities": {
        "canCopy": False,
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
        "id": "1BZ18zfDtsNJ4MdQR1A_4nJWZEY7Hptgu",
        "name": "Test Folder",
        "mimeType": "application/vnd.google-apps.folder",
        "starred": False,
        "trashed": False,
        "webViewLink": "https://drive.google.com/drive/folders/1BZ18zfDtsNJ4MdQR1A_4nJWZEY7Hptgu",
        "iconLink": "https://drive-thirdparty.googleusercontent.com/16/type/application/vnd.google-apps.folder",
        "hasThumbnail": False,
        "viewedByMeTime": "2025-10-21T10:07:58.234Z",
        "createdTime": "2025-10-16T09:53:00.993Z",
        "modifiedTime": "2025-10-16T09:53:00.993Z",
        "shared": False,
        "ownedByMe": True
    },
    {
        "capabilities": {
        "canCopy": False,
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
        "id": "1BYCglBzu9CoxaAlGaO-kCSvt4U1bJB7u",
        "name": "SW7 Gruppe Drive",
        "mimeType": "application/vnd.google-apps.folder",
        "starred": False,
        "trashed": False,
        "webViewLink": "https://drive.google.com/drive/folders/1BYCglBzu9CoxaAlGaO-kCSvt4U1bJB7u",
        "iconLink": "https://drive-thirdparty.googleusercontent.com/16/type/application/vnd.google-apps.folder+shared",
        "hasThumbnail": False,
        "viewedByMeTime": "2025-10-10T10:57:49.920Z",
        "createdTime": "2025-09-03T06:38:06.970Z",
        "modifiedTime": "2025-09-08T08:21:04.865Z",
        "shared": True,
        "ownedByMe": False
    },
    {
        "parents": [
        "0AJl3zNrPbzEFUk9PVA"
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
        "id": "1cfqpSKpVcuCDC3UnNL2RKodnVOtB-kv5",
        "name": "Introduction to Compiler Design.pdf",
        "mimeType": "application/pdf",
        "starred": False,
        "trashed": False,
        "webContentLink": "https://drive.google.com/uc?id=1cfqpSKpVcuCDC3UnNL2RKodnVOtB-kv5&export=download",
        "webViewLink": "https://drive.google.com/file/d/1cfqpSKpVcuCDC3UnNL2RKodnVOtB-kv5/view?usp=drivesdk",
        "iconLink": "https://drive-thirdparty.googleusercontent.com/16/type/application/pdf",
        "hasThumbnail": True,
        "viewedByMeTime": "2025-10-24T12:15:14.774Z",
        "createdTime": "2025-10-24T12:15:14.774Z",
        "modifiedTime": "2024-02-07T11:58:07.000Z",
        "shared": False,
        "ownedByMe": True,
        "originalFilename": "Introduction to Compiler Design.pdf",
        "size": "7933431"
    }
    ]

    onedrive_test_files = [
    {
        "@microsoft.graph.downloadUrl": "https://my.microsoftpersonalcontent.com/personal/bde856357e96adb7/_layouts/15/download.aspx?UniqueId=a667d905-bb17-4f02-b22d-c8beb5750e8c&Translate=false&tempauth=v1e.eyJzaXRlaWQiOiI5MzdhMGEwMC0wYWQ3LTQwNDYtYjc4YS02ZmY4ZmY5MDQ1Y2MiLCJhcHBfZGlzcGxheW5hbWUiOiJQNyIsImFwcGlkIjoiOTE1NWYzZjQtOTE5NS00YWVkLWI4NWYtZTkzODNmNWE1YzI4IiwiYXVkIjoiMDAwMDAwMDMtMDAwMC0wZmYxLWNlMDAtMDAwMDAwMDAwMDAwL215Lm1pY3Jvc29mdHBlcnNvbmFsY29udGVudC5jb21AOTE4ODA0MGQtNmM2Ny00YzViLWIxMTItMzZhMzA0YjY2ZGFkIiwiZXhwIjoiMTc2MTMxMzU0NiJ9.letSh1l5ttdd69PqR_abVEJgpqT3Ig8oS6vAhnwI0Cso2aA8VF6JftFKr7zFnolmvKcMucnLUfeWncaPT-l5-AgxiUmFdHEhagEpIQoOVb1xjcW1mbeaJKmCkv9fRqlBToubjK9Bs0jx_NxLrdvohc7UsNARmlYmMVfy9fwcsAbWW1s77d6_aeYQoQlPh0OYYKReh3HHp0gJXHrK24U8OfNp-8vfWlijEQ-ON9vrSivB8pz4_E05YWzM_hKGcmonIUPALdL4a5Edn48evUuEgy_1f8n2Bx1dbdBmn_taBF81YFYHpGaDUrsI1V0aY9oM61KAnIgm-fuK0KUn3GOdy6i0oy5Z6v4IHkbyLaWp623jlZy7_iQeshU3PyU4mZRddOucBJvnvVhEebmaVuCj9mXtU_1sY21eKf4NtrFikPyiFJYYQV-HctkqPTbTtnLe._1iorB-qj4J-oiTbmhFyM0A7aiC-77X9o7ga-OhPZyg&ApiVersion=2.0",
        "createdDateTime": "2025-10-10T12:56:05Z",
        "eTag": "\"{A667D905-BB17-4F02-B22D-C8BEB5750E8C},1\"",
        "id": "BDE856357E96ADB7!sa667d905bb174f02b22dc8beb5750e8c",
        "lastModifiedDateTime": "2025-10-10T12:56:05Z",
        "name": "Document.docx",
        "webUrl": "https://onedrive.live.com/personal/bde856357e96adb7/_layouts/15/doc.aspx?resid=a667d905-bb17-4f02-b22d-c8beb5750e8c&cid=bde856357e96adb7",
        "cTag": "\"c:{A667D905-BB17-4F02-B22D-C8BEB5750E8C},1\"",
        "size": 0,
        "createdBy": {
        "user": {
            "email": "p7swtest1@gmail.com",
            "id": "BDE856357E96ADB7",
            "displayName": "p7sw test1"
        }
        },
        "lastModifiedBy": {
        "user": {
            "email": "p7swtest1@gmail.com",
            "id": "BDE856357E96ADB7",
            "displayName": "p7sw test1"
        }
        },
        "parentReference": {
        "driveType": "personal",
        "driveId": "BDE856357E96ADB7",
        "id": "BDE856357E96ADB7!sea8cc6beffdb43d7976fbc7da445c639",
        "name": "Documents",
        "path": "/drive/root:",
        "siteId": "937a0a00-0ad7-4046-b78a-6ff8ff9045cc"
        },
        "file": {
        "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "hashes": {
            "quickXorHash": "AAAAAAAAAAAAAAAAAAAAAAAAAAA="
        }
        },
        "fileSystemInfo": {
        "createdDateTime": "2025-10-10T12:56:05Z",
        "lastModifiedDateTime": "2025-10-10T12:56:05Z"
        }
    },
    {
        "@microsoft.graph.downloadUrl": "https://my.microsoftpersonalcontent.com/personal/bde856357e96adb7/_layouts/15/download.aspx?UniqueId=f1498202-2725-4d34-bb53-4ef4144d01fc&Translate=false&tempauth=v1e.eyJzaXRlaWQiOiI5MzdhMGEwMC0wYWQ3LTQwNDYtYjc4YS02ZmY4ZmY5MDQ1Y2MiLCJhcHBfZGlzcGxheW5hbWUiOiJQNyIsImFwcGlkIjoiOTE1NWYzZjQtOTE5NS00YWVkLWI4NWYtZTkzODNmNWE1YzI4IiwiYXVkIjoiMDAwMDAwMDMtMDAwMC0wZmYxLWNlMDAtMDAwMDAwMDAwMDAwL215Lm1pY3Jvc29mdHBlcnNvbmFsY29udGVudC5jb21AOTE4ODA0MGQtNmM2Ny00YzViLWIxMTItMzZhMzA0YjY2ZGFkIiwiZXhwIjoiMTc2MTMxMzU0NiJ9.uYW5bwXKmbDdFwBpVJQ9uJJDpfkLTLxERmn-VFCy31m5dT3E_ugPsJhkuDyeCWLlsdJZ8Cf7D8Ou9ul7wdyFEK18KgIklki1oFGezlD61oIdRuqiV7JwgTdmsYP3nVppFTsdVXTMNt5eX6XjvDn6WN1oansOsdIM6ZamKha-OdFwNUS55xKL1vzsx5y0RDsM5P46ynTRW1SJZBdPN_PMp237qbLimUqmHgpAFUEwGGCmbFQ1xz7hxeWkUnLu0mMrtOiJ8GpBh9Rl5L5j7BqXVpbh6S8KGbqdDwoTEJKxT8amavATUcbX8Zwjd6KR3oSSOknggyUm62OdtwV3Qxh7sdYN7MH1CYxwIzuz7eqKuQfesUIyGa4xSf98OrvnhvFrV5nL8pikrHimqrEFiSboqSATB346uZcjWg13qVhmYtkLVkFZjLNzeGHMByUljtqQ.BjdhU_YpAkIRRKHEo0ag0Sf0yGvx2Oc0H6gh_vmRd7w&ApiVersion=2.0",
        "createdDateTime": "2025-10-10T12:56:59Z",
        "eTag": "\"{F1498202-2725-4D34-BB53-4EF4144D01FC},1\"",
        "id": "BDE856357E96ADB7!sf149820227254d34bb534ef4144d01fc",
        "lastModifiedDateTime": "2025-10-10T12:56:59Z",
        "name": "Document1.docx",
        "webUrl": "https://onedrive.live.com/personal/bde856357e96adb7/_layouts/15/doc.aspx?resid=f1498202-2725-4d34-bb53-4ef4144d01fc&cid=bde856357e96adb7",
        "cTag": "\"c:{F1498202-2725-4D34-BB53-4EF4144D01FC},1\"",
        "size": 0,
        "createdBy": {
        "user": {
            "email": "p7swtest1@gmail.com",
            "id": "BDE856357E96ADB7",
            "displayName": "p7sw test1"
        }
        },
        "lastModifiedBy": {
        "user": {
            "email": "p7swtest1@gmail.com",
            "id": "BDE856357E96ADB7",
            "displayName": "p7sw test1"
        }
        },
        "parentReference": {
        "driveType": "personal",
        "driveId": "BDE856357E96ADB7",
        "id": "BDE856357E96ADB7!sea8cc6beffdb43d7976fbc7da445c639",
        "name": "Documents",
        "path": "/drive/root:",
        "siteId": "937a0a00-0ad7-4046-b78a-6ff8ff9045cc"
        },
        "file": {
        "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "hashes": {
            "quickXorHash": "AAAAAAAAAAAAAAAAAAAAAAAAAAA="
        }
        },
        "fileSystemInfo": {
        "createdDateTime": "2025-10-10T12:56:59Z",
        "lastModifiedDateTime": "2025-10-10T12:56:59Z"
        }
    },
    {
        "@microsoft.graph.downloadUrl": "https://my.microsoftpersonalcontent.com/personal/bde856357e96adb7/_layouts/15/download.aspx?UniqueId=b369d2c0-247f-48c5-8b7c-228389c36b6c&Translate=false&tempauth=v1e.eyJzaXRlaWQiOiI5MzdhMGEwMC0wYWQ3LTQwNDYtYjc4YS02ZmY4ZmY5MDQ1Y2MiLCJhcHBfZGlzcGxheW5hbWUiOiJQNyIsImFwcGlkIjoiOTE1NWYzZjQtOTE5NS00YWVkLWI4NWYtZTkzODNmNWE1YzI4IiwiYXVkIjoiMDAwMDAwMDMtMDAwMC0wZmYxLWNlMDAtMDAwMDAwMDAwMDAwL215Lm1pY3Jvc29mdHBlcnNvbmFsY29udGVudC5jb21AOTE4ODA0MGQtNmM2Ny00YzViLWIxMTItMzZhMzA0YjY2ZGFkIiwiZXhwIjoiMTc2MTMxMzU0NiJ9.jCBFJnsT1BFbcnIAjJa7bNG7yDit1pRxvk8pAPPPDeyKu-QADpS19z-37cJxH44LcRlNwtp_tiUFzbbA2qsmAzL5AcakL0XH4w-rUKLeOtNS_ta_vdVEA1n50RJ8RRqjmTfG0QR_NfhnRU0NRumI5rYqkBIP2dN_xcSAmFNluOMUFWRoteHiiEXq2VCxXttRaso34mJ-tfF4whRVBrmzwX2MvfW9uwVRUF1Pvks-t1uVrN9sFz2eQiO-nauMnb92TKxpHhuZPcHUIyvxLG0Iy4I4FERE1nBPrCbHfm8Fjl4pXytlaxX1TrZCWdV5h-yNm7sGVesm1eh6l-xxj0Nf_kyQ0_zKxyaKRnqE6YMUqt0XIO_7HGxe3IpXSHu-6KRX3hLWuvAQtWEOz04WEOMpGfmoPr_Efknn5aEaborPto3PI2BJUvhjRM9sarW-drPI.w4QbUQOZHBRsuNnPwqrhoY6dc82QSLVOv_70rMtpwmo&ApiVersion=2.0",
        "createdDateTime": "2025-10-03T10:38:31Z",
        "eTag": "\"{B369D2C0-247F-48C5-8B7C-228389C36B6C},1\"",
        "id": "BDE856357E96ADB7!sb369d2c0247f48c58b7c228389c36b6c",
        "lastModifiedDateTime": "2025-10-03T10:38:31Z",
        "name": "Kom godt i gang med OneDrive.pdf",
        "webUrl": "https://onedrive.live.com?cid=BDE856357E96ADB7&id=BDE856357E96ADB7!sb369d2c0247f48c58b7c228389c36b6c",
        "cTag": "\"c:{B369D2C0-247F-48C5-8B7C-228389C36B6C},1\"",
        "size": 1071905,
        "createdBy": {
        "application": {
            "id": "00000000-0000-0000-0000-000000048beb",
            "displayName": "i:0i.t|ms.sp.ext|00000000-0000-0000-0000-000000048beb@9188040d-6c67-4c5b-b112-36a304b66dad"
        },
        "user": {
            "email": "p7swtest1@gmail.com",
            "id": "BDE856357E96ADB7",
            "displayName": "p7sw test1"
        }
        },
        "lastModifiedBy": {
        "application": {
            "id": "00000000-0000-0000-0000-000000048beb",
            "displayName": "i:0i.t|ms.sp.ext|00000000-0000-0000-0000-000000048beb@9188040d-6c67-4c5b-b112-36a304b66dad"
        },
        "user": {
            "email": "p7swtest1@gmail.com",
            "id": "BDE856357E96ADB7",
            "displayName": "p7sw test1"
        }
        },
        "parentReference": {
        "driveType": "personal",
        "driveId": "BDE856357E96ADB7",
        "id": "BDE856357E96ADB7!sea8cc6beffdb43d7976fbc7da445c639",
        "name": "Documents",
        "path": "/drive/root:",
        "siteId": "937a0a00-0ad7-4046-b78a-6ff8ff9045cc"
        },
        "file": {
        "mimeType": "application/pdf",
        "hashes": {
            "quickXorHash": "kM6KTOwm5LIb9jFDxVuoX8tcgsk="
        }
        },
        "fileSystemInfo": {
        "createdDateTime": "2025-10-03T10:38:31Z",
        "lastModifiedDateTime": "2025-10-03T10:38:31Z"
        }
    },
    {
        "@microsoft.graph.downloadUrl": "https://my.microsoftpersonalcontent.com/personal/bde856357e96adb7/_layouts/15/download.aspx?UniqueId=e3039fb0-28bc-4299-bc5c-f75da060c2c6&Translate=false&tempauth=v1e.eyJzaXRlaWQiOiI5MzdhMGEwMC0wYWQ3LTQwNDYtYjc4YS02ZmY4ZmY5MDQ1Y2MiLCJhcHBfZGlzcGxheW5hbWUiOiJQNyIsImFwcGlkIjoiOTE1NWYzZjQtOTE5NS00YWVkLWI4NWYtZTkzODNmNWE1YzI4IiwiYXVkIjoiMDAwMDAwMDMtMDAwMC0wZmYxLWNlMDAtMDAwMDAwMDAwMDAwL215Lm1pY3Jvc29mdHBlcnNvbmFsY29udGVudC5jb21AOTE4ODA0MGQtNmM2Ny00YzViLWIxMTItMzZhMzA0YjY2ZGFkIiwiZXhwIjoiMTc2MTMxMzU0NiJ9.h_88PFUx0OzF18ifll6V80-TIPtgtHCzNvERjSlCG6BVD2B3DvJyw0p8fcI6NF6UwUUI6YaCtU71C7frVLK1dBlsukQpxAkdjc9VWiSxdfu7yIbzyWuFKdFuQTw16Co3Jo0vQYG9tgJOUa3HGs4qgoQjNBrfDHnw7kkH_tOBYJ-53JdAD-onyY6qEH_MQ2RlsWDXXyYJ0c9s0TnGbVn51kfaRBXOa5fdkb-1M1sPS58rC4FZ05F3k4VrihedHV8rdqV8c9D2p5GbWb6vb5AYWnGtTCpH3T-ovyr-gYVGQ66VDHUZUjtdiOt2OErqtKEo9PuMg6pBKL3za2SCaQpQQLY3ich_tNOaWyfu2zSjbWkJGkZJ2jTE8ctz07nwvBGrAFe_cCTCEAgKsXWlFut1rOfuPNqWncSOfHM4MgKonIdCCjbyYIzIz3hitQiM3kr2.KpytYIMgVrkGbWm1eOp-sH2DbOJvW7PctUG4WyNV4b0&ApiVersion=2.0",
        "createdDateTime": "2025-10-24T12:45:05Z",
        "eTag": "\"{E3039FB0-28BC-4299-BC5C-F75DA060C2C6},4\"",
        "id": "BDE856357E96ADB7!se3039fb028bc4299bc5cf75da060c2c6",
        "lastModifiedDateTime": "2025-10-24T12:45:16Z",
        "name": "Onedrive test 1.docx",
        "webUrl": "https://onedrive.live.com/personal/bde856357e96adb7/_layouts/15/doc.aspx?resid=e3039fb0-28bc-4299-bc5c-f75da060c2c6&cid=bde856357e96adb7",
        "cTag": "\"c:{E3039FB0-28BC-4299-BC5C-F75DA060C2C6},3\"",
        "size": 10568,
        "createdBy": {
        "user": {
            "email": "p7swtest1@gmail.com",
            "id": "BDE856357E96ADB7",
            "displayName": "p7sw test1"
        }
        },
        "lastModifiedBy": {
        "user": {
            "email": "p7swtest1@gmail.com",
            "id": "BDE856357E96ADB7",
            "displayName": "p7sw test1"
        }
        },
        "parentReference": {
        "driveType": "personal",
        "driveId": "BDE856357E96ADB7",
        "id": "BDE856357E96ADB7!sea8cc6beffdb43d7976fbc7da445c639",
        "name": "Documents",
        "path": "/drive/root:",
        "siteId": "937a0a00-0ad7-4046-b78a-6ff8ff9045cc"
        },
        "file": {
        "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "hashes": {
            "quickXorHash": "Ahz4V/ImZe/yqKJSOy4aQzsfkL8=",
            "sha1Hash": "98F764D76668838C4212604C68BD30DBCB842829",
            "sha256Hash": "0CB5B3F302285377A2F93FECA531348E11C46DA5AF1E379DD6C2EE7811C85191"
        }
        },
        "fileSystemInfo": {
        "createdDateTime": "2025-10-24T12:45:05Z",
        "lastModifiedDateTime": "2025-10-24T12:45:16Z"
        }
    },
    {
        "@microsoft.graph.downloadUrl": "https://my.microsoftpersonalcontent.com/personal/bde856357e96adb7/_layouts/15/download.aspx?UniqueId=7a85de28-00f5-4f08-860e-81db7be7ee20&Translate=false&tempauth=v1e.eyJzaXRlaWQiOiI5MzdhMGEwMC0wYWQ3LTQwNDYtYjc4YS02ZmY4ZmY5MDQ1Y2MiLCJhcHBfZGlzcGxheW5hbWUiOiJQNyIsImFwcGlkIjoiOTE1NWYzZjQtOTE5NS00YWVkLWI4NWYtZTkzODNmNWE1YzI4IiwiYXVkIjoiMDAwMDAwMDMtMDAwMC0wZmYxLWNlMDAtMDAwMDAwMDAwMDAwL215Lm1pY3Jvc29mdHBlcnNvbmFsY29udGVudC5jb21AOTE4ODA0MGQtNmM2Ny00YzViLWIxMTItMzZhMzA0YjY2ZGFkIiwiZXhwIjoiMTc2MTMxMzU0NiJ9.jz1JuHc8hIB7IX2EOY4k-P60AsIFBKpQMXvTsKWZZgG1hohDSayeuvU9s-CPrgY94iV7Aa8LtLIwST-w6cGGWOAacbU-6AXzHNWVvrUSmY96OTgkdq9nInknRBltsDvyZoYin_pUSaLQkavun3BEFvVykWrCLP0itEY-QB4zTpN6XSzwlaI9hfbbrNBs-nB6pq6ThCtRmzFZnydBEPRMXMMKWlyuBGrYxK58BO7O38OqxIZLD8io1d8tx6xHYsqfnYKnPsTZUZc_0BONq3QWYWAwzHCgtQYn7FAGH-WRQ4OfKoJr7F-pK7mvSWcylQtlpzAE5LfIUqtfaFnwKuRFLGB3_QbWlOt2RaFohQH9HVIY0mKoY_Aaek0Js0c-yYcYOcYua4U48kZzzEpqF9rUyQWQaJ2FMJWT0dbQmu9r8bT-XoufVPDf1_fTG-CNEnU2.xWoWv6sEs05riIG6UXOfBIUqKpWF2fNQvG8HgGsEUrk&ApiVersion=2.0",
        "createdDateTime": "2025-10-24T12:44:57Z",
        "eTag": "\"{7A85DE28-00F5-4F08-860E-81DB7BE7EE20},1\"",
        "id": "BDE856357E96ADB7!s7a85de2800f54f08860e81db7be7ee20",
        "lastModifiedDateTime": "2025-10-24T12:44:57Z",
        "name": "Operating_Systems_three_easy_pieces.pdf",
        "webUrl": "https://onedrive.live.com?cid=BDE856357E96ADB7&id=BDE856357E96ADB7!s7a85de2800f54f08860e81db7be7ee20",
        "cTag": "\"c:{7A85DE28-00F5-4F08-860E-81DB7BE7EE20},1\"",
        "size": 5658674,
        "createdBy": {
        "user": {
            "email": "p7swtest1@gmail.com",
            "id": "BDE856357E96ADB7",
            "displayName": "p7sw test1"
        }
        },
        "lastModifiedBy": {
        "user": {
            "email": "p7swtest1@gmail.com",
            "id": "BDE856357E96ADB7",
            "displayName": "p7sw test1"
        }
        },
        "parentReference": {
        "driveType": "personal",
        "driveId": "BDE856357E96ADB7",
        "id": "BDE856357E96ADB7!sea8cc6beffdb43d7976fbc7da445c639",
        "name": "Documents",
        "path": "/drive/root:",
        "siteId": "937a0a00-0ad7-4046-b78a-6ff8ff9045cc"
        },
        "file": {
        "mimeType": "application/pdf",
        "hashes": {
            "quickXorHash": "26eYa+eLOZsTePXPRVok27HPdnQ="
        }
        },
        "fileSystemInfo": {
        "createdDateTime": "2025-10-24T12:44:57Z",
        "lastModifiedDateTime": "2025-10-24T12:44:57Z"
        }
    },
    {
        "@microsoft.graph.downloadUrl": "https://my.microsoftpersonalcontent.com/personal/bde856357e96adb7/_layouts/15/download.aspx?UniqueId=ec363614-9bc9-4e1c-ae2b-5169d38082cc&Translate=false&tempauth=v1e.eyJzaXRlaWQiOiI5MzdhMGEwMC0wYWQ3LTQwNDYtYjc4YS02ZmY4ZmY5MDQ1Y2MiLCJhcHBfZGlzcGxheW5hbWUiOiJQNyIsImFwcGlkIjoiOTE1NWYzZjQtOTE5NS00YWVkLWI4NWYtZTkzODNmNWE1YzI4IiwiYXVkIjoiMDAwMDAwMDMtMDAwMC0wZmYxLWNlMDAtMDAwMDAwMDAwMDAwL215Lm1pY3Jvc29mdHBlcnNvbmFsY29udGVudC5jb21AOTE4ODA0MGQtNmM2Ny00YzViLWIxMTItMzZhMzA0YjY2ZGFkIiwiZXhwIjoiMTc2MTMxMzU0NiJ9.nGWhHdgHiIr80xPuS7ahXHqm5pRq05Kbld1tGf6GhC3wjWhvrZUpRoLXBg5oEQEv1qUzdQZoPIiOmsmFg_LnuWj00odXUTB0Lz4WMqWgrXeAtSDtDg1-EIzM46ltjCZIkSE67e_chX-27eUKDtqB-bDw9dXEUwFwcYgYKU180ZMfW5ZW48BFknuyHFnHYvLu6DiwwYMdQ6P7JQoQQVd5ey-gSKXxk8UW5iD6hTwfb2WyTN8WlluLwf8at4pMSJHNsOCGfetbBj1efwhhZbuSLIUL46eaExdiZ3ldhRIhbFZltu77KWovgUWUAEhtxsCem3JN6azAUDCtLNoNqc2DFPRLRZeR1U9KLmqz8m3Avl_d-KAAtqhBWVtn4opVc-JDwYdiRG3xteTtX4RlRUqqWk0VvQ2oCgfe2gPOkCFb_YCmzYUbUqVC6X5hXbfsmciv.u3BF99COqt6fJEHuKsDqsHhpXv8PrDLyj9DRaOiPZbo&ApiVersion=2.0",
        "createdDateTime": "2025-10-17T12:45:00Z",
        "eTag": "\"{EC363614-9BC9-4E1C-AE2B-5169D38082CC},4\"",
        "id": "BDE856357E96ADB7!sec3636149bc94e1cae2b5169d38082cc",
        "lastModifiedDateTime": "2025-10-17T12:45:22Z",
        "name": "Random Document.docx",
        "webUrl": "https://onedrive.live.com/personal/bde856357e96adb7/_layouts/15/doc.aspx?resid=ec363614-9bc9-4e1c-ae2b-5169d38082cc&cid=bde856357e96adb7",
        "cTag": "\"c:{EC363614-9BC9-4E1C-AE2B-5169D38082CC},3\"",
        "size": 10560,
        "createdBy": {
        "user": {
            "email": "p7swtest1@gmail.com",
            "id": "BDE856357E96ADB7",
            "displayName": "p7sw test1"
        }
        },
        "lastModifiedBy": {
        "user": {
            "email": "p7swtest1@gmail.com",
            "id": "BDE856357E96ADB7",
            "displayName": "p7sw test1"
        }
        },
        "parentReference": {
        "driveType": "personal",
        "driveId": "BDE856357E96ADB7",
        "id": "BDE856357E96ADB7!sea8cc6beffdb43d7976fbc7da445c639",
        "name": "Documents",
        "path": "/drive/root:",
        "siteId": "937a0a00-0ad7-4046-b78a-6ff8ff9045cc"
        },
        "file": {
        "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "hashes": {
            "quickXorHash": "JaMjH/K+NNHkoh6DmtC2SN+V4QE=",
            "sha1Hash": "8F5C138C23D97D583D65127D42A46D528178A5EA",
            "sha256Hash": "2560977AC0915D774CA6FBB1C275BF5E2AD679C34E6B66112F79C542667345DD"
        }
        },
        "fileSystemInfo": {
        "createdDateTime": "2025-10-17T12:45:00Z",
        "lastModifiedDateTime": "2025-10-17T12:45:22Z"
        }
    },
    {
        "@microsoft.graph.downloadUrl": "https://my.microsoftpersonalcontent.com/personal/bde856357e96adb7/_layouts/15/download.aspx?UniqueId=6232e8b5-2a02-49af-83d0-8cded5b91395&Translate=false&tempauth=v1e.eyJzaXRlaWQiOiI5MzdhMGEwMC0wYWQ3LTQwNDYtYjc4YS02ZmY4ZmY5MDQ1Y2MiLCJhcHBfZGlzcGxheW5hbWUiOiJQNyIsImFwcGlkIjoiOTE1NWYzZjQtOTE5NS00YWVkLWI4NWYtZTkzODNmNWE1YzI4IiwiYXVkIjoiMDAwMDAwMDMtMDAwMC0wZmYxLWNlMDAtMDAwMDAwMDAwMDAwL215Lm1pY3Jvc29mdHBlcnNvbmFsY29udGVudC5jb21AOTE4ODA0MGQtNmM2Ny00YzViLWIxMTItMzZhMzA0YjY2ZGFkIiwiZXhwIjoiMTc2MTMxMzU0NiJ9.HcZQ0ndPvgdb36tr2s7za9wLhHMmBV-anAcv6KCPYZJB9f68aHynyurHmwbVHKOR8xPVPHBFjSbnNidVzK3YczgIfA-EeC1yUHFBmQX-_kV6Ipa949hQ1G5xrKUEmIPfXTmuGT9wn3fwlFLBed5plDYi574KXpy4Dg5lvyQskQ9MIVx0BZqbcxh7_0eHFr8uL_bmzImCdZT0f22yfqjI9P3D9U-VSuWVmoWwyar5HcR9Of5rwGjJB6ZFea8L7byCz6v84l4SlNGnxdol6Fxlsju23wXoJ9S0wIb3nKrcHYvSKYZ5l7I3qqf-qfF9xlRk0gc5bW7rMVIvraNbCZYgcKhP-QUGdzk4gnPbz5xXNHcx81ecp8j_RDCvQTJ3ODaGwUIjC9MEkglKcrzVqav_89H-3j-yURCyk2wjAIFY6HKXaoq_MSNR4A_DIZcvpgd1.l_W59m5uReaHCh7RGEcZBa-57OwI65NfrjmJlBiDkPk&ApiVersion=2.0",
        "createdDateTime": "2025-10-10T12:57:23Z",
        "eTag": "\"{6232E8B5-2A02-49AF-83D0-8CDED5B91395},5\"",
        "id": "BDE856357E96ADB7!s6232e8b52a0249af83d08cded5b91395",
        "lastModifiedDateTime": "2025-10-10T12:57:34Z",
        "name": "Random notes.docx",
        "webUrl": "https://onedrive.live.com/personal/bde856357e96adb7/_layouts/15/doc.aspx?resid=6232e8b5-2a02-49af-83d0-8cded5b91395&cid=bde856357e96adb7",
        "cTag": "\"c:{6232E8B5-2A02-49AF-83D0-8CDED5B91395},4\"",
        "size": 11339,
        "createdBy": {
        "user": {
            "email": "p7swtest1@gmail.com",
            "id": "BDE856357E96ADB7",
            "displayName": "p7sw test1"
        }
        },
        "lastModifiedBy": {
        "user": {
            "email": "p7swtest1@gmail.com",
            "id": "BDE856357E96ADB7",
            "displayName": "p7sw test1"
        }
        },
        "parentReference": {
        "driveType": "personal",
        "driveId": "BDE856357E96ADB7",
        "id": "BDE856357E96ADB7!sea8cc6beffdb43d7976fbc7da445c639",
        "name": "Documents",
        "path": "/drive/root:",
        "siteId": "937a0a00-0ad7-4046-b78a-6ff8ff9045cc"
        },
        "file": {
        "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "hashes": {
            "quickXorHash": "qdSPqJsJIiPyIdW0N2Rm2Cxyh6g=",
            "sha1Hash": "910A412ED04D82550BAC862AC799F511D3E68172",
            "sha256Hash": "82FB2EAF6F756525BBB7FBF8F29B5029787020379A6733E5EE75DD980AAC3452"
        }
        },
        "fileSystemInfo": {
        "createdDateTime": "2025-10-10T12:57:23Z",
        "lastModifiedDateTime": "2025-10-10T12:57:34Z"
        }
    }
    ]

    for file in dropbox_test_files:
        update_or_create_file_dropbox(file, service_dropbox)

    file_by_id = {file["id"]: file for file in google_drive_test_files}

    for file in google_drive_test_files:
        # Skip non-files (folders, shortcuts, etc)
        mime_type = file.get("mimeType", "")
        if (
            mime_type == "application/vnd.google-apps.folder"
            or mime_type == "application/vnd.google-apps.shortcut"
            or mime_type == "application/vnd.google-apps.drive-sdk"
        ):  # https://developers.google.com/workspace/drive/api/guides/mime-types
            continue
        update_or_create_file_google_drive(file, service_google_drive, file_by_id)

    for file in onedrive_test_files:
        update_or_create_file_onedrive(file, service_onedrive)

    response = sync_files_client_fixture.get(
                f"/?user_id={user_id}",
                headers={"x-internal-auth": os.getenv("INTERNAL_API_KEY")},
                )

    check.equal(response.status_code, 200)

    dropbox_files = get_files_by_service(service_dropbox)
    google_drive_files = get_files_by_service(service_google_drive)
    onedrive_files = get_files_by_service(service_onedrive)

    #Check correct update Dropbox
    #Check that file has been deleted
    check.equal(any(file.serviceFileId == dropbox_test_files[2]["id"] for file in dropbox_files), False)

    #Check that the 3 other files still exists
    check.equal(any(file.serviceFileId == dropbox_test_files[0]["id"] for file in dropbox_files), True)
    check.equal(any(file.serviceFileId == dropbox_test_files[1]["id"] for file in dropbox_files), True)
    check.equal(any(file.serviceFileId == dropbox_test_files[3]["id"] for file in dropbox_files), True)

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
    check.equal(any(file.serviceFileId == google_drive_test_files[5]["id"] for file in google_drive_files), False)

    #Check that the 3 other files still exists
    check.equal(any(file.serviceFileId == google_drive_test_files[0]["id"] for file in google_drive_files), True)
    check.equal(any(file.serviceFileId == google_drive_test_files[3]["id"] for file in google_drive_files), True)
    check.equal(any(file.serviceFileId == google_drive_test_files[4]["id"] for file in google_drive_files), True)

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
    check.equal(any(file.serviceFileId == onedrive_test_files[4]["id"] for file in onedrive_files), False)

    #Check that the 3 other files still exists
    check.equal(any(file.serviceFileId == onedrive_test_files[3]["id"] for file in onedrive_files), True)
    check.equal(any(file.serviceFileId == onedrive_test_files[5]["id"] for file in onedrive_files), True)
    check.equal(any(file.serviceFileId == onedrive_test_files[6]["id"] for file in onedrive_files), True)

    for file in onedrive_files:
        #Check that name has been updated from OneDrive 1.docx to OneDrive 2.docx
        if file.serviceFileId == onedrive_test_files[3]["id"]:
            check.equal(file.name, "Onedrive test 2.docx")
        #Check that other files are unchanged
        if file.serviceFileId == onedrive_test_files[5]["id"]:
            check.equal(file.name, onedrive_test_files[5]["name"])
        if file.serviceFileId == onedrive_test_files[6]["id"]:
            check.equal(file.name, onedrive_test_files[6]["name"])
