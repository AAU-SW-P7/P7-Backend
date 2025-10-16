"""Helper functions for testing fetch service endpoints for Dropbox, Google, and OneDrive."""
import os
import pytest_check as check

from repository.models import Service, User, File

def assert_fetch_dropbox_files_success(client, user_id, service):
    """Helper function to assert successful fetching of Dropbox files 
    for a given user_id and service.

    params:
        client: Test client to make requests.
        user_id: ID of the user whose files are to be fetched.
        service: Name of the service (e.g., 'dropbox').
    """
    # Get initial user count
    initial_user_count = User.objects.count()
    initial_service_count = Service.objects.count()
    initial_file_count = File.objects.filter(
        serviceId__userId=user_id,
        serviceId__name=service
        ).count()

    # Assuming 3 users are already created for service creation
    check.equal(initial_user_count == 3, True)
    check.equal(initial_service_count == 9, True)
    # Assuming no files are created initially
    check.equal(initial_file_count == 0, True)

    try:
        response = client.get(
            f"/?user_id={user_id}",
            headers={"x-internal-auth": os.getenv("INTERNAL_API_KEY")}
            )
    except Exception as e:
        print(f"Exception during GET request: {e}")
        raise

    check.equal(response.status_code, 200)
    check.equal(response.json() is not None, True)
    check.equal(isinstance(response.json(), list), True)

def assert_fetch_dropbox_files_invalid_auth(client, user_id):
    """Helper function to assert unauthorized access when invalid auth token is provided.

    params:
        client: Test client to make requests.
        user_id: ID of the user whose files are to be fetched.
    """
    print(f"Fetching Dropbox files for user_id: {user_id}")
    response = client.get(f"/?user_id={user_id}", headers={"x-internal-auth": "invalid_token"})

    check.equal(response.status_code, 401)
    check.equal(response.json(), {"error": "Unauthorized - invalid x-internal-auth"})

def assert_fetch_dropbox_files_missing_header(client, user_id):
    """Helper function to assert bad request when auth header is missing.
    params:
        client: Test client to make requests.
        user_id: ID of the user whose files are to be fetched.
    """
    response = client.get(f"/?user_id={user_id}")

    check.equal(response.status_code, 422)
    check.equal(response.json(), {
        'detail': [{
            'loc': ['header', 'x-internal-auth'],
            'msg': 'Input should be a valid string',
            'type': 'string_type'
                    }]})


def assert_fetch_dropbox_files_missing_userid(client):
    """Helper function to assert bad request when userId query parameter is missing.
    params:
        client: Test client to make requests.
    """
    response = client.get("/")

    check.equal(response.status_code, 422)
    check.equal(response.json(), {
        'detail': [
            {
                'type': 'string_type',
                'loc': ['query', 'user_id'],
                'msg': 'Input should be a valid string'
            },
            {
                'type': 'string_type',
                'loc': ['header', 'x-internal-auth'],
                'msg': 'Input should be a valid string'
            }
        ]
    })

def assert_fetch_google_files_success(client, user_id, service):
    """Helper function to assert successful fetching of Google files
    for a given user_id and service.
    params:
        client: Test client to make requests.
        user_id: ID of the user whose files are to be fetched.
        service: Name of the service (e.g., 'google').
    """
    # Get initial user count
    initial_user_count = User.objects.count()
    initial_service_count = Service.objects.count()
    initial_file_count = File.objects.filter(
        serviceId__userId=user_id,
        serviceId__name=service
        ).count()

    # Assuming 3 users are already created for service creation
    check.equal(initial_user_count == 3, True)
    check.equal(initial_service_count == 9, True)
    # Assuming no files are created initially
    check.equal(initial_file_count == 0, True)

    try:
        response = client.get(
            f"/?user_id={user_id}",
            headers={"x-internal-auth": os.getenv("INTERNAL_API_KEY")}
        )
    except Exception as e:
        print(f"Exception during GET request: {e}")
        raise

    check.equal(response.status_code, 200)
    check.equal(response.json() is not None, True)
    check.equal(isinstance(response.json(), list), True)

