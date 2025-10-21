"""Helper functions for parameter validation in tests."""
import os
import pytest_check as check

from repository.models import User

def assert_missing_query_param_type(client, query_param_type=None):
    """Helper function to assert finding a service by user ID with missing email.

    params:
        client: Test client to make requests.
        query_param_type: Type of the query parameter, either 'user_id' or 'email'.
    """
    try:
        response = client.get("/",)
    except Exception as e:
        print(f"Exception during GET request: {e}")
        raise

    check.equal(response.status_code, 422)
    check.equal(response.json() is not None, True)
    check.equal(isinstance(response.json(), dict), True)
    check.equal(response.json(), {
        'detail': [
            {
                'type': 'string_type',
                'loc': ['query', 'user_id' if query_param_type == 'user_id' else 'email'],
                'msg': 'Input should be a valid string'
            },
            {
                'type': 'string_type', 
                'loc': ['header', 'x-internal-auth'], 
                'msg': 'Input should be a valid string'
            }
        ]
    })

def assert_missing_header(client, query_param, query_param_type=None):
    """Helper function to assert finding a user by user_id with missing auth header.

    params:
        client: Test client to make requests.
        query_param: Either users ID or email.
        query_param_type: Type of the query parameter, either 'user_id' or 'email'.
    """
    try:
        response = client.get(f"/?{query_param_type}={query_param}")
    except Exception as e:
        print(f"Exception during GET request: {e}")
        raise

    check.equal(response.status_code, 422)
    check.equal(response.json() is not None, True)
    check.equal(isinstance(response.json(), dict), True)
    check.equal(response.json(), {
        'detail': [
            {
                'loc': ['header', 'x-internal-auth'], 
                'msg': 'Input should be a valid string', 
                'type': 'string_type'
            }
        ]
    })


def assert_invalid_auth(client, query_param, query_param_type=None):
    """Helper function to assert finding a service with invalid auth.

    params:
        client: Test client to make requests.
        query_param: Either users ID or email.
        query_param_type: Type of the query parameter, either 'user_id' or 'email'.
    """
    try:
        response = client.get(
            f"/?{query_param_type}={query_param}",
            headers={"x-internal-auth": "invalid_token"}
            )
    except Exception as e:
        print(f"Exception during GET request: {e}")
        raise

    check.equal(response.status_code, 401)
    check.equal(response.json() is not None, True)
    check.equal(isinstance(response.json(), dict), True)
    check.equal(response.json(), {"error": "Unauthorized - invalid x-internal-auth"})
