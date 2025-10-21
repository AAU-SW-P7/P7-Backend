"""Helper functions for testing user creation."""
import os
import pytest_check as check

from repository.models import User

def assert_create_user_success(client, user_number):
    """Test the successful creation of a user.

    params:
        client: The test client to make requests.
        user_number: The expected number of users after creation.
    """
    # Get initial user count
    initial_count = User.objects.count()

    check.equal(initial_count == user_number - 1, True)

    response = client.post("/", headers={"x-internal-auth": os.getenv("INTERNAL_API_KEY")})

    data = response.json()

    check.equal(response.status_code, 200)
    check.equal("id" in data, True)
    check.equal("error" not in data, True)
    check.equal(isinstance(data["id"], int), True)

    # Assert that a new user was created in the database
    check.equal(User.objects.count(), user_number)

    # Assert that the user with the returned ID actually exists
    created_user = User.objects.get(id=data["id"])
    check.is_not_none(created_user)
    check.equal(created_user.id, data["id"])

def assert_create_user_invalid_auth(client):
    """Test the creation of a user with invalid authentication.
    
    params:
        client: The test client to make requests.
    """
    response = client.post("/", headers={"x-internal-auth": "invalid_token"})

    check.equal(response.status_code, 401)
    check.equal(response.json(), {
            "error": "Unauthorized - invalid x-internal-auth"
        }
    )

def assert_create_user_missing_header(client):
    """Test the creation of a user with a missing authentication header.

    params:
        client: The test client to make requests.
    """
    response = client.post("/")

    check.equal(response.status_code, 422)
    check.equal(response.json() in ({
        'detail': [
            {'type': 'missing', 'loc': ['header', 'x-internal-auth'], 'msg': 'Field required'}
        ]
    }, {
        'detail': [
            {'type': 'string_type', 'loc': ['header', 'x-internal-auth'], 'msg': 'Input should be a valid string'}
        ]
    }), True)