def assert_fetch_google_files_invalid_auth(client, user_id):
    """Helper function to assert unauthorized access when invalid auth token is provided.
    params:
        client: Test client to make requests.
        user_id: ID of the user whose files are to be fetched.
    """
    response = client.get(f"/?user_id={user_id}", headers={"x-internal-auth": "invalid_token"})

    check.equal(response.status_code, 401)
    check.equal(response.json(), {"error": "Unauthorized - invalid x-internal-auth"})

def assert_fetch_google_files_missing_header(client, user_id):
    """Helper function to assert bad request when auth header is missing.
    params:
        client: Test client to make requests.
        user_id: ID of the user whose files are to be fetched.
    """
    response = client.get(f"/?user_id={user_id}")

    check.equal(response.status_code, 422)
    check.equal(response.json(), {
        'detail': [
            {
                'loc': ['header', 'x-internal-auth'],
                'msg': 'Input should be a valid string',
                'type': 'string_type'
            }
        ]
    })

def assert_fetch_google_files_missing_userid(client):
    """Helper function to assert bad request when userId query parameter is missing.
    params:
        client: Test client to make requests.
    """
    response = client.get("/")

    check.equal(response.status_code, 422)
    check.equal(response.json(), {
        'detail': [
            {
                'type': 'string_type',
                'loc': ['query', 'user_id'],
                'msg': 'Input should be a valid string'
            },
            {
                'type': 'string_type',
                'loc': ['header', 'x-internal-auth'],
                'msg': 'Input should be a valid string'
            }
        ]
    })

def assert_fetch_onedrive_files_success(client, user_id, service):
    """Helper function to assert successful fetching of OneDrive files
    params:
        client: Test client to make requests.
        user_id: ID of the user whose files are to be fetched.
        service: Name of the service (e.g., 'onedrive').
    """
    # Get initial user count
    initial_user_count = User.objects.count()
    initial_service_count = Service.objects.count()
    initial_file_count = File.objects.filter(
        serviceId__userId=user_id,
        serviceId__name=service
    ).count()

    # Assuming 3 users are already created for service creation
    check.equal(initial_user_count == 3, True)
    check.equal(initial_service_count == 9, True)
    # Assuming no files are created initially
    check.equal(initial_file_count == 0, True)

    try:
        response = client.get(
            f"/?user_id={user_id}",
            headers={"x-internal-auth": os.getenv("INTERNAL_API_KEY")}
        )
    except Exception as e:
        print(f"Exception during GET request: {e}")
        raise

    check.equal(response.status_code, 200)
    check.equal(response.json() is not None, True)
    check.equal(isinstance(response.json(), list), True)

def assert_fetch_onedrive_files_invalid_auth(client, user_id):
    """Helper function to assert unauthorized access when invalid auth token is provided.
    params:
        client: Test client to make requests.
        user_id: ID of the user whose files are to be fetched.
    """
    response = client.get(f"/?user_id={user_id}", headers={"x-internal-auth": "invalid_token"})

    check.equal(response.status_code, 401)
    check.equal(response.json(), {"error": "Unauthorized - invalid x-internal-auth"})

def assert_fetch_onedrive_files_missing_header(client, user_id):
    """Helper function to assert bad request when auth header is missing.
    params:
        client: Test client to make requests.
        user_id: ID of the user whose files are to be fetched.
    """
    response = client.get(f"/?user_id={user_id}")

    check.equal(response.status_code, 422)
    check.equal(response.json(), {
        'detail': [
            {
                'loc': ['header', 'x-internal-auth'], 
                'msg': 'Input should be a valid string', 
                'type': 'string_type'
            }
        ]
    })

def assert_fetch_onedrive_files_missing_userid(client):
    """Helper function to assert bad request when userId query parameter is missing.
    params:
        client: Test client to make requests.
    """
    response = client.get("/")

    check.equal(response.status_code, 422)
    check.equal(response.json(), {
        'detail': [
            {
                'type': 'string_type',
                'loc': ['query', 'user_id'],
                'msg': 'Input should be a valid string'
            },
            {
                'type': 'string_type', 
                'loc': ['header', 'x-internal-auth'], 
                'msg': 'Input should be a valid string'
            }
        ]
    })
