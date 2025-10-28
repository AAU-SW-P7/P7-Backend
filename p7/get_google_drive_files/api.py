"""API route to fetch and save Google Drive files for a user."""
from datetime import datetime, timezone
import os
from typing import Dict
from ninja import Router, Header
from django.http import JsonResponse
# Google libs
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from p7.helpers import validate_internal_auth, smart_extension
from repository.service import get_tokens, get_service
from repository.file import save_file

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

        access_token = _get_new_access_token(
            service,
            creds,
            access_token,
        )

        # Build Drive service and list files
        drive_api = build("drive", "v3", credentials=creds)
        # Request all file fields and paginate through results
        files = _fetch_recursive_files(
            drive_api,
            access_token,
            creds,
            refresh_token,
        )

        # Build a fast lookup for any item (files + folders)
        file_by_id = {file["id"]: file for file in files}

        for file in files:
            extension = smart_extension("google", file["name"], file.get("mimeType"))
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

        return JsonResponse(files, safe=False)
    except (ValueError,TypeError,KeyError, RuntimeError) as e:
        return JsonResponse({"error": str(e)}, status=500)

def _fetch_recursive_files(
    drive_api,
    service,
    creds,
    access_token: str,
) -> list[dict]:
    """Helper function to fetch the initial set of files from Dropbox."""

    files = []
    page_token = None
    while True:
        access_token = _get_new_access_token(
            service,
            creds,
            access_token,
        )

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

    return [
        file for file in files if not (
            file.get("mimeType") == "application/vnd.google-apps.folder"
            or file.get("mimeType") == "application/vnd.google-apps.shortcut"
            or file.get("mimeType") == "application/vnd.google-apps.drive-sdk"
        ) # https://developers.google.com/workspace/drive/api/guides/mime-types
    ]

def _get_new_access_token(
    service,
    creds,
    access_token: str,
) -> str:
    """Helper function to get a new access token using the refresh token.

    params:
        refresh_token (str): The refresh token to use for obtaining a new access token.
    
    returns:
        str: A string with the new access token.
    """
    # Refresh if needed (this will update creds.token)
    if not creds.valid:
        print("Refreshing Google Drive access token...")
        creds.refresh(Request())

        # Optionally persist the new access_token back to DB so next calls use it
        new_token = creds.token
        new_token_expiration = datetime.fromtimestamp(creds.expiry.timestamp(), tz=timezone.utc)
        service.accessToken = new_token
        service.accessTokenExpiration = new_token_expiration
        service.save(update_fields=["accessToken", "accessTokenExpiration"])

        return new_token

    return access_token

def build_google_drive_path(file_meta: dict, file_by_id: dict) -> str:
    """
    Build a display path like /FolderA/FolderB/filename 
    using only the current `files` array.

    params:
        file_meta (dict): The metadata dictionary of the file for which to build the path.
    returns:
        str: The constructed file path.
    """
    parents = file_meta.get("parents") or []
    prefix_parts = (
        google_drive_folder_path_parts(parents[0], file_by_id)
        if parents
        else []
    )
    # Join and include filename at the end to mimic Dropbox-style path_display
    return "/" + "/".join(prefix_parts + [file_meta.get("name", "")])

def google_drive_folder_path_parts(
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
    prefix = google_drive_folder_path_parts(parents[0], file_by_id) if parents else []
    return prefix + [folder.get("name", folder_id)]
