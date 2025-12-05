"""Helper functions for testing search_files_by_name function."""

import pytest_check as check
from p7.search.api import (
    sanitize_user_search,
    query_files,
    tokenize,
)

def assert_query_file_by_name(user_id, query, expected_name):
    """Assert that searching by filename works correctly.

    params:
        user_id (int): ID of the user to search files for
        query (str): Search string
        expected_name (list): The expected filename in results
    """
    results = query_files(query, user_id)

    # 1. Check all returned files belong to the user
    for file in results:
        check.equal(file.serviceId.userId.id, user_id)

    # 2. Extract actual names
    result_names = [file.name for file in results]

    # 3. Check that ALL expected names are present
    for expected in expected_name:
        check.is_in(expected, result_names)

def assert_query_matches_count(user_id, query, expected_count):
    """Assert that search returns no results for a missing query."""
    for i, q in enumerate(query):
        query[i] = sanitize_user_search(q)
    results = query_files(query, user_id)
    for file in results:
        check.equal(file.serviceId.userId.id, user_id)
    check.equal(len(results), expected_count)

def assert_search_filename_invalid_auth(client, user_id, search_string):
    """Helper function to assert unauthorized access when invalid auth token is provided.

    params:
        client: Test client to make requests.
        user_id: ID of the user whose files are to be fetched.
    """
    print(f"Fetching Dropbox files for user_id: {user_id}")
    response = client.get(
        f"/?user_id={user_id}&search_string={search_string}",
        headers={"x-internal-auth": "invalid_token"},
    )

    check.equal(response.status_code, 401)
    check.equal(response.json(), {"error": "Unauthorized - invalid x-internal-auth"})


def assert_search_filename_missing_header(client, user_id, search_string):
    """Helper function to assert bad request when auth header is missing.
    params:
        client: Test client to make requests.
        user_id: ID of the user whose files are to be fetched.
    """
    response = client.get(f"/?user_id={user_id}&search_string={search_string}")

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


def assert_search_filename_missing_userid(client, search_string):
    """Helper function to assert bad request when userId query parameter is missing.
    params:
        client: Test client to make requests.
    """
    response = client.get(f"/?search_string={search_string}")

    check.equal(response.status_code, 422)
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


def assert_search_filename_missing_search_string(client, user_id):
    """Helper function to assert bad request when userId query parameter is missing.
    params:
        client: Test client to make requests.
    """
    response = client.get(f"/?user_id={user_id}", headers={"x-internal-auth": "p7"})

    check.equal(response.status_code, 422)
    check.equal(
        response.json()
        in (
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["query", "search_string"],
                        "msg": "Field required",
                    },
                ]
            },
            {
                "detail": [
                    {
                        "type": "string_type",
                        "loc": ["query", "search_string"],
                        "msg": "Input should be a valid string",
                    },
                ]
            },
        ),
        True,
    )


def assert_search_filename_sanitization(input_str):
    """Helper function to assert the sanitization of user search input."""
    sanitized = sanitize_user_search(input_str)
    assert isinstance(sanitized, str)
    assert sanitized == sanitized.lower()
    assert all(
        c.isalnum() or c.isspace() or c in "'-_" for c in sanitized
    )  # Check allowed chars


def assert_search_filename_basic_sanitization():
    """Helper function to assert basic sanitization cases."""
    assert (
        sanitize_user_search("Aalborg's Bedste <script>") == "aalborgs bedste script"
    )
    assert sanitize_user_search('Hello "World" / Test') == "hello world test"
    assert sanitize_user_search("NoSpecialChars") == "nospecialchars"
    assert sanitize_user_search("<>'\"/|:;?") == ""
    assert sanitize_user_search("") == ""
    assert sanitize_user_search("   Leading and trailing   ") == "leading and trailing"
    assert sanitize_user_search("Multiple   spaces") == "multiple spaces"
    assert (
        sanitize_user_search("Café-Del'Mar -  “Best of ’98”!!! ")
        == "café delmar best of 98"
    )


def assert_tokenize_match(input_str, expected_tokens):
    """Helper function to assert tokenization with numbers in the string.
    params:
        input_str (str): Input string to be tokenized.
        expected_tokens (list): Expected list of tokens.
    """
    tokens = tokenize(input_str)
    assert tokens == expected_tokens


def assert_tokenize_hypothesis(input_str):
    """Helper function to assert tokenization with various inputs using Hypothesis.
    params:
        input_str (str): Randomly generated input string.
    """
    tokens = tokenize(input_str)
    assert all(isinstance(token, str) for token in tokens)
