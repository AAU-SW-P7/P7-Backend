"""Tests for the create_user endpoint."""
import os
import sys
from pathlib import Path

# # Make the local backend package importable so `from p7...` works under pytest
repo_backend = Path(__file__).resolve().parents[1]  # backend/
sys.path.insert(0, str(repo_backend))
# # Make the backend/test dir importable so you can use test_settings.py directly
sys.path.insert(0, str(repo_backend / "test"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_settings")

import django
django.setup()

import pytest
from ninja.testing import TestClient
from helpers.delete_user import (
    assert_delete_user_invalid_auth,
    assert_delete_user_invalid_user_id,
    assert_delete_user_missing_header,
    assert_delete_user_success
)
from helpers.general_helper_functions import create_x_users
from p7.delete_user.api import delete_user_router

pytestmark = pytest.mark.usefixtures("django_db_setup")
#pytestmark = pytest.mark.django_db

@pytest.fixture(name="d_user_client", scope='module', autouse=True)
def delete_user_client():
    """Fixture for creating a test client for the delete_user endpoint.
     Returns:
         TestClient: A test client for the delete_user endpoint.
     """
    return TestClient(delete_user_router)

def test_create_user_success():
    """Create 3 users."""
    create_x_users(3)

def test_delete_user_success(d_user_client): # make 3 users
    """Test creating 3 users successfully.
    params:
        d_user_client: Fixture for deleting a test client through the delete_user endpoint.
    """
    for user_number in range(3, 0, -1):  # 3 to 1
        assert_delete_user_success(d_user_client, user_number)

def test_delete_user_invalid_auth(d_user_client):
    """Test deleting a user with invalid auth token.
    params:
        d_user_client: Fixture for deleting a test client through the delete_user endpoint.
    """
    for user_number in range(3, 0, -1):  # 3 to 1
        assert_delete_user_invalid_auth(d_user_client, user_number)

def test_delete_user_missing_header(d_user_client):
    """Test deleting a user with missing headers.
    params:
        d_user_client: Fixture for deleting a test client through the delete_user endpoint.
    """
    for user_number in range(3, 0, -1):  # 3 to 1
        assert_delete_user_missing_header(d_user_client, user_number)

def test_delete_user_invalid_user_id(d_user_client):
    """Test deleting a user with invalid user_id.
    params:
        d_user_client: Fixture for deleting a test client through the delete_user endpoint.
    """
    for user_number in range(3, 0, -1):  # 3 to 1
        assert_delete_user_invalid_user_id(d_user_client, user_number)
