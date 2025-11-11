"""Helper functions for testing filename search ranking."""

import pytest_check as check

from repository.models import File


def assert_get_exact_match(
    query: str, filename_exact_match: str, filename_partial_match: str
):
    """Test exact match ranking higher than partial matches.
    params:
        query: search query string
        filename_exact_match: name of the file that exactly matches the query
        filename_partial_match: name of the file that partially matches the query
    """
    results = File.objects.ranking_based_on_file_name(query)
    rank_exact = None
    rank_partial = None
    for result in results:
        if result.name == filename_exact_match:
            rank_exact = result.rank
        if result.name == filename_partial_match:
            rank_partial = result.rank
    check.is_true(rank_exact is not None, "exact match not found in results")
    check.is_true(rank_partial is not None, "partial match not found in results")
    check.greater(rank_exact, rank_partial)


def assert_file_length(query, short_name, long_name):
    """Test shorter file names rank higher when tokens are the same.
    params:
        query: search query string
        short_name: name of the shorter file
        long_name: name of the longer file
    """
    results = File.objects.ranking_based_on_file_name(query)
    short_rank = None
    long_rank = None
    for result in results:
        if result.name == short_name:
            short_rank = result.rank
        if result.name == long_name:
            long_rank = result.rank
    check.is_true(short_rank is not None, "short name not found in results")
    check.is_true(long_rank is not None, "long name not found in results")
    check.greater(short_rank, long_rank)


def assert_token_position(query_close: str, query_far_away: str, file_name: str):
    """Test token position affects ranking.
    params:
        query_close: search query string with tokens in similar position
        query_far_away: search query string with tokens in distant position
        file_name: name of the file being tested
    """
    result_close = File.objects.ranking_based_on_file_name(query_close)
    close_rank = None
    for result in result_close:
        if result.name == file_name:
            close_rank = result.rank
    result_far_away = File.objects.ranking_based_on_file_name(query_far_away)
    far_away_rank = None
    for result in result_far_away:
        if result.name == file_name:
            far_away_rank = result.rank
    check.is_true(close_rank is not None, "file not found in close results")
    check.is_true(far_away_rank is not None, "file not found in far away results")
    check.greater(close_rank, far_away_rank)


def assert_overfitting_token_count(query_exact_match: str, query_more_tokens: str, file_name: str):
    """Test that overfitting penalizes the ranking score.
    params:
        query_exact_match: search query string that exactly matches the file name
        query_more_tokens: search query string with additional tokens
        file_name: name of the file being tested
    """
    result_exact = File.objects.ranking_based_on_file_name(query_exact_match)
    exact_rank = None
    for result in result_exact:
        if result.name == file_name:
            exact_rank = result.rank
    result_more_tokens = File.objects.ranking_based_on_file_name(query_more_tokens)
    more_tokens_rank = None
    for result in result_more_tokens:
        print(result.name, result.rank)
        if result.name == file_name:
            more_tokens_rank = result.rank
    check.is_true(exact_rank is not None, "file not found in exact results")
    check.is_true(more_tokens_rank is not None, "file not found in more tokens results")
    check.greater(exact_rank, more_tokens_rank)


def assert_partial_token_match(
    query_partial: str, query_more_tokens_partial: str, file_name: str
):
    """Test that partial token matches rank lower than full token matches.
    params:
        query_partial: search query string with partial token match
        query_more_tokens_partial: search query string with additional tokens but partial matches
        file_name: name of the file being tested
    """
    result_partial = File.objects.ranking_based_on_file_name(query_partial)
    partial_rank = None
    for result in result_partial:
        if result.name == file_name:
            partial_rank = result.rank
    result_more_partial = File.objects.ranking_based_on_file_name(
        query_more_tokens_partial
    )
    more_partial_rank = None
    for result in result_more_partial:
        if result.name == file_name:
            more_partial_rank = result.rank
    check.is_true(partial_rank is not None, "file not found in partial results")
    check.is_true(more_partial_rank is not None, "file not found in more partial results")
    check.greater(more_partial_rank, partial_rank)
