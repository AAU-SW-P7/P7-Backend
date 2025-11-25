"""Helper functions for testing search_files_by_name function."""

import pytest_check as check
from p7.search.api import (
    query_files,
)


def assert_query_file_by_content(user_id, query, expected_ids):
    """Assert that searching by content works correctly.

    params:
        user_id (int): ID of the user to search files for
        query (str): Search string
        expected_name (list): The expected filename in results
    """
    results = query_files(query, user_id)
    result_ids = []

    for result in results:
        result_ids.append(result.id)

    # 1. Check all returned files belong to the user
    for file in results:
        check.equal(file.serviceId.userId.id, user_id)

    # 2. Check that we return the same number of files as expected
    check.equal(len(results), len(expected_ids))

    # 3. Check that ALL expected ids are present
    for expected in expected_ids:
        check.is_in(expected.id, result_ids)
