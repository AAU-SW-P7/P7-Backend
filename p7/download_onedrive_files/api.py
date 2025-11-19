"""API endpoint to download OneDrive files for a user."""

# Microsoft libs
import os
import msal
import requests

from ninja import Router, Header
from django.http import JsonResponse
from django.utils import timezone
from django_q.tasks import async_task
from repository.file import update_tsvector, fetch_downloadable_files
from repository.service import get_tokens, get_service
from repository.user import get_user
from p7.helpers import validate_internal_auth, parse_file_content
from p7.get_onedrive_files.helper import get_new_access_token

download_onedrive_files_router = Router()
@download_onedrive_files_router.get("/")
def download_onedrive_files(
    request,
    user_id: str,
    x_internal_auth: str = Header(..., alias="x-internal-auth"),
):
    """Schedule download OneDrive files for a given user.

    params:
        x_internal_auth (str): The internal auth header for validating the request.
        user_id (str): The ID of the user whose OneDrive files are to be fetched.
    """

    auth_resp = validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp

    user = get_user(user_id)

    if isinstance(user, JsonResponse):
        return user

    task_id = async_task(
        process_download_onedrive_files,
        user_id,
        cluster="high",
        group=f"Onedrive-{user_id}"
        )
    return JsonResponse({"task_id": task_id, "status": "processing"}, status=202)


def process_download_onedrive_files(user_id):
    """Download OneDrive files for a given user.
    
    params:
        user_id: The ID of the user whose OneDrive files are to be fetched.
    """
    access_token, access_token_expiration, refresh_token = get_tokens(
        user_id, "onedrive"
    )
    service = get_service(user_id, "onedrive")

    try:
        app = msal.ConfidentialClientApplication(
            os.getenv("MICROSOFT_CLIENT_ID"),
            authority="https://login.microsoftonline.com/common",
            client_credential=os.getenv("MICROSOFT_CLIENT_SECRET"),
        )

        access_token = get_new_access_token(
            service,
            app,
            access_token,
            access_token_expiration,
            refresh_token,
        )

        files = download_recursive_files(
            service,
            app,
            access_token,
            access_token_expiration,
            refresh_token,
        )

        return files
    except (KeyError, ValueError, ConnectionError, RuntimeError, TypeError, OSError) as e:
        response = JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)
        return response


def download_recursive_files(
    service,
    app,
    access_token,
    access_token_expiration,
    refresh_token,
):
    """Download files recursively from a user's OneDrive account.

    Returns a list of File-like objects (from the `repository.models.File` type)
    or False on error.
    """

    # Tell static type checkers that we expect a list of File objects here.
    onedrive_files = fetch_downloadable_files(service)
    if not onedrive_files:
        print("No downloadable OneDrive files found for user.")

        return []  # Return empty as it has a filetype we do not handle yet

    files = []
    errors = []
    for onedrive_file in onedrive_files:
        file_id = onedrive_file.serviceFileId

        access_token = get_new_access_token(
            service,
            app,
            access_token,
            access_token_expiration,
            refresh_token,
        )

        try:
            response = requests.post(
                f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}/content",
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
                timeout=30,
            )

            if response.status_code != 200:
                raise RuntimeError(
                    f"Onedrive download failed for {file_id}: \
                    {response.status_code} - {response.text}"
                )
        except RuntimeError as e:
            errors.append(f"Failed to download {file_id}: {e}")
            continue

        onedrive_content = parse_file_content(
            response.content,
            onedrive_file,
        )

        if onedrive_content:
            try:
                update_tsvector(
                    onedrive_file,
                    onedrive_content,
                    timezone.now(),
                )

                files.append({
                    "id": onedrive_file.serviceFileId,
                    "content": onedrive_content,
                })
            except RuntimeError as e:
                errors.append(f"Error updating tsvector for file {file_id}: {str(e)}")

    if errors:
        print("Errors occurred during OneDrive file downloads:")
        for error in errors:
            print(error)

    return files
