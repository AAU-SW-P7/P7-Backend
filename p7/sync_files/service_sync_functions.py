"""Service functions for syncing files from different services."""
import os
from datetime import datetime, timezone


from django.http import JsonResponse
from p7.get_dropbox_files.helper import (
    update_or_create_file, fetch_recursive_files, get_new_access_token
    )
from p7.get_google_drive_files.helper import (
    update_or_create_file, fetch_recursive_files, get_new_access_token)
from p7.get_onedrive_files.helper import (
    update_or_create_file, fetch_recursive_files
    )
from repository.service import get_tokens, get_service
from repository.file import get_files_by_service

# Google libs
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Microsoft libs
import msal

def sync_dropbox_files(
    user_id: str = None,
):
    """Fetches file metadata and updates files that have been modified since the last sync.
        params: 
        x_internal_auth: Internal auth token for validating the request.
        user_id: The id of the user whose files are to be synced.
    """
    if not user_id:
        return JsonResponse({"error": "user_id required"}, status=400)

    access_token, access_token_expiration, refresh_token = get_tokens(user_id, "dropbox")
    service = get_service(user_id, "dropbox")

    try:
        access_token, access_token_expiration = get_new_access_token(
            service,
            access_token,
            access_token_expiration,
            refresh_token,
        )

        indexing_time = datetime.now(timezone.utc)
        files = fetch_recursive_files(
            service,
            access_token,
            access_token_expiration,
            refresh_token,
        )
        updated_files = []
        for file in files:
            if file[".tag"] != "file":
                continue
            if datetime.fromisoformat(
                file["server_modified"].replace("Z", "+00:00")) <= service.indexedAt:
                continue  # No changes since last sync

            # updated_files should be used, when we want to index the updated files
            updated_files.append(file)
            update_or_create_file(file, service)
        service.indexedAt = indexing_time
        service.save(update_fields=["indexedAt"])

        dropbox_files = get_files_by_service(service)

        for dropbox_file in dropbox_files:
            # Checks if any of the fetched files match the serviceFileId of the stored file
            # If not, it means the file has been deleted in Dropbox
            if not any(file["id"] == dropbox_file.serviceFileId for file in files):
                dropbox_file.delete()

        return updated_files
    except KeyError as e:
        response = JsonResponse({"error": f"Missing key: {str(e)}"}, status=500)
        return response
    except ValueError as e:
        response = JsonResponse({"error": f"Value error: {str(e)}"}, status=500)
        return response
    except ConnectionError as e:
        response = JsonResponse({"error": f"Connection error: {str(e)}"}, status=500)
        return response
    except RuntimeError as e:
        response = JsonResponse({"error": f"Runtime error: {str(e)}"}, status=500)
        return response
    except TypeError as e:
        response = JsonResponse({"error": f"Type error: {str(e)}"}, status=500)
        return response
    except OSError as e:
        response = JsonResponse({"error": f"OS error: {str(e)}"}, status=500)
        return response

def sync_google_drive_files(
    user_id: str = None,
):
    """Fetches file metadata and updates files that have been modified since the last sync.
        params:
        x_internal_auth: Internal auth token for validating the request.
        user_id: The id of the user whose files are to be synced.
    """
    if not user_id:
        return JsonResponse({"error": "user_id required"}, status=400)

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

        indexing_time = datetime.now(timezone.utc)

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

        updated_files = []
        for file in files:
            # Skip non-files (folders, shortcuts, etc)
            mime_type = file.get("mimeType", "")
            if (
                mime_type == "application/vnd.google-apps.folder"
                or mime_type == "application/vnd.google-apps.shortcut"
                or mime_type == "application/vnd.google-apps.drive-sdk"
            ):  # https://developers.google.com/workspace/drive/api/guides/mime-types
                continue
            if datetime.fromisoformat(
                file.get("modifiedTime").replace("Z", "+00:00")) <= service.indexedAt:
                continue  # No changes since last sync
            # updated_files should be used, when we want to index the updated files
            updated_files.append(file)
            update_or_create_file(file, service, file_by_id)
        service.indexedAt = indexing_time
        service.save(update_fields=["indexedAt"])

        google_drive_files = get_files_by_service(service)

        for google_drive_file in google_drive_files:
            # Checks if any of the fetched files match the serviceFileId of the stored file
            # If not, it means the file has been deleted in Google Drive
            if not any(file["id"] == google_drive_file.serviceFileId for file in files):
                google_drive_file.delete()
        return updated_files

    except (ValueError,TypeError,KeyError, RuntimeError) as e:
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
