"""API for fetching and syncing OneDrive files."""
import os
from datetime import datetime, timezone

from ninja import Router, Header
from django.http import JsonResponse

# Microsoft libs
import msal

from p7.helpers import validate_internal_auth
from p7.get_onedrive_files.helper import (
    update_or_create_file, fetch_recursive_files
    )
from repository.service import get_tokens, get_service
from repository.file import get_files_by_service

fetch_onedrive_files_router = Router()

@fetch_onedrive_files_router.get("/")
def fetch_onedrive_files(
    request,
    user_id: str,
    x_internal_auth: str = Header(..., alias="x-internal-auth"),
):
    """Fetch and save OneDrive files for a given user.

    params:
        x_internal_auth (str): The internal auth header for validating the request.
        user_id (str): The ID of the user whose OneDrive files are to be fetched.
    """
    auth_resp = validate_internal_auth(x_internal_auth)

    if auth_resp:
        return auth_resp

    if not user_id:
        return JsonResponse({"error": "user_id required"}, status=400)

    access_token, access_token_expiration, refresh_token = get_tokens(user_id, "microsoft-entra-id")
    service = get_service(user_id, "microsoft-entra-id")

    try:
        # Build MSAL app instance
        app = msal.ConfidentialClientApplication(
            os.getenv("MICROSOFT_CLIENT_ID"),
            authority="https://login.microsoftonline.com/common",
            client_credential=os.getenv("MICROSOFT_CLIENT_SECRET"),
        )

        files = fetch_recursive_files(
            app,
            service,
            access_token,
            access_token_expiration,
            refresh_token,
        )

        for file in files:
            if "folder" in file:  # Skip folders
                continue

            update_or_create_file(file, service)

        return JsonResponse(files, safe=False)
    except (ValueError, TypeError, RuntimeError) as e:
        return JsonResponse({"error": str(e)}, status=500)


def sync_onedrive_files(
    user_id: str = None,
):
    """Fetches file metadata and updates files that have been modified since the last sync.
        params:
        request: The HTTP request object.
        x_internal_auth: Internal auth token for validating the request.
        user_id: The id of the user whose files are to be synced.
    """
    if not user_id:
        return JsonResponse({"error": "user_id required"}, status=400)

    access_token, access_token_expiration, refresh_token = get_tokens(user_id, "microsoft-entra-id")
    service = get_service(user_id, "microsoft-entra-id")

    try:
        indexing_time = datetime.now(timezone.utc)
        # Build MSAL app instance
        app = msal.ConfidentialClientApplication(
            os.getenv("MICROSOFT_CLIENT_ID"),
            authority="https://login.microsoftonline.com/common",
            client_credential=os.getenv("MICROSOFT_CLIENT_SECRET"),
        )

        files = fetch_recursive_files(
            app,
            service,
            access_token,
            access_token_expiration,
            refresh_token,
        )

        updated_files = []
        for file in files:
            if "folder" in file:  # Skip folders
                continue
            if datetime.fromisoformat(
                file["lastModifiedDateTime"].replace("Z", "+00:00")) <= service.indexedAt:
                continue  # No changes since last sync
            # updated_files should be used, when we want to index the updated files
            updated_files.append(file)
            update_or_create_file(file, service)
        service.indexedAt = indexing_time
        service.save(update_fields=["indexedAt"])

        onedrive_files = get_files_by_service(service)

        for onedrive_file in onedrive_files:
            # Checks if any of the fetched files match the serviceFileId of the stored file
            # If not, it means the file has been deleted in Onedrive
            if not any(file["id"] == onedrive_file.serviceFileId for file in files):
                onedrive_file.delete()

        return updated_files
    except (ValueError, TypeError, RuntimeError) as e:
        return JsonResponse({"error": str(e)}, status=500)
