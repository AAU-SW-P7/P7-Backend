"""Tests for search_files_by_name functionality."""

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


from helpers.search_filename import (
    assert_search_filename_invalid_auth,
    assert_search_filename_missing_header,
    assert_search_filename_missing_search_string,
    assert_search_filename_missing_userid,
)
from helpers.create_user import assert_create_user_success
from p7.search_files_by_filename.api import fetch_database_files_by_filename_router
from p7.create_user.api import create_user_router


pytestmark = pytest.mark.usefixtures("django_db_setup")


@pytest.fixture(name="user_client", scope='module', autouse=True)
def create_user_client():
    """Fixture for creating a test client for the fetch_database_files_by_filename endpoint.
     Returns:
         TestClient: A test client for the fetch_database_files_by_filenamer endpoint.
     """
    return TestClient(create_user_router)

@pytest.fixture(name="test_client", scope='module', autouse=True)
def create_test_client():
    """Fixture for creating a test client for the fetch_database_files_by_filename endpoint.
     Returns:
         TestClient: A test client for the fetch_database_files_by_filenamer endpoint.
     """
    return TestClient(fetch_database_files_by_filename_router)

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
