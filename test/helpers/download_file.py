"""Helper functions for testing save files endpoint."""

import os
import pytest_check as check
from django.db import connection
from p7.helpers import smart_extension
from p7.get_google_drive_files.helper import build_google_drive_path
from repository.models import Service, User, File

def assert_download_file_success(client, user_id, service_name):
    """Helper function to assert successful creation of a service.
    params:
        client: Test client to make requests.
        user_id: ID of the user creating the service.
        service_name: Name of the service.
    """
    # Get initial user count
    initial_user_count = User.objects.count()
    initial_service_count = Service.objects.filter(
        userId=user_id,
        name=service_name,
    ).count()

    # Assuming 3 users are already created for service creation
    check.equal(initial_user_count, 3)
    check.equal(initial_service_count, 1)

    response = client.get(
        f"/?user_id={user_id}",
        headers={"x-internal-auth": os.getenv("INTERNAL_API_KEY")},
    )

    data = response.json()
    
    check.equal(response.status_code, 200)
    check.is_instance(data, list)

    for file in data:
        check.is_instance(file, dict)
        if service_name == "dropbox":
            db_file = File.objects.filter(
                serviceFileId=file.get("id"),
            )
            file_count = db_file.count()
            
            check.equal(file_count, 1)
            
            check_tokens_against_ts_vector(db_file, file.get("content"))

        elif service_name == "google":
            db_file = File.objects.filter(
                serviceFileId=file.get("id"),
            )
            file_count = db_file.count()

            check.equal(file_count, 1)
            
            check_tokens_against_ts_vector(db_file, file.get("content"))

        elif service_name == "onedrive":
            db_file = File.objects.filter(
                serviceFileId=file.get("id"),
            )
            file_count = db_file.count()
            
            check.equal(file_count, 1)
            
            check_tokens_against_ts_vector(db_file, file.get("content"))

def assert_download_file_invalid_auth(client, user_id):
    """Helper function to assert finding a service with invalid auth.

    params:
        client: Test client to make requests.
        user_id: ID of the user.
    """
    try:
        response = client.get(
            f"/?user_id={user_id}", headers={"x-internal-auth": "invalid_token"}
        )
    except Exception as e:
        print(f"Exception during GET request: {e}")
        raise

    check.equal(response.status_code, 401)
    check.equal(response.json() is not None, True)
    check.equal(isinstance(response.json(), dict), True)
    check.equal(response.json(), {
            "error": "Unauthorized - invalid x-internal-auth"
        }
    )

def assert_download_file_missing_header(client, user_id):
    """Helper function to assert finding a user by user_id with missing auth header.

    params:
        client: Test client to make requests.
        user_id: ID of the user.
    """
    try:
        response = client.get(f"/?user_id={user_id}")
    except Exception as e:
        print(f"Exception during GET request: {e}")
        raise

    check.equal(response.status_code, 422)
    check.equal(response.json() is not None, True)
    check.equal(isinstance(response.json(), dict), True)
    check.equal(response.json() in ({
        'detail': [
            {'type': 'missing', 'loc': ['header', 'x-internal-auth'], 'msg': 'Field required'}
        ]
    }, {
        'detail': [
            {'type': 'string_type', 'loc': ['header', 'x-internal-auth'], 'msg': 'Input should be a valid string'}
        ]
    }), True)


def assert_download_file_missing_user_id(client):
    """Helper function to assert finding a service by user ID with missing user ID.

    params:
        client: Test client to make requests.
    """
    try:
        response = client.get(
            "/",
        )
    except Exception as e:
        print(f"Exception during GET request: {e}")
        raise

    check.equal(response.status_code, 422)
    check.equal(response.json() is not None, True)
    check.equal(isinstance(response.json(), dict), True)
    check.equal(response.json() in ({
        'detail': [
            {'type': 'missing', 'loc': ['query', 'user_id'], 'msg': 'Field required'},
            {'type': 'missing', 'loc': ['header', 'x-internal-auth'], 'msg': 'Field required'}
        ]
    }, {
        'detail': [
            {'type': 'string_type', 'loc': ['query', 'user_id'], 'msg': 'Input should be a valid string'},
            {'type': 'string_type', 'loc': ['header', 'x-internal-auth'], 'msg': 'Input should be a valid string'}
        ]
    }), True)

def check_tokens_against_ts_vector(file: File, content: str):
    """
    Checks tokenized file name and content against the tsvector stored in the database
    """
    # Get produced ts vector for the file
    ts = file.get().ts
    file_name = file.get().name

    # Tokenize & lexize file name
    name_tokens = ts_tokenize_simple(file_name)

    # Tokenize & lexize content (if any)
    content_lexemes = []
    if content:
        content_tokens = ts_tokenize_english(content)
        content_lexemes = [token for token in content_tokens]

    # Combine and dedupe lexemes from name and content
    all_lexemes = set(name_tokens + content_lexemes)

    # Ensure each lexeme appears in the stored tsvector
    for lex in all_lexemes:
        check.equal(lex in ts, True)

def ts_tokenize_simple(text):
    "Tokenizes a string using PostgreSQL's tsvector parser"
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT unnest(tsvector_to_array(to_tsvector('simple', %s)))", [text]
        )
        return [row[0] for row in cursor.fetchall()]

def ts_tokenize_english(text):
    "Tokenizes a string using PostgreSQL's tsvector parser"
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT unnest(tsvector_to_array(to_tsvector('english', %s)))", [text]
        )
        return [row[0] for row in cursor.fetchall()]
