"""Helper functions for testing search_files_by_name function."""

import pytest_check as check
from p7.search.api import (
    query_files,
)

def assert_query_file_by_content(user_id, query, expected_name):
    """Assert that searching by content works correctly.

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
    results = query_files(query, user_id)
    for file in results:
        check.equal(file.serviceId.userId.id, user_id)
    check.equal(results.count(), expected_count)



