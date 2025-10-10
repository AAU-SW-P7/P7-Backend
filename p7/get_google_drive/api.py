import os
import requests
from p7.helpers import validate_internal_auth
from repository.service import get_tokens, get_service
from repository.file import save_file
from typing import Dict

# Helper: compute the folder path pieces for a given folder id (memoized)
from functools import lru_cache

from ninja import Router, Body, Header
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
    userId: str = None,
):
    auth_resp = validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp

    if not userId:
        return JsonResponse({"error": "userId required"}, status=400)

    access_token, refresh_token = get_tokens(userId, "google")
    service = get_service(userId, "google")

    try:
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

        # Build a fast lookup for any item (files + folders)
        file_by_id = {file["id"]: file for file in files}

        def build_google_drive_path(file_meta: dict) -> str:
            """
            Build a display path like /FolderA/FolderB/filename using only the current `files` array.
            """
            parents = file_meta.get("parents") or []
            prefix_parts = (
                _google_drive_folder_path_parts(parents[0], file_by_id)
                if parents
                else []
            )
            # Join and include filename at the end to mimic Dropbox-style path_display
            return "/" + "/".join(prefix_parts + [file_meta.get("name", "")])

        for file in files:
            if (
                file.get("mimeType") == "application/vnd.google-apps.folder"
                or file.get("mimeType") == "application/vnd.google-apps.shortcut"
                or file.get("mimeType") == "application/vnd.google-apps.drive-sdk"
            ):  # https://developers.google.com/workspace/drive/api/guides/mime-types
                continue
            extension = os.path.splitext(file.get("name", ""))[1]
            downloadable = file.get("capabilities", {}).get("canDownload")
            path = build_google_drive_path(file)
            
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

        # return JsonResponse(files, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
