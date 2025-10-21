"""Tests for search_files_by_name functionality."""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_settings")

import django
django.setup()

from hypothesis import given, strategies as st

# Make the local backend package importable so `from p7...` works under pytest
repo_backend = Path(__file__).resolve().parents[1]  # backend/
sys.path.insert(0, str(repo_backend))
# Make the backend/test dir importable so you can use test_settings.py directly
sys.path.insert(0, str(repo_backend / "test"))

import pytest
from helpers.search_filename import (
    assert_search_filename_basic_sanitization,
    assert_search_filename_sanitization,
    assert_search_filename_success,
    assert_search_filename_no_results,
    assert_search_filename_multiple_results,
    assert_search_filename_empty_string,
    assert_search_filename_orm_injection_resistance,
    assert_tokenize_basic,
    assert_tokenize_empty,
    assert_tokenize_hypothesis,
    assert_tokenize_numbers,
)
from p7.search_files_by_filename.api import sanitize_user_search, tokenize
from repository.models import File, Service, User

pytestmark = pytest.mark.usefixtures("django_db_setup")

def test_search_filename():
    """Test searching files by filename for different users and scenarios."""
    user1 = User.objects.create()
    service1 = Service.objects.create(
        userId=user1,
        oauthType="DROPBOX",
        oauthToken="fake-token-1",
        accessToken="fake-access-1",
        accessTokenExpiration=datetime.now() + timedelta(days=365),
        refreshToken="fake-refresh-1",
        name="Dropbox",
        accountId="acc1",
        email="user1@example.com",
        scopeName="files.read",
    )
    file1 = File.objects.create(
        serviceId=service1,
        serviceFileId="file-1",
        name="report-user1.docx",
        extension="docx",
        downloadable=True,
        path="/report-user1.docx",
        link="http://dropbox/link1",
        size=1024,
        createdAt=datetime.now(),
        modifiedAt=datetime.now(),
    )
    file11 = File.objects.create(
        serviceId=service1,
        serviceFileId="file-11",
        name="user1-file-other-11.docx",
        extension="docx",
        downloadable=True,
        path="/report-user1.docx",
        link="http://dropbox/link11",
        size=1024,
        createdAt=datetime.now(),
        modifiedAt=datetime.now(),
    )

    user2 = User.objects.create()
    service2 = Service.objects.create(
        userId=user2,
        oauthType="GOOGLE",
        oauthToken="fake-token-2",
        accessToken="fake-access-2",
        accessTokenExpiration=datetime.now() + timedelta(days=365),
        refreshToken="fake-refresh-2",
        name="GoogleDrive",
        accountId="acc2",
        email="user2@example.com",
        scopeName="files.read",
    )

    file2 = File.objects.create(
        serviceId=service2,
        serviceFileId="file-2",
        name="report-user2.pdf",
        extension="pdf",
        downloadable=True,
        path="/report-user2.pdf",
        link="http://google/link2",
        size=2048,
        createdAt=datetime.now(),
        modifiedAt=datetime.now(),
    )
    file22 = File.objects.create(
        serviceId=service2,
        serviceFileId="file-22",
        name="user2-random-report-file.pdf",
        extension="pdf",
        downloadable=True,
        path="/report-user2.pdf",
        link="http://google/link2",
        size=2048,
        createdAt=datetime.now(),
        modifiedAt=datetime.now(),
    )

    # user1 has "report-user1.docx" and "user1-file-report-11.docx"
    assert_search_filename_success(
        user_id=user1.id,
        query="report",
        expected_name=[file1.name]
    )

    assert_search_filename_success(
        user_id=user2.id,
        query="report",
        expected_name=[file2.name, file22.name]
    )

    assert_search_filename_no_results(
        user_id=user1.id,
        query="report-user2",
        expected_count=0,
    )

    assert_search_filename_multiple_results(
        user_id=user1.id,
        queries=["report", "other"],
        expected_name=[file1.name, file11.name],
    )

    assert_search_filename_empty_string(
        user_id=user1.id,
        query="''",
        expected_count=0,
    )

    assert_search_filename_orm_injection_resistance(
        user_id=user1.id,
        query="'; SELECT * FROM files WHERE userId = 2; --",
        expected_count=0,
    )

@given(st.text())
def test_sanitize_user_search_hypothesis(input_str):
    """Test sanitize_user_search with various inputs using Hypothesis.
    params:
        input_str (str): Randomly generated input string.
    """
    assert_search_filename_sanitization(input_str)

def test_sanitize_user_search_basic():
    """Test sanitize_user_search with basic cases."""
    assert_search_filename_basic_sanitization()

def test_tokenize_search_string():
    """Test tokenize basic functionality"""
    assert_tokenize_basic("We should have five tokens", ["We", "should", "have", "five", "tokens"])

def test_tokenize_search_empty():
    """Test tokenize with an empty string"""
    assert_tokenize_empty("", [])

def test_tokenize_search_numbers():
    """Test tokenize with numbers in the string"""
    assert_tokenize_numbers("Project 2024 Plan", ["Project", "2024", "Plan"])

@given(st.text())
def test_tokenize_search_hypothesis(input_str):
    """Test tokenize with various inputs using Hypothesis."""
    assert_tokenize_hypothesis(input_str)
