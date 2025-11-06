"""Helper functions for testing find service endpoint."""

import os
import pytest_check as check

from repository.models import User


def assert_find_service_success(client, user_id, email):
    """Helper function to assert successful finding of a service.

    params:
        client: Test client to make requests.
        user_id: ID of the user.
        email: Email of the user.
    """
    # Get initial user count
    initial_user_count = User.objects.count()

    # Assuming 3 users are already created for service creation
    check.equal(initial_user_count, 3)

    try:
        response = client.get(
            f"/?user_id={user_id}",
            headers={"x-internal-auth": os.getenv("INTERNAL_API_KEY")},
        )
    except Exception as e:
        print(f"Exception during GET request: {e}")
        raise

    data = response.json()

    check.equal(response.status_code, 200)
    check.equal(data is not None, True)
    check.equal(isinstance(data, list), True)

    for service in data:
        check.equal(isinstance(service, dict), True)
        check.equal(service.get("id") is not None, True)
        check.equal(service.get("userId") is not None, True)
        check.equal(service.get("name") is not None, True)
        check.equal(service.get("email") is not None, True)

        check.equal(service.get("userId") == user_id, True)
        check.equal(service.get("email") == email, True)


def assert_find_service_invalid_auth(client, user_id):
    """Helper function to assert finding a service with invalid auth.

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
    check.equal(response.json(), {"error": "Unauthorized - invalid x-internal-auth"})


def assert_find_service_missing_header(client, user_id):
    """Helper function to assert finding a user by user_id with missing auth header.

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
    check.equal(
        response.json()
        in (
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["header", "x-internal-auth"],
                        "msg": "Field required",
                    }
                ]
            },
            {
                "detail": [
                    {
                        "type": "string_type",
                        "loc": ["header", "x-internal-auth"],
                        "msg": "Input should be a valid string",
                    }
                ]
            },
        ),
        True,
    )


def assert_find_service_missing_user_id(client):
    """Helper function to assert finding a service by user ID with missing email.

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
    check.equal(
        response.json()
        in (
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["query", "user_id"],
                        "msg": "Field required",
                    },
                    {
                        "type": "missing",
                        "loc": ["header", "x-internal-auth"],
                        "msg": "Field required",
                    },
                ]
            },
            {
                "detail": [
                    {
                        "type": "string_type",
                        "loc": ["query", "user_id"],
                        "msg": "Input should be a valid string",
                    },
                    {
                        "type": "string_type",
                        "loc": ["header", "x-internal-auth"],
                        "msg": "Input should be a valid string",
                    },
                ]
            },
        ),
        True,
    )
