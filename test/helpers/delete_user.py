"""Helper functions for testing user creation."""

import os
import pytest_check as check

from repository.models import User


def assert_delete_user_success(client, user_number):
    """Test the successful deletion of a user.

    params:
        client: The test client to make requests.
        user_number: The expected number of users after deletion.
    """
    # Get initial user count
    initial_count = User.objects.count()

    check.equal(initial_count, user_number)

    response = client.post(
        f"/?user_id={user_number}",
        headers={"x-internal-auth": os.getenv("INTERNAL_API_KEY")},
    )

    data = response.json()

    check.equal(response.status_code, 200)
    check.equal("error" not in data, True)

    # Assert that a new user was created in the database
    check.equal(User.objects.count(), user_number - 1)


def assert_delete_user_invalid_auth(client, user_number):
    """Test the deletion of a user with invalid authentication.

    params:
        client: The test client to make requests.
    """
    response = client.post(
        f"/?user_id={user_number}", headers={"x-internal-auth": "invalid_token"}
    )

    check.equal(response.status_code, 401)
    check.equal(response.json(), {"error": "Unauthorized - invalid x-internal-auth"})


def assert_delete_user_missing_header(client, user_number):
    """Test the deletion of a user with a missing authentication header.

    params:
        client: The test client to make requests.
    """
    response = client.post(f"/?user_id={user_number}")

    check.equal(response.status_code, 422)
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


def assert_delete_user_invalid_user_id(client, user_number):
    """Test the deletion of a user with invalid user_id.

    params:
        client: The test client to make requests.
    """
    response = client.post(
        f"/?user_id={user_number}",
        headers={"x-internal-auth": os.getenv("INTERNAL_API_KEY")},
    )

    check.equal(response.status_code, 404)
    check.equal(response.json(), {"error": "User not found"})
