"""Helper functions for testing find user by email endpoint."""

import os
import pytest_check as check

from repository.models import User


def assert_find_user_by_email_success(client, email, expected_user_id):
    """Helper function to assert successful finding of a user by email.

    params:
        client: Test client to make requests.
        email: Email of the user to be found.
        expected_user_id: Expected ID of the found user.
    """
    # Get initial user count
    initial_user_count = User.objects.count()

    # Assuming 3 users are already created for service creation
    check.equal(initial_user_count == 3, True)
    try:
        response = client.get(
            f"/?email={email}",
            headers={"x-internal-auth": os.getenv("INTERNAL_API_KEY")},
        )
    except Exception as e:
        print(f"Exception during GET request: {e}")
        raise

    check.equal(response.status_code, 200)
    check.equal(response.json() is not None, True)
    check.equal(isinstance(response.json(), dict), True)
    check.equal(response.json().get("id") == expected_user_id, True)
    check.equal(response.json().get("email") == email, True)

def assert_find_user_by_email_invalid_auth(client, email):
    """Helper function to assert finding a user by email with invalid auth.

    params:
        client: Test client to make requests.
        email: Email of the user to be found.
    """
    try:
        response = client.get(
            f"/?email={email}",
            headers={"x-internal-auth": "invalid_token"}
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

def assert_find_user_by_email_missing_header(client, email):
    """Helper function to assert finding a user by email with missing auth header.

    params:
        client: Test client to make requests.
        email: Email of the user to be found.
    """
    try:
        response = client.get(f"/?email={email}")
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

def assert_find_user_by_email_missing_email(client):
    """Helper function to assert finding a user by email with missing email.

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
            {'type': 'missing', 'loc': ['query', 'email'], 'msg': 'Field required'},
            {'type': 'missing', 'loc': ['header', 'x-internal-auth'], 'msg': 'Field required'}
        ]
    }, {
        'detail': [
            {'type': 'string_type', 'loc': ['query', 'email'], 'msg': 'Input should be a valid string'},
            {'type': 'string_type', 'loc': ['header', 'x-internal-auth'], 'msg': 'Input should be a valid string'}
        ]
    }), True)
