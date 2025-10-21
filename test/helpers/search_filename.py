
"""Helper functions for testing search_files_by_name function."""
import pytest_check as check
from repository.models import File
from p7.search_files_by_filename.api import search_files_by_name


def assert_search_filename_success(user_id, query, expected_name):
    """Assert that searching by filename works correctly.

    params:
        user_id (int): ID of the user to search files for
        query (str): Search string
        expected_name (list): The expected filename in results
    """
    results = search_files_by_name(query, user_id)
    expected_name_len = len(expected_name)
    for file in results:
        check.equal(file.name, expected_name.pop(0))
        check.equal(file.serviceId.userId.id, user_id)

    check.equal(results.count(), expected_name_len)

def assert_search_filename_multiple_results(user_id, queries, expected_count):
    """Assert that multiple substrings return the correct number of files."""
    results = search_files_by_name(queries, user_id)

    check.equal(results.count(), expected_count)


def assert_search_filename_no_results(user_id, query, expected_count):
    """Assert that search returns no results for a missing query."""
    results = search_files_by_name(query, user_id)

    check.equal(results.count(), expected_count)

def assert_search_filename_empty_string(user_id, query, expected_count=0):
    """Assert that searching with an empty string returns no results."""
    results = search_files_by_name(query, user_id)

    check.equal(results.count(), expected_count)

def assert_search_filename_orm_injection_resistance(user_id, query, expected_count=0):
    """Assert that the search function is resistant to ORM injection attacks."""
    results = search_files_by_name(query, user_id)

    check.equal(results.count(), expected_count)
    
def assert_search_filename_invalid_auth(client, user_id):
    """Helper function to assert unauthorized access when invalid auth token is provided.

    params:
        client: Test client to make requests.
        user_id: ID of the user whose files are to be fetched.
    """
    print(f"Fetching Dropbox files for user_id: {user_id}")
    response = client.get(f"/?user_id={user_id}", headers={"x-internal-auth": "invalid_token"})

    check.equal(response.status_code, 401)
    check.equal(response.json(), {"error": "Unauthorized - invalid x-internal-auth"})

def assert_search_filename_missing_header(client, user_id):
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


def assert_search_filename_missing_userid(client):
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
