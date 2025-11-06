"""Helper functions for test_sync_files.py"""
import os
import json
from datetime import datetime, timezone
import pytest_check as check

from django.http import JsonResponse
from p7.sync_files.service_sync_functions import (
    sync_dropbox_files, sync_google_drive_files, sync_onedrive_files
    )
from repository.user import get_user
from repository.service import save_service

def assert_sync_files_invalid_auth(client, user_id):
    """Helper function to assert syncing with invalid auth.

    params:
        client: Test client to make requests.
        user_id: ID of the user.
    """
    try:
        response = client.get(
            f"/?user_id={user_id}", headers={"x-internal-auth": "invalid_token"}
        )
    except Exception as e:
        print(f"Exception during GET request: {e}")
        raise

    check.equal(response.status_code, 401)
    check.equal(response.json() is not None, True)
    check.equal(isinstance(response.json(), dict), True)
    check.equal(response.json(), {
            "error": "Unauthorized - invalid x-internal-auth"
        }
    )

def assert_sync_files_missing_internal_auth(client, user_id):
    """Helper function to assert syncing by user_id with missing auth header.

    params:
        client: Test client to make requests.
        user_id: ID of the user.
    """
    try:
        response = client.get(f"/?user_id={user_id}")
    except Exception as e:
        print(f"Exception during GET request: {e}")
        raise

    check.equal(response.status_code, 422)
    check.equal(response.json() is not None, True)
    check.equal(isinstance(response.json(), dict), True)
    check.equal(response.json() in ({
        'detail': [
            {'type': 'missing', 'loc': ['header', 'x-internal-auth'], 'msg': 'Field required'}
        ]
    }, {
        'detail': [
            {'type': 'string_type',
             'loc': ['header', 'x-internal-auth'],
             'msg': 'Input should be a valid string'
             }
        ]
    }), True)

def assert_sync_files_missing_user_id(client):
    """Helper function to assert syncing with missing user ID.

    params:
        client: Test client to make requests.
    """
    response = client.get("/")

    print(response.json())
    check.equal(response.status_code, 422)
    check.equal(response.json() in ({
        'detail': [
            {'type': 'missing', 'loc': ['query', 'user_id'], 'msg': 'Field required'},
            {'type': 'missing', 'loc': ['header', 'x-internal-auth'], 'msg': 'Field required'}
        ]
    }, {
        'detail': [
            {'type': 'string_type',
             'loc': ['query', 'user_id'],
             'msg': 'Input should be a valid string'
             },
            {'type': 'string_type',
             'loc': ['header', 'x-internal-auth'],
             'msg': 'Input should be a valid string'
             }
        ]
    }), True)

def assert_sync_files_function_missing_user_id(provider):
    """Helper function to assert behavior when called without user_id"""
    if provider == "dropbox":
        response = sync_dropbox_files("")
    elif provider == "google":
        response = sync_google_drive_files("")
    elif provider == "onedrive":
        response = sync_onedrive_files("")
    else:
        print("Wrong provider provided. Please use dropbox, google, or onedrive")
        check.equal(True, False)
        return

    check.equal(response.status_code, 400)
    check.equal(response is not None, True)
    check.equal(isinstance(response, JsonResponse), True)

def create_service(provider, user_id):
    """Helper function to create a service"""
    user_id = os.getenv(f"TEST_USER_{provider}_ID_{user_id}")
    oauth_type = os.getenv(f"TEST_USER_{provider}_OAUTHTYPE_{user_id}")
    oauth_token = os.getenv(f"TEST_USER_{provider}_OAUTHTOKEN_{user_id}")
    access_token = os.getenv(f"TEST_USER_{provider}_ACCESSTOKEN_{user_id}")
    access_token_expiration = os.getenv(
        f"TEST_USER_{provider}_ACCESSTOKENEXPIRATION_{user_id}"
    )
    refresh_token = os.getenv(f"TEST_USER_{provider}_REFRESHTOKEN_{user_id}")
    name = os.getenv(f"TEST_USER_{provider}_NAME_{user_id}")
    account_id = os.getenv(f"TEST_USER_{provider}_ACCOUNTID_{user_id}")
    email = os.getenv(f"TEST_USER_{provider}_EMAIL_{user_id}")
    scope_name = os.getenv(f"TEST_USER_{provider}_SCOPENAME_{user_id}")

    # Save service and link to user
    user = get_user(user_id)
    save_service(
        user,
        oauth_type,
        oauth_token,
        access_token,
        access_token_expiration,
        refresh_token,
        name,
        account_id,
        email,
        scope_name,
        datetime.now(timezone.utc),
    )

def read_json_file(file_path):
    """
    Read and parse a list of JSON objects from a file.

    Args:
        path (str | pathlib.Path): Path to the JSON file containing an array of objects.

    Returns:
        list: List of JSON objects, or JsonResponse error if file cannot be loaded.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return json.loads(text)
    except (FileNotFoundError, json.JSONDecodeError):
        return JsonResponse({"error": "Failed to load json"}, status=422)
