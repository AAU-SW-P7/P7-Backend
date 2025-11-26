"""Tests for search (content) functionality."""

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
from django.utils import timezone
from django.contrib.postgres.search import SearchVector, Value
from django.db.models import Q

django.setup()

import pytest

from helpers.search_content_rank import (
    assert_files_appear_in_specified_order,
    assert_files_have_same_rank,
)
from repository.models import File, Service, User

pytestmark = pytest.mark.django_db


@pytest.fixture(name="test_data", scope="function", autouse=True)
def test_data_fixture():
    """Fixture to create test users, services, and files."""
    user = User.objects.create()
    service = Service.objects.create(
        userId=user,
        oauthType="type1",
        oauthToken="token1",
        accessToken="access1",
        accessTokenExpiration=timezone.now() + timedelta(days=365),
        refreshToken="refresh1",
        name="cloudservice",
        accountId="account1",
        email="user1@example.com",
        scopeName="files.read",
    )
    doc1 = File.objects.create(
        serviceId=service,
        serviceFileId="doc1",
        name="Document 1 - Ranking",
        extension=".whatever",
        downloadable=True,
        path="/Document 1 - Ranking",
        link="http://cloudservice/Document 1 - Ranking",
        size=1024,
        createdAt=timezone.now(),
        modifiedAt=timezone.now(),
        tsFilename=SearchVector(
            Value("Document 1 - Ranking"), weight="A", config="simple"
        ),
        tsContent=SearchVector(
            Value("I like big burgers"), weight="B", config="english"
        ),
    )
    doc2 = File.objects.create(
        serviceId=service,
        serviceFileId="doc2",
        name="Document 2 - Ranking",
        extension=".whatever",
        downloadable=True,
        path="/Document 2 - Ranking",
        link="http://cloudservice/Document 2 - Ranking",
        size=1024,
        createdAt=timezone.now(),
        modifiedAt=timezone.now(),
        tsFilename=SearchVector(
            Value("Document 2 - Ranking"), weight="A", config="simple"
        ),
        tsContent=SearchVector(
            Value("Mega like mega burgers"), weight="B", config="english"
        ),
    )
    doc3 = File.objects.create(
        serviceId=service,
        serviceFileId="doc3",
        name="Document 3 - Ranking",
        extension=".whatever",
        downloadable=True,
        path="/Document 3 - Ranking",
        link="http://cloudservice/Document 3 - Ranking",
        size=1024,
        createdAt=timezone.now(),
        modifiedAt=timezone.now(),
        tsFilename=SearchVector(
            Value("Document 3 - Ranking"), weight="A", config="simple"
        ),
        tsContent=SearchVector(Value("Mega burgers"), weight="B", config="english"),
    )
    doc4 = File.objects.create(
        serviceId=service,
        serviceFileId="doc4",
        name="Document 4 - Ranking",
        extension=".whatever",
        downloadable=True,
        path="/Document 4 - Ranking",
        link="http://cloudservice/Document 4 - Ranking",
        size=1024,
        createdAt=timezone.now(),
        modifiedAt=timezone.now(),
        tsFilename=SearchVector(
            Value("Document 4 - Ranking"), weight="A", config="simple"
        ),
        tsContent=SearchVector(Value("Like burgers big"), weight="B", config="english"),
    )

    return {
        "user": user,
        "service": service,
        "doc1": doc1,
        "doc2": doc2,
        "doc3": doc3,
        "doc4": doc4,
    }


def test_user_search_for_exact_match(test_data):
    """
    Test user1 searches for 'mega like mega burgers'
    The ranking should be:
    1) Doc 2 (contains all words)
    2) Doc 3 (contains "mega" and "burgers")
    3) Doc 1 (contains 'burgers' ; Length = 3 words) (remember stop words are removed)
    4) Doc 4 (contains 'brugers' ; Length = 3 words)
    params:
        test_data: Fixture containing test users and files.
    """
    assert_files_appear_in_specified_order(
        query="mega like mega burgers",
        ordered_files=[
            test_data["doc2"],
            test_data["doc3"],
            test_data["doc1"],
            test_data["doc4"],
        ],
        base_filter=Q(serviceId=test_data["service"]),
    )


def test_user_search_for_partial_match(test_data):
    """
    Test user searches for 'like burgers'
    The ranking should be:
    1) Doc 1 (I like big burgers) - 3 Words, contains both words
    2) Doc 4 (Like burgers big) - 3 Words, contains both words
    3) Doc 2 (Mega like mega burgers) - 4 Words, contains both
    4) Doc 3 (Mega burgers) - Only contains one of the words
    Note Doc 1 and Doc 4 has same rank
    params:
        test_data: Fixture containing test users and files.
    """
    assert_files_appear_in_specified_order(
        query="like burgers",
        ordered_files=[
            test_data["doc1"],
            test_data["doc4"],
            test_data["doc2"],
            test_data["doc3"],
        ],
        base_filter=Q(serviceId=test_data["service"]),
    )


def test_user_search_for_equally_ranked_files(test_data):
    """
    Test user searches for 'big'
    The ranking should be equal for:
    1) Doc 1 ("I like big burgers")
    4) Doc 4 ("Like burgers big")
    params:
        test_data: Fixture containing test users and files.
    """
    assert_files_have_same_rank(
        query="big", base_filter=Q(serviceId=test_data["service"])
    )
