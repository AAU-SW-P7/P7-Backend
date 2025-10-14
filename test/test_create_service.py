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
from p7.create_service.api import create_service_router
from helpers.create_user import (
    assert_create_user_success,
    assert_create_user_invalid_auth,
    assert_create_user_missing_header,
)
from helpers.create_service import (
    assert_create_service_success,
    assert_create_service_invalid_auth,
    assert_create_service_missing_header,
    assert_create_service_missing_payload,
)

pytestmark = pytest.mark.usefixtures("django_db_setup")

@pytest.fixture(scope='module', autouse=True)
def create_user_client():
    return TestClient(create_user_router)

@pytest.fixture(scope='module', autouse=True)
def create_service_client():
    return TestClient(create_service_router)

def test_create_user_success(create_user_client): # make 3 users
    assert_create_user_success(create_user_client, 1)
    assert_create_user_success(create_user_client, 2)
    assert_create_user_success(create_user_client, 3)

def test_create_user_invalid_auth(create_user_client):
    assert_create_user_invalid_auth(create_user_client)

def test_create_user_missing_header(create_user_client):
    assert_create_user_missing_header(create_user_client)
    
def test_create_service_success(create_service_client):
    service_count = 0
    for service_number in range(1, 3+1):  # 3 services
        for provider in ["DROPBOX", "GOOGLE", "ONEDRIVE"]:
            payload = {
                "userId": os.getenv(f"TEST_USER_{provider}_ID_{service_number}"),
                "oauthType": os.getenv(f"TEST_USER_{provider}_OAUTHTYPE_{service_number}"),
                "oauthToken": os.getenv(f"TEST_USER_{provider}_OAUTHTOKEN_{service_number}"),
                "accessToken": os.getenv(f"TEST_USER_{provider}_ACCESSTOKEN_{service_number}"),
                "accessTokenExpiration": os.getenv(f"TEST_USER_{provider}_ACCESSTOKENEXPIRATION_{service_number}"),
                "refreshToken": os.getenv(f"TEST_USER_{provider}_REFRESHTOKEN_{service_number}"),
                "name": os.getenv(f"TEST_USER_{provider}_NAME_{service_number}"),
                "accountId": os.getenv(f"TEST_USER_{provider}_ACCOUNTID_{service_number}"),
                "email": os.getenv(f"TEST_USER_{provider}_EMAIL_{service_number}"),
                "scopeName": os.getenv(f"TEST_USER_{provider}_SCOPENAME_{service_number}"),
            }

            assert_create_service_success(create_service_client, payload, service_count)

            service_count += 1

def test_create_service_invalid_auth(create_service_client):
    service_count = 0
    for i in range(1, 3+1):  # 3 users
        for provider in ["DROPBOX", "GOOGLE", "ONEDRIVE"]:

            service_count += 1

            payload = {
                "userId": os.getenv(f"TEST_USER_{provider}_ID_{i}"),
                "oauthType": os.getenv(f"TEST_USER_{provider}_OAUTHTYPE_{i}"),
                "oauthToken": os.getenv(f"TEST_USER_{provider}_OAUTHTOKEN_{i}"),
                "accessToken": os.getenv(f"TEST_USER_{provider}_ACCESSTOKEN_{i}"),
                "accessTokenExpiration": os.getenv(f"TEST_USER_{provider}_ACCESSTOKENEXPIRATION_{i}"),
                "refreshToken": os.getenv(f"TEST_USER_{provider}_REFRESHTOKEN_{i}"),
                "name": os.getenv(f"TEST_USER_{provider}_NAME_{i}"),
                "accountId": os.getenv(f"TEST_USER_{provider}_ACCOUNTID_{i}"),
                "email": os.getenv(f"TEST_USER_{provider}_EMAIL_{i}"),
                "scopeName": os.getenv(f"TEST_USER_{provider}_SCOPENAME_{i}"),
            }

            assert_create_service_invalid_auth(create_service_client, payload)

def test_create_service_missing_header(create_service_client):
    for i in range(1, 3+1):  # 3 users
        for provider in ["dropbox", "google", "microsoft-entra-id"]:
            payload = {
                "userId": os.getenv(f"TEST_USER_{provider}_ID_{i}"),
                "oauthType": os.getenv(f"TEST_USER_{provider}_OAUTHTYPE_{i}"),
                "oauthToken": os.getenv(f"TEST_USER_{provider}_OAUTHTOKEN_{i}"),
                "accessToken": os.getenv(f"TEST_USER_{provider}_ACCESSTOKEN_{i}"),
                "accessTokenExpiration": os.getenv(f"TEST_USER_{provider}_ACCESSTOKENEXPIRATION_{i}"),
                "refreshToken": os.getenv(f"TEST_USER_{provider}_REFRESHTOKEN_{i}"),
                "name": os.getenv(f"TEST_USER_{provider}_NAME_{i}"),
                "accountId": os.getenv(f"TEST_USER_{provider}_ACCOUNTID_{i}"),
                "email": os.getenv(f"TEST_USER_{provider}_EMAIL_{i}"),
                "scopeName": os.getenv(f"TEST_USER_{provider}_SCOPENAME_{i}"),
            }

            assert_create_service_missing_header(create_service_client, payload)

def test_create_service_missing_payload(create_service_client):

    assert_create_service_missing_payload(create_service_client)