"""Helper functions for testing create service endpoint."""
import os
import pytest_check as check

from repository.models import Service, User

def assert_create_service_success(client, payload, service_count):
    """Helper function to assert successful creation of a service.
    params:
        client: Test client to make requests.
        payload: JSON payload for creating the service.
        service_count: Expected number of services before creation.
    """
    # Get initial user count
    initial_user_count = User.objects.count()
    initial_service_count = Service.objects.count()

    check.equal(initial_service_count, service_count)

    response = client.post(
        "/",
        json=payload, headers={"x-internal-auth": os.getenv("INTERNAL_API_KEY")}
    )

    data = response.json()

    check.equal(response.status_code, 200)
    check.equal("id" in data, True)
    check.equal("error" not in data, True)
    check.equal(isinstance(data["id"], int), True)
    check.equal(isinstance(data["name"], str), True)
    check.equal(data["name"], payload["name"])

    # Assert that a new service was created in the database
    check.equal(User.objects.count(), initial_user_count)  # User count should remain the same
    check.equal(Service.objects.count(), initial_service_count + 1)

    # Assert that the service with the returned ID actually exists
    created_service = Service.objects.get(id=data["id"], name=payload["name"])
    check.is_not_none(created_service)
    check.equal(created_service.id, data["id"])

def assert_create_service_invalid_auth(client, payload):
    """Helper function to assert unauthorized access when invalid auth token is provided.
    params:
        client: Test client to make requests.
        payload: JSON payload for creating the service.
    """
    response = client.post("/", json=payload, headers={"x-internal-auth": "invalid_token"})

    check.equal(response.status_code, 401)
    check.equal(response.json(), {"error": "Unauthorized - invalid x-internal-auth"})

def assert_create_service_missing_header(client, payload):
    """Helper function to assert bad request when auth header is missing.
    params:
        client: Test client to make requests.
        payload: JSON payload for creating the service.
    """
    response = client.post("/", json=payload)

    check.equal(response.status_code, 422)
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

def assert_create_service_missing_payload(client):
    """Helper function to assert bad request when payload is missing.
    params:
        client: Test client to make requests.
    """
    response = client.post("/")

    check.equal(response.status_code, 422)
    check.equal(response.json() in ({
        'detail': [
            {'type': 'missing',
             'loc': ['header', 'x-internal-auth'],
             'msg': 'Field required'
             },
            {'type': 'missing', 'loc': ['body', 'payload'], 'msg': 'Field required'}
        ]
    }, {
        'detail': [
            {'type': 'string_type',
             'loc': ['header', 'x-internal-auth'],
             'msg': 'Input should be a valid string'
             },
            {'type': 'missing', 'loc': ['body', 'payload'], 'msg': 'Field required'}
        ]
    }), True)
