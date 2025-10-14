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
from p7.create_user.api import create_user_router
from helpers.create_user import (
    assert_create_user_success,
    assert_create_user_invalid_auth,
    assert_create_user_missing_header,
)

pytestmark = pytest.mark.usefixtures("django_db_setup")

@pytest.fixture(scope='module', autouse=True)
def create_user_client():
    return TestClient(create_user_router)

def test_create_user_success(create_user_client): # make 3 users
    for user_number in range(1, 3+1):  # 3 users
        assert_create_user_success(create_user_client, user_number)

def test_create_user_invalid_auth(create_user_client):
    assert_create_user_invalid_auth(create_user_client)

def test_create_user_missing_header(create_user_client):
    assert_create_user_missing_header(create_user_client)