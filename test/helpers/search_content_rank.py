"""Helper functions for testing filename search ranking."""

import math
import pytest_check as check
from typing import List

from repository.models import File
from django.db.models import Q


def assert_files_appear_in_specified_order(query: str, ordered_files: List[File], base_filter: Q):
    """
    Test files appear in the order specified by the ordered_files
    params:
        query: search query string
        ordered_files: files ordered in the way they should appear in the search results
    """
    results = File.objects.ranking_based_on_content(query, base_filter=base_filter)

    check.equal(
        len(results), len(ordered_files), "Search returned unexpected number of files"
    )
    for index, expected in enumerate(ordered_files):
        check.equal(
            results[index].pk,
            expected.pk,
            f"Result #{index + 1} ({results[index]!r}) != expected {expected!r}",
        )

def assert_files_have_same_rank(query: str,  base_filter: Q):
    """
    Test files have the same rank
    params:
        query: search query string
        ordered_files: files ordered in the way they should appear in the search results
    """
    results = File.objects.ranking_based_on_content(query, base_filter=base_filter)
    check.is_true(results, "Search returned no files")

    first_rank = getattr(results[0], "rank", None)
    check.is_not_none(first_rank, "First search result is missing rank")

    for index, file in enumerate(results[1:], start=1):
        rank = getattr(file, "rank", None)
        check.is_not_none(rank, f"Result #{index + 1} is missing rank")
        check.is_true(
            math.isclose(rank, first_rank, rel_tol=1e-9),
            f"Result #{index + 1} rank {rank} != {first_rank}",
        )




