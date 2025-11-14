"""Helper functions for testing save files endpoint."""

import os
import pytest_check as check
from django.db import connection
from django_q.tasks import result
from p7.helpers import smart_extension
from p7.get_google_drive_files.helper import build_google_drive_path
from repository.models import Service, User, File
from repository.file import remove_extension_from_ts_vector_smart
from repository.helpers import ts_tokenize

def assert_save_file_success(client, user_id, service_name):
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
    data = result(task_id=response.json().get("task_id")) if response.status_code == 202 else data

    check.equal(response.status_code, 202)
    check.is_instance(data, list)

    for file in data:
        check.is_instance(file, dict)
        if service_name == "dropbox":
            extension = smart_extension("dropbox", file["name"], file.get("mime_type"))
            path = file["path_display"]
            link = "https://www.dropbox.com/preview" + path

            db_file = File.objects.filter(
                serviceId__userId=user_id,
                serviceId__name=service_name,
                serviceFileId=file.get("id"),
                name=file.get("name"),
                extension=extension,
                downloadable=file.get("is_downloadable"),
                path=path,
                link=link,
                size=file.get("size"),
            )
            file_count = db_file.count()
            check.equal(file_count, 1)
            check_tokens_against_ts_vector(db_file)

        elif service_name == "google":
            # Skip non-files (folders, shortcuts, etc)
            if (
                file.get("mimeType", "") in (
                'application/vnd.google-apps.folder',
                'application/vnd.google-apps.shortcut',
                'application/vnd.google-apps.drive-sdk',
            )
            ):  # https://developers.google.com/workspace/drive/api/guides/mime-types
                continue
            file_by_id = {file["id"]: file for file in data}
            extension = smart_extension("google", file["name"], file.get("mimeType"))
            downloadable = file.get("capabilities", {}).get("canDownload")
            path = build_google_drive_path(file, file_by_id)

            db_file = File.objects.filter(
                serviceId__userId=user_id,
                serviceId__name=service_name,
                serviceFileId=file.get("id"),
                name=file.get("name"),
                extension=extension,
                downloadable=downloadable,
                path=path,
                link=file.get("webViewLink"),
                size=file.get("size", 0),
            )
            file_count = db_file.count()
            check.equal(file_count, 1)
            check_tokens_against_ts_vector(db_file)

        elif service_name == "onedrive":
            extension = smart_extension(
                "onedrive",
                file["name"],
                file.get("file", {}).get("mimeType"),
            )
            path = (
                (file.get("parentReference", {}).get("path", "")).replace(
                    "/drive/root:", ""
                )
                + "/"
                + file["name"]
            )

            db_file = File.objects.filter(
                serviceId__userId=user_id,
                serviceId__name=service_name,
                serviceFileId=file.get("id"),
                name=file.get("name"),
                extension=extension,
                downloadable=1,
                path=path,
                link=file.get("webUrl"),
                size=file.get("size", 0),
            )
            file_count = db_file.count()
            check.equal(file_count, 1)
            check_tokens_against_ts_vector(db_file)


def assert_save_file_invalid_auth(client, user_id):
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
    check.equal(response.json(), {"error": "Unauthorized - invalid x-internal-auth"})


def assert_save_file_missing_header(client, user_id):
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
    check.equal(
        response.json()
        in (
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["header", "x-internal-auth"],
                        "msg": "Field required",
                    }
                ]
            },
            {
                "detail": [
                    {
                        "type": "string_type",
                        "loc": ["header", "x-internal-auth"],
                        "msg": "Input should be a valid string",
                    }
                ]
            },
        ),
        True,
    )


def assert_save_file_missing_user_id(client):
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
    check.equal(
        response.json()
        in (
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["query", "user_id"],
                        "msg": "Field required",
                    },
                    {
                        "type": "missing",
                        "loc": ["header", "x-internal-auth"],
                        "msg": "Field required",
                    },
                ]
            },
            {
                "detail": [
                    {
                        "type": "string_type",
                        "loc": ["query", "user_id"],
                        "msg": "Input should be a valid string",
                    },
                    {
                        "type": "string_type",
                        "loc": ["header", "x-internal-auth"],
                        "msg": "Input should be a valid string",
                    },
                ]
            },
        ),
        True,
    )


def check_tokens_against_ts_vector(file: File, ts_type: str = None):
    """
    Checks tokenized file name against the ts_vector stored in the database
    """
    # Get produced ts vector for the file
    ts = file.get().ts
    file_name = file.get().name
    # Check that each token in the name appears as a term in our tsvector
    # To produce the tokens PostgreSQL's tsvector parser is used
    # NOTE: this currently only takes into account the file name
    name_tokens = ts_tokenize(file_name, "simple")

    for i, token in enumerate(name_tokens):
        token_extension = smart_extension(file.get().serviceId.name, file_name)
        if token_extension and token.endswith(token_extension):
            name_tokens[i] = token[: -len(token_extension)]
    remove_extension_from_ts_vector_smart(file.get())
    for token in name_tokens:
        check.equal(token.lower() in ts, True)

