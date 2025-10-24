"""Tests for search_files_by_name functionality."""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

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


from helpers.search_filename import (
    assert_search_filename_invalid_auth,
    assert_search_filename_missing_header,
    assert_search_filename_missing_search_string,
    assert_search_filename_missing_userid,
)
#ESlint: disable=C0411
from helpers.create_user import assert_create_user_success
from repository.models import File, Service, User
from p7.search_files_by_filename.api import search_files_by_filename_router
from p7.create_user.api import create_user_router

pytestmark = pytest.mark.usefixtures("django_db_setup")

@pytest.fixture(name="search_file", scope='module', autouse=True)
def create_search_file_client():
    """Fixture for creating a test client for the search_files_by_filename_router endpoint.
     Returns:
         TestClient: A test client for the search_files_by_filename_router endpoint.
    """
    return TestClient(search_files_by_filename_router)

@pytest.fixture(name="user_client", scope='module', autouse=True)
def create_user_client():
    """Fixture for creating a test client for the search_files_by_filename_router endpoint.
     Returns:
         TestClient: A test client for the search_files_by_filename_router endpoint.
     """
    return TestClient(create_user_router)

@pytest.fixture(name="test_client", scope='module', autouse=True)
def create_test_client():
    """Fixture for creating a test client for the search_files_by_filename_router endpoint.
     Returns:
         TestClient: A test client for the search_files_by_filename_router endpoint.
     """
    return TestClient(search_files_by_filename_router)

def test_create_user_success(user_client):
    """Test creating 3 users successfully.
    params:
        user_client: Fixture for creating a test client for the create_user endpoint.
    """
    for user_number in range(1, 3+1):  # 3 users
        assert_create_user_success(user_client, user_number)

def test_missing_user_id(test_client):
    """Test searching files with invalid user ID parameter.
    params:
        client: Test client to make requests.
    """
    assert_search_filename_missing_userid(test_client, "sample_search")

def test_missing_auth_header(test_client):
    """Test searching files with missing auth header.
    params:
        client: Test client to make requests.
    """
    for user_number in range(1, 3+1):  # 3 users
        assert_search_filename_missing_header(test_client, user_number, "sample_search")

def test_invalid_auth_header(test_client):
    """Test searching files with invalid auth header.
    params:
        client: Test client to make requests.
    """
    for user_number in range(1, 3+1):  # 3 users
        assert_search_filename_invalid_auth(test_client, user_number, "sample_search")

def test_search_filename_missing_search_string(test_client):
    """Test searching files with missing search string parameter.
    params:
        client: Test client to make requests.
    """
    for user_number in range(1, 3+1):  # 3 users
        assert_search_filename_missing_search_string(test_client, user_number)


def test_search_filename_end_to_end(search_file):
    """Test searching files by filename end-to-end.
    params:
        search_file: Fixture for creating a test client
                     for the search_files_by_filename_router endpoint.
    """
    user1 = User.objects.create()
    service1 = Service.objects.create(
        userId=user1,
        oauthType="GOOGLE",
        oauthToken="fake-token-1",
        accessToken="fake-access-1",
        accessTokenExpiration=datetime.now() + timedelta(days=365),
        refreshToken="fake-refresh-1",
        name="google",
        accountId="acc1",
        email="user1@example.com",
        scopeName="files.read",
    )
    File.objects.create(
        serviceId=service1,
        serviceFileId="file-1",
        name="report-user1.docx",
        extension="docx",
        downloadable=True,
        path="/report-user1.docx",
        link="http://dropbox/link1",
        size=1024,
        createdAt=datetime.now(),
        modifiedAt=datetime.now(),
    )

    # Perform a search
    response = search_file.get(
        f"/?user_id={user1.id}&search_string=report",
        headers={"x-internal-auth": "p7"}
    )

    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert "files" in data
    assert len(data["files"]) == 1
    assert data["files"][0]["name"] == "report-user1.docx"
