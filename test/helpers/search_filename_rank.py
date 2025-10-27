"""Helper functions for testing filename search ranking."""

import os
import pytest_check as check
from django.db import connection

from repository.models import File


def assert_get_exact_match(query: str, filename_exact_match: str, filename_partial_match: str):
    """Test exact match ranking higher than partial matches.
    params:
        query: search query string for exact match
        query2: search query string for partial match
    """
    results = File.objects.smart_search(query)
    for result in results:
        print(f"File: {result.name}, Rank: {result.rank}")
    check.equal(results[0].name, filename_exact_match)
    check.equal(results[1].name, filename_partial_match)
    check.greater(results[0].rank, results[1].rank)
     
def assert_file_length(query, short_name, long_name):
    """Test shorter file names rank higher when tokens are the same.
    params:
        query: search query string
        short_name: name of the shorter file
        long_name: name of the longer file
    """
    results = File.objects.smart_search(query)
    check.equal(results[0].name, short_name)
    check.equal(results[1].name, long_name)
    check.greater(results[0].rank, results[1].rank)

def assert_token_position(query_close: str, query_far_away: str, file_name: str):
    """Test token position affects ranking.
    params: 
        query_close: search query string with tokens in similar position
        query_far_away: search query string with tokens in distant position
        file_name: name of the file being tested
    """
    result_close = File.objects.smart_search(query_close)
    check.equal(result_close[0].name, file_name)
    result_far_away = File.objects.smart_search(query_far_away)
    check.equal(result_far_away[0].name, file_name)
    check.greater(result_close[0].rank, result_far_away[0].rank)


def assert_overfitting_token_count(query_exact_match: str, query_more_tokens: str, file_name: object):
    """Test that overfitting penalizes the ranking score.
    params: 
        query_exact_match: search query string that exactly matches the file name
        query_more_tokens: search query string with additional tokens
        file_name: name of the file being tested
    """
    result_exact = File.objects.smart_search(query_exact_match)
    check.equal(result_exact[0].name, file_name)
    result_more_tokens = File.objects.smart_search(query_more_tokens)
    check.equal(result_more_tokens[0].name, file_name)
    check.greater(result_exact[0].rank, result_more_tokens[0].rank)

def assert_partial_token_match(query_partial: str, query_more_tokens_partial: str, file_name: str):
    """Test that partial token matches rank lower than full token matches.
    params:
        query_partial: search query string with partial token match
        query_more_tokens_partial: search query string with additional tokens but partial matches
        file_name: name of the file being tested
    """
    result_partial = File.objects.smart_search(query_partial)
    check.equal(result_partial[0].name, file_name)
    result_more_partial = File.objects.smart_search(query_more_tokens_partial)
    check.equal(result_more_partial[0].name, file_name)
    check.greater(result_more_partial[0].rank, result_partial[0].rank)
    # Test Exact Match - DONE
    # Test File Length - DONE 
    # Test Wrong Order NOT IMPLEMENTED YET
    # Test Tokens Position - DONE 
    # Test Partial Matches - DONE
    # Test overfitting to token count - DONE


    # Token1 Token2 Token3
    # Token1 Token3 Token2 - results in same rank as above when searching for Token2 Token3
    