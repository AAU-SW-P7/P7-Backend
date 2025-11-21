"""API for fetching and saving Google Drive files."""

import os
from ninja import Router, Header
from django.http import JsonResponse
from django_q.tasks import async_task
# Google libs
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from repository.service import get_tokens, get_service
from repository.user import get_user
from p7.helpers import validate_internal_auth
from p7.get_google_drive_files.helper import (
    update_or_create_file,
    fetch_recursive_files,
    get_new_access_token,
)
from p7.download_google_drive_files.api import process_download_google_drive_files

fetch_google_drive_files_router = Router()


@fetch_google_drive_files_router.get("/")
def fetch_google_drive_files(
    request,
    user_id: str,
    x_internal_auth: str = Header(..., alias="x-internal-auth"),
):
    """Fetch and save Google Drive files for a given user.

    params:
        x_internal_auth (str): The internal auth header for validating the request.
        user_id (str): The ID of the user whose Google Drive files are to be fetched.
    """
    auth_resp = validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp

    user = get_user(user_id)
    if isinstance(user, JsonResponse):
        return user

    task_id = async_task(
        process_google_drive_files,
        user_id,
        cluster="high",
        group=f"Google-Drive-{user_id}"
    )
    return JsonResponse({"task_id": task_id, "status": "processing"}, status=202)

def process_google_drive_files(user_id):
    """Process and sync Google Drive files for a given user.
    params:
        user_id (str): The ID of the user whose Google Drive files are to be processed.
    Returns:
        list: A list of processed Google Drive files or a JsonResponse with an error message.
    """
    # Build credentials object. token may be stale; refresh() will update it.
    try:
        access_token, _, refresh_token = get_tokens(user_id, "google")
        service = get_service(user_id, "google")
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            scopes=["https://www.googleapis.com/auth/drive.metadata.readonly"],
        )

        access_token = get_new_access_token(
            service,
            creds,
            access_token,
        )

        # Build Drive service and list files
        drive_api = build("drive", "v3", credentials=creds)
        # Request all file fields and paginate through results
        files = fetch_recursive_files(
            drive_api,
            access_token,
            creds,
            refresh_token,
        )

        # Build a fast lookup for any item (files + folders)
        file_by_id = {file["id"]: file for file in files}

        for file in files:
            if file.get("trashed"): # If the file is in the trash, it should be skipped
                continue
            # Skip non-files (folders, shortcuts, etc)
            if file.get("mimeType", "") in (
                "application/vnd.google-apps.folder",
                "application/vnd.google-apps.shortcut",
                "application/vnd.google-apps.drive-sdk",
            ):  # https://developers.google.com/workspace/drive/api/guides/mime-types
                continue

            update_or_create_file(file, service, file_by_id)

        async_task(
            process_download_google_drive_files,
            user_id,
            cluster="high",
            group=f"Google-Drive-{user_id}"
        )

        return files

    except (ValueError, TypeError, KeyError, RuntimeError) as e:
        return JsonResponse({"error": str(e)}, status=500)
