"""API for fetching, saving, and syncing Google Drive files."""
import os
from typing import Dict
from p7.helpers import validate_internal_auth
from repository.service import get_tokens, get_service
from repository.file import save_file

from ninja import Router, Header
from django.http import JsonResponse
# Google libs
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


fetch_google_drive_files_router = Router()


def _google_drive_folder_path_parts(
    folder_id: str, file_by_id: Dict[str, dict]
) -> list:
    """
    Returns a list like ['FolderA', 'FolderB'] for a folder id.
    Stops gracefully if an ancestor isn't in `files`.
    Works for 'root' (My Drive) and shared drives (top-level folder has no parents).
    params:
        folder_id (str): The Google Drive folder ID to build the path for.
        file_by_id (Dict[str, dict]): A mapping of file IDs to their metadata dictionaries.
    returns:
        list: A list of folder names from the root to the specified folder.
    """
    if not folder_id or folder_id == "root":
        return []

    folder = file_by_id.get(folder_id)
    if not folder:  # ancestor not present in current listing
        return []  # return partial path instead of failing

    parents = folder.get("parents") or []
    # Use the first parent if multiple
    prefix = _google_drive_folder_path_parts(parents[0], file_by_id) if parents else []
    return prefix + [folder.get("name", folder_id)]


@fetch_google_drive_files_router.get("/")
def fetch_google_drive_files(
    request,
    x_internal_auth: str = Header(..., alias="x-internal-auth"),
    user_id: str = None,
):
    """
        Fetches all file metadata from a user's Google Drive account and saves it to the DB
        params:
        x_internal_auth: Internal auth token for validating the request.
        user_id: The id of the user whose files are to be fetched.
    """
    try:
        files, service = get_file_meta_data(x_internal_auth, user_id)
        # Build a fast lookup for any item (files + folders)
        file_by_id = {file["id"]: file for file in files}

        for file in files:
            update_or_create_file(file, service, file_by_id)

    except (ValueError,TypeError,KeyError, RuntimeError) as e:
        return JsonResponse({"error": str(e)}, status=500)

sync_google_drive_files_router = Router()
@sync_google_drive_files_router.get("/")
def sync_google_drive_files(
    request,
    x_internal_auth: str = Header(..., alias="x-internal-auth"),
    user_id: str = None,
):
    """Fetches file metadata and updates files that have been modified since the last sync.
        params:
        x_internal_auth: Internal auth token for validating the request.
        user_id: The id of the user whose files are to be synced.
    """
    try:
        files, service = get_file_meta_data(x_internal_auth, user_id)
        # Build a fast lookup for any item (files + folders)
        file_by_id = {file["id"]: file for file in files}

        updated_files = []
        for file in files:
            if file.get("modifiedTime") <= service.modifiedAt.isoformat():
                continue  # No changes since last sync

            updated_files.append(file)
            update_or_create_file(file, service, file_by_id)

    except (ValueError,TypeError,KeyError, RuntimeError) as e:
        return JsonResponse({"error": str(e)}, status=500)

def get_file_meta_data(
    x_internal_auth: str = Header(..., alias="x-internal-auth"),
    user_id: str = None,
):
    """Fetches all file metadata from a user's Google Drive account.
        params:
        x_internal_auth: Internal auth token for validating the request.
        user_id: The id of the user whose files are to be fetched.
        
        Returns:
        List of fetched files
        Service object.
    """
    auth_resp = validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp

    if not user_id:
        return JsonResponse({"error": "user_id required"}, status=400)

    access_token, refresh_token = get_tokens(user_id, "google")
    service = get_service(user_id, "google")

    # Build credentials object. token may be stale; refresh() will update it.
    creds = Credentials(
        token=access_token or None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
    )

    # Refresh if needed (this will update creds.token)
    if not creds.valid:
        print("Refreshing Google access token...")
        creds.refresh(Request())

    # Optionally persist the new access_token back to DB so next calls use it
    new_token = creds.token
    if new_token and new_token != access_token:
        # Update via Django ORM instead of raw SQL
        service.accessToken = new_token
        service.save(update_fields=["accessToken"])

    # Build Drive service and list files
    drive_api = build("drive", "v3", credentials=creds)
    # Request all file fields and paginate through results
    files = []
    page_token = None
    while True:
        resp = (
            drive_api.files()
            .list(
                pageSize=1000,
                fields="nextPageToken, files(id, name, parents, "
                "capabilities/canCopy, capabilities/canDownload, downloadRestrictions, "
                "kind, mimeType, starred, "
                "trashed, webContentLink, webViewLink, "
                "iconLink, hasThumbnail, viewedByMeTime, "
                "createdTime, modifiedTime, shared, "
                "ownedByMe, originalFilename, size)",
                pageToken=page_token,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
        files.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return files, service

def update_or_create_file(file, service, file_by_id: Dict[str, dict]):
    """ Updates or creates a File record from Google Drive file metadata.
        params:
        file: A dictionary containing Google Drive file metadata.
        service: The service object associated with the user.
        file_by_id: A dictionary mapping file IDs to their metadata for path construction.
    """
    # Skip non-files (folders, shortcuts, etc)
    mime_type = file.get("mimeType", "")
    if (
        mime_type == "application/vnd.google-apps.folder"
        or mime_type == "application/vnd.google-apps.shortcut"
        or mime_type == "application/vnd.google-apps.drive-sdk"
    ):  # https://developers.google.com/workspace/drive/api/guides/mime-types
        return

    extension = os.path.splitext(file.get("name", ""))[1]
    downloadable = file.get("capabilities", {}).get("canDownload")
    path = build_google_drive_path(file, file_by_id)

    save_file(
        service,
        file["id"],
        file["name"],
        extension,
        downloadable,
        path,
        file["webViewLink"],
        file.get("size", 0), # Can be empty
        file["createdTime"],
        file["modifiedTime"],
        None,
        None,
        None,
    )

def build_google_drive_path(file_meta: dict, file_by_id: Dict[str, dict]) -> str:
    """ Build a display path like /FolderA/FolderB/filename using only the current `files` array.
        params:
        file_meta: A dictionary containing Google Drive file metadata.
        file_by_id: A dictionary mapping file IDs to their metadata for path construction.

        Returns:
        A string representing the file path.
    """
    parents = file_meta.get("parents") or []
    prefix_parts = (
        _google_drive_folder_path_parts(parents[0], file_by_id)
        if parents
        else []
    )
    # Join and include filename at the end to mimic Dropbox-style path_display
    return "/" + "/".join(prefix_parts + [file_meta.get("name", "")])
