"""API endpoint to download Dropbox files for a user."""
import json
from datetime import datetime
import requests

from ninja import Router, Header
from django.http import JsonResponse
from p7.helpers import validate_internal_auth, parse_file_content
from p7.get_dropbox_files.helper import get_new_access_token
from repository.file import update_tsvector, fetch_downloadable_files
from repository.service import get_tokens, get_service
from repository.user import get_user

download_dropbox_files_router = Router()
@download_dropbox_files_router.get("/")
def download_dropbox_files(
    request,
    user_id: str,
    x_internal_auth: str = Header(..., alias="x-internal-auth"),
):
    """Download Dropbox files for a given user.

    params:
        x_internal_auth (str): The internal auth header for validating the request.
        user_id (str): The ID of the user whose Dropbox files are to be fetched.
    """
    auth_resp = validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp

    user = get_user(user_id)
    if isinstance(user, JsonResponse):
        return user

    access_token, access_token_expiration, refresh_token = get_tokens(
        user_id, "dropbox"
    )
    service = get_service(user_id, "dropbox")

    try:
        access_token, access_token_expiration = get_new_access_token(
            service,
            access_token,
            access_token_expiration,
            refresh_token,
        )

        files = download_recursive_files(
            service,
            access_token,
            access_token_expiration,
            refresh_token,
        )

        return JsonResponse(files, safe=False)
    except (KeyError, ValueError, ConnectionError, RuntimeError, TypeError, OSError) as e:
        response = JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)
        return response


def download_recursive_files(
    service,
    access_token,
    access_token_expiration,
    refresh_token,
):
    """Download files recursively from a user's Dropbox account."""

    dropbox_files = fetch_downloadable_files(service)
    if not dropbox_files:
        print("No downloadable Dropbox files found for user.")

        return []

    files = []
    errors = []
    for dropbox_file in dropbox_files:
        file_id = dropbox_file.serviceFileId

        access_token, access_token_expiration = get_new_access_token(
            service,
            access_token,
            access_token_expiration,
            refresh_token,
        )

        try:
            response = requests.post(
                "https://content.dropboxapi.com/2/files/download",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Dropbox-API-Arg": json.dumps({"path": file_id}),
                },
                timeout=30,
            )

            dropbox_result = json.loads(response.headers.get("Dropbox-API-Result"))

            if response.status_code != 200 and dropbox_result is None:
                errors.append(f"Dropbox download failed for {file_id} \
                                : {response.status_code} - {response.text}")
        except RuntimeError as e:
            errors.append(f"Failed to download {file_id}: {e}")
            continue

        dropbox_content = parse_file_content(
            response.content,
            dropbox_file,
        )

        if dropbox_content:
            try:
                update_tsvector(
                    dropbox_file,
                    dropbox_result.get("name"),
                    dropbox_content,
                    datetime.now(),
                )

                files.append({
                    "id": file_id,
                    "content": dropbox_content,
                })
            except RuntimeError as e:
                errors.append(f"Error updating tsvector for file {file_id}: {str(e)}")

    if errors:
        print("Errors occurred during Dropbox file downloads:")
        for error in errors:
            print(error)

    return files
