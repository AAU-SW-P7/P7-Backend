"""Service functions for syncing files from different services."""
import os
from datetime import datetime, timezone

from django.http import JsonResponse

# Google libs
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Microsoft libs
import msal

from p7.get_dropbox_files.helper import (
    update_or_create_file as update_or_create_file_dropbox,
    fetch_recursive_files as fetch_recursive_files_dropbox,
    get_new_access_token as get_new_access_token_dropbox
    )
from p7.get_google_drive_files.helper import (
    update_or_create_file as update_or_create_file_google_drive,
    fetch_recursive_files as fetch_recursive_files_google_drive,
    get_new_access_token as get_new_access_token_google_drive)
from p7.get_onedrive_files.helper import (
    update_or_create_file as update_or_create_file_onedrive,
    fetch_recursive_files as fetch_recursive_files_onedrive
    )
from repository.service import get_tokens, get_service
from repository.file import get_files_by_service
from repository.user import get_user

def sync_dropbox_files(
    user_id: str = None,
):
    """Fetches file metadata and updates files that have been modified since the last sync.
        params: 
        user_id: The id of the user whose files are to be synced.
    """

    user = get_user(user_id)
    if isinstance(user, JsonResponse):
        return user

    access_token, access_token_expiration, refresh_token = get_tokens(user_id, "dropbox")
    service = get_service(user_id, "dropbox")

    try:
        access_token, access_token_expiration = get_new_access_token_dropbox(
            service,
            access_token,
            access_token_expiration,
            refresh_token,
        )

        indexing_time = datetime.now(timezone.utc)
        files = fetch_recursive_files_dropbox(
            service,
            access_token,
            access_token_expiration,
            refresh_token,
        )
        updated_files = []
        for file in files:
            if file[".tag"] != "file":
                continue
            if (
                datetime.fromisoformat(
                    file.get("server_modified").replace("Z", "+00:00")) <= service.indexedAt
                and datetime.fromisoformat(
                    file.get("client_modified").replace("Z", "+00:00")) <= service.indexedAt
                ):
                continue  # No changes since last sync

            # updated_files should be used, when we want to index the updated files
            updated_files.append(file)
            update_or_create_file_dropbox(file, service)
        # Updating indexedAt may have to be moved
        # Such that it only updates if all files are processed successfully
        service.indexedAt = indexing_time
        service.save(update_fields=["indexedAt"])

        dropbox_files = get_files_by_service(service)

        for dropbox_file in dropbox_files:
            # Checks if any of the fetched files match the serviceFileId of the stored file
            # If not, it means the file has been deleted in Dropbox
            if not any(file["id"] == dropbox_file.serviceFileId for file in files):
                dropbox_file.delete()

        return updated_files
    except (ValueError, TypeError, RuntimeError, KeyError, ConnectionError, OSError) as e:
        return JsonResponse({"error": str(e)}, status=500)

def sync_google_drive_files(
    user_id: str = None,
):
    """Fetches file metadata and updates files that have been modified since the last sync.
        params:
        user_id: The id of the user whose files are to be synced.
    """

    user = get_user(user_id)
    if isinstance(user, JsonResponse):
        return user

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

        access_token = get_new_access_token_google_drive(
            service,
            creds,
            access_token,
        )

        indexing_time = datetime.now(timezone.utc)

        # Build Drive service and list files
        drive_api = build("drive", "v3", credentials=creds)
        # Request all file fields and paginate through results
        files = fetch_recursive_files_google_drive(
            drive_api,
            access_token,
            creds,
            refresh_token,
        )

        # Build a fast lookup for any item (files + folders)
        file_by_id = {file["id"]: file for file in files}

        updated_files = []
        trashed_files = []
        for file in files:
            # Skip non-files (folders, shortcuts, etc)
            mime_type = file.get("mimeType", "")
            mime_type_set = {
                "application/vnd.google-apps.folder",
                "application/vnd.google-apps.shortcut",
                "application/vnd.google-apps.drive-sdk"}
            if (mime_type in mime_type_set
            ):  # https://developers.google.com/workspace/drive/api/guides/mime-types
                continue
            if file.get("trashed"):
                trashed_files.append(file)
                continue
            if (
                datetime.fromisoformat(
                    file.get("modifiedTime").replace("Z", "+00:00")) <= service.indexedAt
                and datetime.fromisoformat(
                    file.get("createdTime").replace("Z", "+00:00")) <= service.indexedAt
                ):
                continue  # No changes since last sync

            # updated_files should be used, when we want to index the updated files
            updated_files.append(file)
            update_or_create_file_google_drive(file, service, file_by_id)
        # Updating indexedAt may have to be moved
        # Such that it only updates if all files are processed successfully
        service.indexedAt = indexing_time
        service.save(update_fields=["indexedAt"])

        google_drive_files = get_files_by_service(service)

        for google_drive_file in google_drive_files:
            # Checks if any of the fetched files match the serviceFileId of the stored file
            # If not, it means the file has been deleted in Google Drive
            if  not any(file["id"] == google_drive_file.serviceFileId for file in files):
                google_drive_file.delete()
                continue
            if  any(file["id"] == google_drive_file.serviceFileId for file in trashed_files):
                google_drive_file.delete()
                continue

        return updated_files

    except (ValueError,TypeError,KeyError, RuntimeError) as e:
        return JsonResponse({"error": str(e)}, status=500)

def sync_onedrive_files(
    user_id: str = None,
):
    """Fetches file metadata and updates files that have been modified since the last sync.
        params:
        user_id: The id of the user whose files are to be synced.
    """

    user = get_user(user_id)
    if isinstance(user, JsonResponse):
        return user

    access_token, access_token_expiration, refresh_token = get_tokens(user_id, "onedrive")
    service = get_service(user_id, "onedrive")

    try:
        indexing_time = datetime.now(timezone.utc)
        # Build MSAL app instance
        app = msal.ConfidentialClientApplication(
            os.getenv("MICROSOFT_CLIENT_ID"),
            authority="https://login.microsoftonline.com/common",
            client_credential=os.getenv("MICROSOFT_CLIENT_SECRET"),
        )

        files = fetch_recursive_files_onedrive(
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
            update_or_create_file_onedrive(file, service)
        # Updating indexedAt may have to be moved
        # Such that it only updates if all files are processed successfully
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
