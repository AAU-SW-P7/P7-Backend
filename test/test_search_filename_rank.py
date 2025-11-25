"""Tests for search_files_by_name functionality."""

import os
import sys
from pathlib import Path
from datetime import timedelta

# Make the local backend package importable so `from p7...` works under pytest
repo_backend = Path(__file__).resolve().parents[1]  # backend/
sys.path.insert(0, str(repo_backend))
# Make the backend/test dir importable so you can use test_settings.py directly
sys.path.insert(0, str(repo_backend / "test"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_settings")

import django
django.setup()
from django.utils import timezone
from django.contrib.postgres.search import SearchVector, Value
import pytest

from helpers.search_filename_rank import (
    assert_get_exact_match,
    assert_file_length,
    assert_token_position,
    assert_overfitting_token_count,
    assert_partial_token_match
)
from repository.models import File, Service, User


pytestmark = pytest.mark.usefixtures("django_db_setup")

@pytest.fixture(name="test_data", scope='module', autouse=True)
def test_data_fixture():
    """Fixture to create test users, services, and files."""
    user1 = User.objects.create()
    service1 = Service.objects.create(
        userId=user1,
        oauthType="DROPBOX",
        oauthToken="fake-token-1",
        accessToken="fake-access-1",
        accessTokenExpiration=timezone.now() + timedelta(days=365),
        refreshToken="fake-refresh-1",
        name="Dropbox",
        accountId="acc1",
        email="user1@example.com",
        scopeName="files.read",
    )
    file1 = File.objects.create(
        serviceId=service1,
        serviceFileId="file-1",
        name="Token1 Token2 Token3 Token4 Token5.docx",
        extension="docx",
        downloadable=True,
        path="/report-user1.docx",
        link="http://dropbox/link1",
        size=1024,
        createdAt=timezone.now(),
        modifiedAt=timezone.now(),
        tsFilename=SearchVector(Value("Token1 Token2 Token3 Token4 Token5"), \
                                               weight="A", config='simple'),
        tsContent=SearchVector(Value(""), weight="B", config='english'),
    )
    file2 = File.objects.create(
        serviceId=service1,
        serviceFileId="file-2",
        name="Token1 Token2",
        extension="docx",
        downloadable=True,
        path="/report-user1.docx",
        link="http://dropbox/link1",
        size=1024,
        createdAt=timezone.now(),
        modifiedAt=timezone.now(),
        tsFilename=SearchVector(Value("Token1 Token2"), weight="A", config='simple'),
        tsContent=SearchVector(Value(""), weight="B", config='english'),
    )
    file3 = File.objects.create(
        serviceId=service1,
        serviceFileId="file-3",
        name="Token2 Token1",
        extension="docx",
        downloadable=True,
        path="/report-user1.docx",
        link="http://dropbox/link1",
        size=1024,
        createdAt=timezone.now(),
        modifiedAt=timezone.now(),
        tsFilename=SearchVector(Value("Token2 Token1"), weight="A", config='simple'),
        tsContent=SearchVector(Value(""), weight="B", config='english'),
    )
    return {
        "user1": user1,
        "service1": service1,
        "file1": file1,
        "file2": file2,
        "file3": file3,
    }


def test_exact_match(test_data):
    """Test exact match ranking higher than partial matches."""
    assert_get_exact_match("Token1 Token2", test_data["file2"].name, test_data["file3"].name)

def test_file_name_length(test_data):
    """Test that shorter file names rank higher than longer ones."""
    assert_file_length("Token1", test_data["file2"].name, test_data["file1"].name)

def test_token_position(test_data):
    """Test that files with tokens in the beginning rank higher."""
    assert_token_position("Token1 Token2", "Token1 Token3", test_data["file1"].name)

def test_overfitting_token_count(test_data):
    """Test that overfitting penalizes the ranking score."""
    assert_overfitting_token_count("Token1 Token2", "Token1 Token2 Token3", test_data["file3"].name)

def test_partial_token_match(test_data):
    """Test that partial token matches rank lower than full token matches."""
    assert_partial_token_match("Token1", "Token1 Token2", test_data["file1"].name)
