"""Tests for getting files based on the service."""
import os
import sys
from pathlib import Path

import django

from django.utils import timezone

import pytest
from ninja.testing import TestClient
from helpers.create_user import (
    assert_create_user_success
)
from helpers.create_service import (
    assert_create_service_success
)

django.setup()

# Make the local backend package importable so `from p7...` works under pytest
repo_backend = Path(__file__).resolve().parents[1]  # backend/
sys.path.insert(0, str(repo_backend))
# Make the backend/test dir importable so you can use test_settings.py directly
sys.path.insert(0, str(repo_backend / "test"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_settings")

from p7.get_dropbox_files.api import fetch_dropbox_files_router
from p7.get_google_drive_files.api import fetch_google_drive_files_router
from p7.get_onedrive_files.api import fetch_onedrive_files_router
from p7.create_user.api import create_user_router
from p7.create_service.api import create_service_router
from repository.service import get_service
from repository.file import get_files_by_service

pytestmark = pytest.mark.usefixtures("django_db_setup")

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

    """Fixture for creating a test client for the save_file endpoint.
    Returns:
        TestClient: A test client for the save_file endpoint.
    """
    return TestClient(fetch_onedrive_files_router)


def test_get_files_by_service(
    django_db_setup,
    user_client: TestClient,
    service_client: TestClient,
):
    """Test getting files by service for Google Drive."""
    for user_id in range(1, 3+1):
        # Create users
        assert_create_user_success(user_client, user_id)

    service_count = 0
    for user_id in range(1, 3+1):
        # Create a service for each provider for each user
        #TODO: Expand with GOOGLE once the problem with access tokens is solved
        for provider in ["DROPBOX", "ONEDRIVE"]:
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

            assert_create_service_success(service_client, payload, service_count)

            service_count += 1

    # Save files for users
    # TODO: Update when Google Drive tests can be run properly
    now = timezone.now()
    files_payload = []
    file_count = 9
    service_count = 6  # 3 users * 2 services each
    for i in range(1, file_count+1):
        files_payload.append(
            {
                "serviceId": i % service_count,  # FK instance
                "serviceFileId": f"file_{i}",
                "name": f"Document {i}.txt",
                "extension": "txt",
                "downloadable": True,
                "path": f"/docs/doc{i}.txt",
                "link": f"https://example.com/files/{i}",
                "size": 1024 * i,
                "createdAt": now,
                "modifiedAt": now,
                "lastIndexed": None,
                "snippet": f"Snippet for document {i}",
                "content": f"Full content for document {i}",
            }
        )
    service_list = []
    service_list.append(get_service(1, "dropbox"))
    service_list.append(get_service(1, "microsoft-entra-id"))
    service_list.append(get_service(2, "dropbox"))
    service_list.append(get_service(2, "microsoft-entra-id"))
    service_list.append(get_service(3, "dropbox"))
    service_list.append(get_service(3, "microsoft-entra-id"))

    print(service_list)

    #Check that we can get the correct files for each service
    for service in service_list:
        files = get_files_by_service(service)
        for i, file in enumerate(files):
            assert file.serviceId.id == service.id
            assert file.serviceFileId == f"file_{service.id + service_count * i}"
            assert file.name == f"Document {service.id + service_count * i}.txt"
            assert file.path == f"/docs/doc{service.id + service_count * i}.txt"
            assert file.link == f"https://example.com/files/{service.id + service_count * i}"
            assert file.size == 1024 * (service.id + service_count * i)
            assert file.snippet == f"Snippet for document {service.id + service_count * i}"
            assert file.content == f"Full content for document {service.id + service_count * i}"
