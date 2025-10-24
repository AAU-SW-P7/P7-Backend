"""Tests for search_files_by_name functionality."""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Make the local backend package importable so `from p7...` works under pytest
repo_backend = Path(__file__).resolve().parents[1]  # backend/
sys.path.insert(0, str(repo_backend))
# Make the backend/test dir importable so you can use test_settings.py directly
sys.path.insert(0, str(repo_backend / "test"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_settings")

import django
django.setup()

import pytest

from repository.models import File, Service, User

pytestmark = pytest.mark.usefixtures("django_db_setup")

@pytest.fixture(name="test_data", scope='function', autouse=True)
def test_data_fixture():
    """Fixture to create test users, services, and files."""
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
        name="Token1 Token2 Token3 Token4 Token5.docx",
        extension="docx",
        downloadable=True,
        path="/report-user1.docx",
        link="http://dropbox/link1",
        size=1024,
        createdAt=datetime.now(),
        modifiedAt=datetime.now(),
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
        createdAt=datetime.now(),
        modifiedAt=datetime.now(),
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
        createdAt=datetime.now(),
        modifiedAt=datetime.now(),
    )
    
def test_exact_match():
    """Test exact match ranking higher than partial matches."""
    query = "Token1 Token2"
    results = File.objects.smart_search(query)
    query2 = "Token2 Token1"
    results2 = File.objects.smart_search(query2)
    assert results[0].name == "Token1 Token2"
    assert results[1].name == "Token2 Token1"
    print(f"Exact Match Rank: {results[0]}, Wrong Order Rank: {results[1].rank}")
    assert results[0].rank > results[1].rank
     
    # Test Exact Match
    # Test File Length
    # Test Wrong Order NOT IMPLEMENTED YET
    # Test Tokens Position
    # Test Partial Matches
    # Test overfitting to token count
    # Trim Similarity
    # Token1 Token2 Token3
    # Token1 Token3 Token2 - results in same rank as above when searching for Token2 Token3
    
    