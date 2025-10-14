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
from p7.get_dropbox_files.api import fetch_dropbox_files_router
from p7.get_google_drive.api import fetch_google_drive_files_router
from p7.get_onedrive_files.api import fetch_onedrive_files_router
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
from helpers.fetch_service import (
    assert_fetch_dropbox_files_success,
    assert_fetch_dropbox_files_invalid_auth,
    assert_fetch_dropbox_files_missing_header,
    assert_fetch_dropbox_files_missing_userid,
    assert_fetch_google_files_success,
    assert_fetch_google_files_invalid_auth,
    assert_fetch_google_files_missing_header,
    assert_fetch_google_files_missing_userid,
    assert_fetch_onedrive_files_success,
    assert_fetch_onedrive_files_invalid_auth,
    assert_fetch_onedrive_files_missing_header,
    assert_fetch_onedrive_files_missing_userid,
)

pytestmark = pytest.mark.usefixtures("django_db_setup")

@pytest.fixture(scope='module', autouse=True)
def create_user_client():
    return TestClient(create_user_router)

@pytest.fixture(scope='module', autouse=True)
def create_service_client():
    return TestClient(create_service_router)

@pytest.fixture(scope='module', autouse=True)
def fetch_dropbox_files_client():
    return TestClient(fetch_dropbox_files_router)

@pytest.fixture(scope='module', autouse=True)
def fetch_google_files_client():
    return TestClient(fetch_google_drive_files_router)

@pytest.fixture(scope='module', autouse=True)
def fetch_onedrive_files_client():
    return TestClient(fetch_onedrive_files_router)

def test_create_user_success(create_user_client): # make 3 users
    for user_number in range(1, 3+1):  # 3 users
        assert_create_user_success(create_user_client, user_number)

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
    for user_number in range(1, 3+1):  # 3 users
        for provider in ["DROPBOX", "GOOGLE", "ONEDRIVE"]:
            payload = {
                "userId": os.getenv(f"TEST_USER_{provider}_ID_{user_number}"),
                "oauthType": os.getenv(f"TEST_USER_{provider}_OAUTHTYPE_{user_number}"),
                "oauthToken": os.getenv(f"TEST_USER_{provider}_OAUTHTOKEN_{user_number}"),
                "accessToken": os.getenv(f"TEST_USER_{provider}_ACCESSTOKEN_{user_number}"),
                "accessTokenExpiration": os.getenv(f"TEST_USER_{provider}_ACCESSTOKENEXPIRATION_{user_number}"),
                "refreshToken": os.getenv(f"TEST_USER_{provider}_REFRESHTOKEN_{user_number}"),
                "name": os.getenv(f"TEST_USER_{provider}_NAME_{user_number}"),
                "accountId": os.getenv(f"TEST_USER_{provider}_ACCOUNTID_{user_number}"),
                "email": os.getenv(f"TEST_USER_{provider}_EMAIL_{user_number}"),
                "scopeName": os.getenv(f"TEST_USER_{provider}_SCOPENAME_{user_number}"),
            }

            assert_create_service_missing_header(create_service_client, payload)

def test_create_service_missing_payload(create_service_client):

    assert_create_service_missing_payload(create_service_client)

def test_fetch_dropbox_files_success(fetch_dropbox_files_client):

    for user_number in range(1, 3+1):  # 3 users

        assert_fetch_dropbox_files_success(fetch_dropbox_files_client, user_number, "dropbox")

def test_fetch_dropbox_files_invalid_auth(fetch_dropbox_files_client):

    for user_number in range(1, 3+1):  # 3 users

        assert_fetch_dropbox_files_invalid_auth(fetch_dropbox_files_client, user_number)

def test_fetch_dropbox_files_missing_header(fetch_dropbox_files_client):

    for user_number in range(1, 3+1):  # 3 users

        assert_fetch_dropbox_files_missing_header(fetch_dropbox_files_client, user_number)

def test_fetch_dropbox_files_missing_userid(fetch_dropbox_files_client):

    for user_number in range(1, 3+1):  # 3 users

        assert_fetch_dropbox_files_missing_userid(fetch_dropbox_files_client)

def test_fetch_google_files_success(fetch_google_files_client):

    for user_number in range(1, 3+1):  # 3 users

        assert_fetch_google_files_success(fetch_google_files_client, user_number, "google")

def test_fetch_google_files_invalid_auth(fetch_google_files_client):

    for user_number in range(1, 3+1):  # 3 users

        assert_fetch_google_files_invalid_auth(fetch_google_files_client, user_number)

def test_fetch_google_files_missing_header(fetch_google_files_client):

    for user_number in range(1, 3+1):  # 3 users

        assert_fetch_google_files_missing_header(fetch_google_files_client, user_number)

def test_fetch_google_files_missing_userid(fetch_google_files_client):

    for user_number in range(1, 3+1):  # 3 users

        assert_fetch_google_files_missing_userid(fetch_google_files_client)

def test_fetch_onedrive_files_success(fetch_onedrive_files_client):

    for user_number in range(1, 3+1):  # 3 users

        assert_fetch_onedrive_files_success(fetch_onedrive_files_client, user_number, "microsoft-entra-id")

def test_fetch_onedrive_files_invalid_auth(fetch_onedrive_files_client):

    for user_number in range(1, 3+1):  # 3 users

        assert_fetch_onedrive_files_invalid_auth(fetch_onedrive_files_client, user_number)

def test_fetch_onedrive_files_missing_header(fetch_onedrive_files_client):

    for user_number in range(1, 3+1):  # 3 users

        assert_fetch_onedrive_files_missing_header(fetch_onedrive_files_client, user_number)

def test_fetch_onedrive_files_missing_userid(fetch_onedrive_files_client):

    for user_number in range(1, 3+1):  # 3 users

        assert_fetch_onedrive_files_missing_userid(fetch_onedrive_files_client)
