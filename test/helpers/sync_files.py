"""Helper functions for test_sync_files.py"""
import pytest_check as check

from django.http import JsonResponse
from p7.sync_files.service_sync_functions import sync_dropbox_files, sync_google_drive_files, sync_onedrive_files

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
            {'type': 'string_type', 'loc': ['header', 'x-internal-auth'], 'msg': 'Input should be a valid string'}
        ]
    }), True)


def assert_sync_files_missing_user_id(client):
    """Helper function to assert syncing with missing user ID.

    params:
        client: Test client to make requests.
    """
    try:
        response = client.get(
            "/",
        )
    except Exception as e:
        print(f"Exception during GET request: {e}")
        raise

    check.equal(response.status_code, 422)
    check.equal(response.json() is not None, True)
    check.equal(isinstance(response.json(), dict), True)
    check.equal(response.json() in ({
        'detail': [
            {'type': 'missing', 'loc': ['query', 'user_id'], 'msg': 'Field required'},
            {'type': 'missing', 'loc': ['header', 'x-internal-auth'], 'msg': 'Field required'}
        ]
    }, {
        'detail': [
            {'type': 'string_type', 'loc': ['query', 'user_id'], 'msg': 'Input should be a valid string'},
            {'type': 'string_type', 'loc': ['header', 'x-internal-auth'], 'msg': 'Input should be a valid string'}
        ]
    }), True)

def assert_sync_files_function_missing_user_id(provider):
    """Helper function to assert behavior when called without user_id"""
    if provider == "dropbox":
        response = sync_dropbox_files()
    elif provider == "google":
        response = sync_google_drive_files()
    elif provider == "onedrive":
        response = sync_onedrive_files()
    else:
        print("Wrong provider provided. Please use dropbox, google, or onedrive")
        check.equal(True, False)
        return

    check.equal(response.status_code, 400)
    check.equal(response is not None, True)
    check.equal(isinstance(response, JsonResponse), True)
