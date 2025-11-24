"""API for fetching and saving Google Drive files."""

import io
import os
from django.utils import timezone
from django.http import JsonResponse
from ninja import Router, Header
from django_q.tasks import async_task

# Google libs
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

from p7.helpers import validate_internal_auth, parse_file_content
from p7.get_google_drive_files.helper import get_new_access_token
from repository.file import update_tsvector, fetch_downloadable_files
from repository.service import get_tokens, get_service
from repository.user import get_user

download_google_drive_files_router = Router()


@download_google_drive_files_router.get("/")
def download_google_drive_files(
    request,
    user_id: str,
    x_internal_auth: str = Header(..., alias="x-internal-auth"),
):
    """Schedule download Google Drive files for a given user.

    params:
        x_internal_auth (str): The internal auth header for validating the request.
        user_id (str): The ID of the user whose Google Drive files are to be downloaded.
    """
    auth_resp = validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp

    user = get_user(user_id)
    if isinstance(user, JsonResponse):
        return user

    task_id = async_task(
        process_download_google_drive_files,
        user_id,
        cluster="high",
        group=f"Google-Drive-{user_id}",
    )
    return JsonResponse({"task_id": task_id, "status": "processing"}, status=202)


def process_download_google_drive_files(user_id):
    """Download Google Drive files for a given user.
    params:
        user_id: The ID of the user whose Google Drive files are to be downloaded.
    """
    access_token, _, refresh_token = get_tokens(user_id, "google")
    service = get_service(user_id, "google")

    try:
        # Build credentials object. token may be stale; refresh() will update it.
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            scopes=["https://www.googleapis.com/auth/drive.readonly"],
        )

        access_token = get_new_access_token(
            service,
            creds,
            access_token,
        )

        # Build Drive service and list files
        drive_api = build("drive", "v3", credentials=creds)

        files = download_recursive_files(
            drive_api,
            creds,
            service,
            access_token,
        )

        return files
    except (
        KeyError,
        ValueError,
        ConnectionError,
        RuntimeError,
        TypeError,
        OSError,
    ) as e:
        response = JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)
        return response


"""API for fetching and saving Google Drive files."""

import io
import os
from django.utils import timezone
from django.http import JsonResponse
from ninja import Router, Header
from django_q.tasks import async_task

# Google libs
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

from p7.helpers import validate_internal_auth, parse_file_content
from p7.get_google_drive_files.helper import get_new_access_token
from repository.file import update_tsvector, fetch_downloadable_files
from repository.service import get_tokens, get_service
from repository.user import get_user

download_google_drive_files_router = Router()


@download_google_drive_files_router.get("/")
def download_google_drive_files(
    request,
    user_id: str,
    x_internal_auth: str = Header(..., alias="x-internal-auth"),
):
    """Schedule download Google Drive files for a given user.

    params:
        x_internal_auth (str): The internal auth header for validating the request.
        user_id (str): The ID of the user whose Google Drive files are to be downloaded.
    """
    auth_resp = validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp

    user = get_user(user_id)
    if isinstance(user, JsonResponse):
        return user

    task_id = async_task(
        process_download_google_drive_files,
        user_id,
        cluster="high",
        group=f"Google-Drive-{user_id}",
    )
    return JsonResponse({"task_id": task_id, "status": "processing"}, status=202)


def process_download_google_drive_files(user_id):
    """Download Google Drive files for a given user.
    params:
        user_id: The ID of the user whose Google Drive files are to be downloaded.
    """
    access_token, _, refresh_token = get_tokens(user_id, "google")
    service = get_service(user_id, "google")

    try:
        # Build credentials object. token may be stale; refresh() will update it.
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            scopes=["https://www.googleapis.com/auth/drive.readonly"],
        )

        access_token = get_new_access_token(
            service,
            creds,
            access_token,
        )

        # Build Drive service and list files
        drive_api = build("drive", "v3", credentials=creds)

        files = download_recursive_files(
            drive_api,
            creds,
            service,
            access_token,
        )

        return files
    except (
        KeyError,
        ValueError,
        ConnectionError,
        RuntimeError,
        TypeError,
        OSError,
    ) as e:
        response = JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)
        return response


def download_recursive_files(
    drive_api,
    creds,
    service,
    access_token,
):
    """Download files recursively from a user's Google Drive account."""

    google_drive_files = fetch_downloadable_files(service)
    if not google_drive_files:
        print("No downloadable Google Drive files found for user.")

        return []

    files = []
    errors = []
    for google_drive_file in google_drive_files:
        file_id = google_drive_file.serviceFileId

        access_token = get_new_access_token(
            service,
            creds,
            access_token,
        )

        try:
            try:
                request = drive_api.files().export(
                    fileId=file_id, mimeType="text/plain"
                )

                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
            except (HttpError, RuntimeError):
                request = drive_api.files().get_media(fileId=file_id)

                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()

            google_drive_content = parse_file_content(
                fh.getvalue(),
                google_drive_file,
            )

            update_tsvector(
                google_drive_file,
                google_drive_content,
                timezone.now(),
            )

            files.append(
                {
                    "id": file_id,
                    "content": google_drive_content,
                }
            )

        except RuntimeError as e:
            errors.append(f"Error updating tsvector for file {file_id}: {str(e)}")

    if errors:
        print("Errors occurred during Google Drive file downloads:")
        for error in errors:
            print(error)

    return files
