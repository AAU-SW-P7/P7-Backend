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

django.setup()
from django.utils import timezone
from django.contrib.postgres.search import SearchVector, Value

import pytest
from helpers.search_content import assert_query_file_by_content
from repository.models import File, Service, User

pytestmark = pytestmark = pytest.mark.django_db


@pytest.fixture(name="test_data", scope="function", autouse=True)
def test_data_fixture():
    """Fixture to create test users, services, and files."""
    user1 = User.objects.create()
    service1 = Service.objects.create(
        userId=user1,
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
    user1_doc1 = File.objects.create(
        serviceId=service1,
        serviceFileId="user1-doc1",
        name="user1-doc1",
        extension=".whatever",
        downloadable=True,
        path="/Something about corona",
        link="http://cloudservice/Something about corona",
        size=1024,
        createdAt=timezone.now(),
        modifiedAt=timezone.now(),
        tsFilename=SearchVector(
            Value("Something about corona"), weight="A", config="simple"
        ),
        tsContent=SearchVector(
            Value("Corona virus is something that was very annoying"),
            weight="B",
            config="english",
        ),
    )
    user1_doc2 = File.objects.create(
        serviceId=service1,
        serviceFileId="user1-doc2",
        name="user1-doc2",
        extension=".whatever",
        downloadable=True,
        path="/The president of the united states does it again",
        link="http://cloudservice/The president of the united states does it again",
        size=1024,
        createdAt=timezone.now(),
        modifiedAt=timezone.now(),
        tsFilename=SearchVector(
            Value("The president of the united states does it again"),
            weight="A",
            config="simple",
        ),
        tsContent=SearchVector(
            Value("The president of the united states is orange"),
            weight="B",
            config="english",
        ),
    )
    user1_doc3 = File.objects.create(
        serviceId=service1,
        serviceFileId="user1-doc3",
        name="user1-doc3",
        extension=".whatever",
        downloadable=True,
        path="/Novo nordisk stock",
        link="http://cloudservice/Novo nordisk stock",
        size=1024,
        createdAt=timezone.now(),
        modifiedAt=timezone.now(),
        tsFilename=SearchVector(
            Value("Novo nordisk stock"), weight="A", config="simple"
        ),
        tsContent=SearchVector(
            Value("Novo nordisk stock drops to a record low"),
            weight="B",
            config="english",
        ),
    )

    user2 = User.objects.create()
    service2 = Service.objects.create(
        userId=user2,
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
    user2_doc1 = File.objects.create(
        serviceId=service2,
        serviceFileId="user2-doc1",
        name="user2-doc1",
        extension=".whatever",
        downloadable=True,
        path="/A file with the same content as for user 1",
        link="http://cloudservice/A file with the same content as for user 1",
        size=1024,
        createdAt=timezone.now(),
        modifiedAt=timezone.now(),
        tsFilename=SearchVector(
            Value("A file with the same content as for user 1"),
            weight="A",
            config="simple",
        ),
        tsContent=SearchVector(
            Value("Novo nordisk stock drops to a record low"),
            weight="B",
            config="english",
        ),
    )

    return {
        "user1": user1,
        "service1": service1,
        "user1_doc1": user1_doc1,
        "user1_doc2": user1_doc2,
        "user1_doc3": user1_doc3,
        "user2": user2,
        "service2": service2,
        "user2_doc1": user2_doc1,
    }


def test_user_search_for_exact_match(test_data):
    """
    User 1 searches for "The president of the united states is orange"
    """
    assert_query_file_by_content(
        user_id=test_data["user1"].id,
        query=["The president of the united states is orange"],
        expected_ids=[test_data["user1_doc2"]],
    )


def test_user_search_for_partial_match(test_data):
    """
    User 1 searches for "Corona"
    """
    assert_query_file_by_content(
        user_id=test_data["user1"].id,
        query=["Corona"],
        expected_ids=[test_data["user1_doc1"]],
    )


def test_user_search_multiple_results(test_data):
    """
    User 1 searches for "Corona Novo Nordisk"
    """
    assert_query_file_by_content(
        user_id=test_data["user1"].id,
        query=["Corona Novo Nordisk"],
        expected_ids=[test_data["user1_doc1"], test_data["user1_doc3"]],
    )
